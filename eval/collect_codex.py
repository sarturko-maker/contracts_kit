#!/usr/bin/env python3
"""Build helper: retain actual Codex tool records and final JSON, excluding reasoning."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def collect(agent_path, question, mode, sessions=None):
    sessions = sessions or Path.home() / ".codex" / "sessions"
    matches = []
    for path in sessions.rglob("*.jsonl"):
        try:
            with path.open(encoding="utf-8") as handle:
                meta = json.loads(next(handle))["payload"]
            if meta.get("agent_path") == agent_path:
                matches.append((path, meta))
        except (OSError, StopIteration, ValueError, KeyError):
            continue
    if len(matches) != 1:
        raise ValueError(f"Expected one actual rollout for {agent_path}, found {len(matches)}")
    path, meta = matches[0]
    transcript = [{"type": "agent_provenance", "payload": {k: meta.get(k) for k in
                   ("id", "agent_path", "timestamp", "history_mode", "subagent_history_start_ordinal")}}]
    final = None
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        value = record.get("payload", {})
        if record.get("type") == "response_item" and value.get("type") in (
                "function_call", "function_call_output", "custom_tool_call", "custom_tool_call_output"):
            transcript.append(record)
        if record.get("type") == "event_msg" and value.get("type") == "task_complete":
            final = value.get("last_agent_message")
    if not final:
        raise ValueError("No completed final response yet")
    runs = ROOT / "work" / "eval" / "runs"
    transcripts = ROOT / "work" / "eval" / "transcripts"
    runs.mkdir(parents=True, exist_ok=True)
    transcripts.mkdir(parents=True, exist_ok=True)
    stem = f"{question}-{mode}"
    raw = runs / f"{stem}.response.txt"
    raw.write_text(final, encoding="utf-8")
    transcript_path = transcripts / f"{stem}.jsonl"
    transcript_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in transcript) + "\n", encoding="utf-8")
    data = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", final.strip()))
    if data.get("question_id") != question or data.get("mode") != mode:
        raise ValueError("Completed response question/mode mismatch")
    (runs / f"{stem}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance = {"agent_id": meta["id"], "agent_path": agent_path,
                  "transcript": str(transcript_path.relative_to(ROOT)), "rollout": str(path)}
    (runs / f"{stem}.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Collected {stem}: final response and {len(transcript)-1} actual tool records; grading required.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent_path")
    parser.add_argument("question")
    parser.add_argument("mode", choices=list("ABC"))
    args = parser.parse_args()
    try:
        collect(args.agent_path, args.question, args.mode)
    except (ValueError, OSError) as error:
        parser.exit(1, f"STOP: {error}\n")
