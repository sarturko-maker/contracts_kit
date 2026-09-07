# House rules — the DCG intake kit

- This folder is the DCG intake kit. The contract files, the ERP record, and everything under
  `work/` and `out/` are confidential, never leave this machine, and are never committed.
- Copy, never move or rename an original file. `work/files/` holds numbered copies.
- Documents are referred to by number (doc 017), never by filename.
- Every file in the pile gets a row somewhere. Nothing is skipped silently.
- The ERP record is the only source of account folder names.
- In full analysis the sort card (`stage1/sort-card.md`) is the first list of questions; for extraction the
  form (`stage2/document-form.md`) is. Do not add, skip or reword questions while reading. A
  question the paper cannot answer gets "not found".
- Where evidence is required it is a page or clause reference and the exact words, forty or
  fewer. Never paraphrase in an evidence field.
- During full reading, look at the signature page as a picture. Companies sign, not people: record entities.
  A `.docx` is unsigned unless a signature image is present; tracked changes and comments mean
  draft.
- Look for parts with different lives before answering dates or scope.
- Readers and extractors handle one document and return one line. Judges and mappers work from
  cards and forms, not documents, except to check a quote. Nobody edits another agent's output.
- Nothing goes in a position note that is not in a sort card.
- Account matching follows `stage1/sorting-rules.md` section A; full status judgments follow B.
  Every account match has a basis and a confidence.
- Do not change the DCG standard (`dcg/`), the card or the form during a run. Write what did not
  fit in the didn't-fit list. The user decides changes afterwards.
- Cards, forms and filing records are the source; `out/` is generated. Hand-edit only `inputs/entity-map.csv`
  and `inputs/corrections.csv`. Never edit anything under `out/` or `work/` by hand.
- Cost stages stop independently: `/sort` files by identity, `/visualise` renders existing reports,
  `/deep-dive` performs full analysis. Never advance to the next stage unasked.
- Cheap `work/filing/` records are not sort cards: at most 3 pages or 20 Word paragraphs per
  document. Unclear identity stays unresolved; legal status remains unassessed.
- Full-reading budget: read the body fully; schedules get title and first page unless needed;
  return one line, not a summary. Consult the relevant full instrument for substantive answers.
- `README.md` also documents explicit components: `/read`, `/match`, `/judge`, `/extract`,
  `/map`, `/report`. A report never creates graph rows without explicit `--graph`.
