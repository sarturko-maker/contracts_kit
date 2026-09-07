"""Evidence gate regression tests; all documents and forms here are invented."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "validate_forms", Path(__file__).resolve().parents[1] / "scripts" / "validate_forms.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def empty_form():
    """A complete form with honest unknown answers, not a shortened substitute form."""
    return {
        "A": {"doc_id": "001", "source_path": "invented.pdf", "file_type": "pdf", "sha256": "a" * 64,
              "pages": "2", "text_or_scan": "tt", "language_guess": "en", "docx_author": "n/a",
              "docx_dates": "n/a", "docx_tracked_changes": "n/a", "side": "customers",
              "account": "Imaginary Example", "match_basis": "same name", "match_confidence": "sure",
              "tree": "T1", "folder": "unsure"},
        "B": {"B1_cover_title": "not_found", "B1_evidence": None,
              "B2_document_kind": "not_found", "B2_evidence": None,
              "B3_whose_paper": "not_found", "B3_evidence": None,
              "B4_signed_status": "not_found", "B4_evidence": None,
              "B5_complete": "not_found", "B5_missing": "", "B5_evidence": None,
              "B6_duplicate_or_draft_of": "none", "B6_evidence": None, "B6a_best_copy": "not_found",
              "B7_language": "not_found", "B9_layered": "not_found", "B9_evidence": None},
        "C": {"C1_their_entities": "not_found", "C1_evidence": None,
              "C2_our_entities": "not_found", "C2_evidence": None,
              "C4_signature_dates_seen": "not_found", "C4_evidence": None},
        "D": {"D1_start_date": "not_found", "D1a_basis": "not_found", "D1_evidence": None,
              "D2_end_type": "not_found", "D2_detail": "", "D2_evidence": None,
              "D3_ended_evidence": "not_found", "D3_detail": "", "D3_evidence": None,
              "D4_status_as_read": "not_found", "D4_evidence": None},
        "E": {"E1_products_services": "not_found", "E1_evidence": None,
              "E2_territory": "not_found", "E2_detail": "", "E2_evidence": None,
              "E3_entities_covered": "not_found", "E3_evidence": None,
              "E4_trade_scope": "not_found", "E4_evidence": None},
        "F": [], "G": {"G1_governs_orders": "not_found", "G1_detail": "", "G1_evidence": None,
                         "G2_commitment_or_status": "none", "G2_detail": "", "G2_evidence": None},
        "H": {"H1_attaches_to": "none", "H1_evidence": None,
              "H2_replaces": "none", "H2_evidence": None,
              "H3_refers_to_missing": "none", "H3_evidence": None},
        "I": [], "J": {"notes": ""}, "K": [], "L": {"return_line": "not_found"},
    }


class FormsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.text = self.root / "001.txt"
        self.text.write_text("=== page 1 ===\nInvented Framework\n1. Orders may be placed\nunder this Agreement.\n"
                             "=== page 2 ===\nPricing Schedule\n2. Prices prevail over General Terms.\n", encoding="utf-8")
        self.form = empty_form()
        self.form["B"].update(B1_cover_title="Invented Framework", B1_evidence={"ref": "p. 1", "words": "Invented Framework"})

    def errors(self, form=None):
        return validator.validate_form(form or self.form, self.text)

    def assertError(self, fragment, form=None):
        self.assertTrue(any(fragment in error for error in self.errors(form)), self.errors(form))

    def test_complete_unknown_answers_are_allowed(self):
        self.assertEqual([], self.errors())
        self.assertEqual([], validator.evidence_warnings(self.form, self.text))

    def test_mandatory_survival_fields_may_not_be_missing_or_blank(self):
        for section, key in (("C", "C1_their_entities"), ("C", "C2_our_entities"),
                             ("D", "D1_start_date"), ("D", "D2_end_type"), ("D", "D3_ended_evidence")):
            for blank in (False, True):
                with self.subTest(field=key, blank=blank):
                    form = copy.deepcopy(self.form)
                    if blank:
                        form[section][key] = ""
                    else:
                        del form[section][key]
                    self.assertError(key, form)

    def test_fixed_choices_and_unknown_fields_are_rejected(self):
        self.form["B"]["B4_signed_status"] = "probably_signed"
        self.assertError("B4_signed_status")
        self.form = empty_form()
        self.form["A"]["invented_dcg_field"] = "yes"
        self.assertError("not in the fixed form")

    def test_required_evidence_and_empty_entity_lists(self):
        self.form["B"]["B1_evidence"] = None
        self.assertError("B1_evidence")
        self.form = empty_form()
        self.form["C"]["C1_their_entities"] = []
        self.assertError("C1_their_entities")

    def test_quote_must_be_on_cited_page_and_preserve_words(self):
        self.form["B"]["B1_evidence"]["ref"] = "page 2"
        self.assertError("at the cited location")
        self.form["B"]["B1_evidence"] = {"ref": "p. 1", "words": "Orders may be placed under this Agreement."}
        self.assertEqual([], self.errors())  # Line wraps are not words.
        self.form["B"]["B1_evidence"]["words"] = "Orders must be placed under this Agreement."
        self.assertError("not found verbatim")

    def test_quote_word_limit_and_impossible_citations(self):
        self.form["B"]["B1_evidence"]["words"] = " ".join(["invented"] * 41)
        self.assertError("exceeds 40 words")
        self.form["B"]["B1_evidence"] = {"ref": "page 9", "words": "Invented Framework"}
        self.assertError("page does not exist")
        self.form["B"]["B1_evidence"]["ref"] = "page 2-1"
        self.assertError("range is invalid")
        self.form["B"]["B1_evidence"]["ref"] = "the cover"
        self.assertError("must identify a page")

    def test_programme_clause_label_does_not_override_explicit_page(self):
        self.form['B']['B1_evidence'] = {'ref': 'P6 (p.2)', 'words': 'Prices prevail over General Terms.'}
        self.assertEqual([], self.errors())
        self.form['B']['B1_evidence']['ref'] = 'P6 (p.1)'
        self.assertError('at the cited location')
        self.form['B']['B1_evidence']['ref'] = 'P6'
        self.assertError('page does not exist')

    def test_scan_is_flagged_for_visual_review(self):
        self.text.write_text("=== page 1 ===\n[scan: look at the page]\n", encoding="utf-8")
        self.assertEqual([], self.errors())
        self.assertTrue(any("scanned page" in warning for warning in validator.evidence_warnings(self.form, self.text)))
        self.form["B"]["B1_evidence"]["words"] = "[scan: look at the page]"
        self.assertError("scan marker is not words")

    def test_word_paragraph_scope(self):
        self.form["A"].update(file_type="docx", pages="", text_or_scan="")
        self.text.write_text("[doc 001 | invented metadata]\n[¶ 1] Invented Framework\n[¶ 2] Prices change.\n", encoding="utf-8")
        self.form["B"]["B1_evidence"]["ref"] = "¶ 1"
        self.assertEqual([], self.errors())
        self.form["B"]["B1_evidence"]["ref"] = "paragraph 2"
        self.assertError("at the cited location")
        self.form["B"]["B1_evidence"]["ref"] = "p. 1"
        self.assertError("Word evidence must cite")

    def test_clause_only_quote_is_checked_and_location_warned(self):
        self.form["B"]["B1_evidence"] = {"ref": "cl. 1", "words": "Orders may be placed under this Agreement."}
        self.assertEqual([], self.errors())
        self.assertTrue(any("clause location" in warning for warning in validator.evidence_warnings(self.form, self.text)))
        self.form["B"]["B1_evidence"]["words"] = "This was never said."
        self.assertError("not found verbatim")

    def test_real_dates_and_required_details(self):
        evidence = {"ref": "p. 1", "words": "Invented Framework"}
        self.form["D"].update(D1_start_date="2025-02-30", D1a_basis="stated", D1_evidence=evidence)
        self.assertError("calendar date")
        self.form["D"].update(D1_start_date="2024-02-29", D2_end_type="rolling_until_notice", D2_evidence=evidence)
        self.assertError("D2_detail")
        self.form["D"]["D2_detail"] = "6 months"
        self.assertEqual([], self.errors())

    def test_layered_parts_inherit_and_resolve_precedence(self):
        evidence = {"ref": "p. 1", "words": "Invented Framework"}
        self.form["B"].update(B9_layered="yes", B9_evidence=evidence)
        self.assertError("at least one part")
        base = {"F1_part_name": "General Terms", "F1_evidence": evidence, "F2_pages_from_to": "1",
                "F3_part_kind": "general_terms", "F3_evidence": evidence,
                "F4_D": "inherits", "F5_E": "inherits", "F6_internal_precedence": "not_found", "F6_evidence": None}
        pricing = copy.deepcopy(base)
        pricing.update(F1_part_name="Pricing Schedule", F2_pages_from_to="2", F3_part_kind="pricing_schedule",
                       F6_internal_precedence={"wins_over": ["General Terms"], "page": "2", "words": "Prices prevail over General Terms."},
                       F6_evidence={"ref": "p. 2", "words": "Prices prevail over General Terms."})
        self.form["F"] = [base, pricing]
        self.assertEqual([], self.errors())
        saved_evidence = pricing["F6_evidence"]
        pricing["F6_evidence"] = None
        self.assertError("F6_evidence")
        pricing["F6_evidence"] = saved_evidence
        pricing["F6_internal_precedence"]["wins_over"] = ["Absent Part"]
        self.assertError("target is not a part")
        pricing["F6_internal_precedence"]["wins_over"] = ["General Terms"]
        base["F4_D"] = copy.deepcopy(self.form["D"])
        base["F4_D"]["D1_start_date"] = ""
        self.assertError("F4_D.D1_start_date")

    def test_topic_fixed_readings_and_silent_evidence(self):
        self.form["I"] = [{"topic": "freight", "part": "whole document", "page_or_clause": "p. 1",
                           "words": "Invented Framework", "reading": "cost_plus"}]
        self.assertError("reading")
        self.form["I"][0].update(reading="silent", words="not_found", page_or_clause="not_found")
        self.assertEqual([], self.errors())
        self.assertTrue(any("absence finding" in warning for warning in validator.evidence_warnings(self.form, self.text)))
        self.form["I"][0].update(topic="payment_terms", reading="30 days")
        self.assertError("reading")

    def test_missing_text_cannot_certify_evidence(self):
        self.assertTrue(any("text is unavailable" in error for error in validator.validate_form(self.form, self.root / "absent.txt")))

    def test_notes_return_line_and_duplicate_json_keys(self):
        self.form["J"]["notes"] = " ".join(["note"] * 201)
        self.assertError("200 words")
        self.form["J"]["notes"] = ""
        self.form["L"]["return_line"] = "doc 999 | wrong"
        self.assertError("does not agree")
        path = self.root / "001.json"
        path.write_text('{"A": {}, "A": {}}', encoding="utf-8")
        self.assertTrue(any("duplicate JSON key" in error for error in validator.validate_path(path, self.text)))

    def test_path_cli_and_filename_mismatch(self):
        path = self.root / "001.json"
        path.write_text(json.dumps(self.form), encoding="utf-8")
        self.assertEqual([], validator.validate_path(path, self.text))
        self.assertEqual(0, validator.main([str(path), "--text", str(self.text)]))
        path = self.root / "002.json"
        path.write_text(json.dumps(self.form), encoding="utf-8")
        self.assertTrue(any("filename" in error for error in validator.validate_path(path, self.text)))


if __name__ == "__main__":
    unittest.main()
