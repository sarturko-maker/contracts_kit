"""Evaluation provenance and isolation checks; these are not model evaluation trials."""
import contextlib
import csv
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("eval_runner", Path(__file__).parents[1] / "eval" / "run.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class EvalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / "work" / "eval"
        self.kit = self.work / "kit"
        self.runs = self.work / "runs"
        self.runs.mkdir(parents=True)
        self.overrides = patch.multiple(RUNNER, ROOT=self.root, EVAL=self.root / "eval",
                                       WORK=self.work, KIT=self.kit, RUNS=self.runs)
        self.overrides.start()
        self.addCleanup(self.overrides.stop)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        return path

    def response(self, mode="A", **changes):
        run = {"question_id": "Q01", "mode": mode, "answer": "Synthetic answer for scorer tests.",
               "evidence": [{"doc_id": "001", "ref": "p1", "words": "Synthetic test words"}],
               "read_log": [{"doc_id": "001", "pages": [1, 1, 2], "docx": False},
                            {"doc_id": "004", "pages": [], "docx": True}],
               "files_read": ["work/text/001.txt", "work/text/004.txt"]}
        run.update(changes)
        self.write(f"work/eval/runs/Q01-{mode}.json", json.dumps(run))

    def grade(self, mode="A", **changes):
        self.write("work/eval/transcripts/synthetic.txt", "Harness fixture, not a real model trial.")
        grade = {"agent_id": "synthetic-agent", "fresh_context": True,
                 "transcript": "work/eval/transcripts/synthetic.txt", "access_compliant": True,
                 "correct": True, "evidence_cited": True, "wrong_part_error": False,
                 "pages_verified": True, "reason": "Synthetic harness fixture only."}
        grade.update(changes)
        self.write(f"work/eval/runs/Q01-{mode}.grade.json", json.dumps(grade))

    def test_scratch_omits_operator_data_keys_expected_and_local_settings(self):
        for file in ("CLAUDE.md", "README.md", "requirements.txt", "scripts/main.py",
                     "stage1/card.md", "stage2/form.md", "dcg/types.csv", "assets/mermaid.min.js",
                     ".claude/agents/reader.md", ".claude/skills/read/SKILL.md",
                     "inputs/entity-map.example.csv", "eval/pile/ERP_record.csv"):
            self.write(file, "allowed fixture")
        forbidden = ["inputs/entity-map.csv", "inputs/erp-record.csv", "work/cards/001.json",
                     "out/CORPUS.csv", "eval/questions.csv", "sample/expected/answer.json",
                     ".claude/settings.local.json", ".claude/private-notes.txt", ".env"]
        for file in forbidden:
            self.write(file, "PRIVATE OPERATOR DATA OR ANSWER KEY")
        with contextlib.redirect_stdout(io.StringIO()):
            RUNNER.prepare()
        for file in self.kit.rglob("*"):
            if file.is_file():
                self.assertNotIn("PRIVATE OPERATOR", file.read_text())
        self.assertTrue((self.kit / "inputs/entity-map.example.csv").is_file())
        self.assertTrue((self.kit / "pile/ERP_record.csv").is_file())
        self.assertFalse((self.kit / "eval/questions.csv").exists())
        self.assertEqual((self.root / "inputs/entity-map.csv").read_text(), "PRIVATE OPERATOR DATA OR ANSWER KEY")

    def test_existing_scratch_is_not_overwritten(self):
        self.kit.mkdir()
        (self.kit / "marker").write_text("existing run")
        with contextlib.redirect_stdout(io.StringIO()):
            RUNNER.prepare()
        self.assertEqual((self.kit / "marker").read_text(), "existing run")

    def test_mode_b_rejects_form_columns_in_its_map(self):
        self.write('eval/questions.csv', 'id,scope,account,question\nQ01,account,Tallowfield Industries,Test question?\n')
        self.write('work/eval/kit/out/graph/nodes.csv', 'id:ID\n')
        path = self.write('work/eval/kit/out/customers/Tallowfield Industries/documents.csv', '')
        for extra in (['form_B_B3_whose_paper'], []):
            with path.open('w', newline='') as handle:
                csv.writer(handle).writerow(list(RUNNER.CORPUS_COLUMNS) + extra)
            with contextlib.redirect_stdout(io.StringIO()):
                if extra:
                    with self.assertRaisesRegex(ValueError, 'stage 1 columns only'):
                        RUNNER.prompt('Q01', 'B')
                else:
                    RUNNER.prompt('Q01', 'B')

    def test_missing_or_ungraded_runs_remain_explicit(self):
        self.assertEqual(RUNNER.score_run("Q01", "A", set())[-2], "NOT RUN")
        self.response()
        self.assertEqual(RUNNER.score_run("Q01", "A", set())[-2], "NOT GRADED")

    def test_distinct_source_pages_and_docx_count_separately(self):
        self.response()
        self.grade()
        result = RUNNER.score_run("Q01", "A", set())
        self.assertEqual(result[:6], ["yes", "yes", "no", "2", "1", "SCORED"])

    def test_unverified_cost_is_not_guessed(self):
        self.response()
        self.grade(pages_verified=False)
        self.assertEqual(RUNNER.score_run("Q01", "A", set())[3:5], ["not measured", "not measured"])

    def test_reused_agent_and_missing_transcript_are_rejected(self):
        self.response()
        self.grade()
        with self.assertRaisesRegex(ValueError, "reused agent"):
            RUNNER.score_run("Q01", "A", {"synthetic-agent"})
        self.grade(transcript="does-not-exist.txt")
        with self.assertRaisesRegex(ValueError, "existing tool transcript"):
            RUNNER.score_run("Q01", "A", set())

    def test_inherited_context_or_wrong_mode_access_is_invalid(self):
        self.response()
        for changes in ({"fresh_context": False}, {"access_compliant": False}):
            self.grade(**changes)
            self.assertEqual(RUNNER.score_run("Q01", "A", set())[-2], "INVALID RUN")

    def test_graph_only_cannot_report_source_reading(self):
        self.response(mode="C")
        self.grade(mode="C")
        with self.assertRaisesRegex(ValueError, "graph-only run"):
            RUNNER.score_run("Q01", "C", set())

    def test_empty_evidence_cannot_receive_evidence_credit(self):
        self.response(evidence=[])
        self.grade()
        with self.assertRaisesRegex(ValueError, "without citations"):
            RUNNER.score_run("Q01", "A", set())

    def test_question_mismatch_is_rejected(self):
        self.response(question_id="Q02")
        self.grade()
        with self.assertRaisesRegex(ValueError, "question_id/mode mismatch"):
            RUNNER.score_run("Q01", "A", set())

    def test_structured_answer_preserved_without_rewriting_response(self):
        self.response(answer={"accounts": ["Invented fixture account"]})
        self.grade()
        self.assertEqual(RUNNER.score_run("Q01", "A", set())[-2], "SCORED")
        self.response(answer={})
        with self.assertRaisesRegex(ValueError, "answer must be nonempty"):
            RUNNER.score_run("Q01", "A", set())


if __name__ == "__main__":
    unittest.main()
