"""The two card checks: question 2 read the wrong way round, and evidence over forty words.

Both are warnings. A card is never edited by a script, and no run stops because of them; the
reader is asked again, or the user decides. scripts/check_cards.py prints the same warnings for
cards that already exist.
"""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sample"))
sys.path.insert(0, str(ROOT / "scripts"))
import kit_common  # noqa: E402
from kit_common import (  # noqa: E402
    CARD_EVIDENCE_KEYS, CARD_KEYS, card_warnings, check_card, evidence_quotes, load_card,
)
from make_expected import OURS, NORTH, isolated_kit  # noqa: E402

REVERSED = "may be reversed"


def card(**answers):
    """A card with the sample's answers to question 2 unless the test changes them."""
    values = {key: "not found" for key in CARD_KEYS}
    values.update(doc_id="001", q1_title="Supply Agreement", q1_kind="master or framework",
                  q2_their_signing_entities=f"{NORTH} (signatory)", q2_their_group_companies="none",
                  q2_our_entity=OURS, q3_signed="both")
    values.update(answers)
    return values


class QuestionTwoReversal(unittest.TestCase):
    def test_a_card_the_right_way_round_says_nothing(self):
        self.assertEqual([], card_warnings(card(), [OURS]))

    def test_our_entity_in_the_other_sides_slot_is_warned_about(self):
        reversed_card = card(q2_their_signing_entities=f"{OURS} (signatory)", q2_our_entity=NORTH)
        messages = card_warnings(reversed_card, [OURS])
        self.assertEqual(["doc 001: question 2 may be reversed (our entity in the other side's slot)"],
                         messages)

    def test_our_entity_in_both_slots_is_still_warned_about(self):
        both = card(q2_their_signing_entities=f"{NORTH} (signatory) | {OURS} (parent listed)")
        self.assertEqual(1, len(card_warnings(both, [OURS])))
        group = card(q2_their_group_companies=f"{OURS} (other)")
        self.assertEqual(1, len(card_warnings(group, [OURS])))

    def test_an_our_entity_slot_that_is_not_one_of_ours_is_warned_about(self):
        # 'not found' in our slot, or somebody else's name there, both need a second look.
        for value in ("not found", "none", NORTH):
            with self.subTest(value=value):
                messages = card_warnings(card(q2_our_entity=value), [OURS])
                self.assertTrue(any(REVERSED in m for m in messages), messages)

    def test_the_check_is_skipped_when_we_have_no_list_of_our_names(self):
        reversed_card = card(q2_their_signing_entities=f"{OURS} (signatory)", q2_our_entity=NORTH)
        self.assertEqual([], card_warnings(reversed_card, []))
        self.assertEqual([], card_warnings(reversed_card))

    def test_an_abbreviated_spelling_of_our_name_is_still_our_name(self):
        # 'Marrowgate Supply Limited' and 'Marrowgate Supply Ltd' are one company.
        long_form = OURS.replace("Ltd", "Limited")
        self.assertEqual([], card_warnings(card(q2_our_entity=long_form), [OURS]))
        moved = card(q2_their_signing_entities=f"{long_form} (signatory)", q2_our_entity=NORTH)
        self.assertTrue(any(REVERSED in m for m in card_warnings(moved, [OURS])))

    def test_a_role_in_brackets_does_not_hide_our_name(self):
        moved = card(q2_their_signing_entities=f"{OURS} (guarantor)", q2_our_entity=NORTH)
        self.assertTrue(any(REVERSED in m for m in card_warnings(moved, [OURS])))


class EvidenceLength(unittest.TestCase):
    def quote(self, words):
        return 'p.1 cl.2: "' + " ".join(f"word{n}" for n in range(words)) + '"'

    def test_forty_words_is_allowed_and_forty_one_is_warned_about(self):
        self.assertEqual([], card_warnings(card(q4_evidence=self.quote(40))))
        messages = card_warnings(card(q4_evidence=self.quote(41)))
        self.assertEqual(1, len(messages))
        self.assertIn("q4_evidence quotes 41 words", messages[0])
        self.assertIn("doc 001", messages[0])

    def test_every_evidence_field_is_checked_and_only_those(self):
        self.assertEqual(["q2_evidence", "q3_evidence", "q4_evidence", "q6_evidence", "q7_evidence"],
                         CARD_EVIDENCE_KEYS)
        for key in CARD_EVIDENCE_KEYS:
            with self.subTest(key=key):
                self.assertEqual(1, len(card_warnings(card(**{key: self.quote(45)}))))
        # q10_oddities is not evidence: it is not measured.
        self.assertEqual([], card_warnings(card(q10_oddities=self.quote(60))))

    def test_each_joined_quote_is_measured_on_its_own(self):
        two_short = self.quote(30) + " | " + self.quote(30)
        self.assertEqual([], card_warnings(card(q2_evidence=two_short)))
        one_long = self.quote(30) + " | " + self.quote(50)
        self.assertEqual(1, len(card_warnings(card(q2_evidence=one_long))))

    def test_an_answer_with_no_quotation_marks_is_still_measured(self):
        bare = "p.1: " + " ".join(f"word{n}" for n in range(50))
        self.assertEqual(1, len(card_warnings(card(q7_evidence=bare))))
        self.assertEqual([], card_warnings(card(q7_evidence="not found")))
        self.assertEqual([], card_warnings(card(q7_evidence="")))

    def test_evidence_quotes_reads_the_card_shape(self):
        self.assertEqual(["the exact words", "more words"],
                         evidence_quotes('p.3: "the exact words" | cl. 12.1: "more words"'))
        self.assertEqual(["curly words"], evidence_quotes('p.3: “curly words”'))
        self.assertEqual([], evidence_quotes("not found"))
        self.assertEqual([], evidence_quotes(""))


class LoadCardWarns(unittest.TestCase):
    """load_card runs the checks, prints them and changes nothing."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-cards-test-")
        self.addCleanup(self.temp.cleanup)
        self.cards = Path(self.temp.name) / "cards"
        self.cards.mkdir()
        self.original = (kit_common.WORK_CARDS, kit_common._OUR_NAMES_FOR_CHECKS)
        kit_common.WORK_CARDS = self.cards
        kit_common._OUR_NAMES_FOR_CHECKS = [OURS]

        def restore():
            kit_common.WORK_CARDS, kit_common._OUR_NAMES_FOR_CHECKS = self.original
        self.addCleanup(restore)

    def write(self, doc_id, values):
        (self.cards / f"{doc_id}.json").write_text(json.dumps(values), encoding="utf-8")

    def loaded(self, doc_id, quiet=False):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            result = load_card(doc_id, quiet=quiet)
        return result, printed.getvalue()

    def test_load_card_warns_and_returns_the_card_as_written(self):
        values = card(doc_id="017", q2_their_signing_entities=f"{OURS} (signatory)",
                      q2_our_entity=NORTH)
        self.write("017", values)
        loaded, printed = self.loaded("017")
        self.assertIn("WARNING: doc 017: question 2 may be reversed", printed)
        self.assertEqual(values["q2_our_entity"], loaded["q2_our_entity"])
        self.assertEqual(values["q2_their_signing_entities"], loaded["q2_their_signing_entities"])
        self.assertEqual(json.loads((self.cards / "017.json").read_text()), values)

    def test_quiet_suppresses_the_warnings(self):
        self.write("017", card(doc_id="017", q2_our_entity=NORTH))
        _, printed = self.loaded("017", quiet=True)
        self.assertEqual("", printed)

    def test_no_list_of_our_names_means_no_reversal_warning(self):
        kit_common._OUR_NAMES_FOR_CHECKS = []
        self.write("017", card(doc_id="017", q2_our_entity=NORTH))
        _, printed = self.loaded("017")
        self.assertEqual("", printed)

    def test_check_card_returns_what_it_printed(self):
        values = card(doc_id="017", q2_our_entity=NORTH)
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            messages = check_card(values, our_names=[OURS])
        self.assertEqual(1, len(messages))
        self.assertIn(messages[0], printed.getvalue())


class CheckCardsCommand(unittest.TestCase):
    """python scripts/check_cards.py prints the warnings for cards that already exist."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-check-cards-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        (self.root / "work" / "cards").mkdir(parents=True)
        (self.root / "inputs" / "our-entities.csv").write_text(f"name\n{OURS}\n", encoding="utf-8")
        self.write("001", card(doc_id="001"))
        self.write("002", card(doc_id="002", q2_their_signing_entities=f"{OURS} (signatory)",
                               q2_our_entity=NORTH))
        self.write("003", card(doc_id="003",
                               q3_evidence='p.4: "' + " ".join(["word"] * 41) + '"'))

    def write(self, doc_id, values):
        (self.root / "work" / "cards" / f"{doc_id}.json").write_text(json.dumps(values),
                                                                     encoding="utf-8")

    def run_check(self, *args):
        result = subprocess.run([sys.executable, "scripts/check_cards.py", *args], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout

    def test_every_card_is_checked_and_the_exit_code_is_zero(self):
        out = self.run_check()
        self.assertIn("doc 002: question 2 may be reversed", out)
        self.assertIn("doc 003: q3_evidence quotes 41 words", out)
        self.assertNotIn("doc 001:", out)
        self.assertIn("3 cards checked; 2 warnings", out)

    def test_one_document_can_be_checked_on_its_own(self):
        out = self.run_check("2")
        self.assertIn("doc 002: question 2 may be reversed", out)
        self.assertIn("1 cards checked; 1 warnings", out)
        self.assertNotIn("q3_evidence", out)

    def test_without_our_entities_only_the_evidence_length_is_checked(self):
        (self.root / "inputs" / "our-entities.csv").unlink()
        out = self.run_check()
        self.assertIn("is not there, so question 2 is not checked", out)
        self.assertNotIn(REVERSED, out)
        self.assertIn("doc 003: q3_evidence quotes 41 words", out)

    def test_nothing_is_edited(self):
        before = (self.root / "work" / "cards" / "002.json").read_text()
        self.run_check()
        self.assertEqual(before, (self.root / "work" / "cards" / "002.json").read_text())


if __name__ == "__main__":
    unittest.main()
