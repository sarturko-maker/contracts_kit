# The document form — stage 2

One document, one form. The extractor starts from the document's sort card (`work/cards/<id>.md`) and
does not re-answer what the card already answers unless the form needs a fixed choice the card does
not give. It reads for the extra detail: parts in full, precedence words, links, and topics if enabled.

Rules. One row per question. Every row in sections B to I requires evidence unless the answer is
`not_found` (or `none`, or `inherits`): a page or clause reference and the exact words, forty or fewer,
verbatim. "Per part if layered" means once for the whole document and once per part in section F.
Family is decided per tree by the mapper, never per document. Section I is off by default. DCG names
are used verbatim from `dcg/`; nothing is invented; where DCG lacks what the form needs the mapping says
`DCG: none — didn't-fit candidate` and section K records it. `not_found` is a valid answer anywhere.

Column key: **DCG mapping** names the node type, edge type or property in `dcg/node_types.csv`,
`dcg/edge_types.csv` or `dcg/properties.csv` that the answer feeds. **Evidence**: `yes` = required
unless `not_found`; `no` = not required.

## A. Identity (copied, not read)

Filled from `work/inventory.csv`, `work/logs/sort.csv`, `inputs/entity-map.csv` and
`work/placements/<account>.csv`. Never re-read from the document.

| id | field | source | DCG mapping |
| --- | --- | --- | --- |
| A | `doc_id` | inventory | node id root (`DOC-<doc_id>`) |
| A | `source_path` | inventory | `source_key` |
| A | `file_type` | inventory | none |
| A | `sha256` | inventory | `source_key` companion; none in DCG |
| A | `pages` | inventory | none |
| A | `text_or_scan` | inventory `page_kinds` | none |
| A | `language_guess` | inventory | none |
| A | `docx_author`, `docx_dates`, `docx_tracked_changes` | inventory | none (draft evidence) |
| A | `side` | erp.json | `category` on the relationship node (customer / supplier) |
| A | `account` | sort log | `account` node (`belongs_to`) |
| A | `match_basis`, `match_confidence` | entity map | on the entity-to-account edge; DCG: none — didn't-fit candidate (basis) |
| A | `tree`, `folder` | placements | tree = the family unit the mapper classifies; folder: none |

## B. What it is

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| B1 | `cover_title` — the title as printed | free text | `alias` in `dcg/aliases.csv` (a hint, never a decision) | yes |
| B2 | `document_kind` | `master_or_framework` / `local_adoption_of_group_agreement` / `standard_terms_of_sale` / `project_or_programme_agreement` / `schedule_or_annex` / `amendment_or_side_letter` / `pricing_or_rebate_letter` / `nda` / `guarantee_or_bond` / `other_overlay` / `order_or_quote` / `credit_application` / `internal_playbook` / `letter_or_email` / `other` | node type: master_or_framework → `master`; local_adoption_of_group_agreement → `participation`; standard_terms_of_sale → `shared_terms`; project_or_programme_agreement → `master` (or `work_instrument` when H1 attaches it to a master); schedule_or_annex → `component`; amendment_or_side_letter → `change`; pricing_or_rebate_letter → `change`; nda → `master` (overlay O3); guarantee_or_bond → `security`; other_overlay → `component` (attached) or `shared_terms` (standalone); order_or_quote → `order` / `order_response`; credit_application → `master` (C4 anchor); internal_playbook → DCG: none — didn't-fit candidate; letter_or_email → `change` if it changes something, `evidence` if it records something, else DCG: none — didn't-fit candidate; other → function tag only (`function_tag`) | yes |
| B3 | `whose_paper` | `ours` / `theirs` / `hybrid` / `model_form` / `not_found` | `paper` | yes |
| B4 | `signed_status` | `both` / `ours_only` / `theirs_only` / `unsigned` / `signature_page_missing` / `not_found` | `status` = `signed` when both; DCG has no value for one-sided or unsigned execution: DCG: none — didn't-fit candidate (missing_allowed_value) | yes |
| B5 | `complete` — is the whole document here? | `yes` / `no` + `missing` (what is missing) | none (review note; missing referenced documents go to H3) | yes if `no` |
| B6 | `duplicate_or_draft_of` | `doc NNN` / `none` | none: the best copy is the node, the others are not graph rows | yes if not `none` |
| B6a | `best_copy` | `yes` / `no` | none | no |
| B7 | `language` | ISO 639-1 code, e.g. `en` | none (note only) | no |
| B9 | `layered` — parts with different lives? | `yes` / `no` | `yes` → one `component` node per part with `forms_part_of` → the document's node | yes |

## C. Who (mandatory; the survival rule)

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| C1 | `their_entities` — every company on their side | list of `{name_as_printed, address_or_registration_if_printed, role, page}`; role: `signatory` / `affiliate_listed` / `guarantor` / `other`; or `not_found` | `legal_entity` node per name (status `provisional` until the entity map resolves it) + `party_to` edge (document → entity) for each signatory; affiliate_listed → entity node, resolved to the account through the entity map with its basis; guarantor → `guaranteed_by` | yes |
| C2 | `our_entities` — every company on our side | same shape | `legal_entity` with `is_ours` = true + `party_to` | yes |
| C4 | `signature_dates_seen` | as printed, one per signatory, or `not_found` | feeds D1 (`valid_from`); none of its own | yes |

## D. When (per document; per part if layered)

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| D1 | `start_date` + D1a `basis` | date `YYYY-MM-DD` or `not_found`; basis: `stated` / `date_of_last_signature` / `not_found` | `valid_from` on the node | yes |
| D2 | `end_type` + `detail` | `fixed_date` (the date) / `rolling_until_notice` (the period) / `until_project_complete` (the project) / `not_found` | fixed_date → `valid_to`; rolling → `valid_to` blank, notice period: DCG: none — didn't-fit candidate; until_project_complete → `valid_to` blank: DCG: none — didn't-fit candidate | yes |
| D3 | `ended_evidence` + `detail` | `none_found` / `termination_letter` (doc id) / `expiry_date_passed` / `replaced_by` (doc id or description) / `not_found` | termination_letter → `terminates` edge; replaced_by → `supersedes` edge (new → old); expiry → `status` = `expired` | yes unless `none_found` |
| D4 | `status_as_read` | `live_fixed_term` / `live_rolling_presumed` / `expired_by_date` / `terminated` / `replaced` / `unknown` | `status`: live_* → `active`; expired_by_date → `expired`; terminated → `terminated`; replaced → `superseded`; unknown → `provisional` | yes |

## E. Scope (per document; per part if layered)

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| E1 | `products_services` | short, as printed, or `not_found` | `covers_product` edges only where product master data exists; else note only | yes |
| E2 | `territory` + `detail` | `global` / `regional` (name it) / `single_country` (name it) / `not_found` | `covers_territory` edges to `country` nodes; informs `scope` | yes |
| E3 | `entities_covered` | `signatories_only` / `named_affiliates` / `all_group_companies` / `not_found` | `scope`: signatories_only → `single`; named_affiliates → `group_referenced` (or `global` when the paper provides a per-entity adoption instrument); all_group_companies → `group_referenced` | yes |
| E4 | `trade_scope` | `all_purchases` / `defined_product_set` / `project_site_or_programme` / `period` / `none` | with G1 → `commercial_completeness` | yes unless `none` |

## F. Parts (only if B9 = yes; repeat per part)

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| F1 | `part_name` | as printed | `component` node name | yes |
| F2 | `pages_from_to` | e.g. `10-12` | none | no |
| F3 | `part_kind` | `general_terms` / `programme_or_project_terms` / `pricing_schedule` / `service_schedule` / `affiliate_list` / `other` | `component` (kind recorded in `type`) | yes |
| F4 | D fields for the part | the D block, or `inherits` | `valid_from` / `valid_to` / `status` on the component | yes unless `inherits` |
| F5 | E fields for the part | the E block, or `inherits` | as E, on the component | yes unless `inherits` |
| F6 | `internal_precedence` — which part wins on conflict | `{wins_over: [part names], words, page}` or `not_found` | `prevails_over` edge (winner → loser) + `precedence` property | yes |

## G. Does it govern trade?

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| G1 | `governs_orders` + `detail` | `yes` / `no` / `not_found`; detail: orders placed under it (we sell or we buy), prices set by it, or one side's standard terms applied by it | `commercial_completeness` (`yes` when an order alone completes a contract on the pre-agreed commercials) | yes |
| G2 | `commitment_or_status` | `none` / `volume_or_target` / `exclusivity_or_sole_supplier` / `preferred_or_approved_supplier` | `commitment`: volume_or_target → `volume` or `target` (say which); exclusivity_or_sole_supplier → `exclusivity`; none → `none`. preferred_or_approved_supplier → `appointment` only where the paper confers channel status, else DCG: none — didn't-fit candidate | yes unless `none` |

Deliberately absent: entire-agreement clauses and "prevails over purchase orders" clauses. Nearly
every contract has both; neither changes what governs.

## H. Links

| id | question | allowed answers | DCG mapping | evidence |
| --- | --- | --- | --- | --- |
| H1 | `attaches_to` | list of `{as_printed, doc_id}` (doc_id = `NNN` or `not_in_pile`) + `relation`: `forms_part_of` / `accedes_to` / `amends` / `placed_under` / `agreed_under` / `varies` / `extends` / `renews`; or `none` | that edge, exact name from `dcg/edge_types.csv`, from this document's node to the target | yes unless `none` |
| H2 | `replaces` | same shape; relation `supersedes` (or `terminates`) | `supersedes` (new → old) / `terminates` | yes unless `none` |
| H3 | `refers_to_missing` | list of `{as_printed, where}` or `none` | placeholder node, `status` = `provisional`, flagged for review (an edge never points at nothing) | yes unless `none` |

## I. Topics (off by default; see `stage2/topics.md`)

Per ticked topic: `{topic, part, page_or_clause, words, reading}` with the fixed readings in
`stage2/topics.md`. → DCG L3: `clause` → `has_term` → `term_fact`; SALI left `pending`. Evidence: yes.

## J. Extractor's notes

`notes`: 200 words or fewer. Ambiguities, conflicts inside the document, wording the fixed answers
cannot hold (record the words). Not a summary.

## K. Didn't fit the standard

Only when something did not fit: list of `{type, description, page}`, type one of `missing_field` /
`family_misfire` / `no_family_fits` / `missing_edge` / `missing_allowed_value` / `other`. Empty list
when nothing.

## L. Return line

`doc 017 | <kind> | <status> | layered: y/n | flags: <n> | work/forms/017.json` where `<n>` is the
number of entries in K.

## The JSON shape (`work/forms/<id>.json`; schema in `document-form.schema.json`)

Top level keys `A` to `L`. Answers are strings unless the table says list. Every question `Xn` that
requires evidence has a sibling `Xn_evidence`: `{"ref": "cl. 3.1 (p.2)", "words": "<exact words>"}`,
or `null` when the answer is `not_found`, `none` or `inherits`. Details ride in `Xn_detail`.

```
{"A": {"doc_id": "001", "source_path": "…", "file_type": "pdf", "sha256": "…", "pages": "14",
       "text_or_scan": "ttttttttttttts", "language_guess": "en", "docx_author": "n/a",
       "docx_dates": "n/a", "docx_tracked_changes": "n/a", "side": "customers",
       "account": "…", "match_basis": "same name", "match_confidence": "sure",
       "tree": "T1", "folder": "1-governs-trade"},
 "B": {"B1_cover_title": "…", "B1_evidence": {…}, "B2_document_kind": "…", "B2_evidence": {…},
       "B3_whose_paper": "…", "B3_evidence": {…}, "B4_signed_status": "…", "B4_evidence": {…},
       "B5_complete": "yes", "B5_missing": "", "B5_evidence": null,
       "B6_duplicate_or_draft_of": "none", "B6_evidence": null, "B6a_best_copy": "yes",
       "B7_language": "en", "B9_layered": "yes", "B9_evidence": {…}},
 "C": {"C1_their_entities": [{"name_as_printed": "…", "address_or_registration_if_printed": "…",
                              "role": "signatory", "page": "1"}], "C1_evidence": {…},
       "C2_our_entities": [{…}], "C2_evidence": {…},
       "C4_signature_dates_seen": "…", "C4_evidence": {…}},
 "D": {"D1_start_date": "2019-03-14", "D1a_basis": "date_of_last_signature", "D1_evidence": {…},
       "D2_end_type": "rolling_until_notice", "D2_detail": "6 months", "D2_evidence": {…},
       "D3_ended_evidence": "none_found", "D3_detail": "", "D3_evidence": null,
       "D4_status_as_read": "live_rolling_presumed", "D4_evidence": {…}},
 "E": {"E1_products_services": "…", "E1_evidence": {…}, "E2_territory": "regional",
       "E2_detail": "United Kingdom; Germany", "E2_evidence": {…},
       "E3_entities_covered": "named_affiliates", "E3_evidence": {…},
       "E4_trade_scope": "all_purchases", "E4_evidence": {…}},
 "F": [{"F1_part_name": "…", "F1_evidence": {…}, "F2_pages_from_to": "1-9",
        "F3_part_kind": "general_terms", "F3_evidence": {…},
        "F4_D": "inherits" | {the D block}, "F5_E": "inherits" | {the E block},
        "F6_internal_precedence": "not_found" | {"wins_over": ["…"], "words": "…", "page": "2"},
        "F6_evidence": {…} | null}],
 "G": {"G1_governs_orders": "yes", "G1_detail": "…", "G1_evidence": {…},
       "G2_commitment_or_status": "none", "G2_detail": "", "G2_evidence": null},
 "H": {"H1_attaches_to": "none" | [{"as_printed": "…", "doc_id": "001", "relation": "amends"}],
       "H1_evidence": null | {…}, "H2_replaces": "none" | [{…, "relation": "supersedes"}],
       "H2_evidence": null | {…}, "H3_refers_to_missing": "none" | [{"as_printed": "…", "where": "cl. 5.1"}],
       "H3_evidence": null | {…}},
 "I": [{"topic": "freight", "part": "General Terms", "page_or_clause": "cl. 6.2", "words": "…",
        "reading": "charged_at_cost"}],
 "J": {"notes": "…"},
 "K": [{"type": "missing_allowed_value", "description": "…", "page": "…"}],
 "L": {"return_line": "doc 001 | master_or_framework | live_rolling_presumed | layered: y | flags: 1 | work/forms/001.json"}}
```

`validate_forms.py` enforces the allowed values, the evidence rule (present, ≤ 40 words, and found
verbatim in `work/text/<id>.txt` when the page has native text), and that C1, C2, D1, D2 and D3 are
present (`not_found` allowed, blank not).
