---
name: match
description: Matches every document to an ERP account, writes the entity map, then runs sort.py to build the account folders. Usage /match [--force].
disable-model-invocation: true
---

# /match [--force]

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
1. Read `work/erp.json` (accounts, side, stream candidates), `inputs/our-entities.csv` if present,
   the `q2_*` fields of every `work/cards/<id>.json`, and the existing `inputs/entity-map.csv`
   (`name_as_printed,account,basis,confidence,decided_by,note`). Keep every existing row; rows with
   `decided_by` = `user` win. A name that already has a row is not re-decided unless `--force`.
2. For every company name without a row (their signing entities and group companies; skip our
   own entities, `none` and `not found`): decide `account` (an ERP row name spelled exactly, or
   `_not-on-the-list`, or `_not-sure` with the candidate in `note`), `basis`, `confidence`, `note`.
   For `known group` the note says what you know.
3. Decide the streams: an ERP row that is a stream of another gets a row with `name_as_printed` =
   the stream row, `account` = the main row, basis `same name`. Say which rows you treated as one.
4. Append your new rows with `decided_by` = `claude`. Never change a `user` row. With `--force`,
   replace the `claude` rows you re-decided.
5. Run `python scripts/sort.py` (with `--force` if it was typed). Put its output in your reply:
   documents per account, holding folders, streams.
6. List the names that need the user's decision (no row, or confidence `not sure`). Say: edit
   `inputs/entity-map.csv`, set `decided_by` = `user`, run `/match` again; nothing is asked twice.
7. Stop after matching. `/judge` is an explicit analysis step, normally orchestrated by `/deep-dive`.
