"""Replay the entity map: python scripts/sort.py [--force]

The model decides which company name belongs to which ERP account and writes those decisions
to inputs/entity-map.csv (the /match skill). This script decides nothing. It reads the map, the
ERP record, the inventory and the sort cards, then:

- creates one folder per ERP account under out/<side>/ (streams get a README only),
- copies every document with a card into out/<side>/<account>/_to-judge/ (or into a holding
  folder: _not-on-the-list, _not-sure, _no-name-found, grouped by the company name found),
- writes work/logs/sort.csv, one row per (document, target),
- prints what needs the user's decision.

Copies are named by kit_common.filed_name() from the card and the target folder; the originals
and work/files/<id>.<ext> keep their own names.

Copy, never move. Re-runs are deterministic: stale copies from an earlier run are removed.
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import (  # noqa: E402
    CONFIDENCE_RANK, HOLDING_FOLDERS, OUT, SORT_LOG_COLUMNS, SORT_LOG_CSV, TO_JUDGE, WORK, WORK_FILES,
    _header_of,
    account_folder, apply_corrections_to_card, counterparty_for, load_corrections, doc_label,
    entity_row_for, erp_account_names, fail, filed_name, group_key, join_multi, load_all_cards, load_entity_map,
    load_erp, load_inventory, load_our_entities, load_sort_log, names_from_card, naming_from_card, norm_name, rel,
    WORK_CARDS, WORK_PLACEMENTS, read_csv, read_json, split_multi,
    safe_folder_name, say, stream_map, unique_filed_name, warn, write_csv, write_text,
)


def copy_if_needed(source, target, produced, force):
    """Copy source to target unless it is already there. Records the target as produced."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if force or not target.exists():
        shutil.copyfile(source, target)
    produced.add(target.resolve())


def remove_stale_copies(side, accounts, produced, selected=None):
    """Delete files in _to-judge and the holding folders that this run did not produce."""
    folders = [account_folder(side, a) / TO_JUDGE for a in accounts]
    folders += [OUT / side / h for h in HOLDING_FOLDERS]
    removed = 0
    for folder in folders:
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if selected is not None and path.name.split(" ", 1)[0].split(".", 1)[0] not in selected:
                continue
            if path.is_file() and path.resolve() not in produced:
                path.unlink()
                removed += 1
        # drop empty sub-folders left behind (holding folders are grouped by company name)
        for path in sorted(folder.rglob("*"), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
        if not any(folder.iterdir()) and folder.name == TO_JUDGE:
            folder.rmdir()
    if removed:
        say(f"removed {removed} stale copies from an earlier run")


def archive_filing_report(side, inventory, cards):
    """Retain the whole cheap report before starting a full-card matching pass.

    Cheap output has extra holding tables and copies that a normal full replay does
    not own. Keeping them in the active output would mix two different read stages.
    Validate the transition before changing any generated files; an ordinary full
    replay keeps its established behavior.
    """
    corpus = OUT / side / "CORPUS.csv"
    if not corpus.is_file():
        return
    if "read_status" not in _header_of(corpus) and not any(
            r.get('analysis_stage') == 'filing only' for r in read_csv(corpus)):
        return
    readable_cards = [row for row in inventory
                      if row.get("doc_id") != "erp" and row.get("readable") == "yes"
                      and row.get("doc_id") in cards]
    if not readable_cards:
        fail("The current report is filing only and no full cards are available. "
             "Run /read or /deep-dive before /match. The filing report is unchanged.")
    for row in readable_cards:
        source = WORK_FILES / f"{row['doc_id']}.{row.get('ext', '')}"
        if not source.is_file():
            fail(f"doc {row['doc_id']}: {rel(source)} is missing; run /prepare again. "
                 "The filing report is unchanged.")
    history = WORK / "history"
    history.mkdir(parents=True, exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix="analysis-transition-", dir=history))
    OUT.rename(archive / "out")
    say(f"Previous filing report retained at {rel(archive / 'out')} before full matching.")


def decide_targets(names, entity_by_name, erp_names_by_norm, streams):
    """Where a document with these company names goes.

    Returns (kind, targets, undecided) where kind is 'account', '_not-sure', '_not-on-the-list'
    or '_no-name-found'; targets is a list of dicts {target, basis, confidence, names, note};
    undecided is the list of names that still need the user's decision.
    """
    if not names:
        return "_no-name-found", [{"target": "_no-name-found", "basis": "", "confidence": "",
                                   "names": [], "note": "no company name found on the card"}], []

    per_account = {}   # account -> list of (rank, name, row)
    not_sure = []      # (name, row or None)
    not_listed = []    # (name, row or None)
    undecided = []
    for name in names:
        row = entity_row_for(entity_by_name, name)
        if row is None:
            not_listed.append((name, None))
            undecided.append(name)
            continue
        account_text = row.get("account", "").strip()
        confidence = row.get("confidence", "").strip().lower()
        if row.get('basis') == 'known group' and confidence == 'sure':
            row = {**row, 'confidence': 'fairly sure'}
            confidence = 'fairly sure'
            warn(f"entity map: {name!r}: known group cannot be better than fairly sure")
        if account_text not in ('_not-on-the-list', '_not-sure') and row.get('basis') not in ('same name', 'in the document', 'known group'):
            not_sure.append((name, row))
            undecided.append(name)
            continue
        if account_text == "_not-sure":
            not_sure.append((name, row))
            undecided.append(name)
            continue
        if account_text == "_not-on-the-list":
            not_listed.append((name, row))
            continue
        account = erp_names_by_norm.get(norm_name(account_text))
        if account is None:
            warn(f"entity map: {name!r} is mapped to {account_text!r}, which is not an ERP row; "
                 "treated as no decision")
            not_listed.append((name, None))
            undecided.append(name)
            continue
        if account in streams:
            account = streams[account][0]
        # Rule A1: an explicitly named ERP stream has its own filing destination.
        # A user-confirmed parent mapping still wins over this automatic exception.
        printed_account = erp_names_by_norm.get(norm_name(name))
        if printed_account and printed_account not in streams and row.get("decided_by") != "user":
            if account != printed_account:
                row = {**row, 'note': 'Rule A1: explicitly named ERP stream retains its own folder. '
                                      + row.get('note', '')}
            account = printed_account
        if confidence == "not sure":
            not_sure.append((name, row))
            undecided.append(name)
            continue
        rank = CONFIDENCE_RANK.get(confidence, 0)
        if rank == 0:
            warn(f"entity map: {name!r} has confidence {confidence!r}; treated as 'not sure'")
            not_sure.append((name, row))
            undecided.append(name)
            continue
        per_account.setdefault(account, []).append((rank, name, row))

    if per_account:
        targets = []
        for account in per_account:
            matches = sorted(per_account[account], key=lambda m: -m[0])
            best_rank, best_name, best_row = matches[0]
            note_bits = [f"matched on {best_name!r}"]
            others = [m[1] for m in matches[1:]]
            if others:
                note_bits.append("also: " + ", ".join(repr(o) for o in others))
            if best_row.get("note"):
                note_bits.append(best_row["note"])
            targets.append({"target": account, "basis": best_row.get("basis", ""),
                            "confidence": best_row.get("confidence", ""), "names": [best_name] + others,
                            "note": "; ".join(note_bits)})
        return "account", targets, undecided

    if not_sure:
        targets = []
        for name, row in not_sure:
            candidate = row.get("account", "") if row else ""
            note = row.get("note", "") if row else ""
            if candidate and candidate != "_not-sure":
                note = f"candidate: {candidate}" + (f"; {note}" if note else "")
            targets.append({"target": f"_not-sure/{name}", "basis": row.get("basis", "") if row else "",
                            "confidence": row.get("confidence", "") if row else "", "names": [name],
                            "note": note or "not sure; decide in inputs/entity-map.csv"})
        return "_not-sure", targets, undecided

    targets = []
    for name, row in not_listed:
        if row is None:
            note = "no decision in entity map"
        else:
            note = row.get("note", "") or "not one of the accounts on the list"
        targets.append({"target": f"_not-on-the-list/{name}", "basis": row.get("basis", "") if row else "",
                        "confidence": row.get("confidence", "") if row else "", "names": [name], "note": note})
    return "_not-on-the-list", targets, undecided


def group_holding_targets(targets, holding_names):
    """One holding folder per company, however the name is abbreviated.

    'Brenlow Dockyard Svcs Ltd' and 'Brenlow Dockyard Services Limited' share a group key, so
    the second spelling is filed under the first one seen and the user decides the name once.
    Duplicate targets inside one document are dropped, so a document is copied only once.
    """
    result = []
    seen = set()
    for target in targets:
        name = target["target"]
        if "/" in name and name.split("/", 1)[0] in HOLDING_FOLDERS:
            folder, printed = name.split("/", 1)
            display = holding_names.setdefault(group_key(printed), printed)
            if display != printed:
                target = {**target, "target": f"{folder}/{display}",
                          "note": (target.get("note", "") + f"; printed as {printed!r}").lstrip("; ")}
            else:
                target = {**target, "target": f"{folder}/{display}"}
        if target["target"] in seen:
            continue
        seen.add(target["target"])
        result.append(target)
    return result


def main():
    parser = argparse.ArgumentParser(description="Replay inputs/entity-map.csv into account folders.")
    parser.add_argument("--force", action="store_true", help="copy again even if the copy exists")
    parser.add_argument("--account", help="rematch only documents already filed to this ERP account")
    parser.add_argument("--top", action="store_true",
                        help="rematch only the documents in work/top/scope.json (the top accounts' documents "
                             "and the unfiled ones); every other filing row is kept")
    args = parser.parse_args()
    if args.account and args.top:
        fail("Use --account or --top, not both.")

    if (WORK / "review-table/active.json").is_file():
        fail("Review_Table is the analysis index. Use /analyse and review_table.py --assign; "
             "native card matching would overwrite the table account decisions.")

    erp = load_erp()
    side = erp.get("side")
    if not side:
        fail("work/erp.json has no side. Re-run /prepare with --side customers|suppliers.")
    inventory = load_inventory()
    cards = load_all_cards()
    corrections = load_corrections()
    cards = {d: apply_corrections_to_card(c, corrections) for d, c in cards.items()}
    entity_by_name, map_rows = load_entity_map()
    our_names = load_our_entities()
    if not map_rows:
        warn("inputs/entity-map.csv is missing or empty: every name will need a decision")

    erp_names = erp_account_names(erp)
    erp_names_by_norm = {norm_name(n): n for n in erp_names}
    previous = load_sort_log()
    selected = None
    focus = set()
    if args.account:
        if args.account not in erp_names:
            fail(f"{args.account!r} is not an ERP account")
        focus = {args.account}
        selected = {r['doc_id'] for r in previous if r.get('account') == args.account}
        if not selected:
            fail("This account has no filing rows. Run /sort first, or use /analyse all.")
        missing = {d for d in selected if d not in cards or not (WORK_CARDS / f'{d}.md').is_file()}
        if missing:
            fail("Account analysis is incomplete; missing full cards: " + ", ".join(sorted(missing)))
    if args.top:
        scope = read_json(WORK / "top" / "scope.json")
        if not scope or not scope.get("docs"):
            fail("No top scope. Run python scripts/top.py --scope first.")
        focus = set(scope.get("accounts", []))
        selected = set(scope["docs"])
        missing = {d for d in selected if d not in cards or not (WORK_CARDS / f'{d}.md').is_file()}
        if missing:
            warn("top scope: no full card yet for " + ", ".join(sorted(missing)) + "; their filing rows are kept")
            selected -= missing
        if not selected:
            fail("No document in the top scope has a full card yet. Run /read top first.")
    if selected is not None:
        for row in inventory:
            if row.get('doc_id') in selected and not (WORK_FILES / f"{row['doc_id']}.{row.get('ext', '')}").is_file():
                fail(f"doc {row['doc_id']}: prepared copy missing; run /prepare again")
    named = [n for c in cards.values() for n in names_from_card(c, our_names)]
    named += [n for r in previous if r['doc_id'] not in cards
              for n in split_multi(r.get('companies_found', ''))]
    streams = stream_map(erp, entity_by_name, named)
    main_accounts = [n for n in erp_names if n not in streams]

    incomplete = any(r.get('readable') == 'yes' and r.get('doc_id') != 'erp'
                     and r.get('doc_id') not in cards for r in inventory)
    if selected is None and not incomplete:
        archive_filing_report(side, inventory, cards)
    elif selected is None and not cards:
        archive_filing_report(side, inventory, cards)  # fail before replacing a filing-only report

    # 2. streams: a README only
    for stream, (main, row) in streams.items():
        if selected is not None and stream != args.account:
            continue
        folder = account_folder(side, stream)
        folder.mkdir(parents=True, exist_ok=True)
        write_text(folder / "README.md",
                   f'This ERP row ("{stream}") is treated as a stream of "{main}": {row.get("basis", "")}, '
                   f'{row.get("confidence", "")}, decided by {row.get("decided_by", "")}.\n'
                   f"Its documents are filed under ../{safe_folder_name(main)}/. Nothing else is written here.\n")

    # 3. one folder per account
    for account in main_accounts:
        folder = account_folder(side, account)
        folder.mkdir(parents=True, exist_ok=True)
        if folder.name != account:
            warn(f"account {account!r} uses folder name {folder.name!r} (characters not allowed in folder names replaced)")

    # 4. every document
    produced = set()
    used_names = {}
    log_rows = [r for r in previous if r['doc_id'] not in selected] if selected is not None else []
    holding = {h: {} for h in HOLDING_FOLDERS}  # holding folder -> {name: [doc ids]}
    undecided_names = {}
    holding_names = {}  # group key -> the printed name that names the holding folder
    no_card = []
    unreadable = []

    for row in inventory:
        doc_id = row.get("doc_id", "")
        if doc_id == "erp":
            continue
        if selected is not None and doc_id not in selected:
            continue
        original = row.get("original_path", "")
        if row.get("readable") != "yes":
            unreadable.append(doc_id)
            log_rows.append({"doc_id": doc_id, "original_path": original, "companies_found": "",
                             "account": "_unreadable", "basis": "", "confidence": "",
                             "note": row.get("note", "not readable by the kit")})
            continue
        card = cards.get(doc_id)
        if card is None:
            no_card.append(doc_id)
            retained = [r for r in previous if r['doc_id'] == doc_id]
            if retained:
                log_rows.extend(retained)
                continue
            log_rows.append({"doc_id": doc_id, "original_path": original, "companies_found": "",
                             "account": "_no-card", "basis": "", "confidence": "", "note": "no card yet; run /read"})
            continue
        source = WORK_FILES / f"{doc_id}.{row.get('ext', '')}"
        if not source.exists():
            warn(f"doc {doc_id}: {rel(source)} is missing; run /prepare again")
        names = names_from_card(card, our_names)
        naming = naming_from_card(card)
        kind, targets, undecided = decide_targets(names, entity_by_name, erp_names_by_norm, streams)
        targets = group_holding_targets(targets, holding_names)
        for name in undecided:
            undecided_names.setdefault(holding_names.setdefault(group_key(name), name), []).append(doc_id)
        account_targets = [t["target"] for t in targets] if kind == "account" else []
        for t in targets:
            note = t["note"]
            if kind == "account":
                others = [a for a in account_targets if a != t["target"]]
                if others:
                    note = f"shared with: {', '.join(others)}; " + note
                folder_path = account_folder(side, t["target"]) / TO_JUDGE
            elif kind == "_no-name-found":
                holding["_no-name-found"].setdefault("(no name)", []).append(doc_id)
                folder_path = OUT / side / "_no-name-found"
            else:
                folder, name = t["target"].split("/", 1)
                holding[folder].setdefault(name, []).append(doc_id)
                folder_path = OUT / side / folder / safe_folder_name(name)
            filed = filed_name(doc_id, row.get("ext", ""), counterparty=counterparty_for(t["target"], names),
                               pages=row.get("pages", ""), unresolved=kind == "_no-name-found", **naming)
            target_path = folder_path / unique_filed_name(filed, used_names.setdefault(folder_path, set()))
            if source.exists():
                copy_if_needed(source, target_path, produced, args.force)
            log_rows.append({"doc_id": doc_id, "original_path": original, "companies_found": join_multi(names),
                             "account": t["target"], "basis": t["basis"], "confidence": t["confidence"],
                             "note": note})

    remove_stale_copies(side, main_accounts, produced, selected if selected is not None else set(cards))

    if selected is not None:
        # A changed shared document also makes the other account's judgment stale.
        # Keep its source copies and filing rows; /report marks it awaiting judgment.
        affected = {r['account'] for r in previous + log_rows if r['doc_id'] in selected}
        archive = None
        for account in affected & set(erp_names):
            for path in list(WORK_PLACEMENTS.glob('*')):
                if (path.is_file() and path.suffix in ('.csv', '.md')
                        and safe_folder_name(path.stem) == safe_folder_name(account)):
                    if archive is None:
                        history = WORK / 'history' / 'scoped-placements'
                        history.mkdir(parents=True, exist_ok=True)
                        archive = Path(tempfile.mkdtemp(prefix='previous-', dir=history))
                    path.rename(archive / path.name)
            if account not in focus:
                say(f"{account}: shared or reassigned document changed; judgment must be refreshed explicitly.")

    # 5. the log and the summary
    log_rows.sort(key=lambda r: (r["doc_id"], r["account"]))
    write_csv(SORT_LOG_CSV, log_rows, SORT_LOG_COLUMNS)

    say(f"Side: {side}. Accounts: {len(main_accounts)}" + (f", streams: {len(streams)}" if streams else ""))
    for account in main_accounts:
        docs = [r['doc_id'] for r in log_rows if r['account'] == account]
        say(f"  {account}: " + (", ".join(doc_label(d) for d in docs) if docs else "(no documents)"))
    for stream, (main, _) in streams.items():
        say(f"  stream: {stream!r} treated as one with {main!r} (README only)")
    for folder in HOLDING_FOLDERS:
        groups = holding[folder]
        if not groups:
            continue
        say(f"  {folder}:")
        for name, docs in groups.items():
            say(f"    {name}: " + ", ".join(doc_label(d) for d in docs))
    if no_card:
        say("  no card yet (run /read): " + ", ".join(doc_label(d) for d in no_card))
    if unreadable:
        say("  not readable by the kit: " + ", ".join(doc_label(d) for d in unreadable))
    say("")
    if undecided_names:
        say("Names that need your decision (add or edit a row in inputs/entity-map.csv with decided_by = user, then run /match again):")
        for name, docs in undecided_names.items():
            row = entity_row_for(entity_by_name, name)
            why = "no entity-map row" if row is None else f"mapped to {row.get('account', '')!r} with confidence {row.get('confidence', '')!r}"
            say(f"  - {name}  ({why}; in " + ", ".join(doc_label(d) for d in docs) + ")")
    else:
        say("Names that need your decision: none")
    say(f"Written: {rel(SORT_LOG_CSV)} ({len(log_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
