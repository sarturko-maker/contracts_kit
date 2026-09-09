"""Inventory the pile: python scripts/prepare.py PILE [--erp PATH] [--account-column NAME]
                                                    [--side customers|suppliers] [--force]

What it does, in order:
1. Walks the pile (files only, symlinks not followed) and finds the ERP record.
2. Copies the ERP record to inputs/erp-record.csv and writes work/erp.json (columns, guessed
   account column, side, accounts, stream candidates).
3. Gives every other file a three-digit number in stable sorted order. Readable files
   (pdf, docx, page images) are hashed, copied to work/files/<id>.<ext>, and their native text
   is written to work/text/<id>.txt with page or paragraph markers. Scanned pages get a marker;
   the model reads those as pictures later.
4. Writes work/inventory.csv (one row per file, unreadable ones included) and
   work/logs/prepare.log, then prints the table, the totals and the unreadable files.

The pile is never modified. Re-runs skip files already done unless --force.
"""

import argparse
import csv
import hashlib
import io
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import (  # noqa: E402
    ERP_EXTS, ERP_JSON, ERP_RECORD_CSV, INVENTORY_COLUMNS, INVENTORY_CSV, NOT_FOUND,
    READABLE_EXTS, KIT, WORK, OUT, WORK_FILES, WORK_LOGS, WORK_TEXT, fail, read_csv, read_json, rel, say, warn,
    safe_folder_name,
    write_csv, write_json, write_text,
)

SCAN_THRESHOLD = 25  # a pdf page with fewer stripped characters than this is "scanned"
SCAN_MARKER = "[scan: look at the page]"

# XML namespaces used inside a .docx
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
DC = "{http://purl.org/dc/elements/1.1/}"
DCTERMS = "{http://purl.org/dc/terms/}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# Short stop-word lists for a rough language guess of the native text.
STOP_WORDS = {
    "en": "the and of to in is that for with by this shall or be are".split(),
    "de": "der die und das ist nicht von mit dem den ein eine zu im auf".split(),
    "fr": "le la les et des est dans pour une un du que par sur au".split(),
    "nl": "de het een en van is niet dat met voor op zijn aan te ook".split(),
    "es": "el la los las y de que en un una por con para es del".split(),
    "it": "il la di che e un una per con non del della sono gli le".split(),
}


# --------------------------------------------------------------------------- walking the pile
def walk_files(folder):
    """Every file under `folder`, recursively, in a stable order. Symlinks are listed, not followed."""
    for entry in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_symlink():
            yield entry
        elif entry.is_dir():
            yield from walk_files(entry)
        elif entry.is_file():
            yield entry


def sha256_of(path):
    """Hex sha256 of the file bytes."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type_of(path):
    """pdf | docx | image | csv | xlsx | other, from the extension."""
    ext = path.suffix.lower().lstrip(".")
    if ext in READABLE_EXTS:
        return READABLE_EXTS[ext]
    if ext in ERP_EXTS:
        return ERP_EXTS[ext]
    return "other"


def guess_language(text):
    """Pick the language with the most stop-word hits (at least 5), else 'not found'."""
    tokens = re.findall(r"[a-zà-ÿ]+", text.lower())
    if not tokens:
        return NOT_FOUND
    best_lang, best_hits = NOT_FOUND, 0
    for lang, words in STOP_WORDS.items():
        wanted = set(words)
        hits = sum(1 for t in tokens if t in wanted)
        if hits > best_hits:
            best_lang, best_hits = lang, hits
    return best_lang if best_hits >= 5 else NOT_FOUND


def first_line(text, limit=80):
    """First non-empty line of the text, cut to `limit` characters."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:limit]
    return ""


# --------------------------------------------------------------------------- the ERP record
def find_erp_record(pile, files, erp_arg):
    """Return the ERP record path. Stops with a plain message if none or several."""
    if erp_arg:
        path = Path(erp_arg).expanduser().resolve()
        if not path.is_file():
            fail(f"--erp {path} is not a file.")
        if path.suffix.lower().lstrip(".") not in ERP_EXTS:
            fail(f"--erp {path.name} must be a .csv or .xlsx file.")
        return path
    candidates = [p for p in files if not p.is_symlink() and file_type_of(p) in ("csv", "xlsx") and "erp" in p.name.lower()]
    if not candidates:
        fail("No ERP record found: a .csv or .xlsx whose name contains 'erp'. "
             "Add one to the pile or pass --erp <path>.")
    if len(candidates) > 1:
        listing = "\n  ".join(str(c) for c in candidates)
        fail(f"{len(candidates)} files look like the ERP record; pass --erp <path> to pick one:\n  {listing}")
    return candidates[0].resolve()


def read_erp_table(path):
    """Read the ERP record as (columns, rows-as-dicts), every value a string."""
    if path.suffix.lower() == ".xlsx":
        return read_xlsx_table(path)
    return read_csv_table(path)


def read_csv_table(path):
    """CSV with unknown encoding and delimiter (comma or semicolon)."""
    raw = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            raw = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        fail(f"could not decode {path.name} as text.")
    header_line = raw.splitlines()[0] if raw.splitlines() else ""
    delimiter = ";" if header_line.count(";") > header_line.count(",") else ","
    reader = csv.reader(io.StringIO(raw), delimiter=delimiter)
    table = [row for row in reader]
    if not table:
        fail(f"{path.name} is empty.")
    columns = [c.strip() for c in table[0]]
    rows = []
    for values in table[1:]:
        if not any(v.strip() for v in values):
            continue
        row = {}
        for i, col in enumerate(columns):
            row[col] = values[i].strip() if i < len(values) else ""
        rows.append(row)
    return columns, rows


def read_xlsx_table(path):
    """First sheet of an .xlsx, header = first row, values as strings."""
    try:
        import openpyxl
    except ImportError:
        fail("the ERP record is .xlsx and openpyxl is not installed: run `pip install -r requirements.txt`.")
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = book.worksheets[0]
    table = []
    for values in sheet.iter_rows(values_only=True):
        table.append([cell_text(v) for v in values])
    book.close()
    if not table:
        fail(f"{path.name} has no rows on its first sheet.")
    columns = [c.strip() for c in table[0]]
    while columns and not columns[-1]:
        columns.pop()
    rows = []
    for values in table[1:]:
        if not any(v.strip() for v in values):
            continue
        rows.append({col: (values[i].strip() if i < len(values) else "") for i, col in enumerate(columns)})
    return columns, rows


def cell_text(value):
    """A spreadsheet cell as plain text."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.hour == 0 and value.minute == 0 and value.second == 0:
            return value.date().isoformat()
        return value.isoformat(sep=" ")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def column_tokens(name):
    """Lower-cased word tokens of a column name."""
    return [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]


def looks_like_id_column(name):
    """True for columns named like a number, id or code."""
    lower = name.lower()
    tokens = set(column_tokens(name))
    return bool(tokens & {"number", "no", "nr", "id", "code", "num"}) or "number" in lower \
        or "code" in lower or lower.endswith("id")


ACCOUNT_COLUMN_PREFERENCE = ["account_name", "account name", "customer_name", "supplier_name",
                             "name", "account", "customer", "supplier", "vendor"]
STRONG_ACCOUNT_NAMES = {"account_name", "account name", "customer_name", "supplier_name",
                        "customer name", "supplier name", "customer_account", "supplier_account",
                        "customer account", "supplier account"}


def guess_account_column(columns):
    """First column whose name contains a preferred word, skipping number/id/code columns."""
    for wanted in ACCOUNT_COLUMN_PREFERENCE:
        for col in columns:
            if wanted in col.lower() and not looks_like_id_column(col):
                return col
    return None


def guess_side(columns, rows):
    """(side, column) from a side/type/category/role column whose values all agree; else (None, None)."""
    for col in columns:
        lower = col.lower()
        if not any(word in lower for word in ("side", "type", "category", "role")):
            continue
        values = {row.get(col, "").strip().lower().rstrip("s") for row in rows if row.get(col, "").strip()}
        if values and values <= {"customer"}:
            return "customers", col
        if values and values <= {"supplier", "vendor"}:
            return "suppliers", col
        if values & {'customer', 'supplier', 'vendor'}:
            return None, None  # Mixed/contradictory side data requires the operator.
    named_sides = {}
    for col in columns:
        if col.lower() in STRONG_ACCOUNT_NAMES:
            words = set(column_tokens(col))
            for word, side in [('customer', 'customers'), ('supplier', 'suppliers')]:
                if word in words:
                    named_sides[side] = col
    if len(named_sides) == 1:
        side, col = next(iter(named_sides.items()))
        return side, col
    return None, None


def guess_number_column(columns, account_column):
    """First number/id/code column that is not the account column."""
    for col in columns:
        if col != account_column and looks_like_id_column(col):
            return col
    return None


def guess_country_column(columns):
    """A column named like 'country'."""
    for col in columns:
        if "country" in col.lower():
            return col
    return None


def stream_candidates(names):
    """{longer name: shorter name} where a name starts with another name plus a space."""
    found = {}
    for name in names:
        best = None
        for other in names:
            if other != name and name.lower().startswith(other.lower() + " "):
                if best is None or len(other) > len(best):
                    best = other
        if best:
            found[name] = best
    return found


def prepare_erp(erp_path, args):
    """Copy the ERP record, guess its columns, write work/erp.json. Returns the erp dict."""
    columns, rows = read_erp_table(erp_path)
    write_csv(ERP_RECORD_CSV, rows, columns)
    say(f"ERP record: {erp_path}")
    say(f"  copied to {rel(ERP_RECORD_CSV)} with columns: {', '.join(columns)}")

    if args.account_column:
        if args.account_column not in columns:
            fail(f"--account-column {args.account_column!r} is not a column. Columns: {', '.join(columns)}")
        account_column = args.account_column
        account_confirmed = True
    else:
        account_column = guess_account_column(columns)
        account_confirmed = account_column is not None and account_column.lower() in STRONG_ACCOUNT_NAMES

    side_column = None
    if args.side:
        side = args.side
        side_confirmed = True
    else:
        side, side_column = guess_side(columns, rows)
        side_confirmed = side is not None

    number_column = guess_number_column(columns, account_column)
    country_column = guess_country_column(columns)

    accounts = []
    if account_column:
        for row in rows:
            name = row.get(account_column, "").strip()
            if not name:
                continue
            accounts.append({
                "account": name,
                "account_number": row.get(number_column, "").strip() if number_column else "",
                "country": row.get(country_column, "").strip() if country_column else "",
            })
    names = [a["account"] for a in accounts]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        warn(f"the ERP record repeats these account names: {', '.join(duplicates)}; one folder each")
    portable_names = {}
    for name in names:
        folder = safe_folder_name(name).casefold()
        if folder in {'_not-on-the-list', '_not-sure', '_no-name-found', '_unreadable', 'assets'}:
            fail(f"ERP account {name!r} conflicts with a reserved holding folder; correct the ERP record.")
        if folder in portable_names and portable_names[folder] != name:
            fail(f"ERP accounts {portable_names[folder]!r} and {name!r} produce the same portable folder.")
        portable_names[folder] = name

    erp = {
        "source_path": str(erp_path),
        "copied_to": "inputs/erp-record.csv",
        "columns": columns,
        "account_column": account_column,
        "side": side,
        "side_column": side_column,
        "account_number_column": number_column,
        "country_column": country_column,
        "accounts": accounts,
        "stream_candidates": stream_candidates(names),
        "confirmed": bool(account_confirmed and side_confirmed),
    }
    write_json(ERP_JSON, erp)

    say(f"  account column: {account_column or 'NOT FOUND - pass --account-column <name>'}"
        + ("" if account_confirmed else " (guess; confirm it)"))
    say(f"  side: {side or 'NOT FOUND - pass --side customers|suppliers'}"
        + (f" (from column {side_column!r})" if side_column else ""))
    say(f"  account number column: {number_column or 'none'}; country column: {country_column or 'none'}")
    say(f"  accounts ({len(accounts)}):")
    for acc in accounts:
        extra = ", ".join(x for x in (acc["account_number"], acc["country"]) if x)
        say(f"    - {acc['account']}" + (f" ({extra})" if extra else ""))
    if erp["stream_candidates"]:
        say("  stream candidates (rows that look like streams of another row; /sort decides):")
        for name, main in erp["stream_candidates"].items():
            say(f"    - {name!r} looks like a stream of {main!r}")
    say(f"  confirmed: {erp['confirmed']}"
        + ("" if erp["confirmed"] else "  (the /prepare skill re-runs with --account-column and --side to confirm)"))
    return erp


# --------------------------------------------------------------------------- pdf
def pdf_page_has_image(page):
    """True when the page's resources hold an /XObject of /Subtype /Image."""
    try:
        resources = page.get("/Resources")
        if resources is None:
            return False
        xobjects = resources.get_object().get("/XObject")
        if xobjects is None:
            return False
        xobjects = xobjects.get_object()
        for name in xobjects:
            obj = xobjects[name].get_object()
            if obj.get("/Subtype") == "/Image":
                return True
    except Exception:  # noqa: BLE001 - a broken resource tree is not a reason to stop
        return False
    return False


def extract_pdf(source, doc_id, file_name):
    """Read a pdf. Returns (fields for the inventory row, text file content) or (fields, None) if unreadable."""
    import pypdf
    fields = {}
    try:
        reader = pypdf.PdfReader(str(source))
        if reader.is_encrypted:
            try:
                if not reader.decrypt(""):
                    raise ValueError("encrypted")
            except Exception:  # noqa: BLE001
                fields["readable"] = "no"
                fields["note"] = "pdf is encrypted"
                return fields, None
        pages = list(reader.pages)
    except Exception as err:  # noqa: BLE001 - pypdf raises many kinds
        fields["readable"] = "no"
        fields["note"] = f"pdf could not be opened: {err}"
        return fields, None

    page_texts = []
    kinds = []
    has_image = False
    for page in pages:
        try:
            text = page.extract_text() or ""
        except Exception as err:  # noqa: BLE001
            text = f"[text extraction failed: {err}]"
            kinds.append("s")
            page_texts.append(text)
            has_image = has_image or pdf_page_has_image(page)
            continue
        kinds.append("s" if len(text.strip()) < SCAN_THRESHOLD else "t")
        page_texts.append(text)
        has_image = has_image or pdf_page_has_image(page)

    scanned = [i + 1 for i, k in enumerate(kinds) if k == "s"]
    native_text = "\n".join(t for t, k in zip(page_texts, kinds) if k == "t")
    lines = [f"[doc {doc_id} | {file_name} | {len(pages)} pages | scanned pages: "
             f"{', '.join(str(n) for n in scanned) if scanned else 'none'}]"]
    for number, (text, kind) in enumerate(zip(page_texts, kinds), start=1):
        lines.append(f"=== page {number} ===")
        if kind == "s":
            if text.startswith("[text extraction failed"):
                lines.append(text)
            lines.append(SCAN_MARKER)
        else:
            lines.append(text.rstrip())
    fields.update({
        "readable": "yes",
        "pages": str(len(pages)),
        "scanned_pages": str(len(scanned)),
        "text_pages": str(len(pages) - len(scanned)),
        "page_kinds": "".join(kinds),
        "language": guess_language(native_text),
        "has_images": "yes" if has_image else "no",
        "title_guess": first_line(native_text),
        "note": "" if not scanned else (
            "every page is a scan" if len(scanned) == len(pages) else f"scanned pages: {', '.join(str(n) for n in scanned)}"),
    })
    return fields, "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- docx
def docx_core_properties(zf):
    """(author, created, modified) from docProps/core.xml; blanks when absent."""
    try:
        root = ElementTree.fromstring(zf.read("docProps/core.xml"))
    except (KeyError, ElementTree.ParseError):
        return "", "", ""
    author = (root.findtext(f"{DC}creator") or "").strip()
    created = (root.findtext(f"{DCTERMS}created") or "").strip()
    modified = (root.findtext(f"{DCTERMS}modified") or "").strip()
    return author, created, modified


def docx_relationships(zf):
    """{rId: target} from word/_rels/document.xml.rels."""
    try:
        root = ElementTree.fromstring(zf.read("word/_rels/document.xml.rels"))
    except (KeyError, ElementTree.ParseError):
        return {}
    rels = {}
    for rel_el in root.iter(f"{PKG_REL}Relationship"):
        rels[rel_el.get("Id", "")] = rel_el.get("Target", "")
    return rels


def docx_comments(zf):
    """List of (id, author, date, text) from word/comments.xml, in file order."""
    try:
        root = ElementTree.fromstring(zf.read("word/comments.xml"))
    except (KeyError, ElementTree.ParseError):
        return []
    comments = []
    for c in root.iter(f"{W}comment"):
        text = " ".join(t.text or "" for t in c.iter(f"{W}t")).strip()
        comments.append((c.get(f"{W}id", ""), c.get(f"{W}author", ""), c.get(f"{W}date", ""), text))
    return comments


def paragraph_content(p_el, rels, media_prefix):
    """Text of one w:p with tracked changes inline; also the image markers and comment ids found.

    Inserted runs are shown as {+text+}, deleted runs as {-text-}. Nested paragraphs (text
    boxes) are not descended into here; the caller lists every w:p on its own.
    """
    pieces = []
    images = []
    comment_ids = []

    def run_text(run_el, deleted):
        out = []
        for child in run_el:
            if child.tag == f"{W}t" or (deleted and child.tag == f"{W}delText"):
                out.append(child.text or "")
            elif child.tag == f"{W}tab":
                out.append("\t")
            elif child.tag in (f"{W}br", f"{W}cr"):
                out.append("\n")
            elif child.tag == f"{W}commentReference":
                comment_ids.append(child.get(f"{W}id", ""))
            elif child.tag in (f"{W}drawing", f"{W}pict", f"{W}object"):
                images.append(image_marker(child, rels, media_prefix))
        return "".join(out)

    def visit(el, mode):
        for child in el:
            tag = child.tag
            if tag == f"{W}p":
                continue  # a nested paragraph is listed on its own
            if tag == f"{W}r":
                text = run_text(child, deleted=(mode == "del"))
                if text:
                    pieces.append(wrap(text, mode))
            elif tag == f"{W}ins":
                visit(child, "ins")
            elif tag == f"{W}del":
                visit(child, "del")
            elif tag == f"{W}commentRangeStart":
                comment_ids.append(child.get(f"{W}id", ""))
            elif tag in (f"{W}hyperlink", f"{W}smartTag", f"{W}sdt", f"{W}sdtContent",
                         f"{W}fldSimple", f"{W}customXml", f"{W}moveTo", f"{W}moveFrom"):
                visit(child, mode)

    def wrap(text, mode):
        if mode == "ins":
            return "{+" + text + "+}"
        if mode == "del":
            return "{-" + text + "-}"
        return text

    visit(p_el, "")
    text = "".join(pieces)
    # merge adjacent markers of the same kind so a word split over runs reads as one change
    text = text.replace("+}{+", "").replace("-}{-", "")
    return text, images, comment_ids


def image_marker(el, rels, media_prefix):
    """'[image: work/files/<id>-media/<file>]' for the picture referenced inside el."""
    for node in el.iter():
        rid = node.get(f"{R}embed") or node.get(f"{R}id") or node.get(f"{R}link")
        if rid and rid in rels:
            target = rels[rid]
            if "media/" in target:
                return f"[image: {media_prefix}/{Path(target).name}]"
    return "[image: embedded picture, not extracted]"


def extract_docx(source, doc_id, file_name, media_folder):
    """Read a docx. Returns (fields, text) or (fields, None) if unreadable."""
    fields = {}
    try:
        zf = zipfile.ZipFile(source)
        document_xml = zf.read("word/document.xml")
        root = ElementTree.fromstring(document_xml)
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError, OSError) as err:
        fields["readable"] = "no"
        fields["note"] = f"docx could not be opened: {err}"
        return fields, None

    with zf:
        author, created, modified = docx_core_properties(zf)
        rels = docx_relationships(zf)
        comments = docx_comments(zf)
        media_names = [n for n in zf.namelist() if n.startswith("word/media/") and not n.endswith("/")]
        if media_names:
            media_folder.mkdir(parents=True, exist_ok=True)
            for name in media_names:
                target = media_folder / Path(name).name
                target.write_bytes(zf.read(name))

        body = root.find(f"{W}body")
        if body is None:
            body = root
        n_ins = sum(1 for _ in root.iter(f"{W}ins"))
        n_del = sum(1 for _ in root.iter(f"{W}del"))
        tracked = f"yes ({n_ins + n_del})" if (n_ins + n_del) else "no"
        comment_index = {cid: i + 1 for i, (cid, _, _, _) in enumerate(comments)}
        media_prefix = f"work/files/{doc_id}-media"

        header = (f"[doc {doc_id} | {file_name} | docx | author: {author} | created: {created} | "
                  f"modified: {modified} | tracked changes: {tracked} | comments: {len(comments)} | "
                  f"images: {len(media_names)}]")
        lines = [header]
        plain_lines = []
        paragraphs = list(body.iter(f"{W}p"))
        for number, p_el in enumerate(paragraphs, start=1):
            text, images, comment_ids = paragraph_content(p_el, rels, media_prefix)
            parts = []
            if text.strip():
                parts.append(text.strip())
            parts.extend(images)
            if not parts:
                continue
            line = " ".join(parts)
            anchors = sorted({comment_index[c] for c in comment_ids if c in comment_index})
            for anchor in anchors:
                line += f" [comment {anchor}]"
            lines.append(f"[¶ {number}] {line}")
            if text.strip():
                plain_lines.append(re.sub(r"\{[+-]|[+-]\}", "", text.strip()))
        for i, (_, c_author, c_date, c_text) in enumerate(comments, start=1):
            lines.append(f"[comment {i} by {c_author} ({c_date}): {c_text}]")

    plain_text = "\n".join(plain_lines)
    fields.update({
        "readable": "yes",
        "pages": "",
        "scanned_pages": "0",
        "text_pages": "0",
        "page_kinds": "",
        "paragraphs": str(len(paragraphs)),
        "language": guess_language(plain_text),
        "docx_author": author,
        "docx_created": created,
        "docx_modified": modified,
        "docx_tracked_changes": tracked,
        "docx_comments": str(len(comments)),
        "has_images": "yes" if media_names else "no",
        "title_guess": first_line(plain_text),
        "note": "; ".join(n for n in (
            "tracked changes present" if tracked != "no" else "",
            f"{len(comments)} comments" if comments else "",
        ) if n),
    })
    return fields, "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- one file
def blank_row(doc_id, path, pile):
    """An inventory row with the identity fields filled and the rest blank."""
    ext = path.suffix.lower().lstrip(".")
    row = {c: "" for c in INVENTORY_COLUMNS}
    row.update({
        "doc_id": doc_id,
        "original_path": str(path),
        "file_name": path.name,
        "ext": ext,
        "file_type": file_type_of(path),
        "readable": "no",
    })
    if row["file_type"] != "docx":
        for col in ("docx_author", "docx_created", "docx_modified", "docx_tracked_changes", "docx_comments"):
            row[col] = "n/a"
    return row


def process_file(doc_id, path, pile, previous, force, log):
    """Build the inventory row for one numbered file, copying and extracting when readable."""
    row = blank_row(doc_id, path, pile)
    if path.is_symlink():
        row["note"] = "symbolic link; not followed"
        return row
    if path.name.startswith("."):
        row["note"] = "hidden file"
        row["size_bytes"] = str(path.stat().st_size)
        return row
    row["size_bytes"] = str(path.stat().st_size)
    row["sha256"] = sha256_of(path)
    if row["file_type"] not in ("pdf", "docx", "image"):
        row["note"] = "not readable by the kit"
        return row

    copy_target = WORK_FILES / f"{doc_id}.{row['ext']}"
    text_target = WORK_TEXT / f"{doc_id}.txt"
    old = previous.get(doc_id)
    if (not force and old is not None and copy_target.exists() and text_target.exists()
            and old.get("sha256") == row["sha256"] and old.get("original_path") == row["original_path"]
            and old.get("readable") == "yes"):
        log.append(f"skip doc {doc_id} (done)")
        say(f"skip doc {doc_id} (done)")
        kept = {c: old.get(c, "") for c in INVENTORY_COLUMNS}
        return kept
    if old is not None and old.get("original_path") and old.get("original_path") != row["original_path"]:
        warn(f"doc {doc_id} was {old['original_path']} on the last run and is now {row['original_path']}: "
             "the pile changed, so earlier cards may point at the wrong document")

    if row["file_type"] == "pdf":
        fields, text = extract_pdf(path, doc_id, path.name)
    elif row["file_type"] == "docx":
        fields, text = extract_docx(path, doc_id, path.name, WORK_FILES / f"{doc_id}-media")
    else:
        fields, text = {
            "readable": "yes", "pages": "1", "scanned_pages": "1", "text_pages": "0",
            "page_kinds": "s", "language": NOT_FOUND, "has_images": "yes", "title_guess": "",
            "note": "page image; read as a picture",
        }, f"[doc {doc_id} | {path.name} | 1 pages | scanned pages: 1]\n{SCAN_MARKER}\n"
    row.update(fields)
    if row["readable"] != "yes":
        return row

    WORK_FILES.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, copy_target)
    write_text(text_target, text)
    log.append(f"doc {doc_id}: copied {path} -> {rel(copy_target)}; text -> {rel(text_target)}")
    return row


# --------------------------------------------------------------------------- reporting
def invalidate_changed_sources(previous, rows, erp_changed=False):
    """Archive generated readings when their source changes; never reuse a stale card."""
    current = {r['doc_id']: r for r in rows}
    changed = {d for d, old in previous.items() if d != 'erp' and
               (d not in current or any(old.get(k) != current[d].get(k)
                                        for k in ('sha256', 'original_path', 'readable')))}
    added = set(current) - set(previous) - {'erp'}
    if not (changed or added or erp_changed):
        return
    paths = []
    for doc in changed:
        paths += [WORK / sub / f'{doc}{ext}' for sub, extensions in
                  [('cards', ['.json', '.md']), ('forms', ['.json']), ('filing', ['.json'])] for ext in extensions]
    # Placement prose and family proposals depend on the complete account population.
    if previous:
        for sub in ('placements', 'trees', 'didnt-fit'):
            paths.extend((WORK / sub).glob('*'))
        paths.append(WORK_LOGS / 'sort.csv')
        if erp_changed:
            paths.extend((WORK / 'forms').glob('*.json'))
    archive = WORK / 'history' / datetime.now().strftime('%Y%m%dT%H%M%S%f')
    archived = 0
    for path in dict.fromkeys(paths):
        if path.is_file():
            target = archive / path.relative_to(WORK)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            path.unlink()
            archived += 1
    if archived:
        say(f'Archived {archived} stale generated files to {rel(archive)}. Run /sort for filing, or /deep-dive to rebuild full analysis.')


def print_table(rows):
    """Print the inventory as id | file | type | pages | scanned | note."""
    say("")
    say(f"{'id':<4} | {'file':<48} | {'type':<5} | {'pages':>5} | {'scanned':>7} | note")
    say("-" * 100)
    for row in rows:
        name = row["file_name"] if len(row["file_name"]) <= 48 else row["file_name"][:45] + "..."
        say(f"{row['doc_id']:<4} | {name:<48} | {row['file_type']:<5} | {row['pages']:>5} | "
            f"{row['scanned_pages']:>7} | {row['note']}")


def totals_lines(rows):
    """The totals block as a list of lines."""
    docs = [r for r in rows if r["doc_id"] != "erp"]
    by_type = {}
    for r in docs:
        by_type[r["file_type"]] = by_type.get(r["file_type"], 0) + 1
    readable = [r for r in docs if r["readable"] == "yes"]
    unreadable = [r for r in docs if r["readable"] != "yes"]
    total_pages = sum(int(r["pages"] or 0) for r in readable)
    scanned_pages = sum(int(r["scanned_pages"] or 0) for r in readable)
    tracked = [r for r in readable if r["docx_tracked_changes"].startswith("yes")]
    lines = [
        "",
        "Totals",
        "  files by type: " + ", ".join(f"{t} {n}" for t, n in sorted(by_type.items())),
        f"  readable by the kit: {len(readable)}; not readable: {len(unreadable)}",
        f"  pages (pdf and images): {total_pages}",
        f"  scanned pages, read as pictures: {scanned_pages}  "
        "(a page read as a picture costs several times a page read as text)",
        f"  docx files with tracked changes: {len(tracked)}"
        + (" (" + ", ".join("doc " + r["doc_id"] for r in tracked) + ")" if tracked else ""),
    ]
    if unreadable:
        lines.append("")
        lines.append("Files not readable by the kit (listed, not skipped):")
        for r in unreadable:
            lines.append(f"  doc {r['doc_id']}: {r['original_path']}  ({r['note']})")
    else:
        lines.append("  every file in the pile is readable by the kit")
    return lines


# --------------------------------------------------------------------------- main
def main():
    parser = argparse.ArgumentParser(description="Inventory, number, hash and extract the pile.")
    parser.add_argument("pile", help="folder with the contract files and the ERP record (read only)")
    parser.add_argument("--erp", help="path to the ERP record if its name does not contain 'erp'")
    parser.add_argument("--review-table", help="CSV/XLSX review export; otherwise discover Review_Table.csv/xlsx")
    parser.add_argument("--review-table-light", help="CSV/XLSX filing export; otherwise discover Review_Table_Light.csv/xlsx")
    parser.add_argument("--account-column", help="ERP column holding the account name")
    parser.add_argument("--side", choices=["customers", "suppliers"], help="which side this run sorts")
    parser.add_argument("--force", action="store_true", help="redo files already done")
    args = parser.parse_args()

    pile = Path(args.pile).expanduser()
    if not pile.is_dir():
        fail(f"{pile} is not a folder. Give the folder that holds the pile.")
    pile = pile.resolve()
    if KIT.is_relative_to(pile) or any(pile.is_relative_to(p.resolve()) for p in (WORK, OUT)):
        fail('The pile must be separate from the kit root and generated work/out folders.')
    try:
        import pypdf  # noqa: F401
    except ImportError:
        fail("pypdf is not installed: run `pip install -r requirements.txt`.")

    files = list(walk_files(pile))
    if not files:
        fail(f"{pile} holds no files.")
    say(f"Pile: {pile} ({len(files)} files)")

    from review_table import find_review_table, SOURCE as REVIEW_SOURCE
    light_source = WORK / "review-light-source.json"
    try:
        review_path = find_review_table(pile, args.review_table)
        light_path = find_review_table(pile, args.review_table_light, light=True)
    except ValueError as err:
        fail(str(err))
    if review_path and review_path == light_path:
        fail("Review_Table and Review_Table_Light must be separate files.")
    controls = {review_path, light_path} | {
        p.resolve() for p in files if p.stem.casefold() in {"review_table", "review_table_light"}
        and p.suffix.casefold() in {".csv", ".xlsx"} and not p.is_symlink()}
    erp_path = find_erp_record(pile, [p for p in files if p.resolve() not in controls], args.erp)
    if erp_path in controls:
        fail("ERP, Review_Table and Review_Table_Light must be separate files.")
    previous_erp = read_json(ERP_JSON)
    erp = prepare_erp(erp_path, args)

    # numbering: everything but the ERP record, stable sorted order
    others = [p for p in files if p.resolve() not in {erp_path, *controls}]
    others.sort(key=lambda p: p.relative_to(pile).as_posix().lower())

    previous = {r["doc_id"]: r for r in read_csv(INVENTORY_CSV)} if INVENTORY_CSV.exists() else {}
    log = [f"prepare.py run {datetime.now().isoformat(timespec='seconds')} on {pile}"]
    if review_path:
        review_config = read_json(REVIEW_SOURCE) or {}
        if review_config.get("source_path") != str(review_path):
            review_config = {}
        write_json(REVIEW_SOURCE, {**review_config, "source_path": str(review_path), "sha256": sha256_of(review_path)})
        message = f"Review_Table input: {review_path}; registered in work/review-source.json, not numbered as a contract"
        say(message)
        log.append(message)
    if light_path:
        light_config = read_json(light_source) or {}
        if light_config.get("source_path") != str(light_path):
            light_config = {}
        write_json(light_source, {**light_config, "source_path": str(light_path), "sha256": sha256_of(light_path)})
        message = f"Review_Table_Light input: {light_path}; registered separately, not numbered as a contract"
        say(message)
        log.append(message)
    WORK_LOGS.mkdir(parents=True, exist_ok=True)
    WORK_TEXT.mkdir(parents=True, exist_ok=True)
    WORK_FILES.mkdir(parents=True, exist_ok=True)

    rows = []
    erp_row = blank_row("erp", erp_path, pile)
    erp_row.update({
        "readable": "yes",
        "sha256": sha256_of(erp_path),
        "size_bytes": str(erp_path.stat().st_size),
        "note": "ERP record; copied to inputs/erp-record.csv",
    })
    rows.append(erp_row)

    say("")
    say(f"Numbering {len(others)} files ...")
    by_path = {r['original_path']: d for d, r in previous.items() if d != 'erp'}
    next_id = max([int(d) for d in previous if d.isdigit()] or [0]) + 1
    for path in others:
        doc_id = by_path.get(str(path))
        if doc_id is None:
            doc_id = f'{next_id:03d}'
            next_id += 1
        rows.append(process_file(doc_id, path, pile, previous, args.force, log))

    # Removed originals retain their numbers and an explicit audit row; numbers are never reused.
    present_ids = {r['doc_id'] for r in rows}
    for doc_id, old in previous.items():
        if old.get("original_path") in {str(p) for p in controls if p}:
            continue  # the control file is audited in review-source.json, not as a contract
        if doc_id != 'erp' and doc_id not in present_ids:
            rows.append({**old, 'readable': 'no', 'note': 'source no longer in pile; previous number retained'})
    invalidate_changed_sources(previous, rows, previous_erp is not None and previous_erp != erp)

    write_csv(INVENTORY_CSV, rows, INVENTORY_COLUMNS)
    print_table(rows)
    totals = totals_lines(rows)
    for line in totals:
        say(line)
    log.extend(totals)
    log.append(f"inventory written: {rel(INVENTORY_CSV)}")
    write_text(WORK_LOGS / "prepare.log", "\n".join(log) + "\n")
    say("")
    say(f"Written: {rel(INVENTORY_CSV)}, {rel(ERP_JSON)}, {rel(ERP_RECORD_CSV)}, work/text/, work/files/, "
        f"{rel(WORK_LOGS / 'prepare.log')}")
    if not erp["confirmed"]:
        say("The ERP account column or the side is not confirmed yet: re-run with --account-column and --side.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
