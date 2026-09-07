---
name: sort
description: "Low-cost account filing only: folders, CSVs and Markdown explainers. Usage /sort [pile] [--force]."
disable-model-invocation: true
---

# /sort [pile] [--force]

This is the cheap first stage. It stops after filing. Do not call full readers, judges,
extractors, mappers, graph generation or visualisation. Do not determine what governs trade.

1. With a pile path, run `/check` and `/prepare` on it; otherwise use the prepared inventory.
   Resolve only required ERP column/side inputs. Native text extraction is local script work.
2. Run `python scripts/filing.py --pending` (add `--force` only if supplied). Show the document
   count and budget: at most three pages or twenty Word paragraphs per new filing read.
   Existing filing records or full cards are reused by default; unchanged files need no reread.
3. Spawn the `filer` role once per pending id, in batches of at most five. Pass only its id.
   Preserve the configured low-cost model; do not silently escalate to a full reader if an
   identity cannot be found. Retry a failed record once within the same total reading budget,
   then leave it in the needs-reading/holding output. Log one-line returns in `work/logs/filing.log`.
4. Run `python scripts/filing.py --names`. Match these names to ERP rows using the entity-map
   columns `name_as_printed,account,basis,confidence,decided_by,note`. Reuse existing decisions;
   user rows always win. ERP names alone name account folders. Basis is same name, in the
   document, or known group (never better than fairly sure). Do not claim documentary evidence
   from unread pages. Unknown groups go to _not-sure or _not-on-the-list with the reason.
   Preserve the shared-document and stream conventions in sorting-rules.md section A.
5. Append new decisions to inputs/entity-map.csv with decided_by=claude. Do not overwrite user
   rows. Record stream rows as an ERP-to-ERP map entry. Then run `python scripts/filing.py --report`.
   It writes files, per-folder documents.csv/README.md, global CORPUS.csv/ACCOUNTS.csv and INDEX.md.
   An older generated out/ report is retained under work/history; model source records survive.
6. Report counts, unresolved identities and source paths needing attention. Legal/live/signed
   status remains unassessed. Mention `/visualise` and `/deep-dive` as options, then STOP.
