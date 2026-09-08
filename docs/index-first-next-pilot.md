# Next pilot: spend on decisions that need source reading

The implemented command is still `/analyse` with the ten required analysis columns and optional
contents map. The fixes described below refine that route. **`/analyse-light` is a proposal,
not an installed command or an importer option.** A three-column table will not yet pass the
existing importer. Do not pad it with invented answers to make it pass.

## Improvements to test in the current route

- Relationship fields `attaches_to` and `replaces` take one document ID or blank. Invalid targets
  stop publication before existing reports are replaced. Unresolved effects stay in the prose.
- An empty governing folder with unsure documents is reported as unconfirmed. Rule 3 still
  precedes rule 6; the change does not deem rolling agreements expired or decide legal validity.
- Negative execution claims on otherwise governing candidates require a signature-page check.
  Missing attestation metadata alone does not. Do not recheck every positive execution answer.
- Missing/unreviewed schedules require a focused check when they could change a central scope,
  price or rebate qualification. Retain blank entries and completion conditions, without
  extracting every commercial term. Reuse existing current checks.
- Known-group matching stays provisional, and business questions should consolidate requests
  for the same evidence. A previous report is not proof that the current table is wrong.

The scripts can validate IDs, preserve results and expose uncertainty. They cannot mechanically
decide whether every free-text claim warrants a read. The source-check and question-selection
instructions still need a fresh Claude pilot; local tests do not establish their model accuracy.

## Proposed light input

Use exact `file_name` metadata plus three short free-text queries. Existing export facts may be
reused; do not pay to extract them again merely to change their layout.

| Field | Proposed question | Why retain it |
| --- | --- | --- |
| document | Give the printed title, function and own agreement/reference number. Flag distinct instruments combined in the file. | Distinguishes masters, amendments, orders and non-trade documents without trusting filenames. |
| parties | Give exact contracting entity names and their customer/supplier/other roles; distinguish mentioned affiliates. State ambiguity instead of guessing group membership. | Matches the ERP while keeping identity uncertainty visible. |
| trade_scope | Briefly state what this instrument does to purchasing terms or prices, its product/service/site/territory limits, and affiliate/adoption conditions. For an amendment/adoption, preserve the target reference and effect. Say unclear where the file does not establish these facts. | Helps select relevant masters and modifying instruments; prevents dropping a short but material amendment. |

Prefer brief labelled answers, with page pointers when supplied. Do not impose a word cap that
loses a party, target or scope condition. A complete clause map, execution assessment and full
term/precedence extraction would be optional later work in this proposed route.

The light stage should stop with account folders, short CSV/Markdown, a provisional trade /
non-trade / unclear description and a reading plan. It must not label an instrument as governing
or draw legal-effect arrows. Its filing output can use an ordinary folder diagram if wanted.

The next authorised analysis would select likely governing instruments and relevant amendments,
adoptions and schedules. It would read those sources as needed, including signatures and material
appendices. Unclear scope or linkage remains a selection reason, not grounds for automatic
exclusion. Only identical hashes prove byte duplicates. A complex account may still need most
of its documents read: no fixed percentage should manufacture savings by hiding uncertainty.

This could extend the existing cheap `/sort` command instead of adding another stage name.
It needs a distinct minimal import profile and output boundary; renaming the current `/analyse`
or silently accepting incomplete governance input would not implement it.

## Model and retrieval experiment

Start by reducing the repeated input and output. Keep Opus for the account decision while testing
Sonnet for the light filing/selection task and selected source extraction. Pass concise located
findings once; do not pay Opus to repeat every intermediate step. Pin and record actual model
versions, because aliases and enterprise provider availability can differ.

Before switching the entire analysis to Sonnet, compare it on the same table, corrections and
source-check policy in separate fresh contexts. Neither run sees the other's decisions. Compare
governing roots, uncertain status, execution, scope, amendments, missing material qualifications
and unnecessary business questions. Evaluate against selected source evidence and consistent
rules, not agreement with the older model alone.

Embeddings are optional retrieval infrastructure, not a substitute for readable source content
or a governing decision. Start with filename/hash metadata, exact entity/reference matching,
prepared-text search and an available contents map. Consider semantic retrieval when repeated
questions across a large corpus justify the indexing cost.

If tested, chunk at clause/subclause boundaries with the heading, exceptions and parent reference.
For tables keep headers with row groups, blank cells, units and footnotes. Retain document hash,
physical PDF pages, clause/schedule and account/entity metadata on every chunk. Keep signature
images accessible by page; text embeddings cannot recover a signature lost during extraction.
Retrieve neighbouring context and follow explicit references when necessary. Search misses do
not establish absence from the contract or corpus.

## Measure without disturbing the earlier run

Use an isolated copy of the updated kit and the same local corpus/export. Preserve original
exports and previous results. Keep comparison reports out of the fresh analysis context until
its results are frozen. Reuse previous extraction only if that is the experiment being measured;
label it separately from an actual vendor extraction test.

Run `/check`, `/prepare` and `/analyse` once each. On Windows retain the interpreter that works,
including `py`. Give the export short row-1 headers using the example; do not change cell values.
After the run capture `/cost`, elapsed time, actual models, check requests/completions and any
expanded source reads. Verify particularly that negative execution and material schedule gaps
are either resolved or explicitly attributed as unresolved, and that uncertain status is not
described as proof that no contract governs.

Report costs separately:

1. Vendor extraction, including retries and optional contents maps.
2. Preparation/orchestration before analysis.
3. Claude analysis, including the main session, selected reads and any subagents.
4. Comparison and evaluation, outside production analysis cost.

Record input, output, cache-write and cache-read usage where available. Do not compare vendor-only
cost with an all-in earlier run, or call an empty subagent ledger free analysis. State unknown
costs as unknown. Fewer columns or a cheaper model are hypotheses to measure, not a guaranteed
proportional reduction in total cost.

## Repeat with the same XLSX and corpus on Windows

Use the already working XLSX unchanged, including its short headers. Do not regenerate vendor
answers, add columns, or repair its omissions before this test. This measures the kit changes
against the same extraction, not the revised vendor prompts. Keep the same model and effort as
the comparator; the launch command below assumes that was Opus with high effort.

Exit the old Claude session. In PowerShell, starting inside the existing `contracts_kit` clone,
create a fresh sibling clone. The old kit and its outputs stay intact. A separate project path
also avoids reusing that project's automatic session memory. Copy only the existing operator
input CSVs, not old work artifacts or reports:

```powershell
$pilotPreviousKit = (Get-Location).Path
$pilotRerunKit = Join-Path (Split-Path $pilotPreviousKit -Parent) ("contracts_kit_rerun_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
git clone https://github.com/sarturko-maker/contracts_kit.git "$pilotRerunKit"
if ($LASTEXITCODE -ne 0) { throw "Clone failed; stop here." }
foreach ($pilotInput in @("our-entities.csv", "entity-map.csv", "corrections.csv")) {
    $pilotInputPath = Join-Path $pilotPreviousKit "inputs\$pilotInput"
    if (Test-Path -LiteralPath $pilotInputPath) {
        Copy-Item -LiteralPath $pilotInputPath -Destination (Join-Path $pilotRerunKit "inputs\$pilotInput") -ErrorAction Stop
    }
}
Set-Location -LiteralPath $pilotRerunKit
git log -1 --oneline
claude --model opus --effort high --add-dir "..\contracts"
```

This assumes `contracts` is beside the kit and contains the existing ERP and review XLSX, as in
the pilot layout. Adjust paths to their actual locations. If operator corrections or mappings
changed since the comparator, record that additional difference; it is not a pure code-only
comparison. Do not copy machine-generated findings from the previous report into these inputs.

Give the fresh session this instruction before the slash commands:

```text
This is a rerun using the unchanged review XLSX, ERP and corpus. Follow the current /analyse
table route. Do not rewrite the export or read any previous-run results, prior cards or prior
source-check findings. Use the existing operator input CSVs and record their use. Use py where
Python commands are needed on this machine. Wait for my slash commands; do not start the sequence
from this message. Run each stage once and stop after /analyse, with its source-check report.
```

Then enter these separately, waiting for each to finish. Replace the two example filenames
with the actual filenames from the previous successful run:

```text
/check "../contracts" --erp "../contracts/ERP.xlsx" --review-table "../contracts/Review_Table.xlsx"
/prepare "../contracts" --erp "../contracts/ERP.xlsx" --review-table "../contracts/Review_Table.xlsx"
/cost
/analyse
/cost
```

Record the first cost result as setup usage and the second as the cumulative result after
analysis; where the display is cumulative, the difference isolates analysis usage. Keep all
available token categories and elapsed time. Reusing the XLSX incurs no new vendor extraction
for this test; retain the original extraction cost separately when comparing production totals.

Only after saving the analysis and cost figures, ask for the comparison:

```text
Use Sonnet to compare only ../contracts_kit/out and this run's out. Read the reports and CSVs;
do not read contracts, prepared text, cards or previous work. Do not modify either run's outputs.
Compare governing roots, folders, material qualifications, unresolved findings and business
questions. Explain differences without treating the older report as truth; mark differences
that reports alone cannot resolve. Use only recorded cost figures and report comparison cost
separately. Write work/evaluation/COMPARISON.md. Do not rerun analysis or start deep-dive.
```

Use the actual previous kit name in that prompt if it differs. A reports-only comparison cannot
establish which extraction is factually correct; any later source adjudication is separate work.
