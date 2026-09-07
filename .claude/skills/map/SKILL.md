---
name: map
description: Proposes a DCG family per tree and generates stage 2 graph outputs. Usage /map all | "<account>" [--force].
---

# /map all | "<account>" [--force]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

1. Run `python scripts/validate_forms.py --all`; stop on any failure. Read `work/erp.json`,
   the entity map, placements and sort log. Skip stream rows mapped into another ERP account.
2. Select all remaining ERP accounts with extracted forms, or the exact account requested.
   Report accounts without forms. Preserve stage 1 tree numbers; a missing form is a scope gap,
   never permission to silently invent its answers. Skip existing `work/trees/<safe_account>.json`
   unless `--force`; report skips. After changed forms/placements, use `--force` to refresh proposals.
3. Spawn one `mapper` per account, batches of up to five, passing the exact ERP name. Wait for
   each batch. Retry one failed mapper once with its error; never edit its proposal or gaps.
4. Print each account's three-line return and any failures. Run `python scripts/graph.py --all`
   to merge successful source proposals. Say what to run next: `/report --graph`; review `TREES.md`,
   `out/FORM-HEALTH.md` and `out/DIDNT-FIT.md`. The user decides changes to the standard.
