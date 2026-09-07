---
name: visualise
description: Creates offline Mermaid HTMLs from existing reports without another model read. Usage /visualise [all | "account"] [--analysis].
---

# /visualise [all | "account"] [--analysis]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

This is a script-only stage. It does not advance the analysis.

1. Require existing CSV/Markdown reports; if absent, say to run `/analyse` (or `/sort <pile>`
   for the cheap filing map) first and stop. This command is free: no model agent runs, so it can
   be repeated after every correction.
2. Run `python scripts/visualise.py --all`, or `--account "<ERP name>"` for the supplied account.
   Default diagrams show account filing only. If `--analysis` was explicitly supplied after a
   completed deep dive, pass it to draw the existing legal trees and part statuses.
3. Report the HTML/Mermaid files written and any warnings. Open `out/INDEX.html` or an account's
   `position.html` offline. No reader, judge, extractor or mapper may run in this command;
   no raw documents or external services are used. No CSV/Markdown or graph rows are rewritten.
4. Stop. Mention `/analyse` or `/deep-dive` only as optional next commands; never invoke either
   automatically.
