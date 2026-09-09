# Review_Table_Light: twelve questions for filing by script

Review_Table_Light is the export that a script turns into account folders and status folders.
No model reads a contract at this stage. The only model call is for customer names that
neither match an ERP account exactly nor have a row in `inputs/entity-map.csv`; the model sees
that list of names and the ERP account names, nothing else, and its suggestions land in the
entity map as provisional rows for the user to confirm. `/analyse` remains the optional next
stage for the accounts the user picks, and it uses the separate full Review_Table.

Keep the export beside the ERP and the original contracts:

```text
corpus/
  ERP.xlsx
  Review_Table_Light.xlsx
  Review_Table.xlsx            (optional, for /analyse)
  ...contract files...
```

CSV or XLSX, one sheet, one row per file, row 1 holding the column names below. Column names
may be written with spaces; the importer normalises case, spaces and hyphens. Answers are
plain words with spaces. Playbooks and other internal guidance are not sent to the review tool;
they will be filed from a local list into the business practice folder (to do).

Use [the invented example](../inputs/Review_Table_Light.example.csv) as a header and format
guide only. Its rows are invented and must not be imported into a real corpus.

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

| column | permitted answers |
| --- | --- |
| File name | exact filename with extension, supplied by the export, not a question |
| Title | free text, short normalised title |
| Reference | free text, or None |
| Customer entity | one legal name as printed, or Not found |
| Additional customer entities | None, or legal names one per line |
| Supplier entity | one legal name as printed, or Not found |
| Instrument | Global master agreement; Master or supply agreement; Local participation agreement; Standard terms or account form; Project agreement or statement of work; Schedule or exhibit; Amendment or side letter; Pricing or rebate letter; Purchase order or call-off; Purchase order or call-off carrying standard terms; Quote or acknowledgement; Quote or acknowledgement carrying standard terms; NDA, MOU or letter of intent; Guarantee or security; Certificate or evidence; Other overlay; Mixed; Other; Unclear |
| Supply coverage | All supply between the parties; Substantially all supply; Part of supply; Named division or site; Varies commercials only; No supply coverage; Unclear |
| Group mechanism | Contracting for affiliates; Adoption agreement; Entity schedule; Ordering entitlement; None; Unclear |
| Signed | Signed by all parties; Signed by one party; Unsigned; Draft; Signature not established |
| Status | Current; Expired; Terminated; Not yet effective; Unclear |
| Relation to parent | None, or one of Forms part of; Accedes to; Placed under; Agreed under; Governed by; Amends; Varies; Extends; Renews; Supersedes; Terminates, then a vertical bar and the parent's reference, title and date |

Closed answers begin with the permitted value exactly, then a vertical bar, then a short
reason. The script reads the value before the bar and ignores the rest; the analyst reads the
reason.

## The questions

Each question is self-contained because the review tool applies no common instruction.

### Title

```text
Answer from this document only; never use the filename. Give a short normalised title that
says what this document is, based on its printed title and its content, for example Master
Supply Agreement, Amendment No. 2 to Master Supply Agreement, Local Participation Agreement,
Rebate Letter 2026, Purchase Order, Mutual Non-Disclosure Agreement.
```

### Reference

```text
Answer from this document only. Give this document's own contract, agreement or reference
number if one is printed on its cover, header, footer or parties clause, for example a
procurement or contract ID. Give only this document's own number, never the numbers of other
agreements it refers to. If no such number appears in the reviewed content, answer None.
```

### Customer entity

```text
Answer from this document only. Give the one legal entity that contracts as the customer,
buyer or purchaser: the customer entity that signs, or where several customer entities are
parties, the first named. Give the full legal name exactly as printed in the parties clause or
signature block, including suffixes such as Ltd, GmbH or Inc. This is the contracting party,
not the affiliates, sites or divisions permitted to use the agreement. If no customer entity
can be identified, answer Not found.
```

### Additional customer entities

```text
Answer from this document only. Apart from the entity you gave as the customer entity, list
every other legal entity that is itself a contracting party on the customer side, one full
legal name per line exactly as printed, including co-signing group companies and entities
listed as parties in a schedule of signatories. Exclude affiliates, sites or divisions that
are only permitted to use the agreement. If there are none, answer None.
```

### Supplier entity

```text
Answer from this document only. Give the one legal entity that contracts as the supplier,
seller or provider: the supplier entity that signs, or where several are parties, the first
named. Give the full legal name exactly as printed in the parties clause or signature block,
including suffixes. This is the contracting party, not supplier group companies permitted to
supply under it. If none can be identified, answer Not found.
```

### Instrument

```text
Answer from this document only. Classify the document by what it does, not by its title.
Begin with exactly one value below, then a vertical bar, then a reason of at most 25 words
citing the clause or page.
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
Amendment or side letter: a document that amends, varies, extends, renews, restates or
terminates the text of another agreement.
Pricing or rebate letter: a letter or short agreement granting or varying a rebate, bonus,
growth incentive, marketing contribution, special price or payment term for a period or
project, standing beside the supply terms rather than forming part of them.
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
Mixed: distinct instruments bound into one file; name them in the reason.
Other. Unclear.
```

### Supply coverage

```text
Answer from this document only. Governing supply means setting the terms on which goods,
services or software are supplied: what may be ordered, delivery, warranty, price and
payment. A document that only varies prices, rebates, bonuses or incentives under terms that
govern elsewhere does not govern supply, even if it applies to all purchases. This question
asks what supply is covered, not which group entities may use the agreement. Begin with
exactly one value below, then a vertical bar, then a reason of at most 25 words citing the
clause or schedule.
All supply between the parties: all goods, services or software the customer buys from the
supplier, or wording placing all orders between them under this document.
Substantially all supply: supply of a defined product set, bill of materials or catalogue
that the document describes or treats as all or nearly all of what the customer buys from
the supplier.
Part of supply: supply limited to a product set, project, site or programme, while other
supply is or could be governed by something else.
Named division or site: supply to a named division, business unit or group of sites of the
customer only.
Varies commercials only: does not govern supply; grants or varies a rebate, bonus, growth
incentive, marketing contribution, special price or payment term under other governing terms.
No supply coverage: does not concern the supply of goods, services or software, for example
an NDA, MOU, guarantee, certificate or data processing agreement.
Unclear: the reviewed content does not establish which applies.
Decide from the scope, ordering, delivery, price and payment clauses and any product or site
schedule, not from the title. A clause saying this document prevails over purchase orders
does not by itself mean all supply.
```

### Group mechanism

```text
Answer from this document only. Does this agreement reach legal entities beyond the two
contracting parties, and by what mechanism? This is separate from what supply is covered: an
agreement can be open to a whole group while covering one product line. Begin with exactly
one value below, then a vertical bar, then a reason of at most 25 words citing the clause or
schedule.
Contracting for affiliates: a party contracts on behalf of its affiliates, subsidiaries or
group companies so that they are bound or entitled without further signature.
Adoption agreement: affiliates join by signing a participation, adoption, accession,
implementation or joinder agreement, or a template for one is attached or referred to.
Entity schedule: a schedule or appendix lists the affiliates, sites or divisions covered.
Ordering entitlement: affiliates may place orders under it without a separate agreement.
None: the agreement is limited to the two named entities or contains no such wording.
Unclear: the reviewed content does not establish the position.
```

### Signed

```text
Answer from this document only. Begin with exactly one value below, then a vertical bar, then
the signing entities and dates shown, or what was found instead, in at most 25 words.
Signed by all parties: a visible signature, electronic signature certificate or completion
statement for every contracting party.
Signed by one party: visible signature for one side only.
Unsigned: signature blocks are visible and empty for every party.
Draft: tracked changes, comments, a watermark, a version label or the word draft are present.
Signature not established: the signature page is missing, illegible, referred to but not
present, or not among the reviewed content. A typed name is not a signature, and the absence
of a signature from the reviewed content does not mean the document is unsigned.
```

### Status

```text
Answer from this document only, as at the date of this review. Begin with exactly one value
below, then a vertical bar, then the start date, the end date or renewal rule and the clause,
in at most 25 words.
Current: the document has commenced and either its fixed term has not ended or it continues
on a rolling, evergreen, automatic renewal or until-terminated basis. Treat evergreen and
rolling terms as Current unless this document records termination.
Expired: a fixed end date has passed and no extension appears in the reviewed content.
Terminated: this document records its own termination or its replacement by another
agreement.
Not yet effective: commencement depends on a future date or on a condition not shown as met.
Unclear: dates are missing from the reviewed content, or parts of the document have different
terms; say which.
Do not assume anything about amendments or terminations in other documents.
```

### Relation to parent

```text
Answer from this document only. If this document sits under, forms part of, or alters another
agreement, begin with exactly one relation below, then a vertical bar, then that agreement's
reference number if printed, its title and its date as printed. Where there is more than one
parent, give one per line with the principal first.
Forms part of: a schedule, exhibit or annex of the parent.
Accedes to: a participation or joinder under a global master.
Placed under: an order, call-off, quote or acknowledgement issued under an agreement.
Agreed under: a project agreement or statement of work under a master.
Governed by: standard terms incorporated by reference.
Amends, Extends, Renews, Supersedes, Terminates: the effect on the parent's text or term.
Varies: a pricing, rebate or incentive letter that changes the commercial outcome under the
parent without amending its text.
If the document stands alone, answer None. Do not say whether the parent exists elsewhere.
```

## How the script files from these answers

The output is one folder per ERP account, and inside it the status folders of
`stage1/sorting-rules.md` section B: `1-governs-trade`, `2-governs-part-of-trade`,
`3-live-not-trade`, `4-not-live`, `5-orders-drafts-duplicates`, `6-business-practice` and
`unsure`. Every file gets a row, holding folders keep unmatched names, and byte-identical copies
are detected by hash.

1. **Account.** Customer entity is matched exactly to an ERP account, then through the entity
   map. Anything else goes to the model once, as names only, and comes back as provisional
   entity-map rows. Each Additional customer entity that matches receives a copy of the document
   in its own account; unmatched ones are flagged on the row, not dropped.
2. **Instrument gate.** Only Global master agreement, Master or supply agreement, Local
   participation agreement, Standard terms or account form, Project agreement or statement of
   work, Schedule or exhibit and Amendment or side letter can reach folders 1 or 2.
3. **Governing instruments.** Current and signed: folder 1 for All supply between the parties
   and Substantially all supply; folder 2 for Part of supply and Named division or site.
   Expired or Terminated: folder 4. Signing not established, Unsigned without a signed twin, or
   Status Unclear: unsure.
4. **Non-governing instruments.** Pricing or rebate letters, NDA, MOU, guarantees, certificates
   and other overlays: folder 3 when Current, folder 4 when Expired or Terminated, unsure when
   Unclear. Their Supply coverage cell does not route them.
5. **Transactions.** Purchase orders, call-offs, quotes and acknowledgements: folder 5, with
   drafts that have a signed twin and byte-identical copies. An order carrying standard terms
   is still folder 5; when an account has nothing in folders 1 or 2, the account README notes
   that it trades on order terms, which `/analyse` should then examine.
6. **Linking.** A schedule, amendment or participation inherits its parent's place between
   folders 1 and 2 only when the parent is found in the same account by reference number, or by
   a unique title and date, and only when the child is itself Current. A child that is Expired
   or Terminated goes to folder 4 whatever its parent's status. An unresolved parent sends the
   child to unsure.
7. **Contradictions go to review.** A non-governing instrument whose Supply coverage says it
   governs, a governing instrument answering Varies commercials only, or a Global master
   agreement with Group mechanism None, goes to unsure with both cells quoted. Global master
   agreement with Part of supply is consistent and is filed normally.
8. **One signature.** Signed by one party is accepted as live for letters, orders, quotes and
   certificates, and sends masters, participations and project agreements to unsure.
9. **Run metadata.** The script records the export's file hash and its date at import, so the
   Status answers stay interpretable later without a paid review-date column.
10. **Playbooks.** A local list of filenames files internal guidance into folder 6 without
    sending it to the review tool. Not yet built.

## Sorting-rule edits this design requires

- Rule 3, `unsure`: delete the clause sending a rolling agreement with no later evidence to
  unsure. An evergreen or rolling agreement is current unless something records its end.
- Rule 5, `3-live-not-trade`: add pricing, rebate, bonus and incentive letters that vary
  commercials under terms that govern elsewhere.
- Rule 6, `1-governs-trade`: the sentence excluding a period-only pricing or rebate letter now
  points it to folder 3.
- Rule 7, `2-governs-part-of-trade`: delete "or a period (this year's pricing or rebate
  letter)". Folder 2 is for supply limited by product set, project, site, programme or division.

These edits are not yet applied to `stage1/sorting-rules.md`.

## Implementation status

No script reads this schema yet. A five-column prototype of light filing exists locally and is
not committed; it files by account and document type and uses a Haiku turn for name matching,
which this design removes. The next build step is the deterministic script described above,
importing this twelve-column export, plus the rule edits. Until then this file is the prompt
set for the review tool and the specification for that script.
