# The messy invented pile

A second, deliberately untidy fixture: 33 documents plus an ERP extract across six ERP rows, nine
master agreements and four unsigned master drafts, and 28 traps (duplicates, a scanned duplicate, a
concatenated NDA and supply agreement, a missing signature page with a detached scan, lying
filenames, version chaos, rotated and noisy scans, an XLSX schedule, an email, a zero-byte PDF, a
text file with a `.pdf` extension, a 42-page master whose parties first appear on page 4, a company
on no ERP row, supplier-side paper in a customer pile, and our own former name as signatory).
Everything is invented. Rebuild with `python eval/messy/make_messy_pile.py` (build-time reportlab,
Pillow, python-docx, openpyxl, numpy); output is deterministic.

`expected/ANSWER-KEY.md` and `expected/key.json` are the grader's key: per file the expected kind,
account or holding folder with basis and confidence, execution, dates, relationships and status
folder; per account what governs trade on 7 September 2026 with payment, freight and notice terms
and evidence quotes; and every trap with the behaviour expected of the kit. **Never give the key to
an agent that runs the kit.** Copy `inputs-our-entities.csv` to `inputs/our-entities.csv` before
running, as an operator would.

Acceptance on this pile (7 September 2026, Opus main session, Haiku/Sonnet/Opus roles as configured):
`/sort` filed 30 of 33 in the expected place or an acceptable holding, `/deep-dive` matched 26 of 26
placements. Figures and defects are in `BUILD-NOTES.md` under "Live test on the messy pile".
