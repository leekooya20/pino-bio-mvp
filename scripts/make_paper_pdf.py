#!/usr/bin/env python
"""Render a Quarto .qmd (or .md) research paper to PDF via reportlab (pdf skill method).

Canonical source stays the .qmd (render with `quarto render --to typst` for the house-
styled edition). This produces a faithful academic PDF locally without Quarto/Typst.
Handles: front matter (title/subtitle/date/author), headings, paragraphs (**bold**,
`code`), bullet lists, and markdown tables. Unicode sanitized to ASCII where Helvetica
lacks glyphs (pdf skill warning).

Usage: python scripts/make_paper_pdf.py <in.qmd> <out.pdf>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

_UNI = {"×": "x", "≤": "<=", "≥": ">=", "→": "->", "≈": "~", "±": "+/-", "Å": "A",
        "Δ": "delta", "↑": " (up)", "↓": " (down)", "–": "-", "—": "-", "·": " - ",
        "’": "'", "‘": "'", "“": '"', "”": '"', "…": "...", "→": "->", "⁄": "/"}


def sani(s: str) -> str:
    for k, v in _UNI.items():
        s = s.replace(k, v)
    return s


def inline(s: str) -> str:
    s = sani(s)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", s)  # links -> text
    return s


def parse_front_matter(text: str):
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end]
            body = text[end + 4:]
            for line in fm.splitlines():
                m = re.match(r"^(title|subtitle|date):\s*(.+)$", line.strip())
                if m:
                    meta[m.group(1)] = m.group(2).strip().strip('"')
            am = re.search(r"name:\s*(.+)", fm)
            if am:
                meta["author"] = am.group(1).strip()
            afm = re.search(r"affiliations:\s*\n\s*-\s*name:\s*(.+)", fm)
            if afm:
                meta["affiliation"] = afm.group(1).strip()
    return meta, body


def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    meta, body = parse_front_matter(src.read_text(encoding="utf-8"))
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)  # drop HTML comments

    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=13, spaceBefore=12, spaceAfter=6)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11, spaceBefore=9, spaceAfter=4)
    BODY = ParagraphStyle("Body", parent=ss["BodyText"], fontSize=9.5, leading=13, spaceAfter=5, alignment=4)
    BULL = ParagraphStyle("Bull", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=2)
    TITLE = ParagraphStyle("Title", parent=ss["Title"], fontSize=17, leading=21)
    SUB = ParagraphStyle("Sub", parent=ss["Italic"], fontSize=10, textColor=colors.HexColor("#444"), spaceAfter=2)
    BY = ParagraphStyle("By", parent=BODY, fontSize=9, textColor=colors.HexColor("#333"), spaceAfter=1)
    CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
    CELLH = ParagraphStyle("CellH", parent=CELL, textColor=colors.white)

    story = []
    if meta.get("title"):
        story += [Paragraph(sani(meta["title"]), TITLE), Spacer(1, 4)]
    if meta.get("subtitle"):
        story += [Paragraph(sani(meta["subtitle"]), SUB)]
    byline = meta.get("author", "Stan Lee V. Natividad")
    if meta.get("affiliation"):
        byline += " · " + meta["affiliation"]
    story += [Paragraph(sani(byline), BY)]
    if meta.get("date"):
        story += [Paragraph(sani(meta["date"]), BY)]
    story += [Spacer(1, 10)]

    lines = body.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        # table block
        if ln.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                raw = lines[i].strip().strip("|")
                if not re.match(r"^[\s:|-]+$", raw):
                    rows.append([c.strip() for c in raw.split("|")])
                i += 1
            if rows:
                ncol = len(rows[0])
                data = [[Paragraph(inline(c), CELLH if r == 0 else CELL) for c in (row + [""] * ncol)[:ncol]]
                        for r, row in enumerate(rows)]
                t = Table(data, repeatRows=1, hAlign="LEFT")
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b5a3e")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4bd")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f3")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                story += [Spacer(1, 3), t, Spacer(1, 7)]
            continue
        if ln.startswith("# "):
            story += [Paragraph(inline(ln[2:]), H1)]
        elif ln.startswith("## "):
            story += [Paragraph(inline(ln[3:]), H1)]
        elif ln.startswith("### "):
            story += [Paragraph(inline(ln[4:]), H2)]
        elif re.match(r"^\s*[-*]\s+", ln):
            story += [Paragraph(inline(re.sub(r"^\s*[-*]\s+", "", ln)), BULL, bulletText="•")]
        elif re.match(r"^\s*\d+\.\s+", ln):
            story += [Paragraph(inline(ln.strip()), BULL)]
        else:
            story += [Paragraph(inline(ln), BODY)]
        i += 1

    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out), pagesize=A4, topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                            leftMargin=2.0 * cm, rightMargin=2.0 * cm,
                            title=meta.get("title", "paper"), author=meta.get("author", ""))
    doc.build(story)
    print(f"ok  PDF -> {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
