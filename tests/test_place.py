"""What place.py must do without a judge.

Three rules from the live test:
- an ERP account with no documents gets its folder, a README saying nothing is filed and the
  empty diagram, written by the script, with no placements file and no Opus call;
- a document in a holding folder has been read but has no account, so it keeps its card facts
  in CORPUS.csv as `unassessed (no account)` and INDEX.md lists it under "Needs a decision";
- an ERP account name with a slash, a colon or a trailing space is found at the folder-safe
  placements name the judge is told to write, and at the raw name with a warning.
"""

import csv
import json
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
    ENTITY_MAP_COLUMNS, PLACEMENT_COLUMNS, STATUS_FOLDERS, safe_folder_name,
)
from make_expected import ACCOUNT1, ACCOUNT2, GERMAN, NORTH, PARENT, isolated_kit  # noqa: E402

HOSTILE = "Brenlow/Dockyard: Svcs Ltd "     # slash, colon and a trailing space
COLON_ONLY = "Pellmont: Logistics "          # no slash, so the raw name is a legal filename
EMPTY_ONE = "Havershill Marine Ltd"
EMPTY_TWO = "Quenby Rail Services"
UNASSESSED = "unassessed (no account)"

PROSE = """## The position
Invented test position.

## Overlaps and conflicts
None.

## Couldn't find or couldn't tell
Nothing.

## Questions for the business
1. Invented test question.
"""


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path, values, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(values)


class KitFixture(unittest.TestCase):
    """An isolated kit whose ERP accounts the test chooses, with the sample's nine cards."""

    erp_accounts = [ACCOUNT1, ACCOUNT2]
    mapped = {NORTH: ACCOUNT1, PARENT: ACCOUNT1, GERMAN: ACCOUNT1,
              ACCOUNT1: ACCOUNT1, ACCOUNT2: ACCOUNT2}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-place-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        self.pile = Path(self.temp.name) / "pile"
        shutil.copytree(ROOT / "sample/pile", self.pile)
        self.write_erp()
        self.command("prepare.py", str(self.pile), "--account-column", "customer_account",
                     "--side", "customers")
        self.fix_erp_json()
        shutil.copyfile(ROOT / "sample/expected/our-entities.csv", self.root / "inputs/our-entities.csv")
        shutil.copytree(ROOT / "sample/expected/cards", self.root / "work/cards")
        self.write_map()

    def write_erp(self):
        write_rows(self.pile / "ERP_record.csv",
                   [{"account_number": f"INV-{100 + n}", "customer_account": name,
                     "country": "United Kingdom"} for n, name in enumerate(self.erp_accounts)],
                   ["account_number", "customer_account", "country"])

    def fix_erp_json(self):
        """prepare.py strips the ERP cell, so put a deliberate trailing space back by hand.

        A trailing space is legal in a CSV cell and in an ERP export; the point of the test is
        that nothing downstream builds a path from the raw name.
        """
        path = self.root / "work/erp.json"
        erp = json.loads(path.read_text(encoding="utf-8"))
        by_stripped = {name.strip(): name for name in self.erp_accounts}
        for account in erp["accounts"]:
            account["account"] = by_stripped.get(account["account"], account["account"])
        path.write_text(json.dumps(erp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def write_map(self, mapped=None):
        write_rows(self.root / "inputs/entity-map.csv",
                   [{"name_as_printed": name, "account": account, "basis": "in the document",
                     "confidence": "sure", "decided_by": "user", "note": "invented test row"}
                    for name, account in (self.mapped if mapped is None else mapped).items()],
                   ENTITY_MAP_COLUMNS)

    def command(self, script, *args, success=True):
        result = subprocess.run([sys.executable, f"scripts/{script}", *args], cwd=self.root,
                                text=True, capture_output=True)
        if success:
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        else:
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def judge(self, account, doc_ids, name=None):
        """Write one account's placements, as a judge does. `name` overrides the file name."""
        write_rows(self.root / "work/placements" / f"{name or safe_folder_name(account)}.csv",
                   [{**{c: "" for c in PLACEMENT_COLUMNS}, "doc_id": doc_id, "tree": "T1",
                     "folder": "1-governs-trade", "reason": "invented test placement"}
                    for doc_id in doc_ids], PLACEMENT_COLUMNS)
        (self.root / "work/placements" / f"{name or safe_folder_name(account)}.md").write_text(
            PROSE, encoding="utf-8")

    def corpus(self):
        return {r["doc_id"]: r for r in rows(self.root / "out/customers/CORPUS.csv")}

    def sorted_docs(self, account):
        return sorted(r["doc_id"] for r in rows(self.root / "work/logs/sort.csv")
                      if r["account"] == account)


class EmptyAccounts(KitFixture):
    erp_accounts = [ACCOUNT1, ACCOUNT2, EMPTY_ONE, EMPTY_TWO]

    def setUp(self):
        super().setUp()
        self.command("sort.py")
        self.judge(ACCOUNT1, self.sorted_docs(ACCOUNT1))
        self.judge(ACCOUNT2, self.sorted_docs(ACCOUNT2))

    def test_an_account_with_no_documents_is_written_without_a_judge(self):
        out = self.command("place.py", "--all", "--visuals")
        for account in (EMPTY_ONE, EMPTY_TWO):
            with self.subTest(account=account):
                folder = self.root / "out/customers" / account
                self.assertFalse((self.root / "work/placements" / f"{account}.csv").exists())
                readme = (folder / "README.md").read_text(encoding="utf-8")
                self.assertIn("Nothing is filed to this account", readme)
                self.assertIn(account, readme)
                self.assertEqual([], rows(folder / "documents.csv"))
                # The empty diagram: the account node and nothing else.
                diagram = (folder / "position.mmd").read_text(encoding="utf-8")
                self.assertIn(f'ACC["{account}"]', diagram)
                self.assertNotIn("-->", diagram)
                self.assertTrue((folder / "position.html").is_file())
                for status in STATUS_FOLDERS:
                    self.assertTrue((folder / status).is_dir())
                    self.assertEqual([], list((folder / status).iterdir()))
        self.assertIn(f"{EMPTY_ONE}: 0 files copied", out)

    def test_the_index_counts_the_empty_account_as_written_not_as_waiting(self):
        self.command("place.py", "--all", "--visuals")
        index = (self.root / "out/INDEX.md").read_text(encoding="utf-8")
        line = next(l for l in index.splitlines() if l.startswith(f"| {EMPTY_ONE} |"))
        self.assertNotIn("not judged", line)
        self.assertIn("README.md", line)
        accounts = {r["account"]: r for r in rows(self.root / "out/customers/ACCOUNTS.csv")}
        self.assertEqual("0", accounts[EMPTY_ONE]["n_documents"])
        self.assertEqual("0", accounts[EMPTY_ONE]["n_1_governs_trade"])

    def test_the_index_only_run_writes_the_empty_account_too(self):
        out = self.command("place.py", "--index")
        self.assertTrue((self.root / "out/customers" / EMPTY_TWO / "README.md").is_file())
        self.assertNotIn("WARNING", out)

    def test_a_judge_is_only_worth_spending_on_an_account_with_documents(self):
        listed = self.command("place.py", "--accounts-with-documents").strip().splitlines()
        self.assertEqual([ACCOUNT1, ACCOUNT2], listed)
        self.assertNotIn(EMPTY_ONE, listed)

    def test_one_empty_account_can_be_rebuilt_on_its_own(self):
        self.command("place.py", "--account", EMPTY_ONE)
        self.assertIn("Nothing is filed to this account",
                      (self.root / "out/customers" / EMPTY_ONE / "README.md").read_text(encoding="utf-8"))


class HoldingDocuments(KitFixture):
    """Read, but no ERP account: the row stays in CORPUS.csv and the name needs a decision."""

    mapped = {NORTH: ACCOUNT1, GERMAN: ACCOUNT1, ACCOUNT1: ACCOUNT1, ACCOUNT2: ACCOUNT2}

    def setUp(self):
        super().setUp()
        self.command("sort.py")           # doc 003 names only PARENT, which nobody has mapped
        self.judge(ACCOUNT1, self.sorted_docs(ACCOUNT1))
        self.judge(ACCOUNT2, self.sorted_docs(ACCOUNT2))
        self.out = self.command("place.py", "--all", "--visuals")

    def test_the_holding_document_is_in_the_corpus_with_its_card_facts(self):
        row = self.corpus()["003"]
        self.assertEqual(f"_not-on-the-list/{PARENT}", row["account"])
        self.assertEqual(f"_not-on-the-list/{PARENT}", row["folder"])
        self.assertEqual(UNASSESSED, row["status"])
        # The card facts are there: kind, signed and the dates.
        self.assertEqual("NDA", row["kind"])
        self.assertEqual("both", row["signed"])
        self.assertEqual("2019-05-01", row["start_date"])
        self.assertEqual("fixed: 2022-04-30", row["end"])
        self.assertEqual("Mutual Non-Disclosure Agreement", row["title"])
        self.assertNotEqual("no card yet", row["kind"])
        self.assertIn("inputs/entity-map.csv", row["placement_reason"])

    def test_nothing_is_dropped_between_the_sort_log_and_the_corpus(self):
        log = rows(self.root / "work/logs/sort.csv")
        self.assertEqual(sorted(r["doc_id"] for r in log), sorted(self.corpus()))
        self.assertEqual(len(log), len(rows(self.root / "out/customers/CORPUS.csv")))

    def test_the_index_lists_it_under_needs_a_decision_grouped_by_name(self):
        index = (self.root / "out/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("## Needs a decision", index)
        section = index.split("## Needs a decision", 1)[1].split("##", 1)[0]
        self.assertIn(f"- {PARENT} (`_not-on-the-list`): doc 003", section)
        self.assertIn("inputs/entity-map.csv", section)
        html = (self.root / "out/INDEX.html").read_text(encoding="utf-8")
        self.assertIn("Needs a decision", html)
        self.assertIn(PARENT, html)

    def test_a_document_with_no_company_name_is_listed_too(self):
        (self.root / "inputs/corrections.csv").write_text(
            "doc_id,field,value,reason\n"
            "005,q2_their_signing_entities,none,invented test correction\n"
            "005,q2_their_group_companies,none,invented test correction\n", encoding="utf-8")
        self.command("sort.py")
        self.judge(ACCOUNT2, self.sorted_docs(ACCOUNT2))
        self.command("place.py", "--all")
        row = self.corpus()["005"]
        self.assertEqual("_no-name-found", row["folder"])
        self.assertEqual(UNASSESSED, row["status"])
        section = (self.root / "out/INDEX.md").read_text(encoding="utf-8") \
            .split("## Needs a decision", 1)[1].split("##", 1)[0]
        self.assertIn("- (no name) (`_no-name-found`): doc 005", section)

    def test_an_account_document_keeps_the_judges_folder(self):
        row = self.corpus()["001"]
        self.assertEqual("1-governs-trade", row["folder"])
        self.assertNotEqual(UNASSESSED, row["status"])

    def test_when_the_name_is_mapped_the_document_is_judged_normally(self):
        self.write_map({**self.mapped, PARENT: ACCOUNT1})
        self.command("sort.py")
        self.judge(ACCOUNT1, self.sorted_docs(ACCOUNT1))
        self.command("place.py", "--all")
        row = self.corpus()["003"]
        self.assertEqual(ACCOUNT1, row["account"])
        self.assertEqual("1-governs-trade", row["folder"])
        section = (self.root / "out/INDEX.md").read_text(encoding="utf-8") \
            .split("## Needs a decision", 1)[1].split("##", 1)[0]
        self.assertIn("- none", section)


class HostileAccountNames(KitFixture):
    """An ERP name with a slash, a colon and a trailing space, end to end."""

    erp_accounts = [HOSTILE, COLON_ONLY]
    mapped = {NORTH: HOSTILE, PARENT: HOSTILE, GERMAN: HOSTILE, ACCOUNT1: HOSTILE,
              ACCOUNT2: COLON_ONLY}

    def test_the_safe_placements_name_is_what_the_judge_writes(self):
        self.command("sort.py")
        self.judge(HOSTILE, self.sorted_docs(HOSTILE))
        self.judge(COLON_ONLY, self.sorted_docs(COLON_ONLY))
        out = self.command("place.py", "--all", "--visuals")
        self.assertNotIn("WARNING", out)

        folder = self.root / "out/customers" / safe_folder_name(HOSTILE)
        self.assertEqual("Brenlow_Dockyard_ Svcs Ltd", folder.name)
        self.assertTrue((folder / "README.md").is_file())
        self.assertTrue((folder / "position.html").is_file())
        # The copy is named from the account, with every path-hostile character removed.
        self.assertTrue((folder / "1-governs-trade"
                         / "001 master-agreement BrenlowDockyard-Svcs-Ltd 2019-03-14.pdf").is_file())
        corpus = self.corpus()
        self.assertEqual(HOSTILE, corpus["001"]["account"])
        self.assertEqual("1-governs-trade", corpus["001"]["folder"])
        self.assertEqual("1-governs-trade", corpus["005"]["folder"])
        # Every readable document was placed; nothing fell into 'not judged'.
        self.assertFalse([r for r in corpus.values() if r["folder"] == "not judged"])
        # The note names the account as the ERP prints it and says what the folder is called.
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn(HOSTILE.strip(), readme)
        self.assertIn("Brenlow_Dockyard_ Svcs Ltd", readme)

    def test_a_raw_account_name_is_still_read_with_a_warning(self):
        self.command("sort.py")
        self.judge(HOSTILE, self.sorted_docs(HOSTILE))
        # The judge wrote the ERP name as printed instead of the folder-safe name.
        self.judge(COLON_ONLY, self.sorted_docs(COLON_ONLY), name=COLON_ONLY)
        out = self.command("place.py", "--all")
        self.assertIn("placements found as", out)
        self.assertIn(safe_folder_name(COLON_ONLY), out)
        self.assertEqual("1-governs-trade", self.corpus()["005"]["folder"])

    def test_no_placements_at_all_leaves_the_account_waiting_for_the_judge(self):
        self.command("sort.py")
        out = self.command("place.py", "--all")
        self.assertIn("no account has a placements file yet", out)
        self.assertEqual("not judged", self.corpus()["001"]["folder"])
        index = (self.root / "out/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("not judged yet", index)
        # An account with documents is not treated as an empty account.
        self.assertFalse((self.root / "out/customers" / safe_folder_name(HOSTILE)
                          / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
