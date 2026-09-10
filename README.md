# DCG intake kit

File a pile of contracts against your ERP account list, then choose how much analysis to pay for.
There are four commands, and **each stops after its own stage**:

| command | runs | models | delivers |
| --- | --- | --- | --- |
| `/sort <pile>` | Prepare, import Review_Table_Light, match names, file by account and status folder | Scripts; one names-only model turn for customers the script cannot match | account and status folders with copies, CSV/Markdown under `out/sort/`; no contract reads or diagrams |
| `/analyse [all \| account "<name>"]` (optional) | With Review_Table: import, account analysis, rare targeted checks, reports. Otherwise full readers and judges | Opus main session on table rows; otherwise Sonnet readers and Opus judges | status folders, short bullet position, per-account/global CSV, `README.md`, full `ANALYSIS.md`, diagrams and `INDEX.html` |
| `/analyse top [pile]` (optional) | After `/sort`: read in full the accounts listed in ERP_Top, plus files dropped in since; match, judge, report | Sonnet readers and Opus judges for those accounts only | the same deliverables for the top accounts; every other account stays filing only |
| `/deep-dive [top] [--topics ...] [--force]` | prerequisite check, `/extract`, `/map`, `/report --graph`; with `top`, for the ERP_Top accounts only | Sonnet extractors, Opus mappers | validated forms, `TREES.md`, `out/FORM-HEALTH.md`, `out/DIDNT-FIT.md`, `out/graph/` |
| `/visualise [all \| "account"] [--analysis]` | scripts only | none | re-rendered Mermaid HTML after corrections; free |

Stop at `/sort` when folders and a short inventory are enough. It applies section B of the
sorting rules to the export's answers and verifies nothing against the paper. Request `/analyse` for governing status and diagrams,
for all accounts or a selected account. It can also run directly without prior sorting.
See [the fourteen light questions and output layout](docs/review-table-light.md). For the
accounts that deserve a full reading, list them in ERP_Top and run `/analyse top`.
`/deep-dive` never rereads cards or judgments: it requires them and stops if they are missing.

## Setup and inputs

Already have a bulk-review export? Use **ERP + Review_Table + the original contract files**.
ERP controls account names; Review_Table supplies cited document facts. See the
[eleven focused column prompts and import instructions](docs/review-table-pilot.md) and the
[header template](inputs/Review_Table.example.csv). Both inputs accept CSV or XLSX.

```text
corpus/
  ERP.xlsx
  ERP_Top.xlsx
  Review_Table_Light.xlsx
  Review_Table.xlsx
  contracts/
    ...original contract files...
```

For cheap filing, run `/sort <corpus>`; it checks and prepares the corpus and uses only the light
table. Both exports are registered separately and excluded from numbering. For governing analysis,
run `/check <corpus>` then `/prepare <corpus>` then `/analyse`, or request /analyse after /sort.
The full analysis session uses the full Review_Table rows
and ERP directly to decide folders and governing relationships. There is no per-document model
conversion or card-validation pass. It rarely opens a relevant contract excerpt when a specific
material doubt could change the conclusion, recording the reason, scope and finding. Minor blanks
can remain unresolved. Missing citations and signature-attestation labels do not block analysis.
A governing candidate with missing/NOT_FOUND priority information and a competing priority claim
in another row requires a targeted precedence check. Table absence is not proof of source absence.
Material negative signature claims on otherwise governing candidates and gaps in schedules central
to the position also require focused checks. Unknown governing status is labelled unconfirmed;
it does not mean no contract governs. The [pilot guide](docs/review-table-pilot.md) explains the
checks and how to give the export short column headings instead of full question text.
An optional `contents` column, a clause-level map of each file, is held out of the index printout
and fetched only for the document being checked or the lines matching a search.
Initial import requires a row for each readable contract (blank answers are allowed), and exact
filename matching; it never falls back automatically to full-source reading. Table claims stay
externally reported except where a targeted source check is recorded. The main session still costs
money; actual savings and accuracy need a pilot measurement. CSV review_* columns preserve answers.
This table route covers `/analyse`; it does not create the native cards required by the current
`/deep-dive`. Stage 2 integration remains separate work.
For a local comparison using existing invented extraction, follow the
[fresh Opus test and evaluation handover](docs/review-table-handover.md).
For the unchanged-full-table cost comparison, see [the pilot instructions](docs/index-first-next-pilot.md).
The implemented light route now has its own [schema and commands](docs/review-table-light.md).

Use Python 3.10 or later and Claude Code, opened from this kit's root. Clone
`https://github.com/sarturko-maker/contracts_kit.git` or download the zip, then install:

```
pip install -r requirements.txt
```

On Windows, if only the Python launcher is available, use `py -m pip install -r requirements.txt`
and use `py` wherever these instructions say `python`. Claude should retain the interpreter that
passed `/check`, rather than retrying an unavailable command at every step.

For analysis with source image checks, also install **Poppler** separately. Light `/sort` skips
Poppler and Mermaid preflight checks because it does not use them. Claude Code's PDF page/image reading can use its `pdftoppm`
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

## 1. Cheap filing: /sort

```
/sort <path to pile>
```

This includes `/check` and `/prepare`: inventory, stable document numbers, hashes, native text and
ERP setup. Alternatively run those commands separately and then `/sort` without a path.

Review_Table_Light supplies fourteen answers per file: title, reference, document date, the
contracting customer and supplier entities, instrument, supply coverage, group mechanism,
signed, status, end date, and the relation to and words identifying a parent agreement. See
[the copyable questions](docs/review-table-light.md). `scripts/sort_light.py` imports the
export, matches customer entities to ERP accounts by company number, name and the entity map,
links children to parents by the dates they quote, and files every document by section B.
The only model step is one names-only turn for customers the script cannot match; it writes
each decision through `python scripts/sort_light.py --decide`, which checks the account against
the ERP and the basis and confidence, and the rows land in the entity map for you to confirm.
No contract text or image enters the model, and the full Review_Table is not used. A missing
light export stops /sort. So does a missing `inputs/our-entities.csv`: copy the example to that
name and list your contracting entities first, or the script cannot tell your own companies
from counterparties. The side follows the ERP column name; the as-at date comes from the Status
question in the export.

Open `out/sort/INDEX.md`, then `out/sort/<side>/CORPUS.csv`. Each ERP account has a README,
documents.csv and the status folders that apply: `1-governs-trade` to `6-business-practice`
and `unsure`, each with its own documents.csv. Every row carries the export's answers, the
parent it was linked to, the flags the script raised and the basis of the account match.
Files the review tool refused sit in `_unreadable` with its error code. No governing position
or diagram is generated; nothing is verified against the contracts.

Shared documents may appear under multiple accounts. Unknown names stay in holding folders.
Fix account matches in inputs/entity-map.csv with decided_by=user, then rerun /sort. User rows
win. An explicitly named ERP stream keeps its own folder unless a user mapping sends it to a
parent; light filing does not infer unnamed stream consolidation from prior analysis.

Only earlier light reports are archived under work/review-table-light/history. Existing full
analysis is preserved. A subsequent account-only /analyse can use current light matching to
select documents, then decide governing status from the separate full table.

## 2. The deliverable: /analyse

```
/analyse
/analyse account "Exact ERP Account"
```

This is the stage that answers "what governs trade with this account". It needs `/prepare`; it does
not need `/sort`. With Review_Table it reasons directly from rows and uses rare logged source
checks; no cards or reader/judge agents are required. Without a table it reads every
readable document in full (or only the named account's documents),
checks the cards, matches identities from those full cards, judges each account and writes the
account folders, notes and diagrams. It does not fill forms and does not touch the graph.

In the source-reading route, readers inspect the full body and open the signature pages as pictures. Schedules initially get title
and first page, expanding when a question needs them; appendices that list depots, sites or group
companies are read, because they answer the parties question. DOCX signature images, tracked changes
and comments inform the execution/draft assessment. Cheap filing records never substitute for a
full card.

In the full-source route, after the readers return, `python scripts/check_cards.py --all` prints card warnings — most
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

### Top accounts: /analyse top and /deep-dive top

```
/analyse top <pile>
/deep-dive top
```

The light filing covers the whole ERP for the cost of a script. For the customers that matter,
list their ERP account names in `ERP_Top.csv` or `ERP_Top.xlsx` in the pile: one column, the
names spelled as the ERP prints them (a stream row resolves to its main account). Drop any
contracts the business has collected for them into the pile, in any folder. `/analyse top <pile>`
then runs `/prepare` (new files get numbers, the filing log is kept, and ERP_Top is registered as
a control file, never numbered), computes the reading scope by script into `work/top/scope.json`
(the documents `/sort` filed to each top account, plus every readable file that has no filing
row, which is where the dropped-in contracts and the files the review tool refused land), reads
those documents in full with Sonnet readers, matches the names on their cards, judges each top
account with an Opus judge and writes the same notes, `documents.csv`, `CORPUS.csv`, `INDEX.md`
and diagrams as a full `/analyse`, for those accounts only. Every other account keeps its light
filing rows and appears as filing only, with its list and README but no second set of copies.
`--filed-only` leaves the unfiled documents out. Nothing outside the scope is read, and a
registered full Review_Table makes this scope unavailable.

`/deep-dive top` fills the forms for the scope's documents, maps the top accounts and exports
the graph for them. Both stop after their own stage. `python scripts/top.py --status` shows what
is registered, scoped, read and judged.

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

After `/sort` the name comes from the light type, ERP account and document number;
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
and the bundled renderer works offline. The new `/sort` has no diagrams. For previous source-filing
reports the legacy renderer still supports a filing map. After `/analyse`,
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
| `/read all` or `/read <ids>` or `/read account "<name>"` or `/read top` `[--force]` | full sort cards, Sonnet readers |
| `/match [account "<name>" \| top] [--force]` | matches full-card names and replays the entity map; scoped runs keep the other rows |
| `/judge all` or `/judge "account"` | full-card account judgments, Opus judges; accounts with no documents are skipped |
| `/extract default` or `/extract all` or `/extract top [--topics names] [--force]` | validated forms, Sonnet extractors; topics off unless supplied |
| `/map all [--force]` | Opus family mapping and graph export; requires complete valid forms |
| `/report` | rebuild current CSV/Markdown reports only |
| `/report --graph` | explicitly rebuild analysis CSV/Markdown and graph outputs |
| `/report [--graph] top` | the same for the ERP_Top accounts only, other accounts left filing only |
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
