"""Light filing by script: parsing of the review tool's cells and an invented end-to-end run."""

import csv
import json
import unittest
from pathlib import Path

from kit_common import ENTITY_MAP_COLUMNS
from test_place import KitFixture, rows, write_rows
import sort_light
from sort_light import (dates_in, parse_entity, parse_closed, core_name, header_key, entity_lines, as_at_in_headers)


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
        self.assertEqual("2026-09-09", as_at_in_headers(["Name", "9. Status (As at 2026-09-09, choose exactly one value. Current: ...)"]))
        self.assertEqual("2026-09-09", as_at_in_headers(["Status (as at 9 September 2026 choose one)"]))
        self.assertEqual("", as_at_in_headers(["9. Status (choose exactly one value)"]))


COLUMNS = ["Name", "1. Title", "2. Reference", "3. Document Date", "4. Customer Entity",
           "5. Additional Customer Entities", "6. Supplier Entity", "7. Instrument", "8. Supply Coverage",
           "9. Group Mechanism", "10. Signed", "11. Status", "12. End Date", "13. Relation to Parent",
           "14. Parent Agreement"]
NORTH_PRINTED = "Tallowfield Industries (North) Limited (No. 07654321)"
PELLMONT_PRINTED = "Pellmont Logistics Group"


def light_row(name, title, customer, instrument, coverage, signed, status, dated="", end="",
              relation="—", parent="—", reference="—", extra="—"):
    return dict(zip(COLUMNS, [name, title, reference, dated, customer, extra, "Marrowgate Supply Ltd (No. 01234567)",
                              instrument, coverage, "—", signed, status, end, relation, parent]))


def light_export():
    """An invented fourteen-column export over the sample pile (test_top.py reuses it)."""
    north, pellmont = NORTH_PRINTED, PELLMONT_PRINTED
    return [
        light_row("01 Supply Agreement.pdf", "Supply Agreement", north, "Master or supply agreement",
                  "All supply between the parties", "Signed by all parties", "Current", "March 14, 2019"),
        light_row("02 Amendment 1.pdf", "Amendment 1 to Supply Agreement", north, "Amendment or side letter",
                  "Varies commercials only", "Signed by all parties", "Current", "February 1, 2026",
                  relation="Amends", parent="the Supply Agreement dated 14 March 2019"),
        light_row("03 NDA scan.pdf", "Mutual Non-Disclosure Agreement", "Quillbeck Fasteners plc",
                  "NDA, MOU or letter of intent", "No supply coverage", "Signed by all parties", "Current",
                  "May 1, 2019", "April 30, 2029"),
        light_row("04 MSA draft.docx", "Master Services Agreement", pellmont, "Master or supply agreement",
                  "All supply between the parties", "Draft", "Not yet effective", "January 15, 2026"),
        light_row("05 Purchase Order.pdf", "Purchase Order", pellmont, "Purchase order or call-off",
                  "Part of supply", "Signature not established", "Current", "April 6, 2026", "April 20, 2026"),
        light_row("06 Rebate Letter.pdf", "Rebate Letter 2026", pellmont, "Pricing or rebate letter",
                  "Varies commercials only", "Signed by one party", "Current", "January 1, 2026", "December 31, 2026",
                  relation="Varies", parent="our Master Services Agreement"),
        light_row("07 scan_0032.jpg", "Master Services Agreement signature page", pellmont, "Other",
                  "Unclear", "Signed by all parties", "Unclear", "February 2, 2026"),
        light_row("08 Hexley Works Site Agreement.pdf", "Hexley Works Site Agreement", north,
                  "Project agreement or statement of work", "Part of supply", "Signed by all parties", "Current",
                  "March 1, 2026", "Event: practical completion", relation="Agreed under",
                  parent="the Supply Agreement dated 14 March 2019"),
        light_row("09 Internal Account Playbook.docx", "Internal Account Playbook", "Not found", "Other",
                  "Varies commercials only", "Draft", "Unclear", "February 1, 2026"),
    ]


class LightFilingTest(KitFixture):
    """The sample pile with an invented export: every folder rule that the pile can exercise."""

    COLUMNS = COLUMNS

    def export(self):
        return light_export()

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
        self.assertIn("as-at 2026-06-01 (--as-at)", out)
        self.assertIn("most frequent supplier entity: Marrowgate Supply Ltd (9 of 9 rows)", out)
        self.assertIn("side customers: consistent", out)
        self.assertIn("no error log supplied", out)
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

    def test_versions_meet_by_reference_and_a_signature_page_joins_its_body(self):
        table = self.export()
        table[0]["2. Reference"] = "TAL/2019/01"
        table[0]["10. Signed"] = "Signature not established"       # the body; its signature page is a separate scan
        table[3].update({"4. Customer Entity": NORTH_PRINTED, "1. Title": "Master Supply Agreement (Tallowfield)",
                         "2. Reference": "TAL/2019/01", "3. Document Date": "March 1, 2019", "11. Status": "Current"})
        table[6].update({"7. Instrument": "Master or supply agreement", "1. Title": "Supply Agreement",
                         "2. Reference": "TAL/2019/01", "4. Customer Entity": NORTH_PRINTED,
                         "8. Supply Coverage": "All supply between the parties", "3. Document Date": "March 16, 2019"})
        write_rows(self.table, table, self.COLUMNS)
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.light("--file")
        corpus = self.corpus()
        tallow = self.erp_accounts[0]
        body_id, page_id = self.inventory["01 Supply Agreement.pdf"], self.inventory["07 scan_0032.jpg"]
        body = corpus[(body_id, tallow)]
        draft = corpus[(self.inventory["04 MSA draft.docx"], tallow)]
        page = corpus[(page_id, tallow)]
        self.assertEqual("1-governs-trade", body["folder"])
        self.assertIn(f"execution shown on doc {page_id}: Signed by all parties", body["notes"])
        self.assertEqual("Signed by all parties", body["signed"])
        self.assertEqual("5-orders-drafts-duplicates", page["folder"])            # one page of a four-page body
        self.assertIn(f"signature page or partial copy of doc {body_id}", page["notes"])
        self.assertEqual("5-orders-drafts-duplicates", draft["folder"])           # same reference, different title
        self.assertIn(f"draft; executed version is doc {body_id}", draft["notes"])
        self.assertNotIn("draft dated after", draft["flags"])

    def test_the_names_turn_writes_validated_rows_through_the_script(self):
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        name, pellmont = "Quillbeck Fasteners plc", self.erp_accounts[1]
        self.assertIn("--basis must be", self.light("--decide", name, "--account", pellmont, "--basis", "unknown",
                                                    "--confidence", "sure", success=False))
        self.assertIn("not an ERP account", self.light("--decide", name, "--account", "Quillbeck Group",
                                                       "--basis", "known group", "--confidence", "fairly sure", success=False))
        out = self.light("--decide", name, "--account", pellmont.lower(), "--basis", "known group",
                         "--confidence", "sure", "--note", "invented test decision")
        self.assertIn("fairly sure", out)                                     # known group is capped
        unmatched = json.loads(self.light("--unmatched"))
        self.assertEqual([], unmatched["unmatched"])
        self.assertEqual([], unmatched["entity_map_ignored"])
        self.assertEqual("present", unmatched["hints"]["our_entities_file"])
        self.assertIn("Filed 10 documents", self.light("--file"))
        nda = self.corpus()[(self.inventory["03 NDA scan.pdf"], pellmont)]
        self.assertEqual("3-live-not-trade", nda["folder"])
        self.assertEqual(("known group", "fairly sure"), (nda["basis"], nda["confidence"]))
        row = next(r for r in rows(self.root / "inputs/entity-map.csv") if r["name_as_printed"] == name)
        self.assertEqual((pellmont, "claude"), (row["account"], row["decided_by"]))
        index = (self.root / "out/sort/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("## Entity map", index)
        self.assertIn("Quillbeck Fasteners plc -> " + pellmont, index)
        # A user decision is never overwritten.
        write_rows(self.root / "inputs/entity-map.csv", [{**row, "decided_by": "user", "account": "_not-on-the-list"}],
                   ENTITY_MAP_COLUMNS)
        self.assertIn("user decision", self.light("--decide", name, "--account", pellmont, "--basis", "known group",
                                                  "--confidence", "fairly sure", success=False))

    def test_an_entity_map_row_the_script_cannot_apply_is_reported(self):
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        existing = rows(self.root / "inputs/entity-map.csv")
        write_rows(self.root / "inputs/entity-map.csv", existing + [
            {"name_as_printed": "Quillbeck Fasteners plc", "account": "Pellmont Logistics", "basis": "known group",
             "confidence": "fairly sure", "decided_by": "claude", "note": "misspelt account"}], ENTITY_MAP_COLUMNS)
        unmatched = json.loads(self.light("--unmatched"))
        self.assertEqual(["Quillbeck Fasteners plc"], [u["name"] for u in unmatched["unmatched"]])
        self.assertIn("not an ERP account row", unmatched["unmatched"][0]["why_unresolved"])
        self.assertIn("not an ERP account row", unmatched["entity_map_ignored"][0]["reason"])
        self.assertIn("ignored", self.light("--file"))

    def test_the_as_at_date_comes_from_the_status_question(self):
        columns = [c if not c.startswith("11. Status") else
                   "11. Status (As at 2026-06-01, choose exactly one value. Current: the document has commenced)"
                   for c in self.COLUMNS]
        write_rows(self.table, [dict(zip(columns, r.values())) for r in self.export()], columns)
        self.assertIn("as-at 2026-06-01 (the Status question)", self.light("--import", str(self.table)))
        self.assertIn("as at 2026-06-01", self.light("--file") and (self.root / "out/sort/INDEX.md").read_text())
        self.assertIn("differs from the as-at date in the Status question (2026-06-01)",
                      self.light("--import", str(self.table), "--as-at", "2026-07-01"))

    def test_a_child_with_no_parent_named_links_to_the_accounts_only_master(self):
        table = self.export()
        table[1]["14. Parent Agreement"] = "—"                      # Amends, but the export names no parent
        write_rows(self.table, table, self.COLUMNS)
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.light("--file")
        amendment = self.corpus()[(self.inventory["02 Amendment 1.pdf"], self.erp_accounts[0])]
        self.assertEqual(self.inventory["01 Supply Agreement.pdf"], amendment["parent_doc"])
        self.assertEqual("1-governs-trade", amendment["folder"])
        self.assertIn("parent inferred", amendment["flags"])

    def test_a_group_name_alone_says_who_we_are_and_reversed_rows_go_to_unsure(self):
        write_rows(self.root / "inputs/our-entities.csv", [], ["name", "status", "note"])
        self.assertIn("recorded", self.light("--our-group", "Marrowgate"))
        table = self.export()
        table[4].update({"4. Customer Entity": "Marrowgate Supply (Scotland) Ltd",
                         "6. Supplier Entity": PELLMONT_PRINTED})            # the tool swapped the parties
        write_rows(self.table, table, self.COLUMNS)
        out = self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.assertIn("our group: Marrowgate", out)
        self.assertIn("side customers: consistent", out)
        self.light("--file")
        po = self.corpus()[(self.inventory["05 Purchase Order.pdf"], self.erp_accounts[1])]
        self.assertEqual("unsure", po["folder"])
        self.assertIn("sides reversed", po["flags"])
        self.assertIn("Marrowgate (group name)", (self.root / "out/sort/INDEX.md").read_text(encoding="utf-8"))

    def test_without_any_our_entities_the_dominant_supplier_stands_in(self):
        (self.root / "inputs/our-entities.csv").unlink()
        out = self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.assertIn("treating Marrowgate Supply Ltd as our company", out)
        self.assertIn("side customers: consistent", out)
        self.assertEqual("Marrowgate Supply Ltd", json.loads(self.light("--unmatched"))["hints"]["inferred_ours"])

    def test_a_group_member_decision_lands_in_our_entities_not_the_entity_map(self):
        self.light("--import", str(self.table), "--as-at", "2026-06-01")
        self.assertIn("ERP account row", self.light("--decide", self.erp_accounts[1], "--account", "_ours", success=False))
        self.light("--decide", "Quillbeck Fasteners plc", "--account", "_ours", "--basis", "known group",
                   "--note", "invented group company")
        ours = rows(self.root / "inputs/our-entities.csv")
        self.assertIn(("Quillbeck Fasteners plc", "group member"), [(r["name"], r["status"]) for r in ours])
        self.assertNotIn("Quillbeck", (self.root / "inputs/entity-map.csv").read_text(encoding="utf-8"))
        self.assertEqual([], json.loads(self.light("--unmatched"))["unmatched"])
        self.light("--file")
        nda = next(r for (d, a), r in self.corpus().items() if d == self.inventory["03 NDA scan.pdf"])
        self.assertEqual("_no-name-found", nda["account"])                    # both parties are ours
        self.assertIn("only our own companies", nda["notes"])

    def test_import_refuses_a_table_without_the_required_columns(self):
        write_rows(self.table, [{"Name": "01 Supply Agreement.pdf", "1. Title": "x"}], ["Name", "1. Title"])
        self.assertIn("missing columns", self.light("--import", str(self.table), success=False))
        self.assertFalse((self.root / "work/review-table-light/active.json").exists())


class SideCheck(KitFixture):
    def test_prepare_refuses_a_side_that_contradicts_the_account_column(self):
        out = self.command("prepare.py", str(self.pile), "--account-column", "customer_account",
                           "--side", "suppliers", success=False)
        self.assertIn("contradicts the account column", out)

    def test_prepare_derives_the_side_from_a_column_that_names_it(self):
        out = self.command("prepare.py", str(self.pile), "--account-column", "customer_account")
        self.assertIn("side: customers", out.lower())
        self.assertIn('"side": "customers"', (self.root / "work/erp.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
