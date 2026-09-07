# Evaluation results

As of 2026-09-06; invented three-account pile; topics off.
A = read everything; B = map then read; C = forms and graph only.

Questions and grading key: [questions.csv](questions.csv).

| Question | Mode | Correct | Evidence | Wrong part | Source pages | DOCX units | Status | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q01 | A | yes | yes | no | 8 | 1 | SCORED | Current 30-day payment; excludes expired 60-day programme and site-only 45 days. |
| Q01 | B | yes | yes | no | 5 | 0 | SCORED | Same correct payment answer, with fewer source pages. |
| Q01 | C | no | yes | no | 0 | 0 | SCORED | Payment period absent with topics off; appropriate abstention. |
| Q02 | A | yes | yes | no | 8 | 1 | SCORED | Correct freight-at-cost permission; distinguishes expired programme and site-only inclusion. |
| Q02 | B | yes | yes | no | 5 | 1 | SCORED | Correct freight-at-cost answer; reads five pages plus the relevant internal playbook. |
| Q02 | C | no | yes | no | 0 | 0 | SCORED | Freight charging basis absent with topics off; appropriate abstention. |
| Q03 | A | yes | yes | no | 8 | 1 | SCORED | Correct six-month notice; original twelve months and site-only thirty days distinguished. |
| Q03 | B | yes | yes | no | 2 | 0 | SCORED | Correct amended notice period after reading only the relevant two source pages. |
| Q03 | C | yes | yes | no | 0 | 0 | SCORED | Correct six-month notice from the effective amendment. |
| Q04 | A | yes | yes | no | 8 | 1 | SCORED | Correct continuing German affiliate coverage despite the programme expiry. |
| Q04 | B | yes | yes | no | 5 | 0 | SCORED | Correct affiliate coverage; five source pages establish identity, survival and amendment. |
| Q04 | C | yes | yes | no | 0 | 0 | SCORED | Correct continuing German affiliate coverage after programme expiry. |
| Q05 | A | yes | yes | no | 8 | 1 | SCORED | Correct site agreement, 45-day payment and included freight. |
| Q05 | B | yes | yes | no | 2 | 0 | SCORED | Same correct site/payment/freight answer using two source pages. |
| Q05 | C | no | yes | no | 0 | 0 | SCORED | Identifies site agreement; payment and freight terms are missing. |
| Q06 | A | yes | yes | no | 3 | 1 | SCORED | Correct master uncertainty and current 2% rebate; detached signatures do not authenticate draft terms. |
| Q06 | B | yes | yes | no | 3 | 1 | SCORED | Correct answer; checking all four relevant files costs the same source reading as A. |
| Q06 | C | yes | yes | no | 0 | 0 | SCORED | Correct master uncertainty and current 2% rebate only. |
| Q07 | A | yes | yes | no | 4 | 0 | SCORED | Correct 21 days; excludes both expired ten-day schedule and superseded 45-day master. |
| Q07 | B | yes | yes | no | 3 | 0 | SCORED | Correct current 21 days, using only the replacement agreement’s three pages. |
| Q07 | C | no | yes | no | 0 | 0 | SCORED | Finds current General Terms; payment period is missing. |
| Q08 | A | yes | yes | no | 4 | 0 | SCORED | Correct expense basis and GBP 250 per-consignment cap, including pump purchases. |
| Q08 | B | yes | yes | no | 3 | 0 | SCORED | Correct freight expense and cap, using only the replacement agreement’s three pages. |
| Q08 | C | no | yes | no | 0 | 0 | SCORED | Freight expense basis and GBP 250 cap are missing. |
| Q09 | A | yes | yes | no | 15 | 2 | SCORED | Correct Quenby-only current sole-supplier commitment; qualifies Pellmont’s missing execution text. |
| Q09 | B | yes | yes | no | 8 | 1 | SCORED | Correct corpus answer after eight relevant source pages and one DOCX. |
| Q09 | C | yes | yes | no | 0 | 0 | SCORED | Correct: Quenby alone has a confirmed current sole-supplier commitment. |
| Q10 | A | yes | yes | no | 15 | 2 | SCORED | Correct two forthcoming fixed expiries; rolling terms and dead instruments excluded. |
| Q10 | B | yes | yes | no | 2 | 0 | SCORED | Correct two forthcoming fixed expiries, verified from only two source pages. |
| Q10 | C | yes | yes | no | 0 | 0 | SCORED | Correct two fixed expiries; excludes rolling and dead instruments. |
| Q11 | A | yes | yes | no | 15 | 2 | SCORED | Correct two current customer-paper agreements, including the site-only agreement. |
| Q11 | B | yes | yes | no | 9 | 0 | SCORED | Correct customer-paper count after nine source pages; no DOCX needed. |
| Q11 | C | yes | yes | no | 0 | 0 | SCORED | Correct two customer-paper governing agreements; excludes the draft. |
| Q12 | A | yes | yes | no | 15 | 2 | SCORED | Correct Pellmont-only gap; distinguishes confirmed coverage and dead parts elsewhere. |
| Q12 | B | yes | yes | no | 12 | 1 | SCORED | Correct corpus coverage answer; twelve source pages and one DOCX establish the three positions. |
| Q12 | C | yes | yes | no | 0 | 0 | SCORED | Correct: Pellmont alone lacks confirmed terms governing all trade. |

36 of 36 runs scored from saved responses and reviewed transcripts.

Curated cards, placements and forms; deterministic oracle replay, not model extraction. Fresh question trials compare answering on these map/form artifacts.

A and B each answered 12/12 questions correctly; C answered 7/12 fully. All three modes supplied accurate supporting evidence on 12/12, and none made a wrong-part error. Source reading totalled 111 PDF/image pages and 14 DOCX units for A, 59 pages and four DOCX units for B, and zero source pages/units for C. C still read forms and graph rows; that work is outside the page proxy.

B matched A with fewer source pages on 11 of 12 questions, reducing total source pages by 47%. Q06 tied at three pages plus one DOCX because every Pellmont file mattered to the master/rebate question. For the fixed-expiry corpus question Q10, B verified two pointed-to pages while A read all 15 pages plus both DOCX files. A successfully excluded the dead and replaced terms throughout; this run shows a reading-cost advantage for B, with equal observed correctness.

All modes answered the four corpus questions correctly. C's five incomplete account answers were four explicit abstentions (Q01, Q02, Q07, Q08) and one partial answer (Q05): payment or freight detail was missing with topics off. These were information gaps, not asserted answers drawn from dead parts. The run does not establish that only C can answer corpus questions, or test whether enabled topic readings would be too coarse.

The 36 trials used 36 distinct gpt-6-astra Codex agents, each started without inherited conversation. Manual review checked access scopes, citations and page counts. A provenance audit matched every preserved raw final and all 310 saved tool-call/result records to the original local rollouts; reasoning records were excluded. Responses, grades and transcripts remain under the ignored work/eval/ directory. This was one run per question/mode, using curated maps and forms; it measures answering with those artifacts, not extraction accuracy.

Source pages count distinct PDF/image pages read, including native text; DOCX text units are
reported separately because Word pagination is not stable. Map/form access and the cost of building
the map are not included, so the page proxy is not a complete token or runtime cost.

Invented contracts are cleaner than a real pile; eleven readable files are indicative only.
The comparison tests the map thesis; it does not assume B wins or C alone answers corpus questions.
