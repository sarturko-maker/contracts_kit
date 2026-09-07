"""Check existing sort cards without changing them: python scripts/check_cards.py [--all | ids]

Two checks, the same ones kit_common.load_card prints while the reports are built:

- question 2 read the wrong way round (our entity in the other side's slot). Needs
  inputs/our-entities.csv; without that file the check is skipped and says so.
- an evidence quote longer than forty words (stage1/sort-card.md: a page or clause reference
  and the exact words, forty or fewer).

Nothing is edited and nothing fails: the exit code is always 0. A card that needs fixing is
re-read by /read, and the user decides. With no arguments every card is checked.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import (  # noqa: E402
    OUR_ENTITIES_CSV, WORK_CARDS, card_warnings, load_card, our_names_for_checks, rel, say, warn,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warn about reversed question 2 and over-long evidence.")
    parser.add_argument("ids", nargs="*", help="document numbers, e.g. 003 017 (default: every card)")
    parser.add_argument("--all", action="store_true", help="every card in work/cards (the default)")
    args = parser.parse_args(argv)

    our_names = our_names_for_checks()
    if not our_names:
        say(f"{rel(OUR_ENTITIES_CSV)} is not there, so question 2 is not checked; "
            "only the evidence length is.")

    if args.ids and not args.all:
        doc_ids = [i.strip().zfill(3) if i.strip().isdigit() else i.strip() for i in args.ids]
    else:
        doc_ids = sorted(p.stem for p in WORK_CARDS.glob("*.json")) if WORK_CARDS.exists() else []

    if not doc_ids:
        say(f"no cards in {rel(WORK_CARDS)}; run /read first.")
        return 0

    checked, messages = 0, []
    for doc_id in doc_ids:
        card = load_card(doc_id, quiet=True)
        if card is None:
            say(f"doc {doc_id}: no card in {rel(WORK_CARDS)}")
            continue
        checked += 1
        messages.extend(card_warnings(card, our_names))
    for message in messages:
        warn(message)
    say(f"{checked} cards checked; {len(messages)} warnings. Nothing was changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
