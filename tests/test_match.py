"""One company, one group: 'Brenlow Dockyard Svcs Ltd' and 'Brenlow Dockyard Services Limited'.

group_key() canonicalises the few company words that are written two ways, so a holding folder
is not split by an abbreviation and the user decides the name once. The exact printed name,
normalised by norm_name(), is still what an entity-map lookup tries first.
"""

import csv
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
    ENTITY_MAP_COLUMNS, entity_row_for, group_key, norm_name,
)
from make_expected import ACCOUNT1, isolated_kit  # noqa: E402

SVCS = "Brenlow Dockyard Svcs Ltd"
SERVICES = "Brenlow Dockyard Services Limited"


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class GroupKey(unittest.TestCase):
    def test_the_two_spellings_of_one_company_share_a_key(self):
        self.assertEqual(group_key(SVCS), group_key(SERVICES))

    def test_the_words_that_are_written_two_ways(self):
        pairs = [
            ("Acme Ltd", "Acme Limited"),
            ("Acme Ltd.", "Acme Limited"),
            ("Acme plc", "Acme PLC"),
            ("Acme plc", "Acme Public Limited Company"),
            ("Acme Svcs Ltd", "Acme Services Limited"),
            ("Acme Co", "Acme Company"),
            ("Acme Corp", "Acme Corporation"),
            ("Acme Inc", "Acme Incorporated"),
            ("Acme & Sons", "Acme and Sons"),
            ("The Acme Company", "Acme Co"),
            ("Acme Limited,", "Acme Ltd"),
            ("  Acme   Ltd  ", "acme ltd"),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertEqual(group_key(left), group_key(right))

    def test_different_companies_keep_different_keys(self):
        different = [("Acme Ltd", "Acme plc"), ("Acme Ltd", "Acme Holdings Ltd"),
                     ("Acme GmbH", "Acme Ltd"), ("Brenlow Dockyard Ltd", SVCS)]
        for left, right in different:
            with self.subTest(left=left, right=right):
                self.assertNotEqual(group_key(left), group_key(right))

    def test_a_foreign_form_is_left_exactly_as_printed(self):
        self.assertEqual("tallowfield industrie gmbh", group_key("Tallowfield Industrie GmbH"))
        self.assertEqual(group_key("Tallowfield Industrie GmbH"), group_key("tallowfield industrie gmbh"))

    def test_blank_names_have_no_key(self):
        for blank in ("", "   ", None, ".", ",", "()"):
            with self.subTest(blank=blank):
                self.assertEqual("", group_key(blank))


class EntityMapLookup(unittest.TestCase):
    def map_of(self, *names):
        return {norm_name(name): {"name_as_printed": name, "account": account, "basis": "in the document",
                                  "confidence": "sure", "decided_by": "user", "note": ""}
                for name, account in names}

    def test_the_exact_printed_name_still_wins(self):
        entities = self.map_of((SERVICES, ACCOUNT1), (SVCS, "Somewhere Else"))
        self.assertEqual("Somewhere Else", entity_row_for(entities, SVCS)["account"])
        self.assertEqual(ACCOUNT1, entity_row_for(entities, SERVICES)["account"])

    def test_an_abbreviation_finds_the_row_written_out_in_full(self):
        entities = self.map_of((SERVICES, ACCOUNT1))
        self.assertEqual(ACCOUNT1, entity_row_for(entities, SVCS)["account"])
        self.assertEqual(SERVICES, entity_row_for(entities, SVCS)["name_as_printed"])

    def test_a_name_nobody_mapped_is_still_undecided(self):
        entities = self.map_of((SERVICES, ACCOUNT1))
        self.assertIsNone(entity_row_for(entities, "Someone Else Ltd"))
        self.assertIsNone(entity_row_for(entities, ""))

    def test_two_map_rows_that_disagree_are_no_decision(self):
        entities = self.map_of((SERVICES, ACCOUNT1), ("Brenlow Dockyard Services Ltd", "Another Account"))
        self.assertIsNone(entity_row_for(entities, SVCS))


class GroupedHoldingFolders(unittest.TestCase):
    """End to end: two spellings, one holding folder, and one name to decide."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-match-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        self.pile = Path(self.temp.name) / "pile"
        shutil.copytree(ROOT / "sample/pile", self.pile)
        self.command("prepare.py", str(self.pile), "--account-column", "customer_account",
                     "--side", "customers")
        shutil.copyfile(ROOT / "sample/expected/our-entities.csv", self.root / "inputs/our-entities.csv")
        shutil.copytree(ROOT / "sample/expected/cards", self.root / "work/cards")
        # Two documents name the same company, spelled two ways. Nothing else names it.
        (self.root / "inputs/corrections.csv").write_text(
            "doc_id,field,value,reason\n"
            f"003,q2_their_signing_entities,{SVCS} (signatory),invented test correction\n"
            f"005,q2_their_signing_entities,{SERVICES} (signatory),invented test correction\n",
            encoding="utf-8")

    def command(self, script, *args):
        result = subprocess.run([sys.executable, f"scripts/{script}", *args], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout

    def write_map(self, extra=()):
        entity_rows = rows(ROOT / "sample/expected/entity-map.csv") + list(extra)
        path = self.root / "inputs/entity-map.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=ENTITY_MAP_COLUMNS)
            writer.writeheader()
            writer.writerows(entity_rows)

    def test_both_spellings_land_in_one_holding_folder(self):
        self.write_map()
        out = self.command("sort.py")
        holding = self.root / "out/customers/_not-on-the-list"
        self.assertEqual([SVCS], [p.name for p in holding.iterdir()])
        self.assertEqual(2, len(list((holding / SVCS).iterdir())))
        # One name to decide, not two.
        decisions = [line for line in out.splitlines() if "Brenlow" in line and line.startswith("  - ")]
        self.assertEqual(1, len(decisions), out)
        # The sort log says which folder each document is in, under the one printed name.
        log = {r["doc_id"]: r for r in rows(self.root / "work/logs/sort.csv")}
        self.assertEqual(f"_not-on-the-list/{SVCS}", log["003"]["account"])
        self.assertEqual(f"_not-on-the-list/{SVCS}", log["005"]["account"])
        self.assertIn(f"printed as {SERVICES!r}", log["005"]["note"])

    def test_one_entity_map_row_matches_both_spellings(self):
        self.write_map([{"name_as_printed": SERVICES, "account": ACCOUNT1, "basis": "in the document",
                         "confidence": "sure", "decided_by": "user", "note": "one decision for both spellings"}])
        self.command("sort.py")
        log = {r["doc_id"]: r for r in rows(self.root / "work/logs/sort.csv")}
        self.assertEqual(ACCOUNT1, log["003"]["account"])
        self.assertEqual(ACCOUNT1, log["005"]["account"])
        self.assertFalse((self.root / "out/customers/_not-on-the-list").exists())


if __name__ == "__main__":
    unittest.main()
