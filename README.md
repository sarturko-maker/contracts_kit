# DCG intake kit

File a pile of contracts against your ERP account list, then choose how much analysis to do.
`/sort` produces account folders, CSVs and short Markdown explainers with bounded identity reading.
`/visualise` adds offline Mermaid HTML diagrams from the existing reports.
`/deep-dive` reads the contracts fully, assesses what governs trade, fills the fixed forms and exports
Distributor Contract Graph (DCG) data. **Each command stops after its own stage.**

## Setup and inputs

Use Python 3.10 or later and Claude Code, opened from this kit's root. Clone
`https://github.com/sarturko-maker/contracts_kit.git` or download the zip, then install:

```
pip install -r requirements.txt
```

Reports use the bundled diagram library and need no network. Model calls still use your configured
Claude Code service. Paths use `pathlib`; Linux is tested, Windows and macOS are intended targets.

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
  extra holding entries. Example entity maps and corrections are formats, never decisions to import.

## 1. Cheap filing: /sort

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

- `files/`: numbered document copies.
- `documents.csv`: identity, preliminary kind, account, match basis/confidence, original path/hash,
  reading status and uncertainty. It is the account's exact slice of the global table.
- `README.md`: a short list of what is filed there and what remains unclear.

There are **no status folders, position judgments, node/edge tables, HTMLs or diagrams** at this stage.
Execution, current validity and governing terms are unassessed. A company name found on an opening
page is sufficient for preliminary filing; it does not establish that the company signed.

Holding folders retain names not matched to the list, uncertain matches and files with no name;
`_needs-reading` retains failed/missing reads and `_unreadable` lists unsupported files. Stream ERP
rows get a README pointing to the main account. Shared documents may appear under multiple accounts,
so the global CSV has one row per document/account, not necessarily one row per original.

Fix matches in `inputs/entity-map.csv`, set `decided_by` to `user`, then rerun `/sort`. User decisions
win. Rerunning cheap filing archives the old generated `out/` under `work/history/` and produces a
fresh filing report. Existing full cards, forms and judgments remain available for later reuse.

## 2. Diagrams: /visualise

```
/visualise
```

This runs a local script against the existing CSVs and Markdown. It does not start readers,
extractors or mappers. Open `out/INDEX.html` and an account's `position.html`; the Mermaid source is
beside it as `position.mmd`. The bundled renderer works offline.

The initial chart shows **account → filed documents**. Its arrows mean “filed under”; legal links
and governing status have not been assessed. `/visualise "Exact ERP Account"` renders one account.
After a deep dive, `/visualise --analysis` renders the richer document/part relationships and status
from the completed judgments. It refuses to combine old placements with a newer filing table.
Existing CSVs, Markdown and source files are unchanged by visualisation.

## 3. Full analysis: /deep-dive

```
/deep-dive
```

This explicitly authorises full analysis of every readable document in the prepared pile, including
holding files. It fills the unchanged sort card, matches full identities, judges account trees and
status, then fills validated DCG forms and maps them. By default it includes the four defined
commercial topics: freight, pricing, payment terms and termination for convenience.
`/deep-dive --topics off` omits those optional questions; `--topics <names>` selects a subset using
the names in `stage2/topics.md`. Existing compatible readings are reused; `--force` replaces them.

Readers inspect the full body and signatures as pictures. Schedules initially get title and first
page, expanding when a question needs them. DOCX signature images, tracked changes and comments
inform the full execution/draft assessment. Cheap filing records never substitute for full cards.

The previous filing report is archived under `work/history/` when full matching begins.
The result replaces filing lists with full analysis columns and puts copies into status folders:
`1-governs-trade`, `2-governs-part-of-trade`, `3-live-not-trade`, `4-not-live`,
`5-orders-drafts-duplicates`, `6-business-practice`, `unsure`. The account README becomes a position
note: what governs, execution/version uncertainty, limited scopes, missing documents and questions.
Its target is concise; one printed page is not currently enforced.

Graph outputs appear in `out/graph/`: `nodes.csv`, `edges.csv` in the fixed DCG headers, plus companion
properties, evidence, entity/account links and family proposals. Review each account's `TREES.md`,
`out/FORM-HEALTH.md` and `out/DIDNT-FIT.md`. Unsupported links are marked `exported=no` rather than
inventing DCG edge types. Account filing alone does not prove corporate ownership or legal coverage.
The card, form and DCG registries never change during a run; gaps are reported for later decisions.

Deep dive stops after the analysis reports. Use `/visualise --analysis` when you want refreshed HTMLs.

## Review and reruns

After analysis, legal and sales can filter `CORPUS.csv` or an account's `documents.csv` on `folder`,
`status`, `signed` and `account`. Reviewer columns are `legal_agrees`, `sales_agrees`, `correct_folder`
and `comment`. Put agreed corrections in `inputs/corrections.csv` (`doc_id,field,value,reason`),
then rerun the affected full workflow. Cite document numbers, never ambiguous filenames.

Run `/prepare <pile>` when sources change. Numbers stay stable, new files get new numbers, removed
files retain an audit row. Changed sources archive stale filing records, cards, forms and dependent
judgments under `work/history/`. Then choose `/sort` or `/deep-dive`; stages never advance unasked.
Never hand-edit generated `out/` or model-owned `work/` artifacts.

For targeted maintenance, the component commands remain available:

| Command | Scope |
| --- | --- |
| `/read all` or `/read <ids> [--force]` | full sort cards, Sonnet readers |
| `/match` | matches full-card names and replays the entity map |
| `/judge all` or `/judge "account"` | full-card account judgments, Opus judges |
| `/extract default` or `/extract all [--topics names] [--force]` | validated forms, Sonnet extractors; topics off unless supplied |
| `/map all [--force]` | Opus family mapping and graph export; requires complete valid forms |
| `/report` | rebuild current CSV/Markdown reports only |
| `/report --graph` | explicitly rebuild analysis CSV/Markdown and graph outputs |

If corrections change names, rerun `/match` before judgments. Re-extract affected forms with
`--force` after factual corrections, then `/map all --force` and `/report --graph`. Do not run
`/sort` inside this advanced analysis sequence: it deliberately returns the visible report to filing.

## Reading policy and cost

The main cost is model reading, extraction and judgment. Generating CSV or Mermaid HTML is local
script work; separating HTML alone would save little model work. Cheap filing defers the expensive
questions. Full reading may require both a card and a form, so run it only when that analysis is useful.

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
| `scripts/` | preparation, cheap filing, full matching/reporting, visualisation, validation and export |
| `stage1/`, `stage2/` | fixed card/rules and fixed form/topics |
| `dcg/` | unchanged registries, pinned version in `VERSION.md` |
| `inputs/` | editable operator decisions; only examples committed |
| `work/`, `out/` | generated working records and review outputs |
| `sample/`, `eval/` | invented fixtures and evaluation |
| `BUILD-NOTES.md` | acceptance evidence, decisions and outstanding limits |

For a scripted/API reader, preserve the existing card/form JSON contracts and validation gate. The
cheap filing record is deliberately separate. Entity-map basis/confidence remains the account
association layer; graph companion tables retain information outside DCG's fixed headers.
