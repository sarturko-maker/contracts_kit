"""The nine explicit, evidence-backed sample forms; topics are off by default."""
from copy import deepcopy
from pathlib import Path
import csv
import json
import re

from make_expected import ACCOUNT1, ACCOUNT2, GERMAN, NORTH, OURS, PARENT, cards, ev, placements


def first_evidence(text):
    match = re.match(r'(.+?): "([^"]+)"', text)
    return ev(*match.groups()) if match else None


def entity(name, role="signatory", page="1"):
    return {"name_as_printed": name, "address_or_registration_if_printed": "not_found", "role": role, "page": page}


def dates(start="not_found", basis="not_found", start_ev=None, end="not_found", detail="", end_ev=None,
          ended="none_found", ended_detail="", ended_ev=None, status="unknown", status_ev=None):
    return {"D1_start_date": start, "D1a_basis": basis, "D1_evidence": start_ev,
            "D2_end_type": end, "D2_detail": detail, "D2_evidence": end_ev,
            "D3_ended_evidence": ended, "D3_detail": ended_detail, "D3_evidence": ended_ev,
            "D4_status_as_read": status, "D4_evidence": status_ev}


def scope(products="not_found", products_ev=None, territory="not_found", territory_detail="", territory_ev=None,
          entities="not_found", entities_ev=None, trade="not_found", trade_ev=None):
    return {"E1_products_services": products, "E1_evidence": products_ev,
            "E2_territory": territory, "E2_detail": territory_detail, "E2_evidence": territory_ev,
            "E3_entities_covered": entities, "E3_evidence": entities_ev,
            "E4_trade_scope": trade, "E4_evidence": trade_ev}


def build_forms(kit, destination):
    kit, destination = Path(kit), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    inventory = {r["doc_id"]: r for r in csv.DictReader((kit / "work/inventory.csv").open())}
    sort_rows = {r["doc_id"]: r for r in csv.DictReader((kit / "work/logs/sort.csv").open())}
    placed = {r["doc_id"]: r for rows in placements().values() for r in rows}
    kinds = {"001": "master_or_framework", "002": "amendment_or_side_letter", "003": "nda", "004": "master_or_framework", "005": "order_or_quote", "006": "pricing_or_rebate_letter", "007": "other", "008": "project_or_programme_agreement", "009": "internal_playbook"}
    signed = {"both": "both", "nobody": "unsigned", "us only": "ours_only"}
    result = {}
    for doc_id, card in cards().items():
        inv, match, place = inventory[doc_id], sort_rows[doc_id], placed[doc_id]
        page = "¶ 1" if inv["file_type"] == "docx" else "p.1"
        title_ev = ev(page, card["q1_title"])
        parties_ev = first_evidence(card["q2_evidence"])
        signing_ev = first_evidence(card["q3_evidence"])
        date_ev = first_evidence(card["q4_evidence"])
        trade_ev = first_evidence(card["q7_evidence"])
        their_name = PARENT if doc_id == "003" else NORTH if doc_id in ("001", "002", "008") else ACCOUNT1 if doc_id == "009" else ACCOUNT2
        role = "other" if doc_id in ("006", "009") else "signatory"
        ours_role = "other" if doc_id == "009" else "signatory"
        form = {
            "A": {"doc_id": doc_id, "source_path": f"sample/pile/{inv['file_name']}", "file_type": inv["file_type"], "sha256": inv["sha256"], "pages": inv["pages"] or "not_found", "text_or_scan": inv["page_kinds"], "language_guess": inv["language"], "docx_author": inv["docx_author"], "docx_dates": inv["docx_created"] + " | " + inv["docx_modified"], "docx_tracked_changes": inv["docx_tracked_changes"], "side": "customers", "account": match["account"], "match_basis": match["basis"], "match_confidence": match["confidence"], "tree": place["tree"], "folder": place["folder"]},
            "B": {"B1_cover_title": card["q1_title"], "B1_evidence": title_ev, "B2_document_kind": kinds[doc_id], "B2_evidence": title_ev, "B3_whose_paper": "not_found", "B3_evidence": None, "B4_signed_status": signed[card["q3_signed"]], "B4_evidence": signing_ev, "B5_complete": "yes", "B5_missing": "", "B5_evidence": None, "B6_duplicate_or_draft_of": "none", "B6_evidence": None, "B6a_best_copy": "yes", "B7_language": "en", "B9_layered": card["q5_parts"], "B9_evidence": title_ev},
            "C": {"C1_their_entities": [entity(their_name, role, page)], "C1_evidence": parties_ev, "C2_our_entities": [entity(OURS, ours_role, page)], "C2_evidence": parties_ev, "C4_signature_dates_seen": "not_found", "C4_evidence": None},
            "D": dates(status_ev=date_ev or title_ev),
            "E": scope(),
            "F": [],
            "G": {"G1_governs_orders": "not_found" if doc_id == "007" else "no" if doc_id in ("003", "005", "009") else "yes", "G1_detail": card["q7_what_makes_it_govern"], "G1_evidence": trade_ev, "G2_commitment_or_status": "none", "G2_detail": "", "G2_evidence": None},
            "H": {"H1_attaches_to": "none", "H1_evidence": None, "H2_replaces": "none", "H2_evidence": None, "H3_refers_to_missing": "none", "H3_evidence": None},
            "I": [], "J": {"notes": ""},
            "K": [{"type": "missing_field", "description": "Execution status needs a separate property from lifecycle status; DCG status cannot preserve both answers at once.", "page": signing_ev["ref"]}],
            "L": {"return_line": "pending"},
        }
        if doc_id in ("001", "002", "006", "008", "004"):
            paper = "theirs" if doc_id in ("004", "008") else "ours"
            paper_ev = {
                "001": ev("p.1 cl.10", f"This agreement is on {OURS} paper."),
                "002": ev("p.1 cl.6", f"Prepared on {OURS} paper."),
                "004": ev("¶ 7", f"This draft was prepared on {ACCOUNT2} paper."),
                "006": ev("p.1 cl.4", f"Prepared on {OURS} paper."),
                "008": ev("p.1 cl.2", f"Prepared on {NORTH} paper."),
            }[doc_id]
            form["B"].update(B3_whose_paper=paper, B3_evidence=paper_ev)
        if doc_id == "001":
            start = ev("p.4 (picture inspected)", "14 March 2019")
            end = ev("p.1 cl.3", "General Terms continue until either party gives twelve months' written notice.")
            form["C"]["C1_their_entities"] += [entity(PARENT, "other", "p.3"), entity(GERMAN, "affiliate_listed", "p.3")]
            form["C"].update(C1_evidence=ev("p.3 S1-S2", f"{NORTH} trades as {ACCOUNT1} and is a subsidiary of {PARENT}. S2. Named affiliate: {GERMAN}, Germany, may order under the General Terms."), C4_signature_dates_seen="Marrowgate Supply Ltd: 12 March 2019; Tallowfield Industries (North) Limited: 14 March 2019", C4_evidence=start)
            form["D"] = dates("2019-03-14", "date_of_last_signature", start, "rolling_until_notice", "twelve months as printed", end, status="live_rolling_presumed", status_ev=end)
            products = ev("p.1 cl.4", "All purchases of industrial supplies between the parties are placed under these General Terms.")
            covered = ev("p.1 cl.7", "The General Terms cover the Customer and the named affiliate in Schedule 1 in the United Kingdom and Germany.")
            form["E"] = scope("industrial supplies", products, "regional", "United Kingdom; Germany", covered, "named_affiliates", covered, "all_purchases", products)
            form["B"]["B9_evidence"] = ev("p.2, programme clause 6", "General Terms continue after the Programme Terms expire.")
            expiry = ev("p.2, programme clause 2", "These Programme Terms expire on 31 August 2024 without renewal.")
            programme_scope = ev("p.2, programme clause 5", "Scope: industrial supplies for Hexley Refit in the United Kingdom only, for the Customer only.")
            precedence = ev("p.1 cl.9", "Programme Terms prevail over General Terms in case of conflict.")
            form["F"] = [
                {"F1_part_name": "General Terms", "F1_evidence": ev("p.1 title", "General Terms"), "F2_pages_from_to": "1", "F3_part_kind": "general_terms", "F3_evidence": ev("p.1 title", "General Terms"), "F4_D": "inherits", "F5_E": "inherits", "F6_internal_precedence": "not_found", "F6_evidence": None},
                {"F1_part_name": "Programme Terms - Hexley Refit", "F1_evidence": ev("p.2 title", "Programme Terms - Hexley Refit"), "F2_pages_from_to": "2", "F3_part_kind": "programme_or_project_terms", "F3_evidence": ev("p.2 title", "Programme Terms - Hexley Refit"),
                 "F4_D": dates("2019-03-14", "date_of_last_signature", start, "fixed_date", "2024-08-31", expiry, "expiry_date_passed", "2024-08-31", expiry, "expired_by_date", expiry),
                 "F5_E": scope("industrial supplies for Hexley Refit", programme_scope, "single_country", "United Kingdom", programme_scope, "signatories_only", programme_scope, "project_site_or_programme", programme_scope),
                 "F6_internal_precedence": {"wins_over": ["General Terms"], "words": precedence["words"], "page": "p.1 cl.9"}, "F6_evidence": precedence},
            ]
            form["J"]["notes"] = "General Terms operative text is on p.1; Schedule 1 identity material (p.3) and signatures (p.4) share its life. Programme expired 2024-08-31. General Terms are presumed rolling; the judge must check linked documents for continuing use or changes. Topics are off; freight must be read from the pointed-to part."
            form["K"].append({"type": "missing_field", "description": "A rolling termination notice period has no dedicated release-1 DCG property.", "page": "p.1 cl.3"})
            form["K"].append({"type": "missing_field", "description": "Schedule 1 affiliate 'may order under the General Terms' may be deemed participation, but the fixed form does not encode a per-entity deemed participation instrument. Mapper must assess the tree using this source wording.", "page": "p.3 S2"})
        elif doc_id == "002":
            form["C"].update(C4_signature_dates_seen="Both: 1 February 2026", C4_evidence=signing_ev)
            form["D"] = dates("2026-02-01", "stated", date_ev, "rolling_until_notice", "six months; life of General Terms", date_ev, status="live_rolling_presumed", status_ev=ev("p.1 cl.4", "The parties confirm that all their current purchases continue under the General Terms of that Agreement."))
            form["E"] = scope(trade="all_purchases", trade_ev=trade_ev)
            form["H"].update(H1_attaches_to=[{"as_printed": "Supply Agreement dated 14 March 2019", "doc_id": "001", "relation": "amends"}], H1_evidence=first_evidence(card["q6_evidence"]))
            form["K"].append({"type": "missing_field", "description": "A rolling termination notice period has no dedicated release-1 DCG property.", "page": "p.1 cl.3"})
        elif doc_id == "003":
            form["C"].update(C4_signature_dates_seen="Both: 1 May 2019", C4_evidence=signing_ev)
            form["D"] = dates("2019-05-01", "stated", date_ev, "fixed_date", "2022-04-30", date_ev, "expiry_date_passed", "2022-04-30", date_ev, "expired_by_date", date_ev)
            form["E"] = scope(entities="signatories_only", entities_ev=ev("p.1 cl.6 (picture inspected)", "Only the signatories are covered; no country scope is specified."), trade="none")
            form["J"]["notes"] = "Both scanned pages and the signature picture were visually inspected. No obligations survive expiry (p.1 cl.4). Group match comes from doc 001 Schedule 1, not this NDA."
        elif doc_id == "004":
            service = ev("¶ 6", "Services: logistics support in the United Kingdom, for the signatories only.")
            form["E"] = scope("logistics support", service, "single_country", "United Kingdom", service, "signatories_only", service, "all_purchases", trade_ev)
            form["J"]["notes"] = "Unsigned DOCX, two tracked revisions and two comments; no embedded images. Dates and duration are expressly proposed, so D1/D2 remain not_found. Doc 007 is related signature evidence; no complete execution body establishes this draft as agreed."
            form["K"].append({"type": "missing_allowed_value", "description": "DCG lifecycle status does not preserve unsigned draft execution separately.", "page": "¶ 8-9"})
        elif doc_id == "005":
            form["D"] = dates("2026-04-06", "stated", date_ev, status="unknown", status_ev=date_ev)
            service = ev("p.1", "One purchase only: 20 invented transit trays, GBP 400 total, for a United Kingdom site.")
            form["E"] = scope("20 invented transit trays", service, "single_country", "United Kingdom", service, "signatories_only", parties_ev, "none")
            form["J"]["notes"] = "Delivery due date is not treated as an expiry; performance is not found. This is a single purchase, not standard terms."
        elif doc_id == "006":
            form["C"].update(C4_signature_dates_seen="Marrowgate Supply Ltd: 1 January 2026", C4_evidence=signing_ev)
            form["D"] = dates("2026-01-01", "stated", date_ev, "fixed_date", "2026-12-31", date_ev, status="live_fixed_term", status_ev=date_ev)
            form["E"] = scope("logistics support", date_ev, entities="signatories_only", entities_ev=ev("p.1 cl.3", "Only the addressee is covered."), trade="period", trade_ev=trade_ev)
            form["J"]["notes"] = "Only the supplier signed; customer countersignature is expressly unnecessary (cl.3). The fixed form has no addressee-only scope choice; C1 preserves the recipient as other."
            form["K"].append({"type": "missing_allowed_value", "description": "One-sided binding rebate letter: ours_only is not a DCG lifecycle status.", "page": "p.1 cl.3"})
            form["K"].append({"type": "missing_allowed_value", "description": "The fixed scope choices have no addressee-only choice for a unilateral rebate; signatories_only is the closest choice and C1 preserves addressee as other.", "page": "p.1 cl.3"})
        elif doc_id == "007":
            missing = ev("image p.1 (picture inspected)", "The text pages of the execution version are not attached to this page.")
            form["B"].update(B5_complete="no", B5_missing="complete execution text", B5_evidence=missing)
            form["C"]["C2_evidence"] = ev("image p.1 (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 16 January 2026.")
            form["C"].update(C4_signature_dates_seen="Both: 16 January 2026", C4_evidence=date_ev)
            form["D"] = dates(status="unknown", status_ev=missing)
            form["H"].update(H1_attaches_to=[{"as_printed": "Master Services Agreement dated 15 January 2026", "doc_id": "004", "relation": "forms_part_of"}], H1_evidence=first_evidence(card["q6_evidence"]), H3_refers_to_missing=[{"as_printed": "text pages of the execution version", "where": "image p.1"}], H3_evidence=missing)
            form["J"]["notes"] = "Signature picture inspected. This is separate evidence linked by title/date to doc 004; forms_part_of records the document connection but does not authenticate the draft body. Signature date alone does not prove when unknown final terms take effect."
            form["K"].append({"type": "missing_allowed_value", "description": "A detached signature page is evidence about execution, not a complete contract; kind other needs its signature-page function retained.", "page": "image p.1"})
        elif doc_id == "008":
            form["C"].update(C4_signature_dates_seen="Both: 1 March 2026", C4_evidence=signing_ev)
            form["D"] = dates("2026-03-01", "stated", date_ev, "fixed_date", "2027-03-31", date_ev, status="live_fixed_term", status_ev=date_ev)
            form["E"] = scope("industrial supplies for Hexley Works site", trade_ev, "single_country", "United Kingdom", trade_ev, "signatories_only", ev("p.1 cl.7", "Only the signatories are covered."), "project_site_or_programme", trade_ev)
            form["J"]["notes"] = "Clause 5 refers to the 2019 Supply Agreement for orders outside this site. It is a scope cross-reference, not an amendment or adoption; this site contract remains a separate tree. Hexley Works is distinct from Hexley Refit."
        elif doc_id == "009":
            form["D"] = dates("2026-02-01", "stated", date_ev, status="live_rolling_presumed", status_ev=date_ev)
            form["E"] = scope(territory="single_country", territory_detail="United Kingdom", territory_ev=ev("¶ 8", "Coverage: United Kingdom account team only."), trade="none")
            form["J"]["notes"] = "Internal working guidance, not a contract. End type not_found because 'until replaced' has no matching fixed answer. Tracked revisions and one comment remain drafting evidence; the printed guidance says it is current. No signature image."
            form["K"].append({"type": "missing_allowed_value", "description": "internal_playbook has no DCG contract node type; retained in its form and corpus with a gap, not a governing instrument.", "page": "¶ 1-3"})
        form["L"]["return_line"] = f"doc {doc_id} | {kinds[doc_id]} | {form['D']['D4_status_as_read']} | layered: {'y' if form['B']['B9_layered'] == 'yes' else 'n'} | flags: {len(form['K'])} | work/forms/{doc_id}.json"
        (destination / f"{doc_id}.json").write_text(json.dumps(form, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result[doc_id] = form
    return result
