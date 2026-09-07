# House rules — the DCG intake kit

- This folder is the DCG intake kit. The contract files, the ERP record, and everything under
  `work/` and `out/` are confidential, never leave this machine, and are never committed.
- Copy, never move or rename an original file. `work/files/` holds numbered copies.
- Documents are referred to by number (doc 017), never by filename.
- Every file in the pile gets a row somewhere. Nothing is skipped silently.
- The ERP record is the only source of account folder names.
- In stage 1 the sort card (`stage1/sort-card.md`) is the only list of questions; in stage 2 the
  form (`stage2/document-form.md`) is. Do not add, skip or reword questions while reading. A
  question the paper cannot answer gets "not found".
- Where evidence is required it is a page or clause reference and the exact words, forty or
  fewer. Never paraphrase in an evidence field.
- Look at the signature page as a picture, always. Companies sign, not people: record entities.
  A `.docx` is unsigned unless a signature image is present; tracked changes and comments mean
  draft.
- Look for parts with different lives before answering dates or scope.
- Readers and extractors handle one document and return one line. Judges and mappers work from
  cards and forms, not documents, except to check a quote. Nobody edits another agent's output.
- Nothing goes in a position note that is not in a sort card.
- Sorting follows `stage1/sorting-rules.md` word for word. Every account match has a basis and
  a confidence.
- Do not change the DCG standard (`dcg/`), the card or the form during a run. Write what did not
  fit in the didn't-fit list. The user decides changes afterwards.
- Cards and forms are the source; `out/` is generated. Hand-edit only `inputs/entity-map.csv`
  and `inputs/corrections.csv`. Never edit anything under `out/` or `work/` by hand.
- Budget: read the body fully; schedules get title and first page unless a question needs them;
  return one line, not a summary.
- How to run it is in `README.md`: `/check`, `/prepare`, `/read`, `/sort`, `/judge`, `/report`
  for stage 1; `/extract`, `/map`, `/report` for stage 2; `/eval` for stage 3.
