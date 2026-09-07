# Answer key — the messy invented pile

**Held back from the kit.** The filer, reader, judge, extractor and mapper must never see this
file. Only the person judging a run reads it.

Everything in the pile is invented: companies, people, addresses, company numbers, sites, prices
and signatures. Nothing corresponds to a real organisation.

- **Review date assumed throughout:** 7 September 2026.
- **Our side:** Halbrook Electrical Distribution Ltd (company number 04118276), an invented UK
  electrical and industrial distributor. Former name **Halbrook Cable & Fixings Ltd**, changed
  3 June 2019; that former name signs the 2016 Sturmore agreement.
- **34 files:** one ERP record and 33 documents, in seven nested folders with real-world names.
- **Machine copy:** `key/key.json`, same content, one entry per file plus accounts and traps.

## The ERP record — `erp_extract_2026-09-01.csv`

Columns `account_number,customer_account,country,site`.

| account_number | customer_account | country | site | documents |
| --- | --- | --- | --- | --- |
| HAL-40118 | Sturmore Rail Group | United Kingdom | | 9 |
| HAL-40119 | Sturmore Rail Group - Northern Depot | United Kingdom | Northern Depot | stream row of HAL-40118 |
| HAL-40204 | Wexbury Utilities plc | United Kingdom | | 6 |
| HAL-40311 | Ardleigh Marine Systems Limited | United Kingdom | | 6 + 2 Brenlow candidates |
| HAL-40390 | Trentmoor Housing Partnership | United Kingdom | | 5 + 1 shared |
| HAL-40566 | Ravenhead Grid Services Ltd | United Kingdom | | **0** |

Five accounts across six rows: four accounts hold documents (one of them carrying a second,
stream row) and one account row has nothing filed against it at all.

## Expected holding folders

| folder | files |
| --- | --- |
| `_no-name-found` | the 42-page Trentmoor master — **at cheap filing only** |
| `_not-sure` | both Brenlow files; the 2026 rebate letter if the trading name is not accepted |
| `_not-on-the-list` | `Misc/Fenwold master.pdf`, `Misc/Cadmere framework (we buy).pdf` |
| `_unreadable` | `RE_ RE_ amendment.msg`, `Schedule 2 price matrix 2026.xlsx` |
| `_needs-reading` | `new doc 2.pdf` (zero bytes), `contract notes.pdf` (text file, .pdf name) |

---

# Part 1 — one entry per file

Each entry gives: kind, printed company names, expected ERP account with basis and confidence
under sorting rules section A, execution, key dates, relationships, expected status folder under
section B, live and dead parts, and the trap.

## Account A — Sturmore Rail Group (HAL-40118, stream HAL-40119)

### `Customers/Sturmore Rail/2016 old agreement/Sturmore supply agreement 2016 SIGNED.pdf`
- **Kind** master or framework, supplier paper (ours). 3 pages, page 3 a scanned signature page.
- **Names printed** Halbrook Cable & Fixings Ltd (04118276) — *our former name*; Sturmore Rail
  Group Limited (03996120).
- **Account** Sturmore Rail Group — basis `same name`, confidence `sure`.
- **Execution** signed both; R. Aldbury and T. Vessey, both 18 July 2016.
- **Dates** start 18 July 2016 (stated, cl.2.1); rolling until three months' notice (cl.2.2);
  ceased 1 March 2021 on replacement.
- **Relationships** replaced by the Master Supply Agreement dated 22 February 2021 (that
  document's cl.3.1).
- **Status folder** `4-not-live`. Whole document dead.
- **Trap** our own signing entity appears under the *former* name — without
  `inputs-our-entities.csv` a filer reads it as a third company. "Limited" against the ERP's bare
  name. Its 30-day payment and £350/£15.00 carriage terms are dead and must never be reported.

### `Customers/Sturmore Rail/MSA 2021/Sturmore MSA 2021 executed.pdf`
- **Kind** master or framework, customer paper. 4 pages, page 4 a scanned signature page.
- **Names printed** Sturmore Rail Group Ltd (03996120); Halbrook Electrical Distribution Ltd;
  Appendix A names *Sturmore Rail Group - Northern Depot* and *Central Stores*.
- **Account** Sturmore Rail Group; the stream row HAL-40119 is named in Appendix A and shares the
  main folder — basis `same name`, `sure`.
- **Execution** signed both; T. Vessey 22 February 2021, P. Nettlefold 24 February 2021.
- **Dates** start 1 March 2021 (stated, cl.1.1); initial three-year term, then year to year;
  rolling until six months' notice (cl.2.2). **Live.**
- **Relationships** supersedes the 2016 conditions (cl.3.1); amended by Amendment No. 1; an
  unsigned Amendment No. 2 draft exists; PO 88231 is placed under it; carriage varied for one site
  by the Kellerby joint letter.
- **Status folder** `1-governs-trade`. No separately-lived parts (Appendix A has no expiry, A4).
- **Trap** the payment term printed here (45 days, cl.7.1) is **not** the current term. Answering
  payment from the master alone is wrong.

### `Customers/Sturmore Rail/MSA 2021/Amendment 1 signed.pdf`
- **Kind** amendment or side letter. 1 page, drawn signatures.
- **Names printed** Sturmore Rail Group Ltd; Halbrook Electrical Distribution Ltd.
- **Account** Sturmore Rail Group — `same name`, `sure`.
- **Execution** signed both, 6 June 2023.
- **Dates** dated 6 June 2023, effective 1 July 2023, lives as long as the master (cl.1.3).
- **Relationships** amends the 2021 master (cl.1.1). Exact duplicate:
  `00 TO FILE/FINAL FINAL signed (2).pdf`. Scanned copy: `00 TO FILE/scan0007.pdf`.
- **Status folder** `1-governs-trade`, with the master it amends. **Best copy: this one.**
- **Trap** three copies of one instrument under three names.

### `00 TO FILE/FINAL FINAL signed (2).pdf`
- **Kind** amendment (duplicate). **Byte-for-byte identical** to `Amendment 1 signed.pdf` — the
  sha256 is the same, so the duplication is provable.
- **Account** Sturmore Rail Group — `same name`, `sure`. **Status folder**
  `5-orders-drafts-duplicates`, marked "duplicate of". Best copy: no.
- **Trap** a filename that shouts FINAL FINAL signed on a document that is neither final nor a
  master.

### `00 TO FILE/scan0007.pdf`
- **Kind** amendment (scanned copy). 1 page, **rotated 90 degrees**, image only, no native text.
- **Execution** signed both — visible only as a picture.
- **Account** Sturmore Rail Group. **Status folder** `5-orders-drafts-duplicates`. Best copy: no.
- **Trap** must be opened as a picture and recognised as the *same* instrument as Amendment No. 1,
  not filed as a second amendment.

### `Customers/Sturmore Rail/MSA 2021/Amendment 2 - tracked - DO NOT SEND.docx`
- **Kind** amendment or side letter — **unsigned draft**. Two tracked changes, two comments,
  blank signature blocks.
- **Account** Sturmore Rail Group — `same name`, `sure`.
- **Execution** nobody. A `.docx` with no signature image is unsigned; tracked changes and
  comments mean draft.
- **Dates** circulated 14 July 2026. Never effective.
- **Status folder** `unsure` — an unsigned draft with **no** signed version of Amendment No. 2 in
  the pile.
- **Trap** four wrong numbers on one page: proposed £500 carriage and 75 days' payment, plus the
  tracked deletions £400 and 90 days. Clause 2.1 says in terms that it binds nobody until signed.

### `Customers/Sturmore Rail/PO's/PO88231 northern depot.pdf`
- **Kind** purchase order. 2 pages: face and reverse conditions of purchase.
- **Names printed** *Sturmore Rail Group - Northern Depot* (exactly the stream ERP row); "a depot
  of Sturmore Rail Group Ltd"; Halbrook Electrical Distribution Ltd.
- **Account** stream row HAL-40119 is named by the document; filed in the main account folder
  under rule A1 with the stream noted — `same name`, `sure`.
- **Execution** unsigned by design ("no signature is required").
- **Dates** ordered 19 August 2026, delivery 26 August 2026.
- **Status folder** `5-orders-drafts-duplicates` — a single transaction.
- **Trap** reverse condition 14 claims to prevail over "any master agreement … however and
  whenever agreed". It must not change what governs; card question 7 and form section G both say
  to ignore that wording.

### `Customers/Sturmore Rail/Account notes (internal).docx`
- **Kind** internal playbook or guidance. One comment, no signature.
- **Account** Sturmore Rail Group — `same name`, `sure`.
- **Status folder** `6-business-practice`, shown apart in the note.
- **Trap** full of commercial-looking numbers (17.5% margin, list less 20% ad hoc, "do not chase
  before day 65") that are internal practice, not agreed terms — and it recites the real 60-day
  term, which tempts a reader into citing a memo as evidence of a contractual term.

### `00 TO FILE/RE_ RE_ amendment.msg`
- **Kind** email, unreadable format. Forwards the Amendment No. 2 draft.
- **Status folder** `_unreadable`, **with** an inventory row and a report row. Nothing is skipped.
- **Trap** its readable fragments mention the 75-day ask; they must not leak into the terms.

## Account B — Wexbury Utilities plc (HAL-40204)

### `Customers/Wexbury/Framework 12-05-2022.pdf`
- **Kind** master or framework, customer paper. 3 pages, page 3 a scanned execution page.
- **Names printed** Wexbury Utilities plc (05512443); Halbrook Electrical Distribution Ltd
  (04118276).
- **Account** Wexbury Utilities plc — `same name`, `sure`.
- **Execution** **them only.** E. Padstow signed 12 May 2022; our block is blank, with empty
  Name / Title / Date rules.
- **Dates** start 1 June 2022 (stated, cl.2.1); rolling until six months' notice (cl.3.2); notice
  served 14 August 2026, so it ends **14 February 2027**. Live today.
- **Relationships** confirmed by Wexbury's letter of 4 September 2024; terminated with future
  effect by our notice of 14 August 2026; an unsigned draft of it is filed as `Signed final.pdf`.
- **Status folder** `1-governs-trade` with the one-sided execution recorded in the note; `unsure`
  is defensible only if the note explains why.
- **Trap** the status is genuinely arguable. Both "signed by both" and "drop it, we never signed"
  are wrong. Form field B4 has no DCG value for one-sided execution — expect a didn't-fit entry
  (`missing_allowed_value`).

### `Customers/Wexbury/Signed final.pdf`
- **Kind** master or framework — **unsigned draft**, DRAFT watermark on all 3 pages.
- **Account** Wexbury Utilities plc — `same name`, `sure`. **Execution** nobody.
- **Dates** draft dated 3 March 2022; comments due 18 March 2022.
- **Relationships** earlier draft (v0.4) of the framework dated 12 May 2022.
- **Status folder** `5-orders-drafts-duplicates`.
- **Trap** the filename lies outright, *and* the draft carries different terms from the executed
  version — 90 days' payment and twelve months' notice against the real 60 days and six months.

### `Customers/Wexbury/letter from WU Sept 24.pdf`
- **Kind** letter. Signed by Wexbury only, J. Cottrill, 4 September 2024.
- **Account** Wexbury Utilities plc — `same name`, `sure`.
- **Status folder** `1-governs-trade` as a member of the framework's tree (`3-live-not-trade` is
  acceptable if reasoned).
- **Trap** the only paper that cures the missing signature. Miss it and the framework looks
  unexecuted; over-read it and it becomes a variation, which its own last line denies.

### `Customers/Wexbury/rebate 2026.pdf`
- **Kind** pricing or rebate letter, our paper, signed by us only (A. Whitcombe, 12 January 2026).
- **Names printed** **Wexbury Power Networks** — a trading name that is on no ERP row; Halbrook
  Electrical Distribution Ltd.
- **Account** Wexbury Utilities plc — basis `known group`, confidence `fairly sure` at best
  (nothing *in this document* links the trading name to the ERP name). `_not-sure` is an
  acceptable cheap-filing outcome.
- **Dates** 1 January 2026 to 31 December 2026; credit note by 28 February 2027.
- **Status folder** `2-governs-part-of-trade` — a period only.
- **Trap** two in one: a trading name that needs an evidenced basis, and section B rule 6, which
  says a period-only rebate letter does not qualify for `1-governs-trade`.

### `Customers/Wexbury/IMG_2291.jpg`
- **Kind** letter — a **phone photograph** of a signed one-page letter, taken off square under
  uneven light.
- **Names printed** Wexbury Utilities plc; Halbrook Electrical Distribution Ltd.
- **Account** Wexbury Utilities plc — `same name`, `sure`.
- **Execution** them only; J. Cottrill, 21 January 2026.
- **Relationships** accepts the rebate letter of 12 January 2026; confirms the framework is
  unchanged.
- **Status folder** `2-governs-part-of-trade`, with the rebate letter.
- **Trap** it is the bridge that ties "Wexbury Power Networks" back to the ERP name, so dismissing
  it as "just a photo" weakens the rebate letter's match.

### `Customers/Wexbury/notice served 14-08-26.pdf`
- **Kind** letter — notice of termination, our paper, signed by us, 14 August 2026.
- **Account** Wexbury Utilities plc — `same name`, `sure`.
- **Dates** the framework ends **14 February 2027** — in the future.
- **Status folder** `1-governs-trade`, with the framework, which is still live today.
- **Trap** a termination letter that does **not** make its target dead. Filing the framework as
  `4-not-live` because a termination letter exists is the error this file catches. It also proves
  both sides treat the one-sided framework as binding.

## Account C — Ardleigh Marine Systems Limited (HAL-40311), formerly Colverne

### `Customers/Ardleigh (ex Colverne)/old files/Colverne supply agreement 2019.pdf`
- **Kind** master or framework, supplier paper (ours). 3 pages, page 3 a scanned signature page.
- **Names printed** **Colverne Marine Engineering Limited** (06421889) — the old name; Halbrook
  Electrical Distribution Ltd.
- **Account** Ardleigh Marine Systems Limited — basis `in the document` (the *same company
  number* and address appear on the name-change letter, which names both companies), `sure` once
  that letter is in hand. On this document alone the honest answer is `known group` / not sure.
- **Execution** signed both; R. Aldbury and D. Marrable, both 9 April 2019.
- **Dates** start 9 April 2019 (stated); rolling until three months' notice; ceased
  1 October 2025 on replacement.
- **Status folder** `4-not-live`. Whole document dead.
- **Trap** the counterparty name is not on the ERP at all. The match must be evidenced, not
  assumed. Its 30-day payment and carriage-at-cost terms are dead.

### `Customers/Ardleigh (ex Colverne)/old files/name change letter.pdf`
- **Kind** letter — change of company name. Signed by them only, H. Sculthorpe, 2 February 2021.
- **Names printed** Ardleigh Marine Systems Limited; Colverne Marine Engineering Limited;
  Halbrook Electrical Distribution Ltd. Company number 06421889 on both names.
- **Account** Ardleigh Marine Systems Limited — `same name`, `sure`.
- **Status folder** `3-live-not-trade` (`4-not-live` acceptable if judged into the superseded
  tree). What matters is that the entity link is recorded with its evidence.
- **Trap** it reads like a novation but is a change of name only — same legal person, same number.
  Recording a transfer would create a second entity node and a wrong family.

### `Customers/Ardleigh (ex Colverne)/MSA drafts/MSA v3.docx`
- **Kind** master — unsigned draft, no tracked changes, no comments, blank signature blocks.
- **Account** Ardleigh Marine Systems Limited — `same name`, `sure`. Draft dated 12 June 2025.
- **Status folder** `5-orders-drafts-duplicates`.
- **Trap** version chaos, part 1: 30 days, six months' notice, £250/£24.00 carriage — none of it
  survived. A clean `.docx` with no tracked changes is still unsigned.

### `Customers/Ardleigh (ex Colverne)/MSA drafts/Copy of MSA v4 clean.docx`
- **Kind** master — unsigned draft, no tracked changes. Draft dated 28 July 2025.
- **Status folder** `5-orders-drafts-duplicates`.
- **Trap** version chaos, part 2, and the subtlest: its terms are *identical* to the executed PDF,
  which tempts a reader to treat it as the agreement. It is still unsigned, and the executed PDF
  is the better copy.

### `Customers/Ardleigh (ex Colverne)/MSA drafts/MSA v4 redline.docx`
- **Kind** master — unsigned draft with **three tracked changes** (payment, carriage, notice) and
  **two comments**. The accepted text equals `Copy of MSA v4 clean.docx`.
- **Status folder** `5-orders-drafts-duplicates`.
- **Trap** version chaos, part 3. The kit renders deletions as `{-…-}` and insertions as `{+…+}`,
  so each paragraph carries both the old and the new figure. Quoting the deleted half as a term is
  the trap.

### `Signed 2025/Ardleigh MSA signed 15-09-25.pdf`
- **Kind** master or framework, supplier paper (ours). 3 pages, page 3 a scanned signature page.
- **Names printed** Halbrook Electrical Distribution Ltd (04118276); **Ardleigh Marine Systems
  Ltd** (06421889) — "Ltd" where the ERP says "Limited".
- **Account** Ardleigh Marine Systems Limited — `same name`, `sure`.
- **Execution** signed both; P. Nettlefold and D. Marrable, both 15 September 2025.
- **Dates** start 1 October 2025 (stated, cl.1.1); rolling until twelve months' notice (cl.12.1).
  **Live.**
- **Relationships** supersedes the 2019 Supply Agreement (cl.2.2); it is the executed version of
  MSA v4.
- **Status folder** `1-governs-trade`.
- **Trap** stored in a completely different top-level folder from its own drafts, so folder
  position is no guide to the family.

### `Customers/Ardleigh (ex Colverne)/Brenlow/Brenlow master 2020.pdf`
- **Kind** master or framework, supplier paper (ours). 3 pages, scanned signature page.
- **Names printed** Brenlow Dockyard Services Limited (07733914); Halbrook Electrical Distribution
  Ltd.
- **Account** `_not-sure`, grouped under "Brenlow Dockyard Services Limited" — or Ardleigh Marine
  Systems Limited on a `known group` basis, **never better than `fairly sure`**.
- **Execution** signed both; R. Aldbury and G. Ravenscar, both 3 November 2020.
- **Dates** start 3 November 2020; rolling until one month's notice (cl.12.1); **ended
  30 April 2026**.
- **Status folder** `4-not-live`.
- **Trap** a sister company where **nothing in the document says so** — it shares only the Marn
  Quay locality, and clause 1.2 expressly excludes group companies. "Same name" or "sure" is
  wrong, and a folder must never be invented from the printed name.

### `Customers/Ardleigh (ex Colverne)/Brenlow/fax 24-03-26.pdf`
- **Kind** letter — notice of termination, **faxed scan**: transmission header, grain, blur and a
  coffee ring. 1 page, image only.
- **Names printed** **Brenlow Dockyard Svcs Ltd** (abbreviated); Halbrook Electrical Distribution
  Ltd.
- **Execution** them only; G. Ravenscar, 24 March 2026.
- **Dates** the master ends **30 April 2026** — in the past.
- **Status folder** `4-not-live`, with the master it terminates.
- **Trap** degraded image, abbreviated name, and a past end date — the mirror image of the Wexbury
  notice.

## Account D — Trentmoor Housing Partnership (HAL-40390)

### `Customers/Trentmoor/THP master agreement 2023 FULL.pdf`
- **Kind** master or framework, customer paper. **42 pages**; page 41 is a scanned signature page.
- **Names printed** **The Housing Partnership (Trentmoor) Limited** (08217640) — a word-order
  variant of the ERP's "Trentmoor Housing Partnership"; Halbrook Electrical Distribution Ltd
  (04118276). **Neither appears before page 4.**
- **Account** Trentmoor Housing Partnership — basis `known group` / `same name` once the
  word-order variant is accepted, corroborated by the Larkhall site agreement, `scan0012.pdf` and
  the Kellerby letter. `fairly sure` (sure once corroborated). **At cheap filing: no name at all.**
- **Execution** signed both; M. Elverstone 5 September 2023, P. Nettlefold 7 September 2023.
- **Dates** start 1 October 2023 (stated, cl.3.1); initial three-year term to 30 September 2026;
  then continues until twelve months' notice (cl.22.1). **Live.**
- **Relationships** Schedule 2 issued separately as the `.xlsx` price matrix (cl.8.2); expressly
  preserves the meter cabinet agreement (cl.26.2); the Larkhall site agreement prevails for those
  Works; carriage varied for Kellerby by the joint letter.
- **Status folder** `1-governs-trade`.
- **Live and dead parts** the Conditions, Schedule 1, Schedule 3 and the Annexes run for the term
  with no separate expiry. **Schedule 2 (Price Matrix 2026) is a separately-lived part:** live to
  31 December 2026, then dead, and its expiry does not end the agreement (cl.4.4, S2.7); on expiry
  clause 8.4 puts prices at list less 22 per cent.
- **Trap — the three-page trap.** Page 1 is a cover sheet, page 2 a contents page, page 3 a
  definitions page where "the Customer" and "the Supplier" are defined by cross-reference to the
  signature page. Inside the cheap ceiling of three pages this document **cannot** be identified.
  It should land in `_no-name-found` (or `_not-sure`) and stay unresolved. Guessing the account
  from the `THP/2023/ELEC-11` reference or the `THP-LEGAL-2023-11` document control string is
  exactly the behaviour this file is built to catch. Secondary trap: 42 pages must be read in
  ranges, and the layered Schedule 2 must be found before the dates are answered.

### `Customers/Trentmoor/Schedule 2 price matrix 2026.xlsx`
- **Kind** schedule or annex (pricing), 28 rows. Not signed; issued under cl.8.2 of the master.
- **Names printed** Halbrook Electrical Distribution Ltd; The Housing Partnership (Trentmoor)
  Limited; the master and its date.
- **Account** Trentmoor Housing Partnership — basis `in the document`, `fairly sure`.
- **Dates** valid 1 January 2026 to 31 December 2026.
- **Status folder** `2-governs-part-of-trade` (a period), filed with the master's tree. Live to
  31 December 2026, then dead; the master runs on.
- **Trap** `.xlsx` is **not a readable type for the kit**, so the pricing schedule the 42-page
  master depends on sits in `_unreadable` with only an inventory row. The account's live/dead-part
  story cannot be completed from the kit's own reading, and the note must say so.

### `Customers/Trentmoor/Larkhall Court site agreement.pdf`
- **Kind** project or programme agreement (site agreement). **5 of 6 pages** — page 5 ends
  "[SIGNATURE PAGE FOLLOWS]".
- **Names printed** The Housing Partnership (Trentmoor) Limited; Halbrook Electrical Distribution
  Ltd. Reference THP/2026/SITE-04.
- **Account** Trentmoor Housing Partnership — `same name` (word-order variant), `fairly sure`.
- **Execution** **can't tell — the signature page is missing from the file.** It is in the pile as
  `scans to file/scan0031.pdf`.
- **Dates** start 11 March 2026 (stated); ends on practical completion or 31 December 2027,
  whichever is earlier (cl.2.2).
- **Status folder** `2-governs-part-of-trade` once the detached signature page is matched to it;
  `unsure` if it is read alone (signature page missing, so signing is unknown).
- **Trap** a complete-looking agreement whose execution cannot be established from the file. It
  also flips two commercial answers for the Works: payment 30 days from month end and free
  carriage at any value, against the master's 60 days and £200 threshold.

### `scans to file/scan0031.pdf`
- **Kind** detached signature page — **page 6 of 6** of the Larkhall Court site agreement,
  reference THP/2026/SITE-04. 1 page, image only, **low contrast and noisy**, skewed.
- **Names printed** The Housing Partnership (Trentmoor) Limited; Halbrook Electrical Distribution
  Ltd.
- **Execution** signed both; M. Elverstone 11 March 2026, P. Nettlefold 13 March 2026.
- **Status folder** filed with the site agreement's tree; the *link* matters more than the folder
  (`5-orders-drafts-duplicates` is acceptable for an incomplete copy).
- **Trap** washed-out image three directories away from the body it belongs to. Card question 9
  requires the reader to say which document it belongs to; the shared reference is the evidence.
  It also carries the date of last signature, which the body does not.

### `Customers/Trentmoor/scan0012.pdf`
- **Kind** **two documents in one file.** Pages 1–2: a Mutual Non-Disclosure Agreement dated
  14 June 2022, scanned, signed both. Pages 3–5: a Supply Agreement (Meter Cabinets) dated
  4 July 2022, native text, signed both.
- **Names printed** The Housing Partnership (Trentmoor) Limited; Halbrook Electrical Distribution
  Ltd.
- **Account** Trentmoor Housing Partnership — `same name` (word-order variant), `fairly sure`.
- **Dates** NDA 14 June 2022 to 13 June 2027 (five years). Meter cabinets: dated 4 July 2022,
  starts 1 August 2022, rolling until six months' notice.
- **Relationships** the meter cabinet agreement is expressly preserved by cl.26.2 of the 42-page
  master and excluded from its Schedule 1 by S1.13.
- **Status folder** `2-governs-part-of-trade` for the meter cabinet agreement (a defined product
  set that is plainly not everything). The NDA part is `3-live-not-trade` and must be recorded
  separately in the note and in the didn't-fit list.
- **Live and dead parts** NDA live to 13 June 2027, does not govern trade. Meter cabinet agreement
  live; payment 45 days from invoice date; carriage included.
- **Trap** one file, two unrelated agreements, and the kit's unit of work is the file. Every card
  and form field is single-valued, so the conflict must be recorded in question 10 and section K,
  not resolved silently in favour of one. Mixed mode as well: pages 1–2 are pictures, 3–5 native —
  and the filename says "scan" for a file that is mostly not a scan.

## Shared, unmatched and supplier-side

### `Misc/Kellerby Interchange joint letter.pdf`
- **Kind** amendment or side letter — a three-party site arrangement.
- **Names printed** Halbrook Electrical Distribution Ltd; Sturmore Rail Group Ltd; The Housing
  Partnership (Trentmoor) Limited.
- **Account** **SHARED: Sturmore Rail Group *and* Trentmoor Housing Partnership.** Copied into
  both folders and marked shared; two rows in the global CSV for one original. `same name`, `sure`
  (Sturmore) and `fairly sure` (Trentmoor word-order variant).
- **Execution** signed by all three; P. Nettlefold and T. Vessey 20 April 2026, M. Elverstone
  22 April 2026.
- **Dates** 20 April 2026 until practical completion of the Kellerby works, programmed
  30 June 2027.
- **Status folder** `2-governs-part-of-trade` in both accounts.
- **Trap** one document, two accounts, and a partial variation: it changes carriage for one site
  under both masters and touches nothing else (clause 6 says so).

### `Misc/Fenwold master.pdf`
- **Kind** master or framework, supplier paper (ours). 3 pages, scanned signature page.
- **Names printed** Fenwold Aggregates Limited (09918233); Halbrook Electrical Distribution Ltd.
- **Account** `_not-on-the-list`, grouped under "Fenwold Aggregates Limited". No ERP row matches.
- **Execution** signed both; R. Aldbury 17 January 2024, K. Ollerton 19 January 2024.
- **Dates** start 1 February 2024; rolling until six months' notice. Live on its face.
- **Status folder** holding folder only; no status is assessed for an unmatched document at cheap
  filing.
- **Trap** a live, properly executed, all-purchases master for a company on **no** ERP row. It
  must not be forced into the nearest account and no folder may be created from its name.

### `Misc/Cadmere framework (we buy).pdf`
- **Kind** master or framework — **supplier-side paper: we are the customer.**
- **Names printed** Cadmere Cable Works Limited (03771205) as "the Supplier"; **Halbrook
  Electrical Distribution Ltd (04118276) as "the Customer"**.
- **Account** `_not-on-the-list`. The ERP extract is a customer list and holds no supplier row;
  the side is supplier, and the main session should put the side question to the user.
- **Execution** signed both; S. Bemrose 1 February 2024, A. Whitcombe 5 February 2024.
- **Trap** the sides are reversed. A filer keying on the word "Customer", or seeing a
  familiar-looking framework in a customer pile, will file Cadmere as a customer. Our own entity
  list is what makes the reversal visible.

## Junk

### `00 TO FILE/new doc 2.pdf`
Zero bytes with a `.pdf` extension. `_needs-reading`, with an inventory row. Must not crash
preparation and must not be dropped.

### `00 TO FILE/contract notes.pdf`
Plain text saved with a `.pdf` extension; PDF parsing fails. `_needs-reading`, with an inventory
row. Its content names six companies and five dates and must never be used as evidence.

---

# Part 2 — what governs each account today (7 September 2026)

## Sturmore Rail Group (HAL-40118 + stream HAL-40119)

**Governs trade:** the Master Supply Agreement dated 22 February 2021 (SRG/PROC/2021/114), as
amended by Amendment No. 1 dated 6 June 2023. Commenced 1 March 2021; initial three-year term,
then year to year; no notice served, so live.

| | |
| --- | --- |
| **Payment** | 60 days from the end of the month in which the invoice is dated |
| **Freight** | free of carriage on orders of £250 net or more; below that £22.50. Exception: free at any value to the Kellerby Interchange compound until practical completion (programmed 30 June 2027) |
| **Notice** | six months' written notice, expiring at any time (cl.2.2) |

1. **What payment term applies to an invoice dated today?** 60 days from the end of the month —
   not the 45 days printed in the master.
   *Amendment No. 1, cl.1.1: "The Supplier shall be paid within 60 days from the end of the month
   in which the invoice is dated."*
2. **Does condition 14 on the back of PO 88231 displace the master?** No. It is boilerplate
   precedence wording on a single order; the master is signed by both and orders the same conflict
   the other way.
   *PO 88231 reverse, cl.14: "These Conditions apply to the exclusion of all other terms and
   prevail over any master agreement"; master cl.11.1: "this Agreement prevails, then the Order,
   then the Supplier's conditions of sale".*
3. **Is the carriage-free threshold £250 or £500?** £250. The £500 figure exists only in an
   unsigned draft.
   *Master cl.8.1: "Delivery is free of carriage on Orders with a net value of GBP 250 or more";
   Amendment No. 2 draft, cl.2.1: "This draft has not been agreed and creates no obligation unless
   and until it is signed by both parties."*

## Wexbury Utilities plc (HAL-40204)

**Governs trade:** the Framework Agreement dated 12 May 2022 (WU/2022/EL-07). Signed by Wexbury
alone, but confirmed in writing by Wexbury on 4 September 2024 and treated as binding by our own
notice of 14 August 2026. Live today; **ends 14 February 2027.** The 2026 rebate letter runs
alongside it for that calendar year only.

| | |
| --- | --- |
| **Payment** | 60 days from the end of the month of invoice (cl.6.1) — the 90 days in `Signed final.pdf` is a draft figure |
| **Freight** | delivery included in the price for call offs of £150 net or more; below that carriage at our published rate (cl.7.1) |
| **Notice** | six months for convenience (cl.3.2) — already served, expiring 14 February 2027 |

1. **Is the framework executed?** By Wexbury only; our block is blank — no name, no title, no
   date. The gap is bridged by conduct and by the customer's own confirmation, not by a signature.
   *Wexbury letter, 4 September 2024: "We confirm that we are trading under the terms of the
   Framework Agreement dated 12 May 2022".*
2. **When does trading under the framework end?** 14 February 2027. It is live today; the
   termination letter is prospective.
   *Notice of 14 August 2026: "The six month notice period runs from the date of this letter and
   the Agreement will therefore end on 14 February 2027."*
3. **Does the 2026 rebate letter set the trading terms?** No — 1.75% above £400,000 for the 2026
   calendar year and nothing else.
   *Rebate letter, para 4: "This letter sets the rebate for the 2026 calendar year only. It does
   not vary the prices, the payment term, the carriage arrangement or any other trading term".*

## Ardleigh Marine Systems Limited (HAL-40311)

**Governs trade:** the Master Supply Agreement dated 15 September 2025 (AMS/2025/MSA), commenced
1 October 2025, rolling, live. It replaced the 2019 Supply Agreement made in the customer's former
name. Brenlow Dockyard Services Limited is a separate counterparty whose own master died on
30 April 2026.

| | |
| --- | --- |
| **Payment** | 45 days from the date of the invoice (cl.6.1) |
| **Freight** | free of carriage on orders of £300 net or more; below that £28.00 (cl.7.1) |
| **Notice** | twelve months' written notice for convenience (cl.12.1) |

1. **Is the ERP counterparty the same legal person as the 2019 counterparty?** Yes — a change of
   name only, same company number 06421889, no transfer of business.
   *Name change letter, 2 February 2021: "changed its name from Colverne Marine Engineering
   Limited to Ardleigh Marine Systems Limited with effect from 25 January 2021".*
2. **Which document governs, and from when?** The 2025 master, from 1 October 2025.
   *Executed MSA cl.2.2: "This Agreement supersedes and replaces the Supply Agreement dated
   9 April 2019 between the parties with effect from the Commencement Date".*
3. **Is anything live for Brenlow Dockyard Services?** No, and nothing in any document puts
   Brenlow inside the Ardleigh group.
   *Fax of 24 March 2026: "In accordance with clause 12.1 the Agreement will end on 30 April
   2026"; Brenlow master cl.1.2: "No parent, subsidiary or associated company of the Customer may
   order under it."*

## Trentmoor Housing Partnership (HAL-40390)

**Governs trade:** the Master Supply Agreement dated 5 September 2023 (THP/2023/ELEC-11),
commenced 1 October 2023; the three-year initial term runs to 30 September 2026 and it then
continues until twelve months' notice. Live. Three live overlays sit alongside it — the Supply
Agreement (Meter Cabinets) dated 4 July 2022 for that product set, the Larkhall Court Site
Services Agreement dated 11 March 2026 for those Works, and the Kellerby joint letter for that
site's carriage. The 2022 NDA is live but does not govern trade.

| | |
| --- | --- |
| **Payment** | 60 days from the end of the month (cl.9.1); **30 days** from month end for Larkhall Court Works invoices (site agreement cl.4.2, which prevails for the Works); 45 days from invoice date for meter cabinets |
| **Freight** | free to Schedule 3 sites on orders of £200 net or more, otherwise carriage at cost (cl.7.3); free at any value to the Larkhall Court and Kellerby Interchange compounds; included in the meter cabinet prices |
| **Notice** | twelve months after the initial term (cl.22.1); the site agreement runs on thirty days', the meter cabinet agreement on six months' |

1. **What price applies to an order placed on 5 January 2027 if no new Schedule 2 has been
   issued?** List price less 22 per cent. Schedule 2 expires on 31 December 2026 and its expiry
   does not end the agreement.
   *Master cl.8.4: "If no Schedule 2 is in force, prices are the Supplier's published list price
   less 22 per cent until a replacement Schedule 2 is agreed."*
2. **What payment term applies to a Larkhall Court invoice?** 30 days from the end of the month,
   not the master's 60.
   *Site agreement cl.6.2: "this Agreement prevails in respect of the Works, and the Master
   Agreement prevails for everything else".*
3. **Are meter cabinets bought under the 2023 master?** No — they are carved out and run under the
   2022 agreement inside `scan0012.pdf`.
   *Master cl.26.2: "This Agreement does not affect the Supply Agreement (Meter Cabinets) dated
   4 July 2022 between the parties, which continues in force".*

## Ravenhead Grid Services Ltd (HAL-40566)

**Governs trade:** nothing. There is no document in the pile for this account. Payment, freight
and notice are all `not found`.

1. **What should the kit produce?** An account folder named exactly as the ERP row, empty, with a
   README saying nothing is filed there, and the row present in the account register and in
   `INDEX.md`.
2. **What would be wrong?** Omitting the row because it has no files, or letting the unmatched
   Fenwold or Brenlow paper drift into it to make the folder look populated.

---

# Part 3 — every trap and the expected behaviour

| # | Where | Trap | Expected behaviour |
| --- | --- | --- | --- |
| T01 | `THP master agreement 2023 FULL.pdf` | 42-page master; cover sheet, contents and a definitions page with no party names in full; parties on page 4 and page 41 | **Not resolvable within the cheap 3-page budget.** `_no-name-found` (or `_not-sure`), identity unresolved, no full reader triggered. Guessing the account from the `THP/…` reference or the `THP-LEGAL` document control string is the failure. Full analysis resolves it from page 4 and the signature page |
| T02 | Amendment 1 × 3 | one amendment in three files: two byte-identical PDFs in different folders, plus an image-only scan | one instrument, one best copy (native PDF in the account folder); the others to `5-orders-drafts-duplicates` marked "duplicate of". The identical sha256 proves the first; the scan is matched by content |
| T03 | `scan0007.pdf` | page rotated 90°, no native text | read as a picture; still one page against the budget; identified despite orientation |
| T04 | `Signed final.pdf` | filename lies: an unsigned DRAFT-watermarked document, with different terms | execution read from the page: unsigned. `5-orders-drafts-duplicates`. Its 90 days / twelve months never reach the account's terms |
| T05 | `Framework 12-05-2022.pdf` | master signed by one party only; our block blank; later confirmation and notice | `them only` with the blank block quoted. Status argued, not assumed. A didn't-fit entry for one-sided execution (`missing_allowed_value`) |
| T06 | Ardleigh MSA v3 / v4 clean / v4 redline / executed | version chaos; only the redline has tracked changes; the executed PDF sits elsewhere | all three `.docx` unsigned → `5-orders-drafts-duplicates`; the executed PDF governs; deleted `{-…-}` text is never quoted as a term |
| T07 | `Brenlow master 2020.pdf` | sister company where nothing in the document says so; cl.1.2 says the opposite | basis `known group`, confidence no better than `fairly sure`, or `_not-sure` grouped by name. Never "same name", never "sure", never a new folder |
| T08 | Colverne / Ardleigh | counterparty renamed; ERP holds the new name, the master the old | matched on basis `in the document` using the shared company number and the name-change letter; recorded as a change of name, not a novation |
| T09 | `scan0012.pdf` | one PDF holding two unrelated agreements; mixed scanned and native pages | the conflict recorded (card q10, form section K), not resolved silently; the live meter-cabinet agreement drives the folder; the live NDA reported separately |
| T10 | Larkhall site agreement + `scan0031.pdf` | signature page missing from one file, present as a loose scan three folders away | body reads `can't tell (signature page missing)`; the loose page names its document on the evidence of the shared reference; once linked, `2-governs-part-of-trade`, otherwise `unsure` |
| T11 | `fax 24-03-26.pdf` | fax header, grain, blur and a coffee ring | read as a picture and identified despite the damage; "Svcs" matched to the full name |
| T12 | `scan0031.pdf` | low-contrast, noisy scan | still read as a picture; both signature dates recovered — they are not in the body document |
| T13 | `Schedule 2 price matrix 2026.xlsx` | the master's Schedule 2 is a spreadsheet the kit cannot read | inventory row and `_unreadable`, never a silent omission; the note says the pricing schedule could not be read and that its 31 December 2026 expiry is the separately-lived part |
| T14 | `RE_ RE_ amendment.msg` | an email forwarding an amendment | listed as unreadable **with** an inventory and report row; its fragments are not evidence |
| T15 | `PO88231 northern depot.pdf` | reverse-side conditions claim precedence over any master | `5-orders-drafts-duplicates` as a single transaction; the precedence wording is expressly ignored |
| T16 | Brenlow fax (past) and Wexbury notice (future) | two termination letters, one already expired, one not | Brenlow master `4-not-live` from 30 April 2026; Wexbury framework stays live in `1-governs-trade` with the 14 February 2027 end date recorded |
| T17 | across the pile | "Ltd" vs "Limited"; "Brenlow Dockyard Svcs Ltd"; the trading name "Wexbury Power Networks"; "The Housing Partnership (Trentmoor) Limited" in a different word order | every variant gets a basis and a confidence and is appended to `inputs/entity-map.csv` for the user; suffix and word-order variants may be `same name`, a bare trading name is `known group` at best |
| T18 | HAL-40118 / HAL-40119 | two ERP rows differing only by a suffix | the stream shares the main folder and gets a README pointing to it, unless a document names the stream — PO 88231 and Appendix A both do; the run says which rows were treated as one |
| T19 | `new doc 2.pdf`, `contract notes.pdf` | zero-byte PDF; text file with a `.pdf` extension | neither crashes preparation; both get inventory rows and land in `_needs-reading`; neither is used as evidence |
| T20 | `Account notes (internal).docx` | an internal playbook stuffed with numbers that look like terms | `6-business-practice`, shown apart, never cited as evidence of a contractual term |
| T21 | `rebate 2026.pdf` | rebate letter covering a calendar year only | `2-governs-part-of-trade`; section B rule 6 keeps a period-only letter out of `1-governs-trade` |
| T22 | `Kellerby Interchange joint letter.pdf` | one signed document naming companies from two accounts | copied into both folders, marked shared; one row per document/account pair, so the corpus has more rows than originals |
| T23 | `IMG_2291.jpg` | phone photograph of a signed one-page letter, off square | read as a picture, identified as a signed acceptance, and used as the link between the trading name and the ERP name |
| T24 | `Fenwold master.pdf` | live, executed, all-purchases master for a company on no ERP row | `_not-on-the-list` grouped by name, flagged for the user; no folder is ever created from a name found in a document |
| T25 | `Cadmere framework (we buy).pdf` | supplier-side paper in a customer pile; our company is "the Customer" | recognised as the wrong side; no customer row matches, so `_not-on-the-list`, and the side question goes to the user |
| T26 | 2016 Sturmore agreement | our own former name is the signatory | recognised as ours from `inputs-our-entities.csv`, not turned into a third company; the 2021 master names the same former entity when it supersedes |
| T27 | Amendment 2 draft, v4 redline, `Signed final.pdf` | three documents carrying plausible but non-binding figures — 75/90 days, £400/£500, 30 days, six months, £250/£24.00 | none of these reaches an account's current terms; every reported term traces to a signed, live instrument |
| T28 | HAL-40566 Ravenhead Grid Services Ltd | an ERP account row with no documents | the folder exists, named exactly as the row, README saying nothing is filed; the row is not dropped and unmatched paper is not swept into it |
