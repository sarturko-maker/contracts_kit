"""Preflight for the kit: python scripts/check.py [--pile PATH] [--erp PATH]

Prints one line per check: `ok  <what>` or `FAIL <what>: <how to fix>` (or `skip <what>`).
Exits 1 if any check fails, so nothing else runs on a broken setup.
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import ASSETS, MERMAID_JS, OUT, WORK, ERP_EXTS, is_erp_top  # noqa: E402


def find_erp_candidates(pile):
    """Files under the pile that look like the ERP record: .csv/.xlsx with 'erp' in the name."""
    found = []
    for path in sorted(pile.rglob("*")):
        if path.is_file() and not path.is_symlink():
            if path.suffix.lower().lstrip(".") in ERP_EXTS and "erp" in path.name.lower() and not is_erp_top(path):
                found.append(path)
    return found


def check_writable(folder):
    """Create the folder if needed, write and delete a probe file. Returns an error or None."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".write-probe"
        probe.write_text("probe", encoding="utf-8")
        probe.unlink()
        return None
    except OSError as err:
        return str(err)


def poppler_install_hint():
    if sys.platform == "win32":
        return "run `winget install --id oschwartz10612.Poppler --exact --source winget`"
    if sys.platform == "darwin":
        return "run `brew install poppler`"
    return "install Poppler utilities (Debian/Ubuntu: `sudo apt install poppler-utils`)"


def check_poppler():
    """Render an invented PDF to JPEG; do not read any corpus data. Error or None."""
    executable = shutil.which("pdftoppm")
    if executable is None:
        return (f"pdftoppm not on PATH: {poppler_install_hint()}; "
                "restart the terminal and Claude Code, then rerun /check")
    try:
        from pypdf import PdfWriter
    except ImportError:
        return "JPEG render probe needs pypdf: run `pip install -r requirements.txt`"

    remedy = ("check the pdftoppm selected on PATH and use a Poppler build with JPEG support "
              "(see README.md); restart the terminal and Claude Code, then rerun /check")
    try:
        with tempfile.TemporaryDirectory(prefix="contracts-kit-pdf-check-") as directory:
            pdf = Path(directory) / "probe.pdf"
            prefix = Path(directory) / "probe"
            with PdfWriter() as writer:
                writer.add_blank_page(width=72, height=72)
                writer.write(str(pdf))
            result = subprocess.run(
                [executable, "-f", "1", "-l", "1", "-singlefile", "-r", "72",
                 "-jpeg", str(pdf), str(prefix)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
            )
            if result.returncode:
                detail = " ".join(result.stderr.split())[:240]
                return f"JPEG render failed (exit {result.returncode}; {detail}): {remedy}"
            jpeg = prefix.with_suffix(".jpg")
            data = jpeg.read_bytes() if jpeg.is_file() else b""
            if not (data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")):
                return f"JPEG render produced no JPEG image: {remedy}"
    except subprocess.TimeoutExpired:
        return f"JPEG render timed out after 15 seconds: {remedy}"
    except OSError as err:
        return f"JPEG render could not run ({err}): {remedy}"
    return None


def main():
    parser = argparse.ArgumentParser(description="Preflight checks for the DCG intake kit.")
    parser.add_argument("--pile", help="folder holding the contract files and the ERP record")
    parser.add_argument("--erp", help="the ERP record, if its name does not contain 'erp'")
    parser.add_argument("--review-table", help="CSV/XLSX review export; otherwise discover Review_Table in the pile")
    parser.add_argument("--review-table-light", help="CSV/XLSX light export; otherwise discover Review_Table_Light")
    parser.add_argument("--light-sheet", help="worksheet to check in the Review_Table_Light XLSX")
    parser.add_argument("--light-only", action="store_true", help="check the light workflow without validating the optional full export")
    parser.add_argument("--sheet", help="worksheet to check in the Review_Table XLSX")
    args = parser.parse_args()

    results = []  # (status, text); status is ok / FAIL / skip
    prefixes = {"ok": "ok  ", "FAIL": "FAIL ", "skip": "skip "}

    def ok(text):
        results.append(("ok", text))

    def fail(text):
        results.append(("FAIL", text))

    def skip(text):
        results.append(("skip", text))

    # 1. Python version
    version = sys.version_info
    if version >= (3, 10):
        ok(f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        fail(f"Python {version.major}.{version.minor} found: install Python 3.10 or later")

    # 2. pypdf, and openpyxl only if the ERP record is .xlsx
    try:
        import pypdf  # noqa: F401
        ok(f"pypdf {getattr(pypdf, '__version__', '(version unknown)')} importable")
    except ImportError:
        fail("pypdf not importable: run `pip install -r requirements.txt`")

    erp_path = None
    erp_is_xlsx = None

    # 3 and 4. The pile and the ERP record
    if args.pile is None:
        skip("pile path not given: `/prepare <path>` needs the pile")
        skip("ERP record: not checked without a pile path")
    else:
        pile = Path(args.pile).expanduser()
        if not pile.exists():
            fail(f"pile path {pile} does not exist: check the path")
        elif not pile.is_dir():
            fail(f"pile path {pile} is not a folder: give the folder that holds the files")
        elif not os.access(pile, os.R_OK):
            fail(f"pile path {pile} is not readable: check permissions")
        else:
            files = [p for p in pile.rglob("*") if p.is_file()]
            if not files:
                fail(f"pile path {pile} holds no files: drop the contracts and the ERP record in it")
            else:
                ok(f"pile {pile} readable, {len(files)} files")
            if args.erp:
                erp_path = Path(args.erp).expanduser()
                if erp_path.is_file():
                    ok(f"ERP record given: {erp_path.name}")
                else:
                    fail(f"--erp {erp_path} is not a file: check the path")
                    erp_path = None
            else:
                candidates = find_erp_candidates(pile)
                if len(candidates) == 1:
                    erp_path = candidates[0]
                    ok(f"ERP record found: {erp_path.name}")
                elif not candidates:
                    fail("no ERP record found (a .csv or .xlsx whose name contains 'erp'): "
                         "add one to the pile or pass --erp <path>")
                else:
                    names = ", ".join(c.name for c in candidates)
                    fail(f"{len(candidates)} ERP record candidates ({names}): pass --erp <path> to pick one")
    if erp_path is not None:
        erp_is_xlsx = erp_path.suffix.lower() == ".xlsx"
    if erp_is_xlsx:
        try:
            import openpyxl  # noqa: F401
            ok(f"openpyxl {getattr(openpyxl, '__version__', '')} importable (ERP record is xlsx)")
        except ImportError:
            fail("openpyxl not importable and the ERP record is .xlsx: "
                 "run `pip install -r requirements.txt` or save the ERP record as .csv")
    elif erp_is_xlsx is False:
        ok("openpyxl not needed (ERP record is csv)")
    else:
        skip("openpyxl: only needed if the ERP record is .xlsx")

    # Review_Table is a control input; validate its format without invoking a model.
    if args.light_only:
        skip("Review_Table: full analysis validation deferred; light filing does not use it")
    elif args.review_table or (args.pile and Path(args.pile).expanduser().is_dir()):
        try:
            from review_table import find_review_table, read_table
            review = find_review_table(Path(args.pile or ".").expanduser(), args.review_table)
            if review:
                rows = read_table(review, args.sheet)
                ok(f"Review_Table {review.name}: {len(rows)} rows; ten analysis columns present")
            else:
                skip("Review_Table not supplied: /analyse will use full source readers")
        except (ValueError, OSError, ImportError, zipfile.BadZipFile) as err:
            fail(f"Review_Table: {err}; see docs/review-table-pilot.md")
    else:
        skip("Review_Table: supply a pile path or --review-table to check the export")

    if args.review_table_light or (args.pile and Path(args.pile).expanduser().is_dir()):
        try:
            from review_table import find_review_table
            from sort_light import read_export
            light = find_review_table(Path(args.pile or ".").expanduser(), args.review_table_light, light=True)
            if light:
                light_rows, _ = read_export(light, args.light_sheet)
                ok(f"Review_Table_Light: {len(light_rows)} rows; filing input, separate from full analysis")
            else:
                skip("Review_Table_Light: not supplied; /sort requires this export")
        except (ValueError, OSError, ImportError, csv.Error, zipfile.BadZipFile) as err:
            fail(f"Review_Table_Light: {err}; see docs/review-table-light.md")

    # 5. Claude Code's PDF page/image reads need an external renderer, not just pypdf.
    if args.light_only:
        skip("Poppler: light filing does not open page images")
    else:
        error = check_poppler()
        if error:
            fail(f"Poppler: {error}")
        else:
            ok("Poppler pdftoppm on PATH; invented PDF rendered to JPEG")

    # 6. mermaid.min.js
    if args.light_only:
        skip("Mermaid: light filing produces no diagrams")
    elif MERMAID_JS.is_file() and MERMAID_JS.stat().st_size > 1_000_000:
        ok(f"assets/mermaid.min.js present ({MERMAID_JS.stat().st_size // 1024} KB)")
    elif MERMAID_JS.is_file():
        fail(f"assets/mermaid.min.js is only {MERMAID_JS.stat().st_size} bytes: "
             "re-download the kit; the file should be over 1 MB")
    else:
        fail(f"assets/mermaid.min.js missing from {ASSETS}: re-download the kit")

    # 7. work/ and out/ writable
    for folder in (WORK, OUT):
        err = check_writable(folder)
        if err:
            fail(f"{folder.name}/ not writable ({err}): check folder permissions")
        else:
            ok(f"{folder.name}/ writable")

    failed = False
    for status, text in results:
        print(prefixes[status] + text)
        if status == "FAIL":
            failed = True
    if failed:
        print("Fix the FAIL lines above before running anything else.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
