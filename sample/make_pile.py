#!/usr/bin/env python3
"""Regenerate invented development fixtures; never point this at a real contract pile.

Build-only dependencies: reportlab and Pillow. The enterprise kit does not need either.
Dates are fixed to make the September 2026 acceptance run reproducible.
"""
from pathlib import Path
import argparse
import csv
import io
import math
import textwrap
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

HERE = Path(__file__).resolve().parent
OURS = "Marrowgate Supply Ltd"
ACCOUNT1 = "Tallowfield Industries"
NORTH = "Tallowfield Industries (North) Limited"
PARENT = "Oxbrook Holdings plc"
GERMAN = "Tallowfield Industrie GmbH"
ACCOUNT2 = "Pellmont Logistics Group"
DISCLAIMER = "INVENTED DEVELOPMENT SAMPLE - NOT A REAL AGREEMENT"

SUPPLY = [
    ("Supply Agreement - General Terms", [
        f"1. Parties: {OURS} (Supplier) and {NORTH} (Customer).",
        "2. This Agreement takes effect on the date of the last signature below.",
        "3. General Terms continue until either party gives twelve months' written notice.",
        "4. All purchases of industrial supplies between the parties are placed under these General Terms.",
        "5. The Supplier may charge the Customer the cost of freight.",
        "6. Payment is due within 30 days of invoice.",
        "7. The General Terms cover the Customer and the named affiliate in Schedule 1 in the United Kingdom and Germany.",
        "8. Programme Terms apply only to orders for the Hexley Refit programme.",
        "9. Programme Terms prevail over General Terms in case of conflict.",
        f"10. This agreement is on {OURS} paper. No exclusivity or volume commitment is given.",
    ]),
    ("Programme Terms - Hexley Refit", [
        "P1. These Programme Terms form part of the Supply Agreement and start on its effective date.",
        "P2. These Programme Terms expire on 31 August 2024 without renewal.",
        "P3. For Hexley Refit orders, freight shall be charged.",
        "P4. Payment for Hexley Refit orders is due within 60 days of invoice.",
        "P5. Scope: industrial supplies for Hexley Refit in the United Kingdom only, for the Customer only.",
        "P6. General Terms continue after the Programme Terms expire.",
    ]),
    ("Schedule 1 - Named Affiliate and Group Identity", [
        f"S1. {NORTH} trades as {ACCOUNT1} and is a subsidiary of {PARENT}.",
        f"S2. Named affiliate: {GERMAN}, Germany, may order under the General Terms.",
        f"S3. {PARENT} is the parent only and does not order or guarantee payment under this Agreement.",
        "S4. This schedule has no separate expiry and forms part of the General Terms.",
    ]),
]
AMENDMENT = [("Amendment 1 to Supply Agreement", [
    f"1. Parties: {OURS} and {NORTH}.",
    "2. This amends the Supply Agreement dated 14 March 2019 between the parties.",
    "3. Effective 1 February 2026, the notice period in clause 3 of the General Terms is six months.",
    "4. The parties confirm that all their current purchases continue under the General Terms of that Agreement.",
    "5. No other term changes. This amendment continues for the life of the General Terms.",
    f"6. Prepared on {OURS} paper.",
    f"Signed for {OURS}: A. Wren. Date: 1 February 2026.",
    f"Signed for {NORTH}: B. Reed. Date: 1 February 2026.",
])]
NDA = [
    ("Mutual Non-Disclosure Agreement", [
        f"1. Parties: {PARENT} and {OURS}.",
        "2. This Agreement starts on 1 May 2019 and expires on 30 April 2022, a three-year term.",
        "3. Information disclosed for discussions must be kept confidential during that term.",
        "4. No obligation survives the expiry date. There is no automatic renewal.",
        "5. This Agreement does not govern orders, prices, purchases or the supply of goods.",
        "6. Only the signatories are covered; no country scope is specified.",
    ]),
    ("Mutual Non-Disclosure Agreement - Signatures", [
        f"Signed for {PARENT}: C. Linn. Date: 1 May 2019.",
        f"Signed for {OURS}: A. Wren. Date: 1 May 2019.",
        "The signatories agree to clauses 1 to 6 on page 1.",
    ]),
]
MSA = [
    "Master Services Agreement - draft dated 15 January 2026",
    f"1. Parties: {ACCOUNT2} (Customer) and {OURS} (Supplier).",
    "2. This draft is not agreed. It proposes that all service orders between the parties use these terms.",
    "3. Proposed start: 15 January 2026. Proposed duration: rolling until three months' notice.",
    "4. Payment is proposed within 45 days of invoice.",
    "5. Services: logistics support in the United Kingdom, for the signatories only.",
    f"6. This draft was prepared on {ACCOUNT2} paper.",
    f"Signed for {OURS}: __________________ Date: __________________",
    f"Signed for {ACCOUNT2}: __________________ Date: __________________",
]
PO = [("Purchase Order PL-2026-042", [
    f"Buyer: {ACCOUNT2}. Seller: {OURS}.",
    "Order date: 6 April 2026. Deliver by 13 April 2026.",
    "One purchase only: 20 invented transit trays, GBP 400 total, for a United Kingdom site.",
    "This purchase order contains no standard terms and establishes no terms for other purchases.",
    "No signature is required for this purchase order.",
])]
REBATE = [("2026 Rebate Letter", [
    f"To: {ACCOUNT2}. From: {OURS}.",
    "1. From 1 January 2026 until 31 December 2026, we will credit 2% of your invoiced purchases of logistics support.",
    "2. This letter sets only the rebate for that period. Other trading terms must be agreed separately.",
    "3. This is our commitment and requires no customer countersignature. Only the addressee is covered.",
    f"4. Prepared on {OURS} paper.",
    f"Signed for {OURS}: A. Wren. Date: 1 January 2026.",
])]
PROJECT = [("Hexley Works Site Agreement", [
    f"1. Parties: {NORTH} (Customer) and {OURS} (Supplier).",
    f"2. Prepared on {NORTH} paper.",
    "3. Effective 1 March 2026. Expires 31 March 2027 unless ended earlier on 30 days' written notice.",
    "4. All industrial supply orders for Hexley Works site in the United Kingdom are placed under this agreement.",
    "5. Orders outside Hexley Works continue under the Supply Agreement dated 14 March 2019.",
    "6. Freight is included in the price. Payment is due within 45 days of invoice.",
    "7. Only the signatories are covered. Neither has an exclusivity or volume commitment.",
    f"Signed for {NORTH}: B. Reed. Date: 1 March 2026.",
    f"Signed for {OURS}: A. Wren. Date: 1 March 2026.",
])]
PLAYBOOK = [
    f"Internal Account Playbook - {ACCOUNT1}",
    f"INTERNAL ONLY. Account: {ACCOUNT1}. Maintained by {OURS}; no customer signature.",
    "1. Working guidance from 1 February 2026 until replaced. This is not a contract.",
    "2. Margin practice: seek 18% gross margin on the regular industrial supplies basket.",
    "3. Pricing mechanics: use the internal market basket and review purchase costs quarterly.",
    "4. Low-volume urgent deliveries go ad hoc with the account manager's approval.",
    "5. Do not treat this margin practice as a customer agreement about freight charges.",
    "6. Coverage: United Kingdom account team only.",
]


def font(size=25, italic=False):
    stem = "LiberationSans-Italic.ttf" if italic else "LiberationSans-Regular.ttf"
    path = Path("/usr/share/fonts/truetype/liberation") / stem
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def scrawl(draw, xy, seed=1, scale=1.0):
    """Obviously synthetic pen strokes; they identify no real signatory."""
    x, y = xy
    points = [(x + i * 2 * scale, y + (math.sin(i / 4 + seed) * 16 + math.sin(i / 1.7) * 7) * scale)
              for i in range(105)]
    draw.line(points, fill=(24, 39, 97), width=max(2, round(3 * scale)))
    draw.line([(x, y + 20 * scale), (x + 210 * scale, y + 12 * scale)], fill=(24, 39, 97), width=2)


def scan_page(title, paragraphs, signatures=0, skew=0):
    image = Image.new("RGB", (1240, 1754), "#fcfbf5")
    draw = ImageDraw.Draw(image)
    y = 95
    for line in textwrap.wrap(title, 65):
        draw.text((75, y), line, font=font(31), fill="#18202c")
        y += 42
    y += 30
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, 82):
            draw.text((75, y), line, font=font(25), fill="#222222")
            y += 37
        y += 27
    for i in range(signatures):
        scrawl(draw, (100 + 550 * i, min(y + 70, 1300)), seed=i + 1, scale=1.5)
    draw.text((75, 1670), DISCLAIMER, font=font(20), fill="#555555")
    return image.rotate(skew, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="#f3f2eb") if skew else image


def signature_page():
    image = scan_page("Supply Agreement - Signature Page", [
        f"Supplier: {OURS}",
        f"Customer: {NORTH}",
        "Execution of the Supply Agreement, including General Terms, Programme Terms and Schedule 1.",
        "Effective on the date of the last signature.",
    ])
    draw = ImageDraw.Draw(image)
    draw.text((85, 670), f"Signed for {OURS}", font=font(26), fill="#222222")
    scrawl(draw, (110, 765), seed=3, scale=1.6)
    draw.text((85, 820), "A. Wren", font=font(29, True), fill="#152762")
    draw.text((85, 875), "12 March 2019", font=font(31, True), fill="#152762")
    draw.text((85, 1000), f"Signed for {NORTH}", font=font(26), fill="#222222")
    scrawl(draw, (110, 1100), seed=8, scale=1.6)
    draw.text((85, 1150), "B. Reed", font=font(29, True), fill="#152762")
    draw.text((85, 1210), "14 March 2019", font=font(31, True), fill="#152762")
    return image


def native_pdf(path, pages, signed_pages=None, image_pages=None):
    """Write [(title, [paragraphs])]; optional 1-based page -> signature count/image."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(595, 842), invariant=1)
    pdf.setTitle(pages[0][0])
    pdf.setAuthor("Invented development fixture")
    for n, (title, paragraphs) in enumerate(pages, 1):
        if image_pages and n in image_pages:
            pdf.drawImage(ImageReader(image_pages[n]), 0, 0, width=595, height=842)
            pdf.showPage()
            continue
        pdf.setFont("Helvetica-Bold", 15)
        y = 793
        for line in textwrap.wrap(title, 60):
            pdf.drawString(45, y, line)
            y -= 22
        pdf.setFont("Helvetica", 10)
        y -= 15
        for paragraph in paragraphs:
            for line in textwrap.wrap(paragraph, 98):
                pdf.drawString(45, y, line)
                y -= 15
            y -= 12
        for i in range((signed_pages or {}).get(n, 0)):
            stamp = Image.new("RGBA", (450, 110), (255, 255, 255, 0))
            scrawl(ImageDraw.Draw(stamp), (10, 42), seed=i + 2, scale=1.6)
            pdf.drawImage(ImageReader(stamp), 50 + i * 245, max(70, y - 60), width=200, height=49, mask="auto")
        pdf.setFont("Helvetica", 7)
        pdf.drawString(45, 28, f"{DISCLAIMER} | page {n}")
        pdf.showPage()
    pdf.save()


def docx(path, paragraphs, comments, author, tracked_paragraph):
    """Minimal real OpenXML package, including comments, revision and core metadata."""
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = []
    for i, paragraph in enumerate(paragraphs):
        text = f"<w:r><w:t>{escape(paragraph)}</w:t></w:r>"
        if i == tracked_paragraph:
            text += ('<w:del w:id="10" w:author="Sample Drafter" w:date="2026-01-15T10:00:00Z">'
                     '<w:r><w:delText>Discussion version.</w:delText></w:r></w:del>'
                     '<w:ins w:id="11" w:author="Sample Drafter" w:date="2026-01-15T10:00:00Z">'
                     '<w:r><w:t>Review version.</w:t></w:r></w:ins>')
        if i < len(comments):
            text = f'<w:commentRangeStart w:id="{i}"/>' + text + f'<w:commentRangeEnd w:id="{i}"/><w:r><w:commentReference w:id="{i}"/></w:r>'
        body.append(f"<w:p>{text}</w:p>")
    body.append(f"<w:p><w:r><w:t>{DISCLAIMER}</w:t></w:r></w:p>")
    files = {
        "[Content_Types].xml": '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>''',
        "_rels/.rels": '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>''',
        "word/document.xml": f'<w:document xmlns:w="{w}"><w:body>{"".join(body)}<w:sectPr/></w:body></w:document>',
        "word/_rels/document.xml.rels": '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdComments" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>''',
        "word/comments.xml": f'<w:comments xmlns:w="{w}">' + "".join(f'<w:comment w:id="{i}" w:author="Sample Reviewer" w:date="2026-01-15T11:00:00Z"><w:p><w:r><w:t>{escape(t)}</w:t></w:r></w:p></w:comment>' for i, t in enumerate(comments)) + '</w:comments>',
        "docProps/core.xml": f'''<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:creator>{author}</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">2026-01-14T09:00:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2026-01-15T11:00:00Z</dcterms:modified></cp:coreProperties>''',
    }
    with ZipFile(path, "w") as archive:
        for name, value in files.items():
            info = ZipInfo(name, (2026, 1, 15, 11, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, value.encode("utf-8"))


def make_pile(folder=HERE / "pile", omit_precedence=False):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    supply = [(title, [p for p in paras if not (omit_precedence and p.startswith("9."))]) for title, paras in SUPPLY]
    native_pdf(folder / "01 Supply Agreement.pdf", supply + [("Signatures", [])], image_pages={4: signature_page()})
    native_pdf(folder / "02 Amendment 1.pdf", AMENDMENT, signed_pages={1: 2})
    native_pdf(folder / "03 NDA scan.pdf", NDA, image_pages={i: scan_page(title, paras, signatures=2 if i == 2 else 0, skew=.65 if i == 1 else -.45) for i, (title, paras) in enumerate(NDA, 1)})
    docx(folder / "04 MSA draft.docx", MSA, ["Confirm the commercial terms with sales.", "Obtain the complete execution version before treating this as agreed."], "Fictional MSA Drafter", 3)
    native_pdf(folder / "05 Purchase Order.pdf", PO)
    native_pdf(folder / "06 Rebate Letter.pdf", REBATE, signed_pages={1: 1})
    detached = scan_page("Master Services Agreement - Signature Page", [
        "Signature page for Master Services Agreement dated 15 January 2026.",
        f"Signed for {ACCOUNT2}: D. Moor. Date: 16 January 2026.",
        f"Signed for {OURS}: A. Wren. Date: 16 January 2026.",
        "The text pages of the execution version are not attached to this page.",
    ], signatures=2)
    detached.save(folder / "07 scan_0032.jpg", quality=92)
    native_pdf(folder / "08 Hexley Works Site Agreement.pdf", PROJECT, signed_pages={1: 2})
    docx(folder / "09 Internal Account Playbook.docx", PLAYBOOK, ["Check the quarterly cost review."], "Fictional Account Manager", 2)
    (folder / "10 old email.msg").write_bytes(b"")
    with (folder / "ERP_record.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["account_number", "customer_account", "country"])
        writer.writerows([("INV-100", ACCOUNT1, "United Kingdom"), ("INV-200", ACCOUNT2, "United Kingdom"), ("INV-101", ACCOUNT1 + " Data Centres", "United Kingdom")])
    print(f"Created 11 invented sample files in {folder}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "pile")
    parser.add_argument("--omit-precedence", action="store_true", help="sabotage fixture; use an isolated output folder")
    args = parser.parse_args()
    make_pile(args.output, args.omit_precedence)
