# DCG intake kit

File a pile of contracts against your ERP account list, then choose how much analysis to pay for.
There are four commands, and **each stops after its own stage**:

| command | runs | models | delivers |
| --- | --- | --- | --- |
| `/sort <pile>` (optional triage) | `/check`, `/prepare`, one filer per document, name matching, filing report | Haiku filers; main session matches | account folders with renamed copies, per-folder `documents.csv` and `README.md`, global `CORPUS.csv`/`ACCOUNTS.csv`, `INDEX.md` |
| `/analyse [all \| account "<name>"]` | `/read`, the card check, `/match --force`, `/judge` per account, `place.py --all --visuals` | Sonnet readers, Opus judges | status folders `1`–`6`/`unsure` with renamed copies, a position note per account, `documents.csv`, `CORPUS.csv`, short `README.md`, full `ANALYSIS.md`, `position.html` and `INDEX.html` |
| `/deep-dive [--topics ...] [--force]` | prerequisite check, `/extract`, `/map`, `/report --graph` | Sonnet extractors, Opus mappers | validated forms, `TREES.md`, `out/FORM-HEALTH.md`, `out/DIDNT-FIT.md`, `out/graph/` |
| `/visualise [all \| "account"] [--analysis]` | scripts only | none | re-rendered Mermaid HTML after corrections; free |

`/analyse` is the minimum deliverable: the documents in the right folders, a short CSV and note per
account, and the diagram beside them. `/sort` is **not** on the path to it — it is for a large or
unfamiliar pile where you want to fix the entity map and drop junk before paying for a full read.
`/deep-dive` never rereads cards or judgments: it requires them and stops if they are missing.

## Setup and inputs

Use Python 3.10 or later and Claude Code, opened from this kit's root. Clone
`https://github.com/sarturko-maker/contracts_kit.git` or download the zip, then install:

```
pip install -r requirements.txt
```

Also install **Poppler** separately. Claude Code's PDF page/image reading can use its `pdftoppm`
program; `pypdf` extracts text and does not supply that program. The kit requires `pdftoppm` on
PATH with JPEG output support, including for visually checking signature pages.

On Windows, run this in PowerShell:

```powershell
winget install --id oschwartz10612.Poppler --exact --source winget
```

This uses the [Poppler package in the WinGet repository](https://github.com/microsoft/winget-pkgs/tree/master/manifests/o/oschwartz10612/Poppler).
On macOS use `brew install poppler`; on Debian/Ubuntu use `sudo apt install poppler-utils`.
If WinGet is unavailable, use the [Windows Poppler builds](https://github.com/oschwartz10612/poppler-windows/releases)
and add the extracted `Library/bin` directory to PATH. **Close and reopen the terminal and restart
Claude Code** after installation so both see the updated PATH. `pdftoppm -v` should then print a
version. `/check` also tests actual JPEG rendering; if that fails, check which program is selected
(`Get-Command pdftoppm` in PowerShell) and use a build with JPEG support.

**Mermaid is already bundled** at `assets/mermaid.min.js` and copied into the output reports.
It needs no npm install, Node.js, Mermaid CLI or CDN access. `requirements.txt` installs the two
Python libraries and documents these external/bundled dependencies in comments.

Commands in this README and in the skills are written `python`; use `python3` where that is the
installed name. Reports use the bundled diagram library and need no network. Model calls still use
your configured Claude Code service. Paths use `pathlib`; Linux is tested, Windows and macOS are
intended targets.

Run the main session on Opus (or Fable where your account has it) with effort high. The main
session is the orchestrator: it matches company names to accounts, decides what to retry and reads
every agent's return. In the live test it was about a third of the cheap stage's tokens, and its
judgment is what keeps the sub-agents on their configured cheaper models.

Start with the preflight:

```
/check <path to pile>
```

It checks Python, `pypdf`, Poppler by rendering an invented one-page PDF to JPEG, the pile, the ERP
record, the bundled `mermaid.min.js` and write access. The rendering probe uses a temporary folder,
no contracts and no model calls. Any `FAIL` stops the workflow. A passing probe checks the local
renderer; if Claude's own PDF Read tool still fails, restart Claude and resolve that error before
analysis. Then `/prepare <path to pile>` inventories and numbers the files.
`/sort <pile>` runs both for you. `/analyse` requires prepared inputs; run `/check` and `/prepare` first when skipping triage.

Put contract files and one ERP record in a folder; subfolders are allowed. The kit copies originals
and never modifies, moves or renames them. Keep real piles outside the repository.

- ERP: CSV or XLSX with `erp` in its filename, or supply `/prepare <pile> --erp <file>`. Account rows
  are the sole source of account folder names. A customer/supplier account column determines the side;
  ambiguous columns or sides need your answer before filing.
- Readable: PDF, DOCX and page images (PNG, JPG, TIF). Native text is extracted locally; scans are
  viewed as pictures. There is no OCR dependency. Other formats retain inventory/report rows and paths.
- Optional `inputs/our-entities.csv` (`name,status,note`) helps distinguish your companies from theirs.
  Copy the shape in `inputs/our-entities.example.csv` and replace every example. Supplying your
  own names is recommended for cheap filing: otherwise ambiguous supplier names can become
  extra holding entries, and a reader is likelier to put your own company in a counterparty slot.
  Example entity maps and corrections are formats, never decisions to import.

## 1. Optional triage: /sort

```
/sort <path to pile>
```

This includes `/check` and `/prepare`: inventory, stable document numbers, hashes, native text and
ERP setup. Alternatively run those commands separately and then `/sort` without a path.

Each new document gets an identity pass configured for Haiku: the opening two pages or twelve Word
paragraphs, up to 1,200 native-text words. If identity is unclear, it may inspect one extra page or
up to eight extra paragraphs. The ceiling is **three distinct pages or twenty Word paragraphs**.
Scanned pages count towards that ceiling. It records title, preliminary type and printed company
names with brief exact evidence. An unresolved identity stays unresolved; it never triggers a full
reader. The main session matches those names to ERP rows and records basis and confidence.

Existing filing records or full sort cards are reused unless `/sort --force` is requested. The
`filer` role returns one line per document, in batches of at most five. This bounds source reading;
it is not a guaranteed currency cap. Actual cost on your Claude account has not been benchmarked.

Open `out/INDEX.md`, then `out/<side>/CORPUS.csv`. Each account folder contains:

- `files/`: renamed document copies (see "Renamed copies" below).
- `documents.csv`: identity, preliminary kind, account, match basis/confidence, original path/hash,
  reading status and uncertainty. It is the account's exact slice of the global table.
- `README.md`: a short list of what is filed there and what remains unclear.

There are **no status folders, position judgments, node/edge tables, HTMLs or diagrams** at this stage.
Execution, current validity and governing terms are unassessed. A company name found on an opening
page is sufficient for preliminary filing; it does not establish that the company signed.

Holding folders retain names not matched to the list, uncertain matches and files with no name;
`_needs-reading` retains failed/missing reads and `_unreadable` lists unsupported files. Stream ERP
rows get a README pointing to the main account unless a document explicitly names that stream;
a named stream keeps its own ERP folder. An explicit user mapping to the parent wins. Shared documents may appear under multiple accounts,
so the global CSV has one row per document/account, not necessarily one row per original.

Fix matches in `inputs/entity-map.csv`, set `decided_by` to `user`, then rerun `/sort`. User decisions
win. Rerunning cheap filing archives the old generated `out/` under `work/history/` and produces a
fresh filing report. Existing full cards, forms and judgments remain available for later reuse.

## 2. The deliverable: /analyse

```
/analyse
/analyse account "Exact ERP Account"
```

This is the stage that answers "what governs trade with this account". It needs `/prepare`; it does
not need `/sort`. It reads every readable document in full (or only the named account's documents),
checks the cards, matches identities from those full cards, judges each account and writes the
account folders, notes and diagrams. It does not fill forms and does not touch the graph.

Readers inspect the full body and open the signature pages as pictures. Schedules initially get title
and first page, expanding when a question needs them; appendices that list depots, sites or group
companies are read, because they answer the parties question. DOCX signature images, tracked changes
and comments inform the execution/draft assessment. Cheap filing records never substitute for a
full card.

After the readers return, `python scripts/check_cards.py --all` prints card warnings — most
importantly `question 2 may be reversed`, which is your own company written into a counterparty slot
and the reason a document lands in `_no-name-found`. `/analyse` reruns that one reader with the
warning quoted, never with the answer. Warnings it cannot fix (evidence over forty words, suspected
paraphrase) are reported, not silently repaired.

Judging covers ERP accounts that have documents; an account with no documents gets its empty folder
and README from the script, not from a judge. Documents in the holding folders keep their card facts
in `CORPUS.csv` and stay `unassessed (no account)` until you map the name; `INDEX.md` lists them
under what needs a decision. Nothing is invented and nothing is dropped.

The result puts copies into status folders — `1-governs-trade`, `2-governs-part-of-trade`,
`3-live-not-trade`, `4-not-live`, `5-orders-drafts-duplicates`, `6-business-practice`, `unsure` —
and writes a short `README.md` overview with a classification list and links. The full position,
execution and version uncertainty, limited scopes, conflicts with exact evidence, missing documents
and business questions stay in `ANALYSIS.md` and `position.html`. The judge targets 180 words for
the position paragraph; longer existing positions remain complete in the full analysis, with a
link from the overview.

The CSV `status` follows the final account judgment. `status_per_document` separately preserves
the reader’s initial assessment, before amendments and replacements were linked. The diagram
uses the final placement. `governing_docs` in the account index lists governing roots; amendments
and attached letters remain in the classification counts and document lists.

For `/analyse account "<name>"`, matching is scoped to the documents previously filed to that
account. Other accounts retain their filing rows and copies. The global CSV marks each row as
`filing only`, `read; awaiting judgment`, `judged` or `unreadable` in `analysis_stage`; an incomplete
account gets no governing diagram. A shared or reassigned document invalidates the affected
account’s old judgment, which is archived and must be refreshed explicitly. No additional readers
or judges are started for that account without your instruction.

`/analyse` stops here and mentions `/deep-dive`. Rerun `/visualise --analysis` for free after
corrections.

## 3. Full analysis: /deep-dive

```
/deep-dive
/deep-dive --topics off
```

This is the deepest stage and it explicitly authorises the second full reading pass. It starts with
a prerequisite check: every readable document has a card, every account with documents has
placements, and `work/logs/sort.csv` is not older than the cards. If anything is missing or stale it
names it and tells you to run `/analyse`; it never reads, matches or judges itself.

It then fills the fixed stage 2 form for every readable document, including holding files. By
default it includes the four defined commercial topics: freight, pricing, payment terms and
termination for convenience. `--topics off` omits those optional questions; `--topics <names>`
selects a subset using the names in `stage2/topics.md`. **Topics on roughly doubles extractor cost**
(about 62k tokens per document with all four in the live test). Existing compatible forms are
reused; `--force` replaces them.

Invalid forms block mapping. Mappers then propose a DCG family per tree and record what did not fit.
Graph outputs appear in `out/graph/`: `nodes.csv`, `edges.csv` in the fixed DCG headers, plus companion
properties, evidence, entity/account links and family proposals. Review each account's `TREES.md`,
`out/FORM-HEALTH.md` and `out/DIDNT-FIT.md`. Unsupported links are marked `exported=no` rather than
inventing DCG edge types. Account filing alone does not prove corporate ownership or legal coverage.
The card, form and DCG registries never change during a run; gaps are reported for later decisions.

Deep dive stops after the analysis reports. Use `/visualise --analysis` for refreshed HTMLs.

## Renamed copies

Copies the kit generates are named so that a folder listing reads like an index:

```
<doc_id> <kind> <counterparty> <date>[ <status>].<ext>
```

```
017 master-agreement Sturmore-Rail-Group 2021-02-22.pdf
013 master-agreement Sturmore-Rail-Group 2016-07-18 not-live.pdf
002 duplicate-of-015.pdf
022 unidentified 42pp.pdf
```

After `/sort` the name comes from the filing record (kind, first counterparty entity, date if found);
after `/analyse` it comes from the card (kind, first signing entity, start date) and the placement
(status folder, "duplicate of"). Spaces become hyphens, path-hostile characters and trailing dots are
stripped, the name is ASCII and capped at 120 characters, and it is Windows-safe. No agent ever
chooses a filename: the scripts build it.

Every row in `documents.csv` and `CORPUS.csv` carries a `filed_as` column with that name, and the
account README lists both: `017 — 017 master-agreement Sturmore-Rail-Group 2021-02-22.pdf —
original: Customers/Sturmore Rail/MSA 2021/signed master.pdf`. **Your originals and the numbered
copies in `work/files/` are untouched**; renaming happens only in the generated `out/` copies.

## Review and reruns

After analysis, legal and sales can filter `CORPUS.csv` or an account's `documents.csv` on `folder`,
`status`, `signed` and `account`. Reviewer columns are `legal_agrees`, `sales_agrees`, `correct_folder`
and `comment`. Put agreed corrections in `inputs/corrections.csv` (`doc_id,field,value,reason`),
then rerun the affected full workflow. Cite document numbers, never ambiguous filenames.

`/visualise` is the free re-render: a script-only pass over the existing CSVs and Markdown that
starts no reader, extractor or mapper and rewrites no CSV, Markdown or graph row. Open
`out/INDEX.html` and an account's `position.html`; the Mermaid source is beside it as `position.mmd`
and the bundled renderer works offline. After `/sort` alone the diagram shows **account → filed
documents**, with arrows meaning "filed under" and nothing about legal status. After `/analyse`,
`/visualise --analysis` draws the document and part relationships and the status folders. It refuses
to combine old placements with a newer filing table. `/visualise "Exact ERP Account"` renders one
account.

Run `/prepare <pile>` when sources change. Numbers stay stable, new files get new numbers, removed
files retain an audit row. Changed sources archive stale filing records, cards, forms and dependent
judgments under `work/history/`. Then choose `/sort` or `/analyse`; stages never advance unasked.
Never hand-edit generated `out/` or model-owned `work/` artifacts.

For targeted maintenance, the component commands remain available. Each stops after its own step:

| Command | Scope |
| --- | --- |
| `/check [pile]` | preflight only |
| `/prepare <pile> [--erp <file>]` | inventory, numbering, native text, ERP record |
| `/read all` or `/read <ids>` or `/read account "<name>"` `[--force]` | full sort cards, Sonnet readers |
| `/match [--force]` | matches full-card names and replays the entity map |
| `/judge all` or `/judge "account"` | full-card account judgments, Opus judges; accounts with no documents are skipped |
| `/extract default` or `/extract all [--topics names] [--force]` | validated forms, Sonnet extractors; topics off unless supplied |
| `/map all [--force]` | Opus family mapping and graph export; requires complete valid forms |
| `/report` | rebuild current CSV/Markdown reports only |
| `/report --graph` | explicitly rebuild analysis CSV/Markdown and graph outputs |
| `/visualise [all \| "account"] [--analysis]` | offline Mermaid HTML from existing reports |

If corrections change names, rerun `/match` before judgments. Re-extract affected forms with
`--force` after factual corrections, then `/map all --force` and `/report --graph`. Do not run
`/sort` inside this advanced analysis sequence: it deliberately returns the visible report to filing.

## The cost report and /cost

Every stage keeps a ledger: one row per spawned agent, retries included, in `work/logs/cost.csv`
(`stage,role,model,target,attempt,outcome,tokens,duration_ms,units_read`). The stage's last step is

```
python scripts/cost.py --stage analyse
python scripts/cost.py --stage analyse --extrapolate 200
```

which prints agents, retries, total tokens, tokens per document, tokens per page and wall clock, per
role and for the stage; `--extrapolate N` scales the per-document figures to a pile of N documents at
the same mix of roles and retry rate, and shows the per-page figure separately so a pile of longer
documents can be scaled by pages instead. There is no currency anywhere: token counts only, so you
apply your own rates.

**The main session's own tokens never reach that ledger.** Type `/cost` after each stage, while it is
fresh, and note all four figures — input, output, cache write, cache read — then add them to the
stage total. In the live test the orchestrator was about a third of the cheap stage.

Measured on the invented messy pile (33 files, six ERP accounts, 7 September 2026): filing 33 Haiku
filers for 327k subagent tokens; full reading 32 Sonnet readers at about 28k per document and 6 Opus
judges at about 49k per account; extraction 32 Sonnet extractors at about 62k per document with all
four topics, and 9 Opus mappers at about 106k per account. About 4.5M subagent tokens plus 0.35M
orchestrator tokens for the whole pile, all stages. Those are invented documents on one run; treat
them as an order of magnitude, not a quote.

## Reading policy and cost

The main cost is model reading, extraction and judgment. Generating CSV or Mermaid HTML is local
script work; separating HTML alone would save little model work. Cheap filing defers the expensive
questions. Full reading may require both a card and a form, so run `/deep-dive` only when that
analysis is useful.

A page read as a picture costs several times a page read as text, so a scanned pile costs several
times what the same words cost as native text; `/prepare` prints the scanned-page count on its own
line for exactly that reason. And at forty files the questions matter more than the model: the fixed
card and form, and the rule that a question the paper cannot answer gets "not found", do more for
the result than a model upgrade would.

For substantive answers, use the map to locate the relevant contract, then read its full body and
operative amendments, plus schedules needed for scope or precedence. Definitions, exceptions and
priority wording can change an apparent answer. The graph and forms are useful indexes and can
answer structured questions already captured; they are not a complete replacement for the sources.
This operating policy has not been compared directly with reading only selected parts.
An individual contract question can use the filing index and the relevant full sources directly;
it does not require `/deep-dive` across the entire pile first.

In the existing invented-pile evaluation, reading everything and map-then-selected-source-reading
both answered 12/12 questions; forms/graph alone answered 7/12 fully with optional topics off. The map
reduced PDF/image page reads from 111 to 59. Map construction and form/graph reading cost are excluded,
and those maps were curated. See `eval/RESULTS.md` and `BUILD-NOTES.md` for the limits.

Configured agent models live in `.claude/agents/`. Check `/tasks` during a filing batch on the target Claude account:
allowlist substitutions can change cost. Local tests here use Codex and do not certify Haiku filing
accuracy, Claude enterprise behavior or a dollar budget.

## Development, privacy and layout

`python -m unittest discover -s tests -v` checks isolated invented fixtures without changing operator
data. `sample/expected/` is a curated regression oracle, not a model accuracy measurement.
`/eval` is an optional, costly 36-trial comparison on a separate invented kit; it is never automatic.
See `sample/README.md` and `eval/README.md` for those workflows and build-only dependencies.

Never commit real piles, `inputs/*.csv`, `work/` or `out/`; they are ignored. Only kit source and
invented fixtures belong in commits. Reports stay local; no external sharing is part of any command.

| Path | Purpose |
| --- | --- |
| `CLAUDE.md`, `.claude/skills/`, `.claude/agents/` | runtime rules, commands and agent roles |
| `scripts/` | preparation, cheap filing, full matching/reporting, visualisation, validation, cost and export |
| `stage1/`, `stage2/` | fixed card/rules and fixed form/topics |
| `dcg/` | unchanged registries, pinned version in `VERSION.md` |
| `inputs/` | editable operator decisions; only examples committed |
| `work/`, `out/` | generated working records and review outputs |
| `sample/`, `eval/` | invented fixtures and evaluation |
| `BUILD-NOTES.md` | acceptance evidence, decisions and outstanding limits |

For a scripted/API reader, preserve the existing card/form JSON contracts and validation gate. The
Claude API takes a PDF directly as a `document` content block — base64 inline or by `file_id` from
the Files API, up to 32 MB and 600 pages per request — and each page arrives as extracted text plus a
page image, which is why a scanned page costs several times a text page there too; a scripted reader
therefore needs no local extraction step, but the same page budgets still apply. The cheap filing
record is deliberately separate. Entity-map basis/confidence remains the account association layer;
graph companion tables retain information outside DCG's fixed headers.
