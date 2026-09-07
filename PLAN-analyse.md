# Plan — the `/analyse` stage order and the live-test fixes

Draft written 7 September 2026 from the live test on the messy invented pile (33 files, six ERP
rows). Cheap `/sort` and `/visualise` are scored; `/deep-dive` results are still coming in and the
cost figures below will be updated when it reports. Nothing in this plan has been applied.

## 1. The decision

Three user commands, each stopping after its own stage, plus a free re-render:

| command | runs | models | delivers |
| --- | --- | --- | --- |
| `/sort <pile>` (optional triage) | check, prepare, filer per document, name matching, filing report | Haiku filers; main session matches | account folders with renamed copies, per-folder CSV and README, CORPUS/ACCOUNTS CSV, INDEX.md |
| `/analyse [all \| "account"]` | read all (or the account's documents), match, judge per account, report with visuals | Sonnet readers, Opus judges | status folders 1–6/unsure with renamed copies, position note per account, documents.csv, CORPUS.csv, position.html and INDEX.html |
| `/deep-dive [--topics ...] [--force]` | prerequisite check, extract, map, report with graph | Sonnet extractors, Opus mappers | forms, TREES.md, FORM-HEALTH, DIDNT-FIT, out/graph |
| `/visualise [--analysis]` | scripts only | none | re-render diagrams after corrections |

`/analyse` is the minimum deliverable: right folders, short CSV/Markdown, diagram in the folder.
`/sort` is not on the path to it; it is for large or unfamiliar piles where the user wants to fix
the entity map and drop junk before paying for a full read. `/deep-dive` never rereads cards or
judgments; it requires them and stops if they are missing or stale.

## 2. Changes to make, in order

### 2.1 Skill invocation (blocking defect, confirmed live)
Every kit skill carries `disable-model-invocation: true`, so the Skill tool refused `/sort`,
`/check`, `/prepare`, `/visualise`, `/deep-dive` and every component. The orchestrator only
progressed by reading each SKILL.md and following it by hand.
- Keep `disable-model-invocation: true` on the four user-typed stage skills: `sort`, `analyse`,
  `deep-dive`, `eval`. They are the cost gates.
- Remove it from the component skills: `check`, `prepare`, `read`, `match`, `judge`, `extract`,
  `map`, `report`, `visualise`. A stage skill then invokes its components through the Skill tool.
- CLAUDE.md keeps "never advance to the next stage unasked"; the stage skills are the only ones
  that chain, and they are user-only.

### 2.2 New `analyse` skill; `deep-dive` loses its first three steps
- `.claude/skills/analyse/SKILL.md`: require `/prepare`; optional `/sort` is not required. Steps:
  `/read all` (or `/read account "<name>"`), `/match --force` (preserving user rows), `/judge all`
  (or the one account), then `python scripts/place.py --all --visuals`. Print the judge lines and
  the index counts. Stop; mention `/deep-dive`.
- `.claude/skills/deep-dive/SKILL.md`: steps 1–3 become a prerequisite check: every readable
  document has a card, every non-stream account has placements, `work/logs/sort.csv` is newer
  than the cards it depends on. Missing → say to run `/analyse`, stop. Then extract, map,
  `/report --graph`, stop.
- README section 2 becomes `/analyse`; section 3 `/deep-dive`; `/visualise` moves to "Review and
  reruns" as the free re-render. The stage table in CLAUDE.md is rewritten to the four commands.
- `place.py --visuals` becomes the default for `/analyse`; `/report` without `--graph` keeps the
  current behaviour.

### 2.3 Renamed copies tied to the CSV (user request)
- Generated copies under `out/<side>/<account>/files/` (and status folders after `/analyse`) are
  named `<doc_id> <kind> <counterparty> <date>[ <status>].<ext>`, e.g.
  `017 master-agreement Sturmore-Rail-Group 2021-02-22.pdf`,
  `013 master-agreement Sturmore-Rail-Group 2016-07-18 not-live.pdf`,
  `002 duplicate-of-015.pdf`, `022 unidentified 42pp.pdf` when identity is unresolved.
- Source of the name: after `/sort`, the filing record (kind, first their-entity, date if found);
  after `/analyse`, the card (q1 kind, q2 first signing entity, q4 start) and the placement
  (folder, `duplicate of`). Names are built by `kit_common.filed_name()` and used by `sort.py`,
  `filing.py --report` and `place.py`; no agent writes a filename.
- Sanitising: ERP account name or first printed company, spaces → hyphens, path-hostile
  characters and trailing dots stripped, ASCII only, length capped at 120; Windows-safe.
- New column `filed_as` in `documents.csv` and `CORPUS.csv`; the account README lists
  "017 — 017 master-agreement …pdf — original: Customers/Sturmore Rail/MSA 2021/… .pdf".
- Originals and `work/files/<id>.<ext>` are untouched (CLAUDE.md copy-never-rename rule holds).

### 2.4 Defects from the live test
1. **filer `maxTurns: 12` too low.** 5 of 29 first attempts hit it on Haiku; the one unfiled
   document failed twice for that reason alone. Raise to 20 and tell the filer to write its
   record in one Write call before validating. The page budget is unchanged.
2. **Reader reversed question 2 on 3 of 29 cards** (our entity in the customer slot). The sort
   script then dropped those documents into `_no-name-found`. Add a card check in
   `kit_common.load_card` when `inputs/our-entities.csv` exists: if `q2_our_entity` is not one of
   ours, or a their-entity is one of ours, warn "q2 reversed?" and let `/read` retry that reader
   once with the warning. Add the same sentence to `reader.md` step for q2.
3. **Judge writes `work/placements/<account>.csv`; `place.py` reads `safe_folder_name(account)`.**
   Fix `judge.md` to the safe name (mapper.md already does this). Test with an account name
   containing `/` and a trailing space.
4. **Holding-folder documents are read but never judged.** Rule: the judge covers ERP accounts
   only; holding documents keep their card facts (kind, signed, dates) in CORPUS.csv with
   `folder = <holding>` and `status = unassessed (no account)`, and INDEX.md lists them under
   "Needs a decision" with the name to decide. When the user maps the name, `/analyse "account"`
   judges them. No invented account, no silent drop.
5. **Zero-document accounts** got an Opus judge (wasted call). `/judge all` skips accounts with
   no documents and `place.py` writes the empty-account README and diagram itself.
6. **Matching did not carry documentary links across documents** (name-change letter read and
   matched, but the renamed company's older agreement stayed in `_not-on-the-list`; the folder
   path clue was not mentioned). `/match` step 1 additionally reads q6/q7/q10 evidence for
   "formerly known as", "name change", registered numbers, and the `original_path` folder, and
   the sorting rules' "clue, not a rule; say so" sentence is repeated in the step.
7. **Holding groups split by abbreviation** (`Services Limited` vs `Svcs Ltd`). Extend
   `norm_name` with a small suffix/abbreviation table (Ltd/Limited, plc/PLC, Svcs/Services,
   Co/Company, &/and) so one company is one group and the user decides once.
8. **`python` vs `python3`.** Skills and README say "python (or python3 where that is the
   installed name)"; scripts are unchanged.
9. **Extractor `maxTurns: 40`** was hit by 3 of the first 15 with all four topics on; the
   retry-with-error path repaired every one. Keep 40, note in README that topics on roughly
   doubles extractor cost.
10. **`judge.log` concurrent appends.** Judges return their three lines; the main session
    appends the log, as `/read` and `/extract` already do.
11. **Stage-1 evidence rule not machine-checked.** Add the 40-word/verbatim check for card
    evidence fields to `load_card` (warn, not fail), mirroring `validate_forms.py`.

### 2.5 Documentation gaps carried from the brief review
- README: run the main session on Opus (or Fable where available) with effort high; `/check` as
  the setup step; scanned pages cost several times text pages; at forty files the questions
  matter more than the model; API PDF support in the scaling note.
- BUILD-NOTES: record the live test (this plan's appendix), the reconciliations Codex listed as
  deliberate (10/3 rows, no forbidden `party_to`, family on root instrument), and the acceptance
  criteria that take precedence.
- `requirements.txt`: drop the unused pypdfium2 line.

### 2.6 Tests
- `test_naming.py`: filed names from filing records and from cards; sanitising; collisions;
  `filed_as` in CSVs; originals untouched.
- `test_cards.py`: q2 reversal warning; 40-word evidence warning.
- `test_place.py`: placements path with hostile account names; zero-document account without a
  judge; holding documents in CORPUS with `unassessed (no account)`.
- `test_skills.py`: frontmatter flags (stage skills user-only, components invokable); every
  `python scripts/... --flag` in a skill exists in argparse (today a manual check).
- `test_match.py`: `norm_name` grouping table.
- Keep the 71 existing tests green.

### 2.7 Acceptance
- Add the messy pile as a second fixture: `eval/messy/pile/` (34 files, deterministic generator
  `make_messy_pile.py`) with `eval/messy/expected/` holding the answer key. It is invented and
  deliberately untidy; the tidy sample stays for the deterministic replay tests.
- Fresh handover on the changed README: `/sort`, then `/analyse`, then `/deep-dive`, each as a
  separate user command, with the kit's own agent roles at their configured models. Score with
  the key on the three results: execution and stopping, supported conclusions, cost per stage.
- Record the scores next to the 7 September figures in BUILD-NOTES.

### 2.8 Token report per stage (user request)
Each stage ends with a cost report the user can extrapolate from. Mechanism:
- Every subagent completion already returns its token count and duration to the main session.
  The stage skill appends one row per spawned agent to `work/logs/cost.csv`:
  `stage,role,model,target,attempt,outcome,tokens,duration_ms,pages_or_units_read`. Pages read
  come from the filing record (`pages_read`), the card (q9) or the form's evidence citations.
- `python scripts/cost.py [--stage sort|analyse|deep-dive] [--extrapolate N]` reads that file
  and prints, per stage and per role: agents, retries, total tokens, tokens per document,
  tokens per page, wall clock; then the stage total. With `--extrapolate N` it scales the per-
  document figures to N documents at the same mix of roles and retry rate, and shows the
  per-page figure separately so a pile with longer documents can be scaled by pages instead.
- The stage skill's last step is: run `cost.py --stage <this stage>` and print the table in the
  reply, followed by one line: "main session tokens are not visible to the model; type `/cost`
  for this session's own usage and add it to the stage total". That keeps the report honest
  about the orchestrator's share, which was about a third of the cheap stage in the live test.
- No currency conversion in the kit: token counts only, so the user applies their own rates.
- Test: `test_cost.py` builds a ledger, checks the per-role totals, the retry count and the
  extrapolation arithmetic.

## 3. Sequencing and effort
1. 2.1 + 2.2 skills and README (half a day). Unblocks everything.
2. 2.4 items 1–5 (a day): the cap, the q2 check, the placements path, holdings, empty accounts.
3. 2.3 naming with tests (a day).
4. 2.4 items 6–11 and 2.5 docs (a day).
5. 2.7 fixture and acceptance run (half a day plus model time; the 7 September run cost about
   0.5M tokens for `/sort` and is expected to cost about 2.5M for `/analyse` + `/deep-dive`).

## 4. Parked (TODO, not for the pilot)
- Scaling to thousands of files: script-driven worker pool instead of the main session as loop
  driver; script-first matching with a matcher role for the residue; shard by account after
  filing with a merge step; hierarchical judging for large accounts. Not needed for the pilot.
- Single reading pass (`/analyse --forms`) so `/deep-dive` does not reread; needs the validator
  to accept section A pending and a script to stamp A from placements.
- One-page position note layout.
- `/eval` isolation enforced by script rather than instruction.
- DCG standard decisions (execution status, `party_to` coverage, tree node type).

## Appendix — live test figures so far (7 September 2026)
| stage | agents | subagent tokens | main session tokens | wall clock | result |
| --- | --- | --- | --- | --- | --- |
| /sort | 33 Haiku filers (4 retries) | 327k | 140k | 36 min | 30/33 in the expected place or holding; 1 unfiled; no wrong match |
| /visualise | none | 0 | 17k | 4 min | additive, offline, no reads |
| /deep-dive | 32 readers, 6 judges, 32 extractors, 9 mappers (10 retries, 0 failures) | 3.70M (reader 0.91M, judge 0.30M, extractor 1.97M, mapper 0.53M) | ~190k | ~2h 40m incl. a rate-limit pause | 26/26 placements match the key; every governing document right; 181 nodes / 160 edges; reader missed Appendix A on the master (propagated to the note, caught by the mapper) |

Per-unit figures: filer ~10k per document (Haiku), reader ~28k (Sonnet), extractor ~62k with four
topics (Sonnet), judge ~49k per account (Opus), mapper ~106k per account (Opus). Harness figures do
not split cache reads/writes; record `/cost` per stage for billable weights.
