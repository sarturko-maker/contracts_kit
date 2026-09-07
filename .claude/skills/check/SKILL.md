---
name: check
description: Preflight for the DCG intake kit. Checks Python, pypdf, Poppler PDF-to-JPEG rendering, the pile, the ERP record, bundled Mermaid and write access. Usage /check [pile path].
---

# /check [pile path]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

Run from the kit root. `$ARGUMENTS` is the pile path (the folder holding the contract files
and the ERP record); it may be empty.

1. Run the preflight:
   - with a path: `python scripts/check.py --pile "<pile path>"`
   - with no path: `python scripts/check.py`
   If the user also typed `--erp <file>` (to name the ERP record), pass it through unchanged.
2. Put every line the script printed in your reply, as printed: `ok  ...`, `skip ...`, `FAIL ...`.
3. If any line starts with `FAIL`: tell the user what to fix (the line says how) and stop. Run
   nothing else; do not go on to `/prepare`.
4. If every line is `ok` or `skip`: say so and say what to run next: `/prepare <pile path>`.
   Without a pile path the pile and ERP checks were skipped; `/prepare` still needs the path.

Poppler is an external program, installed separately from `requirements.txt`; follow the script's
platform-specific fix and README setup. Its probe renders an invented one-page PDF in a temporary
directory, without reading contracts or making model/network calls. A version check alone is not
enough: the installed `pdftoppm` must support JPEG output. After installation or a PATH change,
restart the terminal and Claude Code before retrying. If the probe passes but Claude's PDF Read
tool still fails, report that separate tool error and stop; do not omit required image reads.
Mermaid is already bundled in `assets/mermaid.min.js`; do not install it through npm or pip.
