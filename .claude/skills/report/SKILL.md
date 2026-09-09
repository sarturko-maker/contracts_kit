---
name: report
description: Rebuilds existing CSV and Markdown reports; graph export requires explicit --graph. Usage /report [--graph] [top].
---

# /report [--graph] [top]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

Run from the kit root. This command runs scripts only, never reading/judging/extraction agents.

1. Without `--graph`, inspect the current `out/<side>/CORPUS.csv` header. If it contains
   `read_status`, run `python scripts/filing.py --report` to refresh the cheap filing outputs.
   Otherwise, after completed judgments, run `python scripts/place.py --all --visuals` when
   `out/INDEX.html` exists (the `/analyse` diagrams are re-rendered from the same placements;
   a plain `--all` would delete them) and `python scripts/place.py --all` when it does not.
   Missing prerequisites are reported; do not perform them automatically. With `top` (after
   `/analyse top`), use `python scripts/place.py --top --visuals` in place of `--all`: it
   rebuilds the ERP_Top accounts and the index and leaves every other account filing only.
2. Only with explicit `--graph`, run `place.py --all` (or `--top` with `top`) with the same
   `--visuals` rule, then `python scripts/graph.py --all`. Report missing decisions or invalid forms; never fill or
   repair them here. Existing forms alone NEVER authorise graph export.
3. Report written files and every warning, plus the counts and unresolved items in INDEX.md.
   Review identity matches in inputs/entity-map.csv; after analysis, reviewers can filter
   CORPUS.csv and record agreed changes in inputs/corrections.csv. Never hand-edit generated
   work or out files. Reapply corrections through the relevant explicit component commands.
4. Stop. `/visualise` optionally adds filing diagrams; `/visualise --analysis` renders completed
   relationship analysis. Neither is run automatically by this command.
