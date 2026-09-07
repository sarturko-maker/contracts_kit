"""Preflight for the kit: python scripts/check.py [--pile PATH] [--erp PATH]

Prints one line per check: `ok  <what>` or `FAIL <what>: <how to fix>` (or `skip <what>`).
Exits 1 if any check fails, so nothing else runs on a broken setup.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import ASSETS, MERMAID_JS, OUT, WORK, ERP_EXTS  # noqa: E402


def find_erp_candidates(pile):
    """Files under the pile that look like the ERP record: .csv/.xlsx with 'erp' in the name."""
    found = []
    for path in sorted(pile.rglob("*")):
        if path.is_file() and not path.is_symlink():
            if path.suffix.lower().lstrip(".") in ERP_EXTS and "erp" in path.name.lower():
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


def main():
    parser = argparse.ArgumentParser(description="Preflight checks for the DCG intake kit.")
    parser.add_argument("--pile", help="folder holding the contract files and the ERP record")
    parser.add_argument("--erp", help="the ERP record, if its name does not contain 'erp'")
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

    # 5. mermaid.min.js
    if MERMAID_JS.is_file() and MERMAID_JS.stat().st_size > 1_000_000:
        ok(f"assets/mermaid.min.js present ({MERMAID_JS.stat().st_size // 1024} KB)")
    elif MERMAID_JS.is_file():
        fail(f"assets/mermaid.min.js is only {MERMAID_JS.stat().st_size} bytes: "
             "re-download the kit; the file should be over 1 MB")
    else:
        fail(f"assets/mermaid.min.js missing from {ASSETS}: re-download the kit")

    # 6. work/ and out/ writable
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
