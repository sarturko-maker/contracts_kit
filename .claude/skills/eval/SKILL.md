---
name: eval
description: Runs the invented three-account evaluation in an isolated workspace, using a fresh agent for each question and mode.
disable-model-invocation: true
---

# /eval

1. Read `eval/README.md`. Run `python eval/run.py prepare`; use the printed isolated kit path.
   Run `/prepare pile`, `/read all`, `/match`, `/judge all`, then `/extract --all`, `/map all`,
   `/report --graph`. Topics remain off. Never
   replace the operator's existing `work/`, `out/` or inputs with the invented evaluation.
   Finally run `python scripts/place.py --all --visuals` there to give mode B only stage 1 table columns;
   forms and graph rows remain available to mode C. Freeze these artifacts during the trials.
2. For each question id in `eval/questions.csv` and each mode A/B/C, run
   `python eval/run.py prompt <id> <mode>`. Give exactly that prompt to a NEW general-purpose
   agent with no conversation history. Never reuse an agent across questions or modes; never
   provide the answer key. Up to five independent runs at a time, within runtime limits.
3. Save each response verbatim as JSON under `work/eval/runs/<id>-<mode>.json`. Record the actual
   fresh agent id and tool transcript path. Keep question answering separate from grading.
4. Read the saved response, key and actual access transcript. Create its `.grade.json` companion
   using `eval/README.md`: correctness, cited evidence, wrong-part error and access compliance.
   Count actual distinct source pages opened. Do not guess page cost, agent isolation or scores.
5. Run `python eval/run.py score`. Review the generated `eval/RESULTS.md` table and add a short
   evidence-based reading in `work/eval/reading.md`, then score again. Report missing runs as
   NOT RUN, missing measurement as NOT MEASURED, and capability/access failures plainly. Never
   claim a model comparison from prepared answer keys or deterministic fixture tests.
