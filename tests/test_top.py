"""The top-accounts scope: ERP_Top is a control file, the scope is deterministic, scoped matching
keeps every other account's light filing row, and the report marks those accounts filing only."""

import json
import unittest

from make_expected import ACCOUNT1, ACCOUNT2
from test_place import KitFixture, rows, write_rows
import test_sort_light as light


class TopFixture(KitFixture):
    """Sample pile, light filing by script, sample cards for every document, ERP_Top naming one account."""

    def setUp(self):
        super().setUp()
        self.table = self.pile / "Review_Table_Light.csv"
        write_rows(self.table, light.light_export(), light.COLUMNS)
        write_rows(self.root / "inputs/business-practice.csv",
                   [{"file_name": "09 Internal Account Playbook.docx", "account": ACCOUNT1}], ["file_name", "account"])
        self.command("sort_light.py", "--import", str(self.table), "--as-at", "2026-06-01")
        self.command("sort_light.py", "--file")
        self.top_file = self.pile / "ERP_Top.csv"
        write_rows(self.top_file, [{"customer_account": ACCOUNT1}], ["customer_account"])

    def inventory(self):
        return {r["file_name"]: r["doc_id"] for r in rows(self.root / "work/inventory.csv")}

    def prepare(self):
        return self.command("prepare.py", str(self.pile), "--account-column", "customer_account", "--side", "customers")

    def scope(self, *args):
        out = self.command("top.py", "--scope", *args)
        return out, json.loads((self.root / "work/top/scope.json").read_text(encoding="utf-8"))

    def sort_log(self):
        return {(r["doc_id"], r["account"]): r for r in rows(self.root / "work/logs/sort.csv")}


class ErpTopRegistration(TopFixture):
    def test_prepare_registers_erp_top_as_a_control_file_not_a_contract(self):
        out = self.prepare()
        self.assertIn("ERP_Top input", out)
        top = json.loads((self.root / "work/erp-top.json").read_text(encoding="utf-8"))
        self.assertEqual([ACCOUNT1], top["accounts"])
        self.assertEqual([], top["unknown"])
        inventory = rows(self.root / "work/inventory.csv")
        self.assertNotIn("ERP_Top.csv", {r["file_name"] for r in inventory})
        self.assertEqual("ERP_record.csv", next(r["file_name"] for r in inventory if r["doc_id"] == "erp"))
        # A re-run that guesses the side column instead of being told it is the same ERP:
        # the light filing log survives it.
        out = self.command("prepare.py", str(self.pile))
        self.assertNotIn("Archived", out)
        self.assertTrue(rows(self.root / "work/logs/sort.csv"))

    def test_a_name_that_is_not_an_erp_row_is_reported_and_blocks_the_scope(self):
        write_rows(self.top_file, [{"customer_account": ACCOUNT1}, {"customer_account": "Nobody Trading Ltd"}],
                   ["customer_account"])
        out = self.command("top.py", "--register", str(self.top_file))
        self.assertIn("Nobody Trading Ltd", out)
        self.assertIn("Nobody Trading Ltd", self.command("top.py", "--scope", success=False))
        self.assertFalse((self.root / "work/top/scope.json").exists())

    def test_the_scope_needs_a_registered_file_and_a_filing_log(self):
        self.assertIn("No ERP_Top registered", self.command("top.py", "--scope", success=False))


class TopScope(TopFixture):
    """Only the top account's documents get read, so only they have cards here."""

    def setUp(self):
        super().setUp()
        self.command("top.py", "--register", str(self.top_file))
        top_docs = {r["doc_id"] for r in rows(self.root / "work/logs/sort.csv") if r["account"] == ACCOUNT1}
        for card in (self.root / "work/cards").iterdir():
            if card.stem not in top_docs:
                card.unlink()

    def test_scope_is_the_top_accounts_filed_documents_plus_unfiled_readable_ones(self):
        inventory = self.inventory()
        tallow = sorted(inventory[n] for n in ("01 Supply Agreement.pdf", "02 Amendment 1.pdf",
                                                "08 Hexley Works Site Agreement.pdf", "09 Internal Account Playbook.docx"))
        out, scope = self.scope()
        self.assertEqual(tallow, scope["per_account"][ACCOUNT1])
        self.assertEqual([], scope["unfiled"])                     # every readable file had a light row
        self.assertEqual(tallow, scope["docs"])
        self.assertIn(f"{ACCOUNT1}: 4 documents", out)
        self.assertEqual([ACCOUNT1], self.command("top.py", "--accounts").strip().splitlines())

        # A contract dropped in after the export has no filing row: it joins the scope for reading.
        (self.pile / "11 Late Side Letter.pdf").write_bytes((self.pile / "02 Amendment 1.pdf").read_bytes())
        self.prepare()
        late = self.inventory()["11 Late Side Letter.pdf"]
        self.assertTrue(rows(self.root / "work/logs/sort.csv"), "prepare must keep the light filing log")
        out, scope = self.scope()
        self.assertEqual([late], scope["unfiled"])
        self.assertEqual(sorted(tallow + [late]), scope["docs"])
        self.assertIn("1 (" + late + ")", out)
        _, scope = self.scope("--filed-only")
        self.assertEqual(tallow, scope["docs"])

    def test_scoped_matching_and_the_report_leave_other_accounts_as_filing_only(self):
        inventory = self.inventory()
        self.scope()
        before = self.sort_log()
        po = inventory["05 Purchase Order.pdf"]
        out = self.command("sort.py", "--top")
        self.assertNotIn("WARNING", out)
        after = self.sort_log()
        # Pellmont's rows are the light filing rows, untouched; Tallowfield's come from the cards.
        self.assertEqual(before[(po, ACCOUNT2)], after[(po, ACCOUNT2)])
        supply = inventory["01 Supply Agreement.pdf"]
        self.assertEqual("in the document", after[(supply, ACCOUNT1)]["basis"])
        self.assertNotEqual(before[(supply, ACCOUNT1)]["companies_found"], after[(supply, ACCOUNT1)]["companies_found"])
        self.assertEqual(len(before), len(after))

        self.judge(ACCOUNT1, self.sorted_docs(ACCOUNT1))
        out = self.command("place.py", "--top", "--visuals")
        self.assertNotIn("WARNING", out)
        corpus = self.corpus()
        self.assertEqual("judged", corpus[supply]["analysis_stage"])
        self.assertEqual("1-governs-trade", corpus[supply]["folder"])
        self.assertEqual("filing only", corpus[po]["analysis_stage"])
        tallow_folder = self.root / "out/customers" / ACCOUNT1
        pellmont_folder = self.root / "out/customers" / ACCOUNT2
        self.assertTrue((tallow_folder / "position.html").is_file())
        self.assertTrue((tallow_folder / "ANALYSIS.md").is_file())
        self.assertTrue((pellmont_folder / "README.md").is_file())
        self.assertFalse((pellmont_folder / "files").exists())      # copies stay in out/sort/
        self.assertIn("light filing", (pellmont_folder / "README.md").read_text(encoding="utf-8"))
        self.assertTrue((self.root / "out/INDEX.html").is_file())
        index = (self.root / "out/INDEX.md").read_text(encoding="utf-8")
        self.assertIn(f"| {ACCOUNT2} | not judged |", index)
        self.assertIn("1 accounts judged of 2", out)

    def test_place_top_needs_the_judgment_first(self):
        self.scope()
        self.command("sort.py", "--top")
        self.assertIn("Run /judge", self.command("place.py", "--top", success=False))


if __name__ == "__main__":
    unittest.main()
