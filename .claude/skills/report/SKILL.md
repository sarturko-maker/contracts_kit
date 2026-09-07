---
name: report
description: Rebuilds existing CSV and Markdown reports; graph export requires explicit --graph. Usage /report [--graph].
disable-model-invocation: true
---

# /report [--graph]

Run from the kit root. This command runs scripts only, never reading/judging/extraction agents.

1. Without `--graph`, inspect the current `out/<side>/CORPUS.csv` header. If it contains
   `read_status`, run `python scripts/filing.py --report` to refresh the cheap filing outputs.
   Otherwise, after completed judgments, run `python scripts/place.py --all` for analysis
   CSVs and Markdown. Missing prerequisites are reported; do not perform them automatically.
2. Only with explicit `--graph`, run `python scripts/place.py --all`, then
   `python scripts/graph.py --all`. Report missing decisions or invalid forms; never fill or
   repair them here. Existing forms alone NEVER authorise graph export.
3. Report written files and every warning, plus the counts and unresolved items in INDEX.md.
   Review identity matches in inputs/entity-map.csv; after analysis, reviewers can filter
   CORPUS.csv and record agreed changes in inputs/corrections.csv. Never hand-edit generated
   work or out files. Reapply corrections through the relevant explicit component commands.
4. Stop. `/visualise` optionally adds filing diagrams; `/visualise --analysis` renders completed
   relationship analysis. Neither is run automatically by this command.
