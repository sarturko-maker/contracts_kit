---
name: extract
description: Fills validated stage 2 forms with one extractor per document. Usage /extract default | all | <ids> [--force] [--topics <names>].
---

# /extract default | all | <ids> [--force] [--topics <names>]

Normally invoked by a stage skill (`/sort`, `/analyse`, `/deep-dive`); run it directly only for
targeted maintenance. It stops after its own step and never starts the next.
Commands are written `python`; use `python3` where that is the installed name.

Run after stage 1 review and correction. Paths are relative to the kit root.

1. Select unique document ids: omitted/`default` means placements in `1-governs-trade`,
   `2-governs-part-of-trade` or `unsure`; `all` or `--all` means every readable inventory row
   except ERP; explicit numbers are padded to three digits. Every selected id needs a card.
2. Skip existing forms unless `--force`; print selected, skipped and missing-card counts.
   Topics are off unless `--topics` names fixed topics from `stage2/topics.md`. When adding
   topics to existing forms, require `--force` to replace those forms; explain this if omitted.
3. Spawn the `extractor` agent once per selected id, in batches of up to five, with the id and
   enabled topic names. Wait for each batch. The extractor owns its form; never fill or repair
   it yourself. Append each return line to `work/logs/extract.log`.
4. On a missing form, failed validation or unusable return, retry that extractor once with its
   error; record a second failure and continue. Run `python scripts/validate_forms.py --all`.
5. Report forms written, skipped and failures by id. A failed form blocks mapping. Otherwise
   say what to run next: `/map all`, then `/report --graph`. If existing forms were replaced, use
   `/map all --force` so family proposals are refreshed from those changed answers.
