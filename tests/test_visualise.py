"""Cost-stage boundaries: text reports first, explicitly requested visuals only."""

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


def hashes(folder):
    return {path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.rglob("*") if path.is_file() and "__pycache__" not in path.parts}


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def is_visual(path):
    return path == "out/INDEX.html" or path == "out/assets/mermaid.min.js" or (
        path.startswith("out/") and Path(path).name in ("position.html", "position.mmd"))


class VisualBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-visual-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")

    def run_script(self, name, *args):
        result = subprocess.run([sys.executable, f"scripts/{name}", *args], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def audited_visualise(self, *args):
        # An actual runtime boundary check: attempts to read sources, read model
        # outputs in filing mode, execute another process or import graph.py fail.
        wrapper = r'''
import os
from pathlib import Path
import runpy
import sys
root = Path.cwd()
analysis = "--analysis" in sys.argv[1:]
def audit(event, args):
    if event in ("subprocess.Popen", "os.system", "os.exec", "os.spawn"):
        raise RuntimeError("visualisation started another process")
    if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    try:
        local = path.relative_to(root).as_posix()
    except ValueError:
        return
    blocked = local.startswith(("work/files/", "work/text/", "work/forms/", "work/trees/"))
    if not analysis:
        blocked = blocked or (local.startswith("work/") and local != "work/erp.json")
        blocked = blocked or local.startswith("inputs/")
    blocked = blocked or local == "scripts/graph.py"
    if blocked:
        raise RuntimeError("visualisation accessed forbidden input: " + local)
sys.addaudithook(audit)
sys.argv = ["scripts/visualise.py", *sys.argv[1:]]
runpy.run_path("scripts/visualise.py", run_name="__main__")
'''
        result = subprocess.run([sys.executable, "-c", wrapper, *args], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def filing_fixture(self):
        accounts = ["Example Account", "Example Stream", "Empty Account"]
        work = self.root / "work"
        work.mkdir()
        (work / "erp.json").write_text(json.dumps({"side": "suppliers", "accounts": [
            {"account": account} for account in accounts]}))
        for folder in ("files", "text", "cards", "placements", "forms", "trees"):
            target = work / folder / "001.txt"
            target.parent.mkdir()
            target.write_text("This file must not be opened by filing visualisation.")
        out = self.root / "out"
        side = out / "suppliers"
        rows = [{"doc_id": "001", "account": accounts[0], "title": 'Example "Agreement"',
                 "kind": "agreement", "companies_found": "Example Co", "basis": "name match",
                 "confidence": "fairly sure", "read_status": "filing only",
                 "file_path": "work/files/001.txt"}]
        write_csv(side / accounts[0] / "documents.csv", rows, list(rows[0]))
        write_csv(side / accounts[2] / "documents.csv", [], list(rows[0]))
        write_csv(side / "CORPUS.csv", rows, list(rows[0]))
        write_csv(side / "ACCOUNTS.csv", [
            {"account": account, "side": "suppliers", "n_documents": "1" if i == 0 else "0",
             "treated_as_stream_of": accounts[0] if i == 1 else ""}
            for i, account in enumerate(accounts)],
            ["account", "side", "n_documents", "treated_as_stream_of"])
        for account in accounts:
            folder = side / account
            folder.mkdir(exist_ok=True)
            (folder / "README.md").write_text(f"# {account}\n\nFiling information only.\n")
        holding = side / "_not-sure" / "Unmatched Co"
        holding.mkdir(parents=True)
        (holding / "README.md").write_text("# Unmatched company\n")
        write_csv(holding / "documents.csv", [], list(rows[0]))
        (out / "INDEX.md").write_text("# Filed accounts\n\nIncludes an unmatched company.\n")
        return side, accounts

    def test_default_place_has_no_visuals_and_removes_stale_visuals(self):
        replay(self.root)
        # Explicit old visuals and a cheap filing copy exist before the refresh.
        self.run_script("place.py", "--all", "--visuals")
        cheap = self.root / "out/customers" / ACCOUNT1 / "files"
        cheap.mkdir()
        (cheap / "001-example.pdf").write_bytes(b"old generated copy")
        work_before = hashes(self.root / "work")
        self.run_script("place.py", "--all")
        files = hashes(self.root)
        self.assertFalse(any(is_visual(path) for path in files))
        self.assertNotIn("position.html", (self.root / "out/INDEX.md").read_text())
        self.assertFalse(cheap.exists())
        self.assertFalse((self.root / "out/graph").exists())
        self.assertEqual(hashes(self.root / "work"), work_before)
        self.assertTrue((self.root / "out/customers" / ACCOUNT1 / "README.md").is_file())

    def test_account_refresh_retires_its_diagram_and_index_only(self):
        replay(self.root)
        self.run_script("place.py", "--all", "--visuals")
        other = self.root / "out/customers" / ACCOUNT2 / "position.html"
        other_before = other.read_bytes()
        self.run_script("place.py", "--account", ACCOUNT1)
        self.assertFalse((self.root / "out/customers" / ACCOUNT1 / "position.html").exists())
        self.assertFalse((self.root / "out/INDEX.html").exists())
        self.assertEqual(other.read_bytes(), other_before)
        self.assertTrue((self.root / "out/assets/mermaid.min.js").exists())

    def test_explicit_place_visuals_preserve_the_analysis_diagram(self):
        replay(self.root)
        self.run_script("place.py", "--all")
        self.run_script("place.py", "--all", "--visuals")
        diagram = (self.root / "out/customers" / ACCOUNT1 / "position.mmd").read_text()
        self.assertIn("subgraph D001", diagram)
        self.assertIn("D001_p2 part_dead", diagram)
        self.assertTrue((self.root / "out/INDEX.html").exists())
        self.assertTrue((self.root / "out/assets/mermaid.min.js").exists())
        self.run_script("place.py", "--index")
        self.assertFalse(any(is_visual(path) for path in hashes(self.root)))

    def test_filing_visuals_only_read_tables_and_erp_and_write_visual_artifacts(self):
        side, accounts = self.filing_fixture()
        before = hashes(self.root)
        self.audited_visualise("--all")
        after = hashes(self.root)
        self.assertEqual({p: h for p, h in before.items() if not is_visual(p)},
                         {p: h for p, h in after.items() if not is_visual(p)})
        diagram = (side / accounts[0] / "position.mmd").read_text()
        self.assertIn('ACC -- "filed under" --> F1', diagram)
        self.assertIn("doc 001", diagram)
        self.assertIn("#quot;Agreement#quot;", diagram)
        for unsupported in ("governs", "attaches", "replaces", "live", "part_dead"):
            self.assertNotIn(unsupported, diagram)
        page = (side / accounts[0] / "position.html").read_text()
        self.assertIn("filing map", page)
        self.assertIn("../../assets/mermaid.min.js", page)
        self.assertNotIn("https://", page)
        self.assertIn("No documents filed", (side / accounts[2] / "position.mmd").read_text())
        self.assertEqual([p.name for p in (side / accounts[1]).iterdir()], ["README.md"])
        index = (self.root / "out/INDEX.html").read_text()
        self.assertIn("stream of Example Account", index)
        self.assertIn("_not-sure/Unmatched%20Co/README.md", index)

    def test_account_visualisation_leaves_other_accounts_unrendered(self):
        side, accounts = self.filing_fixture()
        self.audited_visualise("--account", accounts[0])
        self.assertTrue((side / accounts[0] / "position.html").exists())
        self.assertFalse((side / accounts[2] / "position.html").exists())
        self.audited_visualise("--account", accounts[1])
        self.assertEqual([p.name for p in (side / accounts[1]).iterdir()], ["README.md"])

    def test_analysis_visualisation_uses_existing_cards_without_reading_sources(self):
        replay(self.root)
        self.run_script("place.py", "--all")
        before = hashes(self.root)
        self.audited_visualise("--all", "--analysis")
        after = hashes(self.root)
        self.assertEqual({p: h for p, h in before.items() if not is_visual(p)},
                         {p: h for p, h in after.items() if not is_visual(p)})
        diagram = (self.root / "out/customers" / ACCOUNT1 / "position.mmd").read_text()
        self.assertIn("subgraph D001", diagram)
        self.assertIn("D001_p2 part_dead", diagram)
        self.assertFalse((self.root / "out/graph").exists())

    def test_analysis_visualisation_does_not_reuse_old_placements_for_new_filing_tables(self):
        replay(self.root)
        self.run_script("place.py", "--all")
        folder = self.root / "out/customers" / ACCOUNT1
        write_csv(folder / "documents.csv", [{"doc_id": "001", "title": "Fresh filing", "kind": "agreement"}],
                  ["doc_id", "title", "kind"])
        before = hashes(self.root)
        result = self.audited_visualise("--account", ACCOUNT1, "--analysis")
        self.assertIn("current tables do not match", result)
        self.assertFalse((folder / "position.html").exists())
        after = hashes(self.root)
        self.assertEqual({p: h for p, h in before.items() if not is_visual(p)},
                         {p: h for p, h in after.items() if not is_visual(p)})


if __name__ == "__main__":
    unittest.main()
