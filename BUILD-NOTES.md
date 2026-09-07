# Build notes

Resumed on 6 September 2026 and continued on 7 September. Claude Code had left an
uncommitted working tree: stage 1 scripts, agents and commands; the fixed stage 2 form;
the DCG registries; and the offline Mermaid asset. The schema, validator, graph exporter,
stage 2 workflows, samples, tests and evaluation were missing. The original brief was
recovered from `/home/sarturko/contracts_kit_BRIEF.md`; the repository's `CLAUDE.md`
contains the runtime house rules.

The local scripts and workflows are built, and both stages' independent reading/export
checks are recorded.
All 53 automated tests pass. Final acceptance still has one unresolved sorting-rule/example
conflict, described under “Decision needed” below; the rule has not been changed.

## What was completed

- Stage 2 JSON Schema and a standard-library validator: fixed choices, required answers,
  real dates, nested parts, precedence targets, optional topics, exact evidence at the
  cited native-text location, quote limits and duplicate JSON key rejection.
- Graph export using the unchanged DCG headers and registries. Stable entity/document/part
  IDs; dated replacement and termination links; independent part lifecycles; missing-document
  placeholders; cycle and structural-parent checks; optional clause/term facts.
- Generated family reports, flattened form columns in the corpus/account lists, form health,
  merged didn't-fit findings and companion audit tables for facts the DCG headers omit.
  Each mapper writes its own account report; the main session merges shared tables after
  all mappers finish, preventing concurrent output writes.
- Extractor/mapper agents and `/extract`, `/map`, `/eval` commands. Existing stage 1 commands
  were retained. No card question, sorting rule, form question or DCG registry was changed.
- Invented sample: nine readable files, one unreadable file and three ERP rows; explicit
  expected cards, placements, forms, family proposals and generated notes.
- Three-account evaluation pile, twelve keyed questions, isolated scratch-kit preparation,
  fresh-agent prompts, transcript collector and a scorer that keeps missing/ungraded runs
  explicit. The current evaluation uses curated maps/forms; it tests answering, not extraction.
- Fifty-three automated tests, including isolated end-to-end sample replay.

## Stage 1 fixes

New source files now receive new document numbers without shifting existing ones. Removed
sources retain an inventory audit row. A changed source archives stale cards/forms and
account judgments under `work/history/`; old readings cannot silently become another
file's answers. Account/entity corrections apply during sorting. Known-group confidence
is capped at fairly sure. Portable account paths cannot escape the output directory;
colliding ERP folder names stop preparation. DOCX media is refreshed when its source changes.

The note's completeness check now counts document rows, excluding cross-references in
other rows. Unambiguous `customer_account` and `supplier_account` headers determine side;
conflicting side data still needs an operator. The offline diagram uses Mermaid's strict
security setting. Auto-detection does not follow ERP symlinks. The index counts the numbered
business questions shown in each account note, avoiding duplicate counts when one question
concerns several documents.

Git attributes preserve PDFs, Office files and images as binary and keep CSV record endings.
This prevents checkout line-ending conversion from changing byte offsets or source hashes.
All 24 staged invented source files across sample/eval matched the tested bytes exactly.

## Recorded acceptance output

Environment: Python 3.11.2, pypdf 6.12.2, openpyxl 3.1.5 on Linux. Runtime scripts require
only the pinned enterprise dependencies; fixture rebuilding additionally needs the
build-time libraries listed in requirements.txt. Windows and macOS were not exercised.

`python -m unittest discover -s tests -v`: **53 tests passed**. Script compilation and all
workflow source-path references passed. An independent Draft 2020-12 JSON Schema validator
also accepted all nine shipped forms. These are deterministic regression checks, not model
reading scores.

Sample replay (`python sample/make_expected.py`, isolated temporary kit):

```text
ERP columns preserved: account_number, customer_account, country
Inventory: ERP + docs 001–010
Readable: 9; unreadable: 1
PDF/image pages: 11; scanned pages: 4
Doc 001 page kinds: ttts; doc 003: ss; doc 007: s
DOCX: 004 has tracked changes and 2 comments; 009 has tracked changes and 1 comment
Original hashes unchanged; second sort reproduces the same sort log/entity map

Tallowfield: folder 1 = 001, 002; folder 2 = 008; folder 4 = 003; folder 6 = 009
Pellmont: folder 2 = 006; folder 5 = 005; unsure = 004, 007
Stream row: README only
CORPUS.csv: 10 rows; account views exactly match its filters
ACCOUNTS.csv: 3 ERP rows, including 1 stream
Forms: 9 checked, 0 invalid; image evidence remains visibly flagged for human review
Graph: 19 nodes, 17 edges; 7 tree proposals; headers exactly match the DCG sample
```

The sample builder visually checked the signature/scanned pages. Headless Chromium rendered
Tallowfield's generated offline diagram to an SVG with no Mermaid syntax error, including
its live/dead part styling. Independent handover and sabotage outcomes are recorded below.

## Decisions and DCG limitations

1. The brief's acceptance counts of nine corpus rows and two account rows conflict with its
   all-file audit and all-ERP-row requirements. Preserve **ten corpus rows** (nine readable
   plus one unreadable) and **three account rows** (two main accounts plus the stream).
   Shared documents have one corpus row per document/account target so each account view
   remains an exact filter; the inventory retains one source row.
2. `source_key`, `confidence`, `commitment`, precedence and other registered properties have
   no columns in the copied sample header. Preserve them in `node-properties.csv`; retain
   link quotes in `edge-evidence.csv`, entity/account decisions in `entity-account-links.csv`,
   and account-specific tree memberships/proposals in `tree-proposals.csv`. These are
   companion tables, not invented DCG columns or edge types.
3. An ERP association is not proof that an entity owns that account. In particular a parent
   signing an NDA does not thereby own its subsidiary's trading account. The association
   and its basis/confidence survive in the companion table; no unsupported `belongs_to`
   assertion is added. DCG's registered direction is account → entity.
4. The registry has no tree node type. Family proposals go on unambiguous existing root
   instruments and in the tree-proposal table. Conflicting account-context classifications
   remain in that table and are flagged.
5. Execution and lifecycle cannot both occupy `status`. Graph status represents lifecycle;
   the form/corpus preserves execution status and the gap is reported. A later dated
   replacement can settle an older node's status without rewriting the older form.
6. DCG does not allow `party_to` from orders, components, shared terms or evidence. Such
   proposed edges remain in `edge-evidence.csv` with `exported=no`; they are not inserted as
   invalid graph edges. Consequently the brief's demand for party edges on every document
   conflicts with the unchanged registry. This remains an explicit standard limitation.
7. The detached signature page (007, kind `other`) and internal playbook (009) have no
   unambiguous permitted mapping from the fixed form. Both remain in forms/corpus and the
   didn't-fit list. They are not turned into invented governing instruments.
8. Doc 001's affiliate wording suggests C1 deemed participation, but the fixed form has no
   explicit per-entity deemed participation instrument. The curated sample proposes C1 with
   `not_sure` confidence, names the missing structure and flags it for review. The independent
   mapper reads the standard's express “affiliates may order hereunder” deemed-participation
   example as sufficient for C1 with `sure` confidence; the exporter still cannot create a
   per-entity participation node from the fixed form, so representation remains incomplete. No adoption
   nodes are inferred by a script. A governed-order answer alone also does not prove
   commercial completeness; that ambiguity is recorded.
9. Quote verification normalizes whitespace only. A scanned quote is not certified as
   verbatim by the script; it requires visual review. Clause-only citations check words but
   expose their location-verification limitation. Missing native extraction is a failure,
   not permission to accept unverified prose.
10. Evaluation mode B uses only stage 1 document-list columns; prompt generation rejects
    expanded tables to prevent form answers from leaking into mode B. Rebuilding its map after graph
    generation removes stage 2 columns that would otherwise leak form answers into mode B.
    Source-page counts exclude map-building cost and separately count DOCX text units.

The standard remains unchanged. Proposed changes belong in the didn't-fit list for the user.
MVP2 business-practice modelling was not built.

## Fresh handover and evaluation

The fresh README-only handover completed stage 1 in an isolated kit without expected answers.
It produced nine cards, two account reports, ten corpus rows and all three ERP rows; all eleven
input hashes were unchanged. Nineteen local HTML links resolved, and Chromium rendered both
account diagrams offline as SVG without Mermaid syntax errors.

The handover found the unnecessary ERP-side prompt and the duplicate question count, both
fixed and retested. Detailed note review also found that doc 001's reader paraphrased competing
freight terms and omitted express paper attribution, leaving the judge unable to quote the
conflict or identify whose paper it was. The reader instructions now retain that material
wording in question 10, group schedules that inherit the same life, and distinguish a mere
cross-reference from an operative attachment. The card's questions
remain unchanged. The judge instructions also separate historical precedence from current
applicability, so expired parts cannot hide a missing priority rule. Fresh document/judge
retests completed with the corrected reader/judge instructions.

Codex needs an absolute working directory in each reader's initial prompt; two attempts that
lacked it were discarded before acceptance. No expected-answer contents were read. These are
recorded as harness substitutions, not a claim that Claude Code itself ran on an enterprise
account. The final restored run has both fresh account judgments, all nine source copies,
all source hashes unchanged and no generator warnings. It keeps doc 008 as a standalone
tree. Its priority against the broad General Terms remains an expressly quoted unresolved
current overlap; the curated fixture instead relies on the site allocation. The literal-rule
placement discrepancy for doc 006 is below.

The evaluation's actual scored results and limitations are in [eval/RESULTS.md](eval/RESULTS.md).
Only saved fresh-agent responses with reviewed tool transcripts receive scores. Curated
fixture replay is not reported as independent extraction accuracy.

The missing-precedence retest explicitly reports historical priority as unresolved while
keeping current General Terms applicability separate. Removing only clause 9 leaves the
Programme's historical freight/payment priority unresolved; restoring it restores express
Programme priority. Current General Terms applicability is reported separately in both runs.
The source was restored and all eleven input hashes match the baseline. Thirty-two selected
native-source quotations were checked exactly, each within forty words. All nine final status
copies were unique and matched their sources. The final index's question counts were 3/2/0.

The final handover also exposed misleading automatic wording about the unsigned draft's
rolling term. The generator now says “rolling terms recorded; no evidence of current trading
under this text”; the draft's unknown execution/lifecycle qualification remains in its card
and position note. Reports were regenerated after the fix.

Independent stage 2 extraction and mapping are complete, and all 36 evaluation trials are
scored. The implementation is saved in local commits. Nothing has been pushed.

The separate stage 2 read exposed a distinction the schema cannot validate semantically:
the first doc 007 extractor encoded a confirmed attachment to the matching draft while its
notes called that match uncertain. That would overstate what the signature sheet proves.
The original form and transcript are preserved. Extractor instructions now classify the file
actually present and keep an absent execution version distinct from a possible matching draft;
a fresh replacement read classified the sheet as `other`, pointed to the absent execution
version with `not_in_pile`, and kept the draft candidate qualified in J/K. No fixed form field
was changed.

The evidence parser also initially mistook a Programme clause label `P6 (p.2)` for pages 6
and 2. Explicit page references now take precedence over bare `P` labels, with a regression
test. Form health counts valid negative answers such as `none`, and inheritance answers, as
answered rather than missing.
The health report also distinguishes the scalar answer `D3_ended_evidence` from quote objects;
its name no longer causes it to be silently omitted from the counts.

The evaluation's C results depend on its curated topics-off forms. Independent extractors
may retain additional commercial wording in free-text notes, as the separate doc 001 reader
did here. The measured C answers therefore do not establish the maximum capability of the
form, or measure the accuracy of the independent extraction pipeline.

### Independent stage 2 acceptance

Nine fresh accepted document reads, followed by two account mappers, used the restored
stage 1 cards and unchanged invented sources in an isolated kit with no expected forms.
Doc 007 required one fresh replacement after the semantic review described above. The
Tallowfield mapper corrected its own wording after review found it describing a missing
participation node as present. Its C1/sure interpretation remains independent of the curated
oracle's more cautious proposal. Both mappers now distinguish classification from export.

| doc | kind | status as read | layered | extractor K flags |
| --- | --- | --- | --- | --- |
| 001 | master_or_framework | live_rolling_presumed | yes, two parts | 2 |
| 002 | amendment_or_side_letter | live_rolling_presumed | no | 2 |
| 003 | nda | expired_by_date | no | 1 |
| 004 | master_or_framework | unknown | no | 3 |
| 005 | order_or_quote | unknown | no | 2 |
| 006 | pricing_or_rebate_letter | live_fixed_term | no | 3 |
| 007 | other | unknown | no | 3 |
| 008 | project_or_programme_agreement | live_fixed_term | no | 1 |
| 009 | internal_playbook | unknown | no | 4 |

```text
Forms: 9 valid; independent Draft 2020-12 validation: 9 valid
Doc 001: B9 yes; two parts; German entity affiliate_listed
Doc 007: missing execution version, no asserted attachment to draft 004
Doc 008: standalone site agreement, no asserted attachment to 001
NDA: separate T3 with overlay O3
Graph: 19 nodes, 17 edges, exact DCG headers, no dangling edges
Tree proposals: 7; entity/account associations with basis and confidence: 9
CORPUS: 10 rows; both account tables exactly match filtered corpus rows
Original input hashes unchanged: 11; extractor form hashes unchanged by mapping: 9
Scan-evidence review flags retained: 28
```

The accepted extractors viewed the signature/image pages of docs 001/002/003/005/006/007/008;
both Word files contained no embedded signature images. The flags remain because the script
cannot itself certify scanned wording. Actual tool records and one-line returns are retained
locally under `work/acceptance/stage2/`, with final forms, proposals and generated output.
The stage 1 handover transcript/checks and final reports are under `work/acceptance/stage1/`.
These audit artifacts are excluded from Git.

The mappers recorded 15 Tallowfield and 13 Pellmont findings before the combined merge.
Additional limits surfaced by those reads include non-signing-addressee coverage, proposed
versus confirmed effective dates, noncontiguous part-page sets, precedence-edge conditions
absent from the headers, and references/conflicts retained in prose but not emitted as graph
edges. Their presence in a family explanation does not add them to the graph. The independent
families were Tallowfield T1 C1/sure, T2 C2/fairly_sure, T3 overlay-only O3, T4 no family;
Pellmont T1 C13/sure, T2 and T3 no family.

### Measured evaluation

As of 2026-09-06, topics off. A reads all raw sources; B reads the map then pointed-to
sources; C reads forms and graph only. Question wording and the grading key are in
[eval/questions.csv](eval/questions.csv). All 36 rows below are actual fresh-agent trials.

| Question | Mode | Correct | Evidence | Wrong part | Source pages | DOCX units | Status | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q01 | A | yes | yes | no | 8 | 1 | SCORED | Current 30-day payment; excludes expired 60-day programme and site-only 45 days. |
| Q01 | B | yes | yes | no | 5 | 0 | SCORED | Same correct payment answer, with fewer source pages. |
| Q01 | C | no | yes | no | 0 | 0 | SCORED | Payment period absent with topics off; appropriate abstention. |
| Q02 | A | yes | yes | no | 8 | 1 | SCORED | Correct freight-at-cost permission; distinguishes expired programme and site-only inclusion. |
| Q02 | B | yes | yes | no | 5 | 1 | SCORED | Correct freight-at-cost answer; reads five pages plus the relevant internal playbook. |
| Q02 | C | no | yes | no | 0 | 0 | SCORED | Freight charging basis absent with topics off; appropriate abstention. |
| Q03 | A | yes | yes | no | 8 | 1 | SCORED | Correct six-month notice; original twelve months and site-only thirty days distinguished. |
| Q03 | B | yes | yes | no | 2 | 0 | SCORED | Correct amended notice period after reading only the relevant two source pages. |
| Q03 | C | yes | yes | no | 0 | 0 | SCORED | Correct six-month notice from the effective amendment. |
| Q04 | A | yes | yes | no | 8 | 1 | SCORED | Correct continuing German affiliate coverage despite the programme expiry. |
| Q04 | B | yes | yes | no | 5 | 0 | SCORED | Correct affiliate coverage; five source pages establish identity, survival and amendment. |
| Q04 | C | yes | yes | no | 0 | 0 | SCORED | Correct continuing German affiliate coverage after programme expiry. |
| Q05 | A | yes | yes | no | 8 | 1 | SCORED | Correct site agreement, 45-day payment and included freight. |
| Q05 | B | yes | yes | no | 2 | 0 | SCORED | Same correct site/payment/freight answer using two source pages. |
| Q05 | C | no | yes | no | 0 | 0 | SCORED | Identifies site agreement; payment and freight terms are missing. |
| Q06 | A | yes | yes | no | 3 | 1 | SCORED | Correct master uncertainty and current 2% rebate; detached signatures do not authenticate draft terms. |
| Q06 | B | yes | yes | no | 3 | 1 | SCORED | Correct answer; checking all four relevant files costs the same source reading as A. |
| Q06 | C | yes | yes | no | 0 | 0 | SCORED | Correct master uncertainty and current 2% rebate only. |
| Q07 | A | yes | yes | no | 4 | 0 | SCORED | Correct 21 days; excludes both expired ten-day schedule and superseded 45-day master. |
| Q07 | B | yes | yes | no | 3 | 0 | SCORED | Correct current 21 days, using only the replacement agreement’s three pages. |
| Q07 | C | no | yes | no | 0 | 0 | SCORED | Finds current General Terms; payment period is missing. |
| Q08 | A | yes | yes | no | 4 | 0 | SCORED | Correct expense basis and GBP 250 per-consignment cap, including pump purchases. |
| Q08 | B | yes | yes | no | 3 | 0 | SCORED | Correct freight expense and cap, using only the replacement agreement’s three pages. |
| Q08 | C | no | yes | no | 0 | 0 | SCORED | Freight expense basis and GBP 250 cap are missing. |
| Q09 | A | yes | yes | no | 15 | 2 | SCORED | Correct Quenby-only current sole-supplier commitment; qualifies Pellmont’s missing execution text. |
| Q09 | B | yes | yes | no | 8 | 1 | SCORED | Correct corpus answer after eight relevant source pages and one DOCX. |
| Q09 | C | yes | yes | no | 0 | 0 | SCORED | Correct: Quenby alone has a confirmed current sole-supplier commitment. |
| Q10 | A | yes | yes | no | 15 | 2 | SCORED | Correct two forthcoming fixed expiries; rolling terms and dead instruments excluded. |
| Q10 | B | yes | yes | no | 2 | 0 | SCORED | Correct two forthcoming fixed expiries, verified from only two source pages. |
| Q10 | C | yes | yes | no | 0 | 0 | SCORED | Correct two fixed expiries; excludes rolling and dead instruments. |
| Q11 | A | yes | yes | no | 15 | 2 | SCORED | Correct two current customer-paper agreements, including the site-only agreement. |
| Q11 | B | yes | yes | no | 9 | 0 | SCORED | Correct customer-paper count after nine source pages; no DOCX needed. |
| Q11 | C | yes | yes | no | 0 | 0 | SCORED | Correct two customer-paper governing agreements; excludes the draft. |
| Q12 | A | yes | yes | no | 15 | 2 | SCORED | Correct Pellmont-only gap; distinguishes confirmed coverage and dead parts elsewhere. |
| Q12 | B | yes | yes | no | 12 | 1 | SCORED | Correct corpus coverage answer; twelve source pages and one DOCX establish the three positions. |
| Q12 | C | yes | yes | no | 0 | 0 | SCORED | Correct: Pellmont alone lacks confirmed terms governing all trade. |

A and B each answered 12/12 questions correctly; C answered 7/12 fully. All three modes supplied accurate supporting evidence on 12/12, and none made a wrong-part error. Source reading totalled 111 PDF/image pages and 14 DOCX units for A, 59 pages and four DOCX units for B, and zero source pages/units for C. C still read forms and graph rows; that work is outside the page proxy.

B matched A with fewer source pages on 11 of 12 questions, reducing total source pages by 47%. Q06 tied at three pages plus one DOCX because every Pellmont file mattered to the master/rebate question. For the fixed-expiry corpus question Q10, B verified two pointed-to pages while A read all 15 pages plus both DOCX files. A successfully excluded the dead and replaced terms throughout; this run shows a reading-cost advantage for B, with equal observed correctness.

All modes answered the four corpus questions correctly. C's five incomplete account answers were four explicit abstentions (Q01, Q02, Q07, Q08) and one partial answer (Q05): payment or freight detail was missing with topics off. These were information gaps, not asserted answers drawn from dead parts. The run does not establish that only C can answer corpus questions, or test whether enabled topic readings would be too coarse.

The 36 trials used 36 distinct gpt-6-astra Codex agents, each started without inherited conversation. Manual review checked access scopes, citations and page counts. A provenance audit matched every preserved raw final and all 310 saved tool-call/result records to the original local rollouts; reasoning records were excluded. Responses, grades and transcripts remain under the ignored work/eval/ directory. This was one run per question/mode, using curated maps and forms; it measures answering with those artifacts, not extraction accuracy.

Source pages and DOCX units are separate proxies; neither map-building nor form/graph
reading cost is counted. This single run on eleven clean invented files does not measure
production accuracy or total token/runtime savings. The curated artifact limitation above
also applies. Full results are in [eval/RESULTS.md](eval/RESULTS.md).

### Decision needed: a sole live period-only letter

The independent judge put Pellmont doc 006 in folder 1, citing rule 6's instruction that a sole
live trade-governing document belongs there even when its scope is limited. The sample expects
folder 2 for that period-only rebate. All other baseline folder placements matched. This is a
conflict between the fixed sorting rules and the acceptance example, not a missing script branch.

Proposed resolution, subject to the user's choice: add this sentence to sorting rule 6:
“A pricing or rebate letter that sets only a period does not qualify under this rule.”
Rule 7 would then place such a letter in folder 2. The alternative is to retain the literal
rule and update the expected sample placement, keeping the scope qualification prominent.
No sorting rule has been changed without that decision.

## Documentation checks

The existing Claude model aliases, agent frontmatter/effort settings and inherited thinking
behaviour were checked against [Anthropic's subagent documentation](https://code.claude.com/docs/en/sub-agents).
PDF page-range and image-reading instructions match its [tools reference](https://code.claude.com/docs/en/tools-reference).
The independent test backend here is Codex; it does not certify enterprise allowlist behaviour
or Claude subscription availability.

## Local commits

- `bbd7ef8` — Build stage 1 contract sorting and offline reports.
- `e87bd8f` — Add validated DCG forms and graph export.
- `2a9c33e` — Add invented fixtures and measured three-mode evaluation.
- The following documentation commit records the README, acceptance results and remaining decisions.

The configured origin remains `https://github.com/sarturko-maker/contracts_kit.git`.
No push was performed; the user reviews these notes before pushing.

## TODO and release limits

- Resolve the rule 6 versus period-letter acceptance conflict above, then rerun the affected
  judgment and refresh its expected artifacts under the chosen rule.
- Verify the same workflow on the target Claude Code enterprise account, including the actual
  model allowlist and PDF/image tool behaviour. The local fresh-agent tests used Codex.
- Physical one-page note layout is not enforced. The fresh Tallowfield note is 1,372 words
  because it retains all required sections, document rows and competing quotations; it exceeds
  the brief's one-page aim. The HTML is an offline review page, not a validated print layout.
- Review the recorded DCG gaps before importing the graph as complete. In particular execution,
  unresolved version links, entity/account association and unsupported kinds need decisions in
  the standard, rather than invented columns or edges in this kit.
