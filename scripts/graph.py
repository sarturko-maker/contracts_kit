"""Export validated forms using the unchanged DCG headers; retain gaps in companion tables.

The mapper writes work/trees/<account>.json. This script does no legal classification.
--account validates one mapper proposal and writes its TREES.md. --all merges
all accounts after the mappers finish, avoiding concurrent writes to shared CSVs.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import (
    KIT, WORK, OUT, CORPUS_COLUMNS, account_folder, fail, norm_name, read_csv,
    read_json, safe_folder_name, say, write_csv, write_text,
)
from place import load_context, settled_for_all_accounts, build_all_rows
from validate_forms import validate_form, evidence_warnings, load_form

DCG = KIT / 'dcg'
ABSENT = {'', 'not_found', 'none', 'none_found', 'inherits'}
KINDS = {
    'master_or_framework': 'master', 'local_adoption_of_group_agreement': 'participation',
    'standard_terms_of_sale': 'shared_terms', 'project_or_programme_agreement': 'master',
    'schedule_or_annex': 'component', 'amendment_or_side_letter': 'change',
    'pricing_or_rebate_letter': 'change', 'nda': 'master', 'guarantee_or_bond': 'security',
    'other_overlay': 'shared_terms', 'order_or_quote': 'order', 'credit_application': 'master',
}
STATUS = {'live_fixed_term': 'active', 'live_rolling_presumed': 'active',
          'expired_by_date': 'expired', 'terminated': 'terminated', 'replaced': 'superseded',
          'unknown': 'provisional', 'not_found': 'provisional'}


def stable_id(prefix, *values):
    value = json.dumps([norm_name(str(v)) for v in values], ensure_ascii=False)
    return prefix + '-' + hashlib.sha256(value.encode()).hexdigest()[:20]


def present(value):
    return isinstance(value, (dict, list)) or str(value) not in ABSENT


def items(value):
    return value if isinstance(value, list) else []


def header(name):
    with (DCG / name).open(encoding='utf-8-sig', newline='') as handle:
        return next(csv.reader(handle))


def flatten(value, prefix=''):
    """One fixed column per field; repeated parts stay labelled and never become JSON cells."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            result.update(flatten(child, f'{prefix}_{key}' if prefix else key))
        return result
    if isinstance(value, list):
        collected = defaultdict(list)
        for child in value:
            label = child.get('F1_part_name', child.get('part', '')) if isinstance(child, dict) else ''
            for key, val in flatten(child, prefix).items():
                collected[key].append(f'{label}: {val}' if label else val)
        return {key: ' | '.join(vals) for key, vals in collected.items()}
    return {prefix: 'not_found' if value is None else str(value)}


def health_fields(value, prefix=''):
    """Count each repeated part answer separately under the same fixed question name."""
    if isinstance(value, dict):
        for key, child in value.items():
            if (key.endswith('_evidence') and key != 'D3_ended_evidence') or key in ('words', 'page_or_clause', 'page'):
                continue
            yield from health_fields(child, f'{prefix}.{key}' if prefix else key)
    elif isinstance(value, list):
        for child in value:
            yield from health_fields(child, prefix)
    else:
        yield prefix, value


class Export:
    def __init__(self):
        self.node_types = {r['id']: r for r in read_csv(DCG / 'node_types.csv')}
        self.edge_types = {r['id']: r for r in read_csv(DCG / 'edge_types.csv')}
        self.properties = {r['property']: r for r in read_csv(DCG / 'properties.csv')}
        self.node_columns = header('sample-nodes-header.csv')
        self.edge_columns = header('sample-edges-header.csv')
        self.nodes = {}
        self.edges = {}
        self.node_properties = {}
        self.edge_evidence = {}
        self.matches = {}
        self.gaps = set()
        self.sources = {}

    def gap(self, doc, kind, description, place='', ref=''):
        self.gaps.add((kind, description, place, doc, ref))

    def node(self, node_id, kind, name, doc='', **properties):
        if kind not in self.node_types:
            raise ValueError(f'Unknown DCG node type: {kind}')
        row = self.nodes.setdefault(node_id, {'id:ID': node_id, 'name': name, ':LABEL': kind,
                                             'layer': self.node_types[kind]['layer']})
        if row[':LABEL'] != kind:
            raise ValueError(f'Conflicting node types for {node_id}')
        for key, value in properties.items():
            if value is None or value == '' or value == 'not_found':
                continue
            value = str(value)
            if key in self.node_columns:
                row[key] = value
            elif key in self.properties:
                self.node_properties[(node_id, key)] = {'node_id': node_id, 'property': key, 'value': value}
                self.gap(doc, 'missing_field', f'{key} has no column in the sample node header; retained in node-properties.csv', key)
            else:
                raise ValueError(f'Unknown DCG property: {key}')
        return node_id

    def edge(self, source, target, kind, doc='', evidence=None, **properties):
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f'Dangling {kind} edge: {source} -> {target}')
        if kind not in self.edge_types:
            raise ValueError(f'Unknown DCG edge type: {kind}')
        rule = self.edge_types[kind]
        a, b = self.nodes[source][':LABEL'], self.nodes[target][':LABEL']
        source_ok = rule['from_types'] == 'any versioned' or a in rule['from_types'].split('|')
        target_ok = (b == a if rule['to_types'] == 'same type' else b in rule['to_types'].split('|'))
        if not source_ok or not target_ok:
            self.gap(doc, 'missing_edge', f'{kind} does not allow {a} -> {b}; proposed link retained in edge-evidence.csv', kind)
        key = (source, target, kind)
        record = {'source_id': source, 'target_id': target, 'relation': kind,
                  'exported': 'yes' if source_ok and target_ok else 'no', 'doc_id': doc,
                  'ref': (evidence or {}).get('ref', ''), 'words': (evidence or {}).get('words', '')}
        self.edge_evidence[(key, doc, record['ref'], record['words'])] = record
        if source_ok and target_ok:
            self.edges[key] = {':START_ID': source, ':END_ID': target, ':TYPE': kind,
                               **{k: str(v) for k, v in properties.items() if k in self.edge_columns and present(v)}}

    def dates(self, block):
        if not isinstance(block, dict):
            return {'status': 'provisional'}
        return {'valid_from': block['D1_start_date'],
                'valid_to': block['D2_detail'] if block['D2_end_type'] == 'fixed_date' else '',
                'status': STATUS[block['D4_status_as_read']]}

    def lifecycle_gaps(self, doc, block):
        if not isinstance(block, dict):
            return
        if block['D2_end_type'] in ('rolling_until_notice', 'until_project_complete'):
            self.gap(doc, 'missing_field', f"End condition {block['D2_end_type']}: {block['D2_detail']}", 'valid_to',
                     (block.get('D2_evidence') or {}).get('ref', ''))

    def check_cycles(self):
        parents = defaultdict(set)
        for source, target, relation in self.edges:
            if relation == 'forms_part_of':
                parents[source].add(target)
        if any(len(targets) > 1 for targets in parents.values()):
            raise ValueError('forms_part_of requires one structural parent per node; review source links')
        for relation in ('prevails_over', 'forms_part_of', 'supersedes'):
            graph = defaultdict(list)
            for source, target, kind in self.edges:
                if kind == relation:
                    graph[source].append(target)
            active, done = set(), set()
            def visit(node):
                if node in active:
                    raise ValueError(f'{relation} cycle involving {node}; correct the source forms')
                if node in done:
                    return
                active.add(node)
                for child in graph[node]:
                    visit(child)
                active.remove(node)
                done.add(node)
            for node in list(graph):
                visit(node)


def build_graph(ctx, forms, proposals, as_of=None):
    as_of = as_of or date.today().isoformat()
    out = Export()
    doc_nodes, part_nodes = {}, {}
    real_accounts = set(ctx['accounts']) - set(ctx['streams'])
    accounts = {a: out.node(stable_id('ACC', ctx['side'], a), 'account', a) for a in sorted(real_accounts)}
    relationships = {a: out.node(stable_id('REL', ctx['side'], a), 'relationship', f'{a} relationship',
                                category=ctx['side'].removesuffix('s')) for a in sorted(real_accounts)}
    sorted_accounts = defaultdict(set)
    for row in ctx['sort_rows']:
        if row['account'] in real_accounts:
            sorted_accounts[row['doc_id']].add(row['account'])

    # All real instruments before links; duplicates keep their evidence in the forms/corpus.
    for doc, form in sorted(forms.items()):
        for gap in items(form['K']):
            out.gap(doc, gap['type'], gap['description'], 'form K', gap['page'])
        b, d = form['B'], form['D']
        kind = b['B2_document_kind']
        if b['B6a_best_copy'] == 'no' and present(b['B6_duplicate_or_draft_of']):
            out.gap(doc, 'other', 'Non-best copy excluded from graph; retained in form and corpus', 'B6')
            continue
        target_type = KINDS.get(kind)
        if kind == 'project_or_programme_agreement' and items(form['H']['H1_attaches_to']):
            target_type = 'work_instrument'
        if kind == 'other_overlay' and items(form['H']['H1_attaches_to']):
            target_type = 'component'
        if kind == 'letter_or_email':
            links = items(form['H']['H1_attaches_to']) + items(form['H']['H2_replaces'])
            target_type = 'change' if links else None
        if not target_type:
            out.gap(doc, 'missing_allowed_value', f'No unambiguous node mapping for {kind}; retained in form and corpus', 'node_types')
            continue
        identity = form['A']
        node = out.node('DOC-' + doc, target_type, f"doc {doc} · {b['B1_cover_title']}", doc,
                        **out.dates(d), source_key=identity['source_path'], source_system='dcg-intake-kit')
        doc_nodes[doc] = node
        out.sources[node] = doc
        out.lifecycle_gaps(doc, d)
        if present(b['B4_signed_status']):
            out.gap(doc, 'missing_allowed_value', 'Execution and lifecycle cannot both occupy status; execution retained in form', 'status')
        if target_type in ('master', 'participation'):
            out.node(node, target_type, '', doc, paper=b['B3_whose_paper'])
        if target_type == 'master':
            scope = {'signatories_only': 'single', 'named_affiliates': 'group_referenced',
                     'all_group_companies': 'group_referenced'}.get(form['E']['E3_entities_covered'], '')
            # "Governs orders" alone does not establish pre-agreed commercial completeness.
            out.node(node, target_type, '', doc, scope=scope)
            if form['G']['G1_governs_orders'] == 'no':
                out.node(node, target_type, '', doc, commercial_completeness='no')
            elif form['G']['G1_governs_orders'] == 'yes':
                out.gap(doc, 'missing_field', 'G1 governs orders does not alone prove an order completes pre-agreed commercials', 'commercial_completeness')
            commitment = form['G']['G2_commitment_or_status']
            mapped = {'none': 'none', 'exclusivity_or_sole_supplier': 'exclusivity'}.get(commitment)
            if commitment == 'volume_or_target' and form['G']['G2_detail'] in ('volume', 'target'):
                mapped = form['G']['G2_detail']
            if mapped:
                out.node(node, target_type, '', doc, commitment=mapped)
            elif present(commitment):
                out.gap(doc, 'missing_allowed_value', f'Commitment needs disambiguation: {commitment}', 'commitment')
        for part in items(form['F']):
            name = part['F1_part_name']
            block = d if part['F4_D'] == 'inherits' else part['F4_D']
            p = out.node(stable_id('PART', doc, name), 'component', name, doc,
                         **out.dates(block), type=part['F3_part_kind'])
            part_nodes[(doc, name)] = p
            out.sources[p] = doc
            out.edge(p, node, 'forms_part_of', doc, part['F1_evidence'])
            out.lifecycle_gaps(doc, block)

    for doc, form in sorted(forms.items()):
        if doc not in doc_nodes:
            continue
        node = doc_nodes[doc]
        for field, ours in [('C1_their_entities', False), ('C2_our_entities', True)]:
            entities = items(form['C'][field])
            if not entities:
                unknown = out.node(stable_id('ENTITY', doc, field, 'unknown'), 'legal_entity',
                                   f"Unresolved {'our' if ours else 'their'} party, doc {doc}", doc,
                                   is_ours=str(ours).lower(), status='provisional')
                out.edge(node, unknown, 'party_to', doc)
                out.gap(doc, 'missing_field', f'{field} not found; provisional party needs review', field)
            for entity in entities:
                name = entity['name_as_printed']
                mapping = ctx['entity_by_name'].get(norm_name(name), {}) if not ours else {}
                resolved = mapping.get('account') in accounts and mapping.get('confidence') in ('sure', 'fairly sure')
                entity_id = out.node(stable_id('ENTITY', name), 'legal_entity', name, doc,
                                     is_ours=str(ours).lower(), **({} if ours or resolved else {'status': 'provisional'}))
                evidence = form['C'].get(field[:2] + '_evidence')
                if entity['role'] == 'signatory':
                    out.edge(node, entity_id, 'party_to', doc, evidence)
                elif entity['role'] == 'guarantor':
                    out.edge(node, entity_id, 'guaranteed_by', doc, evidence)
                if ours:
                    continue
                account = mapping.get('account', '')
                out.matches[(doc, entity_id, account)] = {
                    'doc_id': doc, 'entity_id': entity_id, 'name_as_printed': name,
                    'account_id': accounts.get(account, ''), 'account': account,
                    'basis': mapping.get('basis', ''), 'confidence': mapping.get('confidence', ''),
                    'decided_by': mapping.get('decided_by', ''), 'note': mapping.get('note', ''),
                    'role': entity['role'],
                }
                if resolved:
                    # Account association is not proof of legal ownership of that account.
                    out.gap(doc, 'missing_edge', 'Entity-to-ERP association has no DCG edge or basis column; retained in entity-account-links.csv', 'belongs_to')
                else:
                    out.gap(doc, 'missing_field', f'Unresolved account for entity {name}', 'legal_entity')
        if out.nodes[node][':LABEL'] == 'order':
            for account in sorted_accounts[doc]:
                out.edge(node, accounts[account], 'ordered_by', doc, form['G'].get('G1_evidence'))

        def target_for(link, relation):
            target_doc = link['doc_id'].removeprefix('doc ').zfill(3)
            if target_doc in doc_nodes:
                return doc_nodes[target_doc]
            target_type = out.nodes[node][':LABEL'] if relation == 'supersedes' else 'master'
            target_id = ('DOC-' + target_doc if target_doc in ctx['inventory']
                         else stable_id('MISSING', doc, link['as_printed']))
            out.gap(doc, 'missing_field', f"Linked document not extracted or not in pile: {link['as_printed']}", relation)
            return out.node(target_id, target_type, link['as_printed'], doc, status='provisional')

        for key, ev_key in [('H1_attaches_to', 'H1_evidence'), ('H2_replaces', 'H2_evidence')]:
            for link in items(form['H'][key]):
                relation = link['relation']
                target = target_for(link, relation)
                out.edge(node, target, relation, doc, form['H'][ev_key], effective_from=form['D']['D1_start_date'])
        ending = form['D']['D3_ended_evidence']
        if ending in ('termination_letter', 'replaced_by'):
            description = form['D']['D3_detail']
            match = re.fullmatch(r'(?:doc\s+)?(\d{3,})', description.strip())
            source_doc = match.group(1) if match else None
            source = doc_nodes.get(source_doc)
            relation = 'terminates' if ending == 'termination_letter' else 'supersedes'
            if source is None:
                source_type = 'change' if relation == 'terminates' else out.nodes[node][':LABEL']
                source_id = ('DOC-' + source_doc if source_doc in ctx['inventory']
                             else stable_id('MISSING', doc, description))
                source = out.node(source_id, source_type, description, doc, status='provisional')
                out.gap(doc, 'missing_field', f'Ending instrument not extracted or not in pile: {description}', 'D3')
            out.edge(source, node, relation, doc, form['D']['D3_evidence'])
        for missing in items(form['H']['H3_refers_to_missing']):
            p = out.node(stable_id('MISSING', doc, missing['as_printed']), 'master', missing['as_printed'], doc,
                         status='provisional')
            out.edge(node, p, 'references', doc, form['H']['H3_evidence'])
            out.gap(doc, 'missing_field', f"Referenced document missing; placeholder type provisional: {missing['as_printed']}", 'H3', missing['where'])
        for part in items(form['F']):
            winner = part_nodes[(doc, part['F1_part_name'])]
            precedence = part['F6_internal_precedence']
            if isinstance(precedence, dict):
                out.node(winner, 'component', '', doc, precedence=precedence['words'])
                for name in precedence['wins_over']:
                    loser = part_nodes.get((doc, name))
                    if not loser:
                        raise ValueError(f'doc {doc}: precedence names missing part {name!r}')
                    out.edge(winner, loser, 'prevails_over', doc, part['F6_evidence'])
            scope = form['E'] if part['F5_E'] == 'inherits' else part['F5_E']
            if isinstance(scope, dict) and scope['E2_territory'] == 'single_country':
                country = scope['E2_detail']
                c = out.node(stable_id('COUNTRY', country), 'country', country)
                out.edge(winner, c, 'covers_territory', doc, scope['E2_evidence'])
        for topic in items(form['I']):
            if topic['reading'] in ('silent', 'not_found'):
                out.gap(doc, 'missing_field', f"Topic {topic['topic']} is {topic['reading']}; no source clause to attach a term fact", 'has_clause')
                continue
            parent = part_nodes.get((doc, topic['part']), node)
            clause = out.node(stable_id('CLAUSE', parent, topic['page_or_clause']), 'clause', topic['page_or_clause'], doc,
                              eid=f"{parent}#{topic['page_or_clause']}", sali_tag='pending')
            fact = out.node(stable_id('TERM', clause, topic['topic']), 'term_fact', topic['topic'], doc,
                            type=topic['topic'], value=topic['reading'], sali_tag='pending',
                            valid_from=out.nodes[parent].get('valid_from', ''), valid_to=out.nodes[parent].get('valid_to', ''))
            ev = {'ref': topic['page_or_clause'], 'words': topic['words']}
            out.edge(parent, clause, 'has_clause', doc, ev)
            out.edge(clause, fact, 'has_term', doc, ev)
        for gap in items(form['K']):
            out.gap(doc, gap['type'], gap['description'], 'form K', gap['page'])

    # Later evidence settles lifecycle without rewriting what the older form says.
    for (source, target, relation), edge in out.edges.items():
        if relation not in ('supersedes', 'terminates'):
            continue
        effective = edge.get('effective_from') or out.nodes[source].get('valid_from')
        if effective and effective <= as_of:
            out.nodes[target]['status'] = 'superseded' if relation == 'supersedes' else 'terminated'
        elif not effective:
            out.gap(out.sources.get(target, ''), 'missing_field', f'{relation} has no effective date; lifecycle needs review', relation)
    for (source, target, relation) in out.edges:
        if relation == 'forms_part_of' and out.nodes[target].get('status') in ('superseded', 'terminated'):
            if out.nodes[source].get('status') in ('active', 'provisional'):
                out.nodes[source]['status'] = out.nodes[target]['status']

    # Family proposals are on actual roots, not an invented "tree" node type.
    root_families = defaultdict(list)
    for account, rows in proposals.items():
        for proposal in rows:
            members = set(proposal['doc_ids'])
            roots = [doc_nodes[d] for d in sorted(members) if d in doc_nodes and not any(
                x['doc_id'].removeprefix('doc ').zfill(3) in members for x in items(forms[d]['H']['H1_attaches_to']))]
            for node in roots:
                confidence = {'sure': '1.00', 'fairly_sure': '0.67', 'not_sure': '0.33', 'no_family_fits': '0.00'}[proposal['confidence']]
                if present(proposal['family']):
                    root_families[node].append((proposal['family'], confidence))
                if proposal['confidence'] == 'no_family_fits':
                    out.gap(out.sources[node], 'no_family_fits', proposal['structural_evidence'], 'family')
    for node, choices in root_families.items():
        if len({family for family, _ in choices}) > 1:
            out.gap(out.sources[node], 'family_misfire', 'Shared root has different family proposals; see tree-proposals.csv', 'family')
        else:
            out.node(node, out.nodes[node][':LABEL'], '', out.sources[node], family=choices[0][0],
                     confidence=min(confidence for _, confidence in choices))
    out.check_cycles()
    return out


def load_forms(ctx):
    forms, warnings = {}, []
    errors = []
    for path in sorted((WORK / 'forms').glob('*.json')):
        try:
            form = load_form(path)
            issues = validate_form(form, WORK / 'text' / f'{path.stem}.txt')
            if not issues and form['A']['doc_id'] != path.stem:
                issues.append('A.doc_id differs from the form filename')
            if not issues and path.stem not in ctx['inventory']:
                issues.append('document is absent from the inventory')
            if not issues and form['A']['sha256'] != ctx['inventory'][path.stem]['sha256']:
                issues.append('A.sha256 differs from inventory; re-extract this changed document')
            if not issues and form['A']['side'] != ctx['side']:
                issues.append('A.side differs from the ERP run; re-extract this document')
            matched = {r['account'] for r in ctx['sort_rows'] if r['doc_id'] == path.stem}
            if not issues and form['A']['account'] not in matched:
                issues.append('A.account differs from current sorting; re-extract after account corrections')
            errors += [f'doc {path.stem}: {issue}' for issue in issues]
            if not issues:
                forms[path.stem] = form
                warnings.extend(f'doc {path.stem}: {x}' for x in evidence_warnings(form, WORK / 'text' / f'{path.stem}.txt'))
        except (ValueError, OSError) as err:
            errors.append(f'{path.name}: {err}')
    if errors:
        raise ValueError('Forms failed validation:\n' + '\n'.join(errors))
    if not forms:
        raise ValueError('No forms found. Run /extract first.')
    return forms, warnings


def load_proposals(ctx, settled):
    families = {row['code']: row for row in read_csv(DCG / 'families.csv')}
    overlays = {row['code'] for row in read_csv(DCG / 'overlays.csv')}
    proposals = {}
    for account, (placements, _) in settled.items():
        path = WORK / 'trees' / f'{safe_folder_name(account)}.json'
        if not path.exists():
            continue
        data = read_json(path)
        if not isinstance(data, dict) or data.get('account') != account or not isinstance(data.get('trees'), list):
            raise ValueError(f'Invalid proposal file for {account}')
        seen = set()
        for row in data['trees']:
            required = {'tree', 'family', 'confidence', 'structural_evidence', 'doc_ids', 'overlays'}
            if not isinstance(row, dict) or not required <= row.keys():
                raise ValueError(f'{account}: each tree proposal requires {sorted(required)}')
            if row['tree'] in seen:
                raise ValueError(f'{account}: duplicate tree proposal {row["tree"]}')
            seen.add(row['tree'])
            if row['confidence'] not in ('sure', 'fairly_sure', 'not_sure', 'no_family_fits'):
                raise ValueError(f'{account}: invalid family confidence')
            if row['family'] not in families and row['family'] not in ('not_found', 'none'):
                raise ValueError(f'{account}: unknown family {row["family"]}')
            if row['family'] in families and families[row['family']]['category'].lower() != ctx['side']:
                raise ValueError(f'{account}: family is for a different side')
            if not isinstance(row['overlays'], list) or not set(row['overlays']) <= overlays:
                raise ValueError(f'{account}: invalid overlays')
            if not isinstance(row['structural_evidence'], str) or not row['structural_evidence'].strip():
                raise ValueError(f'{account}: structural evidence is required')
            expected = {d for d, p in placements.items() if p['tree'] == row['tree']}
            if not isinstance(row['doc_ids'], list) or set(row['doc_ids']) != expected or not expected:
                raise ValueError(f'{account}: stale or incomplete membership for {row["tree"]}; run /map again')
        proposals[account] = data['trees']
    return proposals


def md_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def write_trees(ctx, proposals):
    tree_rows = []
    family_by_tree = {}
    for account, proposals_for_account in sorted(proposals.items()):
        lines = [f'# Trees — {account}', '', '| tree | family | confidence | overlays | docs | structural evidence |',
                 '| --- | --- | --- | --- | --- | --- |']
        for row in proposals_for_account:
            tree_rows.append({'account': account, **{k: ' | '.join(v) if isinstance(v, list) else v for k, v in row.items()}})
            family_by_tree[(account, row['tree'])] = row
            lines.append('| ' + ' | '.join(md_cell(x) for x in [row['tree'], row['family'], row['confidence'],
                         ', '.join(row['overlays']), ', '.join('doc ' + d for d in row['doc_ids']), row['structural_evidence']]) + ' |')
        write_text(account_folder(ctx['side'], account) / 'TREES.md', '\n'.join(lines) + '\n')
    return tree_rows, family_by_tree


def write_reports(ctx, settled, forms, proposals, out, warnings):
    destination = OUT / 'graph'
    write_csv(destination / 'nodes.csv', [out.nodes[k] for k in sorted(out.nodes)], out.node_columns)
    write_csv(destination / 'edges.csv', [out.edges[k] for k in sorted(out.edges)], out.edge_columns)
    write_csv(destination / 'node-properties.csv', [out.node_properties[k] for k in sorted(out.node_properties)],
              ['node_id', 'property', 'value'])
    write_csv(destination / 'edge-evidence.csv', [out.edge_evidence[k] for k in sorted(out.edge_evidence)],
              ['source_id', 'target_id', 'relation', 'exported', 'doc_id', 'ref', 'words'])
    write_csv(destination / 'entity-account-links.csv', [out.matches[k] for k in sorted(out.matches)],
              ['doc_id', 'entity_id', 'name_as_printed', 'account_id', 'account', 'basis', 'confidence', 'decided_by', 'note', 'role'])
    tree_rows, family_by_tree = write_trees(ctx, proposals)
    write_csv(destination / 'tree-proposals.csv', tree_rows,
              ['account', 'tree', 'family', 'confidence', 'structural_evidence', 'doc_ids', 'overlays'])
    corpus = build_all_rows(ctx, {a: s for a, (s, _) in settled.items()})
    columns = list(CORPUS_COLUMNS)
    health = defaultdict(Counter)
    for row in corpus:
        form = forms.get(row['doc_id'])
        if form:
            for key, value in flatten({k: v for k, v in form.items() if k not in ('A', 'L')}, 'form').items():
                row[key] = value
                if key not in columns:
                    columns.append(key)
        proposal = family_by_tree.get((row['account'], row['tree']), {})
        row['dcg_family'] = proposal.get('family', 'not_found')
        row['dcg_family_confidence'] = proposal.get('confidence', 'not_found')
    columns += ['dcg_family', 'dcg_family_confidence']
    # Rebuild from sources; human reviewer annotations belong in corrections.csv.
    write_csv(OUT / ctx['side'] / 'CORPUS.csv', corpus, columns)
    for account in settled:
        write_csv(account_folder(ctx['side'], account) / 'documents.csv',
                  [r for r in corpus if r['account'] == account], columns)
    for form in forms.values():
        for key, value in health_fields({k: v for k, v in form.items() if k not in ('A', 'L')}):
            state = 'not_found' if value in ('', None, 'not_found') else 'not_sure' if value in ('unknown', 'not_sure', 'signature_page_missing') else 'answered'
            health[key][state] += 1
    lines = ['# Form health', '', f'{len(forms)} forms validated. Image evidence still requires visual review.', '',
             '| field | answered | not_found | not_sure |', '| --- | --- | --- | --- |']
    lines += [f'| {md_cell(k)} | {v["answered"]} | {v["not_found"]} | {v["not_sure"]} |' for k, v in sorted(health.items())]
    lines += ['', '## Evidence checks', ''] + [f'- {md_cell(w)}' for w in sorted(set(warnings))]
    missing = sorted(r['doc_id'] for r in ctx['inventory'].values()
                     if r['doc_id'] != 'erp' and r['readable'] == 'yes' and r['doc_id'] not in forms)
    lines += ['', 'Not extracted: ' + (', '.join('doc ' + d for d in missing) or 'none'), '']
    write_text(OUT / 'FORM-HEALTH.md', '\n'.join(lines))
    merged = defaultdict(set)
    suggestions = defaultdict(set)
    for kind, description, place, doc, ref in out.gaps:
        merged[(kind, description, place)].add('doc ' + doc if doc else 'export')
    # Mapper tables use the exact five columns in stage2/didnt-fit.md.
    for path in sorted((WORK / 'didnt-fit').glob('*.md')):
        for line in path.read_text(encoding='utf-8').splitlines():
            cells = [c.strip() for c in re.split(r'(?<!\\)\|', line.strip().strip('|'))]
            if len(cells) == 5 and cells[0] in ('missing_field', 'family_misfire', 'no_family_fits', 'missing_edge', 'missing_allowed_value', 'other'):
                merged[(cells[0], cells[1], cells[2])].update(re.findall(r'doc \d+', cells[3]) or [path.stem])
                suggestions[(cells[0], cells[1], cells[2])].add(cells[4])
    lines = ['# Didn’t fit the standard', '', 'The DCG registries are unchanged. Companion tables preserve facts the sample headers cannot carry.', '',
             '| documents | type | what did not fit | DCG place | proof | suggested change |', '| --- | --- | --- | --- | --- | --- |']
    for (kind, description, place), docs in sorted(merged.items(), key=lambda x: (-len(x[1]), x[0])):
        lines.append('| ' + ' | '.join(md_cell(x) for x in [len(docs), kind, description, place, ', '.join(sorted(docs)),
                                                          '; '.join(sorted(suggestions[(kind, description, place)]))]) + ' |')
    write_text(OUT / 'DIDNT-FIT.md', '\n'.join(lines) + '\n')
    write_text(destination / 'README.md', '# Graph export\n\nnodes.csv and edges.csv use the unchanged DCG sample headers. '
               'Load those as graph rows. Other CSVs are companion audit tables, not DCG edges. '
               'An exported=no row records a link the registry cannot represent. '
               'Entity-account associations do not assert legal ownership. Family proposals live on actual roots '
               'where unambiguous and in tree-proposals.csv for every account context. '
               'Blank fields mean not represented or not found, never a negative answer.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true')
    group.add_argument('--account')
    parser.add_argument('--as-of', default=date.today().isoformat(), help='lifecycle date, YYYY-MM-DD (default today)')
    args = parser.parse_args()
    try:
        ctx = load_context()
        if args.account and args.account not in ctx['accounts']:
            raise ValueError('Account must be spelled exactly as an ERP row')
        settled = settled_for_all_accounts(ctx)
        forms, warnings = load_forms(ctx)
        if args.account:
            if args.account not in settled:
                raise ValueError('Account has no placements to map')
            proposals = load_proposals(ctx, {args.account: settled[args.account]})
            if args.account not in proposals:
                raise ValueError('Account has no tree proposals; the mapper must write them first')
            write_trees(ctx, proposals)
            say(f'{args.account}: validated proposals and written TREES.md. Run --all after all mappers finish.')
            return 0
        proposals = load_proposals(ctx, settled)
        date.fromisoformat(args.as_of)
        result = build_graph(ctx, forms, proposals, args.as_of)
        write_reports(ctx, settled, forms, proposals, result, warnings)
    except (ValueError, OSError, KeyError, TypeError) as err:
        fail(str(err))
    say(f'Graph: {len(result.nodes)} nodes, {len(result.edges)} edges; {len(forms)} validated forms. '
        'Written out/graph/, TREES.md, CORPUS.csv, FORM-HEALTH.md and DIDNT-FIT.md.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
