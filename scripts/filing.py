"""Cheap identity-only filing: bounded reading packets, validation and CSV/Markdown reports.

This stage never fills the full sort card, judges status, or builds diagrams/graph rows.
Existing full cards can supply identity without another model read.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote

from kit_common import (
    KIT, WORK, WORK_FILES, WORK_TEXT, OUT, ENTITY_MAP_CSV, SORT_LOG_CSV, SORT_LOG_COLUMNS,
    account_folder, apply_corrections_to_card, erp_account_names, join_multi, load_all_cards,
    load_corrections, load_entity_map, load_erp, load_inventory, load_our_entities,
    names_from_card, norm_name, safe_folder_name, stream_map, write_csv, write_text,
)
from sort import decide_targets
from validate_forms import PAGE_MARKER, PARAGRAPH_MARKER, _segments, _evidence_checks, load_form

FILINGS = WORK / 'filing'
COLUMNS = ['doc_id', 'original_path', 'file_type', 'pages', 'scanned_pages', 'sha256',
           'account', 'title', 'kind', 'companies_found', 'basis', 'confidence',
           'read_status', 'file_path', 'note']
KEYS = {'doc_id', 'sha256', 'title', 'kind', 'their_entities', 'our_entities',
        'pages_read', 'paragraphs_read', 'note'}


def inventory():
    return {r['doc_id']: r for r in load_inventory() if r['doc_id'] != 'erp'}


def units(doc, row):
    text = (WORK_TEXT / f'{doc}.txt').read_text(encoding='utf-8-sig')
    if row['file_type'] == 'docx':
        return _segments(text, PARAGRAPH_MARKER), 'paragraph'
    return _segments(text, PAGE_MARKER) or {1: text}, 'page'


def packet(doc, row, extra_page=None, extra_paragraph=None):
    segments, label = units(doc, row)
    selected = list(sorted(segments))[:12 if label == 'paragraph' else 2]
    if extra_page is not None:
        if label != 'page' or extra_page not in segments:
            raise ValueError('Extra page must be an existing PDF/image page')
        selected = [extra_page]
    if extra_paragraph is not None:
        if label != 'paragraph' or extra_paragraph not in segments:
            raise ValueError('Extra paragraphs must start at an existing Word paragraph')
        selected = [n for n in sorted(segments) if n >= extra_paragraph][:8]
    remaining = 600 if extra_page is not None or extra_paragraph is not None else 1200
    excerpt = []
    for number in selected:
        words = segments[number].split()
        shown = words[:remaining]
        excerpt.append(f'=== {label} {number} ===\n' + ' '.join(shown))
        remaining -= len(shown)
        if len(shown) < len(words):
            excerpt.append('[packet truncated; identity may be unresolved]')
        if remaining <= 0:
            break
    print(json.dumps({k: row.get(k, '') for k in ('doc_id', 'sha256', 'file_type', 'pages',
          'scanned_pages', 'docx_tracked_changes', 'docx_comments')}, indent=2))
    print('Identity/type only. Legal status is unassessed. Total limit: 3 pages or 20 Word paragraphs.')
    print('\n'.join(excerpt))


def validate(record, doc, row):
    if not isinstance(record, dict) or set(record) != KEYS:
        raise ValueError(f'doc {doc}: filing record must have exactly {sorted(KEYS)}')
    if record['doc_id'] != doc or record['sha256'] != row['sha256']:
        raise ValueError(f'doc {doc}: stale source hash or mismatched id; rerun the filer')
    for key in ('title', 'kind', 'note'):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ValueError(f'doc {doc}: {key} must be a nonblank string')
    if len(record['note'].split()) > 80:
        raise ValueError(f'doc {doc}: filing note exceeds 80 words')
    for key, maximum, ceiling in [('pages_read', 3, int(row.get('pages') or 1)),
                                  ('paragraphs_read', 20, int(row.get('paragraphs') or 0))]:
        values = record[key]
        if not isinstance(values, list) or len(values) > maximum or any(
                type(n) is not int or n < 1 or n > ceiling for n in values) or len(values) != len(set(values)):
            raise ValueError(f'doc {doc}: invalid or over-budget {key}')
    if row['file_type'] == 'docx':
        if record['pages_read'] or not record['paragraphs_read']:
            raise ValueError(f'doc {doc}: Word reading must record paragraphs, not pages')
    elif record['paragraphs_read'] or not record['pages_read']:
        raise ValueError(f'doc {doc}: PDF/image reading must record pages')
    evidence = []
    for key in ('their_entities', 'our_entities'):
        if not isinstance(record[key], list):
            raise ValueError(f'doc {doc}: {key} must be a list; [] means no name identified')
        for entity in record[key]:
            if not isinstance(entity, dict) or set(entity) != {'name', 'ref', 'words'} or any(
                    not isinstance(entity[k], str) or not entity[k].strip() for k in entity):
                raise ValueError(f'doc {doc}: each entity needs name, ref and exact words')
            if entity['name'] not in entity['words']:
                raise ValueError(f'doc {doc}: printed entity name must appear exactly in its quotation')
            match = re.fullmatch(r'(p\.|¶)\s*(\d+)', entity['ref'])
            if not match:
                raise ValueError(f'doc {doc}: use p.N or ¶ N for filing evidence')
            read_key = 'pages_read' if match[1] == 'p.' else 'paragraphs_read'
            if int(match[2]) not in record[read_key]:
                raise ValueError(f'doc {doc}: citation is outside the reported reading budget')
            evidence.append({'identity_evidence': {k: entity[k] for k in ('ref', 'words')}})
    errors, warnings = _evidence_checks({'identity': evidence}, WORK_TEXT / f'{doc}.txt')
    if errors:
        raise ValueError(f'doc {doc}: ' + '; '.join(errors))
    return warnings


def identities(rows):
    full = load_all_cards()
    corrections = load_corrections()
    ours = load_our_entities()
    result = {}
    for doc, row in rows.items():
        if row['readable'] != 'yes':
            continue
        path = FILINGS / f'{doc}.json'
        if doc in full and not path.exists():
            card = apply_corrections_to_card(full[doc], corrections)
            result[doc] = {'title': card['q1_title'], 'kind': card['q1_kind'],
                           'names': names_from_card(card, ours), 'read_status': 'full_card_reused',
                           'note': 'Existing full reading reused for filing identity only.'}
            continue
        if not path.exists():
            continue
        try:
            record = load_form(path)
            warnings = validate(record, doc, row)
        except (ValueError, OSError, KeyError) as error:
            print(f'REVIEW: doc {doc}: invalid filing record; needs reading: {error}', file=sys.stderr)
            continue
        card = {'doc_id': doc, 'q2_their_signing_entities': join_multi(e['name'] for e in record['their_entities']),
                'q2_their_group_companies': 'not found',
                'q2_our_entity': join_multi(e['name'] for e in record['our_entities'])}
        card = apply_corrections_to_card(card, corrections)
        result[doc] = {'title': record['title'], 'kind': record['kind'],
                      'names': names_from_card(card, ours), 'read_status': 'filing_only',
                      'note': record['note'] + (' Visual identity evidence needs review.' if warnings else '')}
    return result


def target_folder(side, target):
    if target.startswith('_'):
        return OUT / side / Path(*(safe_folder_name(part) for part in target.split('/')))
    return account_folder(side, target)


def report(rows, records):
    erp = load_erp()
    side = erp['side']
    accounts = erp_account_names(erp)
    entities, _ = load_entity_map()
    streams = stream_map(erp, entities)
    corpus, logs = [], []
    by_norm = {norm_name(a): a for a in accounts}
    # Resolve and validate everything before replacing a generated report.
    for doc, inv in sorted(rows.items()):
        identity = records.get(doc, {})
        names = identity.get('names', [])
        if inv['readable'] != 'yes':
            targets = [{'target': '_unreadable', 'basis': '', 'confidence': '', 'note': inv.get('note', '')}]
        elif not identity:
            targets = [{'target': '_needs-reading', 'basis': '', 'confidence': '', 'note': 'No filing record; run /sort again.'}]
        else:
            _, targets, _ = decide_targets(names, entities, by_norm, streams)
        for target in targets:
            account = target['target']
            folder = target_folder(side, account)
            source = WORK_FILES / f"{doc}.{inv['ext']}"
            dest = folder / 'files' / f"{doc}-{inv['file_name']}"
            if inv['readable'] == 'yes' and not source.exists():
                raise ValueError(f'doc {doc}: prepared source copy missing; run /prepare again')
            row = {k: inv.get(k, '') for k in COLUMNS}
            row.update(account=account, title=identity.get('title', 'not found'),
                       kind=identity.get('kind', 'not assessed'), companies_found=join_multi(names),
                       basis=target['basis'], confidence=target['confidence'],
                       read_status=identity.get('read_status', 'unreadable' if inv['readable'] != 'yes' else 'needs_reading'),
                       file_path=str(dest.relative_to(KIT)) if source.exists() and inv['readable'] == 'yes' else '',
                       note='; '.join(x for x in [identity.get('note', ''), target['note']] if x))
            corpus.append(row)
            logs.append({k: row.get(k, '') for k in SORT_LOG_COLUMNS})
    if OUT.exists():
        archive = WORK / 'history' / ('filing-' + datetime.now().strftime('%Y%m%dT%H%M%S%f'))
        archive.mkdir(parents=True)
        OUT.rename(archive / 'out')
        print(f'Previous generated report retained at {archive.relative_to(KIT)}/out')
    for row in corpus:
        if row['file_path']:
            dest = KIT / row['file_path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(WORK_FILES / f"{row['doc_id']}.{rows[row['doc_id']]['ext']}", dest)
    folder_targets = (set(accounts) - set(streams)) | {r['account'] for r in corpus}
    for target in sorted(folder_targets):
        folder = target_folder(side, target)
        selected = [r for r in corpus if r['account'] == target]
        write_csv(folder / 'documents.csv', selected, COLUMNS)
        lines = [f'# {target} — filed documents', '',
                 'Identity and filing pass only. Contract validity, execution, governing status, parts and links are not assessed here.', '',
                 '| doc | title | preliminary kind | match | note |', '| --- | --- | --- | --- | --- |']
        for row in selected:
            cells = [row['doc_id'], row['title'], row['kind'],
                     f"{row['basis']} / {row['confidence']}", row['note']]
            lines.append('| ' + ' | '.join(str(c).replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |')
        lines += ['', 'Source paths and hashes are in documents.csv. /visualise adds a filing diagram; /deep-dive assesses the contracts.', '']
        write_text(folder / 'README.md', '\n'.join(lines))
    for stream, (main, _) in streams.items():
        write_text(account_folder(side, stream) / 'README.md',
                   f'# {stream}\n\nTreated as a stream of {main}; files are in ../{safe_folder_name(main)}/.\n')
    write_csv(SORT_LOG_CSV, logs, SORT_LOG_COLUMNS)
    write_csv(OUT / side / 'CORPUS.csv', corpus, COLUMNS)
    write_csv(OUT / side / 'ACCOUNTS.csv', [dict(account=a, side=side,
              n_documents=sum(r['account'] == a for r in corpus),
              treated_as_stream_of=streams[a][0] if a in streams else '') for a in accounts],
              ['account', 'side', 'n_documents', 'treated_as_stream_of'])
    index = [f'# Filed accounts ({side})', '', 'Filing only; legal status has not been assessed.', '',
             f'Global table: [{side}/CORPUS.csv]({quote(side)}/CORPUS.csv).', '',
             '| folder | documents | contents |', '| --- | --- | --- |']
    for target in sorted(set(accounts) | {r['account'] for r in corpus}):
        folder = target_folder(side, target)
        link = quote(str((folder / 'README.md').relative_to(OUT)), safe='/')
        index.append(f"| {target.replace('|', '/')} | {sum(r['account'] == target for r in corpus)} | [readme]({link}) |")
    write_text(OUT / 'INDEX.md', '\n'.join(index) + '\n')
    print(f'Filed {len(rows)} documents into {len(accounts)} ERP rows; {len(corpus)} corpus rows. CSV/Markdown only.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--packet', metavar='DOC')
    actions.add_argument('--validate', metavar='DOC')
    actions.add_argument('--pending', action='store_true')
    actions.add_argument('--names', action='store_true')
    actions.add_argument('--report', action='store_true')
    extra = parser.add_mutually_exclusive_group()
    extra.add_argument('--page', type=int, help='one extra page, only with --packet')
    extra.add_argument('--paragraph', type=int, help='first of at most eight extra Word paragraphs, only with --packet')
    parser.add_argument('--force', action='store_true', help='include previously read documents in --pending')
    args = parser.parse_args()
    if (args.page is not None or args.paragraph is not None) and not args.packet:
        parser.error('--page and --paragraph require --packet')
    try:
        rows = inventory()
        if args.packet or args.validate:
            doc = (args.packet or args.validate).zfill(3)
            if not re.fullmatch(r'\d{3,}', doc) or doc not in rows or rows[doc]['readable'] != 'yes':
                raise ValueError('Choose a readable document number from the inventory')
            if args.packet:
                packet(doc, rows[doc], args.page, args.paragraph)
            else:
                warnings = validate(load_form(FILINGS / f'{doc}.json'), doc, rows[doc])
                print(f'doc {doc}: valid filing record')
                for warning in warnings:
                    print('REVIEW: ' + warning)
            return 0
        records = identities(rows)
        if args.pending:
            pending = [d for d, r in rows.items() if r['readable'] == 'yes' and (args.force or d not in records)]
            print(json.dumps({'pending': pending, 'reused': [] if args.force else sorted(records),
                              'budget': 'at most 3 pages or 20 Word paragraphs per new filing read'}, indent=2))
        elif args.names:
            print(json.dumps({d: {'names': r['names'], 'note': r['note']} for d, r in records.items()}, indent=2))
        else:
            report(rows, records)
        return 0
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
