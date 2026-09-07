#!/usr/bin/env python3
"""Generate a deliberately messy, entirely invented contract pile.

Everything in here is fictional: companies, people, addresses, company numbers,
sites, prices and signatures. Nothing corresponds to a real organisation.

Our side is an invented UK electrical and industrial distributor,
Halbrook Electrical Distribution Ltd (formerly Halbrook Cable & Fixings Ltd).

Build-only dependencies: reportlab, Pillow, openpyxl, numpy.
Output is deterministic. Review date assumed by the corpus: 2026-09-07.

    python make_messy_pile.py [--output DIR]
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _helpers import (  # noqa: E402
    DISCLAIMER, add_coffee_ring, add_fax_header, add_noise, docx, native_pdf,
    photograph, scan_page, xlsx,
)

REVIEW_DATE = "2026-09-07"

# ------------------------------------------------------------------ entities
OURS = "Halbrook Electrical Distribution Ltd"
OURS_OLD = "Halbrook Cable & Fixings Ltd"
OURS_NO = "04118276"
OURS_ADDR = "Halbrook House, Marmion Way, Ellersby EL4 7QN"

STURMORE_ERP = "Sturmore Rail Group"
STURMORE_LTD = "Sturmore Rail Group Ltd"
STURMORE_LIMITED = "Sturmore Rail Group Limited"
STURMORE_NO = "03996120"
STURMORE_ADDR = "Sturmore House, Calder Rise, Northgate Bridge NB2 5HF"
STURMORE_DEPOT = "Sturmore Rail Group - Northern Depot"

WEXBURY = "Wexbury Utilities plc"
WEXBURY_TRADING = "Wexbury Power Networks"
WEXBURY_NO = "05512443"
WEXBURY_ADDR = "Brinkholt Power Park, Brinkholt BK9 3TA"

COLVERNE = "Colverne Marine Engineering Limited"
ARDLEIGH = "Ardleigh Marine Systems Limited"
ARDLEIGH_LTD = "Ardleigh Marine Systems Ltd"
ARDLEIGH_NO = "06421889"
ARDLEIGH_ADDR = "Ardleigh Yard, Marn Quay, Stanwick Vale SV1 8LR"

BRENLOW = "Brenlow Dockyard Services Limited"
BRENLOW_SHORT = "Brenlow Dockyard Svcs Ltd"
BRENLOW_NO = "07733914"
BRENLOW_ADDR = "No. 4 Dry Dock, Marn Quay, Stanwick Vale SV1 8QP"

TRENTMOOR_ERP = "Trentmoor Housing Partnership"
TRENTMOOR_PRINTED = "The Housing Partnership (Trentmoor) Limited"
TRENTMOOR_NO = "08217640"
TRENTMOOR_ADDR = "Trentmoor Civic Offices, Larkhall Road, Cawdale CW3 2RN"

FENWOLD = "Fenwold Aggregates Limited"
FENWOLD_NO = "09918233"
FENWOLD_ADDR = "Pitside Offices, Hessleby Quarry, Ravensmoor RV7 1BB"

CADMERE = "Cadmere Cable Works Limited"
CADMERE_NO = "03771205"
CADMERE_ADDR = "Cadmere Works, Foundry Lane, Netherford NF2 9DD"

RAVENHEAD = "Ravenhead Grid Services Ltd"

# ------------------------------------------------------------------ people
ALDBURY = "R. Aldbury, Sales Director"
NETTLEFOLD = "P. Nettlefold, Commercial Director"
WHITCOMBE = "A. Whitcombe, Finance Director"
VESSEY = "T. Vessey, Head of Procurement"
PADSTOW = "E. Padstow, Procurement Director"
COTTRILL = "J. Cottrill, Category Manager"
MARRABLE = "D. Marrable, Operations Director"
SCULTHORPE = "H. Sculthorpe, Company Secretary"
ELVERSTONE = "M. Elverstone, Director"
RAVENSCAR = "G. Ravenscar, Managing Director"
OLLERTON = "K. Ollerton, Finance Director"
BEMROSE = "S. Bemrose, Sales Manager"


def sig_scan(title, lines, subtitle=None, blocks=(), footer=None, skew=0.0):
    """A signature page rendered as a picture, with drawn blocks."""
    from PIL import ImageDraw
    from _helpers import font, scrawl
    image, body_end = scan_page(title, lines, subtitle=subtitle, skew=skew, footer=footer,
                                return_end_y=True)
    draw = ImageDraw.Draw(image)
    spacing = 330 if len(blocks) < 2 else 320
    y = max(body_end + 55, 1620 - spacing * len(blocks))
    if y + spacing * len(blocks) > 1640:
        spacing = max(285, (1640 - y) // max(1, len(blocks)))
    for i, block in enumerate(blocks):
        draw.text((110, y), block["for"], font=font(26), fill="#222222")
        if block.get("signed", True):
            scrawl(draw, (140, y + 100), seed=3 + i * 5, scale=1.55)
            draw.text((110, y + 150), block["name"], font=font(29, italic=True), fill="#152762")
            draw.text((110, y + 200), block["title"], font=font(23), fill="#333333")
            draw.text((110, y + 245), "Date: " + block["date"], font=font(27, italic=True),
                      fill="#152762")
        else:
            draw.line([(110, y + 120), (620, y + 120)], fill="#555555", width=2)
            draw.text((110, y + 132), "Name:", font=font(23), fill="#555555")
            draw.line([(230, y + 152), (620, y + 152)], fill="#555555", width=2)
            draw.text((110, y + 178), "Title:", font=font(23), fill="#555555")
            draw.line([(230, y + 198), (620, y + 198)], fill="#555555", width=2)
            draw.text((110, y + 224), "Date:", font=font(23), fill="#555555")
            draw.line([(230, y + 244), (620, y + 244)], fill="#555555", width=2)
        y += spacing
    return image


# =====================================================================
# Account A - Sturmore Rail Group
# =====================================================================

def build_sturmore_2016(path):
    """2016 supplier-paper conditions, signed, later replaced. Our OLD name is on it."""
    pages = [
        {"title": "CONDITIONS OF SUPPLY AND DISTRIBUTION AGREEMENT",
         "head": f"{OURS_OLD} - form CSD/2014",
         "head_right": "Page 1 of 3",
         "paras": [
             f"THIS AGREEMENT is made on 18 July 2016",
             f"BETWEEN (1) {OURS_OLD} (company number {OURS_NO}) whose registered office is at "
             f"{OURS_ADDR} (\"the Company\"); and",
             f"(2) {STURMORE_LIMITED} (company number {STURMORE_NO}) whose registered office is at "
             f"{STURMORE_ADDR} (\"the Customer\").",
             "",
             "##RECITALS",
             "(A) The Company distributes electrical, lighting, cable and industrial products.",
             "(B) The Customer wishes to buy such products from the Company from time to time and "
             "the parties wish to record the conditions on which those purchases are made.",
             "",
             "##1. DEFINITIONS",
             "1.1 \"Conditions\" means the conditions set out in this Agreement. \"Goods\" means the "
             "electrical, lighting, cable and industrial products supplied by the Company. \"Order\" "
             "means an order for Goods placed by the Customer.",
             "1.2 A reference to writing includes electronic mail.",
             "",
             "##2. COMMENCEMENT AND DURATION",
             "2.1 These Conditions take effect on 18 July 2016 and continue until terminated in "
             "accordance with clause 9.",
             "2.2 Either party may terminate this Agreement at any time by giving the other not less "
             "than three months' written notice.",
             "",
             "##3. ORDERS",
             "3.1 Each Order placed by the Customer is an offer to purchase Goods on these "
             "Conditions and no Order is accepted until the Company despatches the Goods or confirms "
             "the Order in writing.",
             "3.2 All purchases of Goods by the Customer from the Company are made on these "
             "Conditions.",
         ]},
        {"title": None,
         "head": f"{OURS_OLD} - form CSD/2014", "head_right": "Page 2 of 3",
         "paras": [
             "##4. PRICES",
             "4.1 Prices are the Company's published list prices less a trade discount of 34 per "
             "cent, unless a special price has been quoted in writing.",
             "4.2 The Company may revise its list prices on 1 April in each year on giving the "
             "Customer thirty days' written notice.",
             "",
             "##5. PAYMENT",
             "5.1 Payment is due within 30 days of the date of invoice.",
             "5.2 Time of payment is of the essence. The Company may charge interest on overdue "
             "sums at 3 per cent above the base rate of its bankers from time to time.",
             "",
             "##6. DELIVERY AND CARRIAGE",
             "6.1 Carriage is paid by the Company on Orders with a net value of GBP 350 or more. On "
             "Orders below that value a carriage charge of GBP 15.00 is added to the invoice.",
             "6.2 Delivery dates are estimates and time of delivery is not of the essence.",
             "",
             "##7. TITLE AND RISK",
             "7.1 Risk in the Goods passes on delivery. Title does not pass until the Company has "
             "been paid in full for the Goods and for all other sums then due from the Customer.",
             "",
             "##8. WARRANTY AND DEFECTS",
             "8.1 The Company will make good, by replacement or credit at its option, Goods shown to "
             "its reasonable satisfaction to be defective within twelve months of delivery.",
             "8.2 Claims for shortage or damage in transit must be notified within three Business "
             "Days of delivery.",
             "",
             "##9. TERMINATION",
             "9.1 Either party may terminate under clause 2.2 without giving a reason.",
             "9.2 Either party may terminate immediately if the other becomes insolvent or commits a "
             "material breach which is not remedied within thirty days of written notice.",
             "",
             "##10. ENTIRE AGREEMENT AND PRECEDENCE",
             "10.1 These Conditions prevail over any terms put forward by the Customer, including "
             "terms printed on or referred to in the Customer's purchase orders.",
             "10.2 This Agreement is the entire agreement between the parties about the supply of "
             "the Goods and replaces all earlier arrangements between them.",
             "",
             "##11. GOVERNING LAW",
             "11.1 This Agreement is governed by the law of England and Wales and the parties submit "
             "to the exclusive jurisdiction of the courts of England and Wales.",
         ]},
    ]
    signature = sig_scan(
        "CONDITIONS OF SUPPLY AND DISTRIBUTION AGREEMENT",
        ["Execution page. This Agreement is entered into on the date written on page 1.",
         f"The Company: {OURS_OLD}",
         f"The Customer: {STURMORE_LIMITED}"],
        subtitle="Page 3 of 3",
        blocks=[
            {"for": f"SIGNED for and on behalf of {OURS_OLD}", "name": "R. Aldbury",
             "title": "Sales Director", "date": "18 July 2016"},
            {"for": f"SIGNED for and on behalf of {STURMORE_LIMITED}", "name": "T. Vessey",
             "title": "Head of Procurement", "date": "18 July 2016"},
        ], skew=0.4)
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="legal",
                      image_pages={3: signature}, title="Conditions of Supply and Distribution Agreement",
                      author="Halbrook legal (invented)")


def build_sturmore_2021(path):
    """2021 customer-paper master; replaces the 2016 conditions; signed both sides."""
    pages = [
        {"title": "MASTER SUPPLY AGREEMENT",
         "subtitle": "Contract reference SRG/PROC/2021/114 - electrical and industrial products",
         "head": "STURMORE RAIL GROUP - PROCUREMENT", "head_right": "SRG/PROC/2021/114",
         "paras": [
             f"THIS AGREEMENT is dated 22 February 2021 and is made between {STURMORE_LTD} "
             f"(registered in England number {STURMORE_NO}) of {STURMORE_ADDR} (\"SRG\") and "
             f"{OURS} (registered in England number {OURS_NO}) of {OURS_ADDR} (\"the Supplier\").",
             "",
             "##1 DEFINITIONS",
             "1.1 \"Commencement Date\" means 1 March 2021. \"Depot\" means a depot of SRG listed in "
             "Appendix A. \"Price File\" means the schedule of prices issued under clause 6. "
             "\"Products\" means electrical, lighting, cable and industrial products.",
             "",
             "##2 TERM",
             "2.1 This Agreement commences on the Commencement Date and continues for an initial "
             "period of three years.",
             "2.2 At the end of the initial period this Agreement continues from year to year until "
             "either party gives the other not less than six months' written notice expiring at any "
             "time.",
             "",
             "##3 EARLIER AGREEMENT",
             f"3.1 This Agreement supersedes and replaces the Conditions of Supply and Distribution "
             f"Agreement dated 18 July 2016 between SRG and {OURS_OLD}, which ceases to have effect "
             "on the Commencement Date.",
             "3.2 Orders placed before the Commencement Date are completed under the earlier "
             "conditions.",
             "",
             "##4 SCOPE",
             "4.1 All purchases of Products by SRG and its Depots from the Supplier are made under "
             "this Agreement.",
             "4.2 The Supplier is appointed as an approved supplier of the Products. No volume is "
             "guaranteed and the appointment is not exclusive.",
         ]},
        {"title": None, "head": "STURMORE RAIL GROUP - PROCUREMENT", "head_right": "SRG/PROC/2021/114",
         "paras": [
             "##5 ORDERING",
             "5.1 SRG places Orders by its electronic purchasing system. An Order is accepted when "
             "the Supplier acknowledges it or despatches the Products, whichever is earlier.",
             "5.2 The Supplier's own conditions of sale do not apply to an Order placed under this "
             "Agreement.",
             "",
             "##6 PRICE",
             "6.1 Prices are those in the Price File in force at the date of the Order.",
             "6.2 The Price File is reviewed once in each year with effect from 1 April. The "
             "Supplier gives SRG at least sixty days' written notice of a proposed change.",
             "",
             "##7 PAYMENT",
             "7.1 The Supplier shall be paid within 45 days from the end of the month in which the "
             "invoice is dated.",
             "7.2 SRG may set off against any sum due any amount owed to it by the Supplier.",
             "",
             "##8 DELIVERY AND CARRIAGE",
             "8.1 Delivery is free of carriage on Orders with a net value of GBP 250 or more. On "
             "Orders below that value a carriage charge of GBP 22.50 applies.",
             "8.2 Delivery is to the Depot stated on the Order between 07:00 and 16:00 on a Business "
             "Day.",
             "",
             "##9 ENTITIES AND TERRITORY COVERED",
             "9.1 This Agreement covers SRG and the Depots listed in Appendix A. It applies to "
             "deliveries in the United Kingdom only.",
             "9.2 No other company in SRG's group may place Orders under this Agreement without the "
             "Supplier's written agreement.",
             "",
             "##10 TERMINATION",
             "10.1 Either party may terminate under clause 2.2.",
             "10.2 SRG may terminate immediately if the Supplier commits a material breach which is "
             "not remedied within twenty Business Days of written notice.",
             "",
             "##11 PRECEDENCE",
             "11.1 If there is a conflict between this Agreement, an Order and the Supplier's "
             "conditions of sale, this Agreement prevails, then the Order, then the Supplier's "
             "conditions of sale.",
             "",
             "##12 ENTIRE AGREEMENT AND VARIATION",
             "12.1 This Agreement is the entire agreement between the parties in relation to the "
             "supply of the Products.",
             "12.2 No variation of this Agreement is effective unless it is in writing and signed by "
             "both parties.",
             "",
             "##13 GOVERNING LAW",
             "13.1 This Agreement and any dispute arising out of it are governed by the law of "
             "England and Wales.",
         ]},
        {"title": "APPENDIX A - DEPOTS COVERED",
         "head": "STURMORE RAIL GROUP - PROCUREMENT", "head_right": "SRG/PROC/2021/114",
         "paras": [
             "A1. Sturmore Rail Group - Northern Depot, Calder Rise, Northgate Bridge.",
             "A2. Sturmore Rail Group - Central Stores, Marmion Way, Ellersby.",
             "A3. Deliveries to any other address are made under clause 8 at the carriage rates in "
             "clause 8.1.",
             "A4. This Appendix may be amended by SRG on written notice to the Supplier. It has no "
             "separate expiry date and forms part of this Agreement.",
         ]},
    ]
    signature = sig_scan(
        "MASTER SUPPLY AGREEMENT - EXECUTION PAGE",
        ["Contract reference SRG/PROC/2021/114.",
         "Executed by the parties. The Commencement Date is 1 March 2021 as stated in clause 1.1.",
         f"SRG: {STURMORE_LTD}", f"The Supplier: {OURS}"],
        blocks=[
            {"for": f"SIGNED for and on behalf of {STURMORE_LTD}", "name": "T. Vessey",
             "title": "Head of Procurement", "date": "22 February 2021"},
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "P. Nettlefold",
             "title": "Commercial Director", "date": "24 February 2021"},
        ], skew=-0.3)
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="plain",
                      image_pages={4: signature}, title="Master Supply Agreement SRG/PROC/2021/114",
                      author="Sturmore Rail Group procurement (invented)")


def build_sturmore_amendment_1(path):
    pages = [{
        "title": "AMENDMENT No. 1 TO THE MASTER SUPPLY AGREEMENT DATED 22 FEBRUARY 2021",
        "head": "STURMORE RAIL GROUP - PROCUREMENT", "head_right": "SRG/PROC/2021/114/A1",
        "style": "plain",
        "paras": [
            f"THIS AMENDMENT is dated 6 June 2023 and is made between {STURMORE_LTD} (\"SRG\") and "
            f"{OURS} (\"the Supplier\").",
            "",
            "##BACKGROUND",
            "The parties entered into a Master Supply Agreement dated 22 February 2021, reference "
            "SRG/PROC/2021/114 (\"the Agreement\"). The parties wish to amend the payment term.",
            "",
            "##1 AMENDMENT",
            "1.1 With effect from 1 July 2023 clause 7.1 of the Agreement is deleted and replaced "
            "with the following:",
            "\t\"7.1 The Supplier shall be paid within 60 days from the end of the month in which "
            "the invoice is dated.\"",
            "1.2 No other provision of the Agreement is amended and the Agreement continues in full "
            "force and effect as amended by this Amendment.",
            "1.3 This Amendment continues for as long as the Agreement continues.",
            "",
            "##2 CONFIRMATION",
            "2.1 The parties confirm that all purchases of Products by SRG and its Depots continue "
            "to be made under the Agreement.",
            "",
            "##3 GOVERNING LAW",
            "3.1 This Amendment is governed by the law of England and Wales.",
            "",
            f"SIGNED for and on behalf of {STURMORE_LTD}",
            "T. Vessey, Head of Procurement.  Date: 6 June 2023",
            "",
            f"SIGNED for and on behalf of {OURS}",
            "P. Nettlefold, Commercial Director.  Date: 6 June 2023",
        ]}]
    return native_pdf(path, pages, signed_pages={1: 2}, style="plain",
                      title="Amendment No. 1 SRG/PROC/2021/114/A1",
                      author="Sturmore Rail Group procurement (invented)")


AMENDMENT_2_DOCX = [
    "AMENDMENT No. 2 TO THE MASTER SUPPLY AGREEMENT DATED 22 FEBRUARY 2021",
    "Reference SRG/PROC/2021/114/A2 - working draft for discussion, circulated 14 July 2026.",
    f"THIS AMENDMENT is made between {STURMORE_LTD} (\"SRG\") and {OURS} (\"the Supplier\").",
    "BACKGROUND: the parties entered into a Master Supply Agreement dated 22 February 2021 as "
    "amended by Amendment No. 1 dated 6 June 2023 (\"the Agreement\"). The parties are discussing "
    "further changes to carriage and payment.",
    "1.1 With effect from the date of this Amendment clause 8.1 of the Agreement would be deleted "
    "and replaced with: \"Delivery is free of carriage on Orders with a net value of GBP 400 or "
    "more. On Orders below that value a carriage charge of GBP 28.00 applies.\"",
    "1.2 Clause 7.1 of the Agreement (as amended by Amendment No. 1) would be deleted and replaced "
    "with: \"The Supplier shall be paid within 90 days from the end of the month in which the "
    "invoice is dated.\"",
    "1.3 No other provision of the Agreement would be amended.",
    "2.1 This draft has not been agreed and creates no obligation unless and until it is signed by "
    "both parties.",
    "3.1 This Amendment would be governed by the law of England and Wales.",
    f"SIGNED for and on behalf of {STURMORE_LTD}: ______________________  Date: ______________",
    f"SIGNED for and on behalf of {OURS}: ______________________  Date: ______________",
]

PLAYBOOK_DOCX = [
    f"ACCOUNT NOTES - {STURMORE_ERP} - INTERNAL ONLY, DO NOT SEND TO THE CUSTOMER",
    f"Maintained by {OURS} national accounts. Version 4, 3 March 2026. This is guidance, not a "
    "contract, and it is not signed by anyone at Sturmore.",
    "1. Margin. Hold 17.5 per cent gross margin across the regular cable and containment basket. "
    "Anything below 14 per cent needs the Commercial Director's approval before quoting.",
    "2. Market basket. The 240 line market basket is repriced each February ahead of the 1 April "
    "review in clause 6.2 of the master. Keep the top forty lines within two per cent of the "
    "benchmark.",
    "3. Ad hoc. Urgent same day items for the Northern Depot go out ad hoc at list less 20 per "
    "cent with the account manager's approval; do not put them on the contract price file.",
    "4. Payment. Sturmore pay to 60 days end of month since Amendment No. 1. Credit control should "
    "not chase before day 65.",
    "5. Carriage. We absorb carriage at 250 pounds. The 500 pound proposal in the Amendment No. 2 "
    "draft is not agreed and must not be quoted to the customer.",
    "6. Do not treat any note in this document as a variation of the master supply agreement.",
]


def build_sturmore_po(path):
    """Purchase order whose reverse-side conditions claim precedence over any master."""
    pages = [
        {"title": "PURCHASE ORDER", "style": "typed",
         "head": "STURMORE RAIL GROUP - NORTHERN DEPOT", "head_right": "PO 88231",
         "paras": [
             "Order number: 88231            Order date: 19 August 2026",
             f"Buyer: {STURMORE_DEPOT}, Calder Rise, Northgate Bridge NB2 5HF",
             f"A depot of {STURMORE_LTD}. Cost centre NB-4412.",
             f"Supplier: {OURS}, {OURS_ADDR}. Supplier account SRG-0041.",
             "",
             "Line 1   400 m   SWA armoured cable 4 core 16mm            GBP 2,184.00",
             "Line 2    24 ea  Steel trunking 100x100 3m lengths         GBP   612.00",
             "Line 3     6 ea  Distribution board 12 way TP&N            GBP 1,488.00",
             "",
             "Net order value GBP 4,284.00. Delivery required 26 August 2026 to the Northern Depot "
             "goods inward gate between 07:00 and 12:00.",
             "",
             "This order is placed against supplier account SRG-0041. Invoices must quote the order "
             "number. See the conditions of purchase overleaf.",
             "",
             "Raised by: L. Harradine, Stores Controller. No signature is required on this order.",
         ]},
        {"title": "CONDITIONS OF PURCHASE (REVERSE)", "style": "typed",
         "head": "STURMORE RAIL GROUP - NORTHERN DEPOT", "head_right": "PO 88231",
         "paras": [
             "1. In these Conditions \"the Buyer\" means Sturmore Rail Group and \"the Supplier\" "
             "means the person named on the face of this order.",
             "2. This order is an offer to buy the goods described on the face of it on these "
             "Conditions and on no others.",
             "3. Delivery must be made on the date stated. Time is of the essence.",
             "4. Payment terms are 60 days from the end of the month of a correct invoice.",
             "5. Carriage is included in the prices stated unless the face of the order says "
             "otherwise.",
             "6. Title and risk pass to the Buyer on delivery and acceptance at the delivery point.",
             "7. The Supplier warrants that the goods are of satisfactory quality and fit for the "
             "purpose made known to it.",
             "8. The Buyer may reject non conforming goods within ten Business Days of delivery.",
             "9. The Supplier shall indemnify the Buyer against claims arising from defects in the "
             "goods.",
             "10. The Supplier may not assign or subcontract this order without written consent.",
             "11. The Buyer may cancel this order at any time before despatch without charge.",
             "12. Neither party is liable for indirect or consequential loss.",
             "13. The Supplier shall comply with all applicable law and with the Buyer's site rules.",
             "14. These Conditions apply to the exclusion of all other terms and prevail over any "
             "master agreement, framework agreement or standard conditions of the Supplier, however "
             "and whenever agreed.",
             "15. This order is governed by the law of England and Wales.",
         ]},
    ]
    return native_pdf(path, pages, style="typed", title="Purchase Order 88231",
                      author="Sturmore Rail Group Northern Depot (invented)")


# =====================================================================
# Account B - Wexbury Utilities plc
# =====================================================================

def _wexbury_framework_pages(payment_days, notice_months, ref, dated, draft=False):
    return [
        {"title": "FRAMEWORK AGREEMENT FOR THE SUPPLY OF ELECTRICAL PRODUCTS",
         "subtitle": f"Reference {ref}" + (" - DRAFT v0.4, not for signature" if draft else ""),
         "head": "WEXBURY UTILITIES PLC", "head_right": ref,
         "paras": [
             f"THIS FRAMEWORK AGREEMENT is dated {dated} and made between:",
             f"(1) {WEXBURY}, a company registered in England and Wales with number {WEXBURY_NO} "
             f"whose registered office is at {WEXBURY_ADDR} (\"Wexbury\"); and",
             f"(2) {OURS}, a company registered in England and Wales with number {OURS_NO} whose "
             f"registered office is at {OURS_ADDR} (\"the Supplier\").",
             "",
             "##1 INTERPRETATION",
             "1.1 \"Call Off\" means an order placed by Wexbury under this Agreement. \"Products\" "
             "means electrical wholesale products, including cable, cable management, wiring "
             "accessories, lighting and low voltage switchgear.",
             "1.2 \"Group Company\" means a subsidiary of Wexbury within the meaning of section 1159 "
             "of the Companies Act 2006.",
             "",
             "##2 COMMENCEMENT AND DURATION",
             "2.1 This Agreement commences on 1 June 2022 and continues until it is terminated under "
             "clause 3.",
             "",
             "##3 TERMINATION",
             f"3.1 Either party may terminate this Agreement immediately by written notice if the "
             "other commits a material breach which is not remedied within thirty days.",
             f"3.2 Either party may terminate this Agreement for convenience by giving the other not "
             f"less than {notice_months} months' written notice.",
             "3.3 Termination does not affect Call Offs already placed, which are completed on the "
             "terms of this Agreement.",
             "",
             "##4 SCOPE",
             "4.1 All purchases of Products by Wexbury from the Supplier are made under this "
             "Agreement.",
             "4.2 Wexbury and any Group Company may place Call Offs. Wexbury remains liable for "
             "payment of Call Offs placed by a Group Company.",
             "4.3 This Agreement applies to deliveries in the United Kingdom.",
         ]},
        {"title": None, "head": "WEXBURY UTILITIES PLC", "head_right": ref,
         "paras": [
             "##5 PRICES",
             "5.1 Prices are the Supplier's published list prices less the discounts in the discount "
             "matrix issued to Wexbury and reviewed each 1 April.",
             "5.2 The Supplier shall give Wexbury sixty days' written notice of any increase.",
             "",
             "##6 PAYMENT",
             f"6.1 Wexbury shall pay correctly rendered invoices within {payment_days} days from the "
             "end of the month in which the invoice is dated.",
             "6.2 Wexbury may withhold payment of a disputed invoice provided it notifies the "
             "Supplier of the dispute within twenty Business Days of receipt.",
             "",
             "##7 DELIVERY AND CARRIAGE",
             "7.1 Delivery is included in the price for Call Offs with a net value of GBP 150 or "
             "more. Below that value the Supplier may charge carriage at its published rate.",
             "7.2 Delivery is to the site stated in the Call Off.",
             "",
             "##8 QUALITY AND WARRANTY",
             "8.1 The Products shall conform with the relevant British Standard and with the "
             "specification stated in the Call Off.",
             "8.2 The Supplier shall replace or credit defective Products notified within twelve "
             "months of delivery.",
             "",
             "##9 CONFIDENTIALITY AND DATA",
             "9.1 Each party shall keep confidential the other's confidential information for three "
             "years after the end of this Agreement.",
             "",
             "##10 PRECEDENCE AND ENTIRE AGREEMENT",
             "10.1 In the event of conflict this Agreement prevails over the Call Off and over the "
             "Supplier's conditions of sale.",
             "10.2 This Agreement is the entire agreement between the parties about the supply of "
             "the Products.",
             "",
             "##11 GOVERNING LAW",
             "11.1 This Agreement is governed by the law of England and Wales and the courts of "
             "England and Wales have exclusive jurisdiction.",
         ]},
    ]


def build_wexbury_framework(path):
    """Signed by Wexbury only: our execution block is blank."""
    pages = _wexbury_framework_pages(60, "six", "WU/2022/EL-07", "12 May 2022")
    signature = sig_scan(
        "FRAMEWORK AGREEMENT - EXECUTION",
        ["Reference WU/2022/EL-07.",
         "The parties have executed this Agreement on the dates shown below.",
         f"Wexbury: {WEXBURY}", f"The Supplier: {OURS}"],
        blocks=[
            {"for": f"SIGNED for and on behalf of {WEXBURY}", "name": "E. Padstow",
             "title": "Procurement Director", "date": "12 May 2022"},
            {"for": f"SIGNED for and on behalf of {OURS}", "signed": False,
             "name": "", "title": "", "date": ""},
        ], skew=0.5)
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="legal",
                      image_pages={3: signature}, title="Framework Agreement WU/2022/EL-07",
                      author="Wexbury Utilities plc procurement (invented)")


def build_wexbury_draft(path):
    """Filename says signed final; it is an unsigned watermarked draft with different terms."""
    pages = _wexbury_framework_pages(90, "twelve", "WU/2022/EL-07", "3 March 2022", draft=True)
    pages.append({
        "title": "EXECUTION", "head": "WEXBURY UTILITIES PLC", "head_right": "WU/2022/EL-07 DRAFT",
        "paras": [
            "This draft is issued for review only. Comments to Wexbury procurement by 18 March 2022.",
            f"SIGNED for and on behalf of {WEXBURY}",
            "Name: ____________________  Title: ____________________  Date: ______________",
            "",
            f"SIGNED for and on behalf of {OURS}",
            "Name: ____________________  Title: ____________________  Date: ______________",
        ]})
    return native_pdf(path, pages, style="legal", watermark="DRAFT",
                      title="Framework Agreement WU/2022/EL-07 draft v0.4",
                      author="Wexbury Utilities plc procurement (invented)")


def build_wexbury_confirmation(path):
    pages = [{
        "title": None, "style": "letter",
        "paras": [
            f"{WEXBURY}",
            f"{WEXBURY_ADDR}",
            "",
            "4 September 2024",
            "",
            f"{OURS}",
            f"{OURS_ADDR}",
            "",
            "Dear Sirs",
            "",
            "SUPPLY OF ELECTRICAL PRODUCTS - TRADING TERMS",
            "",
            "We write following your credit control team's query about the basis on which our "
            "purchase orders are placed.",
            "We confirm that we are trading under the terms of the Framework Agreement dated 12 May "
            "2022, reference WU/2022/EL-07, and that all purchase orders issued by Wexbury Utilities "
            "plc and by our subsidiaries for electrical products are placed under that agreement.",
            "For the avoidance of doubt this includes the payment term of 60 days from the end of "
            "the month of invoice at clause 6.1 and the carriage arrangement at clause 7.1.",
            "This letter is not a variation of that agreement and no other term is affected.",
            "",
            "Yours faithfully",
            "",
            "",
            "J. Cottrill",
            "Category Manager, Electrical",
            f"for and on behalf of {WEXBURY}",
        ]}]
    return native_pdf(path, pages, signed_pages={1: 1}, style="letter",
                      title="Letter confirming framework terms",
                      author="Wexbury Utilities plc (invented)")


def build_wexbury_rebate(path):
    pages = [{
        "title": None, "style": "letter",
        "paras": [
            f"{OURS}",
            f"{OURS_ADDR}    Registered in England number {OURS_NO}",
            "",
            "12 January 2026",
            "",
            f"The Head of Procurement",
            f"{WEXBURY_TRADING}",
            f"{WEXBURY_ADDR}",
            "",
            "Dear Colleague",
            "",
            "REBATE ARRANGEMENT FOR THE 2026 CALENDAR YEAR",
            "",
            "Thank you for your continued business. We are pleased to confirm the rebate for the "
            "period 1 January 2026 to 31 December 2026.",
            "1. We will credit 1.75 per cent of your net invoiced spend on electrical products in "
            "the period, on the amount by which that spend exceeds GBP 400,000.",
            "2. The rebate is calculated on invoices dated in the period, net of returns and "
            "credits, and excluding carriage and value added tax.",
            "3. The credit note will be issued by 28 February 2027.",
            "4. This letter sets the rebate for the 2026 calendar year only. It does not vary the "
            "prices, the payment term, the carriage arrangement or any other trading term, and it "
            "does not commit either of us beyond 31 December 2026.",
            "5. This arrangement is personal to the addressee and may not be assigned.",
            "",
            "Yours sincerely",
            "",
            "",
            "A. Whitcombe",
            "Finance Director",
            f"for and on behalf of {OURS}",
        ]}]
    return native_pdf(path, pages, signed_pages={1: 1}, style="letter",
                      title="2026 rebate letter", author="Halbrook finance (invented)")


def build_wexbury_photo(path):
    """A phone photograph of a one page signed letter, taken off square."""
    page = sig_scan(
        "WEXBURY UTILITIES PLC",
        ["Brinkholt Power Park, Brinkholt BK9 3TA",
         "",
         "21 January 2026",
         "",
         f"{OURS}, {OURS_ADDR}",
         "",
         "Dear Ms Whitcombe",
         "",
         "REBATE ARRANGEMENT 2026 - ACCEPTANCE",
         "",
         "Thank you for your letter of 12 January 2026. We accept the rebate arrangement for the "
         "period 1 January 2026 to 31 December 2026 on the terms set out in it.",
         "We note that the arrangement covers that period only and does not change the Framework "
         "Agreement dated 12 May 2022.",
         "",
         "Yours sincerely"],
        blocks=[{"for": f"for and on behalf of {WEXBURY}", "name": "J. Cottrill",
                 "title": "Category Manager, Electrical", "date": "21 January 2026"}],
        footer=DISCLAIMER)
    photo = photograph(page, angle=6.5, seed=11)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    photo.save(path, quality=74)
    return path


def build_wexbury_notice(path):
    pages = [{
        "title": None, "style": "letter",
        "paras": [
            f"{OURS}",
            f"{OURS_ADDR}",
            "",
            "14 August 2026",
            "",
            "BY EMAIL AND BY RECORDED DELIVERY",
            "",
            "The Procurement Director",
            f"{WEXBURY}",
            f"{WEXBURY_ADDR}",
            "",
            "Dear Ms Padstow",
            "",
            "FRAMEWORK AGREEMENT DATED 12 MAY 2022 (REFERENCE WU/2022/EL-07) - NOTICE OF "
            "TERMINATION",
            "",
            "We refer to the Framework Agreement dated 12 May 2022 between Wexbury Utilities plc and "
            "Halbrook Electrical Distribution Ltd.",
            "We hereby give notice under clause 3.2 of that Agreement to terminate it for "
            "convenience. The six month notice period runs from the date of this letter and the "
            "Agreement will therefore end on 14 February 2027.",
            "Until that date the Agreement continues in full force. Call Offs placed before 14 "
            "February 2027 will be completed on its terms in accordance with clause 3.3.",
            "We would be glad to discuss replacement arrangements before the end of the notice "
            "period.",
            "",
            "Yours sincerely",
            "",
            "",
            "P. Nettlefold",
            "Commercial Director",
            f"for and on behalf of {OURS}",
        ]}]
    return native_pdf(path, pages, signed_pages={1: 1}, style="letter",
                      title="Notice of termination WU/2022/EL-07",
                      author="Halbrook commercial (invented)")


# =====================================================================
# Account C - Ardleigh Marine Systems Limited (formerly Colverne) and Brenlow
# =====================================================================

def build_colverne_2019(path):
    pages = [
        {"title": "SUPPLY AGREEMENT",
         "head": f"{OURS} - agreement 2019/044", "head_right": "Page 1 of 3",
         "paras": [
             f"THIS SUPPLY AGREEMENT is made on 9 April 2019 between {OURS} (company number "
             f"{OURS_NO}) of {OURS_ADDR} (\"the Supplier\") and {COLVERNE} (company number "
             f"{ARDLEIGH_NO}) of {ARDLEIGH_ADDR} (\"the Customer\").",
             "",
             "##1 WHAT THIS AGREEMENT COVERS",
             "1.1 The Supplier supplies electrical, cable and industrial products to the Customer.",
             "1.2 All purchases of those products by the Customer from the Supplier are made under "
             "this Agreement, whether ordered by telephone, by electronic mail or through the "
             "Supplier's trade counter.",
             "1.3 This Agreement covers the Customer only. It does not cover any other company.",
             "",
             "##2 HOW LONG IT LASTS",
             "2.1 This Agreement starts on 9 April 2019.",
             "2.2 It continues until either party ends it by giving the other not less than three "
             "months' written notice.",
             "2.3 Either party may end this Agreement immediately if the other becomes insolvent.",
             "",
             "##3 PRICES",
             "3.1 Prices are those in the Supplier's price file for the Customer, being list price "
             "less 31 per cent on cable and less 26 per cent on all other product groups.",
             "3.2 Prices are reviewed on 1 April in each year.",
         ]},
        {"title": None, "head": f"{OURS} - agreement 2019/044", "head_right": "Page 2 of 3",
         "paras": [
             "##4 PAYMENT",
             "4.1 The Customer shall pay each invoice within 30 days of the date of the invoice.",
             "4.2 The Supplier may suspend deliveries while any sum is overdue.",
             "",
             "##5 DELIVERY AND CARRIAGE",
             "5.1 Carriage is charged to the Customer at cost on every delivery. There is no "
             "carriage free threshold under this Agreement.",
             "5.2 Delivery is to the Customer's yard at Marn Quay unless the order says otherwise.",
             "",
             "##6 QUALITY",
             "6.1 The Supplier passes on to the Customer the benefit of any manufacturer's warranty "
             "and will replace or credit products shown to be defective within twelve months.",
             "",
             "##7 TITLE AND RISK",
             "7.1 Risk passes on delivery; title passes on payment in full.",
             "",
             "##8 CHANGE OF NAME OR OWNERSHIP",
             "8.1 If either party changes its name it shall tell the other in writing. A change of "
             "name does not affect this Agreement, which continues in the new name.",
             "",
             "##9 PRECEDENCE",
             "9.1 This Agreement prevails over any purchase order, delivery note or other document "
             "used by either party.",
             "",
             "##10 ENTIRE AGREEMENT",
             "10.1 This Agreement is the entire agreement between the parties about the supply of "
             "the products.",
             "",
             "##11 LAW",
             "11.1 The law of England and Wales applies.",
         ]},
    ]
    signature = sig_scan(
        "SUPPLY AGREEMENT - SIGNATURES",
        ["Agreement 2019/044, made on 9 April 2019.",
         f"The Supplier: {OURS}", f"The Customer: {COLVERNE}"],
        subtitle="Page 3 of 3",
        blocks=[
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "R. Aldbury",
             "title": "Sales Director", "date": "9 April 2019"},
            {"for": f"SIGNED for and on behalf of {COLVERNE}", "name": "D. Marrable",
             "title": "Operations Director", "date": "9 April 2019"},
        ], skew=-0.6)
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="plain",
                      image_pages={3: signature}, title="Supply Agreement 2019/044",
                      author="Halbrook sales (invented)")


def build_name_change_letter(path):
    pages = [{
        "title": None, "style": "letter",
        "paras": [
            f"{ARDLEIGH}",
            f"(formerly {COLVERNE})",
            f"{ARDLEIGH_ADDR}    Registered in England number {ARDLEIGH_NO}",
            "",
            "2 February 2021",
            "",
            "The Sales Director",
            f"{OURS}",
            f"{OURS_ADDR}",
            "",
            "Dear Mr Aldbury",
            "",
            "CHANGE OF COMPANY NAME",
            "",
            "We write to tell you that following a special resolution passed on 21 January 2021 our "
            f"company changed its name from {COLVERNE} to {ARDLEIGH} with effect from 25 January "
            "2021. The certificate of incorporation on change of name has been issued.",
            f"The company number, {ARDLEIGH_NO}, the registered office and the trading address are "
            "unchanged. This is a change of name only. There has been no transfer of the business "
            "and no new company has been formed.",
            "All existing agreements continue in force in the new name, including the Supply "
            "Agreement dated 9 April 2019 (your reference 2019/044). Please update your ledger, "
            "invoices and delivery notes accordingly.",
            "Our purchasing contacts and account arrangements are unchanged.",
            "",
            "Yours sincerely",
            "",
            "",
            "H. Sculthorpe",
            "Company Secretary",
            f"for and on behalf of {ARDLEIGH}",
        ]}]
    return native_pdf(path, pages, signed_pages={1: 1}, style="letter",
                      title="Change of company name", author="Ardleigh Marine Systems (invented)")


def _ardleigh_msa_body(version, dated, payment_days, notice_months, threshold, carriage,
                       execution=False):
    """Shared body text so v3, v4 clean, v4 redline and the executed PDF really are versions."""
    return [
        f"MASTER SUPPLY AGREEMENT - {version}",
        f"Draft dated {dated}. Reference AMS/2025/MSA." if not execution
        else f"Reference AMS/2025/MSA. Dated {dated}.",
        f"THIS AGREEMENT is made between {OURS} (company number {OURS_NO}) of {OURS_ADDR} (\"the "
        f"Supplier\") and {ARDLEIGH_LTD} (company number {ARDLEIGH_NO}) of {ARDLEIGH_ADDR} (\"the "
        "Customer\").",
        "BACKGROUND: the parties have traded since 2019 under a Supply Agreement dated 9 April 2019 "
        "and wish to replace it with this Agreement.",
        "1.1 Definitions. \"Commencement Date\" means 1 October 2025. \"Products\" means electrical, "
        "cable, containment and industrial products supplied by the Supplier. \"Order\" means an "
        "order for Products placed by the Customer.",
        "2.1 Term. This Agreement commences on the Commencement Date and continues until terminated "
        "under clause 12.",
        "2.2 Replacement. This Agreement supersedes and replaces the Supply Agreement dated 9 April "
        "2019 between the parties with effect from the Commencement Date, and that agreement then "
        "ceases to have effect.",
        "3.1 Scope. All purchases of Products by the Customer from the Supplier are made under this "
        "Agreement. The Agreement covers the Customer only and applies in the United Kingdom.",
        "4.1 Ordering. An Order is an offer to buy on these terms and is accepted when the Supplier "
        "acknowledges it or despatches the Products.",
        "5.1 Prices. Prices are list price less the discounts in the discount schedule issued to the "
        "Customer, reviewed on 1 April each year on sixty days' notice.",
        f"6.1 Payment. The Customer shall pay each invoice within {payment_days} days of the date of "
        "the invoice.",
        f"7.1 Carriage. Delivery is free of carriage on Orders with a net value of GBP {threshold} "
        f"or more. On Orders below that value a carriage charge of GBP {carriage} applies.",
        "8.1 Quality. The Supplier shall replace or credit Products shown to be defective within "
        "twelve months of delivery.",
        "9.1 Title and risk. Risk passes on delivery. Title passes on payment in full.",
        "10.1 Confidentiality. Each party shall keep the other's confidential information "
        "confidential for three years after this Agreement ends.",
        "11.1 Liability. Neither party excludes liability for death or personal injury caused by "
        "negligence or for fraud. Subject to that, neither party is liable for indirect or "
        "consequential loss and each party's total liability in any twelve month period is limited "
        "to the sums invoiced in that period.",
        f"12.1 Termination for convenience. Either party may terminate this Agreement by giving the "
        f"other not less than {notice_months} months' written notice.",
        "12.2 Termination for breach. Either party may terminate immediately by written notice if "
        "the other commits a material breach which is not remedied within thirty days.",
        "13.1 Precedence. This Agreement prevails over any purchase order, order acknowledgement or "
        "other document passing between the parties.",
        "13.2 Entire agreement. This Agreement is the entire agreement between the parties about the "
        "supply of the Products.",
        "14.1 Governing law. This Agreement is governed by the law of England and Wales and the "
        "courts of England and Wales have exclusive jurisdiction.",
    ]


def build_ardleigh_executed(path):
    body = _ardleigh_msa_body("EXECUTION VERSION", "15 September 2025", 45, "twelve", "300",
                              "28.00", execution=True)
    pages = [
        {"title": body[0], "subtitle": body[1], "head": f"{OURS} / {ARDLEIGH_LTD}",
         "head_right": "AMS/2025/MSA", "paras": body[2:12]},
        {"title": None, "head": f"{OURS} / {ARDLEIGH_LTD}", "head_right": "AMS/2025/MSA",
         "paras": body[12:]},
    ]
    signature = sig_scan(
        "MASTER SUPPLY AGREEMENT - EXECUTION PAGE",
        ["Reference AMS/2025/MSA.",
         "Executed on the dates below. The Commencement Date is 1 October 2025 (clause 1.1).",
         f"The Supplier: {OURS}", f"The Customer: {ARDLEIGH_LTD}"],
        blocks=[
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "P. Nettlefold",
             "title": "Commercial Director", "date": "15 September 2025"},
            {"for": f"SIGNED for and on behalf of {ARDLEIGH_LTD}", "name": "D. Marrable",
             "title": "Operations Director", "date": "15 September 2025"},
        ])
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="legal",
                      image_pages={3: signature}, title="Master Supply Agreement AMS/2025/MSA",
                      author="Halbrook legal (invented)")


def build_brenlow_master(path):
    pages = [
        {"title": "MASTER SUPPLY AGREEMENT",
         "head": f"{OURS} - agreement 2020/091", "head_right": "Page 1 of 3",
         "paras": [
             f"THIS AGREEMENT is made on 3 November 2020 between {OURS} (company number {OURS_NO}) "
             f"of {OURS_ADDR} (\"the Supplier\") and {BRENLOW} (company number {BRENLOW_NO}) of "
             f"{BRENLOW_ADDR} (\"the Customer\").",
             "",
             "##1 SCOPE",
             "1.1 All purchases of electrical, cable and industrial products by the Customer from "
             "the Supplier are made under this Agreement.",
             "1.2 This Agreement covers the Customer alone. No parent, subsidiary or associated "
             "company of the Customer may order under it.",
             "",
             "##2 DURATION",
             "2.1 This Agreement starts on 3 November 2020 and continues until terminated under "
             "clause 12.",
             "",
             "##3 PRICES AND PAYMENT",
             "3.1 Prices are list price less 24 per cent, reviewed on 1 April each year.",
             "3.2 The Customer shall pay each invoice within 30 days from the end of the month in "
             "which the invoice is dated.",
             "",
             "##4 CARRIAGE",
             "4.1 Carriage is charged at cost on all deliveries to the dry dock.",
         ]},
        {"title": None, "head": f"{OURS} - agreement 2020/091", "head_right": "Page 2 of 3",
         "paras": [
             "##5 QUALITY", "5.1 Twelve month replacement or credit for defective products.",
             "##6 TITLE AND RISK", "6.1 Risk on delivery; title on payment in full.",
             "##7 MARINE ENVIRONMENT",
             "7.1 Products supplied for use below the waterline shall meet the specification agreed "
             "in writing for that use.",
             "##8 INSURANCE", "8.1 Each party shall maintain public liability insurance of not less "
             "than GBP 5,000,000.",
             "##9 CONFIDENTIALITY", "9.1 Three years after the end of this Agreement.",
             "##10 LIABILITY", "10.1 Neither party is liable for indirect or consequential loss.",
             "##11 ASSIGNMENT", "11.1 Neither party may assign without written consent.",
             "##12 TERMINATION",
             "12.1 Either party may terminate this Agreement for convenience by giving the other not "
             "less than one month's written notice.",
             "12.2 Either party may terminate immediately for an unremedied material breach.",
             "##13 PRECEDENCE AND ENTIRE AGREEMENT",
             "13.1 This Agreement prevails over any purchase order. It is the entire agreement "
             "between the parties about the supply of the products.",
             "##14 LAW", "14.1 The law of England and Wales applies.",
         ]},
    ]
    signature = sig_scan(
        "MASTER SUPPLY AGREEMENT - SIGNATURES",
        ["Agreement 2020/091, made on 3 November 2020.",
         f"The Supplier: {OURS}", f"The Customer: {BRENLOW}"],
        subtitle="Page 3 of 3",
        blocks=[
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "R. Aldbury",
             "title": "Sales Director", "date": "3 November 2020"},
            {"for": f"SIGNED for and on behalf of {BRENLOW}", "name": "G. Ravenscar",
             "title": "Managing Director", "date": "3 November 2020"},
        ], skew=0.35)
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="plain",
                      image_pages={3: signature}, title="Master Supply Agreement 2020/091",
                      author="Halbrook sales (invented)")


def build_brenlow_termination_fax(path):
    """A faxed, coffee stained scan terminating the Brenlow master with a past end date."""
    page = sig_scan(
        f"{BRENLOW_SHORT}",
        [f"{BRENLOW_ADDR}",
         "",
         "24 March 2026",
         "",
         f"{OURS}, {OURS_ADDR}",
         "For the attention of the Sales Director",
         "",
         "MASTER SUPPLY AGREEMENT DATED 3 NOVEMBER 2020 - NOTICE OF TERMINATION",
         "",
         "We refer to the Master Supply Agreement dated 3 November 2020 between our companies, your "
         "reference 2020/091.",
         "We hereby give notice under clause 12.1 to terminate that Agreement for convenience. In "
         "accordance with clause 12.1 the Agreement will end on 30 April 2026.",
         "Orders placed before that date will be paid on the existing terms. Please close the "
         "account on 30 April 2026 and issue a final statement.",
         "",
         "Yours faithfully"],
        blocks=[{"for": f"for and on behalf of {BRENLOW_SHORT}", "name": "G. Ravenscar",
                 "title": "Managing Director", "date": "24 March 2026"}])
    page = add_fax_header(page, "FROM: BRENLOW DOCKYARD SVCS 01xxx 550142   24/03/2026 09:14   P.01/01")
    page = add_coffee_ring(page, centre=(900, 1230), radius=195)
    page = add_noise(page, seed=21, amount=13, blur=0.6)
    return native_pdf(path, [{"title": None, "paras": []}], image_pages={1: page},
                      title="Fax - notice of termination", author="scanner (invented)")


# =====================================================================
# Account D - Trentmoor Housing Partnership
# =====================================================================

THP_REF = "THP/2023/ELEC-11"

THP_CLAUSES = [
    ("2 THE PARTIES; 3 COMMENCEMENT AND TERM", [
        f"2.1 This Agreement is made between {TRENTMOOR_PRINTED}, a company registered in England "
        f"and Wales with number {TRENTMOOR_NO} whose registered office is at {TRENTMOOR_ADDR} (\"the "
        "Customer\"), and",
        f"2.2 {OURS}, a company registered in England and Wales with number {OURS_NO} whose "
        f"registered office is at {OURS_ADDR} (\"the Supplier\").",
        "2.3 The Customer is a registered provider of social housing. The Supplier is a distributor "
        "of electrical, lighting and cable products.",
        "3.1 This Agreement commences on 1 October 2023 (\"the Commencement Date\").",
        "3.2 The initial term is three years from the Commencement Date, ending on 30 September 2026.",
        "3.3 At the end of the initial term this Agreement continues until terminated by either "
        "party under clause 22.1.",
        "3.4 This Agreement is executed on the date written on the signature page.",
    ]),
    ("4 STRUCTURE OF THE AGREEMENT AND ORDER OF PRECEDENCE", [
        "4.1 This Agreement consists of these Conditions, Schedule 1 (Product Categories), Schedule "
        "2 (Price Matrix), Schedule 3 (Delivery Sites), Annex A (Notices) and Annex B (Escalation).",
        "4.2 If there is a conflict between them, the order of precedence is: these Conditions; "
        "Schedule 2; Schedule 1; Schedule 3; the Order.",
        "4.3 Schedule 2 is issued separately as a spreadsheet under clause 8.2 and is valid only for "
        "the period stated in it. The remaining parts of this Agreement have no separate expiry and "
        "run for the term of this Agreement.",
        "4.4 The expiry of Schedule 2 does not end this Agreement.",
    ]),
    ("5 SCOPE OF SUPPLY", [
        "5.1 All Orders for electrical, lighting and cable products placed by the Customer with the "
        "Supplier are placed under this Agreement.",
        "5.2 The product categories are described in Schedule 1. That description is indicative and "
        "does not limit clause 5.1.",
        "5.3 The Agreement applies to deliveries in the United Kingdom.",
        "5.4 The Customer and any body corporate under its control may place Orders. The Customer "
        "remains responsible for payment.",
        "5.5 The Supplier is one of two approved distributors. No volume is guaranteed.",
    ]),
    ("6 ORDERING", [
        "6.1 Orders are placed through the Customer's purchasing system or by electronic mail to the "
        "address in Annex A.",
        "6.2 An Order is accepted when the Supplier acknowledges it in writing or despatches the "
        "goods, whichever happens first.",
        "6.3 The Supplier shall acknowledge each Order within one Business Day.",
        "6.4 The Supplier's own conditions of sale do not apply to an Order.",
    ]),
    ("7 DELIVERY, CARRIAGE AND PACKAGING", [
        "7.1 Delivery is to the Site stated in the Order during the Working Hours stated in Schedule "
        "3.",
        "7.2 Time of delivery is not of the essence but the Supplier shall use reasonable endeavours "
        "to meet the requested date.",
        "7.3 Delivery is free of carriage to the Sites listed in Schedule 3 on Orders with a net "
        "value of GBP 200 or more. On Orders below that value, and on deliveries to any other "
        "address, carriage is charged at cost.",
        "7.4 Packaging is included in the price. The Supplier shall remove packaging waste from "
        "Sites on request at no charge.",
    ]),
    ("8 PRICES AND THE PRICE MATRIX", [
        "8.1 Prices are exclusive of value added tax.",
        "8.2 Prices are those set out in Schedule 2 (Price Matrix), which is issued separately as a "
        "spreadsheet and is valid for the period stated in it. A replacement Schedule 2 takes effect "
        "on the date stated in the replacement.",
        "8.3 The Supplier shall issue a proposed replacement Schedule 2 at least sixty days before "
        "the current Schedule 2 expires.",
        "8.4 If no Schedule 2 is in force, prices are the Supplier's published list price less 22 "
        "per cent until a replacement Schedule 2 is agreed.",
        "8.5 Prices for items not listed in Schedule 2 are quoted on request.",
    ]),
    ("9 PAYMENT", [
        "9.1 The Customer shall pay each correctly rendered invoice within 60 days from the end of "
        "the month in which the invoice is dated.",
        "9.2 Payment is made by bank transfer to the account notified in writing.",
        "9.3 The Supplier may charge interest on sums overdue at 2 per cent above base rate.",
    ]),
    ("10 INVOICING AND DISPUTED INVOICES", [
        "10.1 Each invoice shall quote the Order number and the Site.",
        "10.2 The Customer shall notify a disputed invoice within twenty Business Days of receipt "
        "and shall pay the undisputed part on the due date.",
        "10.3 The parties shall use reasonable endeavours to resolve a disputed invoice within "
        "thirty days.",
    ]),
    ("11 TITLE AND RISK", [
        "11.1 Risk in the goods passes to the Customer on delivery to the Site.",
        "11.2 Title passes on payment in full for the goods concerned.",
        "11.3 Until title passes the Customer shall store the goods so that they remain "
        "identifiable as the Supplier's property.",
    ]),
    ("12 QUALITY, WARRANTY AND DEFECTIVE GOODS", [
        "12.1 The goods shall conform with their description, be of satisfactory quality and comply "
        "with the applicable British and European standards.",
        "12.2 The Supplier shall replace or credit goods shown to be defective within twelve months "
        "of delivery, or within the manufacturer's warranty period if longer.",
        "12.3 Claims for shortage or damage in transit shall be notified within three Business Days.",
    ]),
    ("13 RETURNS AND SURPLUS", [
        "13.1 Unused stock items in original packaging may be returned within ninety days for credit "
        "subject to a handling charge of 10 per cent.",
        "13.2 Special order items are not returnable.",
        "13.3 The Supplier shall collect agreed returns from the Site within ten Business Days.",
    ]),
    ("14 COMPLIANCE WITH LAWS", [
        "14.1 Each party shall comply with all applicable laws, including the Bribery Act 2010 and "
        "the Modern Slavery Act 2015.",
        "14.2 The Supplier shall provide on request evidence of its compliance policies.",
        "14.3 A breach of this clause is a material breach for the purposes of clause 22.2.",
    ]),
    ("15 HEALTH, SAFETY AND SITE RULES", [
        "15.1 The Supplier's personnel shall comply with the Customer's site rules when attending a "
        "Site.",
        "15.2 The Supplier shall provide safety data sheets for hazardous goods before delivery.",
        "15.3 The Supplier shall report to the Customer any accident occurring at a Site within "
        "twenty four hours.",
    ]),
    ("16 INSURANCE", [
        "16.1 The Supplier shall maintain public liability insurance of not less than GBP 10,000,000 "
        "and product liability insurance of not less than GBP 5,000,000 for each occurrence.",
        "16.2 The Supplier shall provide evidence of that insurance on request.",
    ]),
    ("17 CONFIDENTIALITY", [
        "17.1 Each party shall keep confidential the other's confidential information and use it "
        "only for the purposes of this Agreement.",
        "17.2 This clause does not apply to information which is public through no fault of the "
        "receiving party or which must be disclosed by law.",
        "17.3 This clause continues for three years after this Agreement ends.",
    ]),
    ("18 DATA PROTECTION", [
        "18.1 Each party shall comply with applicable data protection law in respect of personal "
        "data processed under this Agreement.",
        "18.2 The parties do not expect either to act as a processor for the other. If that changes "
        "they shall enter into written processing terms.",
    ]),
    ("19 INTELLECTUAL PROPERTY", [
        "19.1 Nothing in this Agreement transfers intellectual property rights.",
        "19.2 The Supplier warrants that the supply of the goods does not infringe a third party's "
        "intellectual property rights.",
    ]),
    ("20 LIMITATION OF LIABILITY", [
        "20.1 Nothing limits liability for death or personal injury caused by negligence, for fraud "
        "or for any liability which cannot lawfully be limited.",
        "20.2 Neither party is liable for loss of profit, loss of contract or indirect or "
        "consequential loss.",
        "20.3 Subject to clauses 20.1 and 20.2, each party's total liability in any period of twelve "
        "months is limited to the sums invoiced under this Agreement in that period.",
    ]),
    ("21 FORCE MAJEURE", [
        "21.1 Neither party is liable for a failure to perform caused by an event beyond its "
        "reasonable control, provided it notifies the other promptly.",
        "21.2 If the event continues for more than sixty days either party may terminate this "
        "Agreement on written notice.",
    ]),
    ("22 TERMINATION", [
        "22.1 After the initial term either party may terminate this Agreement for convenience by "
        "giving the other not less than twelve months' written notice.",
        "22.2 Either party may terminate immediately by written notice if the other commits a "
        "material breach which is not remedied within thirty days of notice requiring remedy.",
        "22.3 Either party may terminate immediately if the other becomes insolvent.",
        "22.4 Termination does not affect Orders already accepted, which are completed on the terms "
        "of this Agreement.",
    ]),
    ("23 CONSEQUENCES OF TERMINATION", [
        "23.1 On termination each party shall return or destroy the other's confidential "
        "information.",
        "23.2 Accrued rights and clauses 17, 20 and 28 survive termination.",
    ]),
    ("24 ASSIGNMENT AND SUBCONTRACTING", [
        "24.1 Neither party may assign this Agreement without the other's written consent, not to be "
        "unreasonably withheld.",
        "24.2 The Supplier may use its own group companies to fulfil Orders but remains responsible "
        "for performance.",
    ]),
    ("25 NOTICES", [
        "25.1 Notices shall be in writing and sent to the addresses in Annex A.",
        "25.2 A notice sent by recorded delivery is treated as received on the second Business Day "
        "after posting.",
        "25.3 A notice of termination may not be given by electronic mail alone.",
    ]),
    ("26 ENTIRE AGREEMENT AND VARIATION", [
        "26.1 This Agreement is the entire agreement between the parties in relation to the products "
        "described in Schedule 1 and supersedes all earlier discussions.",
        "26.2 This Agreement does not affect the Supply Agreement (Meter Cabinets) dated 4 July 2022 "
        "between the parties, which continues in force for the products listed in its Annex.",
        "26.3 No variation is effective unless in writing and signed by an authorised signatory of "
        "each party.",
    ]),
    ("27 THIRD PARTY RIGHTS, WAIVER AND SEVERANCE", [
        "27.1 A person who is not a party has no right to enforce this Agreement.",
        "27.2 A failure to enforce a term is not a waiver of it.",
        "27.3 If a provision is held to be unenforceable the remainder continues in force.",
    ]),
    ("28 GOVERNING LAW AND JURISDICTION", [
        "28.1 This Agreement and any dispute arising out of it are governed by the law of England "
        "and Wales.",
        "28.2 The courts of England and Wales have exclusive jurisdiction.",
    ]),
]


def build_thp_master(path):
    """Forty two pages. Pages 1 to 3 deliberately carry no party names in full."""
    head = "MASTER SUPPLY AGREEMENT"
    pages = [
        # p1 cover sheet - no company names anywhere on it
        {"title": None, "rule": False, "style": "legal", "paras": [
            "", "", "", "",
            "##                         MASTER SUPPLY AGREEMENT",
            "",
            f"##                        Contract reference {THP_REF}",
            "",
            "                          Electrical, lighting and cable products",
            "",
            "                          Execution version",
            "",
            "                          Issued 5 September 2023",
            "", "", "", "", "", "",
            "Document control: THP-LEGAL-2023-11 rev 6. Printed 5 September 2023.",
            "Custodian: contracts team, extension 2214. Retention: seven years from expiry.",
            "This document is confidential and is issued to named recipients only.",
        ]},
        # p2 contents
        {"title": "CONTENTS", "style": "legal", "head": THP_REF, "head_right": "Page 2 of 42",
         "paras": ["1 Definitions and interpretation ......... 3",
                   "2 The parties ......... 4",
                   "3 Commencement and term ......... 4",
                   "4 Structure and order of precedence ......... 5",
                   "5 Scope of supply ......... 6",
                   "6 Ordering ......... 7",
                   "7 Delivery, carriage and packaging ......... 8",
                   "8 Prices and the price matrix ......... 9",
                   "9 Payment ......... 10",
                   "10 Invoicing and disputed invoices ......... 11",
                   "11 Title and risk ......... 12",
                   "12 Quality, warranty and defective goods ......... 13",
                   "13 Returns and surplus ......... 14",
                   "14 Compliance with laws ......... 15",
                   "15 Health, safety and site rules ......... 16",
                   "16 Insurance ......... 17",
                   "17 Confidentiality ......... 18",
                   "18 Data protection ......... 19",
                   "19 Intellectual property ......... 20",
                   "20 Limitation of liability ......... 21",
                   "21 Force majeure ......... 22",
                   "22 Termination ......... 23",
                   "23 Consequences of termination ......... 24",
                   "24 Assignment and subcontracting ......... 25",
                   "25 Notices ......... 26",
                   "26 Entire agreement and variation ......... 27",
                   "27 Third party rights, waiver and severance ......... 28",
                   "28 Governing law and jurisdiction ......... 29",
                   "Schedule 1 Product categories ......... 30",
                   "Schedule 2 Price matrix (issued separately) ......... 34",
                   "Schedule 3 Delivery sites ......... 36",
                   "Annex A Notices ......... 39",
                   "Annex B Escalation contacts ......... 40",
                   "Signature page ......... 41"]},
        # p3 definitions - names the parties only by defined term
        {"title": "1 DEFINITIONS AND INTERPRETATION", "style": "legal", "head": THP_REF,
         "head_right": "Page 3 of 42", "paras": [
             "1.1 In this Agreement the following definitions apply.",
             "\t\"Agreement\" means these Conditions together with the Schedules and Annexes.",
             "\t\"Business Day\" means a day other than a Saturday, Sunday or public holiday in "
             "England.",
             "\t\"Conditions\" means clauses 1 to 28 of this Agreement.",
             "\t\"the Customer\" means the party identified as the Customer on the signature page "
             "and in clause 2.1.",
             "\t\"Order\" means an order for goods placed by the Customer under clause 6.",
             "\t\"Price Matrix\" means Schedule 2 as issued from time to time under clause 8.2.",
             "\t\"Schedule\" means a schedule to this Agreement.",
             "\t\"Site\" means a delivery point listed in Schedule 3.",
             "\t\"the Supplier\" means the party identified as the Supplier on the signature page "
             "and in clause 2.2.",
             "\t\"Working Hours\" means the hours stated for a Site in Schedule 3.",
             "1.2 Clause and Schedule headings do not affect interpretation.",
             "1.3 A reference to a statute includes any amendment or re-enactment of it.",
             "1.4 A reference to writing includes electronic mail except where clause 25.3 applies.",
             "1.5 Words in the singular include the plural and vice versa.",
         ]},
    ]
    page_no = 4
    for title, paras in THP_CLAUSES:
        pages.append({"title": title, "style": "legal", "head": THP_REF,
                      "head_right": f"Page {page_no} of 42", "paras": paras})
        page_no += 1
    # Schedule 1, pages 30-33
    schedule_1 = [
        ("SCHEDULE 1 - PRODUCT CATEGORIES (1 of 4)", [
            "S1.1 The categories below describe the goods normally ordered under this Agreement.",
            "S1.2 Category A - Cable: single core, twin and earth, SWA armoured, fire performance "
            "cable, flexible cable, data cable.",
            "S1.3 Category B - Cable management: steel and PVC trunking, tray, basket, conduit, "
            "fixings and accessories.",
            "S1.4 Category C - Wiring accessories: sockets, switches, back boxes, fused connection "
            "units, cable outlets.",
        ]),
        ("SCHEDULE 1 - PRODUCT CATEGORIES (2 of 4)", [
            "S1.5 Category D - Lighting: internal luminaires, emergency luminaires, external and "
            "amenity lighting, lamps and control gear.",
            "S1.6 Category E - Low voltage distribution: consumer units, distribution boards, "
            "circuit protection, isolators, metering enclosures.",
            "S1.7 Category F - Heating and ventilation controls: room controls, immersion heaters, "
            "extract fans.",
        ]),
        ("SCHEDULE 1 - PRODUCT CATEGORIES (3 of 4)", [
            "S1.8 Category G - Test equipment and consumables: test instruments, calibration, tools, "
            "tapes, cleaning and site consumables.",
            "S1.9 Category H - Fire and security: detectors, sounders, panels, door entry, access "
            "control components.",
            "S1.10 Category J - Renewables and electric vehicle charging: charge points, mounting "
            "and associated protection.",
        ]),
        ("SCHEDULE 1 - PRODUCT CATEGORIES (4 of 4)", [
            "S1.11 This Schedule is indicative. An Order for a product outside these categories is "
            "still placed under this Agreement if the Supplier accepts it.",
            "S1.12 This Schedule has no separate expiry date and runs for the term of this "
            "Agreement.",
            "S1.13 Meter cabinets and associated enclosures are excluded from this Schedule and are "
            "supplied under the Supply Agreement (Meter Cabinets) dated 4 July 2022 referred to in "
            "clause 26.2.",
        ]),
    ]
    for title, paras in schedule_1:
        pages.append({"title": title, "style": "legal", "head": THP_REF,
                      "head_right": f"Page {page_no} of 42", "paras": paras})
        page_no += 1
    schedule_2 = [
        ("SCHEDULE 2 - PRICE MATRIX (1 of 2)", [
            "S2.1 Schedule 2 is not reproduced in this document. It is issued separately as a "
            "spreadsheet under clause 8.2 and forms part of this Agreement while it is in force.",
            "S2.2 The Schedule 2 in force at the date of this Agreement was valid from 1 October "
            "2023 to 31 December 2023 and has been replaced annually since.",
            "S2.3 Each Schedule 2 states the period for which it is valid. It expires at the end of "
            "that period whether or not this Agreement continues.",
            "S2.4 The Schedule 2 issued for the period 1 January 2026 to 31 December 2026 is the "
            "current Price Matrix.",
        ]),
        ("SCHEDULE 2 - PRICE MATRIX (2 of 2)", [
            "S2.5 The format of Schedule 2 is: product group, product code, description, list price, "
            "contract discount and net contract price.",
            "S2.6 Where a product code appears in Schedule 2 the net contract price in it prevails "
            "over any other price quoted, subject to clause 4.2.",
            "S2.7 If Schedule 2 expires without replacement, clause 8.4 applies until a replacement "
            "is agreed. The expiry of Schedule 2 does not end this Agreement.",
        ]),
    ]
    for title, paras in schedule_2:
        pages.append({"title": title, "style": "legal", "head": THP_REF,
                      "head_right": f"Page {page_no} of 42", "paras": paras})
        page_no += 1
    schedule_3 = [
        ("SCHEDULE 3 - DELIVERY SITES (1 of 3)", [
            "S3.1 Cawdale Central Stores, Larkhall Road, Cawdale. Working Hours 07:00 to 16:00 "
            "Monday to Friday.",
            "S3.2 Trentmoor Repairs Depot, Fettle Way, Cawdale. Working Hours 07:00 to 15:30.",
            "S3.3 Netherford Housing Office, Foundry Lane, Netherford. Working Hours 08:30 to 16:00.",
        ]),
        ("SCHEDULE 3 - DELIVERY SITES (2 of 3)", [
            "S3.4 Larkhall Court, Larkhall Road, Cawdale (refurbishment site compound). Working "
            "Hours 07:30 to 16:00.",
            "S3.5 Kellerby Interchange site compound, Kellerby. Working Hours 07:00 to 17:00.",
            "S3.6 Sites may be added or removed by the Customer on ten Business Days' written "
            "notice.",
        ]),
        ("SCHEDULE 3 - DELIVERY SITES (3 of 3)", [
            "S3.7 Deliveries to an address which is not a Site are charged under clause 7.3.",
            "S3.8 This Schedule has no separate expiry date and runs for the term of this Agreement.",
        ]),
    ]
    for title, paras in schedule_3:
        pages.append({"title": title, "style": "legal", "head": THP_REF,
                      "head_right": f"Page {page_no} of 42", "paras": paras})
        page_no += 1
    pages.append({"title": "ANNEX A - NOTICES", "style": "legal", "head": THP_REF,
                  "head_right": f"Page {page_no} of 42", "paras": [
                      f"A1 Notices to the Customer: The Contracts Manager, {TRENTMOOR_PRINTED}, "
                      f"{TRENTMOOR_ADDR}.",
                      f"A2 Notices to the Supplier: The Commercial Director, {OURS}, {OURS_ADDR}.",
                      "A3 Orders are sent to the Supplier's contract desk at the electronic mail "
                      "address notified from time to time.",
                  ]})
    page_no += 1
    pages.append({"title": "ANNEX B - ESCALATION CONTACTS", "style": "legal", "head": THP_REF,
                  "head_right": f"Page {page_no} of 42", "paras": [
                      "B1 First level: the Customer's category buyer and the Supplier's account "
                      "manager.",
                      "B2 Second level: the Customer's Head of Procurement and the Supplier's "
                      "Regional Sales Manager.",
                      "B3 Third level: the Customer's Director of Assets and the Supplier's "
                      "Commercial Director.",
                      "B4 A dispute not resolved at third level within thirty days is referred to "
                      "clause 28.",
                  ]})
    page_no += 1
    signature = sig_scan(
        "MASTER SUPPLY AGREEMENT - SIGNATURE PAGE",
        [f"Contract reference {THP_REF}. Page 41 of 42.",
         f"The Customer: {TRENTMOOR_PRINTED}",
         f"The Supplier: {OURS}",
         "This Agreement is executed on the dates below and commences on 1 October 2023 in "
         "accordance with clause 3.1."],
        blocks=[
            {"for": f"SIGNED for and on behalf of {TRENTMOOR_PRINTED}", "name": "M. Elverstone",
             "title": "Director", "date": "5 September 2023"},
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "P. Nettlefold",
             "title": "Commercial Director", "date": "7 September 2023"},
        ], skew=0.25)
    pages.append({"title": None, "paras": []})   # page 41, replaced by the image
    pages.append({"title": None, "style": "legal", "head": THP_REF, "head_right": "Page 42 of 42",
                  "paras": ["This page is intentionally left blank.", "",
                            "Document control THP-LEGAL-2023-11 rev 6. End of document."]})
    assert len(pages) == 42, len(pages)
    return native_pdf(path, pages, style="legal", image_pages={41: signature},
                      title=f"Master Supply Agreement {THP_REF}",
                      author="Trentmoor contracts team (invented)")


def build_thp_schedule_2(path):
    rows = [
        [f"Contract reference {THP_REF}"],
        ["Schedule 2 - Price Matrix"],
        [f"Issued by {OURS} to {TRENTMOOR_PRINTED}"],
        ["Valid from", "01/01/2026", "Valid to", "31/12/2026"],
        ["Issued under clause 8.2 of the Master Supply Agreement dated 5 September 2023"],
        [],
        ["Product group", "Product code", "Description", "List price GBP", "Contract discount %",
         "Net contract price GBP"],
        ["A Cable", "CAB-TE-2515", "Twin and earth 2.5mm 100m drum", 92.40, 38.0, 57.29],
        ["A Cable", "CAB-SWA-1604", "SWA armoured 16mm 4 core per metre", 12.85, 34.0, 8.48],
        ["A Cable", "CAB-FP2002", "Fire performance cable 2 core 1.5mm per metre", 3.62, 30.0, 2.53],
        ["B Cable management", "TRK-100100", "Steel trunking 100x100 3m", 41.20, 39.0, 25.13],
        ["B Cable management", "TRY-RET300", "Return flange tray 300mm 3m", 58.90, 39.0, 35.93],
        ["C Wiring accessories", "ACC-SKT-2G", "Twin switched socket white moulded", 4.15, 45.0, 2.28],
        ["C Wiring accessories", "ACC-BB-35", "Metal back box 35mm", 1.62, 45.0, 0.89],
        ["D Lighting", "LGT-LED-BH18", "LED bulkhead 18W IP65", 46.30, 41.0, 27.32],
        ["D Lighting", "LGT-EM-3H", "Emergency LED 3 hour maintained", 62.75, 41.0, 37.02],
        ["E LV distribution", "DBD-TPN-12", "Distribution board 12 way TP&N", 388.00, 36.0, 248.32],
        ["E LV distribution", "MCB-B32", "MCB single pole type B 32A", 6.90, 44.0, 3.86],
        ["F Controls", "CTL-IMM-27", "Immersion heater 27 inch with thermostat", 34.10, 33.0, 22.85],
        ["G Consumables", "CON-TAPE-PVC", "PVC insulation tape box of 10", 7.40, 30.0, 5.18],
        ["H Fire and security", "FIR-SMK-OPT", "Optical smoke detector mains with battery", 28.60,
         35.0, 18.59],
        [],
        ["Notes"],
        ["1. This Schedule 2 replaces the Price Matrix for the period 01/01/2025 to 31/12/2025."],
        ["2. This Schedule 2 expires on 31/12/2026. Clause 8.4 (list less 22 per cent) applies "
         "until a replacement Schedule 2 is agreed."],
        ["3. The expiry of this Schedule 2 does not end the Master Supply Agreement."],
        ["4. Meter cabinets are not priced here; see the Supply Agreement (Meter Cabinets) dated "
         "04/07/2022."],
        [DISCLAIMER],
    ]
    return xlsx(path, "Schedule 2 2026", rows,
                widths={"A": 22, "B": 16, "C": 46, "D": 15, "E": 20, "F": 22},
                bold_rows=(7,),
                title_props={"title": "Schedule 2 Price Matrix 2026",
                             "creator": "Halbrook contract desk (invented)"})


def build_larkhall_site_agreement(path):
    """Five pages; the signature page (page 6) is not in the file."""
    ref = "THP/2026/SITE-04"
    pages = [
        {"title": "SITE SERVICES AGREEMENT - LARKHALL COURT REFURBISHMENT",
         "subtitle": f"Contract reference {ref}", "style": "plain",
         "head": "THE HOUSING PARTNERSHIP (TRENTMOOR) LIMITED", "head_right": f"{ref} p.1 of 6",
         "paras": [
             f"THIS SITE SERVICES AGREEMENT is dated 11 March 2026 and is made between "
             f"{TRENTMOOR_PRINTED} (company number {TRENTMOOR_NO}) of {TRENTMOOR_ADDR} (\"the "
             f"Customer\") and {OURS} (company number {OURS_NO}) of {OURS_ADDR} (\"the Supplier\").",
             "",
             "##BACKGROUND",
             "(A) The Customer is refurbishing 148 dwellings at Larkhall Court, Cawdale (\"the "
             "Works\").",
             "(B) The parties have an existing Master Supply Agreement dated 5 September 2023, "
             f"reference {THP_REF} (\"the Master Agreement\").",
             "(C) The parties wish to agree site specific arrangements for the Works.",
             "",
             "##1 SCOPE",
             "1.1 This Agreement applies only to goods ordered for the Works and delivered to the "
             "Larkhall Court site compound.",
             "1.2 Orders for any other site or purpose continue to be placed under the Master "
             "Agreement.",
         ]},
        {"title": None, "style": "plain",
         "head": "THE HOUSING PARTNERSHIP (TRENTMOOR) LIMITED", "head_right": f"{ref} p.2 of 6",
         "paras": [
             "##2 TERM",
             "2.1 This Agreement starts on 11 March 2026.",
             "2.2 It ends on practical completion of the Works or on 31 December 2027, whichever is "
             "the earlier.",
             "2.3 The current programme shows practical completion in October 2027. A change to the "
             "programme does not extend clause 2.2.",
             "",
             "##3 CONSOLIDATED DELIVERIES",
             "3.1 The Supplier shall deliver to the site compound twice each week on Tuesday and "
             "Thursday mornings.",
             "3.2 Deliveries are free of carriage whatever the value of the Order, in place of "
             "clause 7.3 of the Master Agreement.",
             "3.3 The Supplier shall provide a lockable stillage store on the compound at no charge.",
         ]},
        {"title": None, "style": "plain",
         "head": "THE HOUSING PARTNERSHIP (TRENTMOOR) LIMITED", "head_right": f"{ref} p.3 of 6",
         "paras": [
             "##4 PRICES AND PAYMENT",
             "4.1 Prices for the Works are those in Schedule 2 to the Master Agreement in force at "
             "the date of the Order.",
             "4.2 In place of clause 9.1 of the Master Agreement, the Customer shall pay invoices "
             "for the Works within 30 days from the end of the month in which the invoice is dated, "
             "to assist the Supplier with the site holding stock.",
             "4.3 The Supplier shall invoice weekly against the agreed schedule of rates.",
             "",
             "##5 SITE RULES AND SAFETY",
             "5.1 The Supplier's drivers shall report to the site office and comply with the "
             "principal contractor's rules.",
             "5.2 Deliveries outside the agreed windows may be refused.",
         ]},
        {"title": None, "style": "plain",
         "head": "THE HOUSING PARTNERSHIP (TRENTMOOR) LIMITED", "head_right": f"{ref} p.4 of 6",
         "paras": [
             "##6 PRECEDENCE",
             "6.1 This Agreement and the Master Agreement are to be read together.",
             "6.2 In the event of conflict between this Agreement and the Master Agreement, this "
             "Agreement prevails in respect of the Works, and the Master Agreement prevails for "
             "everything else.",
             "6.3 This Agreement does not vary the Master Agreement for any other site and does not "
             "extend or shorten its term.",
             "",
             "##7 TERMINATION",
             "7.1 Either party may end this Agreement on thirty days' written notice.",
             "7.2 Ending this Agreement does not end the Master Agreement.",
         ]},
        {"title": None, "style": "plain",
         "head": "THE HOUSING PARTNERSHIP (TRENTMOOR) LIMITED", "head_right": f"{ref} p.5 of 6",
         "paras": [
             "##8 LIABILITY AND INSURANCE",
             "8.1 Clauses 16 and 20 of the Master Agreement apply to this Agreement.",
             "",
             "##9 GOVERNING LAW",
             "9.1 This Agreement is governed by the law of England and Wales and the courts of "
             "England and Wales have exclusive jurisdiction.",
             "",
             "This Agreement is executed as of the date of the last signature below.",
             "",
             "[SIGNATURE PAGE FOLLOWS]",
         ]},
    ]
    return native_pdf(path, pages, style="plain", title=f"Site Services Agreement {ref}",
                      author="Trentmoor contracts team (invented)")


def build_detached_signature_page(path):
    """A washed out scan of the missing page 6 of the Larkhall Court site agreement."""
    ref = "THP/2026/SITE-04"
    page = sig_scan(
        "SITE SERVICES AGREEMENT - LARKHALL COURT REFURBISHMENT",
        [f"Contract reference {ref}. Page 6 of 6 - signature page.",
         "Executed as of the date of the last signature below.",
         f"The Customer: {TRENTMOOR_PRINTED}",
         f"The Supplier: {OURS}",
         "The text of clauses 1 to 9 is on pages 1 to 5 and is not reproduced on this page."],
        blocks=[
            {"for": f"SIGNED for and on behalf of {TRENTMOOR_PRINTED}", "name": "M. Elverstone",
             "title": "Director", "date": "11 March 2026"},
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "P. Nettlefold",
             "title": "Commercial Director", "date": "13 March 2026"},
        ], skew=-1.1)
    page = add_noise(page, seed=33, amount=19, low_contrast=True, blur=0.9)
    return native_pdf(path, [{"title": None, "paras": []}], image_pages={1: page},
                      title="scan", author="scanner (invented)")


def build_nda_plus_supply(path):
    """One PDF holding two different agreements: a scanned NDA then a native supply agreement."""
    nda_1 = scan_page(
        "MUTUAL NON-DISCLOSURE AGREEMENT",
        [f"THIS AGREEMENT is made on 14 June 2022 between {TRENTMOOR_PRINTED} (company number "
         f"{TRENTMOOR_NO}) and {OURS} (company number {OURS_NO}).",
         "1. Each party may disclose confidential information to the other for the purpose of "
         "discussing a possible supply arrangement for electrical products.",
         "2. Each party shall keep the other's confidential information secret and use it only for "
         "that purpose.",
         "3. This Agreement starts on 14 June 2022 and continues for five years, ending on 13 June "
         "2027.",
         "4. This Agreement does not oblige either party to buy or sell anything, does not set any "
         "price and does not govern any order.",
         "5. Confidential information does not include information which is public through no fault "
         "of the receiving party.",
         "6. The law of England and Wales applies."],
        skew=0.8)
    nda_2 = sig_scan(
        "MUTUAL NON-DISCLOSURE AGREEMENT - SIGNATURES",
        ["Signed by the parties on the date written on page 1.",
         f"Party 1: {TRENTMOOR_PRINTED}", f"Party 2: {OURS}"],
        blocks=[
            {"for": f"SIGNED for and on behalf of {TRENTMOOR_PRINTED}", "name": "M. Elverstone",
             "title": "Director", "date": "14 June 2022"},
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "A. Whitcombe",
             "title": "Finance Director", "date": "14 June 2022"},
        ], skew=-0.5)
    supply_pages = [
        {"title": "SUPPLY AGREEMENT (METER CABINETS)", "style": "plain",
         "head": f"{OURS} - agreement 2022/117", "head_right": "Page 1 of 3",
         "paras": [
             f"THIS AGREEMENT is made on 4 July 2022 between {OURS} (company number {OURS_NO}) of "
             f"{OURS_ADDR} (\"the Supplier\") and {TRENTMOOR_PRINTED} (company number "
             f"{TRENTMOOR_NO}) of {TRENTMOOR_ADDR} (\"the Customer\").",
             "",
             "##1 WHAT IS COVERED",
             "1.1 This Agreement covers the supply of meter cabinets, meter boxes and associated "
             "enclosures and mounting kits listed in the Annex, and nothing else.",
             "1.2 Orders for any other product are not placed under this Agreement.",
             "",
             "##2 TERM",
             "2.1 This Agreement starts on 1 August 2022 and continues until either party gives the "
             "other not less than six months' written notice.",
             "",
             "##3 PRICES AND PAYMENT",
             "3.1 Prices are those in the Annex, fixed until 31 March 2023 and reviewed annually "
             "thereafter on sixty days' notice.",
             "3.2 The Customer shall pay each invoice within 45 days of the date of invoice.",
             "",
             "##4 DELIVERY",
             "4.1 Carriage is included in the prices in the Annex for deliveries within the United "
             "Kingdom.",
         ]},
        {"title": None, "style": "plain", "head": f"{OURS} - agreement 2022/117",
         "head_right": "Page 2 of 3",
         "paras": [
             "##5 QUALITY",
             "5.1 Cabinets shall comply with the relevant meter operator specification current at "
             "the date of the order.",
             "##6 TERMINATION",
             "6.1 Either party may terminate under clause 2.1 or immediately for an unremedied "
             "material breach.",
             "##7 PRECEDENCE",
             "7.1 This Agreement prevails over any purchase order for the products listed in the "
             "Annex.",
             "##8 ENTIRE AGREEMENT",
             "8.1 This Agreement is the entire agreement between the parties about the products "
             "listed in the Annex.",
             "##9 LAW", "9.1 The law of England and Wales applies.",
             "",
             "##ANNEX - PRODUCTS AND PRICES",
             "MC-SGL-01 Single phase surface meter cabinet, GBP 41.80 each.",
             "MC-SGL-02 Single phase recessed meter cabinet, GBP 48.20 each.",
             "MC-TPH-01 Three phase surface meter cabinet, GBP 96.40 each.",
             "MC-GAS-01 Gas meter box with lock, GBP 33.10 each.",
             "MC-MNT-01 Mounting kit and backboard, GBP 12.60 each.",
             "",
             f"SIGNED for and on behalf of {OURS}: R. Aldbury, Sales Director. Date: 4 July 2022.",
             f"SIGNED for and on behalf of {TRENTMOOR_PRINTED}: M. Elverstone, Director. "
             "Date: 4 July 2022.",
         ]},
        {"title": "SUPPLY AGREEMENT (METER CABINETS) - CONTINUATION", "style": "plain",
         "head": f"{OURS} - agreement 2022/117", "head_right": "Page 3 of 3",
         "paras": [
             "This page records the parties' service contacts and is part of the Supply Agreement "
             "(Meter Cabinets) dated 4 July 2022.",
             "Customer contact: the Contracts Manager, Trentmoor Civic Offices, Cawdale.",
             "Supplier contact: the account manager, Halbrook House, Ellersby.",
             "Nothing on this page varies the Agreement.",
         ]},
    ]
    pages = [{"title": None, "paras": []}, {"title": None, "paras": []}] + supply_pages
    return native_pdf(path, pages, style="plain", image_pages={1: nda_1, 2: nda_2},
                      signed_pages={4: 2}, title="scan0012",
                      author="scanner (invented)")


# =====================================================================
# Shared, unmatched and supplier side documents
# =====================================================================

def build_joint_site_letter(path):
    """Names two accounts: it belongs in both folders."""
    pages = [{
        "title": "JOINT SITE DELIVERY ARRANGEMENT - KELLERBY INTERCHANGE", "style": "letter",
        "paras": [
            "Dated 20 April 2026",
            "",
            "PARTIES",
            f"(1) {OURS} of {OURS_ADDR} (\"the Distributor\");",
            f"(2) {STURMORE_LTD} of {STURMORE_ADDR} (\"SRG\"); and",
            f"(3) {TRENTMOOR_PRINTED} of {TRENTMOOR_ADDR} (\"THP\").",
            "",
            "BACKGROUND",
            "(A) SRG and THP are jointly procuring the electrical works at the Kellerby Interchange "
            "development, where SRG is refurbishing the station platforms and THP is building 96 "
            "dwellings above them.",
            "(B) Each of SRG and THP has its own agreement with the Distributor: SRG under the "
            "Master Supply Agreement dated 22 February 2021 (reference SRG/PROC/2021/114) and THP "
            f"under the Master Supply Agreement dated 5 September 2023 (reference {THP_REF}).",
            "(C) The parties wish to consolidate deliveries to a single site compound.",
            "",
            "AGREED TERMS",
            "1. This arrangement applies only to orders for the Kellerby Interchange site, whether "
            "placed by SRG or by THP.",
            "2. The Distributor shall deliver to the Kellerby Interchange site compound free of "
            "carriage whatever the value of the order, in place of the carriage terms in each "
            "party's own agreement, and shall make one consolidated delivery each weekday morning.",
            "3. Each of SRG and THP remains responsible for paying for the goods it orders, on the "
            "payment terms of its own agreement with the Distributor. Neither is liable for the "
            "other's orders.",
            "4. Prices remain those under each party's own agreement. This arrangement sets no "
            "prices and creates no volume commitment.",
            "5. This arrangement starts on 20 April 2026 and ends on practical completion of the "
            "Kellerby Interchange works, which is programmed for 30 June 2027.",
            "6. Save as set out above, the Master Supply Agreement dated 22 February 2021 and the "
            f"Master Supply Agreement dated 5 September 2023 continue unchanged and each governs the "
            "trade of its own party.",
            "7. This arrangement is governed by the law of England and Wales.",
            "",
            f"SIGNED for and on behalf of {OURS}: P. Nettlefold, Commercial Director. "
            "Date: 20 April 2026.",
            f"SIGNED for and on behalf of {STURMORE_LTD}: T. Vessey, Head of Procurement. "
            "Date: 20 April 2026.",
            f"SIGNED for and on behalf of {TRENTMOOR_PRINTED}: M. Elverstone, Director. "
            "Date: 22 April 2026.",
        ]}]
    return native_pdf(path, pages, signed_pages={1: 3}, style="letter",
                      title="Joint site delivery arrangement - Kellerby Interchange",
                      author="Halbrook commercial (invented)")


def build_fenwold_master(path):
    """A perfectly good master for a company that is on no ERP row."""
    pages = [
        {"title": "MASTER SUPPLY AGREEMENT", "style": "plain",
         "head": f"{OURS} - agreement 2024/012", "head_right": "Page 1 of 3",
         "paras": [
             f"THIS AGREEMENT is made on 17 January 2024 between {OURS} (company number {OURS_NO}) "
             f"of {OURS_ADDR} (\"the Supplier\") and {FENWOLD} (company number {FENWOLD_NO}) of "
             f"{FENWOLD_ADDR} (\"the Customer\").",
             "",
             "##1 SCOPE",
             "1.1 All purchases of electrical, cable and industrial products by the Customer from "
             "the Supplier are made under this Agreement.",
             "1.2 The Agreement covers the Customer only, at its quarry and processing sites in the "
             "United Kingdom.",
             "",
             "##2 TERM",
             "2.1 This Agreement starts on 1 February 2024 and continues until either party gives "
             "not less than six months' written notice.",
             "",
             "##3 PRICES AND PAYMENT",
             "3.1 Prices are list price less 28 per cent, reviewed on 1 April each year.",
             "3.2 The Customer shall pay each invoice within 30 days from the end of the month in "
             "which the invoice is dated.",
             "",
             "##4 CARRIAGE",
             "4.1 Delivery is free of carriage on orders of GBP 400 or more; below that value "
             "carriage is charged at GBP 25.00.",
         ]},
        {"title": None, "style": "plain", "head": f"{OURS} - agreement 2024/012",
         "head_right": "Page 2 of 3",
         "paras": [
             "##5 QUALITY AND WARRANTY",
             "5.1 Twelve months from delivery, replacement or credit at the Supplier's option.",
             "##6 SITE CONDITIONS",
             "6.1 Deliveries to a working quarry are made to the weighbridge office only.",
             "##7 TITLE AND RISK", "7.1 Risk on delivery, title on payment in full.",
             "##8 LIABILITY", "8.1 No liability for indirect or consequential loss.",
             "##9 TERMINATION",
             "9.1 Either party may terminate under clause 2.1 or immediately for an unremedied "
             "material breach.",
             "##10 PRECEDENCE AND ENTIRE AGREEMENT",
             "10.1 This Agreement prevails over any purchase order and is the entire agreement "
             "between the parties about the supply of the products.",
             "##11 LAW", "11.1 The law of England and Wales applies.",
         ]},
    ]
    signature = sig_scan(
        "MASTER SUPPLY AGREEMENT - SIGNATURES",
        ["Agreement 2024/012, made on 17 January 2024.",
         f"The Supplier: {OURS}", f"The Customer: {FENWOLD}"],
        subtitle="Page 3 of 3",
        blocks=[
            {"for": f"SIGNED for and on behalf of {OURS}", "name": "R. Aldbury",
             "title": "Sales Director", "date": "17 January 2024"},
            {"for": f"SIGNED for and on behalf of {FENWOLD}", "name": "K. Ollerton",
             "title": "Finance Director", "date": "19 January 2024"},
        ], skew=0.5)
    return native_pdf(path, pages + [{"title": None, "paras": []}], style="plain",
                      image_pages={3: signature}, title="Master Supply Agreement 2024/012",
                      author="Halbrook sales (invented)")


def build_cadmere_framework(path):
    """Supplier side paper: we are the customer here, buying cable for resale."""
    pages = [
        {"title": "FRAMEWORK PURCHASE AGREEMENT", "style": "legal",
         "head": "CADMERE CABLE WORKS LIMITED", "head_right": "CCW/FPA/2024",
         "paras": [
             f"THIS FRAMEWORK PURCHASE AGREEMENT is dated 1 February 2024 and is made between "
             f"{CADMERE} (company number {CADMERE_NO}) of {CADMERE_ADDR} (\"the Supplier\") and "
             f"{OURS} (company number {OURS_NO}) of {OURS_ADDR} (\"the Customer\").",
             "",
             "##BACKGROUND",
             "(A) The Supplier manufactures cable and cable accessories.",
             "(B) The Customer is a distributor which buys those products for resale to its own "
             "customers.",
             "",
             "##1 SCOPE",
             "1.1 All purchases of the Supplier's products by the Customer are made under this "
             "Agreement.",
             "1.2 The Customer buys as principal for resale and not as an agent of the Supplier.",
             "",
             "##2 TERM",
             "2.1 This Agreement starts on 1 February 2024 and continues until either party gives "
             "the other not less than six months' written notice.",
             "",
             "##3 PRICES AND PAYMENT",
             "3.1 Prices are those in the Supplier's distributor price list less the distributor "
             "discount notified to the Customer, reviewed each 1 January.",
             "3.2 The Customer shall pay each invoice within 45 days from the end of the month in "
             "which the invoice is dated.",
             "3.3 The Supplier shall pay the Customer an annual volume rebate of 2 per cent of net "
             "purchases above GBP 1,200,000 in each calendar year.",
         ]},
        {"title": None, "style": "legal", "head": "CADMERE CABLE WORKS LIMITED",
         "head_right": "CCW/FPA/2024",
         "paras": [
             "##4 DELIVERY",
             "4.1 Delivery is DDP to the Customer's national distribution centre at Ellersby, "
             "Incoterms 2020.",
             "4.2 Full drum quantities are delivered carriage paid; part drums are charged at cost.",
             "##5 STOCK AND FORECASTS",
             "5.1 The Customer shall give the Supplier a rolling twelve week non binding forecast.",
             "5.2 The Supplier shall hold four weeks of the agreed stock profile.",
             "##6 QUALITY", "6.1 Products shall comply with the applicable British Standard and "
             "carry the Supplier's twelve month warranty, which the Customer may pass to its own "
             "customers.",
             "##7 RESALE AND BRANDING",
             "7.1 The Customer may resell the products under the Supplier's brand. The Customer is "
             "not appointed as an exclusive distributor and may sell competing products.",
             "##8 TERMINATION",
             "8.1 Either party may terminate under clause 2.1 or immediately for an unremedied "
             "material breach or insolvency.",
             "##9 PRECEDENCE",
             "9.1 This Agreement prevails over the Customer's purchase order conditions and over "
             "the Supplier's conditions of sale.",
             "##10 LAW", "10.1 The law of England and Wales applies.",
             "",
             f"SIGNED for and on behalf of {CADMERE}: S. Bemrose, Sales Manager. "
             "Date: 1 February 2024.",
             f"SIGNED for and on behalf of {OURS}: A. Whitcombe, Finance Director. "
             "Date: 5 February 2024.",
         ]},
    ]
    return native_pdf(path, pages, signed_pages={2: 2}, style="legal",
                      title="Framework Purchase Agreement CCW/FPA/2024",
                      author="Cadmere Cable Works (invented)")


# ---------------------------------------------------------------- junk files

MSG_BYTES = (
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 24
    + b"\x3e\x00\x03\x00\xfe\xff\x09\x00\x06\x00\x00\x00" + b"\x00" * 40
    + b"__nameid_version1.0\x00\x00__substg1.0_0037001F\x00\x00"
    + "RE: RE: amendment 2 - Sturmore\x00".encode("utf-16-le")
    + b"\x00" * 16 + b"__substg1.0_1000001F\x00\x00"
    + ("Hi - forwarding the amendment 2 draft again, attached as "
       "'Amendment 2 - tracked - DO NOT SEND.docx'. Sturmore have not come back on the 75 day "
       "payment ask. Do not send anything to them until legal have looked at it. "
       "Original message from T. Vessey 14/07/2026.\x00").encode("utf-16-le")
    + b"\x00" * 32 + b"__properties_version1.0\x00" + b"\x00" * 128
)

TEXT_PRETENDING_TO_BE_PDF = """CONTRACT NOTES - not a PDF, this file is plain text with the
wrong extension.

Sturmore: amendment 2 still with legal, do not quote the 500 pound carriage threshold.
Wexbury: notice served 14/08/26, ends 14/02/27. Ask sales whether we are replacing it.
Ardleigh: new MSA signed 15/09/25, ledger still shows the old Colverne name in places.
Trentmoor: schedule 2 price matrix runs out 31/12/26, start the replacement in October.
Brenlow: account closed 30/04/26.
Fenwold: not on the customer list in the ERP extract - ask finance which account this is.

(Someone saved this out of Notepad and typed .pdf on the end.)
"""


# =====================================================================
# Assembly
# =====================================================================

ERP_ROWS = [
    ("HAL-40118", STURMORE_ERP, "United Kingdom", ""),
    ("HAL-40119", STURMORE_DEPOT, "United Kingdom", "Northern Depot"),
    ("HAL-40204", WEXBURY, "United Kingdom", ""),
    ("HAL-40311", ARDLEIGH, "United Kingdom", ""),
    ("HAL-40390", TRENTMOOR_ERP, "United Kingdom", ""),
    ("HAL-40566", RAVENHEAD, "United Kingdom", ""),
]

OUR_ENTITIES = [
    (OURS, "current", "Our current trading and contracting entity; company number "
                      f"{OURS_NO}. All customer paper since June 2019 is in this name."),
    (OURS_OLD, "former", "Former name of the same company, changed on 3 June 2019. Appears on "
                         "agreements signed before that date; the company number is unchanged."),
    ("Halbrook Electrical Distribution (Scotland) Ltd", "current",
     "Our Scottish subsidiary; invoices a small number of northern accounts."),
]


def write_erp(path):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["account_number", "customer_account", "country", "site"])
        writer.writerows(ERP_ROWS)


def write_our_entities(path):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "status", "note"])
        writer.writerows(OUR_ENTITIES)


def make_pile(folder):
    folder = Path(folder)
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)

    inbox = folder / "00 TO FILE"
    sturmore = folder / "Customers" / "Sturmore Rail"
    wexbury = folder / "Customers" / "Wexbury"
    ardleigh = folder / "Customers" / "Ardleigh (ex Colverne)"
    trentmoor = folder / "Customers" / "Trentmoor"
    signed2025 = folder / "Signed 2025"
    misc = folder / "Misc"
    scans = folder / "scans to file"
    for directory in (inbox, sturmore / "2016 old agreement", sturmore / "MSA 2021",
                      sturmore / "PO's", wexbury, ardleigh / "old files",
                      ardleigh / "MSA drafts", ardleigh / "Brenlow", trentmoor,
                      signed2025, misc, scans):
        directory.mkdir(parents=True, exist_ok=True)

    created = []

    # ---- ERP record
    erp_path = folder / "erp_extract_2026-09-01.csv"
    write_erp(erp_path)
    created.append(erp_path)

    # ---- Account A: Sturmore Rail Group
    created.append(build_sturmore_2016(
        sturmore / "2016 old agreement" / "Sturmore supply agreement 2016 SIGNED.pdf"))
    created.append(build_sturmore_2021(
        sturmore / "MSA 2021" / "Sturmore MSA 2021 executed.pdf"))
    amendment_1 = build_sturmore_amendment_1(sturmore / "MSA 2021" / "Amendment 1 signed.pdf")
    created.append(amendment_1)
    # byte for byte duplicate of the amendment, filed somewhere else under a worse name
    duplicate = inbox / "FINAL FINAL signed (2).pdf"
    shutil.copyfile(amendment_1, duplicate)
    created.append(duplicate)
    # and a scanned, sideways copy of the same amendment
    amendment_scan = scan_page(
        "AMENDMENT No. 1 TO THE MASTER SUPPLY AGREEMENT DATED 22 FEBRUARY 2021",
        [f"Dated 6 June 2023, between {STURMORE_LTD} (\"SRG\") and {OURS} (\"the Supplier\").",
         "Reference SRG/PROC/2021/114/A1.",
         "1.1 With effect from 1 July 2023 clause 7.1 of the Agreement is deleted and replaced "
         "with: \"The Supplier shall be paid within 60 days from the end of the month in which the "
         "invoice is dated.\"",
         "1.2 No other provision of the Agreement is amended.",
         "2.1 The parties confirm that all purchases of Products by SRG and its Depots continue to "
         "be made under the Agreement.",
         "3.1 Governed by the law of England and Wales."],
        signatures=2, skew=1.2)
    amendment_scan = add_noise(amendment_scan, seed=5, amount=10)
    created.append(native_pdf(
        inbox / "scan0007.pdf", [{"title": None, "paras": []}],
        image_pages={1: amendment_scan.rotate(90, expand=True)},
        landscape_pages=(1,), title="scan0007", author="scanner (invented)"))
    created.append(docx(
        sturmore / "MSA 2021" / "Amendment 2 - tracked - DO NOT SEND.docx",
        AMENDMENT_2_DOCX,
        comments=["Sturmore have not agreed 75 days. Do not send this out.",
                  "Check the carriage threshold with the Commercial Director first."],
        author="Invented drafter, Halbrook commercial",
        tracked=[(4, "GBP 400 or more", "GBP 500 or more"),
                 (5, "within 90 days from the end of the month",
                  "within 75 days from the end of the month")],
        comment_anchors=[5, 4],
        created="2026-07-10T08:30:00Z", modified="2026-07-14T15:45:00Z",
        comment_author="Invented reviewer, Halbrook legal",
        comment_date="2026-07-14T16:02:00Z"))
    created.append(build_sturmore_po(sturmore / "PO's" / "PO88231 northern depot.pdf"))
    created.append(docx(
        sturmore / "Account notes (internal).docx", PLAYBOOK_DOCX,
        comments=["Update after the April price review."], comment_anchors=[3],
        author="Invented account manager, Halbrook",
        created="2026-03-03T09:15:00Z", modified="2026-03-03T17:40:00Z",
        comment_author="Invented sales manager, Halbrook",
        comment_date="2026-03-04T08:20:00Z"))
    msg_path = inbox / "RE_ RE_ amendment.msg"
    msg_path.write_bytes(MSG_BYTES)
    created.append(msg_path)

    # ---- Account B: Wexbury Utilities plc
    created.append(build_wexbury_framework(wexbury / "Framework 12-05-2022.pdf"))
    created.append(build_wexbury_draft(wexbury / "Signed final.pdf"))
    created.append(build_wexbury_confirmation(wexbury / "letter from WU Sept 24.pdf"))
    created.append(build_wexbury_rebate(wexbury / "rebate 2026.pdf"))
    created.append(build_wexbury_photo(wexbury / "IMG_2291.jpg"))
    created.append(build_wexbury_notice(wexbury / "notice served 14-08-26.pdf"))

    # ---- Account C: Ardleigh / Colverne / Brenlow
    created.append(build_colverne_2019(
        ardleigh / "old files" / "Colverne supply agreement 2019.pdf"))
    created.append(build_name_change_letter(ardleigh / "old files" / "name change letter.pdf"))
    v3 = _ardleigh_msa_body("VERSION 3", "12 June 2025", 30, "six", "250", "24.00")
    v4 = _ardleigh_msa_body("VERSION 4 (CLEAN)", "28 July 2025", 45, "twelve", "300", "28.00")
    # the redline carries the version 3 wording with tracked changes that produce version 4
    v4_redline = _ardleigh_msa_body("VERSION 4 (REDLINE AGAINST VERSION 3)", "28 July 2025", 30,
                                    "six", "250", "24.00")
    blank_blocks = [
        f"SIGNED for and on behalf of {OURS}: ______________  Name: ______________  "
        "Date: ______________",
        f"SIGNED for and on behalf of {ARDLEIGH_LTD}: ______________  Name: ______________  "
        "Date: ______________",
    ]
    created.append(docx(ardleigh / "MSA drafts" / "MSA v3.docx", v3 + blank_blocks,
                        author="Invented drafter, Halbrook legal",
                        created="2025-06-10T10:00:00Z", modified="2025-06-12T14:05:00Z"))
    created.append(docx(ardleigh / "MSA drafts" / "Copy of MSA v4 clean.docx", v4 + blank_blocks,
                        author="Invented drafter, Halbrook legal",
                        created="2025-07-24T09:00:00Z", modified="2025-07-28T11:30:00Z"))
    created.append(docx(
        ardleigh / "MSA drafts" / "MSA v4 redline.docx", v4_redline + blank_blocks,
        comments=["Ardleigh asked for 45 days at the meeting on 22 July; agreed subject to the "
                  "longer notice period.",
                  "Twelve months' notice is the trade off for the payment change - keep both or "
                  "neither."],
        author="Invented drafter, Halbrook legal",
        tracked=[(10, "within 30 days of the date of "
                  "the invoice", "within 45 days of the date of the invoice"),
                 (11, "GBP 250 or more. On Orders below that value a carriage charge of GBP 24.00 "
                  "applies", "GBP 300 or more. On Orders below that value a carriage charge of "
                  "GBP 28.00 applies"),
                 (16, "not less than six months' written notice",
                  "not less than twelve months' written notice")],
        created="2025-07-24T09:00:00Z", modified="2025-07-28T11:32:00Z",
        comment_anchors=[10, 16],
        comment_author="Invented reviewer, Ardleigh Marine Systems",
        comment_date="2025-07-28T15:10:00Z"))
    created.append(build_ardleigh_executed(signed2025 / "Ardleigh MSA signed 15-09-25.pdf"))
    created.append(build_brenlow_master(ardleigh / "Brenlow" / "Brenlow master 2020.pdf"))
    created.append(build_brenlow_termination_fax(ardleigh / "Brenlow" / "fax 24-03-26.pdf"))

    # ---- Account D: Trentmoor Housing Partnership
    created.append(build_thp_master(trentmoor / "THP master agreement 2023 FULL.pdf"))
    created.append(build_thp_schedule_2(trentmoor / "Schedule 2 price matrix 2026.xlsx"))
    created.append(build_larkhall_site_agreement(
        trentmoor / "Larkhall Court site agreement.pdf"))
    created.append(build_nda_plus_supply(trentmoor / "scan0012.pdf"))
    created.append(build_detached_signature_page(scans / "scan0031.pdf"))

    # ---- shared, unmatched, supplier side
    created.append(build_joint_site_letter(misc / "Kellerby Interchange joint letter.pdf"))
    created.append(build_fenwold_master(misc / "Fenwold master.pdf"))
    created.append(build_cadmere_framework(misc / "Cadmere framework (we buy).pdf"))

    # ---- junk
    empty = inbox / "new doc 2.pdf"
    empty.write_bytes(b"")
    created.append(empty)
    fake = inbox / "contract notes.pdf"
    fake.write_text(TEXT_PRETENDING_TO_BE_PDF, encoding="utf-8")
    created.append(fake)

    return created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "pile")
    parser.add_argument("--our-entities", type=Path, default=HERE / "inputs-our-entities.csv")
    args = parser.parse_args()
    created = make_pile(args.output)
    write_our_entities(args.our_entities)
    print(f"{len(created)} invented files written to {args.output}")
    print(f"our-entities written to {args.our_entities}")


if __name__ == "__main__":
    main()
