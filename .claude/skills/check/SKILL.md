---
name: check
description: Preflight for the DCG intake kit. Checks Python, pypdf, the pile, the ERP record, mermaid.min.js and write access before anything else runs. Usage /check [pile path].
disable-model-invocation: true
---

# /check [pile path]

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
