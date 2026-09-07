# {{account}} — position ({{side}})

<!--
This is the template for out/<side>/<account>/ANALYSIS.md, the complete evidence and reasoning.
README.md is a separate short overview linking here. Its position is three to six Markdown
bullet points, with short bold labels and at most 180 words in total;
all longer prose stays here in full, with a link in the overview. Plain words,
no hedging, no recitals, every sentence a fact. Nothing in it that is not in a sort card.

place.py fills every {{placeholder}}. Sections 1, 3, 4, 5, 6 and the list in 8 are generated
from work/placements/<account>.csv and the cards. Sections 2, 7, 8 (the prose) and 9 are the
judge's prose, taken from work/placements/<account>.md under the headings
"## The position", "## Overlaps and conflicts", "## Couldn't find or couldn't tell" and
"## Questions for the business". Documents are named by number (doc 001), never by filename.
-->

## 1. Account

{{account_block}}

<!-- generated: ERP name and side (with account number and country if the ERP has them); our
entities found; their entities found, each with how sure the match was and on what basis. -->

## 2. The position

{{position}}

<!-- judge bullets, three to six points, no table or introductory paragraph: what governs trade, since when, whose paper,
signed by whom, what it covers, how it ends; the one qualification that matters most; what
governs part of the trade; what is missing. If nothing governs, say so and say what the account
appears to trade on instead. An invented example:

- **Governing agreement:** The 2019 Supply Agreement (doc 001), our paper, signed by both,
  covers all UK sites.
- **Changes and duration:** Doc 002 (2022) reduced the rolling notice period from twelve
  months to six months.
- **Expired part:** The Line 4 programme terms ended in March 2024. Their mandatory freight
  charge differs from the live general terms; the historical priority is unresolved.
- **Limited scope:** Doc 008 governs Hexley Works only. Nothing else governs all the trade.
- **Other paper:** The parent NDA expired in 2023.
- **Missing:** The price list referred to in clause 5 is not in the pile.
-->

## 3. Governs trade

{{governs_table}}

<!-- generated, by tree: tree | doc | title | kind | companies | start / end / status | scope |
why (one line) -->

## 4. Governs part of the trade

{{part_table}}

<!-- generated, same table plus the limit (project, site, product set or period) -->

## 5. Everything else

{{everything_else}}

<!-- generated: every remaining document, one line each: what it is, which folder, why, and what
would change the answer ("expired 2023 unless renewed", "draft, no signed copy found", "single
PO"). This is where sales says "actually we renewed that". -->

## 6. How we trade in practice

{{practice_line}}

<!-- reserved for MVP2. In stage 1 one line: any playbook found in the pile (folder 6), or
"nothing in the pile; sales to confirm". -->

## 7. Overlaps and conflicts

{{overlaps}}

<!-- judge prose: where two live places cover the same subject: doc and part, the exact words
from each, which wins and why (internal precedence, a replacement, an order-of-precedence
clause), or "unresolved". Later in time does not win by itself. "None found" if none. -->

<!-- For layered parts, also retain competing wording from expired parts. State their current
applicability separately from priority while both applied; missing precedence leaves that
earlier priority unresolved. Expiry does not create a historical precedence rule. -->

## 8. Couldn't find or couldn't tell

{{couldnt}}

<!-- generated list (referred-to documents not in the pile; undated documents; rolling agreements
with no proof of use; matches made on known group only) followed by the judge's prose. -->

## 9. Questions for the business

{{questions}}

<!-- judge prose: numbered, each naming the document number it is about. -->

---

Legal: is the contract and its status right? Sales: is this how we trade with them? Reply with
the document number.
