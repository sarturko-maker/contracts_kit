---
name: prepare
description: Inventories the pile, copies the ERP record, numbers every file and pulls the native text. Usage /prepare <pile path> [--erp <file>].
disable-model-invocation: true
---

# /prepare <pile path> [--erp <file>]

Run from the kit root. `$ARGUMENTS` is the pile path, optionally followed by `--erp <file>`
(name the ERP record when its file name does not contain "erp", or when several files do).

1. Run `python scripts/prepare.py "<pile path>"`, adding `--erp "<file>"` if given. If it stops
   (no ERP record found, or more than one candidate), put its message in your reply and stop.
2. Read `work/erp.json`. If `confirmed` is true, tell the user the account column and the side
   it found and continue. If it is false: show the columns and the guesses, ask the user which
   column holds the account name and which side this run is for (customers or suppliers), then
   run `python scripts/prepare.py "<pile path>" --account-column "<column>" --side <customers|suppliers>`
   (with `--erp` again if it was given). Files already done are skipped; that is expected.
3. Put in your reply what the script printed: the inventory table (id | file | type | pages |
   scanned | note); the totals: files by type, readable and not readable, total pages, scanned
   pages on their own line (a page read as a picture costs several times a page read as text),
   docx files with tracked changes; the accounts and the stream candidates from the ERP record.
4. List every file not readable by the kit, with its path. Nothing is skipped silently.
5. Say what to run next: `/sort`. Stop after preparation unless a parent `/sort` or `/deep-dive` command explicitly includes the next stage.

Never edit the pile, `work/inventory.csv` or `work/text/`. To redo every file, add `--force`.
