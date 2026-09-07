# The invented-contract evaluation

This tests whether a map finds the current document and part at less reading cost than reading
everything, and which questions the fixed form/graph can answer. It does not presume a winner.
The answer key in `questions.csv` is for the grader only. The as-of date is **2026-09-06**.

`pile/` contains the sample plus Quenby's old master and a replacement with a separately expired
pricing schedule: three accounts, eleven readable files (including the playbook and detached
signature), one unreadable file and an ERP record. Rebuild invented PDFs with
`python eval/make_pile.py` using build-time `reportlab` and `Pillow` from the sample instructions.

Run `/eval` in Claude Code. It prepares `work/eval/kit/`, an isolated copy containing no answer
keys, expected results, operator inputs or existing work. In that kit run `/prepare pile`, `/read all`, `/match`, `/judge all`,
then `/extract --all`, `/map all`, `/report --graph` with topics off. The account column is `customer_account`, the side
is customers. All stages use the fixed as-of date. Prepared source text is available without
OCR. Do not import `sample/expected/` answers as evaluation agent responses.
After the final graph report, run `python scripts/place.py --all --visuals` in the isolated kit to
remove stage 2 columns from mode B's document lists; the forms and graph remain available
to C. Prompt generation rejects B lists containing stage 2 columns. Keep artifacts fixed
while question agents run.

Run each of the twelve questions in A (all raw documents for the account, or all for corpus),
B (account position, document list and diagram, then just the indicated documents/parts), and
C (forms and graph rows only). Each of the 36 runs gets a **fresh agent with no inherited
conversation**, only the output of `python eval/run.py prompt Q01 A` with its id/mode changed.
The tool transcript must show which files/pages were accessed; instructions alone do not prove
that an agent stayed within its mode. Never reuse an agent across runs.

Save the untouched JSON response to `work/eval/runs/Q01-A.json`. The response records the answer,
citations, all accessed file paths and distinct source pages; a DOCX is a separate text unit,
not an invented page count. A picture and native text of the same page count once. A graph-only
run has zero source pages, but still incurs form/graph reading cost outside this proxy.

Grade against the key and the cited source, using the actual transcript, then write a companion
`Q01-A.grade.json` (never send it or the key to an answering agent):

```json
{"agent_id":"actual-new-agent-id", "fresh_context":true,
 "transcript":"work/eval/transcripts/Q01-A.txt", "access_compliant":true,
 "correct":true, "evidence_cited":true, "wrong_part_error":false,
 "pages_verified":true, "reason":"Concrete comparison to the answer key and evidence."}
```

Correct means the material answer matches the key, including its current/dead distinction;
equivalent words are fine. Evidence means an accurate document/part/page or clause reference
and supporting exact words, not merely naming a file. A wrong-part error relies on an expired
or replaced provision as current; merely mentioning it is not an error. Unknown/abstention may
be appropriate for C's information limits but is not scored as answering a question whose key
is definite. For Q06 the correct answer is expressly uncertain. Record access violations as
invalid runs, and missing page measurement as `pages_verified: false`.

Run `python eval/run.py score` to generate `RESULTS.md`. Missing responses stay **NOT RUN**;
unreviewed responses stay **NOT GRADED**. Review comparisons before writing a short reading to
`work/eval/reading.md`, then score again: where B matches A at less reading cost, any dead-part
errors, and C's successes or missing/coarse answers. Report ties and counterexamples honestly.
Map-building cost is excluded. Eleven invented files are cleaner than a real pile and only
indicative; this does not establish enterprise cost or accuracy.

For this build's measured runs, `python eval/make_expected.py` supplies curated cards,
placements and forms in the isolated kit. The question agents are still fresh and blind, but
this measures answering with curated maps, **not extraction accuracy**. Separate stage 1
handover acceptance tests the model reading workflow. `collect_codex.py` can retain the actual
local Codex rollout's tool calls/results and raw final response for grading; it excludes
reasoning records. Full-page PNG previews used by Codex are a build-only rendering aid; the
enterprise workflow uses Claude Code's native PDF/image viewing and needs no renderer.
