# Review_Table_Light: fourteen questions for filing by script

Review_Table_Light is the export that a script turns into account folders and status folders.
No model reads a contract at this stage. The only model call is for customer names that
neither match an ERP account exactly nor have a row in `inputs/entity-map.csv`; the model sees
that list of names and the ERP account names, nothing else, and its suggestions land in the
entity map as provisional rows for the user to confirm. `/analyse` remains the optional next
stage for the accounts the user picks, and it uses the separate full Review_Table.

What the script needs from each row, in order of importance: the nature of the instrument,
whether it is current, what supply it covers, and which customer contracts. Reference numbers
are rare in real piles; the Reference column is kept because it costs little and the script
uses a reference only when it finds one. Dates are the anchor instead: the date a document
bears links a draft to its executed version, an amendment or notice to its parent, and a
superseding agreement to the one it replaces.

Keep the export beside the ERP and the original contracts:

```text
corpus/
  ERP.xlsx
  Review_Table_Light.xlsx
  Review_Table.xlsx            (optional, for /analyse)
  ...contract files...
```

CSV or XLSX, one sheet, one row per file, row 1 holding the column names below. Column names
may be written with spaces, and the review tool may append the question text to them; the
importer keys on the leading number and name. An empty cell, None and an em dash all mean no
answer. Playbooks and other internal guidance are not sent to the review tool; they are filed
from a local list into the business practice folder (to do).

Use [the invented example](../inputs/Review_Table_Light.example.csv) as a header and format
guide only. Its rows are invented and must not be imported into a real corpus.

## Overview: the light sort on one page

`/sort <pile>` is the cheap filing stage. Its inputs are the ERP extract (the only source of
account folder names), the fourteen-column Review_Table_Light that the review tool exports after
answering the questions below on every file, the tool's error workbook, and two local lists:
`inputs/our-entities.csv` (our own contracting entities, required) and, optionally,
`inputs/business-practice.csv` (playbooks). `scripts/sort_light.py` imports the export, takes
the as-at date from the Status question, matches each customer entity to an ERP account by
company number, normalised name and the entity map, links children to parents by the dates
they quote, detects byte-identical copies, drafts, copies and detached signature pages, applies
section B of `stage1/sorting-rules.md` to the answers and writes one folder per ERP account with
the status folders inside, plus `INDEX.md`, `CORPUS.csv`, `ACCOUNTS.csv` and
`work/logs/sort.csv`. Every file gets a row. Names it cannot match go to holding folders grouped
by name, with no status. Nothing is verified against the paper, and the report says so.

The one model step is a names-only turn. `sort_light.py --unmatched` prints the customer names
the script could not match, the ERP account list, any entity-map row it could not apply and
why, and hints (a name that is also the supplier entity on other rows is probably ours). The
model decides each name under section A and writes the decision with `sort_light.py --decide`,
which validates the account against the ERP, the basis and the confidence, caps known group at
fairly sure, and never overwrites a user decision. The model sees no contract text. What the
design does not do: it does not infer affiliate coverage from group membership (a sister
company is `_not-sure` until a person decides), it does not treat a missing answer as an
absence in the contract, and it does not judge. The governing judgment belongs to `/analyse`,
or to `/analyse top` for the accounts in ERP_Top.

Where to look: `scripts/sort_light.py` (the script), `.claude/skills/sort/SKILL.md` (the steps
the model follows), `stage1/sorting-rules.md` (sections A and B), `tests/test_sort_light.py` and
`tests/test_top.py` (behaviour on the invented sample), and `eval/messy/score_light.py` with
`eval/messy/expected/` (the messy-pile key, for evaluators only, never for a runner).

## Column types in the review tool

The review tool offers free text (a model summary), classify (one of a fixed list), date (one
date), verbatim (words copied from the document), currency and number. Use them like this:

| type | columns |
| --- | --- |
| classify | Instrument, Supply coverage, Group mechanism, Signed, Status, Relation to parent |
| date | Document date, End date |
| verbatim | Parent agreement |
| free text | Title, Reference, Customer entity, Additional customer entities, Supplier entity |

A classify field exports only its label, so the closed questions do not ask for a reason, and
an unanswered one exports as an em dash: require an answer so that None is chosen. A date
field holds one date and is blank when the document states none; the script reads a blank End
date together with Status. Replace `[AS-AT DATE]` in the Status question with the date of the
run, in the form 2026-09-10, every time the table is generated; the model's own sense of today
cannot be trusted and the script needs the same date.

## What "governs supply" means

A document governs trade, and so belongs in folders 1 or 2, when it sets the terms on which
goods, services or software are supplied: what may be ordered, delivery, warranty, price and
payment. Price schedules and amendments that form part of those terms belong to the governing
tree. A rebate, bonus, growth incentive, marketing contribution or special-price letter that
sits beside those terms and varies the commercial outcome does not govern, even when it applies
to every purchase. It is filed as a live document that does not govern trade. The DCG standard
says the same of its family C13: such letters vary pricing under whatever else governs.

Three things are asked separately and must never be merged: what kind of instrument it is,
which group entities can use it, and what supply it covers. A global framework that covers
one product line is a normal combination.

## Columns and permitted answers

| column | type | permitted answers |
| --- | --- | --- |
| File name | metadata | exact filename with extension, supplied by the export |
| Title | free text | short normalised title |
| Reference | free text | the document's own reference number, or None |
| Document date | date | the date the document bears; blank if none |
| Customer entity | free text | one legal name as printed, with company number if printed, or Not found |
| Additional customer entities | free text | None, or legal names one per line |
| Supplier entity | free text | one legal name as printed, with company number if printed, or Not found |
| Instrument | classify | Global master agreement; Master or supply agreement; Local participation agreement; Standard terms or account form; Project agreement or statement of work; Schedule or exhibit; Amendment or side letter; Pricing or rebate letter; Notice letter; Purchase order or call-off; Purchase order or call-off carrying standard terms; Quote or acknowledgement; Quote or acknowledgement carrying standard terms; NDA, MOU or letter of intent; Guarantee or security; Certificate or evidence; Other overlay; Mixed; Other; Unclear |
| Supply coverage | classify | All supply between the parties; Substantially all supply; Part of supply; Named division or site; Varies commercials only; No supply coverage; Unclear |
| Group mechanism | classify | Contracting for affiliates; Adoption agreement; Entity schedule; Ordering entitlement; None; Unclear |
| Signed | classify | Signed by all parties; Signed by one party; Unsigned; Draft; Signature not established |
| Status | classify | Current; Expired; Terminated; Not yet effective; Unclear |
| End date | date | the date the document's own effect ends; blank if none is stated |
| Relation to parent | classify | None; Forms part of; Accedes to; Placed under; Agreed under; Governed by; Amends; Extends; Renews; Supersedes; Terminates; Varies; Confirms |
| Parent agreement | verbatim | the words in this document that identify the parent: title, date and any reference |

## The questions

Each question is self-contained because the review tool applies no common instruction.

### 1. Title

```text
Answer from this document only; never use the filename. Give a short normalised title that
says what this document is, based on its printed title and its content, for example Master
Supply Agreement, Amendment No. 2 to Master Supply Agreement, Local Participation Agreement,
Rebate Letter 2026, Purchase Order, Notice of Termination, Mutual Non-Disclosure Agreement.
```

### 2. Reference

Unchanged from the first export: the document's own contract, agreement or reference number
if one is printed, never the numbers of agreements it refers to; None if there is none.

### 3. Document date

```text
Answer from this document only. Give the date this document bears: the date it states it is
made or dated, or the latest signature date if there is no dated line. Not its commencement
or effective date, which can be later. If the document bears no date, leave the answer blank.
```

### 4. Customer entity

```text
Answer from this document only. Give the one legal entity that contracts as the customer,
buyer or purchaser: the customer entity that signs, or where several customer entities are
parties, the first named. Give the full legal name exactly as printed in the parties clause or
signature block, including suffixes such as Ltd, GmbH or Inc. If a registered company number
is printed for that entity, add it after the name in the form (No. 12345678). This is the
contracting party, not the affiliates, sites or divisions permitted to use the agreement. If
no customer entity can be identified, answer Not found.
```

### 5. Additional customer entities

```text
Answer from this document only. Apart from the entity you gave as the customer entity, list
every other legal entity that is itself a contracting party on the customer side, one full
legal name per line exactly as printed, with its registered company number in the form
(No. 12345678) where printed, including co-signing group companies and entities listed as
parties in a schedule of signatories. Exclude affiliates, sites or divisions that are only
permitted to use the agreement. If there are none, answer None.
```

### 6. Supplier entity

```text
Answer from this document only. Give the one legal entity that contracts as the supplier,
seller or provider: the supplier entity that signs, or where several are parties, the first
named. Give the full legal name exactly as printed in the parties clause or signature block,
including suffixes, and its registered company number in the form (No. 12345678) where
printed. This is the contracting party, not supplier group companies permitted to supply under
it. If none can be identified, answer Not found.
```

### 7. Instrument

```text
Answer from this document only. Classify the document by what it does, not by its title, as
exactly one of the values below.
Global master agreement: a negotiated agreement of standing supply terms that other legal
entities can adopt, through a participation, adoption, accession or joinder mechanism, an
affiliate or entity schedule, or the parties contracting on behalf of their affiliates.
Master or supply agreement: standing terms between two contracting entities under which the
customer places repeated orders, including supply, sales, framework and blanket order
agreements, with no mechanism for other entities to adopt it.
Local participation agreement: a local participation, participation, implementation,
accession or joinder agreement or country addendum applying another agreement to one entity,
site or territory.
Standard terms or account form: terms of sale or purchase, online terms, or a customer
account application form that binds the customer to standard terms.
Project agreement or statement of work: supply terms for one defined project, programme,
works package or statement of work.
Schedule or exhibit: a price list, product schedule, specification, service level or other
schedule, exhibit or annex that the parent agreement incorporates as part of its supply terms
and that is issued or updated on its own.
Amendment or side letter: a document agreed by the parties that amends, varies, extends,
renews or restates the text of another agreement.
Pricing or rebate letter: a letter or short agreement granting or varying a rebate, bonus,
growth incentive, marketing contribution, special price or payment term for a period or
project, standing beside the supply terms rather than forming part of them.
Notice letter: a letter from one party giving notice of termination, non-renewal, extension,
a price change or a change of name, or confirming that trading continues under an agreement,
without amending the agreement's text.
Purchase order or call-off: a single order with no standard terms printed, attached or
incorporated by reference.
Purchase order or call-off carrying standard terms: a single order that prints, attaches or
incorporates standard terms of purchase.
Quote or acknowledgement: a quotation, tender response or order acknowledgement with no
standard terms.
Quote or acknowledgement carrying standard terms: one that prints, attaches or incorporates
standard terms of sale.
NDA, MOU or letter of intent: confidentiality, memorandum of understanding, heads of terms or
letter of intent that does not itself set supply terms.
Guarantee or security: a guarantee, bond, letter of credit or charge.
Certificate or evidence: an acceptance certificate, declaration of conformity, insurance
certificate or similar record with a validity period.
Other overlay: data processing, code of conduct, EDI, quality or similar side terms.
Mixed: distinct instruments bound into one file.
Other. Unclear.
```

### 8. Supply coverage

```text
Answer from this document only. Governing supply means setting the terms on which goods,
services or software are supplied: what may be ordered, delivery, warranty, price and
payment. Choose exactly one of the values below.
All supply between the parties: the document states that all purchases, all orders or all
supply between the customer and the supplier are made under it, or it sets the standing terms
for whatever the customer buys from the supplier. A definition of Products, or a schedule of
product categories, does not make the coverage partial when the scope or ordering clause
applies to all purchases.
Substantially all supply: the document limits itself to a listed product set, bill of
materials or catalogue, and describes or treats that set as all or nearly all of what the
customer buys from the supplier.
Part of supply: the document expressly limits itself to one project, site, programme or works
package, or to a product subset while other purchases from the supplier are, or could be,
made under different terms.
Named division or site: the document applies only to purchases by a named division, business
unit or group of sites of the customer.
Varies commercials only: the document does not itself set supply terms; it grants or changes
a rebate, bonus, incentive, price or payment term under terms that govern elsewhere.
No supply coverage: the document does not concern the supply of goods, services or software,
for example an NDA, MOU, guarantee, certificate or data processing agreement.
Unclear: the reviewed content does not establish which applies.
For an amendment, schedule, notice or letter under another agreement, answer for the change
it makes. Decide from the scope, ordering, delivery, price and payment clauses and any product
or site schedule, not from the title. A clause saying this document prevails over purchase
orders does not by itself mean all supply.
```

### 9. Group mechanism

```text
Answer from this document only. Does this agreement reach legal entities beyond the two
contracting parties, and by what mechanism? This is separate from what supply is covered: an
agreement can be open to a whole group while covering one product line. Choose exactly one
of the values below.
Contracting for affiliates: a party contracts on behalf of its affiliates, subsidiaries or
group companies so that they are bound or entitled without further signature.
Adoption agreement: affiliates join by signing a participation, adoption, accession,
implementation or joinder agreement, or a template for one is attached or referred to.
Entity schedule: a schedule or appendix lists the affiliates, sites, depots or divisions
covered.
Ordering entitlement: affiliates or bodies under the customer's control may place orders
under it without a separate agreement.
None: the agreement is limited to the two named entities or contains no such wording.
Unclear: the reviewed content does not establish the position.
```

### 10. Signed

```text
Answer from this document only. Choose exactly one of the values below.
Signed by all parties: a visible signature, electronic signature certificate or completion
statement for every contracting party.
Signed by one party: visible signature for one side only.
Unsigned: signature blocks are visible and empty for every party.
Draft: tracked changes, comments, a watermark, a version label or the word draft are present.
Signature not established: the signature page is missing, illegible, referred to but not
present, or not among the reviewed content. A typed name is not a signature, and the absence
of a signature from the reviewed content does not mean the document is unsigned.
```

### 11. Status

```text
Answer from this document only, as at [AS-AT DATE]. Choose exactly one of the values below.
Current: the document has commenced and either its fixed term has not ended or it continues
on a rolling, evergreen, automatic renewal or until-terminated basis. Treat evergreen and
rolling terms as Current unless this document records termination.
Expired: a fixed end date has passed and no extension appears in the reviewed content.
Terminated: this document records its own termination or its replacement by another
agreement.
Not yet effective: commencement depends on a date after [AS-AT DATE] or on a condition not
shown as met.
Unclear: dates are missing from the reviewed content, or parts of the document have different
terms.
Do not assume anything about amendments or terminations in other documents.
```

### 12. End date

```text
Answer from this document only. Give the date on which this document's own effect ends: the
end of a fixed term, the end of the period a letter or schedule covers, the date on which a
termination or notice takes effect, or the delivery date of an order. Where the end is the
earlier of a date and an event, give the date. If the document continues until terminated,
renews automatically with no fixed end, ends only on an undated event such as practical
completion, or states no end, leave the answer blank.
```

### 13. Relation to parent

```text
Answer from this document only. If this document sits under, forms part of, or alters another
agreement, choose the relation that describes it; otherwise choose None.
Forms part of: a schedule, exhibit or annex of the parent.
Accedes to: a participation or joinder under a global master.
Placed under: an order, call-off, quote or acknowledgement issued under an agreement.
Agreed under: a project agreement or statement of work under a master.
Governed by: standard terms incorporated by reference.
Amends, Extends, Renews, Supersedes, Terminates: the effect on the parent's text or term.
Varies: a pricing, rebate or incentive letter that changes the commercial outcome under the
parent without amending its text.
Confirms: a letter confirming that trading continues under the parent.
None: the document stands alone.
```

### 14. Parent agreement

```text
Copy from this document the words that identify the agreement it sits under, forms part of, or
alters: its title, its date and any reference number, as printed in the recital, definition or
clause that refers to it. Where more than one agreement is referred to, copy the principal one
first. Do not say whether that agreement exists elsewhere. Leave the answer blank if the
document stands alone.
```

## How the script files from these answers

The output is one folder per ERP account, and inside it the status folders of
`stage1/sorting-rules.md` section B: `1-governs-trade`, `2-governs-part-of-trade`,
`3-live-not-trade`, `4-not-live`, `5-orders-drafts-duplicates`, `6-business-practice` and
`unsure`. Every file gets a row, holding folders keep unmatched names, and byte-identical copies
are detected by hash. The script records the export's hash and date and the as-at date at
import. The as-at date is read from the Status question's header ("As at 2026-09-09"), so the
Current answers and the date they were given as at travel together; `--as-at` overrides it with
a warning, and without either the export file's date is used and said.

1. **Account.** Customer entity is matched to an ERP account by company number where both
   sides have one, then by name after normalising case, punctuation and Ltd, Limited, plc and
   Inc, then through the entity map. A customer entity that is one of our own entities means the
   sides are reversed: the row goes to a holding folder under the supplier's name. Anything else
   goes to the model once, as names only, and comes back as entity-map rows written through
   `--decide` with `decided_by=claude`; a row whose account is not an ERP row, or whose basis is
   not one of the three permitted, is reported as ignored, never silently dropped. A name mapped
   with confidence `not sure` stays in `_not-sure`. Each Additional customer entity that matches
   receives a copy of the document in its own account; unmatched ones are flagged on the row,
   not dropped. The import also prints the most frequent supplier and customer entities and,
   with `inputs/our-entities.csv`, whether they fit the side.
2. **Same document, several files.** Byte-identical files are copies. Rows in one account with
   the same family of instrument that share a reference, or a title, are candidate versions of
   one document; they are treated as one instrument when their references agree or, without a
   reference on both, when their titles agree. A Draft dated on or before the executed version
   goes to folder 5 as its draft; a scanned or image copy of a signed version goes to folder 5
   marked as a copy, the best copy being the one with the strongest Signed answer and native
   text. A one- or two-page signed copy beside a much longer executed body of the same
   instrument is its signature page or a partial copy: it goes to folder 5 and the body carries
   the execution that page shows, with a note.
3. **Instrument gate.** Only Global master agreement, Master or supply agreement, Local
   participation agreement, Standard terms or account form, Project agreement or statement of
   work, Schedule or exhibit and Amendment or side letter can reach folders 1 or 2.
4. **Current or not.** When End date holds a date, the script compares it with the as-at date.
   When it is blank, the Status label decides, and Current with no end date means continuing.
   A child that has ended goes to folder 4 whatever its parent does.
5. **Governing instruments.** Current: folder 1 for All supply between the parties and
   Substantially all supply; folder 2 for Part of supply and Named division or site. Ended:
   folder 4. Unsigned without a signed version, or Draft without one: unsure. Signature not
   established routes nothing by itself; it is flagged for `/analyse`. When an account has no
   folder 1 candidate but exactly one current master or supply agreement answering Part of
   supply, that agreement goes to folder 1 with a scope note, as rule 6 provides.
6. **Non-governing instruments.** Pricing or rebate letters, notice letters, NDA, MOU,
   guarantees, certificates and other overlays: folder 3 when current, folder 4 when ended,
   unsure when Unclear. Their Supply coverage cell does not route them.
7. **Transactions.** Purchase orders, call-offs, quotes and acknowledgements: folder 5. When an
   account has nothing in folders 1 or 2, the account README notes that it trades on order
   terms, which `/analyse` should then examine.
8. **Linking.** Relation to parent says what the child does; the Parent agreement words are
   matched to a row in the same account by the date they quote against Document date, with
   title similarity as the tiebreak, then by a unique title, and by reference whenever one is
   quoted and present. A schedule, amendment, participation or notice that finds its parent inherits the
   parent's place between folders 1 and 2 unless its own coverage is narrower. A Supersedes or
   Terminates child whose End date, or Document date when there is none, is on or before the
   as-at date sends its parent to folder 4; a future date leaves the parent live and flagged.
   An unresolved parent sends the child to unsure. When the export names no parent at all and
   the relation is one that attaches rather than ends (amends, extends, renews, forms part of,
   agreed under, accedes to, governed by, placed under, varies, confirms), and the account holds
   exactly one master that is not a draft or copy, the child is linked to that master with the
   flag "parent inferred"; Terminates and Supersedes are never inferred.
9. **Contradictions go to review.** A non-governing instrument whose Supply coverage says it
   governs, a master answering Varies commercials only, or a Global master agreement with Group
   mechanism None, goes to unsure with both cells quoted. Global master agreement with Part of
   supply is consistent and is filed normally.
10. **Rows that are not contracts.** A row for the ERP file or the review table itself is
    ignored. A readable file with no row goes to a holding folder with the review tool's
    rejection code when its error log is supplied. Playbooks come from a local list,
    `inputs/business-practice.csv` (file name and account), into folder 6.

## What the first export showed (9 September 2026, messy pile)

The review tool processed 30 of 33 documents, rejecting the zero-byte PDF, the text file with a
PDF extension and the .msg. It read the xlsx and the jpg. Single-select fields exported labels
only, so every reason and every parent target was lost, and empty selections came back as an
em dash. The model's sense of today was earlier than 2026: five current instruments dated in
2026 came back Not yet effective. Signature detection on image signature pages was
inconsistent. Two all-purchases masters came back Part of supply. Entities, titles, instrument
types, drafts, the reversed sides on a supplier-paper framework and the additional customer on
a three-party letter came back right. The questions above are the revision that followed.

## Sorting-rule edits this design required

- Rule 3, `unsure`: delete the clause sending a rolling agreement with no later evidence to
  unsure. An evergreen or rolling agreement is current unless something records its end.
- Rule 5, `3-live-not-trade`: add pricing, rebate, bonus and incentive letters that vary
  commercials under terms that govern elsewhere, and notice letters.
- Rule 6, `1-governs-trade`: the sentence excluding a period-only pricing or rebate letter now
  points it to folder 3.
- Rule 7, `2-governs-part-of-trade`: delete "or a period (this year's pricing or rebate
  letter)". Folder 2 is for supply limited by product set, project, site, programme or division.

Applied to `stage1/sorting-rules.md` on 10 September 2026, so the judge in `/analyse` and the
script in `/sort` follow the same rules. Rule 4 now says in terms that a rolling or evergreen
agreement is current unless something in the pile records its end.

## Implementation and results

`scripts/sort_light.py` implements the filing above: `--import FILE [--error-log FILE]
[--as-at DATE]`, `--unmatched` (the names for the one model turn), `--file` and `--status`.
`eval/messy/score_light.py` scores a filing against the messy pile's key; it is for the
evaluator only. On the messy pile (33 documents, six ERP rows), as at the export date:

| run | in an accepted folder and account |
| --- | --- |
| first export (no dates, no parent words), with the entity map | 20 of 33 |
| second export, script alone, empty entity map | 22 of 33 |
| second export, after the names-only turn filled the entity map | 26 of 33 |
| third export (Title and Reference back, Signed reworded), script alone | 27 of 33 |
| third export, after the names-only turn | 32 of 33 |

The third export (10 September 2026) settled the Ardleigh family: the executed master no longer
reads as Draft, so it, its three drafts and the agreement it supersedes file correctly. Two
script changes followed it. Versions and copies of one instrument now meet on the reference as
well as the title, which files the Wexbury draft whose title is worded differently from the
executed framework. And a one- or two-page signed copy beside a much longer executed body of
the same instrument is filed as its signature page, the body carrying the execution it shows,
which ties the detached Larkhall signature page to its body. The one remaining miss is the file
holding two agreements: Mixed goes to unsure by design. The six script-alone misses are all
names that the one model turn decides (the word-order variant of Trentmoor and the Wexbury
trading name).

Two things to know about the third export. The reworded Signed question made the model more
cautious: five documents that read Signed by all parties in the second export now read
Signature not established, which routes nothing but weakens the choice of best copy. And Group
mechanism still exports as an em dash on most rows, so the required-answer setting either did
not take effect or is not available; the script treats the dash as blank.

## After the light filing: the top accounts

The light folders are the whole ERP for the cost of a script. For the accounts that matter,
`ERP_Top.csv` or `ERP_Top.xlsx` in the pile lists their ERP names, the business drops the
contracts it has collected for them into the pile, and `/analyse top <pile>` reads those
accounts in full (the documents `/sort` filed to them plus every readable file without a
filing row), judges them and writes the notes and diagrams; `/deep-dive top` fills the forms and
maps them. Everything else stays filing only. The README describes both commands.
