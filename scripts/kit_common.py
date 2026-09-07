"""Shared helpers for the stage 1 scripts (check, prepare, sort, place).

Everything here is plain: paths relative to the kit root, CSV read/write, loading the
sort cards, the entity map, the corrections, and a few small text helpers. No third-party
imports. Every path is a pathlib.Path so the same code runs on macOS, Windows and Linux.
"""

import csv
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- paths
KIT = Path(__file__).resolve().parent.parent
WORK = KIT / "work"
OUT = KIT / "out"
INPUTS = KIT / "inputs"
ASSETS = KIT / "assets"
STAGE1 = KIT / "stage1"

WORK_FILES = WORK / "files"
WORK_TEXT = WORK / "text"
WORK_CARDS = WORK / "cards"
WORK_PLACEMENTS = WORK / "placements"
WORK_LOGS = WORK / "logs"
INVENTORY_CSV = WORK / "inventory.csv"
ERP_JSON = WORK / "erp.json"
SORT_LOG_CSV = WORK_LOGS / "sort.csv"

ERP_RECORD_CSV = INPUTS / "erp-record.csv"
ENTITY_MAP_CSV = INPUTS / "entity-map.csv"
CORRECTIONS_CSV = INPUTS / "corrections.csv"
OUR_ENTITIES_CSV = INPUTS / "our-entities.csv"

MERMAID_JS = ASSETS / "mermaid.min.js"
NOTE_TEMPLATE = STAGE1 / "position-note.md"

# --------------------------------------------------------------------------- fixed names
STATUS_FOLDERS = [
    "1-governs-trade",
    "2-governs-part-of-trade",
    "3-live-not-trade",
    "4-not-live",
    "5-orders-drafts-duplicates",
    "6-business-practice",
    "unsure",
]
HOLDING_FOLDERS = ["_not-on-the-list", "_not-sure", "_no-name-found"]
TO_JUDGE = "_to-judge"

READABLE_EXTS = {
    "pdf": "pdf",
    "docx": "docx",
    "png": "image", "jpg": "image", "jpeg": "image", "tif": "image", "tiff": "image",
}
ERP_EXTS = {"csv": "csv", "xlsx": "xlsx"}

NOT_FOUND = "not found"
MULTI_SEP = " | "

INVENTORY_COLUMNS = [
    "doc_id", "original_path", "file_name", "ext", "file_type", "readable", "sha256",
    "size_bytes", "pages", "scanned_pages", "text_pages", "page_kinds", "paragraphs",
    "language", "docx_author", "docx_created", "docx_modified", "docx_tracked_changes",
    "docx_comments", "has_images", "title_guess", "note",
]

# The card keys, exactly as stage1/sort-card.md lists them.
CARD_KEYS = [
    "doc_id",
    "q1_title", "q1_kind",
    "q2_their_signing_entities", "q2_their_group_companies", "q2_our_entity", "q2_evidence",
    "q3_signed", "q3_evidence",
    "q4_start_date", "q4_start_basis", "q4_end", "q4_ended_sign", "q4_status", "q4_evidence",
    "q5_parts", "q5_parts_detail", "q5_precedence",
    "q6_attaches_to", "q6_replaces", "q6_referred_to_not_in_pile", "q6_evidence",
    "q7_trade_scope", "q7_what_makes_it_govern", "q7_evidence",
    "q8_entities_covered", "q8_countries",
    "q9_copy_or_draft_of", "q9_better_copy",
    "q10_oddities",
]

ENTITY_MAP_COLUMNS = ["name_as_printed", "account", "basis", "confidence", "decided_by", "note"]
CORRECTIONS_COLUMNS = ["doc_id", "field", "value", "reason"]
SORT_LOG_COLUMNS = ["doc_id", "original_path", "companies_found", "account", "basis", "confidence", "note"]
PLACEMENT_COLUMNS = [
    "doc_id", "tree", "folder", "reason", "attaches_to", "attach_kind", "replaces",
    "parts_status", "limit", "overlap", "question", "what_would_change",
]
CORPUS_COLUMNS = [
    # identity
    "doc_id", "original_path", "file_type", "pages", "scanned_pages", "language",
    "docx_author", "docx_created", "docx_modified", "docx_tracked_changes",
    # sort
    "side", "account", "companies_found", "match_basis", "match_confidence", "sort_note",
    # card
    "kind", "title", "their_signing_entities", "their_group_companies", "our_entity", "signed",
    "start_date", "start_basis", "end", "ended_sign", "status", "parts", "attaches_to",
    "replaces", "referred_to_not_in_pile", "trade_scope", "what_makes_it_govern",
    "entities_covered", "countries_covered", "copy_or_draft_of", "oddities",
    # judge
    "tree", "folder", "placement_reason", "overlap_or_conflict", "question_for_business",
    # evidence
    "evidence_signed", "evidence_dates", "evidence_companies", "evidence_trade",
    # reviewer
    "legal_agrees", "sales_agrees", "correct_folder", "comment",
]
REVIEWER_COLUMNS = ["legal_agrees", "sales_agrees", "correct_folder", "comment"]
ACCOUNTS_COLUMNS = [
    "account", "side", "account_number", "country", "treated_as_stream_of", "governing_docs",
    "part_docs", "n_1_governs_trade", "n_2_part", "n_3_live_not_trade", "n_4_not_live",
    "n_5_orders_drafts_duplicates", "n_6_business_practice", "n_unsure", "n_documents",
    "open_questions", "review_status",
]

CONFIDENCE_RANK = {"sure": 3, "fairly sure": 2, "not sure": 1}


# --------------------------------------------------------------------------- messages
def say(message):
    """Print one progress line."""
    print(message)


def warn(message):
    """Print a warning the user should read. Never stops the run."""
    print("WARNING: " + message)


def fail(message):
    """Print a plain message and exit 1. Used for problems the user must fix."""
    print("STOP: " + message)
    sys.exit(1)


# --------------------------------------------------------------------------- csv helpers
def read_csv(path, required_columns=None):
    """Read a CSV into a list of dicts (UTF-8, BOM tolerated). Missing file -> []."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            clean = {}
            for key, value in row.items():
                if key is None:
                    continue
                clean[key.strip()] = (value or "").strip() if isinstance(value, str) else (value or "")
            rows.append(clean)
    if required_columns:
        have = set(rows[0].keys()) if rows else set(_header_of(path))
        missing = [c for c in required_columns if c not in have]
        if missing:
            warn(f"{rel(path)} is missing columns: {', '.join(missing)}")
    return rows


def _header_of(path):
    """Return the header row of a CSV file (used when the file has no data rows)."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            return [c.strip() for c in row]
    return []


def write_csv(path, rows, columns):
    """Write rows (dicts) to a CSV with exactly these columns, in this order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def write_text(path, text):
    """Write a UTF-8 text file, creating parent folders."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path):
    """Read a JSON file; missing file -> None."""
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    """Write JSON, indented, UTF-8, stable key order as given."""
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- small text helpers
def rel(path):
    """Path shown relative to the kit root when possible (for messages)."""
    try:
        return Path(path).resolve().relative_to(KIT).as_posix()
    except ValueError:
        return str(path)


def join_multi(values):
    """Join several values into one CSV cell with ' | '. Blank values are dropped."""
    return MULTI_SEP.join(str(v).strip() for v in values if str(v).strip())


def split_multi(cell):
    """Split a ' | ' joined cell back into a list. Blank -> []."""
    if not cell:
        return []
    return [part.strip() for part in str(cell).split("|") if part.strip()]


def safe_folder_name(name):
    """Portable single path component; never let an ERP name escape the output folder."""
    result = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).rstrip(' .')
    if not result:
        result = '_unnamed'
    if re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', result, re.I):
        result = '_' + result
    return result


def doc_label(doc_id):
    """'001' -> 'doc 001'."""
    return f"doc {doc_id}"


def norm_name(name):
    """Normalise a company name for matching: lower-case, single spaces, trimmed."""
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


def is_empty_answer(value):
    """True for blank, 'none', 'not found', 'n/a' and similar non-answers."""
    return norm_name(value) in {"", "none", "not found", "n/a", "na", "-", "—"}


def strip_role(name_with_role):
    """'Acme Ltd (signatory)' -> 'Acme Ltd'. Only a trailing parenthesis is removed."""
    return re.sub(r"\s*\([^()]*\)\s*$", "", name_with_role.strip()).strip()


def names_from_card(card, our_names=()):
    """Company names on their side, from q2: signing entities then group companies.

    Roles are stripped; 'none' / 'not found' are not names; our own entity names (from
    inputs/our-entities.csv) and the card's own q2_our_entity are left out. Order kept,
    duplicates dropped (case-insensitive).
    """
    excluded = {norm_name(n) for n in our_names}
    excluded.add(norm_name(strip_role(card.get("q2_our_entity", ""))))
    names = []
    seen = set()
    for key in ("q2_their_signing_entities", "q2_their_group_companies"):
        for item in split_multi(card.get(key, "")):
            name = strip_role(item)
            if is_empty_answer(name) or norm_name(name) in excluded:
                continue
            if norm_name(name) in seen:
                continue
            seen.add(norm_name(name))
            names.append(name)
    return names


def truncate(text, limit):
    """Cut text to `limit` characters, adding an ellipsis when cut."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


# --------------------------------------------------------------------------- loaders
def load_inventory():
    """work/inventory.csv as a list of dicts. Fails plainly if missing."""
    if not INVENTORY_CSV.exists():
        fail("work/inventory.csv is missing. Run /prepare first.")
    return read_csv(INVENTORY_CSV)


def load_erp():
    """work/erp.json as a dict. Fails plainly if missing."""
    data = read_json(ERP_JSON)
    if data is None:
        fail("work/erp.json is missing. Run /prepare first.")
    return data


def load_card(doc_id, quiet=False):
    """One sort card from work/cards/<id>.json. Missing keys -> 'not found' with a warning.

    Returns None when there is no card.
    """
    path = WORK_CARDS / f"{doc_id}.json"
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        warn(f"card {rel(path)} could not be read ({err}); treated as missing")
        return None
    if not isinstance(raw, dict):
        warn(f"card {rel(path)} is not a JSON object; treated as missing")
        return None
    card = {}
    missing = []
    for key in CARD_KEYS:
        value = raw.get(key)
        if value is None:
            missing.append(key)
            value = NOT_FOUND
        if not isinstance(value, str):
            value = join_multi(value) if isinstance(value, list) else str(value)
        card[key] = value.strip()
    if not card["doc_id"] or card["doc_id"] == NOT_FOUND:
        card["doc_id"] = doc_id
    if missing and not quiet:
        warn(f"card for doc {doc_id} has no key {', '.join(missing)}; filled with 'not found'")
    extra = sorted(set(raw) - set(CARD_KEYS))
    if extra and not quiet:
        warn(f"card for doc {doc_id} has keys the card does not define (ignored): {', '.join(extra)}")
    return card


def load_all_cards(quiet=False):
    """Every card in work/cards as {doc_id: card}."""
    cards = {}
    if not WORK_CARDS.exists():
        return cards
    for path in sorted(WORK_CARDS.glob("*.json")):
        doc_id = path.stem
        card = load_card(doc_id, quiet=quiet)
        if card is not None:
            cards[doc_id] = card
    return cards


def load_entity_map():
    """inputs/entity-map.csv as {normalised name: row}. User rows win over claude rows.

    Also returns the rows in file order, so callers can report what was read.
    """
    rows = read_csv(ENTITY_MAP_CSV, required_columns=ENTITY_MAP_COLUMNS)
    by_name = {}
    for row in rows:
        key = norm_name(row.get("name_as_printed", ""))
        if not key:
            continue
        row = {c: row.get(c, "") for c in ENTITY_MAP_COLUMNS}
        if row['basis'] == 'known group' and row['confidence'] == 'sure':
            warn(f"entity map: {row['name_as_printed']!r}: known group confidence capped at fairly sure")
            row['confidence'] = 'fairly sure'
        existing = by_name.get(key)
        if existing is None:
            by_name[key] = row
            continue
        # user rows win; among equals the later row wins
        if existing.get("decided_by", "").lower() == "user" and row.get("decided_by", "").lower() != "user":
            continue
        by_name[key] = row
    return by_name, rows


def load_corrections():
    """inputs/corrections.csv rows (may be empty)."""
    rows = read_csv(CORRECTIONS_CSV, required_columns=CORRECTIONS_COLUMNS)
    return [r for r in rows if r.get("doc_id")]


def apply_corrections_to_card(card, corrections):
    """Return a copy of the card with card-key corrections for its doc applied."""
    fixed = dict(card)
    for row in corrections:
        if row.get("doc_id") == card.get("doc_id") and row.get("field") in CARD_KEYS:
            fixed[row["field"]] = row.get("value", "")
    return fixed


def apply_corrections_to_placement(placement, corrections):
    """Return a copy of the placement row with placement-column corrections applied."""
    fixed = dict(placement)
    for row in corrections:
        if row.get("doc_id") == placement.get("doc_id") and row.get("field") in PLACEMENT_COLUMNS:
            fixed[row["field"]] = row.get("value", "")
    return fixed


def load_our_entities():
    """inputs/our-entities.csv names (list of strings), or [] when absent."""
    rows = read_csv(OUR_ENTITIES_CSV)
    return [r.get("name", "") for r in rows if r.get("name", "").strip()]


def load_sort_log():
    """work/logs/sort.csv rows, or [] when absent."""
    return read_csv(SORT_LOG_CSV)


def erp_account_names(erp):
    """List of account names from erp.json, in ERP order."""
    return list(dict.fromkeys(a.get("account", "") for a in erp.get("accounts", []) if a.get("account", "")))


def stream_map(erp, entity_by_name):
    """ERP rows the entity map declares to be streams: {stream row: (main row, map row)}.

    A stream is an entity-map row whose name is itself an ERP row and whose account is a
    different ERP row.
    """
    names = erp_account_names(erp)
    by_norm = {norm_name(n): n for n in names}
    streams = {}
    for name in names:
        row = entity_by_name.get(norm_name(name))
        if not row:
            continue
        target = by_norm.get(norm_name(row.get("account", "")))
        if target and norm_name(target) != norm_name(name):
            streams[name] = (target, row)
    return streams


def account_folder(side, account):
    """out/<side>/<account> with Windows-illegal characters replaced."""
    return OUT / side / safe_folder_name(account)
