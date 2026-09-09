---
name: prepare
description: Inventories contracts, reads ERP and separately registers Review_Table and Review_Table_Light. Usage /prepare <pile path> [--erp <file>] [--review-table <file>] [--review-table-light <file>].
---

# /prepare <pile path> [--erp <file>] [--review-table <file>] [--review-table-light <file>]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name. On Windows,
use `py` if that is the working launcher. Reuse the command that passed /check.

Run from the kit root. `$ARGUMENTS` is the pile path, optionally followed by `--erp <file>`
(name the ERP record when its file name does not contain "erp", or when several files do).
Pass `--review-table "<file>"` when given. Otherwise a single file named Review_Table.csv or
Review_Table.xlsx is discovered automatically. Multiple matches stop preparation. It is recorded
in `work/review-source.json` and the preparation log, and never numbered/read as a contract.
Pass --review-table-light when supplied. A reserved Review_Table_Light.csv/xlsx is discovered
independently and registered in work/review-light-source.json. Both exports are excluded from
numbering, including when both exist in the same corpus. Never substitute one for the other.

1. Run `python scripts/prepare.py "<pile path>"`, adding `--erp "<file>"` if given. If it stops
   (no ERP record found, or more than one candidate), put its message in your reply and stop.
2. Read `work/erp.json`. If `confirmed` is true, tell the user the account column and the side
   it found and continue. If it is false: show the columns and the guesses, ask the user which
   column holds the account name and which side this run is for (customers or suppliers), then
   run `python scripts/prepare.py "<pile path>" --account-column "<column>" --side <customers|suppliers>`
   (with `--erp`, `--review-table` and `--review-table-light` again if given). Files already done are skipped; that is expected.
3. Put in your reply what the script printed: the inventory table (id | file | type | pages |
   scanned | note); the totals: files by type, readable and not readable, total pages, scanned
   pages on their own line (a page read as a picture costs several times a page read as text),
   docx files with tracked changes; the accounts and the stream candidates from the ERP record.
4. List every file not readable by the kit, with its path. Nothing is skipped silently.
5. If Review_Table_Light is registered, say `/sort` uses it for cheap filing with no visuals.
   If a full Review_Table is registered, say `/analyse` optionally uses that separate export
   for governing analysis and visuals. If neither exists, /analyse can use the native full-source
   route; /sort requires the light export and never falls back to source filers.
   Stop after preparation unless a parent command explicitly includes the next stage.

Never edit the pile, `work/inventory.csv` or `work/text/`. To redo every file, add `--force`.
