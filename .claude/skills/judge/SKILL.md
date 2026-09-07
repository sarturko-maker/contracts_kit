---
name: judge
description: Spawns one judge sub-agent per account to build trees, placements and the position note. Usage /judge all | "<account>".
---

# /judge all | "<account>"

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

Run from the kit root. Needs `/read` and `/match` done: full cards in `work/cards/`, rows in
`work/logs/sort.csv`. Cheap `/sort` filing records are insufficient. Require a full card for
every readable document assigned to an account; report incomplete accounts instead of judging
them from filing records.

1. Read `work/erp.json` for `side` and the `accounts` list. Read `inputs/entity-map.csv`: a row
   whose `name_as_printed` is an ERP row name and whose `account` is a different ERP row name
   marks a stream. Streams are not judged; their documents sit under the main row.
2. Accounts to judge: `all` = the accounts printed by
   `python scripts/place.py --accounts-with-documents`, which are the non-stream ERP rows that
   actually have documents. An account with no documents gets **no** judge: `place.py` writes its
   empty README and diagram itself, and an Opus call on nothing is wasted money. Name in your
   reply the ERP accounts you skipped for having no documents. Otherwise judge the one account
   named in `$ARGUMENTS`, spelled exactly as its ERP row; if that account has no documents, say
   so and stop.
3. Spawn the `judge` sub-agent once per account with the Agent tool (`subagent_type: "judge"`),
   prompt exactly `Judge the account "<name>" (side: <side>).`. Up to five in parallel; wait for
   a batch to finish before starting the next.
4. Each judge returns three lines: `governing: ...`, `counts: ...`, `open questions: ...`. Print
   them under the account's name. Judges do not write the log: you append one line per account to
   `work/logs/judge.log` as `<account> | <governing line> | <counts line> | <open questions line>`,
   after the batch returns, exactly as `/read` and `/extract` log their agents' returns. The
   per-document detail is in `work/placements/<safe folder name>.csv`, which the judge owns.
   If a judge returns anything else, run it once more, then report the failure. Never write
   placements or note prose yourself.
5. Say what to run next: `/report`, or `python scripts/place.py --all --visuals` when `/analyse`
   is driving.
