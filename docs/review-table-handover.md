# Handover: test direct Review_Table analysis once

The design has changed. Review_Table IS the index. There is no table-reader conversion stage,
no exact-quotation gate and no routine per-file source verification. The main session decides account
matches and governing relationships directly, reading a source rarely when a material doubt
could change the result. See [the column prompts](review-table-pilot.md).

Run 3 has now been reported complete and frozen: 5m47s, USD2.59 at harness list price, no
subagents and one logged source check. It fixed depot coverage but repeated the missed
Agreement/Order priority clause. These are operator-reported results; preserve that run as it is.
The kit now requires a targeted precedence check when a governing candidate's priority
information is missing/NOT_FOUND and another row makes a competing priority claim; it also
dashes edges from unsure documents. An unchanged table must exercise the new trigger—do not
repair its precedence answer first and thereby conceal the failure being tested.
Do not launch another paid run just because this handover changed. The sequence below is for
the next requested test, including a real vendor export when available.

## Preserve and reuse

Keep the previous full-source run and both conversion-route experiments intact, including their
transcripts and cost reports. If a previous runner is still active, do not mutate its kit or input.
Make one isolated copy of the CURRENT working tree, including uncommitted code/docs; a clean git
clone would omit the changes under test. Exclude work/, out/, memory/, .git/ and private/session
settings. Keep the ERP, ten-file corpus and existing reconstructed Review_Table in that copy's
accessible corpus. Reuse the table already built; do not reconstruct or re-quote its cells again.
Retain filenames, byte hashes and the original table. Do not copy prior cards, forms, placements,
notes, answer keys or evaluator reports into the analysis kit/context.

This is still an extraction-reuse experiment. Existing table preparation is a sunk cost to report
separately, not a new Hagora extraction measurement. Do not claim that the reconstructed cells
represent a real vendor export's quality or cost.

## One fresh main session

Open a fresh Opus Claude Code context in the isolated kit, with access to only that corpus and
kit. If using noninteractive CLI, give one explicit task once. Do not send a startup instruction
that executes the route and then repeat it with slash commands.

In an interactive session, run each command once:

```text
/check <isolated corpus path>
/prepare <isolated corpus path>
/analyse
/cost
```

Tell the runner:

```text
Use Review_Table as the analysis index and ERP for account names. Follow the current /analyse
TABLE route. Do the account reasoning in this main session. No per-document conversion or source
reader agents. Read a particular source excerpt only when you judge a material doubt could change
an important conclusion; those reads should be rare. Log the reason and scope before access and
the finding afterwards, including text/grep/PDF text checks. Minor blanks can remain unresolved.
Write the status folders, short bullet positions, CSVs and diagrams, then stop. No deep-dive,
automatic second run, table rewrite, or independent verification pass. Never inspect prior answers.
```

If an agent tries --publish, table-reader, mandatory VISUAL_CHECK or check_cards on imported rows,
it is using obsolete instructions: stop that attempt and report it rather than retrying the old
conversion loop. Keep the attempt's cost visible.

## Small evaluation after results are saved

Save the new outputs, input hashes, transcript and /cost figures before opening prior judgments.
Then compare the governing roots, account/site coverage, folder choices and material priority or
lifecycle conclusions. The earlier run is a comparator, not truth: inspect only source excerpts
needed to adjudicate material differences. Pay particular attention to the previously reported
master priority clause and named depot appendix, without feeding those answers to the runner.

Write one short comparison with:

- Accuracy: material improvements, regressions and unresolved conclusions, with source support.
- Source access: requested/completed checks, distinct files, actual pages/clauses, text versus
  images; reconcile logs against tool activity so unlogged grep/text reads are counted.
- Cost and elapsed time: preparation, this analysis, and evaluation separately. Include main
  session input/output/cache write/cache read figures. Zero subagents does not mean zero cost.
  Use measured currency totals if available; otherwise report unknown, not guessed savings.
- Column changes: the smallest prompt refinement needed by each observed failure. Try own
  reference in document, named sites/affiliates in group_scope and the instrument's own priority
  clause in precedence before proposing another paid column. No failure means no new column.

Do not run a second analysis automatically. Report whether the table-first design is useful and
what remains uncertain. Automated script tests cannot establish legal accuracy or model savings.
