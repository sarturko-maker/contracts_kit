"""Generate an account's folders, note and document list from the judge's placements.

    python scripts/place.py --account "<name>"   one account: status folders, README.md,
                                                 documents.csv
    python scripts/place.py --index              CORPUS.csv, ACCOUNTS.csv, INDEX.md
    python scripts/place.py --all                every account with a placements file, then --index
    python scripts/place.py --all --visuals      also build the original analysis diagrams/HTML
    python scripts/place.py --accounts-with-documents
                                                 the ERP accounts a document was sorted to, one
                                                 per line, so /judge skips the empty ones

Sources: work/placements/<account>.csv and .md (the judge), work/cards/<id>.json (the readers),
work/inventory.csv and work/erp.json (prepare.py), work/logs/sort.csv (sort.py),
inputs/entity-map.csv and inputs/corrections.csv. Nothing under out/ is edited by hand; run this
again after any input changes.

Copies in the status folders are named by kit_common.filed_name() from the card and the
placement, and that name is the `filed_as` column of documents.csv and CORPUS.csv.

An ERP account with no documents needs no judge: its folder, its README saying nothing is filed
and its empty diagram are written here. A document in a holding folder (no ERP account) has no
judge either: it keeps its card facts in CORPUS.csv as `unassessed (no account)` and is listed
under "Needs a decision" in INDEX.md.
"""

import argparse
import html
import re
import shutil
import sys
from urllib.parse import quote

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from kit_common import (  # noqa: E402
    ACCOUNTS_COLUMNS, CORPUS_COLUMNS, HOLDING_FOLDERS, MERMAID_JS, NOTE_TEMPLATE, NOT_FOUND, OUT,
    PLACEMENT_COLUMNS, REVIEWER_COLUMNS, STATUS_FOLDERS, TO_JUDGE, WORK_FILES, WORK_PLACEMENTS,
    account_folder, apply_corrections_to_card, apply_corrections_to_placement, counterparty_for,
    doc_label, entity_row_for, erp_account_names, fail, filed_name, is_empty_answer, join_multi, load_all_cards,
    load_corrections, load_entity_map, load_erp, load_inventory, load_our_entities, load_sort_log,
    names_from_card, naming_from_card, norm_name, read_csv, rel, safe_folder_name, say, split_multi,
    stream_map, strip_role, truncate, unique_filed_name, warn, write_csv, write_text,
)

FOLDER_WORDS = {
    "1-governs-trade": "governs trade",
    "2-governs-part-of-trade": "governs part of trade",
    "3-live-not-trade": "live, not trade",
    "4-not-live": "not live",
    "5-orders-drafts-duplicates": "order/draft/duplicate",
    "6-business-practice": "business practice",
    "unsure": "unsure",
}
FOLDER_CLASS = {
    "1-governs-trade": "f1", "2-governs-part-of-trade": "f2", "3-live-not-trade": "f3",
    "4-not-live": "f4", "5-orders-drafts-duplicates": "f5", "6-business-practice": "f6", "unsure": "unsure",
}
# fill, stroke, text colour, extra — used by the diagram and the HTML legend
CLASS_STYLE = {
    "f1": ("#1f5fbf", "#163f80", "#ffffff", ""),
    "f2": ("#0f8b8d", "#0a5c5e", "#ffffff", ""),
    "f3": ("#dfe6ee", "#9fb0c3", "#333a44", ""),
    "f4": ("#e6e6e6", "#9a9a9a", "#555555", ""),
    "f5": ("#e6e6e6", "#9a9a9a", "#555555", ""),
    "f6": ("#efe3f7", "#7a3fa0", "#3a1f50", "stroke-dasharray: 4 3"),
    "unsure": ("#fff8e1", "#b58900", "#4a3a00", "stroke-dasharray: 6 4"),
    "part_live": ("#dff3e3", "#3c9d5d", "#1d4d2b", ""),
    "part_dead": ("#e6e6e6", "#9a9a9a", "#666666", "stroke-dasharray: 4 3"),
    "acc": ("#ffffff", "#333333", "#000000", "font-weight:bold"),
}
PROSE_HEADINGS = {
    "the position": "position",
    "overlaps and conflicts": "overlaps",
    "couldn't find or couldn't tell": "couldnt",
    "questions for the business": "questions",
}
NOTHING = "(the judge wrote nothing here)"
NOT_JUDGED = "not judged"
# A document in a holding folder has been read but has no ERP account, so no judge ever sees it.
# It keeps its card facts and says plainly that its status was not assessed.
UNASSESSED = "unassessed (no account)"
NO_ACCOUNT_REASON = "no ERP account for this name yet; decide it in inputs/entity-map.csv"
UNREADABLE = "not readable by the kit"
NO_CARD = "no card yet"


# --------------------------------------------------------------------------- loading
def load_context():
    """Everything place.py needs that does not depend on the account."""
    erp = load_erp()
    side = erp.get("side")
    if not side:
        fail("work/erp.json has no side. Re-run /prepare with --side customers|suppliers.")
    sort_rows = load_sort_log()
    if not sort_rows:
        fail("work/logs/sort.csv is missing or empty. Run /match first.")
    # A CSV cell loses its leading and trailing spaces, so an ERP name written with one would
    # never match its own sort rows. Snap each row back to the ERP spelling.
    by_norm = {norm_name(a): a for a in erp_account_names(erp)}
    for row in sort_rows:
        exact = by_norm.get(norm_name(row.get("account", "")))
        if exact and exact != row.get("account"):
            row["account"] = exact
    entity_by_name, _ = load_entity_map()
    corrections = load_corrections()
    cards = load_all_cards()
    for doc_id, card in list(cards.items()):
        cards[doc_id] = apply_corrections_to_card(card, corrections)
    for row in corrections:
        if row.get("field") not in PLACEMENT_COLUMNS and row.get("field", "") not in cards.get(row["doc_id"], {}):
            warn(f"corrections.csv: field {row.get('field')!r} for doc {row['doc_id']} is neither a card key "
                 "nor a placement column; ignored")
    return {
        "erp": erp,
        "side": side,
        "accounts": erp_account_names(erp),
        "streams": stream_map(erp, entity_by_name),
        "inventory": {r["doc_id"]: r for r in load_inventory()},
        "cards": cards,
        "entity_by_name": entity_by_name,
        "sort_rows": sort_rows,
        "corrections": corrections,
        "our_names": load_our_entities(),
    }


def parse_prose(text):
    """Split the judge's markdown into {section key: body} by its four '## ' headings."""
    sections = {}
    current = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.*?)\s*$", line)
        if heading:
            key = PROSE_HEADINGS.get(heading.group(1).strip().lower().rstrip(":"))
            if key is None:
                warn(f"placements prose has a heading the template does not use: {heading.group(1)!r}")
            current = key
            sections.setdefault(key, [])
            continue
        if current is not None:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if k}


def placements_path(account):
    """work/placements/<safe name>.csv, or the raw account name when only that exists.

    The judge is told to use safe_folder_name(account); an ERP name with a slash, a colon or a
    trailing space written raw is still read, with a warning, so nothing is silently missed.
    """
    safe = WORK_PLACEMENTS / f"{safe_folder_name(account)}.csv"
    if safe.exists():
        return safe
    if not WORK_PLACEMENTS.exists():
        return None
    for path in sorted(WORK_PLACEMENTS.glob("*.csv")):
        if path.name == f"{account}.csv":
            warn(f"{account}: placements found as {rel(path)}; the judge should write "
                 f"{safe.name} (the folder-safe name). Read anyway.")
            return path
    return None


def load_placements(ctx, account):
    """The judge's placements for one account: ({doc_id: row}, prose dict), or None when absent."""
    csv_path = placements_path(account)
    if csv_path is None:
        return None
    rows = read_csv(csv_path, required_columns=PLACEMENT_COLUMNS)
    by_doc = {}
    for row in rows:
        row = {c: row.get(c, "") for c in PLACEMENT_COLUMNS}
        doc_id = row["doc_id"].strip().zfill(3) if row["doc_id"].strip().isdigit() else row["doc_id"].strip()
        row["doc_id"] = doc_id
        if not doc_id:
            continue
        if doc_id in by_doc:
            warn(f"{account}: placements list doc {doc_id} twice; the first row is used")
            continue
        by_doc[doc_id] = apply_corrections_to_placement(row, ctx["corrections"])
    md_path = csv_path.with_suffix(".md")
    prose = parse_prose(md_path.read_text(encoding="utf-8")) if md_path.exists() else {}
    if not md_path.exists():
        warn(f"{account}: {rel(md_path)} is missing; the note's prose sections will be empty")
    return by_doc, prose


def docs_sorted_to(ctx, account):
    """sort.csv rows whose target is this account, in doc order."""
    return sorted((r for r in ctx["sort_rows"] if r.get("account") == account), key=lambda r: r["doc_id"])


def settle_placements(ctx, account, placements):
    """Every doc sorted to the account gets a placement; strays are warned about and dropped."""
    by_doc, prose = placements
    sorted_ids = [r["doc_id"] for r in docs_sorted_to(ctx, account)]
    settled = {}
    for doc_id in sorted_ids:
        row = by_doc.get(doc_id)
        if row is None:
            warn(f"{account}: doc {doc_id} was sorted to this account but the judge did not place it; "
                 "filed in 'unsure' with reason 'not placed by the judge'")
            row = {c: "" for c in PLACEMENT_COLUMNS}
            row.update({"doc_id": doc_id, "tree": "T0", "folder": "unsure", "reason": "not placed by the judge"})
        if row.get("folder") not in STATUS_FOLDERS:
            warn(f"{account}: doc {doc_id} has folder {row.get('folder')!r}, which is not one of the seven; "
                 "filed in 'unsure'")
            row = dict(row)
            row["reason"] = (row.get("reason", "") + f" (judge wrote folder {row.get('folder')!r})").strip()
            row["folder"] = "unsure"
        if not row.get("tree", "").strip():
            warn(f"{account}: doc {doc_id} has no tree number; shown as T0")
            row = dict(row)
            row["tree"] = "T0"
        settled[doc_id] = row
    for doc_id in by_doc:
        if doc_id not in settled:
            warn(f"{account}: placements name doc {doc_id}, which was not sorted to this account; ignored")
    return settled, prose


# --------------------------------------------------------------------------- corpus rows
def merge_parts(detail, parts_status):
    """The card's parts detail with live/dead taken from the judge's parts_status."""
    segments = [] if is_empty_answer(detail) else split_multi(detail)
    status = {}
    originals = {}
    for seg in split_multi(parts_status):
        if ":" in seg:
            name, state = seg.rsplit(":", 1)
            status[norm_name(name)] = state.strip()
            originals[norm_name(name)] = name.strip()
    out = []
    used = set()
    for seg in segments:
        name = seg.split(":", 1)[0].strip()
        state = status.get(norm_name(name))
        if state:
            used.add(norm_name(name))
            new, count = re.subn(r"\b(live|dead|unsure)\b", state, seg, count=1)
            out.append(new if count else f"{seg}, {state}")
        else:
            out.append(seg)
    for key, state in status.items():
        if key not in used:
            out.append(f"{originals[key]}: {state}")
    return join_multi(out) if out else detail


def parts_of(card, placement):
    """[(part name, live|dead|unsure)] for a layered document."""
    parts = []
    if card.get("q5_parts", "").strip().lower() != "yes" and is_empty_answer(placement.get("parts_status", "")):
        return parts
    status = {}
    for seg in split_multi(placement.get("parts_status", "")):
        if ":" in seg:
            name, state = seg.rsplit(":", 1)
            status[norm_name(name)] = (name.strip(), state.strip().lower())
    detail = card.get("q5_parts_detail", "")
    seen = set()
    for seg in ([] if is_empty_answer(detail) else split_multi(detail)):
        name = seg.split(":", 1)[0].strip()
        rest = seg[len(name):].lower()
        state = status.get(norm_name(name), (name, None))[1]
        if state is None:
            state = "dead" if "dead" in rest else "live" if "live" in rest else "unsure"
        parts.append((name, state))
        seen.add(norm_name(name))
    for key, (name, state) in status.items():
        if key not in seen:
            parts.append((name, state))
    return parts


def holding_folder_of(account):
    """'_not-on-the-list/Brenlow Ltd' -> that path; '' when the target is not a holding folder."""
    account = (account or "").strip()
    for holding in HOLDING_FOLDERS:
        if account == holding or account.startswith(holding + "/"):
            return account
    return ""


def holding_name_of(account):
    """The company name a holding row is grouped under; '(no name)' for _no-name-found."""
    holding = holding_folder_of(account)
    if not holding:
        return ""
    return holding.split("/", 1)[1].strip() if "/" in holding else "(no name)"


def corpus_row(ctx, sort_row, placement, judged):
    """One CORPUS.csv row for a (document, target) pair."""
    doc_id = sort_row["doc_id"]
    inv = ctx["inventory"].get(doc_id, {})
    row = {c: "" for c in CORPUS_COLUMNS}
    row.update({
        "doc_id": doc_id,
        "original_path": sort_row.get("original_path") or inv.get("original_path", ""),
        "file_type": inv.get("file_type", ""),
        "side": ctx["side"],
        "account": sort_row.get("account", ""),
    })
    if inv.get("readable") != "yes":
        for col in CORPUS_COLUMNS:
            if col not in ("doc_id", "original_path", "file_type") and col not in REVIEWER_COLUMNS:
                row[col] = UNREADABLE
        row["account"] = sort_row.get("account", "_unreadable")
        return row

    is_docx = inv.get("file_type") == "docx"
    row.update({
        "pages": "n/a" if is_docx else inv.get("pages", ""),
        "scanned_pages": "n/a" if is_docx else inv.get("scanned_pages", ""),
        "language": inv.get("language", ""),
        "docx_author": inv.get("docx_author", ""),
        "docx_created": inv.get("docx_created", ""),
        "docx_modified": inv.get("docx_modified", ""),
        "docx_tracked_changes": inv.get("docx_tracked_changes", ""),
        "companies_found": sort_row.get("companies_found", ""),
        "match_basis": sort_row.get("basis", ""),
        "match_confidence": sort_row.get("confidence", ""),
        "sort_note": sort_row.get("note", ""),
    })
    card = ctx["cards"].get(doc_id)
    card_map = {
        "kind": "q1_kind", "title": "q1_title", "their_signing_entities": "q2_their_signing_entities",
        "their_group_companies": "q2_their_group_companies", "our_entity": "q2_our_entity",
        "signed": "q3_signed", "start_date": "q4_start_date", "start_basis": "q4_start_basis",
        "end": "q4_end", "ended_sign": "q4_ended_sign", "status": "q4_status",
        "attaches_to": "q6_attaches_to", "replaces": "q6_replaces",
        "referred_to_not_in_pile": "q6_referred_to_not_in_pile", "trade_scope": "q7_trade_scope",
        "what_makes_it_govern": "q7_what_makes_it_govern", "entities_covered": "q8_entities_covered",
        "countries_covered": "q8_countries", "copy_or_draft_of": "q9_copy_or_draft_of",
        "oddities": "q10_oddities", "evidence_signed": "q3_evidence", "evidence_dates": "q4_evidence",
        "evidence_companies": "q2_evidence", "evidence_trade": "q7_evidence",
    }
    if card is None:
        for col in list(card_map) + ["parts"]:
            row[col] = NO_CARD
    else:
        for col, key in card_map.items():
            row[col] = card.get(key, "")
        row["parts"] = merge_parts(card.get("q5_parts_detail", ""), placement.get("parts_status", "") if placement else "")

    row["filed_as"] = filed_name(
        doc_id, inv.get("ext", ""),
        counterparty=counterparty_for(sort_row.get("account", ""), split_multi(sort_row.get("companies_found", ""))),
        pages=inv.get("pages", ""), unresolved=card is None,
        **naming_from_card(card, placement if judged else None))

    if judged and placement is not None:
        row.update({
            "tree": placement.get("tree", ""),
            "folder": placement.get("folder", ""),
            "placement_reason": placement.get("reason", ""),
            "overlap_or_conflict": placement.get("overlap", "") or "none",
            "question_for_business": placement.get("question", "") or "none",
        })
    else:
        for col in ("tree", "folder", "placement_reason", "overlap_or_conflict", "question_for_business"):
            row[col] = NOT_JUDGED
        holding = holding_folder_of(sort_row.get("account", ""))
        if holding and card is not None:
            # Read, but no ERP account, so no judge: the card facts stay and the folder is the
            # holding folder the copy is in. Nothing is dropped from the list.
            row["folder"] = holding
            row["status"] = UNASSESSED
            row["placement_reason"] = NO_ACCOUNT_REASON

    for col in CORPUS_COLUMNS:
        if col not in REVIEWER_COLUMNS and row[col] == "":
            row[col] = NOT_FOUND
    return row


def build_all_rows(ctx, settled_by_account):
    """Every CORPUS row, in sort.csv order. settled_by_account: {account: {doc_id: placement}}."""
    rows = []
    for sort_row in sorted(ctx["sort_rows"], key=lambda r: (r["doc_id"], r.get("account", ""))):
        account = sort_row.get("account", "")
        placements = settled_by_account.get(account)
        placement = placements.get(sort_row["doc_id"]) if placements else None
        rows.append(corpus_row(ctx, sort_row, placement, judged=placement is not None))
    return rows


# --------------------------------------------------------------------------- the note
def md_cell(text):
    """Text safe inside a markdown table cell."""
    text = (text or "").replace("\n", " ").replace("|", "\\|").strip()
    return text or NOT_FOUND


def signing_names(card):
    """Their signing entities, roles stripped, joined with '; '."""
    names = [strip_role(x) for x in split_multi(card.get("q2_their_signing_entities", ""))]
    names = [n for n in names if not is_empty_answer(n)]
    return "; ".join(names) if names else NOT_FOUND


def tree_number(tree):
    """'T12' -> 12, for ordering. Anything odd sorts last."""
    digits = re.sub(r"\D", "", tree or "")
    return int(digits) if digits else 10**6


def account_block(ctx, account, settled):
    """Section 1 of the note: ERP row, our entities, their entities with match basis."""
    erp_row = next((a for a in ctx["erp"].get("accounts", []) if a.get("account") == account), {})
    details = [ctx["side"]]
    if erp_row.get("account_number"):
        details.append(f"account number {erp_row['account_number']}")
    if erp_row.get("country"):
        details.append(f"country {erp_row['country']}")
    lines = [f"- ERP account: **{account}** ({'; '.join(details)})"]
    folder = account_folder(ctx["side"], account)
    if folder.name != account:
        lines.append(f"- Folder name: `{folder.name}` (characters not allowed in folder names were replaced by `_`)")
    for stream, (main, row) in ctx["streams"].items():
        if main == account:
            lines.append(f'- ERP row "{stream}" is treated as a stream of this account ({row.get("basis", "")}, '
                         f'{row.get("confidence", "")}, decided by {row.get("decided_by", "")}); its documents are filed here')
    ours, theirs = [], []
    for doc_id in settled:
        card = ctx["cards"].get(doc_id)
        if not card:
            continue
        our = strip_role(card.get("q2_our_entity", ""))
        if not is_empty_answer(our) and norm_name(our) not in {norm_name(o) for o in ours}:
            ours.append(our)
        for name in names_from_card(card, ctx["our_names"]):
            if norm_name(name) not in {norm_name(t) for t in theirs}:
                theirs.append(name)
    lines.append("- Our entities found: " + (join_multi(ours) if ours else NOT_FOUND))
    lines.append("- Their entities found:" if theirs else "- Their entities found: " + NOT_FOUND)
    for name in theirs:
        row = entity_row_for(ctx["entity_by_name"], name)
        if row is None:
            lines.append(f"  - {name} — no entity-map row yet")
            continue
        target = row.get("account", "")
        if target in ctx["streams"]:
            target = f"{ctx['streams'][target][0]} (via stream row {target})"
        lines.append(f"  - {name} — {target}: {row.get('basis', '') or 'no basis'}, "
                     f"{row.get('confidence', '') or 'no confidence'}, decided by {row.get('decided_by', '') or '?'}"
                     + (f" — {row['note']}" if row.get("note") else ""))
    return "\n".join(lines)


def table_rows(ctx, settled, folder, with_limit, filed=None):
    """Markdown table for folder 1 (or folder 2 with a limit column)."""
    header = ["tree", "doc", "filed as", "title", "kind", "companies", "start / end / status", "scope", "why"]
    if with_limit:
        header.insert(8, "limit")
    docs = [(p["tree"], d) for d, p in settled.items() if p.get("folder") == folder]
    if not docs:
        return "(none)"
    docs.sort(key=lambda t: (tree_number(t[0]), t[1]))
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    for tree, doc_id in docs:
        p = settled[doc_id]
        card = ctx["cards"].get(doc_id, {})
        cells = [
            tree, doc_label(doc_id), (filed or {}).get(doc_id, NOT_FOUND),
            card.get("q1_title", NOT_FOUND), card.get("q1_kind", NOT_FOUND),
            signing_names(card),
            f"{card.get('q4_start_date', NOT_FOUND)} / {card.get('q4_end', NOT_FOUND)} / {card.get('q4_status', NOT_FOUND)}",
            card.get("q7_trade_scope", NOT_FOUND),
        ]
        if with_limit:
            cells.append(p.get("limit", "") or NOT_FOUND)
        cells.append(p.get("reason", "") or NOT_FOUND)
        lines.append("| " + " | ".join(md_cell(c) for c in cells) + " |")
    return "\n".join(lines)


def everything_else(ctx, settled, filed=None):
    """Section 5: one bullet per doc outside folders 1 and 2, ordered by folder then doc."""
    order = {f: i for i, f in enumerate(STATUS_FOLDERS)}
    docs = [d for d, p in settled.items() if p.get("folder") not in ("1-governs-trade", "2-governs-part-of-trade")]
    docs.sort(key=lambda d: (order.get(settled[d]["folder"], 99), d))
    if not docs:
        return "(none)"
    lines = []
    for doc_id in docs:
        p = settled[doc_id]
        card = ctx["cards"].get(doc_id, {})
        bits = [f"{doc_label(doc_id)} — {card.get('q1_kind', NOT_FOUND)} \"{card.get('q1_title', NOT_FOUND)}\"",
                f"filed as `{(filed or {}).get(doc_id, NOT_FOUND)}`",
                p["folder"], p.get("reason", "") or NOT_FOUND]
        if p.get("what_would_change", "").strip():
            bits.append(p["what_would_change"].strip())
        lines.append("- " + " — ".join(bits))
    return "\n".join(lines)


def practice_line(ctx, settled):
    """Section 6: playbooks found (folder 6), else the standard line."""
    lines = []
    for doc_id, p in settled.items():
        if p.get("folder") == "6-business-practice":
            card = ctx["cards"].get(doc_id, {})
            lines.append(f"{doc_label(doc_id)} \"{card.get('q1_title', NOT_FOUND)}\" (folder 6-business-practice): "
                         f"{p.get('reason', '') or NOT_FOUND}")
    return "\n".join(f"- {line}" for line in lines) if lines else "Nothing in the pile; sales to confirm."


def couldnt_section(ctx, settled, prose):
    """Section 8: generated bullets, then the judge's prose."""
    bullets = []
    known_group_seen = set()
    for doc_id, p in settled.items():
        card = ctx["cards"].get(doc_id)
        if not card:
            continue
        referred = card.get("q6_referred_to_not_in_pile", "")
        if not is_empty_answer(referred):
            bullets.append(f"- {doc_label(doc_id)} refers to a document not in the pile: {referred}")
        if is_empty_answer(card.get("q4_start_date", "")) or card.get("q4_start_date", "").lower() == "not found":
            bullets.append(f"- {doc_label(doc_id)}: no start date found")
        if card.get("q4_end", "").lower().startswith("rolling") and p.get("folder") == "unsure":
            bullets.append(f"- {doc_label(doc_id)}: rolling terms recorded; no evidence of current trading under this text")
        for name in names_from_card(card, ctx["our_names"]):
            row = entity_row_for(ctx["entity_by_name"], name)
            if row and row.get("basis", "").strip().lower() == "known group" and norm_name(name) not in known_group_seen:
                known_group_seen.add(norm_name(name))
                bullets.append(f"- {name} matched to {row.get('account', '')} on `known group` only "
                               f"({row.get('confidence', '')}; {doc_label(doc_id)}): {row.get('note', '') or 'no note'}")
    text = prose.get("couldnt", "").strip() or NOTHING
    return "\n".join(bullets + [text]) if bullets else text


def build_note(ctx, account, settled, prose, filed=None):
    """Fill stage1/position-note.md for this account."""
    if not NOTE_TEMPLATE.exists():
        fail(f"{rel(NOTE_TEMPLATE)} is missing; the kit is incomplete.")
    template = NOTE_TEMPLATE.read_text(encoding="utf-8")
    template = re.sub(r"<!--.*?-->", "", template, flags=re.DOTALL)
    values = {
        "account": account,
        "side": ctx["side"],
        "account_block": account_block(ctx, account, settled),
        "position": prose.get("position", "").strip() or NOTHING,
        "governs_table": table_rows(ctx, settled, "1-governs-trade", with_limit=False, filed=filed),
        "part_table": table_rows(ctx, settled, "2-governs-part-of-trade", with_limit=True, filed=filed),
        "everything_else": everything_else(ctx, settled, filed=filed),
        "practice_line": practice_line(ctx, settled),
        "overlaps": prose.get("overlaps", "").strip() or NOTHING,
        "couldnt": couldnt_section(ctx, settled, prose),
        "questions": prose.get("questions", "").strip() or NOTHING,
    }
    note = template
    for key, value in values.items():
        note = note.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{\s*[a-z_]+\s*\}\}", note)
    if leftover:
        warn(f"{account}: the note template has placeholders place.py does not fill: {', '.join(sorted(set(leftover)))}")
    note = re.sub(r"\n{3,}", "\n\n", note).strip() + "\n"

    # every document exactly once across sections 3, 4 and 5
    shown = re.findall(r"^\|\s*[^|]+\|\s*doc (\d{3,})\s*\|", values["governs_table"] + "\n" + values["part_table"], re.M)
    shown += re.findall(r"^- doc (\d{3,})\b", values["everything_else"], re.M)
    counts = {d: shown.count(d) for d in settled}
    for doc_id, n in counts.items():
        if n != 1:
            warn(f"{account}: doc {doc_id} appears {n} times across sections 3, 4 and 5 of the note (should be once)")
    return note


# --------------------------------------------------------------------------- the diagram
def mm_label(text):
    """Text safe inside a quoted Mermaid label."""
    return (text or "").replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;").replace("\n", " ")


def node_id(doc_id):
    return "D" + re.sub(r"[^A-Za-z0-9_]", "_", doc_id)


def build_mermaid(ctx, account, settled):
    """position.mmd: account at the top, one node per document, parts as sub-nodes, labelled edges."""
    lines = ["flowchart TB", f'    ACC["{mm_label(account)}"]', "    class ACC acc"]
    node_classes = []
    subgraph_styles = []
    defined = {"ACC"}
    for doc_id in sorted(settled):
        p = settled[doc_id]
        card = ctx["cards"].get(doc_id, {})
        nid = node_id(doc_id)
        defined.add(nid)
        label = mm_label(f"{doc_label(doc_id)} · {truncate(card.get('q1_title', NOT_FOUND), 40)} · "
                         f"{FOLDER_WORDS.get(p['folder'], p['folder'])} · {card.get('q4_status', 'unsure') or 'unsure'}")
        cls = FOLDER_CLASS.get(p["folder"], "unsure")
        parts = parts_of(card, p)
        if parts:
            lines.append(f'    subgraph {nid} ["{label}"]')
            lines.append("        direction TB")
            for i, (name, state) in enumerate(parts, start=1):
                pid = f"{nid}_p{i}"
                defined.add(pid)
                lines.append(f'        {pid}["{mm_label(name)} · {state}"]')
                node_classes.append(f"    class {pid} {'part_dead' if state == 'dead' else 'part_live' if state == 'live' else 'unsure'}")
            lines.append("    end")
            fill, stroke, color, extra = CLASS_STYLE[cls]
            style = f"fill:{fill},stroke:{stroke},color:{color}" + (f",{extra}" if extra else "")
            subgraph_styles.append(f"    style {nid} {style}")
        else:
            lines.append(f'    {nid}["{label}"]')
            node_classes.append(f"    class {nid} {cls}")

    # edges: account -> tree roots; attaches_to and replaces between documents
    edges = []
    trees = {}
    for doc_id, p in settled.items():
        trees.setdefault(p["tree"], []).append(doc_id)
    for tree, docs in trees.items():
        roots = []
        for doc_id in docs:
            p = settled[doc_id]
            target = p.get("attaches_to", "").strip()
            if not target or target.zfill(3) not in settled:
                roots.append(doc_id)
        if not roots:
            roots = [min(docs)]
        for root in roots:
            edges.append(f"    ACC --> {node_id(root)}")
    for doc_id, p in settled.items():
        target = p.get("attaches_to", "").strip()
        if target:
            target = target.zfill(3)
            if target in settled:
                edges.append(f"    {node_id(doc_id)} -- {p.get('attach_kind', '').strip() or 'attached to'} --> {node_id(target)}")
            else:
                warn(f"{account}: doc {doc_id} attaches to doc {target}, which is not in this account; edge left out")
        replaced = p.get("replaces", "").strip()
        if replaced:
            replaced = replaced.zfill(3)
            if replaced in settled:
                edges.append(f"    {node_id(doc_id)} -- replaces --> {node_id(replaced)}")
            else:
                warn(f"{account}: doc {doc_id} replaces doc {replaced}, which is not in this account; edge left out")
    lines.extend(edges)
    for cls, (fill, stroke, color, extra) in CLASS_STYLE.items():
        lines.append(f"    classDef {cls} fill:{fill},stroke:{stroke},color:{color}" + (f",{extra}" if extra else ""))
    lines.extend(node_classes)
    lines.extend(subgraph_styles)
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- html
def inline_md(text):
    """Escape HTML, then **bold** and `code`."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(md):
    """A tiny markdown-to-HTML converter: headings, paragraphs, lists, pipe tables, hr."""
    out = []
    paragraph = []
    list_tag = None
    table = []

    def flush_paragraph():
        if paragraph:
            out.append("<p>" + " ".join(inline_md(l) for l in paragraph) + "</p>")
            paragraph.clear()

    def flush_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def flush_table():
        if table:
            head, *body = table
            out.append("<table><thead><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in head) + "</tr></thead><tbody>")
            for row in body:
                out.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in row) + "</tr>")
            out.append("</tbody></table>")
            table.clear()

    def split_row(line):
        return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]

    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            flush_paragraph(); flush_list()
            if re.fullmatch(r"\|(\s*:?-+:?\s*\|)+", stripped):
                continue
            table.append(split_row(stripped))
            continue
        flush_table()
        if not stripped:
            flush_paragraph(); flush_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            flush_paragraph(); flush_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline_md(heading.group(2))}</h{level}>")
            continue
        if stripped == "---":
            flush_paragraph(); flush_list()
            out.append("<hr>")
            continue
        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            tag = "ul" if bullet else "ol"
            if list_tag != tag:
                flush_list()
                out.append(f"<{tag}>")
                list_tag = tag
            out.append(f"<li>{inline_md((bullet or numbered).group(1))}</li>")
            continue
        if list_tag and line.startswith("  "):
            out[-1] = out[-1][:-5] + " " + inline_md(stripped) + "</li>"
            continue
        flush_list()
        paragraph.append(stripped)
    flush_paragraph(); flush_list(); flush_table()
    return "\n".join(out)


PAGE_CSS = """
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; margin: 2rem auto; max-width: 1100px;
       padding: 0 1rem; color: #222; background: #fff; line-height: 1.45; }
h1 { font-size: 1.6rem; } h2 { font-size: 1.2rem; margin-top: 1.6rem; border-bottom: 1px solid #ddd; }
table { border-collapse: collapse; margin: .5rem 0; font-size: .9rem; } th, td { border: 1px solid #ccc; padding: .3rem .5rem; vertical-align: top; text-align: left; }
th { background: #f3f3f3; } code { background: #f3f3f3; padding: 0 .2rem; } pre.mermaid { background: #fafafa; border: 1px solid #eee; padding: 1rem; overflow-x: auto; }
.legend span { display: inline-block; padding: .15rem .5rem; margin: .15rem; border: 2px solid; border-radius: 4px; font-size: .85rem; }
.links a { margin-right: 1rem; } .note { margin-top: 2rem; }
"""


def legend_html():
    """The folder colours as a row of chips."""
    labels = {
        "f1": "1 governs trade", "f2": "2 governs part of trade", "f3": "3 live, not trade", "f4": "4 not live",
        "f5": "5 orders, drafts, duplicates", "f6": "6 business practice", "unsure": "unsure",
        "part_live": "part: live", "part_dead": "part: dead",
    }
    chips = []
    for cls, text in labels.items():
        fill, stroke, color, extra = CLASS_STYLE[cls]
        dashed = "border-style: dashed;" if "dasharray" in extra else ""
        chips.append(f'<span style="background:{fill};border-color:{stroke};color:{color};{dashed}">{text}</span>')
    return '<div class="legend">' + "".join(chips) + "</div>"


def build_html(account, mmd, note_md, analysis=True):
    """position.html: the diagram, the legend, the note, a link to documents.csv. Offline."""
    report_title = "position" if analysis else "filing map"
    legend = legend_html() if analysis else (
        "<p>The arrows show where documents are filed. They do not establish governing terms, "
        "legal relationships or current status.</p>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(account)} — {report_title}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<h1>{html.escape(account)} — {report_title}</h1>
<p class="links"><a href="README.md">README.md</a> <a href="documents.csv">documents.csv</a> <a href="position.mmd">position.mmd</a> <a href="../../INDEX.html">all accounts</a></p>
{legend}
<pre class="mermaid">
{html.escape(mmd, quote=False)}</pre>
<div class="note">
{md_to_html(note_md)}
</div>
<script src="../../assets/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad: true, securityLevel: 'strict', theme: 'neutral'}});</script>
</body>
</html>
"""


# --------------------------------------------------------------------------- one account
def retire_visuals(folder=None):
    """Remove only stale generated visual artifacts when their text inputs change."""
    if folder is not None:
        for name in ("position.mmd", "position.html"):
            (folder / name).unlink(missing_ok=True)
    (OUT / "INDEX.html").unlink(missing_ok=True)
    # Other account diagrams can remain current after an account-only report refresh.
    # Keep their shared renderer, but do not leave an unused visual bundle behind.
    if not any(OUT.glob("*/*/position.html")):
        (OUT / "assets" / "mermaid.min.js").unlink(missing_ok=True)


def ensure_visual_assets():
    """Copy the local renderer only for an explicitly requested visual output."""
    target_js = OUT / "assets" / "mermaid.min.js"
    if not MERMAID_JS.exists():
        fail(f"{rel(MERMAID_JS)} is missing; the diagrams cannot render offline.")
    if not target_js.exists() or target_js.read_bytes() != MERMAID_JS.read_bytes():
        target_js.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MERMAID_JS, target_js)
        say(f"copied assets/mermaid.min.js to {rel(target_js)}")


def write_account(ctx, account, settled, prose, all_rows, visuals=False):
    """Status folders with copies, documents.csv and README.md; optional diagrams/HTML."""
    folder = account_folder(ctx["side"], account)
    folder.mkdir(parents=True, exist_ok=True)
    for name in [TO_JUDGE, "files"] + STATUS_FOLDERS:
        target = folder / name
        if target.exists():
            shutil.rmtree(target)
    for name in STATUS_FOLDERS:
        (folder / name).mkdir()

    rows = [r for r in all_rows if r["account"] == account]
    filed = {r["doc_id"]: r["filed_as"] for r in rows}

    copied = 0
    used_names = {}
    for doc_id, p in settled.items():
        inv = ctx["inventory"].get(doc_id, {})
        source = WORK_FILES / f"{doc_id}.{inv.get('ext', '')}"
        if not source.exists():
            warn(f"{account}: {rel(source)} is missing (run /prepare again); doc {doc_id} not copied")
            continue
        status_folder = folder / p["folder"]
        name = filed.get(doc_id) or filed_name(doc_id, inv.get("ext", ""), unresolved=True,
                                               pages=inv.get("pages", ""))
        target = status_folder / unique_filed_name(name, used_names.setdefault(status_folder, set()))
        shutil.copyfile(source, target)
        copied += 1

    write_csv(folder / "documents.csv", rows, CORPUS_COLUMNS)
    note = build_note(ctx, account, settled, prose, filed=filed)
    write_text(folder / "README.md", note)
    if visuals:
        ensure_visual_assets()
        mmd = build_mermaid(ctx, account, settled)
        write_text(folder / "position.mmd", mmd)
        write_text(folder / "position.html", build_html(account, mmd, note))
    else:
        retire_visuals(folder)

    counts = {f: sum(1 for p in settled.values() if p["folder"] == f) for f in STATUS_FOLDERS}
    say(f"{account}: {copied} files copied into status folders; "
        + ", ".join(f"{f.split('-')[0]}={n}" for f, n in counts.items())
        + f"; written {rel(folder)}/README.md, documents.csv"
        + (", position.mmd, position.html" if visuals else ""))


EMPTY_ACCOUNT_POSITION = ("Nothing is filed to this account. No document in the pile was matched "
                          "to this ERP row, so nothing was read or judged for it.")


def accounts_with_documents(ctx):
    """ERP accounts (not streams) that at least one document was sorted to, in ERP order."""
    return [a for a in ctx["accounts"] if a not in ctx["streams"] and docs_sorted_to(ctx, a)]


def empty_accounts(ctx, settled_by_account):
    """ERP accounts with no documents at all. They need no judge: place.py writes them itself."""
    return [a for a in ctx["accounts"]
            if a not in ctx["streams"] and a not in settled_by_account and not docs_sorted_to(ctx, a)]


def add_empty_accounts(ctx, settled_by_account):
    """Give every zero-document account an empty placement set, so it is written like the rest.

    No judge is spent on an account with nothing in it: the folder, the README that says
    nothing is filed and the empty diagram are written here. Returns the accounts added, and
    leaves settled_by_account in ERP order.
    """
    added = empty_accounts(ctx, settled_by_account)
    for account in added:
        settled_by_account[account] = ({}, {"position": EMPTY_ACCOUNT_POSITION})
    ordered = {a: settled_by_account[a] for a in ctx["accounts"] if a in settled_by_account}
    settled_by_account.clear()
    settled_by_account.update(ordered)
    return added


def settled_for_all_accounts(ctx):
    """{account: (settled placements, prose)} for every account that has a placements file."""
    result = {}
    for account in ctx["accounts"]:
        if account in ctx["streams"]:
            continue
        placements = load_placements(ctx, account)
        if placements is None:
            continue
        result[account] = settle_placements(ctx, account, placements)
    return result


# --------------------------------------------------------------------------- the index
def account_summary(ctx, account, settled, prose):
    """One ACCOUNTS.csv row."""
    erp_row = next((a for a in ctx["erp"].get("accounts", []) if a.get("account") == account), {})
    row = {c: "" for c in ACCOUNTS_COLUMNS}
    row.update({"account": account, "side": ctx["side"], "account_number": erp_row.get("account_number", ""),
                "country": erp_row.get("country", ""), "review_status": "not reviewed"})
    if account in ctx["streams"]:
        row["treated_as_stream_of"] = ctx["streams"][account][0]
        for col in ACCOUNTS_COLUMNS:
            if col.startswith("n_") or col == "open_questions":
                row[col] = "0"
        return row
    doc_ids = [r["doc_id"] for r in docs_sorted_to(ctx, account)]
    row["n_documents"] = str(len(doc_ids))
    if settled is None:
        return row
    def docs_in(folder):
        return join_multi(doc_label(d) for d, p in sorted(settled.items()) if p["folder"] == folder)
    row["governing_docs"] = docs_in("1-governs-trade")
    row["part_docs"] = docs_in("2-governs-part-of-trade")
    count_cols = dict(zip(STATUS_FOLDERS, ["n_1_governs_trade", "n_2_part", "n_3_live_not_trade", "n_4_not_live",
                                           "n_5_orders_drafts_duplicates", "n_6_business_practice", "n_unsure"]))
    for folder, col in count_cols.items():
        row[col] = str(sum(1 for p in settled.values() if p["folder"] == folder))
    questions = (prose or {}).get("questions", "").strip()
    if not questions or questions.lower().rstrip(".") in ("none", "none found", "no questions"):
        row["open_questions"] = "0"
    else:
        numbered = re.findall(r"^\s*\d+[.)]\s+\S", questions, re.M)
        row["open_questions"] = str(len(numbered)) if numbered else "not numbered"
        if not numbered:
            warn(f"{account}: Questions for the business must be numbered so the index can count them")
    if any(c.get("doc_id") in settled for c in ctx["corrections"]):
        row["review_status"] = "corrections applied"
    return row


def index_links(side, account):
    """Relative links from out/ to an account's files, percent-encoded."""
    base = quote(f"{side}/{safe_folder_name(account)}", safe="/")
    return {"readme": f"{base}/README.md", "csv": f"{base}/documents.csv", "html": f"{base}/position.html"}


def sort_log_summary(ctx):
    """Holding folders with their names, names needing a decision, streams — as markdown lines."""
    lines = []
    holding = {h: {} for h in HOLDING_FOLDERS}
    for r in ctx["sort_rows"]:
        target = r.get("account", "")
        for h in HOLDING_FOLDERS:
            if target == h or target.startswith(h + "/"):
                name = target.split("/", 1)[1] if "/" in target else "(no name)"
                holding[h].setdefault(name, []).append(r["doc_id"])
    for h in HOLDING_FOLDERS:
        if holding[h]:
            lines.append(f"- `{h}`: " + "; ".join(f"{name} ({', '.join(doc_label(d) for d in docs)})"
                                                  for name, docs in holding[h].items()))
    no_card = [r["doc_id"] for r in ctx["sort_rows"] if r.get("account") == "_no-card"]
    if no_card:
        lines.append("- no card yet (run /read): " + ", ".join(doc_label(d) for d in no_card))
    undecided = {}
    for doc_id, card in ctx["cards"].items():
        for name in names_from_card(card, ctx["our_names"]):
            row = entity_row_for(ctx["entity_by_name"], name)
            if row is None or row.get("account") == "_not-sure" or row.get("confidence", "").lower() == "not sure":
                undecided.setdefault(name, []).append(doc_id)
    if undecided:
        lines.append("- names that need a decision in `inputs/entity-map.csv`: "
                     + "; ".join(f"{n} ({', '.join(doc_label(d) for d in sorted(set(docs)))})" for n, docs in undecided.items()))
    else:
        lines.append("- names that need a decision: none")
    for stream, (main, _) in ctx["streams"].items():
        lines.append(f'- stream: ERP row "{stream}" treated as one with "{main}"')
    return lines


def needs_a_decision(all_rows):
    """Read documents in a holding folder, grouped by the name that needs the user's decision.

    One markdown bullet per name. These have cards but no ERP account, so no judge saw them;
    they are in CORPUS.csv as `unassessed (no account)` and are listed here so the user can map
    the name in inputs/entity-map.csv and run /analyse for that account.
    """
    groups = {}
    for row in all_rows:
        if row.get("status") != UNASSESSED:
            continue
        holding = holding_folder_of(row.get("account", ""))
        if not holding:
            continue
        key = (holding.split("/", 1)[0], holding_name_of(row.get("account", "")))
        groups.setdefault(key, []).append(row["doc_id"])
    if not groups:
        return ["- none"]
    lines = []
    for (folder, name), docs in sorted(groups.items()):
        lines.append(f"- {name} (`{folder}`): " + ", ".join(doc_label(d) for d in sorted(docs))
                     + " — map the name in `inputs/entity-map.csv`, then run /analyse for that account")
    return lines


def write_index(ctx, settled_by_account, all_rows, visuals=False):
    """CSV/Markdown index and account lists; optional HTML and offline visual assets."""
    side = ctx["side"]
    if visuals:
        ensure_visual_assets()
    else:
        for account in settled_by_account:
            retire_visuals(account_folder(side, account))
        retire_visuals()

    for account in settled_by_account:
        rows = [r for r in all_rows if r["account"] == account]
        write_csv(account_folder(side, account) / "documents.csv", rows, CORPUS_COLUMNS)

    write_csv(OUT / side / "CORPUS.csv", all_rows, CORPUS_COLUMNS)
    account_rows = [account_summary(ctx, a, *settled_by_account.get(a, (None, None))) for a in ctx["accounts"]]
    write_csv(OUT / side / "ACCOUNTS.csv", account_rows, ACCOUNTS_COLUMNS)

    unreadable = [(r["doc_id"], r["original_path"], ctx["inventory"].get(r["doc_id"], {}).get("note", ""))
                  for r in ctx["sort_rows"] if r.get("account") == "_unreadable"]

    md = [f"# Accounts ({side})", "",
          "| account | governing docs | 1 | 2 | 3 | 4 | 5 | 6 | unsure | docs | open questions | links |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    html_rows = []
    for row in account_rows:
        account = row["account"]
        if row["treated_as_stream_of"]:
            md.append(f"| {md_cell(account)} | stream of {md_cell(row['treated_as_stream_of'])} | | | | | | | | | | |")
            html_rows.append(f"<tr><td>{html.escape(account)}</td><td>stream of {html.escape(row['treated_as_stream_of'])}</td>"
                             + "<td></td>" * 10 + "</tr>")
            continue
        links = index_links(side, account)
        judged = account in settled_by_account
        counts = [row[c] for c in ("n_1_governs_trade", "n_2_part", "n_3_live_not_trade", "n_4_not_live",
                                   "n_5_orders_drafts_duplicates", "n_6_business_practice", "n_unsure")]
        link_md = (f"[note]({links['readme']}) · [list]({links['csv']})" if judged else "not judged yet")
        if judged and visuals:
            link_md = f"[position]({links['html']}) · " + link_md
        link_html = (f'<a href="{links["html"]}">position</a> · <a href="{links["readme"]}">note</a> · '
                     f'<a href="{links["csv"]}">list</a>' if judged else "not judged yet")
        md.append(f"| {md_cell(account)} | {md_cell(row['governing_docs'] or ('not judged' if not judged else 'none'))} | "
                  + " | ".join(counts) + f" | {row['n_documents']} | {row['open_questions']} | {link_md} |")
        html_rows.append("<tr>" + "".join(f"<td>{html.escape(x)}</td>" for x in
                                          [account, row["governing_docs"] or ("not judged" if not judged else "none")] + counts
                                          + [row["n_documents"], row["open_questions"]]) + f"<td>{link_html}</td></tr>")
    md += ["", "## Needs a decision", "",
           "Read, but no ERP account: their status is not assessed until the name is mapped.", ""]
    md += needs_a_decision(all_rows)
    md += ["", "## Files not readable by the kit", ""]
    md += [f"- doc {d}: `{p}` ({n})" for d, p, n in unreadable] or ["- none"]
    md += ["", "## Sort log summary", ""] + sort_log_summary(ctx)
    md += ["", f"Full table: `{side}/CORPUS.csv` (one row per document and target); accounts: `{side}/ACCOUNTS.csv`.", ""]
    write_text(OUT / "INDEX.md", "\n".join(md))

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Accounts — {html.escape(side)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<h1>Accounts ({html.escape(side)})</h1>
<p class="links"><a href="{quote(side)}/CORPUS.csv">CORPUS.csv</a> <a href="{quote(side)}/ACCOUNTS.csv">ACCOUNTS.csv</a> <a href="INDEX.md">INDEX.md</a></p>
<table><thead><tr><th>account</th><th>governing docs</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>unsure</th><th>docs</th><th>open questions</th><th>links</th></tr></thead>
<tbody>
{chr(10).join(html_rows)}
</tbody></table>
<h2>Needs a decision</h2>
{md_to_html(chr(10).join(needs_a_decision(all_rows)))}
<h2>Files not readable by the kit</h2>
{md_to_html(chr(10).join([f"- doc {d}: `{p}` ({n})" for d, p, n in unreadable] or ["- none"]))}
<h2>Sort log summary</h2>
{md_to_html(chr(10).join(sort_log_summary(ctx)))}
</body>
</html>
"""
    if visuals:
        write_text(OUT / "INDEX.html", page)
    say(f"written {rel(OUT / side / 'CORPUS.csv')} ({len(all_rows)} rows), {rel(OUT / side / 'ACCOUNTS.csv')} "
        f"({len(account_rows)} rows), out/INDEX.md" + (", out/INDEX.html" if visuals else ""))
    say(f"totals: {len(settled_by_account)} accounts judged of {len([a for a in ctx['accounts'] if a not in ctx['streams']])}; "
        f"{len(unreadable)} files not readable by the kit")


# --------------------------------------------------------------------------- main
def main():
    parser = argparse.ArgumentParser(description="Generate account folders, Markdown notes and CSV lists.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--account", help="rebuild one account (name exactly as the ERP row)")
    group.add_argument("--index", action="store_true", help="rebuild CORPUS.csv, ACCOUNTS.csv, INDEX.md")
    group.add_argument("--all", action="store_true", help="rebuild every judged account, then the index")
    group.add_argument("--accounts-with-documents", action="store_true",
                       help="list the ERP accounts a document was sorted to, one per line "
                            "(the accounts a judge is worth spending on)")
    parser.add_argument("--visuals", action="store_true", help="also build analysis diagrams, HTML and offline assets")
    args = parser.parse_args()

    ctx = load_context()
    if args.accounts_with_documents:
        for account in accounts_with_documents(ctx):
            print(account)
        return 0

    settled_by_account = settled_for_all_accounts(ctx)
    empties = add_empty_accounts(ctx, settled_by_account)
    all_rows = build_all_rows(ctx, {a: s for a, (s, _) in settled_by_account.items()})

    if args.account:
        account = args.account
        if account not in ctx["accounts"]:
            fail(f"{account!r} is not an ERP account. Accounts: " + "; ".join(ctx["accounts"]))
        if account in ctx["streams"]:
            fail(f"{account!r} is a stream of {ctx['streams'][account][0]!r}; judge the main account instead.")
        if account not in settled_by_account:
            fail(f"work/placements/{safe_folder_name(account)}.csv is missing. Run /judge \"{account}\" first.")
        settled, prose = settled_by_account[account]
        write_account(ctx, account, settled, prose, all_rows, visuals=args.visuals)
        return 0

    if args.all:
        for account, (settled, prose) in settled_by_account.items():
            write_account(ctx, account, settled, prose, all_rows, visuals=args.visuals)
        if not settled_by_account:
            warn("no account has a placements file yet; run /judge first. Writing the index anyway.")
    else:
        # An account with no documents has no judge and no placements file, so --index is the
        # only run that would ever write it. Write it here rather than leave a dead link.
        for account in empties:
            settled, prose = settled_by_account[account]
            write_account(ctx, account, settled, prose, all_rows, visuals=args.visuals)
    write_index(ctx, settled_by_account, all_rows, visuals=args.visuals)
    return 0


if __name__ == "__main__":
    sys.exit(main())
