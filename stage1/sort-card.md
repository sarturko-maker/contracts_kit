# The sort card — ten questions about one document

You are reading ONE document and answering these ten questions about it. Plain words, short
answers. "Not found" is a valid answer anywhere. Do not add, skip or reword a question.

**Evidence** is required for questions 2, 3, 4, 6 and 7: a page (PDF) or clause or paragraph
(`.docx`) reference and the exact words relied on, forty or fewer, verbatim, in quotes. Paraphrase
is not evidence. If there is nothing to quote, write `not found`.

**Before you answer:** read `work/text/<id>.txt` in full. Open `work/files/<id>.<ext>` with the
Read tool for every page marked `[scan: look at the page]`, and ALWAYS for the signature page,
even when the text looks complete: signatures, stamps and handwritten dates are only visible as
a picture. PDFs over ten pages are read in ranges (`pages: "1-20"`). Read the whole body; read
schedules by title and first page unless a question needs more. Look for parts with different
lives (question 5) before answering the dates (question 4).

## The ten questions

1. **What is it?** Title as printed, and the kind, one of: master or framework; local adoption
   of a group agreement; standard terms; project or programme agreement; schedule or annex;
   amendment or side letter; pricing or rebate letter; NDA; guarantee; other overlay (data
   terms, code of conduct, EDI); purchase order or quote; credit application; internal playbook
   or guidance; letter or email; other. The title is a hint, not the decision.
2. **Which companies are on it?** The other side's signing entities first (companies, not the
   people who signed), then any group companies listed, each with its role. Our signing entity.
   All names exactly as printed. *Evidence required.*
3. **Is it signed?** Both / us only / them only / nobody / can't tell (signature page missing).
   Look at the signature page as a picture, always. A `.docx` is "nobody" unless a signature
   image is present; note tracked changes or comments. *Evidence required.*
4. **When does it run?** Start date and how you know it (stated, or date of last signature). End
   date, or rolling until notice (with the period), or until a project ends. Any sign it ended
   (termination letter, expiry, replaced). Your call for today: live / dead / unsure.
   *Evidence required.*
5. **Does it have parts with different lives?** General terms plus programme terms, a framework
   plus an annual pricing appendix, schedules that expire separately. If yes: each part, its
   pages, live or dead, and which part wins on conflict, in its own words.
6. **Does it hang off another document, or replace one?** Quote the reference ("the Agreement
   dated …"). Say whether that document is in the pile. *Evidence required.*
7. **Does it govern trade, and how much of it?** One of: all purchases between the parties; a
   defined product set or bill of materials; a project, site or programme; a period (an annual
   pricing or rebate arrangement); no, it does not govern trade (NDA, guarantee, data terms);
   can't tell. Say what makes it govern trade: orders placed under it, prices set by it, or
   standard terms applied by it. Ignore "these terms prevail over purchase orders"; almost every
   contract says it. A defined product set does not by itself make it narrow: if the set looks
   like everything the account buys, or the document says all orders fall under it, say so.
   *Evidence required.*
8. **Which of their companies and countries does it cover?** Signatories only / named group
   companies / all group companies; which countries.
9. **Is it a copy, version or draft of another document in the pile?** Which one, and which is
   the better copy. A signed signature page filed on its own belongs to some document; say
   which. (`work/inventory.csv` lists every document's number, original path and title guess.)
10. **Anything odd?** Up to three lines: pages missing, schedules referred to but absent, wording
    that matters, conflicts inside the document.

## What you write

Two files with the same answers: `work/cards/<id>.json` (the machine copy, write it first) and
`work/cards/<id>.md` (the human copy, same content laid out under the ten headings). Every value
is a plain string. Several values in one field are joined with ` | `. Dates are `YYYY-MM-DD`
when the paper gives a full date, otherwise as printed. Evidence fields look like
`p.3: "the exact words"` or `cl. 12.1: "the exact words"`, several joined with ` | `.

| key | question | allowed answers or shape |
| --- | --- | --- |
| `doc_id` | | three digits, e.g. `001` |
| `q1_title` | 1 | title as printed |
| `q1_kind` | 1 | one of the fifteen kinds above, spelled as above |
| `q2_their_signing_entities` | 2 | `Name as printed (signatory)`, joined with ` \| ` |
| `q2_their_group_companies` | 2 | `Name as printed (role)`; role: parent listed / affiliate listed / guarantor / other; or `none` |
| `q2_our_entity` | 2 | our signing entity as printed, or `not found` |
| `q2_evidence` | 2 | page or clause + exact words |
| `q3_signed` | 3 | `both` / `us only` / `them only` / `nobody` / `can't tell` |
| `q3_evidence` | 3 | what the signature page shows, page + words; for `.docx`: tracked changes / comments seen |
| `q4_start_date` | 4 | date or `not found` |
| `q4_start_basis` | 4 | `stated` / `date of last signature` / `not found` |
| `q4_end` | 4 | `fixed: <date>` / `rolling until notice (<period>)` / `until project ends: <name>` / `not found` |
| `q4_ended_sign` | 4 | `none found` or what you saw (`expired <date>`, `terminated by …`, `replaced by …`) |
| `q4_status` | 4 | `live` / `dead` / `unsure` |
| `q4_evidence` | 4 | page or clause + exact words for start and end |
| `q5_parts` | 5 | `yes` / `no` |
| `q5_parts_detail` | 5 | `Part name: pp.a-b, live` or `dead (<why>)`, joined with ` \| `; or `none` |
| `q5_precedence` | 5 | which part wins, page or clause + exact words; or `not found` |
| `q6_attaches_to` | 6 | `<reference as printed> → doc NNN` or `→ not in pile`; or `none` |
| `q6_replaces` | 6 | same shape; or `none` |
| `q6_referred_to_not_in_pile` | 6 | documents referred to but absent, or `none` |
| `q6_evidence` | 6 | page or clause + exact words of the reference |
| `q7_trade_scope` | 7 | `all purchases` / `defined product set` / `project, site or programme` / `period` / `no` / `can't tell` |
| `q7_what_makes_it_govern` | 7 | orders placed under it / prices set by it / standard terms applied by it; plus the limit (which project, set or period) |
| `q7_evidence` | 7 | page or clause + exact words |
| `q8_entities_covered` | 8 | `signatories only` / `named group companies` / `all group companies` / `not found` |
| `q8_countries` | 8 | countries named, `; `-separated, or `not found` |
| `q9_copy_or_draft_of` | 9 | `doc NNN (<relation: duplicate / earlier draft / signature page of>)` or `none` |
| `q9_better_copy` | 9 | `this one` / `doc NNN` / `n/a` |
| `q10_oddities` | 10 | up to three lines joined with ` \| `, or `none` |

Then return exactly one line, the shape in `stage1/reader-return.md`, and stop.
