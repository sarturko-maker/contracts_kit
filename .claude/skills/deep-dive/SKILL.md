---
name: deep-dive
description: Explicitly runs full contract reading, status judgments, fixed forms and DCG mapping for the prepared pile. Usage /deep-dive [--topics all|off|names] [--force].
disable-model-invocation: true
---

# /deep-dive [--topics all|off|names] [--force]

This is the expensive stage. Run only when the user invokes it; it never follows automatically
from `/sort` or `/visualise`. It covers the entire prepared pile, including holding files.

1. Require `/prepare` and an ERP record. Select all readable non-ERP ids. Print selected ids
   and counts of existing full cards/forms that can be reused.
2. Run `/read` for the selected ids (`--force` only if supplied). Cheap `work/filing/` records
   never substitute for the fixed sort card. Full readers inspect bodies, separately lived
   parts, scans and signature pages under the existing reading rules.
3. Run `/match --force` from full cards to revisit preliminary model matches while preserving
   user entity decisions, then `/judge all`. Report
   incomplete accounts instead of judging from filing records.
4. Run `/extract` for every selected readable id. Default topics are all four existing topics:
   freight, pricing, payment_terms, termination_for_convenience. `--topics off` opts out;
   explicit names select a subset. If existing forms lack the requested topics, replace those
   forms with `--force`; reuse compatible forms. User `--force` rereads all selected forms too.
   Never invent additional topics.
5. Validate all forms; invalid forms block mapping. Run `/map all --force` after changed forms
   or judgments (mappers consume current forms only). Missing forms or failed judgments must
   be resolved before exporting a complete analysis; report the failure rather than reuse stale maps.
6. Run `/report --graph` to write analysis CSVs/Markdown and graph outputs. No diagram work is
   implied; `/visualise --analysis` is the separate optional rendering command.
7. Summarise status, execution/version uncertainties, missing documents, family proposals and
   standard gaps. The fixed form/graph is an index: consult the full relevant instrument and
   linked amendments/schedules when answering a substantive question. Stop; do not run `/eval`.
