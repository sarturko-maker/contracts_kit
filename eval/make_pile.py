#!/usr/bin/env python3
"""Build the separate invented evaluation pile; requires build-time reportlab and Pillow."""
import csv
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sample_generator", HERE.parent / "sample" / "make_pile.py")
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)
ACCOUNT = "Quenby Marine Services"
OUR = sample.OURS
OLD = [("2018 Marine Supply Master", [
    f"1. Parties: {ACCOUNT} (Customer) and {OUR} (Supplier).",
    "2. This agreement starts on 1 January 2018 and continues until twelve months' written notice.",
    "3. All marine equipment purchases between the signatories in the United Kingdom fall under this agreement.",
    "4. Payment is due within 45 days of invoice. Freight is included in the price.",
    "5. This agreement is on the Supplier's paper and makes no exclusivity commitment.",
    f"Signed for {ACCOUNT}: E. Vale. Date: 1 January 2018.",
    f"Signed for {OUR}: A. Wren. Date: 1 January 2018.",
])]
CURRENT = [
    ("2024 Marine Supply Agreement - General Terms", [
        f"1. Parties: {ACCOUNT} (Customer) and {OUR} (Supplier).",
        "2. Effective 1 January 2024, this agreement supersedes the 2018 Marine Supply Master in its entirety.",
        "3. These General Terms continue until either party gives six months' written notice.",
        "4. All marine equipment purchases between the signatories in the United Kingdom are placed under these General Terms.",
        "5. Payment is due within 21 days of invoice.",
        "6. Freight is charged at reasonable delivery expense, capped at GBP 250 per consignment.",
        "7. The Customer appoints the Supplier as sole supplier for all its marine equipment purchases for the life of these General Terms.",
        "8. This is the Customer's paper. There are no affiliate signatories or adoption instruments.",
        "9. Schedule A prevails over these General Terms only during its stated term and for the products it names.",
    ]),
    ("Schedule A - 2024 Pump Programme", [
        "A1. This Schedule forms part of the 2024 Marine Supply Agreement and applies only to pump purchases.",
        "A2. This Schedule runs from 1 January 2024 to 31 December 2024 and expires without renewal.",
        "A3. During this Schedule's term, payment for pumps is due within 10 days of invoice.",
        "A4. During this Schedule's term, freight for pumps is included in the price.",
        "A5. After this Schedule expires, the General Terms alone apply to pump purchases.",
        "A6. Territory and entities covered are those in the General Terms.",
        f"Signed for {ACCOUNT}: E. Vale. Date: 1 January 2024.",
        f"Signed for {OUR}: A. Wren. Date: 1 January 2024.",
    ]),
    ("Confirmation of Continuing Use - 1 September 2026", [
        "C1. This confirmation forms part of the General Terms of the 2024 Marine Supply Agreement.",
        "C2. The parties confirm that all current marine equipment purchases remain under those General Terms and no notice has been served.",
        "C3. Schedule A expired on 31 December 2024. No term is amended or renewed by this confirmation.",
        f"Signed for {ACCOUNT}: E. Vale. Date: 1 September 2026.",
        f"Signed for {OUR}: A. Wren. Date: 1 September 2026.",
    ]),
]


def main():
    pile = HERE / "pile"
    sample.make_pile(pile)
    sample.native_pdf(pile / "11 Old Marine Master.pdf", OLD, signed_pages={1: 2})
    sample.native_pdf(pile / "12 Marine Supply Agreement.pdf", CURRENT, signed_pages={2: 2, 3: 2})
    with (pile / "ERP_record.csv").open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(["INV-300", ACCOUNT, "United Kingdom"])
    print(f"Added two invented Quenby contracts: {pile}")


if __name__ == "__main__":
    main()
