"""Bounded identity filing, evidence gates and isolated report/rerun acceptance."""

import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sample"))
sys.path.insert(0, str(ROOT / "scripts"))
from kit_common import STATUS_FOLDERS
from make_expected import ACCOUNT1, ACCOUNT2, NORTH, OURS, PARENT, isolated_kit


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, columns=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def hashes(folder):
    return {path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.rglob("*") if path.is_file()}


class FilingAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-filing-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = isolated_kit(Path(self.temp.name) / "kit")
        self.pile = Path(self.temp.name) / "pile"
        shutil.copytree(ROOT / "sample/pile", self.pile)
        self.prepare()
        self.inventory = {r["doc_id"]: r for r in read_csv(self.root / "work/inventory.csv")}
        for name in ("entity-map.csv", "our-entities.csv"):
            shutil.copyfile(ROOT / "sample/expected" / name, self.root / "inputs" / name)

    def command(self, script, *args, success=True):
        result = subprocess.run([sys.executable, f"scripts/{script}", *args], cwd=self.root,
                                text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def prepare(self):
        return self.command("prepare.py", str(self.pile), "--account-column", "customer_account", "--side", "customers")

    def filing(self, *args, success=True):
        return self.command("filing.py", *args, success=success)

    def record(self, doc="001"):
        if doc == "004":
            name, ref = ACCOUNT2, "¶ 2"
            words = f"Parties: {ACCOUNT2} (Customer) and {OURS} (Supplier)."
        elif doc == "003":
            name, ref = PARENT, "p.1"
            words = f"Parties: {PARENT} and {OURS}."
        else:
            name, ref = NORTH, "p.1"
            words = f"Parties: {OURS} (Supplier) and {NORTH} (Customer)."
        return {"doc_id": doc, "sha256": self.inventory[doc]["sha256"],
                "title": "Printed title", "kind": "agreement", "note": "Identity only; status unassessed.",
                "their_entities": [{"name": name, "ref": ref, "words": words}],
                "our_entities": [{"name": OURS, "ref": ref, "words": words}],
                "pages_read": [] if doc == "004" else [1],
                "paragraphs_read": [1, 2] if doc == "004" else []}

    def save(self, record, doc=None):
        path = self.root / "work/filing" / f"{doc or record['doc_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def full_cards(self):
        shutil.copytree(ROOT / "sample/expected/cards", self.root / "work/cards", dirs_exist_ok=True)

    def assert_report_consistent(self):
        out = self.root / "out"
        corpus = read_csv(out / "customers/CORPUS.csv")
        self.assertEqual({r["doc_id"] for r in corpus}, {f"{n:03}" for n in range(1, 11)})
        self.assertEqual(len(corpus), 10)
        self.assertTrue({"doc_id", "account", "title", "kind", "basis", "confidence", "sha256",
                         "file_path", "filed_as"} <= set(corpus[0]))
        self.assertFalse({"folder", "tree", "status", "governing_docs", "node_id", "edge_id"} & set(corpus[0]))
        targets = {r["account"] for r in corpus}
        for target in targets:
            folder = out / "customers" / target
            self.assertEqual(read_csv(folder / "documents.csv"), [r for r in corpus if r["account"] == target])
            readme = (folder / "README.md").read_text()
            self.assertIn("Identity and filing pass only", readme)
            for row in (r for r in corpus if r["account"] == target):
                self.assertIn(f"- {row['doc_id']} — {row['filed_as'] or '(no copy'}", readme)
                self.assertIn(f"original: {row['original_path']}", readme)
        for row in corpus:
            if row["file_path"]:
                copy_path = self.root / row["file_path"]
                self.assertTrue(copy_path.is_relative_to(out))
                self.assertEqual(hashlib.sha256(copy_path.read_bytes()).hexdigest(), row["sha256"])
                self.assertEqual(copy_path.name, row["filed_as"])
                self.assertTrue(re.match(rf"{row['doc_id']}[ .]", row["filed_as"]), row["filed_as"])
            elif row["doc_id"] != "010":
                self.fail(f"Readable doc {row['doc_id']} has no audit-linked copy")
            else:
                self.assertEqual(row["filed_as"], "")
        files = list(out.rglob("*"))
        self.assertFalse(any(p.suffix in (".html", ".mmd", ".js") for p in files))
        self.assertFalse((out / "graph").exists())
        self.assertFalse((out / "assets").exists())
        account_rows = read_csv(out / "customers/ACCOUNTS.csv")
        self.assertEqual(len(account_rows), 3)
        for row in account_rows:
            self.assertEqual(int(row["n_documents"]), sum(r["account"] == row["account"] for r in corpus))
        stream = out / "customers" / (ACCOUNT1 + " Data Centres")
        self.assertEqual([p.name for p in stream.iterdir()], ["README.md"])
        self.assertIn("Filing only", (out / "INDEX.md").read_text())
        return corpus

    def test_packets_bound_native_pdf_pages_and_word_paragraphs(self):
        text = self.root / "work/text"
        (text / "001.txt").write_text("\n".join(
            f"=== page {page} ===\n" + " ".join(f"pdf_{page}_{n}" for n in range(1000))
            for page in range(1, 5)))
        output = self.filing("--packet", "001").stdout
        self.assertEqual(re.findall(r"=== page (\d+) ===", output), ["1", "2"])
        self.assertEqual(len(re.findall(r"\bpdf_\d+_\d+\b", output)), 1200)
        self.assertNotIn("pdf_3_", output)
        extra = self.filing("--packet", "001", "--page", "4").stdout
        self.assertEqual(re.findall(r"=== page (\d+) ===", extra), ["4"])
        self.assertEqual(len(re.findall(r"\bpdf_\d+_\d+\b", extra)), 600)
        self.filing("--packet", "001", "--page", "5", success=False)

        (text / "004.txt").write_text("\n".join(
            f"[¶ {paragraph}]\n" + " ".join(f"word_{paragraph}_{n}" for n in range(100))
            for paragraph in range(1, 31)))
        output = self.filing("--packet", "004").stdout
        self.assertEqual(re.findall(r"=== paragraph (\d+) ===", output), [str(n) for n in range(1, 13)])
        self.assertEqual(len(re.findall(r"\bword_\d+_\d+\b", output)), 1200)
        self.assertNotIn("word_13_", output)
        extra = self.filing("--packet", "004", "--paragraph", "13").stdout
        self.assertEqual(re.findall(r"=== paragraph (\d+) ===", extra), [str(n) for n in range(13, 19)])
        self.assertEqual(len(re.findall(r"\bword_\d+_\d+\b", extra)), 600)
        self.assertNotIn("word_12_", extra)
        self.assertNotIn("word_19_", extra)
        self.filing("--packet", "004", "--paragraph", "31", success=False)
        self.filing("--packet", "001", "--paragraph", "1", success=False)
        self.filing("--packet", "004", "--paragraph", "13", "--page", "1", success=False)
        self.filing("--packet", "004", "--page", "1", success=False)
        self.filing("--packet", "010", success=False)

    def test_native_pdf_and_word_identity_quotes_validate_but_scans_need_review(self):
        for doc in ("001", "004", "003"):
            with self.subTest(doc=doc):
                self.save(self.record(doc))
                result = self.filing("--validate", doc)
                self.assertIn("valid filing record", result.stdout)
                if doc == "003":
                    self.assertIn("REVIEW:", result.stdout)
                    self.assertIn("scanned page", result.stdout)
                else:
                    self.assertNotIn("REVIEW:", result.stdout)

    def test_stale_hash_wrong_id_and_excessive_or_false_reading_budgets_are_rejected(self):
        changes = [
            {"sha256": "0" * 64}, {"doc_id": "002"}, {"pages_read": [1, 2, 3, 4]},
            {"pages_read": [1, 1]}, {"pages_read": [5]}, {"pages_read": [True]},
            {"pages_read": []}, {"paragraphs_read": [1]}, {"note": "word " * 81},
        ]
        for changeset in changes:
            with self.subTest(changes=changeset):
                self.save({**self.record(), **changeset}, "001")
                self.filing("--validate", "001", success=False)
        for changeset in ({"pages_read": [1]}, {"paragraphs_read": []},
                          {"paragraphs_read": list(range(1, 22))}):
            with self.subTest(word_changes=changeset):
                self.save({**self.record("004"), **changeset})
                self.filing("--validate", "004", success=False)

    def test_uncited_unread_or_nonverbatim_identities_are_rejected(self):
        changes = [
            {"ref": ""}, {"ref": "clause 1"}, {"ref": "p.3"},
            {"words": f"{NORTH} signed this agreement."},
            {"name": "Different Company Ltd"},
            {"name": NORTH.lower(), "words": self.record()["their_entities"][0]["words"].lower()},
            {"words": self.record()["their_entities"][0]["words"] + " extra" * 41},
        ]
        for changeset in changes:
            with self.subTest(changes=changeset):
                record = self.record()
                record["their_entities"][0].update(changeset)
                self.save(record)
                self.filing("--validate", "001", success=False)

    def test_cheap_records_reconcile_account_and_global_reports_with_unread_documents(self):
        for doc in ("001", "004"):
            self.save(self.record(doc))
        before_sources, before_copies = hashes(self.pile), hashes(self.root / "work/files")
        self.filing("--report")
        corpus = self.assert_report_consistent()
        by_doc = {r["doc_id"]: r for r in corpus}
        self.assertEqual(by_doc["001"]["account"], ACCOUNT1)
        self.assertEqual(by_doc["004"]["account"], ACCOUNT2)
        self.assertEqual(by_doc["001"]["read_status"], "filing_only")
        self.assertEqual(by_doc["003"]["account"], "_needs-reading")
        self.assertEqual(by_doc["003"]["read_status"], "needs_reading")
        self.assertEqual(by_doc["010"]["account"], "_unreadable")
        self.assertEqual(hashes(self.pile), before_sources)
        self.assertEqual(hashes(self.root / "work/files"), before_copies)
        self.assertFalse(any((self.root / "work/cards").glob("*.json")))
        self.assertFalse(any((self.root / "work/forms").glob("*.json")))
        self.assertFalse(any((self.root / "work/placements").glob("*.csv")))

    def test_uncertain_and_unidentified_companies_remain_in_holding_folders(self):
        record = self.record()
        record["their_entities"] = []
        self.save(record)
        self.save(self.record("003"))
        self.save(self.record("004"))
        entity_path = self.root / "inputs/entity-map.csv"
        entity_rows = read_csv(entity_path)
        entity_rows = [r for r in entity_rows if r["name_as_printed"] != ACCOUNT2]
        for row in entity_rows:
            if row["name_as_printed"] == PARENT:
                row.update(account="_not-sure", confidence="not sure", note="Identity unresolved.")
        write_csv(entity_path, entity_rows)
        self.filing("--report")
        corpus = self.assert_report_consistent()
        by_doc = {r["doc_id"]: r for r in corpus}
        self.assertEqual(by_doc["001"]["account"], "_no-name-found")
        self.assertEqual(by_doc["003"]["account"], "_not-sure/" + PARENT)
        self.assertEqual(by_doc["004"]["account"], "_not-on-the-list/" + ACCOUNT2)
        self.assertIn("Visual identity evidence needs review", by_doc["003"]["note"])

    def test_full_cards_are_reused_without_new_filing_reads_and_force_is_explicit(self):
        self.full_cards()
        before = hashes(self.root / "work/cards")
        pending = json.loads(self.filing("--pending").stdout)
        self.assertEqual(pending["pending"], [])
        self.assertEqual(pending["reused"], [f"{n:03}" for n in range(1, 10)])
        forced = json.loads(self.filing("--pending", "--force").stdout)
        self.assertEqual(forced["pending"], pending["reused"])
        self.assertEqual(forced["reused"], [])
        self.filing("--report")
        corpus = self.assert_report_consistent()
        self.assertTrue(all(r["read_status"] == "full_card_reused" for r in corpus if r["doc_id"] != "010"))
        self.assertFalse(any((self.root / "work/filing").glob("*.json")))
        self.assertEqual(hashes(self.root / "work/cards"), before)

    def test_previous_generated_report_is_archived_without_changing_model_records_or_sources(self):
        self.full_cards()
        form = self.root / "work/forms/001.json"
        form.parent.mkdir(parents=True, exist_ok=True)
        form.write_text('{"preserved":"existing full analysis"}')
        out = self.root / "out"
        for relative, body in [("INDEX.html", "old html"), ("graph/nodes.csv", "old graph"),
                               (f"customers/{ACCOUNT1}/position.mmd", "old diagram")]:
            target = out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body)
        before = {name: hashes(path) for name, path in {
            "out": out, "cards": self.root / "work/cards", "forms": self.root / "work/forms",
            "sources": self.pile, "copies": self.root / "work/files"}.items()}
        self.filing("--report")
        archives = list((self.root / "work/history").glob("filing-*/out"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(hashes(archives[0]), before["out"])
        for name, path in {"cards": self.root / "work/cards", "forms": self.root / "work/forms",
                           "sources": self.pile, "copies": self.root / "work/files"}.items():
            self.assertEqual(hashes(path), before[name])
        self.assert_report_consistent()

    def test_invalid_filing_records_remain_pending_and_report_as_needing_reading(self):
        for malformed in (False, True):
            with self.subTest(malformed=malformed):
                record = self.record()
                record["sha256"] = "0" * 64
                path = self.save(record)
                if malformed:
                    path.write_text('{"broken":')
                self.filing("--validate", "001", success=False)
                pending = self.filing("--pending")
                self.assertIn("001", json.loads(pending.stdout)["pending"])
                self.assertIn("invalid filing record", pending.stderr)
                self.filing("--report")
                corpus = read_csv(self.root / "out/customers/CORPUS.csv")
                row = next(r for r in corpus if r["doc_id"] == "001")
                self.assertEqual(row["account"], "_needs-reading")
                self.assertEqual(row["read_status"], "needs_reading")
                self.assertTrue(path.exists(), "Keep the rejected record for its owner to fix.")

    def test_changed_source_archives_its_filing_record_and_retains_unchanged_readings(self):
        original = self.save(self.record())
        other = self.save(self.record("004"))
        original_bytes, other_bytes = original.read_bytes(), other.read_bytes()
        # Replace only the isolated source; retain its path/doc id while changing content.
        shutil.copyfile(self.pile / "05 Purchase Order.pdf", self.pile / "01 Supply Agreement.pdf")
        self.prepare()
        self.assertFalse(original.exists())
        self.assertEqual(other.read_bytes(), other_bytes)
        archived = list((self.root / "work/history").glob("*/filing/001.json"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_bytes(), original_bytes)
        pending = json.loads(self.filing("--pending").stdout)
        self.assertIn("001", pending["pending"])
        self.assertNotIn("004", pending["pending"])

    def test_upgrade_to_full_analysis_archives_cheap_leftovers_after_prerequisite_checks(self):
        self.save(self.record())
        self.filing("--report")
        out = self.root / "out"
        before_report = hashes(out)
        self.assertTrue((out / "customers/_needs-reading/documents.csv").exists())
        self.assertTrue((out / "customers/_unreadable/documents.csv").exists())
        self.assertTrue((out / "customers" / ACCOUNT1 / "files").exists())
        # A mistaken /match before full reading cannot retire the usable filing report.
        self.command("sort.py", success=False)
        self.assertEqual(hashes(out), before_report)
        self.assertFalse(list((self.root / "work/history").glob("analysis-transition-*")))

        self.full_cards()
        prepared = self.root / "work/files/001.pdf"
        temporary = Path(self.temp.name) / "held-prepared-copy.pdf"
        prepared.rename(temporary)
        self.command("sort.py", success=False)
        self.assertEqual(hashes(out), before_report)
        self.assertFalse(list((self.root / "work/history").glob("analysis-transition-*")))
        temporary.rename(prepared)

        form = self.root / "work/forms/001.json"
        form.parent.mkdir(parents=True, exist_ok=True)
        form.write_text('{"preserved":"full analysis"}')
        preserved = {name: hashes(path) for name, path in {
            "cards": self.root / "work/cards", "forms": self.root / "work/forms",
            "filing": self.root / "work/filing", "inputs": self.root / "inputs",
            "sources": self.pile, "copies": self.root / "work/files"}.items()}
        self.command("sort.py")
        archives = list((self.root / "work/history").glob("analysis-transition-*/out"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(hashes(archives[0]), before_report)
        # Deterministic fixture placements stand in for the next /judge stage.
        shutil.copytree(ROOT / "sample/expected/placements", self.root / "work/placements", dirs_exist_ok=True)
        self.command("place.py", "--all")
        self.assertFalse((out / "customers/_needs-reading").exists())
        self.assertFalse((out / "customers/_unreadable").exists())
        self.assertFalse(any(path.name == "files" for path in out.rglob("*") if path.is_dir()))
        stream = out / "customers" / (ACCOUNT1 + " Data Centres")
        self.assertEqual([p.name for p in stream.iterdir()], ["README.md"])
        corpus = read_csv(out / "customers/CORPUS.csv")
        self.assertEqual(len(corpus), 10)
        self.assertNotIn("read_status", corpus[0])
        self.assertIn("folder", corpus[0])
        copies = [path for path in out.rglob("*") if path.is_file()
                  and path.parent.name in STATUS_FOLDERS and re.match(r"\d{3} \S", path.name)]
        self.assertEqual(len(copies), 9)
        self.assertEqual({row["filed_as"] for row in corpus if row["doc_id"] != "010"},
                         {path.name for path in copies})
        for name, path in {"cards": self.root / "work/cards", "forms": self.root / "work/forms",
                           "filing": self.root / "work/filing", "inputs": self.root / "inputs",
                           "sources": self.pile, "copies": self.root / "work/files"}.items():
            self.assertEqual(hashes(path), preserved[name])
        # Subsequent analysis replay must not archive the full report a second time.
        self.command("sort.py")
        self.command("place.py", "--all")
        self.assertEqual(list((self.root / "work/history").glob("analysis-transition-*/out")), archives)
        self.assertEqual(hashes(archives[0]), before_report)


if __name__ == "__main__":
    unittest.main()
