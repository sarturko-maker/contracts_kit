#!/usr/bin/env python3
"""Rendering helpers for the messy invented pile.

Everything produced here is fictional. Build-only dependencies: reportlab, Pillow,
openpyxl, numpy. Output is deterministic: fixed seeds, fixed zip timestamps,
reportlab invariant mode.
"""
from __future__ import annotations

import io
import math
import random
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

DISCLAIMER = "INVENTED TEST FIXTURE - NOT A REAL AGREEMENT"
FIXED_ZIP_DATE = (2026, 9, 1, 9, 0, 0)
PAGE_W, PAGE_H = 595, 842
SCAN_W, SCAN_H = 1240, 1754

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")


def font(size=25, italic=False, bold=False, mono=False):
    if mono:
        stem = "LiberationMono-Bold.ttf" if bold else "LiberationMono-Regular.ttf"
    elif bold:
        stem = "LiberationSans-Bold.ttf"
    elif italic:
        stem = "LiberationSans-Italic.ttf"
    else:
        stem = "LiberationSans-Regular.ttf"
    path = FONT_DIR / stem
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def scrawl(draw, xy, seed=1, scale=1.0, colour=(24, 39, 97)):
    """Obviously synthetic pen strokes; they identify no real signatory."""
    x, y = xy
    points = [(x + i * 2 * scale,
               y + (math.sin(i / 4 + seed) * 16 + math.sin(i / 1.7 + seed / 3) * 7) * scale)
              for i in range(105)]
    draw.line(points, fill=colour, width=max(2, round(3 * scale)))
    draw.line([(x, y + 20 * scale), (x + 210 * scale, y + 12 * scale)], fill=colour, width=2)


# ---------------------------------------------------------------- scan images

def scan_page(title, paragraphs, signatures=0, skew=0.0, subtitle=None,
              footer=None, base="#fcfbf5", title_size=31, body_size=25,
              wrap=82, indent=75, return_end_y=False):
    image = Image.new("RGB", (SCAN_W, SCAN_H), base)
    draw = ImageDraw.Draw(image)
    y = 95
    if title:
        for line in textwrap.wrap(title, 58):
            draw.text((indent, y), line, font=font(title_size, bold=True), fill="#18202c")
            y += title_size + 11
    if subtitle:
        y += 8
        for line in textwrap.wrap(subtitle, 74):
            draw.text((indent, y), line, font=font(24, italic=True), fill="#3a3a3a")
            y += 34
    y += 30
    for paragraph in paragraphs:
        if paragraph == "":
            y += 22
            continue
        for line in textwrap.wrap(paragraph, wrap):
            draw.text((indent, y), line, font=font(body_size), fill="#222222")
            y += body_size + 12
        y += 22
    for i in range(signatures):
        scrawl(draw, (indent + 30 + 560 * i, min(y + 60, 1420)), seed=i + 1, scale=1.5)
    draw.text((indent, 1672), footer or DISCLAIMER, font=font(19), fill="#666666")
    if skew:
        image = image.rotate(skew, resample=Image.Resampling.BICUBIC, expand=False,
                             fillcolor="#f3f2eb")
    return (image, y) if return_end_y else image


def add_noise(image, seed=7, amount=16, low_contrast=False, blur=0.0):
    """Scanner grain; optionally wash the contrast out the way a bad copier does."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(image).astype(np.float32)
    if low_contrast:
        arr = arr * 0.42 + 118.0
    small = rng.normal(0.0, amount, size=(SCAN_H // 4, SCAN_W // 4, 1)).astype(np.float32)
    grain = np.asarray(Image.fromarray(
        np.clip(small + 128, 0, 255).astype(np.uint8)[:, :, 0]).resize(
            (arr.shape[1], arr.shape[0]), Image.Resampling.BILINEAR)).astype(np.float32) - 128.0
    arr = arr + grain[:, :, None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if blur:
        out = out.filter(ImageFilter.GaussianBlur(blur))
    return out


def add_fax_header(image, text):
    draw = ImageDraw.Draw(image)
    draw.text((60, 30), text, font=font(21, mono=True), fill="#111111")
    draw.line([(50, 66), (SCAN_W - 50, 66)], fill="#111111", width=2)
    return image


def add_coffee_ring(image, centre=(880, 1210), radius=190, seed=3):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = centre
    draw.ellipse([cx - radius, cy - radius * 0.82, cx + radius, cy + radius * 0.82],
                 outline=(112, 70, 30, 205), width=20)
    draw.ellipse([cx - radius + 26, cy - radius * 0.82 + 21, cx + radius - 26,
                  cy + radius * 0.82 - 21], outline=(140, 96, 52, 90), width=6)
    draw.ellipse([cx - radius + 34, cy - radius * 0.82 + 28, cx + radius - 34,
                  cy + radius * 0.82 - 28], fill=(176, 140, 96, 16))
    overlay = overlay.filter(ImageFilter.GaussianBlur(2.5))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def photograph(image, angle=6.5, seed=11):
    """A phone photo of a sheet of paper on a desk, taken slightly off square."""
    page = image.resize((980, 1386), Image.Resampling.LANCZOS)
    page = page.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True,
                       fillcolor=(0, 0, 0))
    canvas_img = Image.new("RGB", (1180, 1600), (86, 79, 70))
    rng = np.random.default_rng(seed)
    desk = np.asarray(canvas_img).astype(np.float32)
    desk += rng.normal(0, 6, desk.shape)
    canvas_img = Image.fromarray(np.clip(desk, 0, 255).astype(np.uint8))
    ox = (1180 - page.width) // 2
    oy = (1600 - page.height) // 2
    mask = Image.new("L", page.size, 0)
    solid = Image.new("L", image.size, 255).resize((980, 1386)).rotate(
        angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=0)
    mask.paste(solid, (0, 0))
    canvas_img.paste(page, (ox, oy), mask)
    # uneven lighting from one side, then camera softness and grain
    arr = np.asarray(canvas_img).astype(np.float32)
    gradient = np.linspace(1.13, 0.80, arr.shape[1])[None, :, None]
    arr = arr * gradient
    arr += rng.normal(0, 4.5, arr.shape)
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return out.filter(ImageFilter.GaussianBlur(0.7))


# ---------------------------------------------------------------- native PDFs

STYLES = {
    "plain": {"body": "Helvetica", "head": "Helvetica-Bold", "italic": "Helvetica-Oblique",
              "size": 9.6, "lead": 14.2, "wrap": 100},
    "legal": {"body": "Times-Roman", "head": "Times-Bold", "italic": "Times-Italic",
              "size": 10.4, "lead": 15.0, "wrap": 96},
    "letter": {"body": "Helvetica", "head": "Helvetica-Bold", "italic": "Helvetica-Oblique",
               "size": 10.2, "lead": 15.4, "wrap": 92},
    "typed": {"body": "Courier", "head": "Courier-Bold", "italic": "Courier-Oblique",
              "size": 9.2, "lead": 14.0, "wrap": 88},
}


def native_pdf(path, pages, signed_pages=None, image_pages=None, watermark=None,
               style="plain", title=None, author="Invented test fixture",
               landscape_pages=(), footer_note=None, page_number_from=1):
    """pages: list of dicts {title, paras, style?, head?, rule?}."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H), invariant=1)
    pdf.setTitle(title or (pages[0].get("title") if pages else "document"))
    pdf.setAuthor(author)
    pdf.setCreator("invented fixture generator")
    for n, page in enumerate(pages, page_number_from):
        st = STYLES[page.get("style", style)]
        if image_pages and n in image_pages:
            img = image_pages[n]
            if n in landscape_pages:
                pdf.setPageSize((PAGE_H, PAGE_W))
                pdf.drawImage(ImageReader(img), 0, 0, width=PAGE_H, height=PAGE_W)
                pdf.showPage()
                pdf.setPageSize((PAGE_W, PAGE_H))
            else:
                pdf.drawImage(ImageReader(img), 0, 0, width=PAGE_W, height=PAGE_H)
                pdf.showPage()
            continue
        y = 800
        if page.get("head"):
            pdf.setFont(st["body"], 7.6)
            pdf.setFillGray(0.35)
            pdf.drawString(45, 812, page["head"])
            pdf.drawRightString(PAGE_W - 45, 812, page.get("head_right", ""))
            pdf.setFillGray(0)
            y = 786
        if page.get("title"):
            pdf.setFont(st["head"], page.get("title_size", 13.5))
            for line in textwrap.wrap(page["title"], page.get("title_wrap", 62)):
                pdf.drawString(45, y, line)
                y -= 19
            if page.get("rule", True):
                pdf.setLineWidth(0.7)
                pdf.line(45, y + 8, PAGE_W - 45, y + 8)
            y -= 12
        if page.get("subtitle"):
            pdf.setFont(st["italic"], st["size"])
            for line in textwrap.wrap(page["subtitle"], st["wrap"]):
                pdf.drawString(45, y, line)
                y -= st["lead"]
            y -= 6
        pdf.setFont(st["body"], st["size"])
        for paragraph in page.get("paras", []):
            if paragraph == "":
                y -= st["lead"] * 0.6
                continue
            indent = 45
            text = paragraph
            if paragraph.startswith("\t"):
                indent = 78
                text = paragraph.lstrip("\t")
            if text.startswith("##"):
                pdf.setFont(st["head"], st["size"] + 1.2)
                for line in textwrap.wrap(text[2:].strip(), st["wrap"] - 6):
                    pdf.drawString(indent, y, line)
                    y -= st["lead"]
                pdf.setFont(st["body"], st["size"])
                y -= 3
                continue
            for line in textwrap.wrap(text, st["wrap"] if indent == 45 else st["wrap"] - 8):
                pdf.drawString(indent, y, line)
                y -= st["lead"]
            y -= st["lead"] * 0.55
        for i in range((signed_pages or {}).get(n, 0)):
            stamp = Image.new("RGBA", (450, 110), (255, 255, 255, 0))
            scrawl(ImageDraw.Draw(stamp), (10, 42), seed=i + 2, scale=1.6)
            pdf.drawImage(ImageReader(stamp), 55 + i * 245, max(60, y - 58),
                          width=200, height=49, mask="auto")
        if watermark:
            pdf.saveState()
            pdf.setFont("Helvetica-Bold", 96)
            pdf.setFillColorRGB(0.72, 0.72, 0.78, alpha=0.30)
            pdf.translate(300, 380)
            pdf.rotate(38)
            pdf.drawCentredString(0, 0, watermark)
            pdf.restoreState()
        pdf.setFont(st["body"], 6.8)
        pdf.setFillGray(0.4)
        pdf.drawString(45, 26, f"{DISCLAIMER}  |  page {n}"
                       + (f"  |  {footer_note}" if footer_note else ""))
        pdf.setFillGray(0)
        pdf.showPage()
    pdf.save()
    return path


# ---------------------------------------------------------------------- DOCX

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx(path, paragraphs, comments=(), author="Invented drafter",
         tracked=(), created="2025-07-28T09:00:00Z", modified="2025-07-28T16:20:00Z",
         comment_author="Invented reviewer", comment_date="2025-07-29T11:00:00Z",
         comment_anchors=None):
    """Minimal but real OpenXML package.

    `tracked` is a list of (paragraph_index, deleted_text, inserted_text).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tracked_by_index = {i: (d, ins) for i, d, ins in tracked}
    anchors = list(comment_anchors) if comment_anchors else list(range(len(comments)))
    comment_at = {paragraph_index: comment_id for comment_id, paragraph_index in enumerate(anchors)}
    body = []
    for i, paragraph in enumerate(paragraphs):
        run = f"<w:r><w:t xml:space=\"preserve\">{escape(paragraph)}</w:t></w:r>"
        if i in tracked_by_index:
            deleted, inserted = tracked_by_index[i]
            change = (f'<w:del w:id="{100 + i}" w:author="{escape(author)}" w:date="{modified}">'
                      f'<w:r><w:delText xml:space="preserve">{escape(deleted)}</w:delText></w:r>'
                      '</w:del>'
                      f'<w:ins w:id="{200 + i}" w:author="{escape(author)}" w:date="{modified}">'
                      f'<w:r><w:t xml:space="preserve">{escape(inserted)}</w:t></w:r></w:ins>')
            if deleted and deleted in paragraph:
                before, after = paragraph.split(deleted, 1)
                run = (f'<w:r><w:t xml:space="preserve">{escape(before)}</w:t></w:r>' + change
                       + f'<w:r><w:t xml:space="preserve">{escape(after)}</w:t></w:r>')
            else:
                run += change
        if i in comment_at:
            cid = comment_at[i]
            run = (f'<w:commentRangeStart w:id="{cid}"/>' + run
                   + f'<w:commentRangeEnd w:id="{cid}"/>'
                     f'<w:r><w:commentReference w:id="{cid}"/></w:r>')
        body.append(f"<w:p>{run}</w:p>")
    body.append(f'<w:p><w:r><w:t>{DISCLAIMER}</w:t></w:r></w:p>')
    comment_xml = "".join(
        f'<w:comment w:id="{i}" w:author="{escape(comment_author)}" w:date="{comment_date}">'
        f'<w:p><w:r><w:t>{escape(t)}</w:t></w:r></w:p></w:comment>'
        for i, t in enumerate(comments))
    files = {
        "[Content_Types].xml":
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '</Types>',
        "_rels/.rels":
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '</Relationships>',
        "word/document.xml":
            f'<w:document xmlns:w="{W_NS}"><w:body>{"".join(body)}<w:sectPr/></w:body></w:document>',
        "word/_rels/document.xml.rels":
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdComments" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>'
            '</Relationships>',
        "word/comments.xml": f'<w:comments xmlns:w="{W_NS}">{comment_xml}</w:comments>',
        "docProps/core.xml":
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"'
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:creator>{escape(author)}</dc:creator>'
            f'<cp:lastModifiedBy>{escape(comment_author)}</cp:lastModifiedBy>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{modified}</dcterms:modified>'
            '</cp:coreProperties>',
    }
    with ZipFile(path, "w") as archive:
        for name, value in files.items():
            info = ZipInfo(name, FIXED_ZIP_DATE)
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, value.encode("utf-8"))
    return path


# ---------------------------------------------------------------------- XLSX

def xlsx(path, sheet_name, rows, widths=None, bold_rows=(), title_props=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    import datetime as _dt

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    for index in bold_rows:
        for cell in ws[index]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(wrap_text=False)
    for column, width in (widths or {}).items():
        ws.column_dimensions[column].width = width
    fixed = _dt.datetime(2025, 12, 12, 10, 30, 0)
    wb.properties.created = fixed
    wb.properties.modified = fixed
    wb.properties.creator = (title_props or {}).get("creator", "Invented test fixture")
    wb.properties.title = (title_props or {}).get("title", sheet_name)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    # rewrite the package with fixed timestamps so the bytes are reproducible
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fixed_core = (
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:creator>{wb.properties.creator}</dc:creator>'
        f'<dc:title>{wb.properties.title}</dc:title>'
        '<dcterms:created xsi:type="dcterms:W3CDTF">2025-12-12T10:30:00Z</dcterms:created>'
        '<dcterms:modified xsi:type="dcterms:W3CDTF">2025-12-12T10:30:00Z</dcterms:modified>'
        '</cp:coreProperties>').encode("utf-8")
    with ZipFile(buffer) as source, ZipFile(path, "w") as target:
        for name in sorted(source.namelist()):
            info = ZipInfo(name, FIXED_ZIP_DATE)
            info.compress_type = ZIP_DEFLATED
            data = fixed_core if name == "docProps/core.xml" else source.read(name)
            target.writestr(info, data)
    return path
