"""Token report per stage, from the ledger the stage skills append to.

    python scripts/cost.py                          # every stage in the ledger
    python scripts/cost.py --stage sort
    python scripts/cost.py --stage analyse --extrapolate 200
    python scripts/cost.py --ledger work/logs/cost.csv --stage deep-dive
    python scripts/cost.py --append --stage sort --role filer --model haiku \\
        --target 017 --attempt 1 --outcome ok --tokens 9800 --duration-ms 41000 --units-read 3

One ledger row per spawned agent:
`stage,role,model,target,attempt,outcome,tokens,duration_ms,units_read`. `units_read` is
pages (or Word paragraphs) read and may be blank or `unknown`; `tokens` may be `unknown`
too, and is then counted as zero and reported as unknown. The report is a plain Markdown
table: no currency anywhere, so the user applies their own rates.

Main session tokens never reach this script; the closing line says so.
"""

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import WORK, fail, read_csv, rel, say, warn  # noqa: E402

LEDGER_COLUMNS = [
    "stage", "role", "model", "target", "attempt", "outcome",
    "tokens", "duration_ms", "units_read",
]
DEFAULT_LEDGER = WORK / "logs" / "cost.csv"

# One agent per document; these scale with the size of the pile.
DOCUMENT_ROLES = ("filer", "reader", "extractor")
# One agent per ERP account; the account count is the user's, not ours to guess.
ACCOUNT_ROLES = ("judge", "mapper")

KNOWN_STAGES = ["sort", "analyse", "deep-dive"]
OK = "ok"
UNKNOWN_VALUES = {"", "unknown", "n/a", "na", "-", "—", "none", "not found"}
DASH = "—"

CLOSING_LINE = (
    "Main session tokens are not visible to the model; type /cost for this session's own "
    "usage and add it to the stage total."
)


# --------------------------------------------------------------------------- small helpers
def as_int(value):
    """A ledger number, or None when the row says it is unknown."""
    text = str(value or "").strip().replace(",", "").replace("_", "")
    if text.lower() in UNKNOWN_VALUES:
        return None
    try:
        number = int(float(text))
    except ValueError:
        return None
    return number if number >= 0 else None


def rounded(value):
    """Nearest whole number, half up, so the arithmetic is predictable."""
    return int(value + 0.5)


def clock(milliseconds):
    """Wall clock as the user reads it: 42.5s, 36m 12s, 1h 04m."""
    if milliseconds <= 0:
        return "0s"
    seconds = milliseconds / 1000.0
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, seconds = divmod(int(seconds + 0.5), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m {seconds:02d}s"


def ratio(top, bottom, blank=DASH):
    """top/bottom rounded, or a dash when there is nothing to divide by."""
    if not bottom:
        return blank
    return str(rounded(top / bottom))


def role_basis(role):
    """How this role scales: per document, per account, or not classified."""
    name = (role or "").strip().lower()
    if name in DOCUMENT_ROLES:
        return "per document"
    if name in ACCOUNT_ROLES:
        return "per account"
    return "not classified"


# --------------------------------------------------------------------------- ledger
def append_row(stage, role, model, target, attempt, outcome, tokens, duration_ms,
               units_read, ledger=None):
    """Create the ledger with its header if missing and append exactly one row."""
    path = Path(ledger) if ledger else DEFAULT_LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists() or path.stat().st_size == 0
    row = {
        "stage": stage, "role": role, "model": model, "target": target,
        "attempt": attempt, "outcome": outcome, "tokens": tokens,
        "duration_ms": duration_ms, "units_read": units_read,
    }
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS, extrasaction="ignore")
        if fresh:
            writer.writeheader()
        writer.writerow({c: "" if row.get(c) is None else str(row.get(c, "")) for c in LEDGER_COLUMNS})
    return path


def load_ledger(path):
    """Ledger rows, in file order. A missing file is not an error: the stage may not have run."""
    path = Path(path)
    if not path.exists():
        return None
    rows = read_csv(path, required_columns=LEDGER_COLUMNS)
    return [row for row in rows if any((row.get(c) or "").strip() for c in LEDGER_COLUMNS)]


# --------------------------------------------------------------------------- summing
def summarise(rows):
    """Counts and totals for one group of ledger rows."""
    total = {
        "agents": len(rows), "retries": 0, "failures": 0, "tokens": 0, "unknown_tokens": 0,
        "targets": set(), "models": [], "duration_ms": 0, "unit_tokens": 0, "units": 0,
    }
    for row in rows:
        attempt = as_int(row.get("attempt"))
        if attempt is not None and attempt > 1:
            total["retries"] += 1
        if (row.get("outcome") or "").strip().lower() != OK:
            total["failures"] += 1
        tokens = as_int(row.get("tokens"))
        if tokens is None:
            total["unknown_tokens"] += 1
        else:
            total["tokens"] += tokens
        target = (row.get("target") or "").strip()
        if target:
            total["targets"].add(target)
        model = (row.get("model") or "").strip()
        if model and model not in total["models"]:
            total["models"].append(model)
        duration = as_int(row.get("duration_ms"))
        if duration is not None:
            total["duration_ms"] += duration
        units = as_int(row.get("units_read"))
        if units is not None and units > 0 and tokens is not None:
            total["unit_tokens"] += tokens
            total["units"] += units
    return total


def tokens_cell(total):
    """Total tokens, saying plainly how many rows did not report a count."""
    if total["unknown_tokens"]:
        return f"{total['tokens']} ({total['unknown_tokens']} unknown)"
    return str(total["tokens"])


def per_target(total):
    return ratio(total["tokens"], len(total["targets"]))


def per_unit(total):
    return ratio(total["unit_tokens"], total["units"])


def group_by(rows, column):
    """Rows grouped by one column, in order of first appearance."""
    groups = {}
    for row in rows:
        groups.setdefault((row.get(column) or "").strip(), []).append(row)
    return groups


def stage_order(rows):
    present = list(group_by(rows, "stage"))
    known = [s for s in KNOWN_STAGES if s in present]
    return known + [s for s in present if s not in known]


# --------------------------------------------------------------------------- printing
def table(header, body):
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(cells) + " |" for cells in body]
    return lines


def stage_table(stage, rows):
    """The per-role table and the stage total line."""
    lines = [f"### {stage or '(no stage)'}", ""]
    body = []
    for role, role_rows in group_by(rows, "role").items():
        total = summarise(role_rows)
        body.append([
            role or "(no role)", " + ".join(total["models"]) or DASH, str(total["agents"]),
            str(total["retries"]), str(total["failures"]), tokens_cell(total),
            per_target(total), per_unit(total), clock(total["duration_ms"]),
        ])
    stage_total = summarise(rows)
    body.append([
        "**total**", "", f"**{stage_total['agents']}**", f"**{stage_total['retries']}**",
        f"**{stage_total['failures']}**", f"**{tokens_cell(stage_total)}**",
        f"**{per_target(stage_total)}**", f"**{per_unit(stage_total)}**",
        f"**{clock(stage_total['duration_ms'])}**",
    ])
    lines += table(["role", "model", "agents", "retries", "failures", "tokens",
                    "tokens/target", "tokens/unit read", "wall clock"], body)
    lines.append("")
    lines.append(f"{len(stage_total['targets'])} distinct targets; retries are attempt > 1 and "
                 f"failures are any outcome other than {OK}.")
    return lines


def extrapolation_table(stage, rows, targets_wanted):
    """Scale the per-document roles to N documents; leave the per-account roles alone."""
    lines = ["", f"#### Extrapolated to {targets_wanted} documents", ""]
    body = []
    projected_total = 0
    scaled_any = False
    account_any = False
    for role, role_rows in group_by(rows, "role").items():
        total = summarise(role_rows)
        count = len(total["targets"])
        basis = role_basis(role)
        attempts = f"{total['agents'] / count:.2f}" if count else DASH
        observed = per_target(total)
        if basis == "per document" and count:
            projected = rounded(total["tokens"] / count * targets_wanted)
            projected_total += projected
            scaled_any = True
            projection = str(projected)
        elif basis == "per account":
            account_any = True
            projection = "per account × your account count"
        else:
            projection = "not scaled"
        body.append([role or "(no role)", basis, observed, attempts, projection, per_unit(total)])
    if scaled_any:
        body.append(["**document roles**", "", "", "", f"**{projected_total}**", ""])
    lines += table(["role", "basis", "observed per target", "attempts per target",
                    f"projected for {targets_wanted}", "tokens/unit read"], body)
    lines.append("")
    lines.append(f"Document roles ({', '.join(DOCUMENT_ROLES)}) are scaled to {targets_wanted} "
                 "documents; the observed per-target figure already carries the observed retry "
                 "rate, because every attempt's tokens are divided by the distinct targets.")
    if account_any:
        lines.append(f"Per-account roles ({', '.join(ACCOUNT_ROLES)}) are not scaled: the number "
                     "of accounts is your input, so multiply the per-account figure by the "
                     "accounts you expect.")
    lines.append("Scaling by pages instead: multiply the tokens/unit read figure by the pages "
                 "(or Word paragraphs) you expect to read, when the new pile's documents are "
                 "longer or shorter than these.")
    return lines


def report(rows, stage_wanted, targets_wanted):
    """Print the whole report. Returns the number of stages shown."""
    stages = stage_order(rows)
    wanted = stages if stage_wanted in (None, "all") else [s for s in stages if s == stage_wanted]
    if not wanted:
        warn(f"no rows for stage {stage_wanted!r}; the ledger has: " + ("; ".join(stages) or "nothing"))
        return 0
    by_stage = group_by(rows, "stage")
    lines = []
    for stage in wanted:
        if lines:
            lines.append("")
        lines += stage_table(stage, by_stage[stage])
        if targets_wanted:
            lines += extrapolation_table(stage, by_stage[stage], targets_wanted)
    for line in lines:
        say(line)
    return len(wanted)


# --------------------------------------------------------------------------- cli
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", help="sort | analyse | deep-dive | all (default all); "
                                        "with --append, the stage of the row")
    parser.add_argument("--extrapolate", type=int, metavar="N",
                        help="scale the per-document roles to N documents")
    parser.add_argument("--ledger", help=f"ledger CSV (default {rel(DEFAULT_LEDGER)})")
    parser.add_argument("--append", action="store_true", help="append one row and stop")
    row = parser.add_argument_group("--append row")
    row.add_argument("--role")
    row.add_argument("--model", default="")
    row.add_argument("--target", default="")
    row.add_argument("--attempt", default="1")
    row.add_argument("--outcome", default=OK)
    row.add_argument("--tokens", default="unknown")
    row.add_argument("--duration-ms", dest="duration_ms", default="")
    row.add_argument("--units-read", dest="units_read", default="")
    args = parser.parse_args(argv)

    ledger = Path(args.ledger) if args.ledger else DEFAULT_LEDGER
    if args.append:
        if not args.stage or args.stage == "all" or not args.role:
            fail("--append needs --stage <stage> and --role <role>.")
        if args.extrapolate is not None:
            fail("--extrapolate reports; it cannot be combined with --append.")
        path = append_row(args.stage, args.role, args.model, args.target, args.attempt,
                          args.outcome, args.tokens, args.duration_ms, args.units_read, ledger)
        say(f"{rel(path)}: appended {args.stage}/{args.role} target {args.target or DASH} "
            f"attempt {args.attempt} {args.outcome}")
        return 0

    if args.extrapolate is not None and args.extrapolate <= 0:
        fail("--extrapolate needs a document count of 1 or more.")
    rows = load_ledger(ledger)
    if rows is None:
        say(f"No cost ledger at {rel(ledger)} yet; stages append one row per agent as they run.")
    elif not rows:
        say(f"{rel(ledger)} has no agent rows yet.")
    else:
        say(f"# Token report — {rel(ledger)}")
        say("")
        report(rows, args.stage, args.extrapolate)
        say("")
    say(CLOSING_LINE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
