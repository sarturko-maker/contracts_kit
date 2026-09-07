#!/usr/bin/env python3
"""Build the sample oracle in an isolated kit, using invented facts fixed at 2026-09-06.

This is a development fixture generator, not a contract reader or a replacement for /read.
Cards and form answers below are the explicit oracle. Notes and reports are script-generated.
"""
from pathlib import Path
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kit_common import CARD_KEYS, PLACEMENT_COLUMNS, ENTITY_MAP_COLUMNS, write_csv, write_json

# Kept free of build-only imports so fixture replay needs only enterprise dependencies.
OURS = "Marrowgate Supply Ltd"
ACCOUNT1 = "Tallowfield Industries"
NORTH = "Tallowfield Industries (North) Limited"
PARENT = "Oxbrook Holdings plc"
GERMAN = "Tallowfield Industrie GmbH"
ACCOUNT2 = "Pellmont Logistics Group"


def ev(ref, words):
    assert len(words.split()) <= 40, (ref, words)
    return {"ref": ref, "words": words}


def quoted(evidence):
    return f'{evidence["ref"]}: "{evidence["words"]}"' if evidence else "not found"


def card(doc_id, title, kind, entity, **answers):
    result = {key: "not found" for key in CARD_KEYS}
    result.update(doc_id=doc_id, q1_title=title, q1_kind=kind,
                  q2_their_signing_entities=entity + " (signatory)", q2_their_group_companies="none",
                  q2_our_entity=OURS, q3_signed="both", q4_ended_sign="none found", q4_status="unsure",
                  q5_parts="no", q5_parts_detail="none", q6_attaches_to="none", q6_replaces="none",
                  q6_referred_to_not_in_pile="none", q8_entities_covered="signatories only",
                  q9_copy_or_draft_of="none", q9_better_copy="this one", q10_oddities="none")
    result.update(answers)
    return result


def cards(omit_precedence=False):
    c = {}
    c["001"] = card("001", "Supply Agreement - General Terms", "master or framework", NORTH,
        q2_their_group_companies=f"{PARENT} (parent listed) | {GERMAN} (affiliate listed)",
        q2_evidence=quoted(ev("p.1 cl.1", f"Parties: {OURS} (Supplier) and {NORTH} (Customer).")) + " | " + quoted(ev("p.3 S1", f"{NORTH} trades as {ACCOUNT1} and is a subsidiary of {PARENT}.")) + " | " + quoted(ev("p.3 S2", f"Named affiliate: {GERMAN}, Germany, may order under the General Terms.")),
        q3_evidence=quoted(ev("p.4 (picture inspected)", f"Signed for {OURS}")) + " | " + quoted(ev("p.4 (picture inspected)", f"Signed for {NORTH}")),
        q4_start_date="2019-03-14", q4_start_basis="date of last signature", q4_end="rolling until notice (twelve months)", q4_status="live",
        q4_evidence=quoted(ev("p.1 cl.2", "This Agreement takes effect on the date of the last signature below.")) + " | " + quoted(ev("p.4 (picture inspected)", "14 March 2019")) + " | " + quoted(ev("p.1 cl.3", "General Terms continue until either party gives twelve months' written notice.")),
        q5_parts="yes", q5_parts_detail="General Terms: pp.1-1 and pp.3-4, live | Programme Terms - Hexley Refit: pp.2-2, dead (expired 2024-08-31)",
        q5_precedence="not found" if omit_precedence else quoted(ev("p.1 cl.9", "Programme Terms prevail over General Terms in case of conflict.")),
        q7_trade_scope="all purchases", q7_what_makes_it_govern="orders placed under it; all industrial supply purchases",
        q7_evidence=quoted(ev("p.1 cl.4", "All purchases of industrial supplies between the parties are placed under these General Terms.")),
        q8_entities_covered="named group companies", q8_countries="United Kingdom; Germany",
        q10_oddities='p.1 cl.5: "may charge the Customer the cost of freight" | p.2 P3: "freight shall be charged" | Our paper (p.1 cl.10); General Terms presumed rolling, subject to evidence of continuing use.')
    c["002"] = card("002", "Amendment 1 to Supply Agreement", "amendment or side letter", NORTH,
        q2_evidence=quoted(ev("p.1 cl.1", f"Parties: {OURS} and {NORTH}.")),
        q3_evidence=quoted(ev("p.1 signature blocks (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 1 February 2026.")) + " | " + quoted(ev("p.1 signature blocks (picture inspected)", f"Signed for {NORTH}: B. Reed. Date: 1 February 2026.")),
        q4_start_date="2026-02-01", q4_start_basis="stated", q4_end="rolling until notice (six months; life of General Terms)", q4_status="live",
        q4_evidence=quoted(ev("p.1 cl.3", "Effective 1 February 2026, the notice period in clause 3 of the General Terms is six months.")) + " | " + quoted(ev("p.1 cl.5", "This amendment continues for the life of the General Terms.")),
        q6_attaches_to="Supply Agreement dated 14 March 2019 → doc 001", q6_evidence=quoted(ev("p.1 cl.2", "This amends the Supply Agreement dated 14 March 2019 between the parties.")),
        q7_trade_scope="all purchases", q7_what_makes_it_govern="amends governing General Terms; confirms all current purchases continue under them",
        q7_evidence=quoted(ev("p.1 cl.4", "The parties confirm that all their current purchases continue under the General Terms of that Agreement.")),
        q8_countries="not found")
    c["003"] = card("003", "Mutual Non-Disclosure Agreement", "NDA", PARENT,
        q2_evidence=quoted(ev("p.1 cl.1 (picture inspected)", f"Parties: {PARENT} and {OURS}.")),
        q3_evidence=quoted(ev("p.2 (picture inspected)", f"Signed for {PARENT}: C. Linn. Date: 1 May 2019.")) + " | " + quoted(ev("p.2 (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 1 May 2019.")),
        q4_start_date="2019-05-01", q4_start_basis="stated", q4_end="fixed: 2022-04-30", q4_ended_sign="expired 2022-04-30", q4_status="dead",
        q4_evidence=quoted(ev("p.1 cl.2 (picture inspected)", "This Agreement starts on 1 May 2019 and expires on 30 April 2022, a three-year term.")),
        q7_trade_scope="no", q7_what_makes_it_govern="confidentiality only; no surviving obligations",
        q7_evidence=quoted(ev("p.1 cl.5 (picture inspected)", "This Agreement does not govern orders, prices, purchases or the supply of goods.")),
        q10_oddities="Every page read from pictures. Oxbrook Holdings plc is linked to Tallowfield Industries only by doc 001 Schedule 1; this NDA itself gives no group link.")
    c["004"] = card("004", "Master Services Agreement - draft dated 15 January 2026", "master or framework", ACCOUNT2,
        q2_evidence=quoted(ev("¶ 2", f"Parties: {ACCOUNT2} (Customer) and {OURS} (Supplier).")),
        q3_signed="nobody", q3_evidence=quoted(ev("¶ 8", f"Signed for {OURS}: __________________ Date: __________________")) + " | " + quoted(ev("¶ 9", f"Signed for {ACCOUNT2}: __________________ Date: __________________")),
        q4_evidence=quoted(ev("¶ 3", "This draft is not agreed.")), q7_trade_scope="all purchases",
        q7_what_makes_it_govern="proposes all service orders under its terms; draft text not authenticated by detached signature page",
        q7_evidence=quoted(ev("¶ 3", "It proposes that all service orders between the parties use these terms.")), q8_countries="United Kingdom",
        q9_copy_or_draft_of="doc 007 (related signature page; final text not established)", q9_better_copy="n/a",
        q10_oddities="Tracked changes present (2); two comments; author Fictional MSA Drafter, created 2026-01-14T09:00:00Z, modified 2026-01-15T11:00:00Z. | No signature image in DOCX; blank blocks. | draft; signed signature page found separately (doc 007); complete signed text not found.")
    c["005"] = card("005", "Purchase Order PL-2026-042", "purchase order or quote", ACCOUNT2,
        q2_evidence=quoted(ev("p.1", f"Buyer: {ACCOUNT2}. Seller: {OURS}.")), q3_signed="nobody",
        q3_evidence=quoted(ev("p.1 (picture inspected)", "No signature is required for this purchase order.")),
        q4_start_date="2026-04-06", q4_start_basis="stated", q4_evidence=quoted(ev("p.1", "Order date: 6 April 2026. Deliver by 13 April 2026.")),
        q7_trade_scope="no", q7_what_makes_it_govern="one purchase only; no standard terms or continuing trade terms",
        q7_evidence=quoted(ev("p.1", "This purchase order contains no standard terms and establishes no terms for other purchases.")), q8_countries="United Kingdom",
        q10_oddities="Delivery due date is not treated as contractual expiry; performance not found.")
    c["006"] = card("006", "2026 Rebate Letter", "pricing or rebate letter", ACCOUNT2,
        q2_their_signing_entities=f"{ACCOUNT2} (addressee)", q2_evidence=quoted(ev("p.1", f"To: {ACCOUNT2}. From: {OURS}.")),
        q3_signed="us only", q3_evidence=quoted(ev("p.1 (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 1 January 2026.")),
        q4_start_date="2026-01-01", q4_start_basis="stated", q4_end="fixed: 2026-12-31", q4_status="live",
        q4_evidence=quoted(ev("p.1 cl.1", "From 1 January 2026 until 31 December 2026, we will credit 2% of your invoiced purchases of logistics support.")),
        q7_trade_scope="period", q7_what_makes_it_govern="sets rebate for 2026 only; general trading terms must be agreed separately",
        q7_evidence=quoted(ev("p.1 cl.2", "This letter sets only the rebate for that period. Other trading terms must be agreed separately.")),
        q10_oddities='p.1 cl.3: "This is our commitment and requires no customer countersignature."')
    c["007"] = card("007", "Master Services Agreement - Signature Page", "other", ACCOUNT2,
        q2_evidence=quoted(ev("image p.1 (picture inspected)", f"Signed for {ACCOUNT2}: D. Moor. Date: 16 January 2026.")) + " | " + quoted(ev("image p.1 (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 16 January 2026.")),
        q3_evidence=quoted(ev("image p.1 (picture inspected)", f"Signed for {ACCOUNT2}: D. Moor. Date: 16 January 2026.")) + " | " + quoted(ev("image p.1 (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 16 January 2026.")),
        q4_evidence=quoted(ev("image p.1 (picture inspected)", "Date: 16 January 2026.")),
        q6_attaches_to="Master Services Agreement dated 15 January 2026 → doc 004", q6_evidence=quoted(ev("image p.1 (picture inspected)", "Signature page for Master Services Agreement dated 15 January 2026.")),
        q7_trade_scope="can't tell", q7_what_makes_it_govern="signature evidence only; agreed text missing", q7_evidence="not found",
        q9_copy_or_draft_of="doc 004 (signature page of)", q9_better_copy="n/a",
        q10_oddities='The two signatures are visible; dates are 16 January 2026. | image p.1: "The text pages of the execution version are not attached to this page." | Links by title/date to doc 004 but does not establish that draft is the executed text.')
    c["008"] = card("008", "Hexley Works Site Agreement", "project or programme agreement", NORTH,
        q2_evidence=quoted(ev("p.1 cl.1", f"Parties: {NORTH} (Customer) and {OURS} (Supplier).")),
        q3_evidence=quoted(ev("p.1 (picture inspected)", f"Signed for {NORTH}: B. Reed. Date: 1 March 2026.")) + " | " + quoted(ev("p.1 (picture inspected)", f"Signed for {OURS}: A. Wren. Date: 1 March 2026.")),
        q4_start_date="2026-03-01", q4_start_basis="stated", q4_end="fixed: 2027-03-31", q4_status="live",
        q4_evidence=quoted(ev("p.1 cl.3", "Effective 1 March 2026. Expires 31 March 2027 unless ended earlier on 30 days' written notice.")),
        q6_evidence=quoted(ev("p.1 cl.5", "Orders outside Hexley Works continue under the Supply Agreement dated 14 March 2019.")),
        q7_trade_scope="project, site or programme", q7_what_makes_it_govern="orders placed under it; Hexley Works site only; outside-site trade under doc 001",
        q7_evidence=quoted(ev("p.1 cl.4", "All industrial supply orders for Hexley Works site in the United Kingdom are placed under this agreement.")), q8_countries="United Kingdom",
        q10_oddities="On their paper (cl.2). Cross-reference to doc 001 defines outside-site trade; this is a separate site tree. | Hexley Works site is distinct from the expired Hexley Refit programme.")
    c["009"] = card("009", f"Internal Account Playbook - {ACCOUNT1}", "internal playbook or guidance", ACCOUNT1,
        q2_their_signing_entities=f"{ACCOUNT1} (internal account subject)",
        q2_evidence=quoted(ev("¶ 2", f"INTERNAL ONLY. Account: {ACCOUNT1}. Maintained by {OURS}; no customer signature.")),
        q3_signed="nobody", q3_evidence=quoted(ev("¶ 2", "no customer signature.")),
        q4_start_date="2026-02-01", q4_start_basis="stated", q4_end="until replaced (internal guidance)", q4_status="live",
        q4_evidence=quoted(ev("¶ 3", "Working guidance from 1 February 2026 until replaced. This is not a contract.")),
        q7_trade_scope="no", q7_what_makes_it_govern="internal business practice, not a contract",
        q7_evidence=quoted(ev("¶ 3", "This is not a contract.")), q8_entities_covered="not found", q8_countries="United Kingdom",
        q10_oddities="Margin practice: seek 18% gross margin; internal market basket with quarterly purchase cost reviews; urgent low-volume deliveries ad hoc. | Tracked changes (2), one comment, author Fictional Account Manager; created 2026-01-14T09:00:00Z, modified 2026-01-15T11:00:00Z. | Practice is not a customer agreement about freight (¶ 7).")
    return c


def placement(doc_id, tree, folder, reason, **kw):
    row = {k: "" for k in PLACEMENT_COLUMNS}
    row.update(doc_id=doc_id, tree=tree, folder=folder, reason=reason, **kw)
    return row


def placements(omit_precedence=False):
    overlap = ('unresolved: precedence not found; General Terms "may charge the Customer the cost of freight"; Programme Terms "freight shall be charged". Programme expired 2024-08-31.' if omit_precedence else 'General Terms "may charge the Customer the cost of freight"; Programme Terms "freight shall be charged". Programme Terms prevail on paper (p.1 cl.9) but are dead (expired 2024-08-31).')
    return {
        ACCOUNT1: [
            placement("001", "T1", "1-governs-trade", "General Terms govern all purchases, as amended by doc 002; current trade confirmed there.", parts_status="General Terms: live | Programme Terms - Hexley Refit: dead", overlap=overlap),
            placement("002", "T1", "1-governs-trade", "Amends General Terms: six months' notice; takes the status of doc 001.", attaches_to="001", attach_kind="amends"),
            placement("003", "T3", "4-not-live", "NDA expired 2022-04-30; no renewal or surviving obligation."),
            placement("008", "T2", "2-governs-part-of-trade", "Live separate agreement for Hexley Works site; other purchases use doc 001.", limit="Hexley Works site in the United Kingdom"),
            placement("009", "T4", "6-business-practice", "Internal margin, market basket and ad hoc delivery guidance; not a contract."),
        ],
        ACCOUNT2: [
            placement("004", "T1", "unsure", "draft; signed signature page found separately (doc 007)", question="Provide the complete execution version matching doc 007.", what_would_change="Signed body matching the detached page would establish the governing text."),
            placement("005", "T3", "5-orders-drafts-duplicates", "Single purchase with no standard terms."),
            placement("006", "T2", "2-governs-part-of-trade", "Current year rebate only; no general trading terms.", limit="1 January to 31 December 2026 rebate"),
            placement("007", "T1", "unsure", "Signed signature page of doc 004; final body absent.", attaches_to="004", attach_kind="signature page of", question="Confirm which complete text the parties signed."),
        ],
    }


def prose(omit_precedence=False):
    overlap = placements(omit_precedence)[ACCOUNT1][0]["overlap"]
    return {
        ACCOUNT1: f"""## The position
Doc 001's General Terms govern all industrial supply purchases from 14 March 2019: our paper, signed by Marrowgate Supply Ltd and Tallowfield Industries (North) Limited, covering the UK and named German affiliate. Doc 002 confirms continuing trade and changes the rolling notice period to six months.
The Hexley Refit Programme Terms expired on 31 August 2024. Doc 008 governs the separate Hexley Works site through 31 March 2027, on their paper and signed by both.
Doc 003's NDA expired on 30 April 2022. Doc 009 is the internal practice guide.

## Overlaps and conflicts
{overlap}

## Couldn't find or couldn't tell
No complete execution version issues found for this account. No evidence that the expired programme was extended.

## Questions for the business
1. Confirm that sales uses doc 001 as amended and doc 008 for Hexley Works.
2. Confirm that the internal margin and ad hoc practice in doc 009 still describes trading.
""",
        ACCOUNT2: """## The position
Nothing establishes the general terms governing trade. Doc 004 is a draft; signed signature page found separately (doc 007), but the agreed body is absent. Doc 006 sets a current 2026 rebate only; it does not supply general trading terms. Doc 005 is a single purchase order with no standard terms.

## Overlaps and conflicts
No competing live general terms can be established. Doc 007 proves signatures but does not authenticate the draft text in doc 004.

## Couldn't find or couldn't tell
The complete execution version of the Master Services Agreement linked to doc 007 is missing.

## Questions for the business
1. Provide the complete signed agreement matching doc 007 and confirm the terms currently used for orders.
2. Confirm whether there is anything beyond the 2026 rebate letter (doc 006).
""",
    }


def entity_rows():
    data = [
        (ACCOUNT1, ACCOUNT1, "same name", "sure", "ERP row; also the account named in doc 009."),
        (NORTH, ACCOUNT1, "in the document", "sure", "doc 001 p.3 S1 says the signatory trades as Tallowfield Industries."),
        (PARENT, ACCOUNT1, "in the document", "sure", "doc 001 p.3 S1 names Oxbrook Holdings plc as parent of the signing company, which trades as the ERP account."),
        (GERMAN, ACCOUNT1, "in the document", "sure", "doc 001 p.3 S2 names Tallowfield Industrie GmbH as the affiliate ordering under the General Terms."),
        (ACCOUNT2, ACCOUNT2, "same name", "sure", "Exact ERP customer account name."),
        (ACCOUNT1 + " Data Centres", ACCOUNT1, "same name", "fairly sure", "ERP stream row; treated as one with the main account because no sample document names the stream."),
    ]
    return [dict(zip(ENTITY_MAP_COLUMNS, [name, account, basis, confidence, "claude", note])) for name, account, basis, confidence, note in data]


def tree_proposals():
    def tree(number, family, confidence, ids, evidence, overlays=None):
        return {"tree": number, "family": family, "confidence": confidence,
                "doc_ids": ids, "structural_evidence": evidence, "overlays": overlays or []}
    return {
        ACCOUNT1: {"account": ACCOUNT1, "trees": [
            tree("T1", "C1", "not_sure", ["001", "002"], "Doc 001 master has two components linked forms_part_of and doc 002 linked amends. Schedule 1 says the German affiliate 'may order under the General Terms' (p.3 S2): DCG C1 treats this as deemed participation. The fixed form has no explicit per-entity deemed participation instrument and the export lacks participation nodes; proposal requires review, not invented nodes."),
            tree("T2", "C2", "fairly_sure", ["008"], "Standalone customer-paper site supply master with orders under it and no participation or versioned commercial layer. Scope is Hexley Works, not a general services SOW; closest C2 structure with a narrower site limit."),
            tree("T3", "C0", "no_family_fits", ["003"], "Standalone expired confidentiality master: no trade-governing family; O3 identifies its NDA overlay role.", ["O3"]),
            tree("T4", "C0", "no_family_fits", ["009"], "Internal practice evidence has no contract-family structure; no DCG internal_playbook node type."),
        ]},
        ACCOUNT2: {"account": ACCOUNT2, "trees": [
            tree("T1", "C0", "not_sure", ["004", "007"], "Unsigned proposed master with separate signature evidence linked by title/date. The execution body is missing; an agreed governing structure cannot be established."),
            tree("T2", "C13", "sure", ["006"], "Standalone annual rebate change instrument, limited to 2026; references no governing master. This is the time-limited commercial-letter structure in C13."),
            tree("T3", "C4", "fairly_sure", ["005"], "Single order with no negotiated master or standard terms in the order. C4's no-anchor transaction structure is the nearest family; no battle-of-forms outcome is asserted."),
        ]},
    }


def write_cards(folder, answers):
    for doc_id, values in answers.items():
        write_json(folder / f"{doc_id}.json", values)
        lines = [f"# Sort card — doc {doc_id}", ""]
        for number in range(1, 11):
            lines += [f"## {number}", ""]
            for key in CARD_KEYS:
                if key.startswith(f"q{number}_"):
                    lines.append(f"- **{key}:** {values[key]}")
            lines.append("")
        (folder / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")


def populate_oracle(target, omit_precedence=False):
    target = Path(target)
    write_cards(target / "cards", cards(omit_precedence))
    for account, rows in placements(omit_precedence).items():
        write_csv(target / "placements" / f"{account}.csv", rows, PLACEMENT_COLUMNS)
        (target / "placements" / f"{account}.md").write_text(prose(omit_precedence)[account], encoding="utf-8")
    write_csv(target / "entity-map.csv", entity_rows(), ENTITY_MAP_COLUMNS)
    write_csv(target / "our-entities.csv", [{"name": OURS}], ["name"])
    for account, data in tree_proposals().items():
        write_json(target / "trees" / f"{account}.json", data)


def isolated_kit(destination):
    destination = Path(destination)
    for folder in ("scripts", "stage1", "stage2", "dcg", "assets"):
        shutil.copytree(ROOT / folder, destination / folder)
    (destination / "inputs").mkdir()
    return destination


def replay(target, oracle=HERE / "expected", pile=HERE / "pile"):
    """Run deterministic stage1 using the explicit oracle, into an isolated copied kit."""
    target = Path(target)
    run = lambda *args: subprocess.run([sys.executable, *args], cwd=target, text=True, capture_output=True, check=True)
    logs = [run("scripts/prepare.py", str(Path(pile).resolve()), "--account-column", "customer_account", "--side", "customers").stdout]
    shutil.copytree(Path(oracle) / "cards", target / "work" / "cards", dirs_exist_ok=True)
    shutil.copytree(Path(oracle) / "placements", target / "work" / "placements", dirs_exist_ok=True)
    for name in ("entity-map.csv", "our-entities.csv"):
        shutil.copyfile(Path(oracle) / name, target / "inputs" / name)
    logs += [run("scripts/sort.py").stdout, run("scripts/place.py", "--all").stdout]
    return "\n".join(logs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "expected")
    args = parser.parse_args()
    populate_oracle(args.output)
    with tempfile.TemporaryDirectory(prefix="dcg-sample-") as temp:
        kit = isolated_kit(temp)
        log = replay(kit, args.output)
        for account in (ACCOUNT1, ACCOUNT2):
            account_out = kit / "out" / "customers" / account
            dest = args.output / "notes" / account
            dest.mkdir(parents=True, exist_ok=True)
            for name in ("README.md", "position.mmd"):
                shutil.copyfile(account_out / name, dest / name)
        # Forms use relative fixture source paths to keep this oracle portable.
        from make_forms import build_forms
        build_forms(kit, args.output / "forms")
        shutil.copytree(args.output / "forms", kit / "work" / "forms")
        shutil.copytree(args.output / "trees", kit / "work" / "trees")
        stage2 = []
        for script in ("validate_forms.py", "graph.py"):
            check = subprocess.run([sys.executable, f"scripts/{script}", "--all"], cwd=kit, capture_output=True, text=True)
            stage2.append(check.stdout + check.stderr)
            if check.returncode:
                raise RuntimeError(stage2[-1])
        for account in (ACCOUNT1, ACCOUNT2):
            shutil.copyfile(kit / "out" / "customers" / account / "TREES.md", args.output / "notes" / account / "TREES.md")
        (args.output / "stage2-replay.txt").write_text("\n".join(stage2), encoding="utf-8")
        portable_log = log.replace(str(HERE / "pile"), "sample/pile")
        (args.output / "stage1-replay.txt").write_text(
            "\n".join(line.rstrip() for line in portable_log.splitlines()) + "\n", encoding="utf-8")
    print(f"Generated nine cards, placements, notes and forms under {args.output}")


if __name__ == "__main__":
    main()
