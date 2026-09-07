---
name: match
description: Matches documents to ERP accounts, writes the entity map, then replays filing. Usage /match [account "<name>"] [--force].
---

# /match [account "<name>"] [--force]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

Run from the kit root. You do the matching; `scripts/sort.py` only replays what you write to
`inputs/entity-map.csv`. These are the rules (`stage1/sorting-rules.md`, section A), followed
word for word:

> You are matching documents to the accounts in the ERP record. You have the account names, the
> company names from every sort card, and our own entity names (`inputs/our-entities.csv`, if
> present). You know how company groups, brands and old names fit together; use that. Two rules
> only:
>
> 1. The ERP record is the only source of folder names. One folder per account row, spelled
>    exactly as the row, under `out/<side>/`. Never create a folder from a name you found in a
>    document. Rows that are streams of one account share the main row's folder unless a
>    document names the stream; say which rows you treated as one.
> 2. Every match gets a basis and a confidence, written down. Basis is one of: `same name`,
>    `in the document` (the document itself says "a subsidiary of", "formerly known as", lists
>    the group companies, or shares a registered address or number with a company already
>    matched), or `known group` (you know the company belongs to the account's group but nothing
>    in the document says so; say what you know). Confidence is sure / fairly sure / not sure.
>    `known group` is never better than fairly sure, because the graph will need that link
>    evidenced or confirmed by a person.
>
> A document naming companies from more than one account is copied into every matching folder
> and marked shared. A document whose companies match no account goes to `_not-on-the-list`; one
> where you have a candidate but are not sure goes to `_not-sure`; one with no readable company
> name goes to `_no-name-found`. Inside the holding folders, group by the company name found, so
> the user decides once per name, not once per document. Where the file sat in the old
> repository is a clue, not a rule; if it disagrees with you, say so.
>
> Copy, never move. Write one line per document to `work/logs/sort.csv`: number, original path,
> company names found, account chosen, basis, confidence, note. Append every new company-name to
> account decision to `inputs/entity-map.csv` with `decided_by` = `claude`. The user edits that
> file (their rows say `decided_by` = `user` and win); `sort.py` replays it, so a re-run after
> edits does not ask you again. Tell the user which names need their decision.

Steps:
With `account "<name>"`, first capture that account's doc ids from `work/logs/sort.csv`.
Require a full card for every selected id; stop if any is missing. Read other existing cards
only as matching context. Re-decide only names found in the selected cards, preserving all
other entity-map rows. Do not read other source documents or start readers for other accounts.

1. Read `work/erp.json` (accounts, side, stream candidates), `inputs/our-entities.csv` if present,
   the `q2_*` fields of every `work/cards/<id>.json`, and the existing `inputs/entity-map.csv`
   (`name_as_printed,account,basis,confidence,decided_by,note`). Keep every existing row; rows with
   `decided_by` = `user` win. A name that already has a row is not re-decided unless `--force`.
   Also read, on every card, the `q6_*`, `q7_*` and `q10_oddities` fields and the `original_path`
   folder of that document's `work/inventory.csv` row. Names travel between documents: a card
   saying "formerly known as", a name-change letter naming both the old and the new company, a
   registered number shared with a company you have already matched, or a group list in a
   schedule, all count as `in the document` for the OTHER documents that name the same company,
   not only for the one you read it in. Carry those links across the whole pile before you decide
   any name, and say in the note which document supplied the link (`doc 012 names Colverne as the
   former name`). The folder a file sat in in the old repository ("Ardleigh (ex Colverne)") is a
   clue, not a rule; if it disagrees with you, say so. One company is one name group: do not open
   a second group for the same company written differently (`Services Limited` / `Svcs Ltd`,
   `plc` / `PLC`, `Co` / `Company`, `&` / `and`), so the user decides once.
2. For every company name without a row (their signing entities and group companies; skip our
   own entities, `none` and `not found`): decide `account` (an ERP row name spelled exactly, or
   `_not-on-the-list`, or `_not-sure` with the candidate in `note`), `basis`, `confidence`, `note`.
   For `known group` the note says what you know.
3. Decide the streams using rule A1's exception: if a document explicitly names the stream,
   map that printed stream name to its own ERP row. Otherwise record `name_as_printed` = the
   stream row, `account` = the main row, basis `same name`. Do not change a user-confirmed
   mapping. The scripts enforce the explicit-name exception for automatic mappings too.
   Say which rows you treated as one and which named streams retain their own folders.
4. Append your new rows with `decided_by` = `claude`. Never change a `user` row. With `--force`,
   replace the `claude` rows you re-decided.
5. Run `python scripts/sort.py` for all, or `python scripts/sort.py --account "<name>"` for the
   selected account (with `--force` if it was typed). Never drop `--account` on a scoped run.
   Put its output in your reply:
   documents per account, holding folders, streams.
6. List the names that need the user's decision (no row, or confidence `not sure`). Say: edit
   `inputs/entity-map.csv`, set `decided_by` = `user`, run `/match` again; nothing is asked twice.
7. Stop after matching. `/judge` is an explicit analysis step, normally orchestrated by `/analyse`.
