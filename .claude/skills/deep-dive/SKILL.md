---
name: deep-dive
description: Fills the fixed stage 2 forms, proposes DCG families and exports the graph from completed cards and judgments. Usage /deep-dive [--topics all|off|names] [--force].
disable-model-invocation: true
---

# /deep-dive [--topics all|off|names] [--force]

Commands are written `python`; use `python3` where that is the installed name.

This is the deepest and most expensive stage. Run it only when the user invokes it; it never
follows automatically from `/sort`, `/analyse` or `/visualise`. It never rereads cards and never
re-judges: it requires `/analyse` to have finished and stops if that work is missing or stale.

Table-route limitation: Review_Table analysis does not create native sort cards. If
`work/review-table/active.json` exists and the native cards below are absent, explain that this
version's /deep-dive requires a separate source-based stage-2 workflow and stop. Do not tell the
user to repeat table /analyse to create cards; it will never do that. Do not start source readers
or manufacture cards from the table to satisfy the prerequisite.

1. Prerequisite check, in this order. Read `work/inventory.csv`, `work/cards/`,
   `work/placements/`, `work/logs/sort.csv` and `work/erp.json`.
   - every readable non-ERP inventory row has both `work/cards/<id>.json` and `<id>.md`;
   - every account that has documents has placements. The accounts that have documents are the
     ones printed by `python scripts/place.py --accounts-with-documents`; each needs
     `work/placements/<safe folder name>.csv` and `.md`. Accounts with no documents need none.
   - `work/logs/sort.csv` is not older than the newest card it depends on (a card written after
     the sort log means matching has not seen it).
   If anything is missing or stale, list exactly what (ids without cards, accounts without
   placements, a sort log older than the cards), say to run `/analyse` (or
   `/analyse account "<name>"` for one account), and **stop**. Do not run a reader, a matcher or
   a judge here. Holding documents have cards but no account and no placement; that is expected
   and is not a missing prerequisite.

2. Print the selected ids: every readable non-ERP row, holding documents included, with the
   count of existing forms that can be reused.

3. Invoke `/extract` for every selected id, writing the argument in full:

   ```
   /extract all --topics freight pricing payment_terms termination_for_convenience
   ```

   Those four are the default. `--topics off` opts out of them; explicit names select a subset,
   using the names in `stage2/topics.md` and no others. If existing forms lack the requested
   topics, replace those forms with `--force`; reuse compatible ones. A user `--force` rereads
   every selected form. Topics on roughly doubles extractor cost.

4. Validate: `python scripts/validate_forms.py --all`. An invalid form blocks mapping; report it
   rather than repairing it here.

5. Invoke `/map all --force`. Mappers consume the current forms and placements only. Missing
   forms or a failed judgment are reported, never worked around with a stale map.

6. Invoke `/report --graph` to write the analysis CSVs, Markdown and `out/graph/`. It keeps the
   `/analyse` diagrams current when they exist and builds none otherwise; `/visualise --analysis`
   is the separate free rendering command.

7. Summarise: families proposed per account, standard gaps (`out/DIDNT-FIT.md`), form health
   (`out/FORM-HEALTH.md`), node and edge counts, and every open question the mappers returned.
   The form and graph are an index: consult the full relevant instrument and its amendments and
   schedules before answering a substantive question.

8. Cost report. As each agent returns, append one ledger row per spawned agent — including
   every retry as its own row:

   ```
   python scripts/cost.py --append --stage deep-dive --role extractor --model sonnet \
       --target 017 --attempt 1 --outcome ok --tokens 62000 --duration-ms 90000 --units-read 42
   ```

   `--role` is `extractor` or `mapper`, `--model` the role's configured model (`sonnet`,
   `opus`), `--target` the doc id for an extractor and the account name for a mapper,
   `--attempt` 1 for the first try and 2 for a retry, `--outcome` `ok` or `failed`, `--tokens`
   and `--duration-ms` the figures the completion reported (`unknown` if the harness did not
   report them), `--units-read` the read units the agent's return or record gives (for an
   extractor, the pages its form's evidence cites), otherwise the document's page count from
   `work/inventory.csv`, or `unknown`.

   Then run `python scripts/cost.py --stage deep-dive` and put its table in the reply, followed
   by exactly this line: "main session tokens are not visible to the model; type `/cost` for this
   session's own usage and add it to the stage total". Tell the user to run `/cost` now, while
   the stage is fresh, and to note all four figures (input, output, cache write, cache read).

9. Stop. Do not run `/eval`. Mention `/visualise --analysis` as the free re-render.
