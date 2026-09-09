"""Light filing by script: parsing of the review tool's cells and an invented end-to-end run."""

import csv
import json
import unittest
from pathlib import Path

from test_place import KitFixture, rows, write_rows
import sort_light
from sort_light import (dates_in, parse_entity, parse_closed, core_name, header_key, entity_lines)


class ParsingTest(unittest.TestCase):
    def test_dates_in_every_export_shape(self):
        self.assertEqual(["2023-06-06"], dates_in("June 6, 2023"))
        self.assertEqual(["2021-02-22"], dates_in("Master Supply Agreement dated 22 February 2021, reference X"))
        self.assertEqual(["2027-12-31"], dates_in("December 31, 2027 (fixed end date)"))
        self.assertEqual(["2022-06-14", "2022-07-04"], dates_in("June 14, 2022 (nda) July 4, 2022 (supply)"))
        self.assertEqual(["2026-01-05"], dates_in("2026-01-05"))
        self.assertEqual([], dates_in("—"))
        self.assertEqual([], dates_in("31 February 2026"))

    def test_entities_keep_names_and_lift_company_numbers(self):
        self.assertEqual(("Brenlow Dockyard Services Limited", "07733914"),
                         parse_entity("Brenlow Dockyard Services Limited (No. 07733914)"))
        self.assertEqual(("Wexbury Utilities plc", ""), parse_entity("Wexbury Utilities plc "))
        self.assertEqual(("", ""), parse_entity("Not found"))
        self.assertEqual(("", ""), parse_entity("—"))
        self.assertEqual([("Sturmore Rail Group Ltd", ""), ("The Housing Partnership (Trentmoor) Limited", "")],
                         entity_lines("Sturmore Rail Group Ltd\nThe Housing Partnership (Trentmoor) Limited"))
        self.assertEqual([], entity_lines("None"))

    def test_closed_cells_accept_labels_lists_and_prose(self):
        self.assertEqual((["Draft"], ""), parse_closed("signed", "Draft"))
        self.assertEqual((["Draft"], ""), parse_closed("signed", "Draft | tracked changes on page 2"))
        self.assertEqual((["Entity schedule", "Ordering entitlement"], ""),
                         parse_closed("group_mechanism", "Entity schedule,Ordering entitlement"))
        self.assertEqual((["NDA, MOU or letter of intent"], ""), parse_closed("instrument", "NDA, MOU or letter of intent"))
        self.assertEqual(([], "Signed by everyone"), parse_closed("signed", "Signed by everyone"))
        self.assertEqual(([], ""), parse_closed("status", "—"))

    def test_names_meet_without_their_legal_form_and_headers_drop_question_text(self):
        self.assertEqual(core_name("Sturmore Rail Group Ltd (No. 03996120)"), core_name("Sturmore Rail Group"))
        self.assertEqual(core_name("Brenlow Dockyard Svcs Ltd"), core_name("Brenlow Dockyard Services Limited"))
        self.assertNotEqual(core_name("Wexbury Power Networks"), core_name("Wexbury Utilities plc"))
        self.assertEqual("supply_coverage", header_key("6. Supply Coverage (Supply coverage\n Question: ...)"))
        self.assertEqual("file_name", header_key("Name"))
        self.assertEqual("relation_to_parent", header_key("11. Relation to Parent"))


class LightFilingTest(KitFixture):
    """The sample pile with an invented export: every folder rule that the pile can exercise."""

    COLUMNS = ["Name", "1. Title", "2. Reference", "3. Document Date", "4. Customer Entity",
               "5. Additional Customer Entities", "6. Supplier Entity", "7. Instrument", "8. Supply Coverage",
               "9. Group Mechanism", "10. Signed", "11. Status", "12. End Date", "13. Relation to Parent",
               "14. Parent Agreement"]

    def row(self, name, title, customer, instrument, coverage, signed, status, dated="", end="",
            relation="—", parent="—", reference="—", extra="—"):
        return dict(zip(self.COLUMNS, [name, title, reference, dated, customer, extra, "Marrowgate Supply Ltd (No. 01234567)",
                                       instrument, coverage, "—", signed, status, end, relation, parent]))

    def export(self):
        north = "Tallowfield Industries (North) Limited (No. 07654321)"
        pellmont = "Pellmont Logistics Group"
        return [
            self.row("01 Supply Agreement.pdf", "Supply Agreement", north, "Master or supply agreement",
                     "All supply between the parties", "Signed by all parties", "Current", "March 14, 2019"),
            self.row("02 Amendment 1.pdf", "Amendment 1 to Supply Agreement", north, "Amendment or side letter",
                     "Varies commercials only", "Signed by all parties", "Current", "February 1, 2026",
                     relation="Amends", parent="the Supply Agreement dated 14 March 2019"),
            self.row("03 NDA scan.pdf", "Mutual Non-Disclosure Agreement", "Quillbeck Fasteners plc",
                     "NDA, MOU or letter of intent", "No supply coverage", "Signed by all parties", "Current",
                     "May 1, 2019", "April 30, 2029"),
            self.row("04 MSA draft.docx", "Master Services Agreement", pellmont, "Master or supply agreement",
                     "All supply between the parties", "Draft", "Not yet effective", "January 15, 2026"),
            self.row("05 Purchase Order.pdf", "Purchase Order", pellmont, "Purchase order or call-off",
                     "Part of supply", "Signature not established", "Current", "April 6, 2026", "April 20, 2026"),
            self.row("06 Rebate Letter.pdf", "Rebate Letter 2026", pellmont, "Pricing or rebate letter",
                     "Varies commercials only", "Signed by one party", "Current", "January 1, 2026", "December 31, 2026",
                     relation="Varies", parent="our Master Services Agreement"),
            self.row("07 scan_0032.jpg", "Master Services Agreement signature page", pellmont, "Other",
                     "Unclear", "Signed by all parties", "Unclear", "February 2, 2026"),
            self.row("08 Hexley Works Site Agreement.pdf", "Hexley Works Site Agreement", north,
                     "Project agreement or statement of work", "Part of supply", "Signed by all parties", "Current",
                     "March 1, 2026", "Event: practical completion", relation="Agreed under",
                     parent="the Supply Agreement dated 14 March 2019"),
            self.row("09 Internal Account Playbook.docx", "Internal Account Playbook", "Not found", "Other",
                     "Varies commercials only", "Draft", "Unclear", "February 1, 2026"),
        ]

    def setUp(self):
        super().setUp()
        self.table = self.pile / "Review_Table_Light.csv"
        write_rows(self.table, self.export(), self.COLUMNS)
        write_rows(self.root / "inputs/business-practice.csv",
                   [{"file_name": "09 Internal Account Playbook.docx", "account": self.erp_accounts[0]}],
                   ["file_name", "account"])
        self.inventory = {r["file_name"]: r["doc_id"] for r in rows(self.root / "work/inventory.csv")}

    def light(self, *args, success=True):
        return self.command("sort_light.py", *args, success=success)

    def corpus(self):
        return {(r["doc_id"], r["account"]): r for r in rows(self.root / "out/sort/customers/CORPUS.csv")}

    def test_folders_follow_the_answers_and_dates(self):
        out = self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.assertIn("9 rows matched to documents; 1 documents without a row", out)
        unmatched = json.loads(self.light("--unmatched"))
        self.assertEqual(["Quillbeck Fasteners plc"], [u["name"] for u in unmatched["unmatched"]])
        self.assertIn("Filed 10 documents", self.light("--file"))
        corpus = self.corpus()
        tallow, pellmont = self.erp_accounts
        folder = {name: next(r["folder"] for (d, a), r in corpus.items() if d == doc)
                  for name, doc in self.inventory.items() if doc.isdigit()}
        self.assertEqual("1-governs-trade", folder["01 Supply Agreement.pdf"])
        self.assertEqual("1-governs-trade", folder["02 Amendment 1.pdf"])       # inherits its parent by date
        self.assertEqual("2-governs-part-of-trade", folder["08 Hexley Works Site Agreement.pdf"])
        self.assertEqual("5-orders-drafts-duplicates", folder["05 Purchase Order.pdf"])
        self.assertEqual("3-live-not-trade", folder["06 Rebate Letter.pdf"])    # end date after the as-at date
        self.assertEqual("unsure", folder["04 MSA draft.docx"])                 # draft, no executed version
        self.assertEqual("unsure", folder["07 scan_0032.jpg"])
        self.assertEqual("6-business-practice", folder["09 Internal Account Playbook.docx"])
        self.assertEqual("3-live-not-trade (provisional)", folder["03 NDA scan.pdf"])
        self.assertEqual("_unreadable", folder["10 old email.msg"])
        amendment = corpus[(self.inventory["02 Amendment 1.pdf"], tallow)]
        self.assertEqual(self.inventory["01 Supply Agreement.pdf"], amendment["parent_doc"])
        self.assertIn(corpus[(self.inventory["01 Supply Agreement.pdf"], tallow)]["basis"],
                      ("same name", "in the document", "company number in the document"))
        nda = next(r for (d, a), r in corpus.items() if d == self.inventory["03 NDA scan.pdf"])
        self.assertTrue(nda["account"].startswith("_not-on-the-list/"))
        self.assertTrue((self.root / "out/sort/customers" / tallow / "1-governs-trade" / "documents.csv").exists())
        self.assertFalse(list((self.root / "out/sort/customers/_not-on-the-list").glob("*/3-live-not-trade")))
        self.assertTrue((self.root / "out/sort/INDEX.md").exists())
        log = rows(self.root / "work/logs/sort.csv")
        self.assertEqual(10, len(log))
        self.assertIn("as at 2026-06-01", (self.root / "out/sort/INDEX.md").read_text())

    def test_end_dates_and_terminations_move_documents_by_the_as_at_date(self):
        table = self.export()
        table[5]["12. End Date"] = "May 31, 2026"                       # rebate period over before the as-at date
        table[6].update({"7. Instrument": "Notice letter", "8. Supply Coverage": "No supply coverage",
                         "11. Status": "Terminated", "12. End Date": "May 1, 2026", "13. Relation to Parent": "Terminates",
                         "14. Parent Agreement": "the Supply Agreement dated 14 March 2019",
                         "4. Customer Entity": "Tallowfield Industries (North) Limited"})
        write_rows(self.table, table, self.COLUMNS)
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.light("--file")
        folder = {name: next(r["folder"] for (d, a), r in self.corpus().items() if d == doc)
                  for name, doc in self.inventory.items() if doc.isdigit()}
        self.assertEqual("4-not-live", folder["06 Rebate Letter.pdf"])
        self.assertEqual("4-not-live", folder["01 Supply Agreement.pdf"])   # terminated with past effect
        self.assertEqual("4-not-live", folder["02 Amendment 1.pdf"])        # follows its parent
        self.assertEqual("4-not-live", folder["07 scan_0032.jpg"])          # the notice itself has taken effect
        table[6]["12. End Date"] = "December 1, 2026"                        # notice served, effect still to come
        write_rows(self.table, table, self.COLUMNS)
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.light("--file")
        corpus = self.corpus()
        master = corpus[(self.inventory["01 Supply Agreement.pdf"], self.erp_accounts[0])]
        self.assertEqual("1-governs-trade", master["folder"])
        self.assertIn("effective 2026-12-01, after the as-at date", master["flags"])
        self.assertTrue(list((self.root / "work/history").glob("sort-light-*")))

    def test_import_refuses_a_table_without_the_required_columns(self):
        write_rows(self.table, [{"Name": "01 Supply Agreement.pdf", "1. Title": "x"}], ["Name", "1. Title"])
        self.assertIn("missing columns", self.light("--import", str(self.table), success=False))
        self.assertFalse((self.root / "work/review-table-light/active.json").exists())


if __name__ == "__main__":
    unittest.main()
