#!/usr/bin/env python3
"""Prepare isolated eval inputs, print blind prompts, and score reviewed agent runs."""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from kit_common import CORPUS_COLUMNS

EVAL = ROOT / "eval"
WORK = ROOT / "work" / "eval"
KIT = WORK / "kit"
RUNS = WORK / "runs"
ACCOUNTS = {
    "Tallowfield Industries": ["001", "002", "003", "008", "009"],
    "Pellmont Logistics Group": ["004", "005", "006", "007"],
    "Quenby Marine Services": ["011", "012"],
}


def questions():
    with (EVAL / "questions.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def prepare():
    if KIT.exists():
        print(f"Reusing isolated kit: {KIT}")
        return
    if not (EVAL / "pile" / "ERP_record.csv").is_file():
        raise ValueError("Build the invented pile first: python eval/make_pile.py")
    KIT.mkdir(parents=True)
    # An allowlist keeps expected answers, other runs and real operator data out.
    for name in ("CLAUDE.md", "README.md", "requirements.txt", "scripts", "stage1",
                 "stage2", "dcg", "assets", ".claude/agents", ".claude/skills"):
        source, target = ROOT / name, KIT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, target)
    (KIT / "inputs").mkdir()
    for source in (ROOT / "inputs").glob("*.example.csv"):
        shutil.copy2(source, KIT / "inputs" / source.name)
    shutil.copytree(EVAL / "pile", KIT / "pile")
    RUNS.mkdir(parents=True, exist_ok=True)
    print(f"Isolated kit: {KIT}")
    print("Run stage 1 on pile, then stage 2 with --all and topics off, in this kit.")
    print("As-of date: 2026-09-06. ERP customer_account; customers; no external sources.")


def prompt(question_id, mode):
    question = next((q for q in questions() if q["id"] == question_id), None)
    if question is None:
        raise ValueError(f"Unknown question {question_id}")
    if not (KIT / "out" / "graph" / "nodes.csv").is_file():
        raise ValueError("Complete isolated stages 1 and 2 before creating evaluation prompts")
    accounts = list(ACCOUNTS) if question["scope"] == "corpus" else [question["account"]]
    if mode == "B":
        for account in accounts:
            path = KIT / 'out' / 'customers' / account / 'documents.csv'
            with path.open(encoding='utf-8-sig', newline='') as handle:
                columns = next(csv.reader(handle), [])
            if columns != list(CORPUS_COLUMNS):
                raise ValueError('Mode B requires stage 1 columns only. In the isolated kit, '
                                 'run python scripts/place.py --all after graph generation, '
                                 'then generate prompts again.')
    ids = sorted({doc for account in accounts for doc in ACCOUNTS[account]})
    print(f"Answer one invented-contract question, as of 2026-09-06. Mode {mode}.")
    print(f"Question {question_id}: {question['question']}")
    print(f"All permitted material is under {KIT}. No other files, network, tools that call")
    print("another model, answer keys or expected outputs. Do not alter any file.")
    print(f"Accounts: {', '.join(accounts)}. Documents: {', '.join(ids)}.")
    if mode == "A":
        print("Read EVERY listed document in full, using work/text/NNN.txt and work/files/NNN.*.")
        print("Full-page PNG previews are under work/files/NNN-pages/<page>.png; use view_image.")
        print("View scanned/image pages and signatures as pictures. Do not read cards, forms,")
        print("placements, maps or graph output. No OCR. DOCX text and extracted media are allowed.")
    elif mode == "B":
        print("First read each listed account's out/customers/<account>/README.md,")
        print("documents.csv and position.mmd. Then read only the document and part these point")
        print("to for this question, from work/text/NNN.txt or work/files/NNN.*. View relevant")
        print("pages via PNG previews at work/files/NNN-pages/<page>.png using view_image.")
        print("scanned/signature pages as pictures. Do not read forms, graph rows or other files.")
    else:
        print("Read only work/forms/NNN.json for listed ids and out/graph/nodes.csv and edges.csv.")
        print("No source documents, native text, cards, maps or position notes. If the fixed")
        print("answers cannot resolve the question, state what is missing instead of guessing.")
    print("Track actual access: count distinct PDF/image pages, including pages whose native")
    print("text you read; rereads count once. DOCX has no stable pages: record a separate text")
    print("unit per DOCX read, and paragraphs in the ref. Derived maps/forms are not source pages.")
    print("Return ONLY JSON with question_id, mode, answer, evidence (list of {doc_id, ref,")
    print("words, part, source}), read_log (list of {doc_id, pages: [integer], docx: boolean}),")
    print("files_read (every permitted path opened), and notes. Cite exact words ≤40 per quote.")
    print("Use [] for read_log in mode C. Be explicit when a part expired or was replaced.")


def load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def score_run(question_id, mode, seen_agents):
    path = RUNS / f"{question_id}-{mode}.json"
    grade_path = path.with_suffix(".grade.json")
    if not path.exists():
        return ["—"] * 5 + ["NOT RUN", "No saved fresh-agent response."]
    if not grade_path.exists():
        return ["—"] * 5 + ["NOT GRADED", "Response saved; transcript review needed."]
    run, grade = load(path), load(grade_path)
    if run.get("question_id") != question_id or run.get("mode") != mode:
        raise ValueError(f"{path}: question_id/mode mismatch")
    answer = run.get("answer")
    if not isinstance(answer, (str, dict, list)) or not answer or (isinstance(answer, str) and not answer.strip()):
        raise ValueError(f"{path}: answer must be nonempty text, object or list")
    for field in ("evidence", "read_log", "files_read"):
        if not isinstance(run.get(field), list):
            raise ValueError(f"{path}: {field} must be a list")
    for field in ("correct", "evidence_cited", "wrong_part_error", "access_compliant",
                  "fresh_context", "pages_verified"):
        if not isinstance(grade.get(field), bool):
            raise ValueError(f"{grade_path}: {field} must be a reviewed boolean")
    if grade["evidence_cited"] and not run["evidence"]:
        raise ValueError(f"{grade_path}: evidence cannot be scored present without citations")
    agent = grade.get("agent_id")
    if not agent or agent in seen_agents:
        raise ValueError(f"{grade_path}: missing or reused agent id; each run must be fresh")
    seen_agents.add(agent)
    transcript = ROOT / grade.get("transcript", "")
    if not transcript.is_file() or not grade.get("reason"):
        raise ValueError(f"{grade_path}: existing tool transcript and grading reason required")
    if not grade["fresh_context"] or not grade["access_compliant"]:
        return ["—"] * 5 + ["INVALID RUN", grade.get("table_note", grade["reason"])]
    page_pairs, docx = set(), set()
    for access in run.get("read_log", []):
        doc = access["doc_id"]
        if access.get("docx"):
            docx.add(doc)
        for page in access.get("pages", []):
            if type(page) is not int or page < 1:
                raise ValueError(f"{path}: source pages must be positive integers")
            page_pairs.add((doc, page))
    if mode == "C" and (page_pairs or docx):
        raise ValueError(f"{path}: graph-only run read source pages")
    costs = [str(len(page_pairs)), str(len(docx))] if grade["pages_verified"] else ["not measured"] * 2
    return ["yes" if grade[field] else "no" for field in
            ("correct", "evidence_cited", "wrong_part_error")] + costs + ["SCORED", grade.get("table_note", grade["reason"])]


def score():
    lines = ["# Evaluation results", "", "As of 2026-09-06; invented three-account pile; topics off.",
             "A = read everything; B = map then read; C = forms and graph only.", "",
             "Questions and grading key: [questions.csv](questions.csv).", "",
             "| Question | Mode | Correct | Evidence | Wrong part | Source pages | DOCX units | Status | Review |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    seen_agents, scored = set(), 0
    for question in questions():
        for mode in "ABC":
            result = score_run(question["id"], mode, seen_agents)
            scored += result[-2] == "SCORED"
            cells = [question["id"], mode] + result
            lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    lines += ["", f"{scored} of {len(questions()) * 3} runs scored from saved responses and reviewed transcripts.", ""]
    reading = WORK / "reading.md"
    provenance = WORK / "FIXTURE-PROVENANCE.md"
    if provenance.exists():
        lines += [provenance.read_text(encoding="utf-8").strip(), ""]
    lines += [reading.read_text(encoding="utf-8").strip() if reading.exists() else
              "No comparative conclusion is available until the fresh-agent runs are completed and reviewed.",
              "", "Source pages count distinct PDF/image pages read, including native text; DOCX text units are",
              "reported separately because Word pagination is not stable. Map/form access and the cost of building",
              "the map are not included, so the page proxy is not a complete token or runtime cost.", "",
              "Invented contracts are cleaner than a real pile; eleven readable files are indicative only.",
              "The comparison tests the map thesis; it does not assume B wins or C alone answers corpus questions.", ""]
    (EVAL / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {EVAL / 'RESULTS.md'}: {scored} scored runs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    p = sub.add_parser("prompt")
    p.add_argument("question_id")
    p.add_argument("mode", choices=list("ABC"))
    sub.add_parser("score")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare()
        elif args.command == "prompt":
            prompt(args.question_id, args.mode)
        else:
            score()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, f"STOP: {error}\n")


if __name__ == "__main__":
    main()
