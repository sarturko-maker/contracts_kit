"""Top accounts: the ERP_Top control file and the reading scope it selects.

    python scripts/top.py --register [FILE] [--account-column NAME]
    python scripts/top.py --scope [--filed-only]
    python scripts/top.py --accounts
    python scripts/top.py --status

ERP_Top is a CSV or XLSX whose rows name ERP accounts, spelled as the ERP prints them. It is a
control file like the ERP record and the review tables: never numbered as a contract, never a
source of folder names. /prepare registers it when it sits in the pile; --register does the
same for an explicit path. Every name must be an ERP account row; a stream row resolves to the
account it is a stream of.

--scope is deterministic. For each top account it takes the documents /sort filed to it (the
rows of work/logs/sort.csv), and adds every readable document that has no filing row at all:
files dropped into the pile after the light export, and files the review tool refused. That is
the list /analyse top reads in full. --filed-only leaves the unfiled documents out. The model
decides nothing here.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import (  # noqa: E402
    WORK, WORK_CARDS, WORK_PLACEMENTS, erp_account_names, fail, is_erp_top, load_entity_map, load_erp,
    load_inventory, load_sort_log, norm_name, read_csv, read_json, safe_folder_name, say, stream_map,
    warn, write_json,
)

ERP_TOP_JSON = WORK / "erp-top.json"
SCOPE_JSON = WORK / "top" / "scope.json"
ACCOUNT_WORDS = ("account", "customer", "supplier", "name")
UNFILED_TARGETS = {"", "_unreadable", "_no-card"}


def sha256_of(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_erp_top(pile, explicit=None):
    """The ERP_Top file in the pile, an explicit path, or None."""
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in {".csv", ".xlsx"}:
            raise ValueError("--erp-top must name a regular CSV or XLSX file")
        return path
    candidates = [p for p in Path(pile).rglob("*") if p.is_file() and not p.is_symlink() and is_erp_top(p)]
    if len(candidates) > 1:
        raise ValueError("Multiple ERP_Top files found; pass --erp-top with the intended file")
    return candidates[0].resolve() if candidates else None


def read_table(path):
    """(columns, rows) of a CSV or the first populated sheet of an XLSX; cells as strings."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        rows = read_csv(path)
        columns = list(rows[0].keys()) if rows else []
        if not columns:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                first = handle.readline().strip()
            columns = [c.strip() for c in first.split(",")] if first else []
        return columns, rows
    import openpyxl
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for sheet in book.worksheets:
            lines = [[("" if v is None else str(v).strip()) for v in row] for row in sheet.iter_rows(values_only=True)]
            lines = [line for line in lines if any(line)]
            if not lines:
                continue
            columns = lines[0]
            rows = [dict(zip(columns, line + [""] * (len(columns) - len(line)))) for line in lines[1:]]
            return columns, rows
    finally:
        book.close()
    return [], []


def account_column_of(columns, erp, explicit=None):
    if explicit:
        if explicit not in columns:
            raise ValueError(f"ERP_Top has no column {explicit!r}; columns: {', '.join(columns)}")
        return explicit
    preferred = erp.get("account_column")
    if preferred and preferred in columns:
        return preferred
    if len(columns) == 1:
        return columns[0]
    for column in columns:
        if any(word in column.casefold() for word in ACCOUNT_WORDS):
            return column
    raise ValueError("ERP_Top: which column holds the account name? Pass --account-column NAME. "
                     f"Columns: {', '.join(columns)}")


def register(path, account_column=None):
    """Validate ERP_Top against the ERP record and write work/erp-top.json."""
    path = Path(path).expanduser().resolve()
    erp = load_erp()
    columns, rows = read_table(path)
    if not columns:
        raise ValueError(f"ERP_Top {path.name} is empty")
    column = account_column_of(columns, erp, account_column)
    names = [(r.get(column) or "").strip() for r in rows]
    names = [n for n in names if n]
    by_norm = {norm_name(a): a for a in erp_account_names(erp)}
    entity_by_name, _ = load_entity_map()
    streams = stream_map(erp, entity_by_name)
    accounts, unknown, notes = [], [], []
    for name in names:
        exact = by_norm.get(norm_name(name))
        if not exact:
            unknown.append(name)
            continue
        if exact in streams:
            main = streams[exact][0]
            notes.append(f'"{exact}" is a stream of "{main}"; that account is analysed')
            exact = main
        if exact not in accounts:
            accounts.append(exact)
    data = {"source_path": str(path), "sha256": sha256_of(path), "column": column,
            "accounts": accounts, "unknown": unknown, "notes": notes,
            "registered_at": datetime.now(timezone.utc).isoformat()}
    write_json(ERP_TOP_JSON, data)
    say(f"ERP_Top: {len(accounts)} top accounts registered from {path.name} ({column})")
    for note in notes:
        say(f"  {note}")
    for name in unknown:
        warn(f"ERP_Top names {name!r}, which is not an ERP account row; fix ERP_Top and register it again")
    return data


def load_top():
    data = read_json(ERP_TOP_JSON)
    if not data:
        fail("No ERP_Top registered. Put ERP_Top.csv or ERP_Top.xlsx in the pile and run /prepare, "
             "or run python scripts/top.py --register <file>.")
    if data.get("unknown"):
        fail("ERP_Top names accounts that are not ERP rows: " + "; ".join(data["unknown"])
             + ". Spell them as the ERP record does, then register the file again.")
    if not data.get("accounts"):
        fail("ERP_Top lists no accounts.")
    return data


def build_scope(filed_only=False):
    """Documents /analyse top reads: the top accounts' filed documents plus the unfiled ones."""
    top = load_top()
    inventory = load_inventory()
    sort_rows = load_sort_log()
    if not sort_rows:
        fail("work/logs/sort.csv is missing or empty: run /sort first, or use /analyse all.")
    readable = {r["doc_id"] for r in inventory if r.get("doc_id") != "erp" and r.get("readable") == "yes"}
    filed = {r["doc_id"] for r in sort_rows if r.get("account", "") not in UNFILED_TARGETS}
    per_account = {a: sorted({r["doc_id"] for r in sort_rows if r.get("account") == a and r["doc_id"] in readable})
                   for a in top["accounts"]}
    unfiled = [] if filed_only else sorted(d for d in readable if d not in filed)
    docs = sorted(set(unfiled) | {d for ids in per_account.values() for d in ids})
    scope = {"accounts": top["accounts"], "docs": docs, "per_account": per_account, "unfiled": unfiled,
             "filed_only": filed_only, "erp_top_sha256": top["sha256"],
             "written_at": datetime.now(timezone.utc).isoformat()}
    write_json(SCOPE_JSON, scope)
    return scope


def has_card(doc):
    return (WORK_CARDS / f"{doc}.json").is_file() and (WORK_CARDS / f"{doc}.md").is_file()


def describe(scope):
    ids = lambda docs: ", ".join(docs) if docs else "none"  # noqa: E731
    for account, docs in scope["per_account"].items():
        say(f"{account}: {len(docs)} documents filed by /sort ({ids(docs)})")
    if scope["filed_only"]:
        say("unfiled readable documents: left out (--filed-only)")
    else:
        say(f"unfiled readable documents (no filing row; dropped in later or refused by the review tool): "
            f"{len(scope['unfiled'])} ({ids(scope['unfiled'])})")
    with_cards = [d for d in scope["docs"] if has_card(d)]
    say(f"scope: {len(scope['docs'])} documents; {len(with_cards)} already have a full card; "
        f"{len(scope['docs']) - len(with_cards)} to read. Written {SCOPE_JSON.relative_to(WORK.parent)}")


def status():
    top = read_json(ERP_TOP_JSON)
    if not top:
        say("ERP_Top: not registered")
        return
    say(f"ERP_Top: {Path(top['source_path']).name}; {len(top['accounts'])} accounts: " + "; ".join(top["accounts"]))
    if top.get("unknown"):
        say("  not ERP rows: " + "; ".join(top["unknown"]))
    scope = read_json(SCOPE_JSON)
    if not scope:
        say("scope: not written (run --scope)")
        return
    say(f"scope: {len(scope['docs'])} documents, written {scope['written_at']}"
        + (" (filed only)" if scope.get("filed_only") else ""))
    missing = [d for d in scope["docs"] if not has_card(d)]
    say(f"  cards: {len(scope['docs']) - len(missing)} present, {len(missing)} missing" + (f" ({', '.join(missing)})" if missing else ""))
    for account in scope["accounts"]:
        placed = (WORK_PLACEMENTS / f"{safe_folder_name(account)}.csv").is_file()
        say(f"  {account}: {len(scope['per_account'].get(account, []))} documents; placements {'present' if placed else 'missing'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--register", nargs="?", const="auto", metavar="FILE",
                        help="validate ERP_Top against the ERP record and write work/erp-top.json")
    action.add_argument("--scope", action="store_true", help="write work/top/scope.json: the documents to read")
    action.add_argument("--accounts", action="store_true", help="the top accounts, one per line")
    action.add_argument("--status", action="store_true")
    parser.add_argument("--account-column", help="ERP_Top column holding the account name")
    parser.add_argument("--filed-only", action="store_true", help="scope only the documents /sort filed to the top accounts")
    args = parser.parse_args()
    try:
        if args.register:
            path = args.register
            if path == "auto":
                configured = read_json(ERP_TOP_JSON) or {}
                path = configured.get("source_path")
                if not path:
                    raise ValueError("No ERP_Top registered by /prepare; pass --register PATH")
            register(path, args.account_column)
        elif args.scope:
            describe(build_scope(args.filed_only))
        elif args.accounts:
            for account in load_top()["accounts"]:
                print(account)
        else:
            status()
    except (ValueError, OSError, json.JSONDecodeError) as err:
        fail(str(err))
    return 0


if __name__ == "__main__":
    sys.exit(main())
