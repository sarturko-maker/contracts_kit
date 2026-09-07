---
name: judge
description: Spawns one judge sub-agent per account to build trees, placements and the position note. Usage /judge all | "<account>".
disable-model-invocation: true
---

# /judge all | "<account>"

Run from the kit root. Needs `/read` and `/match` done: full cards in `work/cards/`, rows in
`work/logs/sort.csv`. Cheap `/sort` filing records are insufficient. Require a full card for
every readable document assigned to an account; report incomplete accounts instead of judging
them from filing records.

1. Read `work/erp.json` for `side` and the `accounts` list. Read `inputs/entity-map.csv`: a row
   whose `name_as_printed` is an ERP row name and whose `account` is a different ERP row name
   marks a stream. Streams are not judged; their documents sit under the main row.
2. Accounts to judge: `all` = every account that is not a stream; otherwise the one account
   named in `$ARGUMENTS`, spelled exactly as its ERP row.
3. Spawn the `judge` sub-agent once per account with the Agent tool (`subagent_type: "judge"`),
   prompt exactly `Judge the account "<name>" (side: <side>).`. Up to five in parallel; wait for
   a batch to finish before starting the next.
4. Each judge returns three lines: `governing: ...`, `counts: ...`, `open questions: ...`. Print
   them under the account's name. If a judge returns anything else, run it once more, then
   report the failure. Never write placements or note prose yourself.
5. Say what to run next: `/report`.
