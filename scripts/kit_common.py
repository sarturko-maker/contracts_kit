"""Shared helpers for the stage 1 scripts (check, prepare, sort, place).

Everything here is plain: paths relative to the kit root, CSV read/write, loading the
sort cards, the entity map, the corrections, and a few small text helpers. No third-party
imports. Every path is a pathlib.Path so the same code runs on macOS, Windows and Linux.
"""

import csv
import json
import re
import sys
import unicodedata
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

# The card questions that require evidence (stage1/sort-card.md: a page or clause reference
# and the exact words, forty or fewer).
CARD_EVIDENCE_KEYS = ["q2_evidence", "q3_evidence", "q4_evidence", "q6_evidence", "q7_evidence"]
EVIDENCE_WORD_LIMIT = 40

ENTITY_MAP_COLUMNS = ["name_as_printed", "account", "basis", "confidence", "decided_by", "note"]
CORRECTIONS_COLUMNS = ["doc_id", "field", "value", "reason"]
SORT_LOG_COLUMNS = ["doc_id", "original_path", "companies_found", "account", "basis", "confidence", "note"]
PLACEMENT_COLUMNS = [
    "doc_id", "tree", "folder", "reason", "attaches_to", "attach_kind", "replaces",
    "parts_status", "limit", "overlap", "question", "what_would_change",
]
CORPUS_COLUMNS = [
    # identity
    "doc_id", "original_path", "filed_as", "file_type", "pages", "scanned_pages", "language",
    "docx_author", "docx_created", "docx_modified", "docx_tracked_changes",
    # sort
    "side", "account", "companies_found", "match_basis", "match_confidence", "sort_note",
    # card
    "kind", "title", "their_signing_entities", "their_group_companies", "our_entity", "signed",
    "start_date", "start_basis", "end", "ended_sign", "status", "status_per_document", "parts", "attaches_to",
    "replaces", "referred_to_not_in_pile", "trade_scope", "what_makes_it_govern",
    "entities_covered", "countries_covered", "copy_or_draft_of", "oddities",
    # judge
    "tree", "folder", "placement_reason", "overlap_or_conflict", "question_for_business", "analysis_stage",
    # evidence
    "evidence_signed", "evidence_dates", "evidence_companies", "evidence_trade",
    # External review index: literal answers, not inferred native-card fields.
    "review_document", "review_parties", "review_execution", "review_term", "review_trade_scope",
    "review_group_scope", "review_links", "review_precedence", "review_parts", "review_gaps",
    "source_checks",
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


# The words one company is written with in two ways. Only the abbreviations the pile actually
# showed; a longer form is the key so 'Ltd' and 'Limited' meet in the middle. Foreign forms
# (GmbH, S.A., B.V.) are left exactly as printed: they are not English abbreviations.
COMPANY_WORDS = {
    "ltd": "limited",
    "limited": "limited",
    "plc": "public limited company",
    "public": "public",
    "svc": "services",
    "svcs": "services",
    "services": "services",
    "co": "company",
    "company": "company",
    "corp": "corporation",
    "corporation": "corporation",
    "inc": "incorporated",
    "incorporated": "incorporated",
    "&": "and",
    "and": "and",
}
TRAILING_PUNCTUATION = ".,;:!?'\"“”‘’()[]"


def group_key(name):
    """One key for the same company written two ways ('Svcs Ltd' and 'Services Limited').

    Used for grouping (holding folders) and as the second try for an entity-map lookup; the
    exact printed name, normalised by norm_name, is always tried first.
    """
    text = norm_name(name)
    text = re.sub(r"^the\s+", "", text)
    words = []
    for token in text.split(" "):
        token = token.strip(TRAILING_PUNCTUATION)
        if not token:
            continue
        words.append(COMPANY_WORDS.get(token, token))
    return " ".join(words).strip()


def entity_row_for(entity_by_name, name):
    """The entity-map row for a printed name: exact name first, then the group key.

    Returns None when nothing matches, or when several map rows share the group key and
    disagree about the account — that name still needs the user's decision.
    """
    row = entity_by_name.get(norm_name(name))
    if row is not None:
        return row
    key = group_key(name)
    if not key:
        return None
    matches = [r for printed, r in entity_by_name.items() if group_key(printed) == key]
    if not matches:
        return None
    accounts = {norm_name(r.get("account", "")) for r in matches}
    if len(accounts) > 1:
        warn(f"entity map: {name!r} looks like " + " and ".join(
            repr(r.get("name_as_printed", "")) for r in matches)
            + ", which are mapped to different accounts; treated as no decision")
        return None
    return matches[0]


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


# --------------------------------------------------------------------------- filed names
# Every generated copy under out/ is named from the record that put it there, never by an
# agent. The document number comes first, so two documents can never collide.
FILED_NAME_LIMIT = 120

# The card's question 1 kinds and the filer's free-text kinds, mapped to short slugs.
# First match wins, so the narrower words come before the wider ones.
KIND_SLUG_RULES = [
    (r"non[- ]?disclos|\bndas?\b|confidential", "nda"),
    (r"amend|side letter|variation|addend", "amendment"),
    (r"rebate|pricing|price list|discount", "rebate-letter"),
    (r"purchase order|\bp\.?o\.?\b|quotation|\bquote\b|order form|\borders?\b", "order"),
    (r"schedule|annex|appendix|exhibit", "schedule"),
    (r"credit application|credit account", "credit-application"),
    (r"local adoption|adoption of", "local-adoption"),
    (r"project|programme|program\b|\bsite\b|works agreement", "site-agreement"),
    (r"draft[ -]?master|unsigned master", "draft-master"),
    (r"master|framework|\bmsa\b|supply agreement|services agreement", "master-agreement"),
    (r"standard terms|terms and conditions|\bt&cs?\b|general terms", "standard-terms"),
    (r"guarantee|indemnit|surety", "guarantee"),
    (r"data (processing|terms)|code of conduct|\bedi\b|\bdpa\b|overlay", "overlay"),
    (r"internal|playbook|guidance", "internal-notes"),
    (r"letter|e-?mail|correspond", "letter"),
]
DRAFT_ANSWERS = {"nobody", "no", "none", "neither", "unsigned", "not signed", "no one"}
DUPLICATE_RE = re.compile(r"duplicate\s+of\s+(?:doc\s+)?(\d{2,})", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
ASCII_FOLDING = {"æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O", "ß": "ss", "đ": "d", "Đ": "D",
                 "ł": "l", "Ł": "L", "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D", "œ": "oe", "Œ": "OE"}


def ascii_only(text):
    """Plain ASCII: accents folded, everything else dropped. Windows and macOS safe."""
    text = "".join(ASCII_FOLDING.get(c, c) for c in str(text or ""))
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).encode("ascii", "ignore").decode("ascii")


def name_slug(text):
    """One filename word: ASCII, spaces to hyphens, only [A-Za-z0-9-.], no trailing dot."""
    text = ascii_only(text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^A-Za-z0-9.\-]", "", text)
    text = re.sub(r"-{2,}", "-", text)
    text = re.sub(r"\.{2,}", ".", text)
    return text.strip("-. ")


def kind_slug(kind):
    """A short slug for the card's q1 kind or a filer's free-text kind. '' when not stated."""
    text = ascii_only(kind).strip().lower()
    if is_empty_answer(text) or text in {"not assessed", "unknown", "unclear", "can't tell", "cant tell"}:
        return ""
    for pattern, slug in KIND_SLUG_RULES:
        if re.search(pattern, text):
            return slug
    slug = name_slug(" ".join(text.split()[:3])).lower()
    return slug[:24].rstrip("-.") or "other"


def date_slug(value):
    """YYYY-MM-DD when the text holds a date we can read, '' otherwise."""
    text = ascii_only(value).strip()
    if not text or is_empty_answer(text):
        return ""
    match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    if match:
        year, month, day = (int(g) for g in match.groups())
    else:
        match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b", text)
        if match:
            day, month, year = int(match.group(1)), _month_number(match.group(2)), int(match.group(3))
        else:
            match = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", text)
            if not match:
                return ""
            month, day, year = _month_number(match.group(1)), int(match.group(2)), int(match.group(3))
    if not month or not 1 <= month <= 12 or not 1 <= day <= 31 or not 1000 <= year <= 9999:
        return ""
    return f"{year:04d}-{month:02d}-{day:02d}"


def _month_number(word):
    word = word.lower().rstrip(".")
    for name, number in MONTHS.items():
        if name == word or (len(word) >= 3 and name.startswith(word)):
            return number
    return 0


def _fit(parts, suffix, limit):
    """Join the parts with spaces inside the length cap, shortening the longest part first."""
    parts = [p for p in parts if p]
    while len(" ".join(parts)) + len(suffix) > limit and len(parts) > 1:
        index = max(range(1, len(parts)), key=lambda i: len(parts[i]))
        if len(parts[index]) <= 1:
            break
        parts[index] = parts[index][:-1].rstrip("-. ") or parts[index][:1]
    name = " ".join(parts)
    if len(name) + len(suffix) > limit:
        name = name[: max(1, limit - len(suffix))]
    return (name.rstrip("-. ") or (parts[0] if parts else "document")) + suffix


def filed_name(doc_id, ext, kind=None, counterparty=None, date=None, status=None,
               duplicate_of=None, pages=None, unresolved=False):
    """The name of a generated copy: '<doc id> <kind> <counterparty> <date>[ <status>].<ext>'.

    A duplicate is '<doc id> duplicate-of-<other>.<ext>'; an unresolved identity is
    '<doc id> unidentified[ <pages>pp].<ext>'. Everything is sanitised to ASCII and to the
    characters Windows allows, and the whole name is capped at 120 characters. The name is
    never empty: with nothing but a document number it is '<doc id>.<ext>'.
    """
    prefix = name_slug(doc_id) or "document"
    extension = name_slug(ext).lstrip(".").lower()
    suffix = f".{extension}" if extension else ""

    if duplicate_of:
        other = name_slug(duplicate_of)
        return _fit([prefix, f"duplicate-of-{other}" if other else "duplicate"], suffix, FILED_NAME_LIMIT)
    if unresolved:
        parts = [prefix, "unidentified"]
        count = str(pages or "").strip()
        if count.isdigit() and int(count) > 0:
            parts.append(f"{int(count)}pp")
        return _fit(parts, suffix, FILED_NAME_LIMIT)

    kind_part = kind_slug(kind)
    party = name_slug(counterparty)
    day = date_slug(date)
    state = name_slug(status).lower()
    if state == "draft" and kind_part in ("master-agreement", "draft-master"):
        kind_part, state = "draft-master", ""
    elif kind_part == "draft-master" and state == "draft":
        state = ""
    return _fit([prefix, kind_part, party, day, state], suffix, FILED_NAME_LIMIT)


def is_unsigned_draft(card):
    """True when the card says nobody signed and the paper reads as a draft."""
    if not card:
        return False
    signed = norm_name(strip_role(card.get("q3_signed", "")))
    words = " ".join(str(card.get(k, "")) for k in ("q1_title", "q1_kind", "q9_copy_or_draft_of")).lower()
    return signed in DRAFT_ANSWERS and "draft" in words


def naming_from_card(card, placement=None):
    """filed_name() keywords from a sort card and, when it exists, the judge's placement."""
    placement = placement or {}
    kind = (card or {}).get("q1_kind", "")
    if is_unsigned_draft(card) and kind_slug(kind) == "master-agreement":
        kind = "draft-master"
    duplicate_of = ""
    for field in ("reason", "replaces", "attaches_to", "attach_kind"):
        match = DUPLICATE_RE.search(placement.get(field, "") or "")
        if match:
            duplicate_of = match.group(1)
            break
    if not duplicate_of and "duplicate" in (placement.get("attach_kind", "") or "").lower():
        match = re.search(r"\d{2,}", placement.get("attaches_to", "") or "")
        if match:
            duplicate_of = match.group(0)
    folder = (placement.get("folder", "") or "").strip()
    status = {"4-not-live": "not-live", "unsure": "unsure"}.get(folder, "")
    if not status and folder == "5-orders-drafts-duplicates" and is_unsigned_draft(card):
        status = "draft"
    return {"kind": kind, "date": (card or {}).get("q4_start_date", ""), "status": status,
            "duplicate_of": duplicate_of}


def counterparty_for(target, names=()):
    """The ERP account name when the copy sits in an account folder, else the printed company."""
    target = (target or "").strip()
    if target.startswith("_"):
        return target.split("/", 1)[1].strip() if "/" in target else ""
    if target:
        return target
    return names[0] if names else ""


def unique_filed_name(name, used):
    """Record a filed name in its folder. The document number keeps every name unique."""
    if name in used:
        raise AssertionError(f"filed name collision in one folder: {name!r}; "
                             "the document number prefix should have kept it unique")
    used.add(name)
    return name


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


def evidence_quotes(field):
    """The quoted words in one evidence field: `p.3: "the exact words" | cl.2: "more words"`.

    Anything between quotation marks is a quote. When a segment has no quotation marks the
    reference prefix ('p.3:') is dropped and the rest is treated as the quote, so an unquoted
    answer is still measured.
    """
    quotes = []
    for segment in split_multi(field):
        if is_empty_answer(segment):
            continue
        found = re.findall(r'["“]([^"”]+)["”]', segment)
        if found:
            quotes.extend(found)
            continue
        quotes.append(re.sub(r"^[^:]{1,40}:\s*", "", segment.strip()))
    return [q.strip() for q in quotes if q.strip()]


def card_warnings(card, our_names=()):
    """Warnings about one card, as a list of sentences. Never changes the card.

    Two checks: question 2 read the wrong way round (our entity in the other side's slot),
    and an evidence quote longer than forty words. The first needs inputs/our-entities.csv,
    so it is skipped when the caller has no list of our names.
    """
    messages = []
    card = card or {}
    doc_id = (card.get("doc_id") or "").strip() or "?"
    ours = {group_key(n) for n in our_names if str(n).strip()}
    if ours:
        our_entity = strip_role(card.get("q2_our_entity", ""))
        theirs = []
        for key in ("q2_their_signing_entities", "q2_their_group_companies"):
            for item in split_multi(card.get(key, "")):
                name = strip_role(item)
                if not is_empty_answer(name):
                    theirs.append(name)
        ours_in_our_slot = not is_empty_answer(our_entity) and group_key(our_entity) in ours
        ours_in_their_slot = any(group_key(name) in ours for name in theirs)
        if not ours_in_our_slot or ours_in_their_slot:
            messages.append(f"doc {doc_id}: question 2 may be reversed "
                            "(our entity in the other side's slot)")
    for key in CARD_EVIDENCE_KEYS:
        for quote in evidence_quotes(card.get(key, "")):
            count = len(quote.split())
            if count > EVIDENCE_WORD_LIMIT:
                messages.append(f"doc {doc_id}: {key} quotes {count} words; evidence is "
                                f"{EVIDENCE_WORD_LIMIT} words or fewer, exactly as printed")
    return messages


_OUR_NAMES_FOR_CHECKS = None


def our_names_for_checks():
    """Our entity names for the card checks, read once. [] when the file is not there yet."""
    global _OUR_NAMES_FOR_CHECKS
    if _OUR_NAMES_FOR_CHECKS is None:
        _OUR_NAMES_FOR_CHECKS = load_our_entities() if OUR_ENTITIES_CSV.exists() else []
    return _OUR_NAMES_FOR_CHECKS


def check_card(card, our_names=None, quiet=False):
    """Run the card checks and print what they found. Returns the warnings."""
    if our_names is None:
        our_names = our_names_for_checks()
    messages = card_warnings(card, our_names)
    if not quiet:
        for message in messages:
            warn(message)
    return messages


def load_card(doc_id, quiet=False):
    """One sort card from work/cards/<id>.json. Missing keys -> 'not found' with a warning.

    check_card() also warns when question 2 looks reversed or an evidence quote is too long.
    Nothing in the card is changed and nothing stops the run. Returns None when there is no card.
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
    check_card(card, quiet=quiet)
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


def stream_map(erp, entity_by_name, named_accounts=()):
    """ERP rows the entity map declares to be streams: {stream row: (main row, map row)}.

    A stream is an entity-map row whose name is itself an ERP row and whose account is a
    different ERP row. A stream explicitly named in a document keeps its own folder,
    unless a user decision explicitly maps it to the parent.
    """
    names = erp_account_names(erp)
    by_norm = {norm_name(n): n for n in names}
    named = {norm_name(n) for n in named_accounts}
    streams = {}
    for name in names:
        row = entity_by_name.get(norm_name(name))
        if not row:
            continue
        if norm_name(name) in named and row.get("decided_by") != "user":
            continue
        target = by_norm.get(norm_name(row.get("account", "")))
        if target and norm_name(target) != norm_name(name):
            streams[name] = (target, row)
    return streams


def account_folder(side, account):
    """out/<side>/<account> with Windows-illegal characters replaced."""
    return OUT / side / safe_folder_name(account)
