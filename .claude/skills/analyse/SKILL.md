---
name: analyse
description: "Full reading, account matching, status judgments and the position notes with diagrams: the minimum deliverable. Usage /analyse [all | account \"<name>\"]."
disable-model-invocation: true
---

# /analyse [all | account "<name>"]

Commands are written `python`; use `python3` where that is the installed name.

This is the stage that produces the deliverable: documents in status folders, one short CSV and
Markdown per account, and the account diagram beside them. It is expensive per document, so it
runs only when the user types it. It never runs `/extract`, `/map` or the graph export.

`/sort` is optional triage and is **not** required first; `/prepare` is required.
`$ARGUMENTS` is empty or `all` (every readable document in the prepared pile) or
`account "<name>"` (one ERP account, spelled exactly as its row).

1. Require `/prepare`: `work/inventory.csv` and `work/erp.json` must both exist. If either is
   missing, say to run `/check <pile>` and `/prepare <pile>` and stop. With `account "<name>"`,
   the account must be an ERP row and `work/logs/sort.csv` must already list its documents (that
   needs an earlier `/sort` or `/analyse`); otherwise say so and stop.

2. Invoke `/read all`, or `/read account "<name>"` for one account. Readers are spawned by that
   skill; the prompt sentence stays exactly `Fill the sort card for doc <id>.` Never fill or
   edit a card yourself.

3. Run `python scripts/check_cards.py --all` (or with the ids just read). Print every warning it
   prints. For each card flagged `question 2 may be reversed`, run that one reader again with
   `/read <id> --force`, quoting the warning in the prompt and nothing more: never tell the
   reader which entity is ours or what the answer should be. One retry per card; if the second
   card is still flagged, leave it, say so, and carry the warning into the report. Other
   warnings (evidence longer than forty words, paraphrase suspected) are reported, not retried.

4. Invoke `/match --force`. Rows with `decided_by` = `user` are preserved untouched; `--force`
   only re-decides the `claude` rows from the full cards. Put the names that still need the
   user's decision in your reply.

5. Invoke `/judge all`, or `/judge "<account>"` for the single account. Accounts with no
   documents get no judge; say which were skipped.

6. Run `python scripts/place.py --all --visuals`. Visuals are the default at this stage: the
   account folders, `documents.csv`, the position notes, `CORPUS.csv`, `ACCOUNTS.csv`,
   `INDEX.md`, and `position.html`/`position.mmd` plus `INDEX.html` are written here.

7. Print, in the reply: each account's three judge lines under its name; the counts from
   `INDEX.md` (documents per status folder, per account, holding folders, anything unresolved);
   and every warning `place.py` printed. Documents in holding folders keep their card facts and
   remain unassessed until the user maps the name; list them under what needs a decision.

8. Cost report. As each agent returns, append one ledger row per spawned agent — including
   every retry as its own row:

   ```
   python scripts/cost.py --append --stage analyse --role reader --model sonnet \
       --target 017 --attempt 1 --outcome ok --tokens 28000 --duration-ms 41000 --units-read 12
   ```

   `--role` is `reader` or `judge`, `--model` the role's configured model (`sonnet`, `opus`),
   `--target` the doc id for a reader and the account name for a judge, `--attempt` 1 for the
   first try and 2 for a retry, `--outcome` `ok` or `failed`, `--tokens` and `--duration-ms` the
   figures the completion reported (`unknown` if the harness did not report them), `--units-read`
   the read units the agent's return or record gives, otherwise the document's page count from
   `work/inventory.csv`, or `unknown`.

   Then run `python scripts/cost.py --stage analyse` and put its table in the reply, followed by
   exactly this line: "main session tokens are not visible to the model; type `/cost` for this
   session's own usage and add it to the stage total". Tell the user to run `/cost` now, while
   the stage is fresh, and to note all four figures (input, output, cache write, cache read).

9. Stop. Say that `/deep-dive` is the optional next stage (fixed forms, DCG families and the
   graph export) and that `/visualise --analysis` re-renders these diagrams for free after
   corrections. Never start either automatically.
