"""Renamed copies: how kit_common.filed_name builds a name and where the name is used.

The rules are: '<doc id> <kind> <counterparty> <date>[ <status>].<ext>', a duplicate is
'<doc id> duplicate-of-<other>.<ext>', an unresolved identity is '<doc id> unidentified
[<pages>pp].<ext>'. No agent writes a filename; the originals and work/files are never renamed.
"""

import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sample"))
sys.path.insert(0, str(ROOT / "scripts"))
from kit_common import (  # noqa: E402
    CORPUS_COLUMNS, FILED_NAME_LIMIT, STATUS_FOLDERS, counterparty_for, date_slug, filed_name,
    kind_slug, name_slug, naming_from_card, unique_filed_name,
)
from make_expected import (  # noqa: E402
    ACCOUNT1, ACCOUNT2, NORTH, OURS, PARENT, isolated_kit, replay,
)


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def hashes(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(folder).rglob("*") if p.is_file()}


class FiledNameRules(unittest.TestCase):
    def test_the_four_shapes_of_a_name(self):
        self.assertEqual("017 master-agreement Sturmore-Rail-Group 2021-02-22.pdf",
                         filed_name("017", "pdf", kind="master or framework",
                                    counterparty="Sturmore Rail Group", date="2021-02-22"))
        self.assertEqual("013 master-agreement Sturmore-Rail-Group 2016-07-18 not-live.pdf",
                         filed_name("013", "pdf", kind="master or framework",
                                    counterparty="Sturmore Rail Group", date="2016-07-18",
                                    status="not-live"))
        self.assertEqual("002 duplicate-of-015.pdf", filed_name("002", "pdf", duplicate_of="015"))
        self.assertEqual("022 unidentified 42pp.pdf",
                         filed_name("022", "pdf", unresolved=True, pages=42))

    def test_duplicate_and_unresolved_beat_the_ordinary_parts(self):
        # A duplicate is named by what it duplicates, whatever else the card says.
        self.assertEqual("002 duplicate-of-015.docx",
                         filed_name("002", "docx", kind="master or framework", counterparty="Acme",
                                    date="2021-01-01", status="unsure", duplicate_of="015"))
        self.assertEqual("022 unidentified.pdf",
                         filed_name("022", "pdf", counterparty="Acme", unresolved=True))
        self.assertEqual("022 unidentified.pdf",
                         filed_name("022", "pdf", unresolved=True, pages="0"))
        self.assertEqual("022 unidentified.pdf",
                         filed_name("022", "pdf", unresolved=True, pages="not counted"))

    def test_a_name_is_never_empty(self):
        self.assertEqual("001.pdf", filed_name("001", "pdf"))
        self.assertEqual("001.pdf", filed_name("001", "pdf", kind="not found",
                                               counterparty="   ", date="not found"))
        self.assertEqual("001.pdf", filed_name("001", ".PDF", counterparty="!!!"))
        self.assertEqual("001", filed_name("001", ""))
        self.assertEqual("document.pdf", filed_name("", "pdf"))

    def test_hostile_characters_never_reach_the_filename(self):
        hostile = {
            "../../etc/passwd": "etcpasswd",
            r"C:\\Windows\\system32": "CWindowssystem32",
            'quote " star * pipe |': "quote-star-pipe",
            "trailing dots... ": "trailing-dots",
            "  leading and trailing  ": "leading-and-trailing",
            "Angstrom\u00c5 & S\u00f8ns, Ltd.": "AngstromA-Sons-Ltd",
            "line\nbreak\ttab": "line-break-tab",
            "null\x00byte\x1f": "nullbyte",
            "CON": "CON",
        }
        for raw, expected in hostile.items():
            with self.subTest(raw=raw):
                self.assertEqual(expected, name_slug(raw))
                name = filed_name("001", "pdf", kind="other", counterparty=raw)
                self.assertTrue(name.startswith("001 "), name)
                self.assertFalse(any(c in name for c in '\\/:*?"<>|'), name)
                self.assertEqual(name, name.encode("ascii", "ignore").decode("ascii"))
                self.assertFalse(any(ord(c) < 32 for c in name), name)
                self.assertEqual(Path(name).name, name)

    def test_length_is_capped_at_120_characters(self):
        name = filed_name("101", "pdf", kind="master or framework", counterparty="Verylongname " * 20,
                          date="2020-01-01", status="not-live")
        self.assertEqual(FILED_NAME_LIMIT, len(name))
        self.assertTrue(name.startswith("101 master-agreement "), name)
        self.assertTrue(name.endswith(" 2020-01-01 not-live.pdf"), name)
        # A single long word is cut rather than the name being dropped.
        long_one = filed_name("101", "pdf", counterparty="x" * 400)
        self.assertLessEqual(len(long_one), FILED_NAME_LIMIT)
        self.assertTrue(long_one.startswith("101 x"))

    def test_kind_slugs_cover_the_card_and_the_filer_vocabulary(self):
        expected = {
            "master or framework": "master-agreement",
            "local adoption of a group agreement": "local-adoption",
            "standard terms": "standard-terms",
            "project or programme agreement": "site-agreement",
            "schedule or annex": "schedule",
            "amendment or side letter": "amendment",
            "pricing or rebate letter": "rebate-letter",
            "NDA": "nda",
            "guarantee": "guarantee",
            "other overlay (data terms, code of conduct, EDI)": "overlay",
            "purchase order or quote": "order",
            "credit application": "credit-application",
            "internal playbook or guidance": "internal-notes",
            "letter or email": "letter",
            "other": "other",
            "draft master": "draft-master",
            "Mutual Non-Disclosure Agreement": "nda",
            "signed MSA": "master-agreement",
        }
        for kind, slug in expected.items():
            with self.subTest(kind=kind):
                self.assertEqual(slug, kind_slug(kind))
        for blank in ("", "   ", "not found", "none", "not assessed", "unknown"):
            self.assertEqual("", kind_slug(blank))
        # An unknown free-text kind keeps a short, safe slug of its own words.
        self.assertEqual("warranty-certificate", kind_slug("Warranty certificate"))
        self.assertLessEqual(len(kind_slug("A " * 40)), 24)

    def test_dates_are_iso_when_they_can_be_read_and_omitted_otherwise(self):
        for text, expected in [("2021-02-22", "2021-02-22"), ("2021-2-2", "2021-02-02"),
                               ("14 March 2019", "2019-03-14"), ("1st Feb. 2026", "2026-02-01"),
                               ("March 14, 2019", "2019-03-14"),
                               ("effective 6 April 2026 (stated)", "2026-04-06")]:
            with self.subTest(text=text):
                self.assertEqual(expected, date_slug(text))
        for text in ("", "not found", "none", "rolling until notice", "2021-13-40", "Q3 2019",
                     "06/04/2026"):
            with self.subTest(text=text):
                self.assertEqual("", date_slug(text))
        self.assertEqual("001 nda Acme.pdf",
                         filed_name("001", "pdf", kind="NDA", counterparty="Acme", date="not found"))

    def test_a_status_slug_appears_only_when_it_is_given(self):
        self.assertEqual("001 nda Acme.pdf", filed_name("001", "pdf", kind="NDA", counterparty="Acme"))
        for status in ("not-live", "unsure", "draft"):
            name = filed_name("001", "pdf", kind="NDA", counterparty="Acme", status=status)
            self.assertTrue(name.endswith(f" {status}.pdf"), name)
        # An unsigned draft of a master is a kind of its own, not a master plus 'draft'.
        self.assertEqual("004 draft-master Acme.docx",
                         filed_name("004", "docx", kind="master or framework", counterparty="Acme",
                                    status="draft"))
        self.assertEqual("004 draft-master Acme.docx",
                         filed_name("004", "docx", kind="draft-master", counterparty="Acme",
                                    status="draft"))


class NamingFromCards(unittest.TestCase):
    def card(self, **answers):
        card = {"q1_title": "Supply Agreement", "q1_kind": "master or framework", "q3_signed": "both",
                "q4_start_date": "2019-03-14", "q9_copy_or_draft_of": "none"}
        card.update(answers)
        return card

    def test_the_card_supplies_kind_and_start_date(self):
        parts = naming_from_card(self.card())
        self.assertEqual({"kind": "master or framework", "date": "2019-03-14", "status": "",
                          "duplicate_of": ""}, parts)
        self.assertEqual("001 master-agreement Acme-Ltd 2019-03-14.pdf",
                         filed_name("001", "pdf", counterparty="Acme Ltd", **parts))

    def test_an_unsigned_draft_master_is_named_draft_master(self):
        draft = self.card(q1_title="Master Services Agreement - draft dated 15 January 2026",
                          q3_signed="nobody", q4_start_date="not found")
        self.assertEqual("draft-master", naming_from_card(draft)["kind"])
        # Nobody signs a purchase order either; that does not make it a draft master.
        order = self.card(q1_title="Purchase Order PL-2026-042", q1_kind="purchase order or quote",
                          q3_signed="nobody")
        self.assertEqual("purchase order or quote", naming_from_card(order)["kind"])

    def test_the_placement_folder_supplies_the_status_slug(self):
        for folder, status in [("1-governs-trade", ""), ("2-governs-part-of-trade", ""),
                               ("3-live-not-trade", ""), ("4-not-live", "not-live"),
                               ("6-business-practice", ""), ("unsure", "unsure")]:
            with self.subTest(folder=folder):
                self.assertEqual(status, naming_from_card(self.card(), {"folder": folder})["status"])
        draft = self.card(q1_title="MSA draft", q3_signed="nobody")
        self.assertEqual("draft", naming_from_card(
            draft, {"folder": "5-orders-drafts-duplicates"})["status"])
        self.assertEqual("", naming_from_card(
            self.card(), {"folder": "5-orders-drafts-duplicates"})["status"])

    def test_a_duplicate_is_found_in_the_reason_or_the_link_fields(self):
        for placement in ({"reason": "Duplicate of doc 015; same text."},
                          {"replaces": "duplicate of 015"},
                          {"attaches_to": "015", "attach_kind": "duplicate of"},
                          {"attach_kind": "duplicate of 015"}):
            with self.subTest(placement=placement):
                self.assertEqual("015", naming_from_card(self.card(), placement)["duplicate_of"])
        self.assertEqual("", naming_from_card(self.card(), {"reason": "Amends doc 015."})["duplicate_of"])

    def test_the_counterparty_is_the_account_or_the_printed_company(self):
        self.assertEqual(ACCOUNT1, counterparty_for(ACCOUNT1, [NORTH]))
        self.assertEqual(NORTH, counterparty_for("_not-sure/" + NORTH, [NORTH]))
        self.assertEqual(NORTH, counterparty_for("_not-on-the-list/" + NORTH, []))
        self.assertEqual("", counterparty_for("_no-name-found", []))
        self.assertEqual("", counterparty_for("_unreadable", [NORTH]))
        self.assertEqual(NORTH, counterparty_for("", [NORTH, OURS]))
        self.assertEqual("", counterparty_for("", []))


class Collisions(unittest.TestCase):
    def test_the_document_number_keeps_two_identical_documents_apart(self):
        arguments = dict(kind="master or framework", counterparty="Acme Ltd", date="2019-03-14")
        first = filed_name("001", "pdf", **arguments)
        second = filed_name("002", "pdf", **arguments)
        self.assertNotEqual(first, second)
        used = set()
        unique_filed_name(first, used)
        unique_filed_name(second, used)
        self.assertEqual({first, second}, used)
        # Even at the length cap the number survives, so the names still differ.
        long = dict(kind="master or framework", counterparty="Verylongname " * 20, date="2019-03-14")
        self.assertNotEqual(filed_name("001", "pdf", **long), filed_name("002", "pdf", **long))

    def test_a_real_collision_is_an_error_not_a_silent_overwrite(self):
        used = set()
        unique_filed_name("001 nda Acme.pdf", used)
        with self.assertRaises(AssertionError):
            unique_filed_name("001 nda Acme.pdf", used)


class FilingReportNames(unittest.TestCase):
    """Cheap filing: names come from the filing record; nothing else is renamed."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-naming-filing-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        self.pile = Path(self.temp.name) / "pile"
        shutil.copytree(ROOT / "sample/pile", self.pile)
        self.command("prepare.py", str(self.pile), "--account-column", "customer_account",
                     "--side", "customers")
        for name in ("entity-map.csv", "our-entities.csv"):
            shutil.copyfile(ROOT / "sample/expected" / name, self.root / "inputs" / name)
        shutil.copytree(ROOT / "sample/expected/cards", self.root / "work/cards")

    def command(self, script, *args):
        result = subprocess.run([sys.executable, f"scripts/{script}", *args], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_filed_copies_are_named_from_the_filing_record(self):
        before_pile, before_work = hashes(self.pile), hashes(self.root / "work/files")
        self.command("filing.py", "--report")
        corpus = {r["doc_id"]: r for r in rows(self.root / "out/customers/CORPUS.csv")}
        self.assertIn("filed_as", corpus["001"])
        self.assertEqual("001 master-agreement Tallowfield-Industries 2019-03-14.pdf",
                         corpus["001"]["filed_as"])
        self.assertEqual("005 order Pellmont-Logistics-Group 2026-04-06.pdf", corpus["005"]["filed_as"])
        # No status slug at the cheap stage: legal status is unassessed.
        for row in corpus.values():
            self.assertNotIn(" not-live.", row["filed_as"])
            self.assertNotIn(" unsure.", row["filed_as"])
        # The unreadable file has no copy and so no filed name.
        self.assertEqual("", corpus["010"]["filed_as"])
        for row in corpus.values():
            if row["filed_as"]:
                copy = self.root / row["file_path"]
                self.assertEqual(row["filed_as"], copy.name)
                self.assertTrue(copy.is_file())
                self.assertEqual("files", copy.parent.name)
        # documents.csv carries the same column, and the README lists the renamed copy.
        account = self.root / "out/customers" / ACCOUNT1
        self.assertIn("filed_as", rows(account / "documents.csv")[0])
        readme = (account / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Renamed copies", readme)
        self.assertIn(f"- 001 — {corpus['001']['filed_as']} — original: "
                      f"{corpus['001']['original_path']}", readme)
        # Copy, never move or rename: the pile and work/files are byte-for-byte unchanged.
        self.assertEqual(before_pile, hashes(self.pile))
        self.assertEqual(before_work, hashes(self.root / "work/files"))
        self.assertTrue((self.root / "work/files/001.pdf").is_file())

    def test_an_unresolved_identity_is_filed_as_unidentified_with_its_page_count(self):
        shutil.rmtree(self.root / "work/cards")
        self.command("filing.py", "--report")
        corpus = {r["doc_id"]: r for r in rows(self.root / "out/customers/CORPUS.csv")}
        self.assertEqual("_needs-reading", corpus["003"]["account"])
        self.assertEqual("003 unidentified 2pp.pdf", corpus["003"]["filed_as"])
        self.assertTrue((self.root / corpus["003"]["file_path"]).is_file())
        readme = (self.root / "out/customers/_needs-reading/README.md").read_text(encoding="utf-8")
        self.assertIn("- 003 — 003 unidentified 2pp.pdf — original:", readme)
        unreadable = (self.root / "out/customers/_unreadable/README.md").read_text(encoding="utf-8")
        self.assertIn("- 010 — (no copy: unreadable) — original:", unreadable)


class AnalysisNames(unittest.TestCase):
    """Full analysis: names come from the card and the judge's placement."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-naming-place-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        self.pile = Path(self.temp.name) / "pile"
        shutil.copytree(ROOT / "sample/pile", self.pile)
        self.before_pile = hashes(self.pile)
        self.log = replay(self.root, pile=self.pile)
        self.corpus = {r["doc_id"]: r for r in rows(self.root / "out/customers/CORPUS.csv")}

    def test_status_folder_copies_are_named_from_the_card_and_the_placement(self):
        expected = {
            "001": "001 master-agreement Tallowfield-Industries 2019-03-14.pdf",
            "002": "002 amendment Tallowfield-Industries 2026-02-01.pdf",
            "003": "003 nda Tallowfield-Industries 2019-05-01 not-live.pdf",
            "004": "004 draft-master Pellmont-Logistics-Group unsure.docx",
            "005": "005 order Pellmont-Logistics-Group 2026-04-06.pdf",
            "006": "006 rebate-letter Pellmont-Logistics-Group 2026-01-01.pdf",
            "007": "007 other Pellmont-Logistics-Group unsure.jpg",
            "008": "008 site-agreement Tallowfield-Industries 2026-03-01.pdf",
            "009": "009 internal-notes Tallowfield-Industries 2026-02-01.docx",
        }
        self.assertEqual(expected, {d: self.corpus[d]["filed_as"] for d in expected})
        copies = [p for p in (self.root / "out").rglob("*")
                  if p.is_file() and p.parent.name in STATUS_FOLDERS]
        self.assertEqual(set(expected.values()), {p.name for p in copies})
        self.assertEqual(len(copies), len(expected), "one copy per placed document")
        self.assertNotIn("WARNING:", self.log)

    def test_filed_as_is_a_corpus_column_in_every_generated_list(self):
        self.assertIn("filed_as", CORPUS_COLUMNS)
        self.assertEqual(CORPUS_COLUMNS[CORPUS_COLUMNS.index("original_path") + 1], "filed_as")
        for account in (ACCOUNT1, ACCOUNT2):
            documents = rows(self.root / "out/customers" / account / "documents.csv")
            self.assertIn("filed_as", documents[0])
            self.assertEqual([r["filed_as"] for r in documents],
                             [self.corpus[r["doc_id"]]["filed_as"] for r in documents])
        # An unreadable file has no copy; its row says so rather than inventing a name.
        self.assertEqual("not readable by the kit", self.corpus["010"]["filed_as"])

    def test_the_note_lists_the_filed_name_of_every_document(self):
        note = (self.root / "out/customers" / ACCOUNT1 / "ANALYSIS.md").read_text(encoding="utf-8")
        self.assertIn("| tree | doc | filed as | title |", note)
        self.assertIn(f"| T1 | doc 001 | {self.corpus['001']['filed_as']} |", note)
        self.assertIn(f"filed as `{self.corpus['003']['filed_as']}`", note)
        for doc_id in ("001", "002", "003", "008", "009"):
            self.assertIn(self.corpus[doc_id]["filed_as"], note)

    def test_originals_and_prepared_copies_are_never_renamed(self):
        self.assertEqual(self.before_pile, hashes(self.pile))
        self.assertEqual(sorted(p.name for p in (self.root / "work/files").iterdir()),
                         ["001.pdf", "002.pdf", "003.pdf", "004.docx", "005.pdf", "006.pdf",
                          "007.jpg", "008.pdf", "009.docx"])

    def test_holding_folder_copies_use_the_printed_company_or_unidentified(self):
        # An undecided name keeps the printed company; a card with no company is unidentified.
        entity_path = self.root / "inputs/entity-map.csv"
        entity_rows = rows(entity_path)
        for row in entity_rows:
            if row["name_as_printed"] == PARENT:
                row.update(account="_not-sure", confidence="not sure")
        with entity_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(entity_rows[0]))
            writer.writeheader()
            writer.writerows(entity_rows)
        (self.root / "inputs/corrections.csv").write_text(
            "doc_id,field,value,reason\n"
            "005,q2_their_signing_entities,none,invented test correction\n"
            "005,q2_their_group_companies,none,invented test correction\n", encoding="utf-8")
        result = subprocess.run([sys.executable, "scripts/sort.py"], cwd=self.root, text=True,
                                capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        holding = self.root / "out/customers/_not-sure" / PARENT
        self.assertEqual(["003 nda Oxbrook-Holdings-plc 2019-05-01.pdf"],
                         [p.name for p in holding.iterdir()])
        self.assertEqual(["005 unidentified 1pp.pdf"],
                         [p.name for p in (self.root / "out/customers/_no-name-found").iterdir()])
        # The account copies waiting to be judged carry the account name and no status slug.
        to_judge = self.root / "out/customers" / ACCOUNT1 / "_to-judge"
        self.assertEqual(["001 master-agreement Tallowfield-Industries 2019-03-14.pdf",
                          "002 amendment Tallowfield-Industries 2026-02-01.pdf",
                          "008 site-agreement Tallowfield-Industries 2026-03-01.pdf",
                          "009 internal-notes Tallowfield-Industries 2026-02-01.docx"],
                         sorted(p.name for p in to_judge.iterdir()))

    def test_every_generated_name_is_unique_and_windows_safe(self):
        copies = [p for p in (self.root / "out").rglob("*")
                  if p.is_file() and p.parent.name in STATUS_FOLDERS]
        self.assertEqual(len(copies), len({p.name for p in copies}))
        for path in copies:
            self.assertLessEqual(len(path.name), FILED_NAME_LIMIT)
            self.assertFalse(any(c in path.name for c in '\\/:*?"<>|'), path.name)
            self.assertEqual(path.name, path.name.encode("ascii", "ignore").decode("ascii"))
            self.assertFalse(path.stem.endswith((" ", ".")), path.name)


if __name__ == "__main__":
    unittest.main()
