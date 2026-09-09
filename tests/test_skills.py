"""Static checks on the workflow layer: skill and agent frontmatter, the script flags the
instructions promise, and the kit paths they point at.

No third-party YAML parser: the frontmatter used here is a flat `key: value` subset, so it is
parsed with the standard library only.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
AGENTS = ROOT / ".claude" / "agents"

# The cost gates the user types. Everything else is a component a stage skill may invoke.
STAGE_SKILLS = {"sort", "analyse", "deep-dive", "eval"}
COMPONENT_SKILLS = {
    "check", "prepare", "read", "match", "judge", "extract", "map", "report", "visualise",
}

# Directories whose referenced paths must exist on disk.
KIT_DIRS = ("stage1", "stage2", "dcg", "scripts", "assets")

PATH_RE = re.compile(r"(?<![\w/.-])(?:%s)/[A-Za-z0-9_./-]*" % "|".join(KIT_DIRS))
COMMAND_RE = re.compile(r"python3?\s+scripts/(\w+)\.py([^`\n]*)")
FLAG_RE = re.compile(r"--[a-z][a-z0-9-]*")
ADD_ARGUMENT_RE = re.compile(r"add_argument\(([^)]*)")


def split_frontmatter(text, source):
    """Return (frontmatter dict, body) for a Markdown file with `---` frontmatter."""
    if not text.startswith("---\n"):
        raise AssertionError(f"{source}: no YAML frontmatter")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise AssertionError(f"{source}: unterminated frontmatter")
    block, body = text[4:end + 1], text[end + 5:]
    data = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise AssertionError(f"{source}: frontmatter line is not `key: value`: {line!r}")
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            quote = value[0]
            inner = value[1:-1]
            if quote in inner.replace("\\" + quote, ""):
                raise AssertionError(f"{source}: unescaped {quote} in {key}")
            if quote == '"':
                inner = inner.replace('\\"', '"').replace("\\\\", "\\")
            value = inner
        elif value.startswith("[") or (":" in value and not value.startswith("http")):
            pass  # lists and colon-bearing plain scalars are kept verbatim
        data[key] = value
    return data, body


def joined_lines(text):
    """Join shell continuation lines so a wrapped command reads as one line."""
    return re.sub(r"\\\n\s*", " ", text)


def instruction_files():
    """Every file whose text drives a run: skills, agents and the two doc files."""
    files = sorted(SKILLS.glob("*/SKILL.md")) + sorted(AGENTS.glob("*.md"))
    files += [ROOT / "README.md", ROOT / "CLAUDE.md"]
    return files


def argparse_flags(script):
    """Flags the script's argparse actually defines."""
    text = script.read_text()
    flags = set()
    for call in ADD_ARGUMENT_RE.findall(text):
        flags.update(FLAG_RE.findall(call))
    return flags


class FrontmatterTest(unittest.TestCase):
    def test_every_skill_and_agent_parses(self):
        seen = 0
        for path in sorted(SKILLS.glob("*/SKILL.md")) + sorted(AGENTS.glob("*.md")):
            with self.subTest(path=str(path.relative_to(ROOT))):
                data, body = split_frontmatter(path.read_text(), path.name)
                self.assertIn("name", data)
                self.assertIn("description", data)
                self.assertTrue(body.strip(), "empty body")
                seen += 1
        self.assertGreaterEqual(seen, len(STAGE_SKILLS) + len(COMPONENT_SKILLS))

    def test_skill_directories_match_the_expected_set(self):
        found = {p.parent.name for p in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(found, STAGE_SKILLS | COMPONENT_SKILLS)

    def test_skill_name_matches_its_directory(self):
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            data, _ = split_frontmatter(path.read_text(), path.name)
            self.assertEqual(data["name"], path.parent.name)

    def test_stage_skills_are_user_only(self):
        for name in sorted(STAGE_SKILLS):
            path = SKILLS / name / "SKILL.md"
            data, _ = split_frontmatter(path.read_text(), path.name)
            self.assertEqual(
                data.get("disable-model-invocation"), "true",
                f"/{name} is a cost gate: it must keep disable-model-invocation: true",
            )

    def test_component_skills_are_invokable(self):
        for name in sorted(COMPONENT_SKILLS):
            path = SKILLS / name / "SKILL.md"
            data, _ = split_frontmatter(path.read_text(), path.name)
            self.assertNotIn(
                "disable-model-invocation", data,
                f"/{name} is invoked by a stage skill: it must not be model-disabled",
            )

    def test_component_skills_say_they_stop_after_their_step(self):
        for name in sorted(COMPONENT_SKILLS):
            body = (SKILLS / name / "SKILL.md").read_text()
            self.assertIn("Normally invoked by a stage skill", body, name)
            self.assertIn("stops after its own step", body, name)

    def test_agent_models_and_caps(self):
        expected_model = {
            "filer": "haiku", "reader": "sonnet", "extractor": "sonnet",
            "judge": "opus", "mapper": "opus",
        }
        for agent, model in expected_model.items():
            data, _ = split_frontmatter((AGENTS / f"{agent}.md").read_text(), agent)
            self.assertEqual(data.get("model"), model, agent)

    def test_filer_turn_cap_is_twenty(self):
        data, _ = split_frontmatter((AGENTS / "filer.md").read_text(), "filer.md")
        self.assertEqual(data.get("maxTurns"), "20",
                         "5 of 29 Haiku filers hit maxTurns 12 in the live test")

    def test_judge_writes_the_safe_placements_path(self):
        body = (AGENTS / "judge.md").read_text()
        self.assertIn("safe_folder_name", body,
                      "judge.md must name kit_common.safe_folder_name, as mapper.md does")
        self.assertIn("work/placements/<safe_account>.csv", body)
        self.assertIn("work/placements/<safe_account>.md", body)
        self.assertNotIn("work/placements/<account>.", body)

    def test_judge_does_not_append_the_shared_log(self):
        body = (AGENTS / "judge.md").read_text()
        self.assertNotIn("Append one line per document to `work/logs/judge.log`", body)
        skill = (SKILLS / "judge" / "SKILL.md").read_text()
        self.assertIn("work/logs/judge.log", skill,
                      "the main session appends judge.log")


class ScriptFlagTest(unittest.TestCase):
    def test_every_promised_flag_exists_in_argparse(self):
        checked = 0
        for path in instruction_files():
            text = joined_lines(path.read_text())
            for script_name, args in COMMAND_RE.findall(text):
                script = ROOT / "scripts" / f"{script_name}.py"
                with self.subTest(file=path.name, script=script_name):
                    self.assertTrue(script.exists(), f"{path.name} names a missing script")
                    # a second command on the same line belongs to that command
                    args = re.split(r"python3?\s+scripts/", args)[0]
                    defined = argparse_flags(script)
                    for flag in FLAG_RE.findall(args):
                        self.assertIn(
                            flag, defined,
                            f"{path.name} tells the model to run "
                            f"`python scripts/{script_name}.py {flag}`, "
                            f"which argparse does not define",
                        )
                        checked += 1
        self.assertGreater(checked, 20, "the flag scan found suspiciously little to check")

    def test_cost_report_is_wired_into_every_stage(self):
        for stage in ("sort", "analyse", "deep-dive"):
            body = (SKILLS / stage / "SKILL.md").read_text()
            if stage != "sort":  # Light sort has only main-session usage, no spawned agents.
                self.assertIn("scripts/cost.py --append", body, stage)
                self.assertIn(f"scripts/cost.py --stage {stage}", body, stage)
            self.assertIn("/cost", body, stage)
            self.assertIn("cache read", body, f"{stage} must name the four /cost figures")

    def test_light_and_analysis_request_their_budgeted_models(self):
        for stage, model in (("sort", "haiku"), ("analyse", "opus")):
            frontmatter, _ = split_frontmatter((SKILLS / stage / "SKILL.md").read_text(), stage)
            self.assertEqual(model, frontmatter.get("model"))


class ReferencedPathTest(unittest.TestCase):
    def test_every_referenced_kit_path_exists(self):
        checked = 0
        for path in instruction_files():
            for raw in PATH_RE.findall(path.read_text()):
                ref = raw.rstrip("`'\",;:)").rstrip(".")
                if not ref or ref.endswith("/"):
                    ref = ref.rstrip("/")
                if "<" in ref or ">" in ref or not ref:
                    continue  # a placeholder such as scripts/<name>.py
                with self.subTest(file=path.name, ref=ref):
                    self.assertTrue((ROOT / ref).exists(),
                                    f"{path.name} refers to {ref}, which does not exist")
                    checked += 1
        self.assertGreater(checked, 20, "the path scan found suspiciously little to check")


class PythonNamingTest(unittest.TestCase):
    def test_skills_and_readme_allow_python3(self):
        sentence = "use `python3` where that is the installed name"
        for path in sorted(SKILLS.glob("*/SKILL.md")) + [ROOT / "README.md"]:
            flat = " ".join(path.read_text().split())
            self.assertTrue(sentence in flat,
                            f"{path.name} must say: python (or python3 where that is installed)")


if __name__ == "__main__":
    unittest.main()
