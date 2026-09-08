---
name: prepare
description: Inventories contracts, reads ERP CSV/XLSX and registers optional Review_Table CSV/XLSX separately. Usage /prepare <pile path> [--erp <file>] [--review-table <file>].
---

# /prepare <pile path> [--erp <file>] [--review-table <file>]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name. On Windows,
use `py` if that is the working launcher. Reuse the command that passed /check.

Run from the kit root. `$ARGUMENTS` is the pile path, optionally followed by `--erp <file>`
(name the ERP record when its file name does not contain "erp", or when several files do).
Pass `--review-table "<file>"` when given. Otherwise a single file named Review_Table.csv or
Review_Table.xlsx is discovered automatically. Multiple matches stop preparation. It is recorded
in `work/review-source.json` and the preparation log, and never numbered/read as a contract.

1. Run `python scripts/prepare.py "<pile path>"`, adding `--erp "<file>"` if given. If it stops
   (no ERP record found, or more than one candidate), put its message in your reply and stop.
2. Read `work/erp.json`. If `confirmed` is true, tell the user the account column and the side
   it found and continue. If it is false: show the columns and the guesses, ask the user which
   column holds the account name and which side this run is for (customers or suppliers), then
   run `python scripts/prepare.py "<pile path>" --account-column "<column>" --side <customers|suppliers>`
   (with `--erp` and `--review-table` again if given). Files already done are skipped; that is expected.
3. Put in your reply what the script printed: the inventory table (id | file | type | pages |
   scanned | note); the totals: files by type, readable and not readable, total pages, scanned
   pages on their own line (a page read as a picture costs several times a page read as text),
   docx files with tracked changes; the accounts and the stream candidates from the ERP record.
4. List every file not readable by the kit, with its path. Nothing is skipped silently.
5. If a Review_Table is registered, say `/analyse` will consume it and ERP without full document
   readers. Otherwise say `/analyse` for the deliverable or `/sort` for optional cheap triage.
   Stop after preparation unless a parent command explicitly includes the next stage.

Never edit the pile, `work/inventory.csv` or `work/text/`. To redo every file, add `--force`.
