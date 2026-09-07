"""Acceptance-level script checks using shipped invented fixtures in isolated kits.

These test deterministic replay, not whether a fresh model independently reads a contract.
The separate README-only handover test supplies that check.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sample"))
from make_expected import ACCOUNT1, ACCOUNT2, isolated_kit, replay


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def hashes(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob("*") if p.is_file()}


class SampleAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-sample-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        self.pile = Path(self.temp.name) / "pile"
        shutil.copytree(ROOT / "sample/pile", self.pile)
        self.original_hashes = hashes(self.pile)
        self.log = replay(self.root, pile=self.pile)

    def run_script(self, script, *args):
        result = subprocess.run([sys.executable, f"scripts/{script}", *args], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_inventory_preserves_scans_docx_metadata_and_unreadable_file(self):
        inventory = {r["doc_id"]: r for r in rows(self.root / "work/inventory.csv")}
        self.assertEqual(set(inventory), {"erp"} | {f"{i:03}" for i in range(1, 11)})
        self.assertEqual(inventory["001"]["page_kinds"], "ttts")
        self.assertEqual(inventory["003"]["page_kinds"], "ss")
        self.assertEqual(inventory["007"]["page_kinds"], "s")
        self.assertEqual(sum(int(r["scanned_pages"] or 0) for r in inventory.values()), 4)
        self.assertEqual(inventory["010"]["readable"], "no")
        self.assertIn("not readable", inventory["010"]["note"])
        self.assertEqual(inventory["004"]["docx_comments"], "2")
        self.assertEqual(inventory["009"]["docx_comments"], "1")
        for doc_id in ("004", "009"):
            self.assertTrue(inventory[doc_id]["docx_tracked_changes"].startswith("yes"))
            self.assertTrue(inventory[doc_id]["docx_author"].startswith("Fictional"))
            self.assertEqual(inventory[doc_id]["docx_created"], "2026-01-14T09:00:00Z")
            self.assertEqual(inventory[doc_id]["has_images"], "no")
        self.assertEqual(list(rows(self.root / "inputs/erp-record.csv")[0]),
                         ["account_number", "customer_account", "country"])
        native = (self.root / "work/text/001.txt").read_text()
        self.assertIn("=== page 4 ===\n[scan: look at the page]", native)
        self.assertNotIn("14 March 2019", native)
        self.assertEqual(hashes(self.pile), self.original_hashes)

    def test_placements_reports_and_stream_are_consistent(self):
        corpus = rows(self.root / "out/customers/CORPUS.csv")
        # All-file audit table includes the unreadable row; nine are readable documents.
        self.assertEqual(len(corpus), 10)
        readable = [r for r in corpus if r["doc_id"] != "010"]
        self.assertEqual(len(readable), 9)
        self.assertEqual([r["doc_id"] for r in corpus if r["folder"] == "1-governs-trade"], ["001", "002"])
        reviewer_columns = {"legal_agrees", "sales_agrees", "correct_folder", "comment"}
        self.assertTrue(all(value for row in corpus for key, value in row.items() if key not in reviewer_columns))
        by_id = {r["doc_id"]: r for r in corpus}
        for doc_id, folder in {"003": "4-not-live", "004": "unsure", "005": "5-orders-drafts-duplicates", "006": "2-governs-part-of-trade", "007": "unsure", "008": "2-governs-part-of-trade", "009": "6-business-practice"}.items():
            self.assertEqual(by_id[doc_id]["folder"], folder)
        accounts = rows(self.root / "out/customers/ACCOUNTS.csv")
        self.assertEqual(len(accounts), 3)
        self.assertEqual(len([r for r in accounts if not r["treated_as_stream_of"]]), 2)
        self.assertEqual({r['account']: r['open_questions'] for r in accounts},
                         {ACCOUNT1: '2', ACCOUNT2: '2', ACCOUNT1 + ' Data Centres': '0'})
        stream = self.root / "out/customers" / (ACCOUNT1 + " Data Centres")
        self.assertEqual([p.name for p in stream.iterdir()], ["README.md"])
        for account in (ACCOUNT1, ACCOUNT2):
            output = self.root / "out/customers" / account
            self.assertEqual(rows(output / "documents.csv"), [r for r in corpus if r["account"] == account])
            html = (output / "position.html").read_text()
            self.assertIn("../../assets/mermaid.min.js", html)
            self.assertIn("mermaid", html)
            self.assertNotIn("https://", html)
            self.assertTrue((self.root / "out/assets/mermaid.min.js").is_file())
        mmd = (self.root / "out/customers" / ACCOUNT1 / "position.mmd").read_text()
        self.assertIn("subgraph D001", mmd)
        self.assertIn("D001_p2 part_dead", mmd)
        note = (self.root / "out/customers" / ACCOUNT1 / "README.md").read_text()
        self.assertIn("may charge the Customer the cost of freight", note)
        self.assertIn("freight shall be charged", note)
        self.assertIn("prevail on paper", note)
        self.assertIn("but are dead", note)
        self.assertNotIn("WARNING:", self.log)

    def test_sort_replay_is_stable_and_never_changes_sources(self):
        log_before = (self.root / "work/logs/sort.csv").read_bytes()
        map_before = (self.root / "inputs/entity-map.csv").read_bytes()
        self.run_script("sort.py")
        self.run_script("place.py", "--all")
        self.assertEqual((self.root / "work/logs/sort.csv").read_bytes(), log_before)
        self.assertEqual((self.root / "inputs/entity-map.csv").read_bytes(), map_before)
        self.assertEqual(hashes(self.pile), self.original_hashes)
        log = {r["doc_id"]: r for r in rows(self.root / "work/logs/sort.csv")}
        self.assertEqual(log["003"]["account"], ACCOUNT1)
        self.assertEqual(log["003"]["basis"], "in the document")
        self.assertIn("001", log["003"]["note"])

    def test_numbering_does_not_shift_when_an_earlier_path_is_added(self):
        shutil.copyfile(self.pile / "05 Purchase Order.pdf", self.pile / "00 Added Purchase Order.pdf")
        self.run_script("prepare.py", str(self.pile), "--account-column", "customer_account", "--side", "customers")
        inventory = {r["file_name"]: r["doc_id"] for r in rows(self.root / "work/inventory.csv")}
        self.assertEqual(inventory["01 Supply Agreement.pdf"], "001")
        self.assertEqual(inventory["10 old email.msg"], "010")
        self.assertEqual(inventory["00 Added Purchase Order.pdf"], "011")

    def test_all_nine_forms_and_graph_validate_with_real_native_quotes(self):
        shutil.copytree(ROOT / "sample/expected/forms", self.root / "work/forms")
        shutil.copytree(ROOT / "sample/expected/trees", self.root / "work/trees")
        validation = self.run_script("validate_forms.py", "--all")
        self.assertIn("9 forms checked; 0 invalid", validation)
        self.assertIn("scanned page", validation)
        self.run_script('graph.py', '--account', ACCOUNT1)
        self.assertTrue((self.root / 'out/customers' / ACCOUNT1 / 'TREES.md').is_file())
        self.assertFalse((self.root / 'out/graph/nodes.csv').exists())
        self.run_script("graph.py", "--all")
        graph = self.root / "out/graph"
        nodes, edges = rows(graph / "nodes.csv"), rows(graph / "edges.csv")
        for name in ("nodes", "edges"):
            with (graph / f"{name}.csv").open() as actual, (self.root / "dcg" / f"sample-{name}-header.csv").open() as expected:
                self.assertEqual(next(csv.reader(actual)), next(csv.reader(expected)))
        self.assertTrue(nodes)
        self.assertTrue(edges)
        form = json.loads((self.root / "work/forms/001.json").read_text())
        self.assertEqual(form["B"]["B9_layered"], "yes")
        self.assertEqual(len(form["F"]), 2)
        self.assertTrue(any(e["role"] == "affiliate_listed" for e in form["C"]["C1_their_entities"]))
        gaps = (self.root / "out/DIDNT-FIT.md").read_text()
        self.assertIn("Execution status", gaps)
        self.assertIn("internal_playbook", gaps)
        self.assertIn("deemed participation", gaps)
        health = (self.root / 'out/FORM-HEALTH.md').read_text()
        self.assertIn('| G.G2_commitment_or_status | 9 | 0 | 0 |', health)
        proposals = rows(graph / "tree-proposals.csv")
        self.assertEqual(len(proposals), 7)


if __name__ == "__main__":
    unittest.main()
