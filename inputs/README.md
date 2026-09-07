# inputs/

What lands here on the enterprise side, and what never gets committed.

| File | Written by | Committed? |
| --- | --- | --- |
| `erp-record.csv` | `prepare.py`, a copy of the ERP record with all its columns | never |
| `entity-map.csv` | `/sort` (rows with `decided_by = claude`) and you (rows with `decided_by = user`, which win) | never |
| `corrections.csv` | you, after legal and sales have reviewed `out/` | never |
| `our-entities.csv` | you, optional: our current and old entity names, one per row | never |
| `*.example.csv` | the kit, to show the columns | yes |

`.gitignore` excludes every `.csv` here except the examples. The pile itself stays where you
dropped it; the kit only reads it.

## entity-map.csv

`name_as_printed, account, basis, confidence, decided_by, note`

One row per company name found in a document, mapped to an ERP account name (spelled exactly as
the ERP row). `basis` is `same name`, `in the document` or `known group`; `confidence` is `sure`,
`fairly sure` or `not sure`. To fix a match, edit the row, set `decided_by` to `user`, and run
`/sort` again. To send a name to a holding folder, set `account` to `_not-on-the-list`. A row
whose `name_as_printed` is itself an ERP row name and whose `account` is another ERP row says the
first row is a stream of the second (its folder holds only a README).

## corrections.csv

`doc_id, field, value, reason`

One row per fact legal or sales have corrected. `field` is a sort-card key (for example
`q4_status`, `q3_signed`) or a placement column (`folder`, `tree`). Corrections are applied by
the judge and by `place.py` on the next `/judge`; the cards themselves are never edited.

## our-entities.csv

`name, status, note` — our legal entities, current and old names (`status` = `current` or
`former`). Used by `/sort` to tell our side from theirs.
