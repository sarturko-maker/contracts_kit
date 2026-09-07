---
name: read
description: Spawns one reader sub-agent per document to fill the sort cards. Usage /read all | <ids> | account "<name>" [--force].
disable-model-invocation: true
---

# /read all | <ids> | account "<name>" [--force]

Run from the kit root. `$ARGUMENTS` says which documents. Build the list of doc ids first:

- `all`: every row of `work/inventory.csv` with `readable` = `yes`, except the `erp` row.
- `<ids>`: the numbers typed (`003 007 012`; pad to three digits).
- `account "<name>"`: the `doc_id` of every row in `work/logs/sort.csv` whose `account` is that
  name (needs an earlier `/sort`).

Drop every id that already has both `work/cards/<id>.json` and `.md` unless `--force` was typed; count those as
skipped. Print the list before starting. Then, in batches of five:

1. Spawn the `reader` sub-agent once per id with the Agent tool (`subagent_type: "reader"`),
   prompt exactly `Fill the sort card for doc <id>.`. Run the five of a batch in parallel and
   wait for all of them before starting the next batch.
2. Append each reader's return line to `work/logs/read.log`, one line per document.
3. If a reader returns no usable line, or `work/cards/<id>.json` is missing afterwards, run that
   reader once more. If it fails again, log `doc <id> | FAILED | <what came back>` and carry on.

Never fill a card yourself; never edit a card a reader wrote.

When every batch is done, print the counts: cards written, cards skipped (already present),
failures (with their ids). Say what to run next: `/sort`.
