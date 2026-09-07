"""Build offline visual reports from existing filing outputs, without reading contracts.

    python scripts/visualise.py --all
    python scripts/visualise.py --account "<ERP account>"
    python scripts/visualise.py --all --analysis

The default reads work/erp.json and existing out/ CSV and Markdown only. Its arrows
mean "filed under". --analysis explicitly reads existing sort cards and placements
to draw the detailed relationship/part diagram. Neither mode reads raw contracts,
runs agents, extracts forms, exports a graph or rewrites the underlying reports.
"""

import argparse
import html
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import (  # noqa: E402
    OUT, account_folder, erp_account_names, fail, load_erp, read_csv, rel, say,
    truncate, warn, write_text,
)
from place import (  # noqa: E402
    PAGE_CSS, build_html, build_mermaid, ensure_visual_assets, load_context,
    add_empty_accounts, md_to_html, mm_label, settled_for_all_accounts,
)


def build_filing_mermaid(account, rows):
    """An account-to-document filing view; every edge has only a filing meaning."""
    lines = ["flowchart TB", f'    ACC["{mm_label(account)}"]',
             "    classDef account fill:#fff,stroke:#333,color:#111,font-weight:bold",
             "    classDef document fill:#edf2f7,stroke:#718096,color:#222",
             "    class ACC account"]
    seen = set()
    for number, row in enumerate(rows, 1):
        doc_id = row.get("doc_id", "").strip()
        if doc_id and doc_id in seen:
            continue
        seen.add(doc_id)
        title = row.get("title", "").strip() or "title not recorded"
        kind = row.get("kind", "").strip() or "kind not recorded"
        label = mm_label(f"doc {doc_id or '?'} · {truncate(title, 80)} · {kind}")
        lines += [f'    F{number}["{label}"]',
                  f'    ACC -- "filed under" --> F{number}',
                  f"    class F{number} document"]
    if not rows:
        lines += ['    EMPTY["No documents filed in this account"]', "    class EMPTY document"]
    return "\n".join(lines) + "\n"


def report_link(path, label):
    target = quote(path.relative_to(OUT).as_posix(), safe="/")
    return f'<a href="{html.escape(target, quote=True)}">{html.escape(label)}</a>'


def write_visual_index(side, accounts, account_rows):
    """Create only INDEX.html, using current report files and account table data."""
    rows = []
    for account in accounts:
        folder = account_folder(side, account)
        row = account_rows.get(account, {})
        links = [report_link(folder / name, label) for name, label in
                 (("position.html", "map"), ("README.md", "note"), ("documents.csv", "list"))
                 if (folder / name).is_file()]
        stream = row.get("treated_as_stream_of", "").strip()
        detail = f"stream of {stream}" if stream else ""
        if not (folder / "documents.csv").is_file() and not stream:
            detail = "No document table; see the account note." if links else "No filing output yet."
        rows.append("<tr>" + "".join(f"<td>{html.escape(value)}</td>" for value in
                                    (account, row.get("n_documents", ""), detail))
                    + f'<td>{" · ".join(links)}</td></tr>')

    # Holding folders are filing destinations, not ERP accounts. Link their existing
    # explainers/lists without creating account nodes or following document paths.
    holding = []
    side_folder = OUT / side
    if side_folder.exists():
        for folder in sorted(side_folder.iterdir()):
            if not folder.is_dir() or not folder.name.startswith("_"):
                continue
            for note in sorted(folder.rglob("README.md")):
                # Only report folders, never a copied source file named README.md.
                if "files" in note.relative_to(folder).parts[:-1]:
                    continue
                links = [report_link(note, note.parent.relative_to(side_folder).as_posix())]
                listing = note.with_name("documents.csv")
                if listing.is_file():
                    links.append(report_link(listing, "list"))
                holding.append("<li>" + " · ".join(links) + "</li>")
    index_md = OUT / "INDEX.md"
    note = index_md.read_text(encoding="utf-8") if index_md.exists() else ""
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Accounts — {html.escape(side)}</title><style>{PAGE_CSS}</style></head>
<body><h1>Accounts ({html.escape(side)})</h1>
<p class="links"><a href="{quote(side)}/CORPUS.csv">CORPUS.csv</a>
<a href="{quote(side)}/ACCOUNTS.csv">ACCOUNTS.csv</a> <a href="INDEX.md">INDEX.md</a></p>
<table><thead><tr><th>account</th><th>documents</th><th>filing note</th><th>links</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<h2>Holding folders</h2><ul>{''.join(holding) or '<li>None listed.</li>'}</ul>
<div class="note">{md_to_html(note)}</div></body></html>
"""
    write_text(OUT / "INDEX.html", page)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="visualise all existing ERP account lists")
    group.add_argument("--account", help="visualise one account (exact ERP name)")
    parser.add_argument("--analysis", action="store_true",
                        help="use existing cards/placements for relationships and part status")
    args = parser.parse_args(argv)
    erp = load_erp()
    side = erp.get("side")
    if side not in ("customers", "suppliers"):
        fail("work/erp.json needs side customers or suppliers; run /prepare first.")
    accounts = erp_account_names(erp)
    if args.account and args.account not in accounts:
        fail(f"{args.account!r} is not an ERP account. Accounts: " + "; ".join(accounts))
    if not (OUT / side / "ACCOUNTS.csv").is_file() or not (OUT / "INDEX.md").is_file():
        fail("Filing tables and INDEX.md are missing. Run /sort first.")
    account_rows = {row.get("account"): row for row in read_csv(OUT / side / "ACCOUNTS.csv")}
    selected = [args.account] if args.account else accounts
    ctx = None
    settled = {}
    if args.analysis:
        ctx = load_context()
        settled = settled_for_all_accounts(ctx)
        add_empty_accounts(ctx, settled)  # a zero-document account has no judge and an empty diagram
    built = 0
    for account in selected:
        folder = account_folder(side, account)
        if account_rows.get(account, {}).get("treated_as_stream_of", "").strip():
            say(f"{account}: stream row; its existing README points to the main account")
            continue
        table = folder / "documents.csv"
        note_path = folder / "README.md"
        if not table.is_file() or not note_path.is_file():
            warn(f"{account}: documents.csv or README.md is missing; no diagram created")
            continue
        rows = read_csv(table, required_columns=["doc_id", "title", "kind"])
        note = note_path.read_text(encoding="utf-8")
        if args.analysis:
            if account not in settled:
                warn(f"{account}: no existing placements; run /deep-dive before --analysis")
                continue
            current = settled[account][0]
            listed = {row.get("doc_id"): row for row in rows}
            if set(listed) != set(current) or any(
                    listed[doc_id].get("tree") != placement.get("tree") or
                    listed[doc_id].get("folder") != placement.get("folder")
                    for doc_id, placement in current.items()):
                warn(f"{account}: current tables do not match the analysis placements; "
                     "refresh /deep-dive reports before --analysis")
                continue
            mmd = build_mermaid(ctx, account, settled[account][0])
        else:
            mmd = build_filing_mermaid(account, rows)
        ensure_visual_assets()
        write_text(folder / "position.mmd", mmd)
        write_text(folder / "position.html", build_html(account, mmd, note, analysis=args.analysis))
        say(f"{account}: written {rel(folder)}/position.mmd and position.html")
        built += 1
    write_visual_index(side, accounts, account_rows)
    say(f"{built} account diagrams; written out/INDEX.html. Existing CSV and Markdown unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
