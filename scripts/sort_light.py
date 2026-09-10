"""File Review_Table_Light rows into account and status folders by script.

No model reads a contract here. The export's closed answers decide, dates anchor the links,
and anything the answers cannot settle goes to `unsure` or a holding folder with a flag.
The only model step is outside this script: --unmatched prints the customer names that
neither match an ERP account nor have an entity-map row, for one names-only decision turn.

Commands: --import [FILE] [--error-log FILE] [--as-at DATE], --unmatched, --file, --status.
"""

import argparse
from collections import Counter
import csv
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

from kit_common import (KIT, WORK, OUT, WORK_FILES, INVENTORY_CSV, STATUS_FOLDERS,
                        SORT_LOG_COLUMNS, read_csv, write_csv, read_json, write_json,
                        write_text, load_erp, erp_account_names, load_entity_map,
                        load_our_entities, entity_row_for, norm_name, group_key,
                        safe_folder_name, filed_name, join_multi, say, warn, fail, ENTITY_MAP_COLUMNS, ENTITY_MAP_CSV,
)

ROOT = WORK / "review-table-light"
ACTIVE = ROOT / "active.json"
SOURCE = WORK / "review-light-source.json"
OUTPUT = OUT / "sort"
SORT_LOG = WORK / "logs" / "sort.csv"
PLAYBOOKS = KIT / "inputs" / "business-practice.csv"
OUR_ENTITIES = KIT / "inputs" / "our-entities.csv"
VERSION = "sort-light-v1"

# Canonical keys; the export may number the headers and append the question text.
KEYS = ("title", "reference", "document_date", "customer_entity", "additional_customer_entities",
        "supplier_entity", "instrument", "supply_coverage", "group_mechanism", "signed", "status",
        "end_date", "relation_to_parent", "parent_agreement")
REQUIRED = ("customer_entity", "instrument", "supply_coverage", "signed", "status")
ALIASES = {"name": "file_name", "file_name": "file_name", "folder": "source_folder",
           "document_classification": "vendor_classification", "relation": "relation_to_parent",
           "parent": "parent_agreement", "date": "document_date"}

INSTRUMENTS = ("Global master agreement", "Master or supply agreement", "Local participation agreement",
               "Standard terms or account form", "Project agreement or statement of work",
               "Schedule or exhibit", "Amendment or side letter", "Pricing or rebate letter",
               "Notice letter", "Purchase order or call-off",
               "Purchase order or call-off carrying standard terms", "Quote or acknowledgement",
               "Quote or acknowledgement carrying standard terms", "NDA, MOU or letter of intent",
               "Guarantee or security", "Certificate or evidence", "Other overlay", "Mixed", "Other",
               "Unclear")
COVERAGE = ("All supply between the parties", "Substantially all supply", "Part of supply",
            "Named division or site", "Varies commercials only", "No supply coverage", "Unclear")
MECHANISM = ("Contracting for affiliates", "Adoption agreement", "Entity schedule",
             "Ordering entitlement", "None", "Unclear")
SIGNED = ("Signed by all parties", "Signed by one party", "Unsigned", "Draft", "Signature not established")
STATUS = ("Current", "Expired", "Terminated", "Not yet effective", "Unclear")
RELATIONS = ("None", "Forms part of", "Accedes to", "Placed under", "Agreed under", "Governed by",
             "Amends", "Extends", "Renews", "Supersedes", "Terminates", "Varies", "Confirms")
CLOSED = {"instrument": INSTRUMENTS, "supply_coverage": COVERAGE, "group_mechanism": MECHANISM,
          "signed": SIGNED, "status": STATUS, "relation_to_parent": RELATIONS}
MULTI = {"group_mechanism", "relation_to_parent"}

MASTERS = {"Global master agreement", "Master or supply agreement", "Standard terms or account form"}
GOVERNING = MASTERS | {"Local participation agreement", "Project agreement or statement of work",
                       "Schedule or exhibit", "Amendment or side letter"}
CHILDREN = {"Local participation agreement", "Schedule or exhibit", "Amendment or side letter",
            "Notice letter", "Pricing or rebate letter"}
TRANSACTIONS = {"Purchase order or call-off", "Purchase order or call-off carrying standard terms",
                "Quote or acknowledgement", "Quote or acknowledgement carrying standard terms"}
NON_GOVERNING = {"Pricing or rebate letter", "Notice letter", "NDA, MOU or letter of intent",
                 "Guarantee or security", "Certificate or evidence", "Other overlay"}
FULL = {"All supply between the parties", "Substantially all supply"}
PARTIAL = {"Part of supply", "Named division or site"}
ENDING = {"Terminates", "Supersedes"}
AMENDING = {"Amends", "Extends", "Renews", "Forms part of", "Agreed under", "Accedes to"}
SIDE_EFFECTS = {"Confirms", "Varies", "Terminates", "Placed under", "Governed by"}
INFERABLE = AMENDING | {"Governed by", "Placed under", "Varies", "Confirms"}
BASES = ("same name", "in the document", "known group")
CONFIDENCES = ("sure", "fairly sure", "not sure")
HOLDING_TARGETS = ("_not-sure", "_not-on-the-list")
F1, F2, F3, F4, F5, F6, UNSURE = STATUS_FOLDERS
BLANKS = {"", "—", "–", "-", "n/a", "na", "none", "null"}

MONTHS = {m: i for i, m in enumerate(("january", "february", "march", "april", "may", "june", "july",
                                      "august", "september", "october", "november", "december"), 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
DATE_PATTERNS = (
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
    re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b"),
    re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b"),
    re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b"),
)


# ---------------------------------------------------------------- parsing helpers

def blank(value):
    return norm_name(str(value or "")) in BLANKS


def dates_in(text):
    """Every date in the text, as ISO strings in order of appearance. Never guesses a year."""
    found = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(str(text or "")):
            groups = match.groups()
            try:
                if pattern is DATE_PATTERNS[0]:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                elif pattern is DATE_PATTERNS[1]:
                    month, day, year = MONTHS.get(groups[0].lower()), int(groups[1]), int(groups[2])
                elif pattern is DATE_PATTERNS[2]:
                    day, month, year = int(groups[0]), MONTHS.get(groups[1].lower()), int(groups[2])
                else:
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                if not month:
                    continue
                found.append((match.start(), date(year, month, day).isoformat()))
            except ValueError:
                continue
    return [iso for _, iso in sorted(found)]


def first_date(text):
    found = dates_in(text)
    return found[0] if found else ""


def parse_closed(key, value):
    """The permitted label(s) in a classify cell; unrecognised text is kept and flagged."""
    if blank(value):
        return [], ""
    text = str(value).split("|")[0].strip()
    labels = CLOSED[key]
    by_norm = {norm_name(label): label for label in labels}
    found = []
    if key in MULTI:
        for part in re.split(r"\s*[,;/]\s*|\n", text):
            label = by_norm.get(norm_name(part))
            if label and label not in found:
                found.append(label)
    exact = by_norm.get(norm_name(text))
    if exact and exact not in found:
        found.insert(0, exact)
    if not found:
        # A label followed by prose ("Draft (v3)"): accept the longest label the text starts with.
        for label in sorted(labels, key=len, reverse=True):
            if norm_name(text).startswith(norm_name(label)):
                found.append(label)
                break
    return found, ("" if found else text)


def parse_entity(value):
    """(name as printed, company number or '') from a free-text entity cell."""
    text = str(value or "").strip()
    if blank(text) or norm_name(text) == "not found":
        return "", ""
    number = ""
    match = re.search(r"\(?\s*(?:No\.?|Number|no\.|company number|registered number)\s*[:#]?\s*([A-Z]{0,2}\d{6,10})\s*\)?", text, re.I)
    if match:
        number = match.group(1).upper()
        text = (text[:match.start()] + text[match.end():]).strip()
    text = re.sub(r"\s*\((?:the\s+)?['\"]?(?:customer|supplier|buyer|seller|company|purchaser|provider)['\"]?\)\s*", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ,;.")
    return text, number


def entity_lines(value):
    lines = re.split(r"\n|;|\s{2,}(?=[A-Z])", str(value or ""))
    result = []
    for line in lines:
        name, number = parse_entity(line)
        if name and norm_name(name) != "none":
            result.append((name, number))
    return result


def header_key(text):
    head = re.sub(r"\s*\(.*$", "", str(text or ""), flags=re.S)
    head = re.sub(r"^\s*\d+\s*[.)]\s*", "", head)
    head = re.sub(r"[\s-]+", "_", head.strip().casefold())
    return ALIASES.get(head, head)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


# ---------------------------------------------------------------- import

def read_export(path, sheet=None):
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        import openpyxl
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            names = book.sheetnames
            selected = book[sheet] if sheet else book[names[0]]
            table = []
            for row in selected.iter_rows(values_only=True):
                table.append([("" if v is None else (v.isoformat() if hasattr(v, "isoformat") else str(v))) for v in row])
        finally:
            book.close()
    elif path.suffix.lower() == ".csv":
        raw = path.read_text(encoding="utf-8-sig")
        try:
            delimiter = csv.Sniffer().sniff(raw[:65536], delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = ","
        table = list(csv.reader(raw.splitlines(True), delimiter=delimiter))
    else:
        raise ValueError("Review_Table_Light must be CSV or XLSX")
    table = [r for r in table if any(str(v).strip() for v in r)]
    if not table:
        raise ValueError("Review_Table_Light is empty")
    keys = [header_key(h) for h in table[0]]
    if "file_name" not in keys:
        raise ValueError("Review_Table_Light needs a File name (or Name) column")
    missing = [k for k in REQUIRED if k not in keys]
    if missing:
        raise ValueError("Review_Table_Light is missing columns: " + ", ".join(missing))
    rows = []
    for values in table[1:]:
        row = {k: (str(values[i]).strip() if i < len(values) else "") for i, k in enumerate(keys) if k}
        rows.append(row)
    return rows, keys, [str(h or "") for h in table[0]]


def as_at_in_headers(headers):
    """The as-at date the Status question states ("As at 2026-09-09, choose..."), or ''."""
    for header in headers:
        found = re.search(r"\bas\s+at\b\s*:?\s*(.{0,40})", str(header), re.I)
        if found:
            dates = dates_in(found.group(1))
            if dates:
                return dates[0]
    return ""


def read_error_log(path):
    """The review tool's error workbook (xlsx, or a zip that is one): {basename: error code}."""
    path = Path(path)
    import openpyxl
    if zipfile.is_zipfile(path) and path.suffix.lower() != ".xlsx":
        copy = ROOT / "imports" / (path.stem + ".xlsx")
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, copy)
        path = copy
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    errors = {}
    try:
        for sheet in book.worksheets:
            for row in sheet.iter_rows(values_only=True):
                cells = [("" if v is None else str(v).strip()) for v in row]
                codes = [c for c in cells if re.fullmatch(r"[A-Z_]{6,}", c)]
                names = [c for c in cells if re.search(r"\.[A-Za-z0-9]{2,5}$", c) and "/" not in c]
                if codes and names:
                    errors[names[-1].casefold()] = codes[0]
    finally:
        book.close()
    return errors


OUR_ENTITY_COLUMNS = ["name", "status", "note"]


def our_entity_rows():
    """inputs/our-entities.csv rows: name, status (current, former, group, group member), note."""
    return [r for r in read_csv(OUR_ENTITIES) if r.get("name", "").strip()] if OUR_ENTITIES.is_file() else []


def write_our_entity_rows(rows):
    write_csv(OUR_ENTITIES, [{c: r.get(c, "") for c in OUR_ENTITY_COLUMNS} for r in rows], OUR_ENTITY_COLUMNS)


def our_group_names(rows=None):
    """The group names as printed in inputs/our-entities.csv (rows with status `group`)."""
    rows = our_entity_rows() if rows is None else rows
    return [r["name"].strip() for r in rows if r.get("status", "").strip().lower() == "group"]


def ours_matcher(inferred=""):
    """is_ours(name): a listed entity, a name carrying the group name, or the inferred entity.

    The user need not list entities. One row with status `group` (the group name) makes every
    entity whose name contains that word ours; the names turn adds group members it recognises
    with --decide --account _ours; and with no rows at all the entity that dominates our side
    of the export (inferred at import) stands in.
    """
    rows = our_entity_rows()
    listed = [r["name"] for r in rows if r.get("status", "").strip().lower() != "group"]
    keys = {norm_name(n) for n in listed} | {group_key(n) for n in listed}
    groups = [re.compile(r"(?<![a-z0-9])" + re.escape(norm_name(g)) + r"(?![a-z0-9])")
              for g in our_group_names(rows) if norm_name(g)]
    if inferred:
        keys |= {norm_name(inferred), group_key(inferred)}

    def is_ours(name):
        if not name:
            return False
        n = norm_name(strip_number(name))
        return n in keys or group_key(name) in keys or any(g.search(n) for g in groups)
    return is_ours


def infer_ours(packets, side):
    """With no our-entities rows at all: the entity that dominates our side's column."""
    parsed = [p.get("parsed") or {} for p in packets.values() if not p.get("no_row")]
    column = "supplier" if side == "customers" else "customer"
    counts = Counter(p.get(column, "") for p in parsed if p.get(column))
    return counts.most_common(1)[0][0] if counts else ""


def side_check(packets, side, inferred=""):
    """Lines saying which entities dominate each column and whether that fits the side."""
    parsed = [p.get("parsed") or {} for p in packets.values() if not p.get("no_row")]
    suppliers = Counter(p.get("supplier", "") for p in parsed if p.get("supplier"))
    customers = Counter(p.get("customer", "") for p in parsed if p.get("customer"))
    if not suppliers and not customers:
        return []
    is_ours = ours_matcher(inferred)
    top_s = suppliers.most_common(1)[0] if suppliers else ("", 0)
    top_c = customers.most_common(1)[0] if customers else ("", 0)
    lines = [f"most frequent supplier entity: {top_s[0] or 'none'} ({top_s[1]} of {len(parsed)} rows); "
             f"most frequent customer entity: {top_c[0] or 'none'} ({top_c[1]} of {len(parsed)} rows)"]
    rows = our_entity_rows()
    groups = our_group_names(rows)
    if groups:
        lines.append("our group: " + ", ".join(groups) + f"; {len(rows) - len(groups)} entities listed")
    elif rows:
        lines.append(f"our entities: {len(rows)} listed in inputs/our-entities.csv (no group name given)")
    elif inferred:
        lines.append(f"no group name given and no inputs/our-entities.csv: treating {inferred} as our company "
                     "(the entity that dominates our side of the export). Pass --our-group to name the group.")
    expected_ours = "supplier" if side == "customers" else "customer"
    other = "customer" if side == "customers" else "supplier"
    ours_top = top_s if side == "customers" else top_c
    theirs_top = top_c if side == "customers" else top_s
    if is_ours(ours_top[0]):
        lines.append(f"side {side}: consistent; the {expected_ours} column is mostly our own entity")
    elif is_ours(theirs_top[0]):
        lines.append(f"WARNING: side {side} looks wrong: the {other} column is mostly our own entity "
                     f"({theirs_top[0]}). Re-run /prepare with the other --side.")
    else:
        lines.append(f"side {side}: neither column's most frequent entity is ours by the group name or the "
                     "listed entities; check the group name given with --our-group")
    return lines


def set_our_group(name):
    """Record the group name as a `group` row in inputs/our-entities.csv (never in the repo)."""
    name = (name or "").strip()
    if not name:
        raise ValueError("--our-group needs the group name")
    rows = [r for r in our_entity_rows()
            if not (r.get("status", "").strip().lower() == "group" and norm_name(r["name"]) == norm_name(name))]
    rows.append({"name": name, "status": "group", "note": "group name given to /sort; every entity whose name "
                                                            "carries it is ours"})
    write_our_entity_rows(rows)
    say(f"our group: {name!r} recorded in inputs/our-entities.csv")


def import_export(path, sheet=None, error_log=None, as_at=None):
    inventory = read_csv(INVENTORY_CSV)
    if not inventory:
        raise ValueError("Run /prepare first: work/inventory.csv is missing")
    erp = load_erp()
    if not erp.get("confirmed"):
        raise ValueError("Confirm the ERP account column and side with /prepare first")
    path = Path(path).expanduser().resolve()
    rows, keys, headers = read_export(path, sheet)
    control = {Path(erp.get("source_path", "")).name.casefold(), path.name.casefold()}
    by_name = {}
    for item in inventory:
        by_name.setdefault(item["file_name"].casefold(), []).append(item)
    packets, ignored, unknown = {}, [], []
    for row in rows:
        name = row.get("file_name", "")
        if name.casefold() in control or not name:
            ignored.append(name)
            continue
        candidates = by_name.get(name.casefold(), [])
        folder = row.get("source_folder", "")
        if len(candidates) > 1 and folder:
            tail = folder.replace("\\", "/").casefold().rstrip("/")
            narrowed = [c for c in candidates if Path(c["original_path"]).parent.as_posix().casefold().endswith(tail.split("/")[-1])]
            candidates = narrowed or candidates
        if len(candidates) != 1:
            unknown.append(name)
            continue
        item = candidates[0]
        if not item["doc_id"].isdigit():
            ignored.append(name)
            continue
        packet = {"doc_id": item["doc_id"], "raw": row, "flags": []}
        answers = {}
        for key in KEYS:
            answers[key] = row.get(key, "")
        parsed = {}
        for key, labels in CLOSED.items():
            found, leftover = parse_closed(key, answers.get(key, ""))
            parsed[key] = found
            if leftover:
                packet["flags"].append(f"{key}: unrecognised answer {leftover!r}")
            if key in REQUIRED and not found and not leftover:
                packet["flags"].append(f"{key}: blank")
        parsed["document_date"] = first_date(answers.get("document_date", ""))
        parsed["end_date"] = first_date(answers.get("end_date", ""))
        parsed["customer"], parsed["customer_number"] = parse_entity(answers.get("customer_entity", ""))
        parsed["supplier"], parsed["supplier_number"] = parse_entity(answers.get("supplier_entity", ""))
        parsed["additional"] = entity_lines(answers.get("additional_customer_entities", ""))
        parsed["parent_dates"] = dates_in(answers.get("parent_agreement", ""))
        packet.update(answers=answers, parsed=parsed, inventory=item)
        packets[item["doc_id"]] = packet
    source_hash = digest(path)
    folder = ROOT / "imports" / source_hash
    folder.mkdir(parents=True, exist_ok=True)
    snapshot = folder / ("Review_Table_Light" + path.suffix.lower())
    if path != snapshot:
        shutil.copyfile(path, snapshot)
    errors = read_error_log(error_log) if error_log else {}
    missing = [i for i in inventory if i["doc_id"].isdigit() and i["doc_id"] not in packets]
    for item in missing:
        code = errors.get(item["file_name"].casefold(), "")
        item_note = code or ("no row in the export" if item["readable"] == "yes" else item.get("note", "not readable"))
        packets[item["doc_id"]] = {"doc_id": item["doc_id"], "raw": {}, "answers": {}, "parsed": {},
                                   "inventory": item, "flags": [f"no row: {item_note}"], "no_row": item_note}
    export_date = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date().isoformat()
    inferred = "" if our_entity_rows() else infer_ours(packets, erp.get("side", ""))
    stated = as_at_in_headers(headers)
    if as_at:
        source = "--as-at"
        if stated and stated != as_at:
            warn(f"--as-at {as_at} differs from the as-at date in the Status question ({stated}); "
                 "the export's Current answers were given as at that date")
    elif stated:
        as_at, source = stated, "the Status question"
    else:
        as_at, source = export_date, "the export file's date; no as-at date in the Status question, pass --as-at if it is wrong"
    date.fromisoformat(as_at)
    write_json(folder / "rows.json", packets)
    write_json(ACTIVE, {"schema": VERSION, "source_path": str(path), "source_hash": source_hash,
                        "snapshot": str(snapshot), "sheet": sheet, "columns": keys,
                        "export_date": export_date, "as_at": as_at, "as_at_source": source,
                        "inferred_ours": inferred,
                        "error_log": str(Path(error_log).resolve()) if error_log else "",
                        "imported_at": datetime.now(timezone.utc).isoformat(),
                        "ignored_rows": ignored, "unknown_rows": unknown,
                        "rows": sorted(packets)})
    write_json(SOURCE, {"source_path": str(path), "sha256": source_hash, "sheet": sheet})
    with_rows = len([p for p in packets.values() if not p.get("no_row")])
    say(f"Review_Table_Light: {with_rows} rows matched to documents; {len(missing)} documents without a row; "
        f"{len(ignored)} control rows ignored; {len(unknown)} rows for unknown files; as-at {as_at} ({source}).")
    if missing and not error_log:
        say("no error log supplied: whether the review tool refused the documents without a row is unknown")
    for line in side_check(packets, erp.get("side", ""), inferred):
        say(line)
    for name in unknown:
        warn(f"export row for a file not in the inventory: {name}")
    for doc in sorted(packets):
        for flag in packets[doc]["flags"]:
            say(f"REVIEW doc {doc}: {flag}")


def load_packets():
    active = read_json(ACTIVE)
    if not active:
        raise ValueError("No imported Review_Table_Light; run --import first")
    source = Path(active["source_path"])
    if not source.is_file() or digest(source) != active["source_hash"]:
        raise ValueError("Review_Table_Light changed or disappeared; reimport it")
    packets = read_json(ROOT / "imports" / active["source_hash"] / "rows.json")
    inventory = {r["doc_id"]: r for r in read_csv(INVENTORY_CSV)}
    for doc, packet in packets.items():
        item = inventory.get(doc)
        if not item or item["sha256"] != packet["inventory"]["sha256"]:
            raise ValueError(f"doc {doc}: inventory changed since import; rerun /prepare and --import")
    return active, packets


# ---------------------------------------------------------------- matching

def strip_number(name):
    return parse_entity(name)[0]


LEGAL_FORMS = {"limited", "ltd", "plc", "public limited company", "inc", "incorporated", "llc",
               "gmbh", "ag", "sa", "bv", "nv", "srl", "sarl", "pty", "co", "company", "corp",
               "corporation", "limited liability company"}


def core_name(name):
    """The name without its legal form, so 'X Ltd', 'X Limited' and the ERP's 'X' meet."""
    words = group_key(strip_number(name)).split()
    while words and words[-1] in LEGAL_FORMS:
        words.pop()
    return " ".join(words)


def distinctive_tokens(name):
    stop = {"the", "and", "of", "limited", "ltd", "plc", "inc", "llc", "gmbh", "group", "company",
            "co", "services", "svcs", "holdings", "international", "uk", "partnership", "networks",
            "systems", "solutions", "industries", "engineering", "utilities", "power", "housing"}
    return {t for t in re.split(r"[^a-z0-9]+", norm_name(name)) if len(t) >= 4 and t not in stop}


def match_accounts(packets, playbooks=None):
    """Deterministic account decisions per document.

    Returns ({doc: [target dict, ...]}, report) where report says which entity-map rows were
    applied and which were ignored and why, so a decision that did not take effect is visible.
    """
    playbooks = playbooks or {}
    report = {"applied": {}, "ignored": {}}
    erp = load_erp()
    accounts = erp_account_names(erp)
    by_norm = {norm_name(a): a for a in accounts}
    holding_labels = {}

    def holding(prefix, name):
        """One holding folder per company however its name is abbreviated."""
        key = group_key(name)
        label = holding_labels.setdefault(key, name)
        if len(name) > len(label):
            holding_labels[key] = label = name
        return f"{prefix}/{label}"
    by_group, by_core = {}, {}
    for account in accounts:
        by_group.setdefault(group_key(account), []).append(account)
        by_core.setdefault(core_name(account), []).append(account)
    entities, _ = load_entity_map()
    is_ours = ours_matcher((read_json(ACTIVE) or {}).get("inferred_ours", ""))

    def resolve(name):
        """(account or holding target, basis, confidence) for one printed name."""
        if not name:
            return "_no-name-found", "", ""
        if norm_name(name) in by_norm:
            return by_norm[norm_name(name)], "same name", "sure"
        hits = by_group.get(group_key(name), []) or by_core.get(core_name(name), [])
        if len(hits) == 1:
            return hits[0], "same name", "sure"
        row = entity_row_for(entities, name)
        if row is not None:
            target = row.get("account", "").strip()
            basis, confidence = row.get("basis", "").strip(), row.get("confidence", "").strip().lower()
            if not target:
                report["ignored"][name] = "the entity-map row has no account"
            elif target in HOLDING_TARGETS:
                report["applied"][name] = target
                return holding(target, name), basis, confidence
            else:
                hits = [by_norm[norm_name(target)]] if norm_name(target) in by_norm else \
                    (by_group.get(group_key(target), []) or by_core.get(core_name(target), []))
                if len(hits) != 1:
                    report["ignored"][name] = (f"mapped to {target!r}, which is not an ERP account row; "
                                               "spell the account as the ERP record does")
                elif basis not in BASES:
                    report["ignored"][name] = (f"basis {basis!r} is not one of {', '.join(BASES)}; "
                                               "left in _not-sure for the user")
                    return holding("_not-sure", name), basis, confidence
                elif confidence != "not sure" and confidence in CONFIDENCES:
                    report["applied"][name] = hits[0]
                    return hits[0], basis, confidence
                else:
                    report["applied"][name] = "_not-sure"
                    return holding("_not-sure", name), basis, confidence or "not sure"
        tokens = distinctive_tokens(name)
        candidates = [a for a in accounts if tokens & distinctive_tokens(a)]
        if candidates:
            return holding("_not-sure", name), "", ""
        return holding("_not-on-the-list", name), "", ""

    # First pass: names. Learn company numbers from the rows that matched an ERP account.
    numbers = {}
    decisions = {}
    for doc, packet in sorted(packets.items()):
        parsed = packet.get("parsed") or {}
        if packet.get("no_row"):
            decisions[doc] = [{"target": "_unreadable", "basis": "", "confidence": "", "names": [],
                               "note": packet["no_row"]}]
            continue
        listed = playbooks.get(packet["inventory"]["file_name"].casefold())
        if listed is not None:
            target = by_norm.get(norm_name(listed)) if listed else None
            decisions[doc] = [{"target": target or "_no-name-found", "basis": "business practice list" if target else "",
                               "confidence": "sure" if target else "", "names": [],
                               "note": "internal guidance listed in inputs/business-practice.csv"}]
            continue
        customer, number = parsed.get("customer", ""), parsed.get("customer_number", "")
        supplier, s_number = parsed.get("supplier", ""), parsed.get("supplier_number", "")
        note = ""
        if customer and is_ours(customer):
            # Sides reversed: the export puts our company in the customer cell. Either the tool
            # swapped the parties or we really are the buyer; neither is filed by rule.
            counterparty, number = supplier, s_number
            note = ("sides reversed in the export: our company is the customer cell and "
                    f"{counterparty or 'nobody'} the supplier; confirm which way the paper runs")
            if not counterparty or is_ours(counterparty):
                decisions[doc] = [{"target": "_no-name-found", "basis": "", "confidence": "", "names": [customer],
                                   "note": "only our own companies are named"}]
                continue
            target, basis, confidence = resolve(counterparty)
            if target.startswith("_"):
                target = holding("_not-on-the-list", counterparty)
            decisions[doc] = [{"target": target, "basis": basis, "confidence": confidence,
                               "names": [counterparty], "note": note, "reversed": True}]
            continue
        if not customer and supplier and not is_ours(supplier):
            customer, number = supplier, s_number
            note = "customer not identified; the supplier cell names a counterparty, sides unclear"
        target, basis, confidence = resolve(customer)
        row = {"target": target, "basis": basis, "confidence": confidence, "names": [customer] if customer else [],
               "note": note, "number": number}
        if number and not target.startswith("_"):
            numbers.setdefault(number, target)
        decisions[doc] = [row]
        for name, extra_number in parsed.get("additional", []):
            if norm_name(name) == norm_name(customer) or is_ours(name):
                continue
            extra_target, extra_basis, extra_conf = resolve(name)
            decisions[doc].append({"target": extra_target, "basis": extra_basis or "co-contracting party",
                                   "confidence": extra_conf, "names": [name], "number": extra_number,
                                   "note": "additional contracting customer"})
            if extra_number and not extra_target.startswith("_"):
                numbers.setdefault(extra_number, extra_target)
    for targets in decisions.values():
        for row in targets:
            prefix, _, name = row["target"].partition("/")
            if prefix in ("_not-sure", "_not-on-the-list") and name:
                row["target"] = holding(prefix, name)
    # Second pass: a company number seen on a matched document settles an unmatched name.
    for doc, targets in decisions.items():
        for row in targets:
            number = row.get("number", "")
            if number and row["target"].startswith("_") and number in numbers:
                row.update(target=numbers[number], basis="company number in the document",
                           confidence="sure", note=(row["note"] + " " if row["note"] else "")
                           + f"company number {number} matches a document filed under this account")
    return decisions, report


def decide_name(name, account, basis, confidence, note=""):
    """The names-only turn writes one decision through here: validated, never a hand-edited CSV."""
    name = (name or "").strip()
    if not name:
        raise ValueError("--decide needs the name as printed")
    erp = load_erp()
    accounts = erp_account_names(erp)
    by_norm = {norm_name(a): a for a in accounts}
    target = (account or "").strip()
    basis, confidence = (basis or "").strip().lower(), (confidence or "").strip().lower()
    if target == "_ours":
        if norm_name(name) in by_norm:
            raise ValueError(f"{name!r} is an ERP account row; a customer account cannot be one of our companies")
        rows = our_entity_rows()
        for row in rows:
            if norm_name(row["name"]) == norm_name(name) and "decided_by=claude" not in row.get("note", ""):
                raise ValueError(f"{name!r} is already in inputs/our-entities.csv ({row.get('status')}); not changed")
        rows = [r for r in rows if norm_name(r["name"]) != norm_name(name)]
        rows.append({"name": name, "status": "group member",
                     "note": "decided_by=claude; " + (basis or "known group") + ("; " + note.strip() if note else "")})
        write_our_entity_rows(rows)
        say(f"our entities: {name!r} recorded as a group member in inputs/our-entities.csv "
            "(decided by claude; the user can delete the row). Run --unmatched to confirm.")
        return rows[-1]
    if target in HOLDING_TARGETS:
        confidence = confidence or "not sure"
    else:
        by_group, by_core = {}, {}
        for a in accounts:
            by_group.setdefault(group_key(a), []).append(a)
            by_core.setdefault(core_name(a), []).append(a)
        hits = [by_norm[norm_name(target)]] if norm_name(target) in by_norm else \
            (by_group.get(group_key(target), []) or by_core.get(core_name(target), []))
        if len(hits) != 1:
            near = [a for a in accounts if distinctive_tokens(target) & distinctive_tokens(a)][:5]
            raise ValueError(f"{target!r} is not an ERP account row (or matches several); spell it as the ERP does"
                             + (": nearest rows " + "; ".join(near) if near else "")
                             + ". Other targets are _not-sure, _not-on-the-list and _ours.")
        target = hits[0]
        if basis not in BASES:
            raise ValueError(f"--basis must be one of: {', '.join(BASES)}")
        if confidence not in CONFIDENCES:
            raise ValueError(f"--confidence must be one of: {', '.join(CONFIDENCES)}")
        if basis == "known group" and confidence == "sure":
            confidence = "fairly sure"
            say("known group is never better than fairly sure; confidence set to fairly sure")
    if confidence and confidence not in CONFIDENCES:
        raise ValueError(f"--confidence must be one of: {', '.join(CONFIDENCES)}")
    existing = read_csv(ENTITY_MAP_CSV) if ENTITY_MAP_CSV.is_file() else []
    kept = []
    for row in existing:
        if norm_name(row.get("name_as_printed", "")) == norm_name(name):
            if row.get("decided_by", "").strip().lower() == "user":
                raise ValueError(f"{name!r} already has a user decision ({row.get('account')!r}); not overwritten")
            continue
        kept.append({c: row.get(c, "") for c in ENTITY_MAP_COLUMNS})
    new_row = {"name_as_printed": name, "account": target, "basis": basis, "confidence": confidence,
               "decided_by": "claude", "note": (note or "").strip()}
    write_csv(ENTITY_MAP_CSV, kept + [new_row], ENTITY_MAP_COLUMNS)
    say(f"entity map: {name!r} -> {target!r} ({basis or 'no basis'}, {confidence}); decided_by claude. "
        "Run --unmatched to confirm it took effect.")
    return new_row


def map_report_lines(report):
    lines = []
    if report["applied"]:
        lines.append("entity map applied: " + "; ".join(f"{n} -> {t}" for n, t in report["applied"].items()))
    for name, reason in report["ignored"].items():
        lines.append(f"WARNING: entity map row for {name!r} ignored: {reason}")
    return lines


def unmatched_names(decisions, packets):
    names = {}
    for doc, targets in decisions.items():
        for row in targets:
            if row["target"].startswith(("_not-sure/", "_not-on-the-list/")):
                names.setdefault(row["names"][0], []).append(doc)
    return names


# ---------------------------------------------------------------- filing

def family(instrument):
    return "master" if instrument in MASTERS else instrument


class Doc:
    def __init__(self, doc, packet, target):
        self.doc = doc
        self.packet = packet
        self.inventory = packet["inventory"]
        parsed = packet.get("parsed") or {}
        self.no_row = packet.get("no_row", "")
        self.instrument = (parsed.get("instrument") or [""])[0]
        self.coverage = (parsed.get("supply_coverage") or [""])[0]
        self.mechanism = parsed.get("group_mechanism") or []
        self.signed = (parsed.get("signed") or [""])[0]
        self.status = (parsed.get("status") or [""])[0]
        self.relations = parsed.get("relation_to_parent") or []
        self.document_date = parsed.get("document_date", "")
        self.end_date = parsed.get("end_date", "")
        self.parent_dates = parsed.get("parent_dates") or []
        self.parent_text = (packet.get("answers") or {}).get("parent_agreement", "")
        self.reference = (packet.get("answers") or {}).get("reference", "")
        self.title = (packet.get("answers") or {}).get("title", "")
        self.target = target
        self.account = target["target"]
        self.flags = list(packet.get("flags", []))
        self.parent = None
        self.ended_by = None
        self.folder = ""
        self.duplicate_of = ""
        self.copy_of = ""
        self.draft_of = ""
        self.notes = []
        self.playbook = False

    @property
    def is_draft(self):
        return self.signed == "Draft"

    @property
    def relation(self):
        return next((r for r in self.relations if r != "None"), "")


def ended_state(d, as_at):
    """'ended', 'live', 'future' or 'unknown' from End date first, then the Status label."""
    if d.end_date:
        return "ended" if d.end_date < as_at else "live"
    if d.status in ("Expired", "Terminated"):
        return "ended"
    if d.status == "Current":
        return "live"
    if d.status == "Not yet effective":
        return "future"
    return "unknown"


def title_similarity(a, b):
    ta = {t for t in re.split(r"[^a-z0-9]+", norm_name(a)) if len(t) > 2}
    tb = {t for t in re.split(r"[^a-z0-9]+", norm_name(b)) if len(t) > 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def find_parent(d, siblings):
    """The row in the same account that the Parent agreement words point at, or None."""
    if not d.relation or not d.parent_text:
        return None, ""
    others = [s for s in siblings if s is not d and not s.no_row]
    # The verbatim citation often repeats the child's own date; the principal parent is the
    # first quoted date that names another document in this account.
    for quoted in [q for q in d.parent_dates if q != d.document_date]:
        by_date = [s for s in others if s.document_date == quoted]
        if len(by_date) == 1:
            return by_date[0], "parent date"
        if len(by_date) > 1:
            ranked = sorted(by_date, key=lambda s: (s.is_draft, bool(s.duplicate_of), bool(s.copy_of),
                                                    -title_similarity(s.title, d.parent_text), int(s.doc)))
            return ranked[0], "parent date (several candidates; best copy)"
    if d.reference or any(s.reference for s in others):
        by_ref = [s for s in others if s.reference and not blank(s.reference)
                  and norm_name(strip_number(s.reference)) in norm_name(d.parent_text)]
        if len(by_ref) == 1:
            return by_ref[0], "reference quoted"
    scored = [(title_similarity(s.title, d.parent_text), s) for s in others if s.title]
    scored = [x for x in scored if x[0] >= 0.6]
    if len(scored) == 1:
        return scored[0][1], "title"
    return None, ""


def ref_key(reference):
    """A reference normalised for comparison; empty when the cell is blank."""
    if not reference or blank(reference):
        return ""
    return re.sub(r"[^a-z0-9]+", "", reference.casefold())


def same_instrument(a, b):
    """Two rows describe one instrument: the same reference, or titles that agree."""
    ra, rb = ref_key(a.reference), ref_key(b.reference)
    if ra and rb:
        return ra == rb
    if not a.title or not b.title:
        return True
    return norm_name(a.title) == norm_name(b.title) or title_similarity(a.title, b.title) >= 0.6


def pages_of(d):
    value = str(d.inventory.get("pages", "") or "")
    return int(value) if value.isdigit() else 0


def group_versions(docs):
    """Rows that may be versions or copies of one instrument: same account and family, sharing
    a reference or a title (or, with neither, the parent date they quote). Grouping is loose;
    same_instrument() decides which rows are actually related."""
    groups = []
    for d in docs:
        if d.no_row or d.instrument in TRANSACTIONS:
            continue
        keys = set()
        if ref_key(d.reference):
            keys.add("ref:" + ref_key(d.reference))
        if d.title:
            keys.add("title:" + norm_name(d.title))
        if not keys and d.parent_dates:
            keys.add("parent:" + d.parent_dates[0])
        if not keys:
            continue
        merged = [d.account, family(d.instrument), set(keys), [d]]
        for g in [g for g in groups if g[0] == d.account and g[1] == merged[1] and g[2] & keys]:
            merged[2].update(g[2])
            merged[3].extend(g[3])
            groups.remove(g)
        groups.append(merged)
    return [sorted(g[3], key=lambda x: int(x.doc)) for g in groups if len(g[3]) > 1]


SIGN_ORDER = {"Signed by all parties": 4, "Signed by one party": 3, "Signature not established": 2,
              "Unsigned": 1, "Draft": 0}


def sign_rank(d):
    native = 1 if str(d.inventory.get("text_pages", "0")).isdigit() and int(d.inventory.get("text_pages") or 0) > 0 else 0
    path = norm_name(str(Path(d.inventory["original_path"]).parent))
    near = 1 if any(t in path for t in distinctive_tokens(d.account)) else 0
    return (SIGN_ORDER.get(d.signed, 0), native, near, -int(d.doc))


def file_documents(as_at, decisions, packets, playbooks):
    docs = []
    for doc in sorted(packets):
        for target in decisions[doc]:
            docs.append(Doc(doc, packets[doc], target))
    by_account = {}
    for d in docs:
        by_account.setdefault(d.account, []).append(d)

    # 1. Byte-identical copies, per account.
    for siblings in by_account.values():
        by_hash = {}
        for d in siblings:
            if not d.no_row:
                by_hash.setdefault(d.inventory["sha256"], []).append(d)
        for same in by_hash.values():
            if len(same) > 1:
                best = max(same, key=sign_rank)
                for d in same:
                    if d is not best:
                        d.duplicate_of = best.doc

    # 2. Playbooks from the local list.
    for d in docs:
        if d.inventory["file_name"].casefold() in playbooks:
            d.playbook = True

    # 3. Versions and copies of one instrument.
    for siblings in by_account.values():
        for group in group_versions([d for d in siblings if not d.duplicate_of and not d.playbook]):
            executed = [d for d in group if not d.is_draft]
            if not executed:
                for d in group:
                    d.flags.append("every version of this instrument is marked Draft; no executed copy found")
                continue
            # A one- or two-page signed copy beside a much longer executed body of the same
            # instrument is its signature page or a partial copy; the body carries the execution
            # that page shows.
            body = max(executed, key=lambda d: (pages_of(d), sign_rank(d)))
            fragments = [d for d in executed if d is not body and 0 < pages_of(d) <= 2
                         and pages_of(body) >= max(3, 3 * pages_of(d)) and same_instrument(d, body)]
            for d in fragments:
                d.copy_of = body.doc
                d.notes.append(f"signature page or partial copy of doc {body.doc} ({pages_of(d)} of {pages_of(body)} pages)")
                if SIGN_ORDER.get(d.signed, 0) > SIGN_ORDER.get(body.signed, 0):
                    body.notes.append(f"execution shown on doc {d.doc}: {d.signed}")
                    body.signed = d.signed
            best = max([d for d in executed if d not in fragments], key=sign_rank)
            for d in group:
                if d is best or d in fragments or not same_instrument(d, best):
                    continue
                if d.is_draft:
                    if not d.document_date or not best.document_date or d.document_date <= best.document_date:
                        d.draft_of = best.doc
                    else:
                        d.flags.append(f"draft dated after the executed doc {best.doc}; may be a later instrument")
                elif d.document_date and d.document_date == best.document_date and d.signed != "Signed by all parties":
                    d.copy_of = best.doc

    # 4. Parents.
    for siblings in by_account.values():
        for d in siblings:
            if d.no_row or not d.relation:
                continue
            parent, how = find_parent(d, siblings)
            if parent is None and blank(d.parent_text) and d.relation in INFERABLE:
                masters = [s for s in siblings if s is not d and not s.no_row and s.instrument in MASTERS
                           and not s.is_draft and not s.duplicate_of and not s.copy_of and not s.draft_of]
                if len(masters) == 1:
                    parent, how = masters[0], "the account's only master; the export names no parent"
                    d.flags.append(f"parent inferred: doc {parent.doc} is the account's only master")
            if parent is not None:
                d.parent = parent
                d.notes.append(f"{d.relation.lower()} doc {parent.doc} ({how})")
            elif blank(d.parent_text):
                d.notes.append(f"{d.relation.lower()} an agreement the export does not name")
            else:
                d.flags.append(f"{d.relation}: parent not found in this account: {d.parent_text[:80]!r}")

    # 5. Terminations and supersessions take effect on the parent by date.
    for d in docs:
        if d.parent is None or d.relation not in ENDING or d.is_draft or d.draft_of:
            continue
        effective = d.end_date or d.document_date
        if effective and effective <= as_at:
            d.parent.ended_by = d
            d.parent.notes.append(f"{'terminated' if d.relation == 'Terminates' else 'superseded'} by doc {d.doc} with effect from {effective}")
        elif effective:
            d.parent.flags.append(f"{d.relation.lower()} notice served by doc {d.doc}, effective {effective}, after the as-at date")
        else:
            d.parent.flags.append(f"doc {d.doc} says it {d.relation.lower()} this document but gives no date")

    # 6. Folders for standalone rows, then children, then the rule 6 fallback.

    def decide(d):
        if d.no_row:
            return "_unreadable"
        if d.playbook:
            return F6
        if d.target.get("reversed"):
            d.flags.append("sides reversed in the export; not filed by rule")
            return UNSURE
        if d.duplicate_of:
            d.notes.append(f"byte-identical duplicate of doc {d.duplicate_of}")
            return F5
        if d.instrument in TRANSACTIONS:
            return F5
        if d.draft_of:
            d.notes.append(f"draft; executed version is doc {d.draft_of}")
            return F5
        if d.copy_of:
            if not any(f"doc {d.copy_of}" in n for n in d.notes):
                d.notes.append(f"copy of doc {d.copy_of}")
            return F5
        state = "ended" if d.ended_by else ended_state(d, as_at)
        if d.instrument in ("Other overlay", "Other") and d.relation in AMENDING and d.parent is not None \
                and d.coverage in FULL | PARTIAL:
            d.notes.append(f"filed as an amendment: it {d.relation.lower()} doc {d.parent.doc} and covers supply")
            return "child"
        if d.instrument in NON_GOVERNING or (d.instrument == "Other overlay" and d.relation in SIDE_EFFECTS):
            if d.coverage in FULL | PARTIAL and d.relation not in SIDE_EFFECTS:
                d.flags.append(f"{d.instrument} answered {d.coverage}: instrument and coverage disagree")
                return UNSURE
            if state == "unknown" and d.parent is not None:
                parent_state = "ended" if d.parent.ended_by else ended_state(d.parent, as_at)
                state = "ended" if parent_state == "ended" else "live"
                d.notes.append(f"life taken from parent doc {d.parent.doc}")
            if state == "ended":
                return F4
            if state in ("live", "future"):
                return F3
            return UNSURE
        if d.instrument in GOVERNING:
            if state == "ended":
                return F4
            if d.signed == "Unsigned":
                d.flags.append("signature blocks empty and no executed version found")
                return UNSURE
            if d.is_draft:
                d.flags.append("draft with no executed version found")
                return UNSURE
            if state in ("future", "unknown"):
                d.flags.append(f"status {d.status or 'blank'} with no end date")
                return UNSURE
            if d.instrument in CHILDREN:
                return "child"
            if d.coverage in FULL:
                return F1
            if d.coverage in PARTIAL:
                return F2
            if d.coverage == "Varies commercials only":
                d.flags.append(f"{d.instrument} answered Varies commercials only: instrument and coverage disagree")
                return UNSURE
            d.flags.append(f"coverage {d.coverage or 'blank'} on a governing instrument")
            return UNSURE
        if d.instrument == "Mixed":
            d.flags.append("several instruments in one file; split before judging")
        elif d.instrument:
            d.flags.append(f"instrument {d.instrument}: not filed by rule")
        else:
            d.flags.append("instrument blank")
        return UNSURE

    for d in docs:
        d.folder = decide(d)
    for d in docs:
        if d.instrument == "Global master agreement" and d.mechanism == ["None"]:
            d.flags.append("Global master agreement with Group mechanism None")
    # Children inherit; two passes so an amendment of an amendment resolves.
    for _ in range(2):
        for d in docs:
            if d.folder != "child":
                continue
            if d.parent is None:
                if d.instrument == "Local participation agreement" and d.coverage in FULL | PARTIAL:
                    d.folder = F1 if d.coverage in FULL else F2
                    d.flags.append("participation with no master found in this account")
                else:
                    d.flags.append("child instrument with no parent found; placed in unsure")
                    d.folder = UNSURE
                continue
            p = d.parent
            if p.folder in (F1, F2):
                d.folder = F2 if d.coverage in PARTIAL else p.folder
            elif p.folder == F4:
                d.folder = F4
            elif p.folder in (F5, UNSURE, "child", ""):
                d.folder = UNSURE
                d.flags.append(f"parent doc {p.doc} is in {p.folder or 'a holding folder'}")
            else:
                d.folder = UNSURE
    # Rule 6 fallback: the only current master in an account governs, with a scope note.
    for account, siblings in by_account.items():
        if account.startswith("_"):
            continue
        if any(d.folder == F1 for d in siblings):
            continue
        masters = [d for d in siblings if d.instrument in MASTERS and d.folder in (F2, UNSURE)
                   and not d.ended_by and ended_state(d, as_at) == "live" and not d.is_draft
                   and d.signed != "Unsigned" and d.coverage in PARTIAL | {"Unclear"}]
        if len(masters) == 1:
            m = masters[0]
            m.folder = F1
            m.notes.append(f"only live master in the account; scope on paper: {m.coverage}; confirm this is all the trade")
            for d in siblings:
                if d.parent is m and d.folder == F2 and d.coverage not in PARTIAL:
                    d.folder = F1
    for account, siblings in by_account.items():
        if account.startswith("_"):
            continue
        governing = [d for d in siblings if d.folder == F1]
        if len(governing) > 1 and len({family(d.instrument) for d in governing if d.instrument in MASTERS}) and \
                len([d for d in governing if d.instrument in MASTERS]) > 1:
            for d in governing:
                if d.instrument in MASTERS:
                    d.flags.append("two live masters claim the whole trade; unresolved")
        if not any(d.folder in (F1, F2) for d in siblings) and \
                any(d.instrument.endswith("carrying standard terms") for d in siblings):
            for d in siblings:
                if d.instrument.endswith("carrying standard terms"):
                    d.flags.append("account has no governing paper; trades on order terms")
    return docs


# ---------------------------------------------------------------- reports

REPORT_COLUMNS = ["doc_id", "account", "folder", "instrument", "supply_coverage", "group_mechanism",
                  "signed", "status", "document_date", "end_date", "relation", "parent_doc",
                  "basis", "confidence", "flags", "notes", "customer_entity", "supplier_entity",
                  "additional_customer_entities", "title", "reference", "original_path", "sha256",
                  "filed_as", "file_path", "local_readable"]


def account_folder(side, account):
    if account.startswith("_"):
        parts = [safe_folder_name(p) for p in account.split("/") if p]
        return OUTPUT / side / Path(*parts)
    return OUTPUT / side / safe_folder_name(account)


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_reports(active, docs, report=None):
    report = report or {"applied": {}, "ignored": {}}
    erp = load_erp()
    side = erp["side"]
    accounts = erp_account_names(erp)
    if OUTPUT.exists():
        archive = WORK / "history" / ("sort-light-" + datetime.now().strftime("%Y%m%dT%H%M%S%f"))
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(OUTPUT), str(archive))
    rows = []
    for d in docs:
        answers = d.packet.get("answers") or {}
        folder = account_folder(side, d.account)
        provisional = d.account.startswith("_") and d.folder not in ("", "_unreadable")
        if d.folder == "_unreadable":
            folder = OUTPUT / side / "_unreadable"
        elif d.folder and not provisional:
            folder = folder / d.folder
        name = d.target["names"][0] if d.target.get("names") else ""
        if d.no_row:
            filename = filed_name(d.doc, d.inventory["ext"], unresolved=True, pages=d.inventory.get("pages"))
        elif d.duplicate_of:
            filename = filed_name(d.doc, d.inventory["ext"], duplicate_of=d.duplicate_of)
        else:
            filename = filed_name(d.doc, d.inventory["ext"], kind=d.instrument or "document",
                                  counterparty=(d.account if not d.account.startswith("_") else name),
                                  date=d.document_date, status=("draft" if d.is_draft else ""))
        dest = folder / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        source = WORK_FILES / f'{d.doc}.{d.inventory["ext"]}' if d.inventory["readable"] == "yes" else Path(d.inventory["original_path"])
        if source.is_file():
            shutil.copyfile(source, dest)
        rows.append({
            "doc_id": d.doc, "account": d.account, "folder": (d.folder + " (provisional)") if provisional else (d.folder or ""),
            "instrument": d.instrument,
            "supply_coverage": d.coverage, "group_mechanism": "; ".join(d.mechanism), "signed": d.signed,
            "status": d.status, "document_date": d.document_date, "end_date": d.end_date,
            "relation": d.relation, "parent_doc": d.parent.doc if d.parent else "",
            "basis": d.target.get("basis", ""), "confidence": d.target.get("confidence", ""),
            "flags": " | ".join(d.flags), "notes": " | ".join(d.notes + ([d.target["note"]] if d.target.get("note") else [])),
            "customer_entity": answers.get("customer_entity", ""), "supplier_entity": answers.get("supplier_entity", ""),
            "additional_customer_entities": answers.get("additional_customer_entities", ""),
            "title": d.title, "reference": d.reference, "original_path": d.inventory["original_path"],
            "sha256": d.inventory["sha256"], "filed_as": filename,
            "file_path": str(dest.relative_to(KIT)), "local_readable": d.inventory["readable"]})
    rows.sort(key=lambda r: (r["account"], r["folder"], r["doc_id"]))
    write_csv(OUTPUT / side / "CORPUS.csv", rows, REPORT_COLUMNS)
    by_account = {}
    for r in rows:
        by_account.setdefault(r["account"], []).append(r)
    write_csv(OUTPUT / side / "ACCOUNTS.csv",
              [{"account": a, "n_documents": len(by_account.get(a, [])),
                "governs_trade": len([r for r in by_account.get(a, []) if r["folder"] == F1]),
                "unsure": len([r for r in by_account.get(a, []) if r["folder"] == UNSURE]),
                "flags": len([r for r in by_account.get(a, []) if r["flags"]])} for a in accounts],
              ["account", "n_documents", "governs_trade", "unsure", "flags"])
    no_row = [d for d in docs if d.no_row]
    index = ["# Light filing", "", f"Review_Table_Light filing by script, as at {active['as_at']} "
             f"(from {active.get('as_at_source', 'the import')}). "
             "Status folders follow stage1/sorting-rules.md section B on the export's answers; "
             "governing status is not verified against the contracts.", "",
             "Two kinds of folder. Account holding folders (`_not-sure/<name>`, `_not-on-the-list/<name>`, "
             "`_no-name-found`, `_unreadable`) hold documents whose ERP account is not settled (section A); "
             "no status is assigned there, and the status columns below show zero for them. Status folders "
             "(`1-governs-trade` to `6-business-practice` and `unsure`) are section B applied within an "
             "account: `unsure` is a status, `_not-sure` is an account question.", "",
             "Our companies: " + (", ".join(our_group_names()) + " (group name)" if our_group_names() else
                                  (f"{active.get('inferred_ours')} (inferred: the entity that dominates our side of the "
                                   "export; no group name given)" if active.get("inferred_ours") else
                                   "the entities listed in inputs/our-entities.csv"))
             + f"; {len([r for r in our_entity_rows() if r.get('status', '').lower() != 'group'])} entities listed. "
             "A row whose customer cell is one of ours is filed as sides reversed, in unsure.", "",
             f"Documents without a row in the export: {len(no_row)}"
             + (". The review tool's error log was supplied; its codes are on the rows." if active.get("error_log")
                else ". No error log was supplied, so whether the review tool refused them is unknown."), "",
             f"[Corpus CSV]({side}/CORPUS.csv)", "", "| account | documents | 1 | 2 | 3 | 4 | 5 | 6 | unsure | flags |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    targets = list(accounts) + sorted(a for a in by_account if a not in accounts)
    for account in targets:
        group = by_account.get(account, [])
        counts = [len([r for r in group if r["folder"] == f]) for f in STATUS_FOLDERS]
        flagged = len([r for r in group if r["flags"]])
        folder = account_folder(side, account)
        link = (folder / "README.md").relative_to(OUTPUT).as_posix().replace(" ", "%20")
        index.append(f"| [{cell(account)}]({link}) | {len(group)} | " + " | ".join(str(c) for c in counts) + f" | {flagged} |")
        lines = [f"# {account}", "", f"Filed by script from Review_Table_Light as at {active['as_at']}. "
                 "Folders are the export's answers applied to section B; nothing here is verified against the paper.", "",
                 "| doc | folder | instrument | coverage | signed | status | dated | ends | parent | flags |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in group:
            lines.append("| " + " | ".join(cell(r[c]) for c in ("doc_id", "folder", "instrument", "supply_coverage",
                                                                "signed", "status", "document_date", "end_date",
                                                                "parent_doc", "flags")) + " |")
        if not group:
            lines += ["", "No documents filed for this account."]
        write_csv(folder / "documents.csv", group, REPORT_COLUMNS)
        write_text(folder / "README.md", "\n".join(lines) + "\n")
        for status in {r["folder"] for r in group if r["folder"] and r["folder"] != "_unreadable" and "provisional" not in r["folder"]}:
            write_csv(folder / status / "documents.csv", [r for r in group if r["folder"] == status], REPORT_COLUMNS)
    unresolved = [r for r in rows if r["account"].startswith("_")]
    if unresolved:
        index += ["", "## Needs a decision", "",
                  "Account holding folders, grouped by the name found. Decide each name once: the names-only "
                  "turn of /sort writes decisions through `python scripts/sort_light.py --decide`, or edit "
                  "`inputs/entity-map.csv` with `decided_by=user`, then run `--file` again.", ""]
        for r in unresolved:
            index.append(f"- doc {r['doc_id']}: {cell(r['account'])} ({cell(r['notes'] or r['flags'])})")
    map_lines = map_report_lines(report)
    if map_lines:
        index += ["", "## Entity map", ""] + [f"- {line}" for line in map_lines]
    write_text(OUTPUT / "INDEX.md", "\n".join(index) + "\n")
    inventory = {r["doc_id"]: r for r in read_csv(INVENTORY_CSV)}
    log = [{"doc_id": r["doc_id"], "original_path": r["original_path"],
            "companies_found": r["customer_entity"], "account": r["account"], "basis": r["basis"],
            "confidence": r["confidence"], "note": r["notes"]} for r in rows]
    write_csv(SORT_LOG, log, SORT_LOG_COLUMNS)
    write_json(ROOT / "filing.json", {"as_at": active["as_at"], "source_hash": active["source_hash"],
                                      "written_at": datetime.now(timezone.utc).isoformat(),
                                      "rows": len(rows), "unresolved": len(unresolved)})
    counts = {f: len([r for r in rows if r["folder"] == f]) for f in STATUS_FOLDERS}
    say(f"Filed {len(inventory) - 1 if 'erp' in inventory else len(inventory)} documents as {len(rows)} account rows under out/sort; "
        + ", ".join(f"{f}: {n}" for f, n in counts.items()) + f"; unresolved names: {len(unresolved)}.")
    say(f"as-at {active['as_at']} ({active.get('as_at_source', 'the import')}); documents without a row: {len(no_row)}"
        + ("" if active.get("error_log") else " (no error log supplied: refusals unknown)"))
    for line in map_lines:
        say(line)


def load_playbooks():
    """inputs/business-practice.csv: file_name and an optional account; {basename: account}."""
    if not PLAYBOOKS.is_file():
        return {}
    return {r.get("file_name", "").casefold(): r.get("account", "").strip()
            for r in read_csv(PLAYBOOKS) if r.get("file_name", "").strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=False)
    action.add_argument("--import", dest="import_path", nargs="?", const="auto", help="light export CSV/XLSX")
    action.add_argument("--unmatched", action="store_true", help="names for the one model decision turn")
    action.add_argument("--file", action="store_true", help="write account and status folders under out/sort")
    action.add_argument("--status", action="store_true")
    action.add_argument("--decide", metavar="NAME", help="write one names-turn decision to inputs/entity-map.csv "
                                                          "(with --account, --basis, --confidence, --note)")
    parser.add_argument("--account", help="with --decide: an ERP account row, _not-sure or _not-on-the-list")
    parser.add_argument("--basis", help="with --decide: same name | in the document | known group")
    parser.add_argument("--confidence", help="with --decide: sure | fairly sure | not sure")
    parser.add_argument("--note", default="", help="with --decide: why")
    parser.add_argument("--our-group", metavar="NAME", help="our group name: every entity whose name carries it is ours "
                                                             "(recorded in inputs/our-entities.csv, which git ignores)")
    parser.add_argument("--sheet")
    parser.add_argument("--error-log", help="the review tool's error workbook for files it refused")
    parser.add_argument("--as-at", help="YYYY-MM-DD used for current/ended; default: export file date")
    args = parser.parse_args()
    if not (args.import_path or args.unmatched or args.file or args.status or args.decide or args.our_group):
        parser.error("one of --import, --unmatched, --file, --status, --decide or --our-group is required")
    try:
        if args.our_group:
            set_our_group(args.our_group)
            if not (args.import_path or args.unmatched or args.file or args.status or args.decide):
                return 0
        if args.import_path:
            path = args.import_path
            if path == "auto":
                configured = read_json(SOURCE) or {}
                path = configured.get("source_path")
                if not path:
                    raise ValueError("No Review_Table_Light registered by /prepare; pass --import PATH")
            import_export(path, args.sheet, args.error_log, args.as_at)
            return 0
        if args.decide:
            if not args.account:
                raise ValueError("--decide needs --account")
            decide_name(args.decide, args.account, args.basis, args.confidence, args.note)
            return 0
        active, packets = load_packets()
        decisions, report = match_accounts(packets, load_playbooks())
        if args.unmatched:
            erp = load_erp()
            entities, _ = load_entity_map()
            names = unmatched_names(decisions, packets)
            suppliers = {}
            for doc, packet in packets.items():
                supplier = (packet.get("parsed") or {}).get("supplier", "")
                if supplier:
                    suppliers.setdefault(norm_name(supplier), []).append(doc)
            unmatched = []
            for name, docs in names.items():
                row = entity_row_for(entities, name)
                unmatched.append({"name": name, "docs": docs,
                                  "entity_map_row": ({c: row.get(c, "") for c in ENTITY_MAP_COLUMNS} if row else None),
                                  "why_unresolved": report["ignored"].get(name) or (
                                      "row says not sure" if row else "no entity-map row"),
                                  "also_the_supplier_entity_on": suppliers.get(norm_name(name), [])})
            say(json.dumps({"erp_accounts": erp_account_names(erp),
                            "unmatched": unmatched,
                            "entity_map_ignored": [{"name": n, "reason": r} for n, r in report["ignored"].items()],
                            "permitted": {"account": "an ERP account row spelled as listed, _not-sure, "
                                                     "_not-on-the-list, or _ours for one of our own group companies",
                                          "basis": list(BASES), "confidence": list(CONFIDENCES)},
                            "hints": {"our_entities_file": "present" if OUR_ENTITIES.is_file() else "missing",
                                      "our_group": our_group_names(),
                                      "our_entities": [r["name"] for r in our_entity_rows()
                                                       if r.get("status", "").lower() != "group"][:40],
                                      "inferred_ours": active.get("inferred_ours", ""),
                                      "side": erp.get("side", ""),
                                      "note": "a name that carries our group name, that you know is one of our "
                                              "group companies, or that is also the supplier entity on other rows "
                                              "is ours: --decide NAME --account _ours. A separate legal entity of "
                                              "a customer's group is _not-sure."}},
                           ensure_ascii=False, indent=1))
        elif args.file:
            docs = file_documents(active["as_at"], decisions, packets, load_playbooks())
            write_reports(active, docs, report)
        else:
            names = unmatched_names(decisions, packets)
            say(f"Review_Table_Light: {len(packets)} documents; as-at {active['as_at']} "
                f"({active.get('as_at_source', 'the import')}); {len(names)} customer names without an ERP match.")
            for line in map_report_lines(report):
                say(line)
    except (ValueError, OSError, ImportError, csv.Error, zipfile.BadZipFile) as err:
        fail(str(err))
    return 0


if __name__ == "__main__":
    sys.exit(main())
