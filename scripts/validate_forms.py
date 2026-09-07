"""Validate stage 2 forms and their quoted evidence, using the standard library only.

Usage: python scripts/validate_forms.py --all | --doc 017 | path/to/017.json
An error rejects the form. Warnings identify evidence that still needs visual review.
Nothing is written. The JSON schema supplies field names, fixed choices and structure;
the checks below supply constraints that depend on other answers or the source text.
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = KIT / "stage2" / "document-form.schema.json"
FORMS = KIT / "work" / "forms"
TEXT = KIT / "work" / "text"
SCAN_MARKER = "[scan: look at the page]"
PAGE_MARKER = re.compile(r"^=== page (\d+) ===\s*$", re.MULTILINE)
PARAGRAPH_MARKER = re.compile(r"\[¶\s*(\d+)\]")
PAGE_REF = re.compile(r"\b(?:pages?|pp?\.?)\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.I)
PARAGRAPH_REF = re.compile(r"(?:¶|\bparagraphs?\b|\bparas?\.)\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.I)
CLAUSE_REF = re.compile(r"(?:\b(?:cl(?:ause)?\.?|section|sec\.)|§)\s*(\d+(?:\.\d+)*[A-Za-z]?)", re.I)


def _schema_errors(value, schema, root, path="form"):
    """Evaluate the JSON Schema keywords used by the shipped schema, not a general engine."""
    errors = []
    if "$ref" in schema:
        target = root
        for segment in schema["$ref"].removeprefix("#/").split("/"):
            target = target[segment.replace("~1", "/").replace("~0", "~")]
        return _schema_errors(value, target, root, path)
    if "anyOf" in schema:
        alternatives = [_schema_errors(value, branch, root, path) for branch in schema["anyOf"]]
        if all(alternatives):
            # Prefer the structural branch's useful field errors to an opaque union failure.
            structural = [issues for branch, issues in zip(schema["anyOf"], alternatives)
                          if "$ref" in branch or branch.get("type") == "object" and isinstance(value, dict)
                          or branch.get("type") == "array" and isinstance(value, list)
                          or branch.get("type") == "string" and isinstance(value, str)]
            errors.extend(min(structural, key=len) if structural else [f"{path}: does not match an allowed value or shape"])
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: must be one of {', '.join(map(str, schema['enum']))}")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']}")
    types = {"object": dict, "array": list, "string": str, "null": type(None)}
    expected = schema.get("type")
    if expected and not isinstance(value, types[expected]):
        return errors + [f"{path}: must be {expected}"]
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}.{name}: required; use not_found for an unanswered question")
        if schema.get("additionalProperties") is False:
            for name in value.keys() - properties.keys():
                errors.append(f"{path}.{name}: field is not in the fixed form")
        for name, item in value.items():
            if name in properties:
                errors.extend(_schema_errors(item, properties[name], root, f"{path}.{name}"))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: empty list is not an answer; use not_found or none as the form allows")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            errors.append(f"{path}: entries must be unique")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(_schema_errors(item, schema["items"], root, f"{path}[{index}]"))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: blank is not an answer; use not_found")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: invalid format or blank answer")
        if schema.get("format") == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                errors.append(f"{path}: must be a real calendar date (YYYY-MM-DD)")
    for branch in schema.get("allOf", []):
        errors.extend(_schema_errors(value, branch, root, path))
    if "if" in schema:
        branch = "else" if _schema_errors(value, schema["if"], root, path) else "then"
        errors.extend(_schema_errors(value, schema.get(branch, {}), root, path))
    return errors


def _nonblank(value):
    return isinstance(value, str) and bool(value.strip()) and value != "not_found"


def _semantic_errors(form):
    errors = []
    # Schema errors have already been returned before any cross-field inspection.
    def detail(block, answer, key, values, path):
        if block[answer] in values and not _nonblank(block[key]):
            errors.append(f"{path}.{key}: detail is required for {block[answer]}")

    def dates(block, path):
        detail(block, "D2_end_type", "D2_detail", {"fixed_date", "rolling_until_notice", "until_project_complete"}, path)
        detail(block, "D3_ended_evidence", "D3_detail", {"termination_letter", "replaced_by"}, path)
        if block["D2_end_type"] == "fixed_date":
            try:
                date.fromisoformat(block["D2_detail"])
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", block["D2_detail"]):
                    raise ValueError
            except ValueError:
                errors.append(f"{path}.D2_detail: fixed_date requires a real date in YYYY-MM-DD format")
        if (block["D1_start_date"] == "not_found") != (block["D1a_basis"] == "not_found"):
            errors.append(f"{path}.D1a_basis: a known start date needs its basis; an unknown start needs not_found")

    def scope(block, path):
        detail(block, "E2_territory", "E2_detail", {"regional", "single_country"}, path)

    dates(form["D"], "D")
    scope(form["E"], "E")
    detail(form["B"], "B5_complete", "B5_missing", {"no"}, "B")
    detail(form["G"], "G1_governs_orders", "G1_detail", {"yes"}, "G")
    if form["G"]["G2_commitment_or_status"] == "volume_or_target" and not re.search(
            r"\b(volume|target)\b", form["G"]["G2_detail"], re.I):
        errors.append("G.G2_detail: say whether volume_or_target is volume or target")

    parts = form["F"]
    layered = form["B"]["B9_layered"]
    if layered == "yes" and not parts:
        errors.append("F: B9_layered is yes, so at least one part is required")
    if layered != "yes" and parts:
        errors.append("F: parts are allowed only when B9_layered is yes")
    names = [part["F1_part_name"] for part in parts]
    if len(set(names)) != len(names):
        errors.append("F: part names must be unique so precedence can identify its targets")
    for index, part in enumerate(parts):
        path = f"F[{index}]"
        if isinstance(part["F4_D"], dict):
            dates(part["F4_D"], path + ".F4_D")
        if isinstance(part["F5_E"], dict):
            scope(part["F5_E"], path + ".F5_E")
        page_range = part["F2_pages_from_to"]
        if page_range != "not_found":
            first, *last = map(int, re.split("[-–]", page_range))
            end = last[0] if last else first
            if first > end:
                errors.append(f"{path}.F2_pages_from_to: page range is reversed")
            pages = form["A"]["pages"]
            if pages.isdigit() and end > int(pages):
                errors.append(f"{path}.F2_pages_from_to: range exceeds the document's pages")
        precedence = part["F6_internal_precedence"]
        if isinstance(precedence, dict):
            for target in precedence["wins_over"]:
                if target not in names:
                    errors.append(f"{path}.F6_internal_precedence: target is not a part in F: {target}")
                if target == part["F1_part_name"]:
                    errors.append(f"{path}.F6_internal_precedence: a part cannot prevail over itself")
            if _normalise(precedence["words"]) != _normalise(part["F6_evidence"]["words"]):
                errors.append(f"{path}.F6_evidence: quote must match F6_internal_precedence.words")
    for index, topic in enumerate(form["I"]):
        if parts and topic["part"] not in names + ["not_found"]:
            errors.append(f"I[{index}].part: must name a part in F or be not_found")
        if topic["reading"] == "silent" and (topic["words"] != "not_found" or topic["page_or_clause"] != "not_found"):
            errors.append(f"I[{index}]: a silent topic uses not_found for words and page_or_clause")
    if len(form["J"]["notes"].split()) > 200:
        errors.append("J.notes: exceeds 200 words")
    doc_id = form["A"]["doc_id"]
    layered_label = {"yes": "y", "no": "n", "not_found": "not_found"}[layered]
    expected = (f"doc {doc_id} | {form['B']['B2_document_kind']} | {form['D']['D4_status_as_read']} | "
                f"layered: {layered_label} | flags: {len(form['K'])} | work/forms/{doc_id}.json")
    if form["L"]["return_line"] not in (expected, "not_found"):
        errors.append("L.return_line: does not agree with doc_id, kind, status, layered, flags or form path")
    return errors


def _normalise(value):
    # Line wraps from extraction may differ. Case, punctuation and words may not.
    return " ".join(value.split())


def _segments(text, marker):
    matches = list(marker.finditer(text))
    return {int(match.group(1)): text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
            for i, match in enumerate(matches)}


def _references(ref, pattern):
    references = []
    matches = list(pattern.finditer(ref))
    if pattern is PAGE_REF:
        # P6 (p.2) cites a labelled programme clause on page 2. Bare uppercase
        # P-number labels must not become extra pages when a clear page ref exists.
        explicit = [match for match in matches if not re.match(r"P\d", match.group())]
        if explicit:
            matches = explicit
    for match in matches:
        first = int(match.group(1))
        last = int(match.group(2) or first)
        if first < 1 or last < first or last - first > 10000:
            return None
        references.extend(range(first, last + 1))
    return references


def _evidence_entries(value, path=""):
    """Yield both sibling evidence objects and the form's two inline evidence shapes."""
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else key
            if key.endswith("_evidence") and isinstance(item, dict) and "ref" in item and "words" in item:
                yield child, item["ref"], item["words"]
            elif key == "F6_internal_precedence" and isinstance(item, dict):
                yield child, item["page"], item["words"]
            else:
                yield from _evidence_entries(item, child)
        if {"topic", "page_or_clause", "words", "reading"} <= value.keys():
            if value["reading"] not in ("silent", "not_found"):
                yield path, value["page_or_clause"], value["words"]
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _evidence_entries(item, f"{path}[{index}]")


def _text_path(form, text_path):
    if text_path is not None:
        return Path(text_path)
    doc_id = form.get("A", {}).get("doc_id", "") if isinstance(form, dict) else ""
    # Invalid IDs must never become filesystem paths.
    safe_id = doc_id if re.fullmatch(r"\d{3,}", str(doc_id)) else "invalid"
    return TEXT / f"{safe_id}.txt"


def _evidence_checks(form, text_path=None):
    errors, warnings = [], []
    entries = list(_evidence_entries(form))
    text = None
    try:
        text = _text_path(form, text_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        if entries:
            errors.append("evidence: prepared text is unavailable; run prepare or supply text_path")
    pages = _segments(text or "", PAGE_MARKER)
    paragraphs = _segments(text or "", PARAGRAPH_MARKER)
    if text is not None and not pages and not paragraphs:
        pages = {1: text}  # A single page image has only its scan marker.
    for path, reference, words in entries:
        if not isinstance(reference, str) or not isinstance(words, str):
            continue  # Structural validation supplies the precise type error.
        if not words.strip() or words in ("not_found", "none", "inherits"):
            errors.append(f"{path}: evidence needs exact words; omit it for an unanswered question")
            continue
        if len(words.split()) > 40:
            errors.append(f"{path}: quote exceeds 40 words")
        if words == SCAN_MARKER:
            errors.append(f"{path}: the scan marker is not words from the document")
        if reference.isdigit():
            page_refs, paragraph_refs = [int(reference)], []
        else:
            page_refs = _references(reference, PAGE_REF)
            paragraph_refs = _references(reference, PARAGRAPH_REF)
        if page_refs is None or paragraph_refs is None:
            errors.append(f"{path}: page or paragraph range is invalid")
            continue
        clause = CLAUSE_REF.search(reference)
        if not page_refs and not paragraph_refs and not clause:
            errors.append(f"{path}: ref must identify a page, paragraph or clause")
            continue
        if text is None:
            continue
        selected = []
        if paragraph_refs:
            missing = [number for number in paragraph_refs if number not in paragraphs]
            if missing:
                errors.append(f"{path}: cited paragraph does not exist: {', '.join(map(str, missing))}")
                continue
            selected = [paragraphs[number] for number in paragraph_refs]
        elif page_refs:
            if paragraphs and not pages:
                errors.append(f"{path}: Word evidence must cite a paragraph or clause, not a PDF page")
                continue
            missing = [number for number in page_refs if number not in pages]
            if missing:
                errors.append(f"{path}: cited page does not exist: {', '.join(map(str, missing))}")
                continue
            selected = [pages[number] for number in page_refs]
        else:
            # A clause reference is legal, but native extraction does not guarantee a
            # reliable heading tree. Check its words; expose that location limitation.
            selected = list(paragraphs.values()) or list(pages.values())
            warnings.append(f"{path}: clause-only reference; words checked, clause location needs review")
        native = [segment for segment in selected if SCAN_MARKER not in segment]
        has_scan = len(native) != len(selected)
        found = bool(native) and _normalise(words) in _normalise("\n".join(native))
        if not found:
            if has_scan:
                warnings.append(f"{path}: scanned page; exact quote requires visual review")
            elif paragraphs and any("[image:" in segment for segment in selected):
                warnings.append(f"{path}: Word image; exact quote requires visual review")
            else:
                errors.append(f"{path}: quote not found verbatim in native text at the cited location")
    if isinstance(form, dict) and isinstance(form.get("I"), list):
        for index, topic in enumerate(form["I"]):
            if isinstance(topic, dict) and topic.get("reading") == "silent":
                warnings.append(f"I[{index}]: silent is an absence finding; review the document to confirm")
    return errors, warnings


def validate_form(form, text_path=None):
    """Return rejection errors; [] means valid, with possible evidence_warnings()."""
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"schema: could not load document-form.schema.json ({exc})"]
    errors = _schema_errors(form, schema, schema)
    if errors:
        return list(dict.fromkeys(errors))
    errors.extend(_semantic_errors(form))
    errors.extend(_evidence_checks(form, text_path)[0])
    return list(dict.fromkeys(errors))


def evidence_warnings(form, text_path=None):
    """Return visual/manual checks separately from errors; no evidence is silently certified."""
    return list(dict.fromkeys(_evidence_checks(form, text_path)[1]))


def load_form(path):
    """Read JSON without accepting duplicate keys (which would silently discard answers)."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def validate_path(path, text_path=None):
    """Load a form and return errors, using an adjacent work/text folder if one exists."""
    path = Path(path)
    try:
        form = load_form(path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"form: could not read JSON ({exc})"]
    if text_path is None and path.parent.name == "forms":
        candidate = path.parent.parent / "text" / f"{path.stem}.txt"
        if candidate.is_file():
            text_path = candidate
    errors = validate_form(form, text_path)
    if isinstance(form, dict) and isinstance(form.get("A"), dict) and path.stem.isdigit() and path.stem != form["A"].get("doc_id"):
        errors.append("A.doc_id: does not match the numbered form filename")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="form JSON paths")
    parser.add_argument("--all", action="store_true", help="validate every work/forms/*.json")
    parser.add_argument("--doc", action="append", default=[], metavar="NNN", help="document number; repeatable")
    parser.add_argument("--text", type=Path, help="prepared text file, when checking one form")
    args = parser.parse_args(argv)
    paths = list(args.paths)
    for doc_id in args.doc:
        if not re.fullmatch(r"\d{3,}", doc_id):
            parser.error("--doc must be a document number such as 017")
        paths.append(FORMS / f"{doc_id}.json")
    if args.all:
        paths.extend(sorted(FORMS.glob("*.json")))
    paths = list(dict.fromkeys(paths))
    if not paths:
        parser.error("no forms selected or found; use --all, --doc NNN or a JSON path")
    if args.text and len(paths) != 1:
        parser.error("--text requires exactly one form")
    invalid, warning_count = 0, 0
    for path in paths:
        errors = validate_path(path, args.text)
        label = f"doc {path.stem}"
        if errors:
            invalid += 1
            print(f"{label}: INVALID")
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            text_path = args.text
            candidate = path.parent.parent / "text" / f"{path.stem}.txt"
            if text_path is None and path.parent.name == "forms" and candidate.is_file():
                text_path = candidate
            warnings = evidence_warnings(load_form(path), text_path)
            warning_count += len(warnings)
            print(f"{label}: valid" + ("; evidence needs review" if warnings else ""))
            for warning in warnings:
                print(f"  REVIEW: {warning}")
    print(f"{len(paths)} forms checked; {invalid} invalid; {warning_count} evidence checks need review.")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
