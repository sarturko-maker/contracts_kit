# DCG intake kit

Give this kit a folder of contract files and the ERP record of the accounts you want sorted. It puts
every file in the folder of the account it belongs to, then into a status folder that says whether the
document governs your trade with that account, and writes for each account a one-page position note, a
document list a reviewer can filter, and a diagram of how the documents hang together (stage 1). For the
documents that matter it then fills a fixed form whose answers map onto the Distributor Contract Graph
(DCG) standard and emits graph rows (stage 2). Stage 3 is an optional eval on the invented sample.

Everything is driven by two lists of questions: the sort card (`stage1/sort-card.md`) and the form
(`stage2/document-form.md`). The scripts only count, hash, copy and pull native text; the model does the
reading, including scanned pages and signature pages, which it looks at as pictures.

## What you need

- Python 3.10 or later. `git clone https://github.com/sarturko-maker/contracts_kit.git` or download the
  zip. No network is needed after that: the diagram library is in `assets/`.
- Claude Code, run **from the kit root**, with the main session on Opus (or Fable where available),
  extended thinking on, effort high. The readers run on Sonnet, the judges and mappers on Opus; that is
  set in `.claude/agents/`. If your organisation's model allowlist substitutes a model, Claude Code warns.
- Designed for Windows, macOS and Linux using `pathlib`; tested on Linux.

## Setup

```
pip install -r requirements.txt
```
Nothing else. Then, in Claude Code, run `/check <path to the pile>`. It prints one line per check
(Python, pypdf, the pile, the ERP record, the diagram library, write access) and stops you if one fails.

## Inputs

Drop the pile and the ERP record into one folder (subfolders are fine; the old folder names are used as a
clue, not a rule). The kit never modifies, moves or renames anything in it.

- **The ERP record**: a `.csv` or `.xlsx` whose file name contains `erp` (or name it with `--erp`).
  Its rows are the accounts to sort for, spelled the way you want the folders spelled. A column that
  says `customer` or `supplier` sets the side; otherwise `/prepare` asks. Rows that are streams of one
  account ("Acme" and "Acme Data Centres") are noticed and confirmed during `/sort`.
- **Readable files**: `.pdf`, `.docx`, page images (`.png`, `.jpg`, `.tif`). A `.docx` is treated as
  unsigned unless a signature image is inside it; tracked changes and comments are recorded as evidence
  of a draft; author and dates from the file properties are kept.
- **Everything else** (`.msg`, `.xls`, `.zip`, ...) is listed in the inventory and the report as "not
  readable by the kit" with its path. Nothing is skipped silently.
- Optional: `inputs/our-entities.csv` (`name,status,note`) with our current and former entity names,
  so the sort can tell our side from theirs. Example rows in `inputs/our-entities.example.csv`.

## Stage 1: the sort

Run these in order, from the kit root. Each one says what to run next.

| Step | What happens |
| --- | --- |
| `/check <pile>` | preflight; stops you if anything is missing |
| `/prepare <pile>` | inventory: every file numbered (doc 001 ...), hashed, native text pulled; ERP record copied to `inputs/erp-record.csv`; the account column and side confirmed; counts of pages and scanned pages (scanned pages cost several times more to read) |
| `/read all` | one reader per document fills its sort card (`work/cards/<id>.md` and `.json`), five at a time |
| `/sort` | the model matches every company name to an ERP account, with a basis and a confidence, and writes `inputs/entity-map.csv`; `scripts/sort.py` replays that file to build the account folders |
| `/judge all` | one judge per account groups the documents into trees, decides the status folder of each, and writes the position note's prose |
| `/report` | builds every account's folders, note, list and diagram, then `CORPUS.csv`, `ACCOUNTS.csv` and the index |

Readers and extractors skip existing answers unless you add `--force`; sorting and reports replay
their inputs, and judging refreshes the account decisions. Run `/prepare` again when the pile changes:
existing document numbers stay fixed, new files get new numbers, and removed files retain an audit row.
Changed sources cause stale cards/forms and dependent judgments to be archived under `work/history/`.

**What to look at first.** `out/INDEX.html`, then for each account under `out/<side>/<account>/`:

- `README.md`: the position note. One page: what governs trade, since when, whose paper, signed by whom,
  what covers part of the trade, what is missing, overlaps, open questions.
- `documents.csv`: one row per document with every fact and finding in plain columns.
- `position.html`: the diagram (opens offline) with the note under it; `position.mmd` beside it.
- The status folders: `1-governs-trade`, `2-governs-part-of-trade`, `3-live-not-trade`, `4-not-live`,
  `5-orders-drafts-duplicates`, `6-business-practice`, `unsure`. Each file is prefixed with its tree and
  document number (`T1-001-...`).

Then the holding folders under `out/<side>/`: `_not-on-the-list` (companies that match no account),
`_not-sure`, `_no-name-found`, grouped by company name; and `inputs/entity-map.csv`, where every match
is written down with its basis. To fix a match, edit the row, set `decided_by` to `user`, run `/sort`
again, then `/judge` and `/report`.

## How legal and sales review

Open `out/<side>/CORPUS.csv` (everything) or an account's `documents.csv` in a spreadsheet. Filter on
`folder`, `status`, `signed`, `account`. Fill the reviewer columns: `legal_agrees`, `sales_agrees`,
`correct_folder`, `comment`. Legal checks "is that the right contract and status"; sales checks "is that
how we actually trade with them". Every position note ends with the same request: reply with the
document number.

Agreed corrections go into `inputs/corrections.csv` as `doc_id,field,value,reason` (a card key such as
`q4_status`, or a placement column such as `folder`). Then run `/judge all` and `/report` again. Never
edit anything under `out/` or `work/` by hand; both are generated and will be overwritten.
If a correction changes company names, run `/sort` first. If stage 2 has already run, re-extract
affected documents with `--force` and run `/map all --force` before the final report.

## Stage 2: the form and the graph

Run after stage 1 has been reviewed and the corrections applied.

| Step | What happens |
| --- | --- |
| `/extract default` | one extractor per document in folders 1, 2 and `unsure` fills the form (`work/forms/<id>.json`), starting from the sort card; `--all` for every document; `--topics` turns on the optional commercial topics in `stage2/topics.md`; `scripts/validate_forms.py` gates every form |
| `/map all` | one mapper per account proposes a DCG family per tree with its structural evidence (`TREES.md`), writes the didn't-fit list, and runs `scripts/graph.py` |
| `/report` | as in stage 1, plus the form's fixed answers and the family proposals as extra columns in `CORPUS.csv`; `out/graph/nodes.csv` and `edges.csv` in the DCG sample's header format; `out/FORM-HEALTH.md`; `out/DIDNT-FIT.md` |

The DCG registries the mapper uses are copied unchanged into `dcg/` (see `dcg/VERSION.md`). Nothing in
`dcg/`, the card or the form is changed during a run; what did not fit goes in `DIDNT-FIT.md` for you
to decide afterwards.

The DCG sample headers cannot carry every required fact. `out/graph/node-properties.csv`,
`edge-evidence.csv`, `entity-account-links.csv` and `tree-proposals.csv` retain properties, quotes,
match basis/confidence and account-specific family proposals. They are companion tables, not extra
DCG edge types. Links the registry cannot represent are marked `exported=no`; read `DIDNT-FIT.md`
before treating the graph as complete. An account match alone does not establish legal ownership.

## Stage 3: the eval (optional)

`/eval` runs stages 1 and 2 on the invented pile in `eval/pile/` and answers twelve questions three ways
(read everything; map then read; graph only), scoring correctness, evidence, wrong-part errors and pages
read. It creates an isolated kit under `work/eval/kit/`, excluding operator data and answer keys.
Each question/mode needs a fresh agent and a reviewed access transcript. `eval/RESULTS.md` records
actual results; missing or ungraded runs are labelled explicitly. See `eval/README.md`.

## Development checks

Run `python -m unittest discover -s tests -v`. Tests use invented files in temporary kits and
do not alter operator inputs or outputs. `sample/expected/` is a curated oracle for deterministic
regression tests; replaying it does not measure a model's reading accuracy. `sample/README.md`
explains fixture generation. Build-time dependencies are unnecessary for normal kit use.

## What never to commit

The pile, `inputs/*.csv` (the ERP record, the entity map, the corrections), `work/` and `out/`. All of
them are confidential and `.gitignore` already excludes them. Commit only changes to the kit itself.

## Budget notes

- Count before reading: `/prepare` reports pages and scanned pages separately. A scanned page is read as
  a picture and costs several times a text page.
- One reader per document, one line back. Schedules are skimmed (title and first page) unless a
  question needs them. Readers run five at a time.
- At forty files the model choice matters less than getting the questions right. Do not tune models;
  fix the card or the form if the answers are wrong, and record what you changed.

## Scaling note for the data science team

The card and the form are the contract. To scale, replace the reader with a script that sends one
document and the questions to the model and writes the same JSON (`work/cards/<id>.json`,
`work/forms/<id>.json`); nothing downstream changes. Send PDFs through the API's PDF support, which gives
the model each page's text and picture together, so scans and signature pages work the same way without
OCR. Keep `scripts/validate_forms.py` as the gate. `inputs/entity-map.csv`, with its `basis` column, is
the legal-entity-to-account layer of the graph; `out/graph/` is what a graph database loads.

## Layout

```
CLAUDE.md          house rules (loaded by every session and sub-agent)
stage1/            sort card, sorting rules, position-note template, reader return line
stage2/            the form, its JSON schema, topics, didn't-fit template
dcg/               the DCG registries, copied unchanged, with VERSION.md
scripts/           check, prepare, sort, place (stage 1); validate_forms, graph (stage 2)
.claude/agents/    reader, judge (stage 1); extractor, mapper (stage 2)
.claude/skills/    check, prepare, read, sort, judge, report, extract, map, eval
sample/            invented pile and the expected cards, placements, notes and forms
eval/              the eval pile, questions and results
inputs/            what lands here (never committed, except the examples)
work/, out/        generated; never committed
BUILD-NOTES.md     what was built, tested, decided and left as TODO
```
