"""The per-stage token report: role totals, retries, unknowns, extrapolation and appending."""

import inspect
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cost  # noqa: E402

LEDGER = """\
stage,role,model,target,attempt,outcome,tokens,duration_ms,units_read
sort,filer,haiku,001,1,ok,9800,40000,3
sort,filer,haiku,002,1,maxTurns,4100,50000,3
sort,filer,haiku,002,2,ok,11200,45000,2
sort,filer,haiku,003,1,ok,10400,30000,unknown
sort,filer,haiku,004,1,ok,unknown,45000,3
analyse,reader,sonnet,001,1,ok,42000,120000,18
analyse,reader,sonnet,002,1,ok,38000,110000,12
analyse,reader,sonnet,003,1,ok,40000,100000,10
analyse,reader,sonnet,003,2,ok,20000,50000,10
analyse,judge,opus,Northgate Rail,1,ok,90000,200000,
analyse,judge,opus,Sturmore Rail Group,1,error,30000,60000,
"""

CLOSING = ("Main session tokens are not visible to the model; type /cost for this session's own "
           "usage and add it to the stage total.")


class TokenReport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dcg-cost-test-")
        self.addCleanup(self.temp.cleanup)
        self.ledger = Path(self.temp.name) / "logs" / "cost.csv"
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text(LEDGER, encoding="utf-8")

    def cost(self, *args, success=True):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/cost.py"),
                                 "--ledger", str(self.ledger), *args],
                                cwd=self.temp.name, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def rows(self, output, stage=None):
        """Markdown table rows as {first cell: [cells]}, optionally under one stage heading."""
        if stage is not None:
            output = output.split(f"### {stage}", 1)[1].split("\n### ", 1)[0]
        table = {}
        for line in output.splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip().strip("*") for cell in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= {"-"} or cells[0] == "role":
                continue
            table[cells[0]] = cells
        return table

    def test_per_role_totals_targets_units_and_wall_clock(self):
        output = self.cost()
        self.assertIn("### sort", output)
        filer = self.rows(output, "sort")["filer"]
        role, model, agents, retries, failures, tokens, per_target, per_unit, wall = filer
        self.assertEqual((model, agents), ("haiku", "5"))
        # 9800 + 4100 + 11200 + 10400, the unknown row counted as zero.
        self.assertEqual(tokens, "35500 (1 unknown)")
        # Four distinct targets, retries included: 35500 / 4.
        self.assertEqual(per_target, "8875")
        # Only rows with both figures known: (9800 + 4100 + 11200) / (3 + 3 + 2) = 3137.5.
        self.assertEqual(per_unit, "3138")
        self.assertEqual(wall, "3m 30s")
        self.assertEqual(self.rows(output, "sort")["total"][2:], ["5", "1", "1", "35500 (1 unknown)",
                                                                 "8875", "3138", "3m 30s"])
        self.assertIn("4 distinct targets", output)

        analyse = self.rows(output, "analyse")
        self.assertEqual(analyse["reader"][5:8], ["140000", "46667", "2800"])
        self.assertEqual(analyse["judge"][5:8], ["120000", "60000", "—"])
        # The stage total counts each distinct target once: 260000 / 5 targets.
        self.assertEqual(analyse["total"][5:7], ["260000", "52000"])

    def test_retries_and_failures_are_counted_separately(self):
        output = self.cost()
        sort_rows, analyse_rows = self.rows(output, "sort"), self.rows(output, "analyse")
        self.assertEqual(sort_rows["filer"][3:5], ["1", "1"])          # one retry, one non-ok row
        self.assertEqual(analyse_rows["reader"][3:5], ["1", "0"])      # a retry that succeeded
        self.assertEqual(analyse_rows["judge"][3:5], ["0", "1"])       # a failure at first attempt
        self.assertEqual(analyse_rows["total"][3:5], ["1", "1"])

    def test_unknown_tokens_count_as_zero_and_unknown_units_are_left_out(self):
        self.ledger.write_text(
            "stage,role,model,target,attempt,outcome,tokens,duration_ms,units_read\n"
            "sort,filer,haiku,001,1,ok,unknown,1000,4\n"
            "sort,filer,haiku,002,1,ok,,2000,\n"
            "sort,filer,haiku,003,1,ok,6000,3000,unknown\n", encoding="utf-8")
        filer = self.rows(self.cost(), "sort")["filer"]
        self.assertEqual(filer[5], "6000 (2 unknown)")
        self.assertEqual(filer[6], "2000")   # 6000 / 3 targets
        self.assertEqual(filer[7], "—")      # no row has both tokens and units

    def test_extrapolation_scales_document_roles_and_leaves_accounts_to_the_user(self):
        output = self.cost("--stage", "analyse", "--extrapolate", "200")
        self.assertNotIn("### sort", output)
        self.assertIn("#### Extrapolated to 200 documents", output)
        table = self.rows(output.split("#### Extrapolated")[1])
        reader = table["reader"]
        self.assertEqual(reader[1], "per document")
        self.assertEqual(reader[2], "46667")           # 140000 / 3 targets
        self.assertEqual(reader[3], "1.33")            # 4 agents over 3 targets
        self.assertEqual(reader[4], str(int(140000 / 3 * 200 + 0.5)))   # 9333333
        self.assertEqual(reader[5], "2800")
        self.assertEqual(table["judge"][1], "per account")
        self.assertEqual(table["judge"][4], "per account × your account count")
        self.assertEqual(table["document roles"][4], reader[4])
        self.assertIn("the account count", output.replace("number of accounts", "the account count"))
        self.assertIn("multiply the tokens/unit read figure by the pages", output)
        # The retry rate is inside the per-target figure: per attempt × attempts per target.
        per_attempt, attempts = 140000 / 4, 4 / 3
        self.assertEqual(int(per_attempt * attempts * 200 + 0.5), int(reader[4]))
        self.cost("--extrapolate", "0", success=False)

    def test_stage_selection_and_a_missing_ledger_stay_plain(self):
        self.assertIn("### sort", self.cost("--stage", "all"))
        output = self.cost("--stage", "deep-dive")
        self.assertIn("no rows for stage 'deep-dive'", output)
        self.assertIn("sort; analyse", output)
        self.ledger.unlink()
        missing = self.cost()
        self.assertIn("No cost ledger", missing)
        self.assertTrue(missing.rstrip().endswith(CLOSING))

    def test_append_creates_the_ledger_with_its_header_and_adds_one_row(self):
        fresh = Path(self.temp.name) / "new" / "cost.csv"
        self.ledger = fresh
        self.cost("--append", "--stage", "sort", "--role", "filer", "--model", "haiku",
                  "--target", "017", "--attempt", "1", "--outcome", "ok", "--tokens", "9800",
                  "--duration-ms", "41000", "--units-read", "3")
        self.cost("--append", "--stage", "sort", "--role", "filer", "--model", "haiku",
                  "--target", "018", "--attempt", "2", "--outcome", "ok", "--tokens", "unknown",
                  "--duration-ms", "12000", "--units-read", "")
        lines = fresh.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], ",".join(cost.LEDGER_COLUMNS))
        self.assertEqual(lines[1], "sort,filer,haiku,017,1,ok,9800,41000,3")
        self.assertEqual(lines[2], "sort,filer,haiku,018,2,ok,unknown,12000,")
        self.assertEqual(len(lines), 3)
        filer = self.rows(self.cost(), "sort")["filer"]
        self.assertEqual(filer[2:7], ["2", "1", "0", "9800 (1 unknown)", "4900"])
        self.cost("--append", "--role", "filer", success=False)          # no stage
        self.cost("--append", "--stage", "sort", success=False)          # no role

    def test_append_row_helper_writes_the_same_row(self):
        signature = list(inspect.signature(cost.append_row).parameters)
        self.assertEqual(signature[:9], ["stage", "role", "model", "target", "attempt",
                                         "outcome", "tokens", "duration_ms", "units_read"])
        path = Path(self.temp.name) / "helper" / "cost.csv"
        cost.append_row("analyse", "reader", "sonnet", "007", 1, "ok", 42000, 120000, 18,
                        ledger=path)
        cost.append_row("analyse", "judge", "opus", "Northgate Rail", 1, "ok", 90000, 200000, "",
                        ledger=path)
        self.assertEqual(path.read_text(encoding="utf-8").splitlines(), [
            ",".join(cost.LEDGER_COLUMNS),
            "analyse,reader,sonnet,007,1,ok,42000,120000,18",
            "analyse,judge,opus,Northgate Rail,1,ok,90000,200000,",
        ])

    def test_the_report_ends_with_the_fixed_main_session_line_and_no_currency(self):
        for args in ([], ["--stage", "sort"], ["--stage", "sort", "--extrapolate", "40"]):
            with self.subTest(args=args):
                output = self.cost(*args)
                self.assertTrue(output.rstrip().endswith(CLOSING), output)
                self.assertEqual(output.count(CLOSING), 1)
                self.assertFalse(set("$£€") & set(output))
                for word in ("cost per", "price", "USD", "GBP", "spend"):
                    self.assertNotIn(word, output)


if __name__ == "__main__":
    unittest.main()
