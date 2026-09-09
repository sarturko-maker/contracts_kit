"""Score a light filing (out/sort/<side>/CORPUS.csv) against the messy pile's key.

Evaluator use only: never run this inside a kit that a runner is working in.
Usage: python eval/messy/score_light.py <kit root> [--key eval/messy/expected/key.json]
"""
import argparse
import csv
import json
import re
from pathlib import Path

FOLDERS = ["1-governs-trade", "2-governs-part-of-trade", "3-live-not-trade", "4-not-live",
           "5-orders-drafts-duplicates", "6-business-practice", "unsure"]

# The key predates the September 2026 rule decisions: rebate, pricing and notice letters do not
# govern trade (folder 3), and a schedule that forms part of the master follows the master.
REVISED = {"rebate 2026.pdf": "3-live-not-trade", "IMG_2291.jpg": "3-live-not-trade",
           "notice served 14-08-26.pdf": "3-live-not-trade",
           "Schedule 2 price matrix 2026.xlsx": "1-governs-trade"}


def expected_folders(text):
    """Folders the key accepts, from its free-text status_folder field."""
    text = text or ""
    found = [f for f in FOLDERS if f in text]
    if "holding folder" in text or text.startswith("_") or "_unreadable" in text or "_needs-reading" in text:
        found.append("holding")
    if not found and text != "n/a":
        found.append("holding" if "holding" in text else "?")
    return found


def expected_accounts(text, erp_names):
    text = text or ""
    found = [a for a in erp_names if a in text]
    if "_not-on-the-list" in text or "_not-sure" in text or text.startswith("unresolved") or "holding" in text:
        found.append("holding")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kit")
    parser.add_argument("--key", default=str(Path(__file__).resolve().parent / "expected" / "key.json"))
    parser.add_argument("--side", default="customers")
    args = parser.parse_args()
    key = json.loads(Path(args.key).read_text())
    erp_names = [r["customer_account"] for r in key["erp_rows"]]
    corpus = list(csv.DictReader((Path(args.kit) / "out" / "sort" / args.side / "CORPUS.csv").open(encoding="utf-8")))
    by_sha = {}
    for row in corpus:
        by_sha.setdefault(row["sha256"], []).append(row)
    right = wrong = 0
    print(f"{'doc':4} {'file':46} {'expected':34} {'got':44} ok")
    for entry in key["documents"]:
        if entry["kind"] == "erp_record":
            continue
        rows = by_sha.get(entry["sha256"], [])
        want_f = expected_folders(entry["status_folder"])
        revised = REVISED.get(Path(entry["path"]).name)
        if revised:
            want_f.append(revised)
        want_a = expected_accounts(entry["account"], erp_names)
        got = [(r["account"], (r["folder"].replace(" (provisional)", "") or "holding")) for r in rows]
        ok = False
        for account, folder in got:
            acc_ok = (account in want_a) or (account.startswith("_") and "holding" in want_a) or not want_a
            fol_ok = (folder in want_f) or (folder == "_unreadable" and "holding" in want_f) or ("holding" in want_f and account.startswith("_"))
            if acc_ok and fol_ok:
                ok = "ok (revised rule)" if revised and folder == revised and revised not in expected_folders(entry["status_folder"]) else "ok"
        right += bool(ok)
        wrong += not ok
        name = Path(entry["path"]).name[:46]
        print(f"{rows[0]['doc_id'] if rows else '---':4} {name:46} {(', '.join(want_f) + ' @ ' + (want_a[0] if want_a else 'any'))[:34]:34} "
              f"{'; '.join(f'{a[:22]}/{f}' for a, f in got)[:44]:44} {ok or 'MISS'}")
    print(f"\n{right} documents in an accepted folder and account, {wrong} not, of {right + wrong}.")


if __name__ == "__main__":
    main()
