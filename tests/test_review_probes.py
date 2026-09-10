"""Regressions from the 10 September 2026 review of commit 0960686: invented rows, no model.

Each test states the invariant the review found broken. They drive file_documents() and
match_accounts() directly, so they run without a pile.
"""

import unittest
from unittest.mock import patch

import sort_light as s

ACCOUNT = "Example Customer Limited"
OURS = "Example Supplier Limited"


def packet(doc, *, title="", reference="", instrument="Master or supply agreement",
           signed="Signed by all parties", status="Current", dated="2020-01-01", end="",
           coverage="All supply between the parties", relation="", parent="", pages=10,
           customer=ACCOUNT, supplier=OURS, number=""):
    return {"doc_id": doc, "flags": [], "raw": {},
            "answers": {"title": title, "reference": reference, "parent_agreement": parent},
            "parsed": {"instrument": [instrument], "signed": [signed], "status": [status],
                       "supply_coverage": [coverage], "document_date": dated, "end_date": end,
                       "relation_to_parent": [relation] if relation else [],
                       "parent_dates": s.dates_in(parent), "customer": customer,
                       "customer_number": number, "supplier": supplier, "additional": []},
            "inventory": {"doc_id": doc, "sha256": "invented-" + doc, "pages": str(pages),
                          "text_pages": "0", "original_path": "/invented/" + doc + ".pdf",
                          "file_name": doc + ".pdf", "ext": "pdf", "readable": "yes"}}


def file_rows(*rows, as_at="2026-09-10"):
    packets = {r["doc_id"]: r for r in rows}
    targets = {doc: [{"target": ACCOUNT, "names": [ACCOUNT], "note": "", "basis": "same name",
                      "confidence": "sure"}] for doc in packets}
    return {d.doc: d for d in s.file_documents(as_at, targets, packets, {})}


def match_rows(rows, *, accounts=(ACCOUNT,), side="customers", mappings=(), ours=(OURS,)):
    erp = {"side": side, "accounts": [{"account": a} for a in accounts]}
    entities = {s.norm_name(r["name_as_printed"]): r for r in mappings}
    our_rows = [{"name": n, "status": "current", "note": ""} for n in ours]
    with patch.object(s, "load_erp", return_value=erp), \
            patch.object(s, "load_entity_map", return_value=(entities, list(mappings))), \
            patch.object(s, "our_entity_rows", return_value=our_rows), \
            patch.object(s, "read_json", return_value={}):
        return s.match_accounts({r["doc_id"]: r for r in rows})


def mapping(name, target, who="user"):
    return {"name_as_printed": name, "account": target, "basis": "same name",
            "confidence": "not sure" if target.startswith("_") else "sure",
            "decided_by": who, "note": "invented explicit decision"}


class MatchingProbes(unittest.TestCase):
    def test_an_applied_holding_decision_leaves_the_model_action_list(self):
        p = packet("001", customer="Example Regional Trading Limited")
        decisions, report = match_rows([p], mappings=[mapping(p["parsed"]["customer"], "_not-sure", "claude")])
        self.assertIn(p["parsed"]["customer"], report["applied"])
        self.assertEqual({}, s.unmatched_names(decisions, {"001": p}))
        self.assertIn(p["parsed"]["customer"], s.awaiting_user_names(decisions))

    def test_a_user_holding_decision_wins_over_an_exact_erp_match(self):
        decisions, _ = match_rows([packet("001")], mappings=[mapping(ACCOUNT, "_not-sure")])
        self.assertTrue(decisions["001"][0]["target"].startswith("_not-sure/"), str(decisions))

    def test_a_user_holding_decision_wins_over_the_company_number(self):
        p = packet("002", customer="Former Customer Name Limited", number="12345678")
        decisions, _ = match_rows([packet("001", number="12345678"), p],
                                  mappings=[mapping(p["parsed"]["customer"], "_not-sure")])
        self.assertTrue(decisions["002"][0]["target"].startswith("_not-sure/"), str(decisions["002"]))

    def test_a_suppliers_side_run_matches_the_supplier_cell(self):
        p = packet("001", customer=OURS, supplier="Example Vendor Limited")
        decisions, _ = match_rows([p], accounts=("Example Vendor Limited",), side="suppliers")
        self.assertEqual("Example Vendor Limited", decisions["001"][0]["target"])
        self.assertFalse(decisions["001"][0].get("reversed"))


class VersionProbes(unittest.TestCase):
    def test_an_old_short_agreement_does_not_sign_a_new_long_one(self):
        docs = file_rows(packet("001", title="Supply Agreement", dated="2019-01-01", pages=2),
                         packet("002", title="Supply Agreement", dated="2026-01-01", pages=40,
                                signed="Signature not established"))
        self.assertEqual("Signature not established", docs["002"].signed, str(docs["002"].notes))
        self.assertEqual("", docs["001"].copy_of)

    def test_a_signature_page_dated_with_its_body_still_joins_it(self):
        docs = file_rows(packet("001", title="Site Agreement", dated="2026-03-13", pages=1),
                         packet("002", title="Site Agreement", dated="2026-03-11", pages=5,
                                signed="Signature not established"))
        self.assertEqual("002", docs["001"].copy_of)
        self.assertEqual("Signed by all parties", docs["002"].signed)

    def test_an_unsigned_copy_is_not_an_executed_twin(self):
        docs = file_rows(packet("001", title="Supply Agreement", signed="Unsigned", dated="2026-01-01"),
                         packet("002", title="Supply Agreement", signed="Draft", dated="2025-01-01"))
        self.assertEqual(s.UNSURE, docs["002"].folder, str(docs["002"].notes))
        self.assertEqual(s.UNSURE, docs["001"].folder)


class LinkingProbes(unittest.TestCase):
    def test_a_quoted_reference_beats_an_unrelated_document_on_the_same_date(self):
        docs = file_rows(packet("001", title="Confidentiality Terms", instrument="NDA, MOU or letter of intent",
                                reference="NDA-B", coverage="No supply coverage"),
                         packet("002", title="Master Supply Terms", reference="SUP-A"),
                         packet("003", title="Termination Notice", dated="2026-01-01",
                                instrument="Notice letter", coverage="No supply coverage",
                                relation="Terminates", parent="Contract SUP-A dated 1 January 2020"))
        self.assertEqual("002", docs["003"].parent.doc, str(docs["003"].notes))
        self.assertEqual(s.F4, docs["002"].folder)
        self.assertEqual(s.F3, docs["001"].folder)

    def test_two_instruments_on_one_date_with_no_deciding_words_link_nothing(self):
        docs = file_rows(packet("001", title="Confidentiality Terms", instrument="NDA, MOU or letter of intent",
                                coverage="No supply coverage"),
                         packet("002", title="Master Supply Terms"),
                         packet("003", title="Termination Notice", dated="2026-01-01",
                                instrument="Notice letter", coverage="No supply coverage",
                                relation="Terminates", parent="our agreement dated 1 January 2020"))
        self.assertIsNone(docs["003"].parent)
        self.assertTrue(any("ambiguous" in f for f in docs["003"].flags), str(docs["003"].flags))
        self.assertEqual(s.F1, docs["002"].folder)

    def test_a_copy_quoting_its_own_reference_still_finds_the_master_it_amends(self):
        docs = file_rows(packet("001", title="Master Supply Agreement", reference="A/2021/114"),
                         packet("002", title="Amendment No. 1", reference="A/2021/114/A1", dated="2023-06-06",
                                instrument="Amendment or side letter", relation="Amends",
                                parent="Amendment No. 1 (A/2021/114/A1) to the Master Supply Agreement A/2021/114"),
                         packet("003", title="Amendment No. 1", reference="A/2021/114/A1", dated="2023-06-06",
                                instrument="Amendment or side letter", relation="Amends", pages=1,
                                signed="Signature not established",
                                parent="Amendment No. 1 (A/2021/114/A1) to the Master Supply Agreement A/2021/114"))
        self.assertEqual("001", docs["002"].parent.doc, str(docs["002"].flags))
        self.assertEqual(s.F1, docs["002"].folder)
        self.assertEqual("002", docs["003"].copy_of)

    def test_an_amendment_chain_settles_whatever_the_numbers(self):
        docs = file_rows(packet("001", title="Second Amendment", instrument="Amendment or side letter",
                                dated="2026-01-01", relation="Amends", parent="First Amendment dated 1 January 2025"),
                         packet("002", title="First Amendment", instrument="Amendment or side letter",
                                dated="2025-01-01", relation="Amends", parent="Master Terms dated 1 January 2020"),
                         packet("003", title="Master Terms"))
        self.assertEqual(s.F1, docs["001"].folder, str(docs["001"].flags))
        self.assertEqual(s.F1, docs["002"].folder)


class LifecycleProbes(unittest.TestCase):
    def test_not_yet_effective_with_a_future_end_is_not_live(self):
        doc = file_rows(packet("001", status="Not yet effective", dated="2027-01-01", end="2029-12-31"))["001"]
        self.assertEqual(s.UNSURE, doc.folder)

    def test_a_replacement_supersedes_from_its_own_date_not_its_expiry(self):
        docs = file_rows(packet("001", title="Original Terms", reference="OLD"),
                         packet("002", title="Replacement Terms", reference="NEW", dated="2026-01-01",
                                end="2029-12-31", relation="Supersedes", parent="OLD dated 1 January 2020"))
        self.assertEqual(s.F4, docs["001"].folder, str(docs["001"].flags))
        self.assertEqual(s.F1, docs["002"].folder)

    def test_a_live_extension_carries_an_expired_master_on(self):
        docs = file_rows(packet("001", title="Original Terms", reference="OLD", status="Expired", end="2025-12-31"),
                         packet("002", title="Extension", instrument="Amendment or side letter",
                                dated="2025-12-01", end="2027-12-31", relation="Extends",
                                parent="OLD dated 1 January 2020; extended to 31 December 2027"))
        self.assertEqual(s.F1, docs["001"].folder, str(docs["001"].flags))
        self.assertEqual(s.F1, docs["002"].folder)
        self.assertIn("extended by doc 002 to 2027-12-31", docs["001"].notes)

    def test_a_governing_instrument_without_established_signature_is_flagged(self):
        doc = file_rows(packet("001", signed="Signature not established"))["001"]
        self.assertEqual(s.F1, doc.folder)
        self.assertTrue(any("signature not established" in f for f in doc.flags), str(doc.flags))


if __name__ == "__main__":
    unittest.main()
