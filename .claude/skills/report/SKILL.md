---
name: report
description: Rebuilds every account's folders, note, list and diagram, then the corpus table, ACCOUNTS.csv and the index. Usage /report.
disable-model-invocation: true
---

# /report

Run from the kit root, after `/judge`.

1. Run `python scripts/place.py --all`. It rebuilds every account that has a placements file,
   then writes `out/<side>/CORPUS.csv`, `out/<side>/ACCOUNTS.csv`, `out/INDEX.md` and
   `out/INDEX.html`, and copies `assets/mermaid.min.js` to `out/assets/`. Put in your reply what
   it says it wrote, and every warning.
2. Print the content of `out/INDEX.md`: accounts, governing docs, counts per folder, open
   questions; the files not readable by the kit; the sort log summary (holding folders and the
   names in them, names needing a decision, streams).
3. Remind the reviewer flow:
   - open `out/INDEX.html`, then each account's `README.md`, `documents.csv` and
     `position.html` (it works offline);
   - legal and sales filter `out/<side>/CORPUS.csv`, or an account's `documents.csv`, in a
     spreadsheet and fill the reviewer columns `legal_agrees`, `sales_agrees`, `correct_folder`,
     `comment`;
   - agreed corrections go into `inputs/corrections.csv` (`doc_id,field,value,reason`); then run
     `/judge` again and `/report` again;
   - never edit anything under `out/` or `work/` by hand.
4. After stage 2 only: if `work/forms/` exists and `scripts/graph.py` exists, also run
   `python scripts/graph.py --all` and say so. Otherwise say nothing about stage 2.
