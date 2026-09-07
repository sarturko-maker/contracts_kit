#!/usr/bin/env python3
"""Prepare curated evaluation maps/forms. This is an oracle replay, not model extraction."""
import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "sample"))
from make_expected import (ACCOUNT1, ACCOUNT2, OURS, card, cards, entity_rows, ev, placement,
                           placements, prose, quoted, tree_proposals, write_cards, write_csv, write_json,
                           ENTITY_MAP_COLUMNS, PLACEMENT_COLUMNS)
from make_forms import build_forms, dates, scope, entity

ACCOUNT = "Quenby Marine Services"
KIT = ROOT / "work" / "eval" / "kit"


def extra_cards():
    parties = quoted(ev("p.1 cl.1", f"Parties: {ACCOUNT} (Customer) and {OURS} (Supplier)."))
    common = dict(q2_evidence=parties, q7_trade_scope="all purchases", q8_countries="United Kingdom")
    old = card("011", "2018 Marine Supply Master", "master or framework", ACCOUNT, **common,
        q3_evidence=quoted(ev("p.1 signatures", f"Signed for {ACCOUNT}: E. Vale. Date: 1 January 2018.")),
        q4_start_date="2018-01-01", q4_start_basis="stated", q4_end="rolling until twelve months' notice",
        q4_evidence=quoted(ev("p.1 cl.2", "This agreement starts on 1 January 2018 and continues until twelve months' written notice.")),
        q7_what_makes_it_govern="all marine equipment purchases; continuing use cannot be established from this document alone",
        q7_evidence=quoted(ev("p.1 cl.3", "All marine equipment purchases between the signatories in the United Kingdom fall under this agreement.")),
        q10_oddities="Later document in the inventory may replace this master; judge must settle the link.")
    current = card("012", "2024 Marine Supply Agreement - General Terms", "master or framework", ACCOUNT, **common,
        q3_evidence=quoted(ev("p.2 signatures", f"Signed for {ACCOUNT}: E. Vale. Date: 1 January 2024.")),
        q4_start_date="2024-01-01", q4_start_basis="stated", q4_end="rolling until six months' written notice", q4_status="live",
        q4_evidence=quoted(ev("p.1 cl.3", "These General Terms continue until either party gives six months' written notice.")),
        q5_parts="yes", q5_parts_detail="General Terms: pp.1-3, live (Schedule A excluded) | Schedule A - 2024 Pump Programme: p.2, dead (expired 2024-12-31)",
        q5_precedence=quoted(ev("p.1 cl.9", "Schedule A prevails over these General Terms only during its stated term and for the products it names.")),
        q6_replaces="2018 Marine Supply Master → doc 011",
        q6_evidence=quoted(ev("p.1 cl.2", "Effective 1 January 2024, this agreement supersedes the 2018 Marine Supply Master in its entirety.")),
        q7_what_makes_it_govern="all marine equipment purchases; 2026 confirmation establishes continuing use",
        q7_evidence=quoted(ev("p.1 cl.4", "All marine equipment purchases between the signatories in the United Kingdom are placed under these General Terms.")),
        q10_oddities='General Terms payment 21 days; expired Schedule A payment 10 days. General freight reasonable delivery expense capped GBP 250 per consignment; expired Schedule A includes freight. Customer paper; sole supplier for all marine equipment purchases. Confirmation p.3 C2: "all current marine equipment purchases remain under those General Terms and no notice has been served."')
    return {"011": old, "012": current}


def extra_forms(kit):
    inventory = {r["doc_id"]: r for r in csv.DictReader((kit / "work/inventory.csv").open())}
    out = {}
    for doc, card_value in extra_cards().items():
        inv = inventory[doc]
        old = doc == "011"
        start_date, printed = ("2018-01-01", "1 January 2018") if old else ("2024-01-01", "1 January 2024")
        title = ev("p.1 title", card_value["q1_title"])
        parties = ev("p.1 cl.1", f"Parties: {ACCOUNT} (Customer) and {OURS} (Supplier).")
        signed = ev("p.1 signatures" if old else "p.2 signatures", f"Signed for {ACCOUNT}: E. Vale. Date: {printed}.")
        start = ev("p.1 cl.2", "This agreement starts on 1 January 2018 and continues until twelve months' written notice." if old else "Effective 1 January 2024, this agreement supersedes the 2018 Marine Supply Master in its entirety.")
        end = start if old else ev("p.1 cl.3", "These General Terms continue until either party gives six months' written notice.")
        trade = ev("p.1 cl.3" if old else "p.1 cl.4", "All marine equipment purchases between the signatories in the United Kingdom fall under this agreement." if old else "All marine equipment purchases between the signatories in the United Kingdom are placed under these General Terms.")
        form = {
            "A": {"doc_id": doc, "source_path": inv["original_path"], "file_type": "pdf", "sha256": inv["sha256"], "pages": inv["pages"], "text_or_scan": inv["page_kinds"], "language_guess": "en", "docx_author": "n/a", "docx_dates": "n/a", "docx_tracked_changes": "n/a", "side": "customers", "account": ACCOUNT, "match_basis": "same name", "match_confidence": "sure", "tree": "T1", "folder": "4-not-live" if old else "1-governs-trade"},
            "B": {"B1_cover_title": card_value["q1_title"], "B1_evidence": title, "B2_document_kind": "master_or_framework", "B2_evidence": title, "B3_whose_paper": "ours" if old else "theirs", "B3_evidence": ev("p.1 cl.5" if old else "p.1 cl.8", "This agreement is on the Supplier's paper and makes no exclusivity commitment." if old else "This is the Customer's paper."), "B4_signed_status": "both", "B4_evidence": signed, "B5_complete": "yes", "B5_missing": "", "B5_evidence": None, "B6_duplicate_or_draft_of": "none", "B6_evidence": None, "B6a_best_copy": "yes", "B7_language": "en", "B9_layered": "no" if old else "yes", "B9_evidence": title if old else ev("p.2 A5", "After this Schedule expires, the General Terms alone apply to pump purchases.")},
            "C": {"C1_their_entities": [entity(ACCOUNT)], "C1_evidence": parties, "C2_our_entities": [entity(OURS)], "C2_evidence": parties, "C4_signature_dates_seen": f"Both: {printed}", "C4_evidence": signed},
            "D": dates(start_date, "stated", start, "rolling_until_notice", "twelve months" if old else "six months", end, status="live_rolling_presumed", status_ev=end),
            "E": scope("marine equipment", trade, "single_country", "United Kingdom", trade, "signatories_only", trade, "all_purchases", trade),
            "F": [], "G": {"G1_governs_orders": "yes", "G1_detail": "all marine equipment purchases", "G1_evidence": trade, "G2_commitment_or_status": "none" if old else "exclusivity_or_sole_supplier", "G2_detail": "" if old else "sole supplier", "G2_evidence": None if old else ev("p.1 cl.7", "The Customer appoints the Supplier as sole supplier for all its marine equipment purchases for the life of these General Terms.")},
            "H": {"H1_attaches_to": "none", "H1_evidence": None, "H2_replaces": "none" if old else [{"as_printed": "2018 Marine Supply Master", "doc_id": "011", "relation": "supersedes"}], "H2_evidence": None if old else start, "H3_refers_to_missing": "none", "H3_evidence": None},
            "I": [], "J": {"notes": "Status as read is rolling; doc 012 supplies the later supersession link. The placement is dead after linking; this form does not quote another document as its own evidence." if old else "Schedule A expired. The General Terms include the continuing-use confirmation on p.3; its later signatures confirm use without changing the start date. Topics off: payment and freight require source reading."},
            "K": [{"type": "missing_field", "description": "A rolling termination notice period has no dedicated release-1 DCG property.", "page": end["ref"]}],
            "L": {"return_line": "pending"},
        }
        if not old:
            expiry = ev("p.2 A2", "This Schedule runs from 1 January 2024 to 31 December 2024 and expires without renewal.")
            part_scope = ev("p.2 A1", "This Schedule forms part of the 2024 Marine Supply Agreement and applies only to pump purchases.")
            precedence = ev("p.1 cl.9", "Schedule A prevails over these General Terms only during its stated term and for the products it names.")
            form["F"] = [
                {"F1_part_name": "General Terms", "F1_evidence": ev("p.1 title", "General Terms"), "F2_pages_from_to": "1-3", "F3_part_kind": "general_terms", "F3_evidence": ev("p.1 title", "General Terms"), "F4_D": "inherits", "F5_E": "inherits", "F6_internal_precedence": "not_found", "F6_evidence": None},
                {"F1_part_name": "Schedule A - 2024 Pump Programme", "F1_evidence": ev("p.2 title", "Schedule A - 2024 Pump Programme"), "F2_pages_from_to": "2", "F3_part_kind": "programme_or_project_terms", "F3_evidence": part_scope,
                 "F4_D": dates("2024-01-01", "stated", expiry, "fixed_date", "2024-12-31", expiry, "expiry_date_passed", "2024-12-31", expiry, "expired_by_date", expiry),
                 "F5_E": scope("pumps", part_scope, "single_country", "United Kingdom", trade, "signatories_only", trade, "defined_product_set", part_scope),
                 "F6_internal_precedence": {"wins_over": ["General Terms"], "words": precedence["words"], "page": precedence["ref"]}, "F6_evidence": precedence}]
        form["L"]["return_line"] = f"doc {doc} | master_or_framework | live_rolling_presumed | layered: {'n' if old else 'y'} | flags: 1 | work/forms/{doc}.json"
        out[doc] = form
    return out


def main():
    if not KIT.exists():
        subprocess.run([sys.executable, str(HERE / "run.py"), "prepare"], check=True)
    def run(*args):
        return subprocess.run([sys.executable, *args], cwd=KIT, text=True, capture_output=True, check=True).stdout
    logs = [run("scripts/prepare.py", "pile", "--account-column", "customer_account", "--side", "customers")]
    write_cards(KIT / "work/cards", cards() | extra_cards())
    all_placements = placements()
    all_placements[ACCOUNT] = [
        placement("011", "T1", "4-not-live", "rule 4: replaced in entirety by doc 012 on 2024-01-01", what_would_change="Evidence that the replacement did not take effect."),
        placement("012", "T1", "1-governs-trade", "rule 6: live General Terms govern all purchases; 2026 continuing-use confirmation", replaces="011", parts_status="General Terms: live | Schedule A - 2024 Pump Programme: dead")]
    notes = prose()
    notes[ACCOUNT] = """## The position
Doc 012 General Terms govern all marine equipment purchases, on the customer's paper, from 1 January 2024 with six months' notice. Its p.3 confirmation establishes continuing use in September 2026. Schedule A's pump programme expired on 31 December 2024; the General Terms alone now cover pumps. Doc 012 superseded doc 011 in its entirety.

## Overlaps and conflicts
Doc 012 Schedule A prevailed only during its term and for pumps (p.1 cl.9); that part is dead. The General Terms now apply. Doc 011 has been superseded.

## Couldn't find or couldn't tell
No current-use gap: the confirmation is on doc 012 p.3.

## Questions for the business
1. Confirm that current marine equipment purchases follow doc 012 General Terms.
"""
    for account, rows in all_placements.items():
        write_csv(KIT / "work/placements" / f"{account}.csv", rows, PLACEMENT_COLUMNS)
        (KIT / "work/placements" / f"{account}.md").write_text(notes[account], encoding="utf-8")
    matches = entity_rows() + [{"name_as_printed": ACCOUNT, "account": ACCOUNT, "basis": "same name", "confidence": "sure", "decided_by": "claude", "note": "Exact invented ERP row."}]
    write_csv(KIT / "inputs/entity-map.csv", matches, ENTITY_MAP_COLUMNS)
    write_csv(KIT / "inputs/our-entities.csv", [{"name": OURS}], ["name"])
    logs += [run("scripts/sort.py"), run("scripts/place.py", "--all")]
    forms = build_forms(KIT, KIT / "work/forms") | extra_forms(KIT)
    for doc, form in forms.items():
        # Keep source paths inside this isolated pile rather than the sample generator's path.
        form["A"]["source_path"] = next(r["original_path"] for r in csv.DictReader((KIT / "work/inventory.csv").open()) if r["doc_id"] == doc)
        write_json(KIT / "work/forms" / f"{doc}.json", form)
    for account, rows in all_placements.items():
        if account in tree_proposals():
            write_json(KIT / 'work/trees' / f'{account}.json', tree_proposals()[account])
            continue
        trees = []
        for tree in sorted({row["tree"] for row in rows}):
            docs = [r["doc_id"] for r in rows if r["tree"] == tree]
            family = "C13" if docs == ["006"] else "not_found" if docs in (["003"], ["009"], ["005"]) else "C2"
            trees.append({"tree": tree, "family": family, "confidence": "no_family_fits" if family == "not_found" else "fairly_sure", "doc_ids": docs, "overlays": ["O3"] if docs == ["003"] else [],
                          "structural_evidence": f"Curated fixture: docs {', '.join(docs)}; " + ("standalone overlay, guidance or transaction; no governing-family structural test is satisfied" if family == "not_found" else "period commercial letter attached to relationship" if family == "C13" else "master instrument with no participation instrument or complete price layer; links and component lives follow the forms")})
        write_json(KIT / "work/trees" / f"{account}.json", {"account": account, "trees": trees})
    logs += [run("scripts/validate_forms.py", "--all"), run("scripts/graph.py", "--all", "--as-of", "2026-09-06")]
    # Mode B gets the stage 1 map, not stage 2 facts appended to the document list.
    # Rebuilding these reports leaves forms and graph rows available to mode C.
    logs.append(run('scripts/place.py', '--all'))
    (KIT.parent / "fixture-build.log").write_text("\n".join(logs), encoding="utf-8")
    (KIT.parent / "FIXTURE-PROVENANCE.md").write_text("Curated cards, placements and forms; deterministic oracle replay, not model extraction. Fresh question trials compare answering on these map/form artifacts.\n", encoding="utf-8")
    print(f"Curated eval map/forms ready: {KIT}; eleven validated forms. This is not model extraction.")


if __name__ == "__main__":
    main()
