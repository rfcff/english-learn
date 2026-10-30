#!/usr/bin/env python3
"""Typeset the handbooks as printed books and write PDFs via headless Chrome."""

import html as html_lib
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/pylibs")

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = Path("/tmp/english-learn-pdf")
OUT.mkdir(exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
IMG = ROOT.as_uri() + "/images/"

CN_DIGIT = {ch: i for i, ch in enumerate("零一二三四五六七八九")}

CSS = r"""
@page {
  size: A4;
  margin: 16mm 16mm 16mm 20mm;
  @bottom-center {
    content: counter(page);
    font-family: "Times New Roman", "Songti SC", serif;
    font-size: 9pt;
    color: #3a342c;
  }
}
@page:left {
  margin-left: 14mm;
  margin-right: 22mm;
}
@page:right {
  margin-left: 22mm;
  margin-right: 14mm;
}
@page:first {
  margin: 22mm 20mm 20mm 20mm;
  @bottom-center { content: none; }
}
@page cover {
  size: A4;
  margin: 22mm 20mm 20mm 20mm;
  @bottom-center { content: none; }
}

* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0;
  color: #1c1916;
  font-family: "Songti SC", "Songti SC Regular", "STSong", "Times New Roman", serif;
  font-size: 10.5pt;
  line-height: 1.75;
  font-weight: 400;
}
h1, h2, h3 {
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-weight: 600;
  line-height: 1.35;
  break-after: avoid;
  page-break-after: avoid;
}
p {
  margin: 0.2em 0 0.35em;
  text-indent: 2em;
  text-align: justify;
  text-justify: inter-ideograph;
  line-break: strict;
}
li p, td p, figcaption, .cover p, p.tablecap { text-indent: 0; }
strong, b { font-weight: 600; }
em, i { font-style: italic; font-family: "Times New Roman", "Songti SC", serif; }
a { color: inherit; text-decoration: none; }
ul, ol { margin: 0.3em 0 0.7em; padding-left: 1.45em; }
li {
  margin: 0.12em 0;
  text-align: justify;
  text-justify: inter-ideograph;
  line-break: strict;
}
hr { display: none; }

section.chapter, section.part { break-before: page; page-break-before: always; }
section.cover { break-before: auto; page-break-before: auto; }

.cover h1 {
  margin: 58mm 0 0;
  text-align: center;
  font-family: "Songti SC", "STSong", serif;
  font-size: 26pt;
  font-weight: 500;
  letter-spacing: 0.18em;
  line-height: 1.45;
}
.latin { letter-spacing: 0; }
.cover .rule {
  width: 28mm;
  border: none;
  border-top: 0.9pt solid #7a2e2a;
  margin: 9mm auto 0;
  height: 0;
}
.cover .meta {
  text-align: center;
  margin-top: 8mm;
  letter-spacing: 0.32em;
  font-size: 11pt;
  color: #3f3832;
}
.cover p { text-align: center; }
.cover table {
  width: 88%;
  margin: 18mm auto 0;
  font-size: 9pt;
}

section.part h1 {
  margin: 72mm 0 0;
  text-align: center;
  font-family: "Songti SC", "STSong", serif;
  font-size: 22pt;
  font-weight: 500;
  letter-spacing: 0.28em;
}
section.part h1::after {
  content: "";
  display: block;
  width: 18mm;
  margin: 8mm auto 0;
  border-top: 0.9pt solid #7a2e2a;
}

h2 {
  margin: 0 0 0.75em;
  font-size: 16pt;
  letter-spacing: 0.06em;
}
h2::after {
  content: "";
  display: block;
  width: 2.4em;
  margin-top: 0.38em;
  border-top: 1.6pt solid #7a2e2a;
}
h3 {
  margin: 1.05em 0 0.35em;
  font-size: 12pt;
  letter-spacing: 0.04em;
}
p.exercise {
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-weight: 600;
  font-size: 12pt;
  line-height: 1.35;
  letter-spacing: 0.04em;
  margin: 1.05em 0 0.35em;
  text-indent: 0;
  text-align: left;
  break-after: avoid;
  page-break-after: avoid;
}
section.toc h2 { margin-bottom: 0.45em; }
section.toc h3 {
  font-size: 11pt;
  margin: 0.7em 0 0.12em;
}
section.toc ul {
  list-style: none;
  margin: 0.1em 0 0.25em;
  padding-left: 0;
}
section.toc li { margin: 0.16em 0; text-align: left; }
section.toc a.toc-entry {
  display: flex;
  align-items: baseline;
  width: 100%;
  text-indent: 0;
}
section.toc h3 a.toc-entry { font-weight: 600; }
section.toc .toc-name { flex: 0 1 auto; }
section.toc .toc-leader {
  flex: 1 1 auto;
  border-bottom: 0.6pt dotted #a3988c;
  margin: 0 0.4em;
  min-width: 0.8em;
  height: 0;
  position: relative;
  top: -0.28em;
}
section.toc .toc-page {
  flex: 0 0 2.2em;
  text-align: right;
  font-family: "Times New Roman", "Songti SC", serif;
  font-variant-numeric: tabular-nums;
}

blockquote {
  margin: 0.55em 0 0.8em;
  padding: 0.05em 0 0.05em 0.75em;
  border-left: 1.6pt solid #7a2e2a;
  color: #2a241f;
  break-inside: avoid;
  page-break-inside: avoid;
}
blockquote p { margin: 0.15em 0; }

p.tablecap {
  text-align: center;
  text-indent: 0;
  margin: 0.85em 0 0.2em;
  font-size: 9.5pt;
  break-after: avoid;
  page-break-after: avoid;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.15em 0 0.9em;
  font-size: 9pt;
  line-height: 1.45;
}
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td {
  border: none;
  border-bottom: 0.35pt solid #e4ddd2;
  padding: 3.2pt 5pt;
  vertical-align: top;
  text-align: left;
  font-weight: 400;
}
th {
  font-family: "Hiragino Sans GB", "STHeiti", sans-serif;
  font-weight: 600;
  font-size: 8.5pt;
  letter-spacing: 0.04em;
  border-top: 1.05pt solid #1c1916;
  border-bottom: 0.6pt solid #1c1916;
  padding-top: 4pt;
  padding-bottom: 3.5pt;
  white-space: nowrap;
}
td { word-break: keep-all; line-break: strict; }
tbody tr:last-child td { border-bottom: 1.05pt solid #1c1916; }
table.wide { font-size: 7.6pt; line-height: 1.35; }
table.wide th, table.wide td { padding: 2.4pt 2.6pt; }

figure {
  margin: 0.7em 0 0.9em;
  break-inside: avoid;
  page-break-inside: avoid;
}
img {
  display: block;
  max-width: 100%;
  max-height: 158mm;
  margin: 0 auto;
}
figcaption {
  margin-top: 0.35em;
  text-align: center;
  font-size: 9pt;
  letter-spacing: 0.02em;
  color: #3a342c;
}
"""


def strip_tags(fragment):
    text = re.sub(r"<[^>]+>", "", fragment)
    return html_lib.unescape(text).strip()


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def cn_to_int(token):
    if not token:
        return 0
    if token == "十":
        return 10
    if token.startswith("十"):
        return 10 + cn_to_int(token[1:])
    if "百" in token:
        left, right = token.split("百", 1)
        base = (cn_to_int(left) or 1) * 100
        if not right:
            return base
        if right.startswith("零"):
            return base + cn_to_int(right[1:])
        return base + cn_to_int(right)
    if "十" in token:
        left, right = token.split("十", 1)
        return (cn_to_int(left) or 1) * 10 + cn_to_int(right)
    if token in CN_DIGIT:
        return CN_DIGIT[token]
    return None


def chapter_number(title):
    matched = re.match(r"第([零一二三四五六七八九十百]+)章", title)
    if not matched:
        matched = re.match(r"^([零一二三四五六七八九十]+)[、.]", title)
    if not matched:
        return None
    return cn_to_int(matched.group(1))


def is_table_caption(text):
    flat = text.replace("\u3000", " ")
    flat = re.sub(r"\s+", " ", flat).strip()
    if not re.match(r"^表(?:附)?\s*\d+(?:-\d+)?(?:\s|$)", flat):
        return False
    if re.search(r"[。！？，；]", flat):
        return False
    return len(flat) <= 36


def mark_wide_tables(html):
    def repl(match):
        table = match.group(0)
        first = re.search(r"<tr\b.*?</tr>", table, re.S)
        n = len(re.findall(r"<t[dh]\b", first.group(0))) if first else 0
        if n >= 6:
            return table.replace("<table>", '<table class="wide">', 1)
        return table

    return re.sub(r"<table\b.*?</table>", repl, html, flags=re.S)


def decorate(html):
    """Number figures by chapter and mark table titles."""
    chapter = None
    fig = 0
    pattern = re.compile(
        r"(<h[12]>.*?</h[12]>)"
        r"|(<p><img alt=\"([^\"]*)\" src=\"([^\"]+)\"\s*/?></p>)"
        r"|(<p>(.*?)</p>)",
        re.S,
    )

    def repl(match):
        nonlocal chapter, fig
        if match.group(1):
            title = strip_tags(match.group(1))
            number = chapter_number(title)
            if number is not None:
                chapter = number
                fig = 0
            return match.group(1)
        if match.group(2):
            alt, src = match.group(3), match.group(4)
            if chapter is not None and alt:
                fig += 1
                alt = f"{chapter}-{fig} {alt}"
            cap = f"<figcaption>{html_lib.escape(alt)}</figcaption>" if alt else ""
            return (
                f'<figure><img alt="{html_lib.escape(alt, quote=True)}" '
                f'src="{src}">{cap}</figure>'
            )
        inner = match.group(6)
        if strip_tags(inner).strip() == "习题":
            return '<p class="exercise">习题</p>'
        if is_table_caption(strip_tags(inner)):
            return f'<p class="tablecap">{inner}</p>'
        return match.group(5)

    html = pattern.sub(repl, html)
    return html.replace('src="images/', f'src="{IMG}')


def toc_links(html):
    def repl(match):
        href, label = match.group(1), match.group(2)
        key = html_lib.escape(norm(strip_tags(label)), quote=True)
        return (
            f'<a class="toc-entry" href="{href}">'
            f'<span class="toc-name">{label}</span>'
            f'<span class="toc-leader"></span>'
            f'<span class="toc-page" data-toc="{key}">000</span>'
            f"</a>"
        )

    return re.sub(r'<a href="([^"]+)">([^<]*)</a>', repl, html)


def heading_pages(pdf_path):
    import fitz

    doc = fitz.open(pdf_path)
    found = {}
    for index, page in enumerate(doc):
        lines = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                size = max(span["size"] for span in spans)
                if size < 14.5:
                    continue
                text = "".join(span["text"] for span in spans).strip()
                if text:
                    lines.append((line["bbox"][1], text, size))
        lines.sort()
        merged = []
        for y, text, size in lines:
            if (
                merged
                and abs(y - merged[-1][0]) < 30
                and abs(size - merged[-1][2]) < 2
            ):
                merged[-1][1] += text
            else:
                merged.append([y, text, size])
        for _y, text, _size in merged:
            found.setdefault(norm(text), index + 1)
    doc.close()
    return found


def fill_toc(html, pages):
    missing = []

    def repl(match):
        label = norm(html_lib.unescape(match.group(1)))
        number = pages.get(label)
        if number is None:
            missing.append(label)
            shown = ""
        else:
            shown = str(number)
        return (
            f'<span class="toc-page" data-toc="{match.group(1)}">{shown}</span>'
        )

    filled = re.sub(
        r'<span class="toc-page" data-toc="([^"]*)">[^<]*</span>',
        repl,
        html,
    )
    return filled, missing


def toc_numbers(pdf_path):
    import fitz

    doc = fitz.open(pdf_path)
    numbers = {}
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                text = "".join(span["text"] for span in line["spans"]).strip()
                matched = re.search(r"(\d{1,3})$", text)
                if not matched:
                    continue
                title = norm(text[: matched.start()])
                title = title.rstrip(".·・… ")
                if title:
                    numbers.setdefault(title, int(matched.group(1)))
    doc.close()
    return numbers


def tighten_latin(fragment):
    """Keep English abbreviations together under CJK letter-spacing."""

    def repl(match):
        inner = re.sub(
            r"[A-Za-z][A-Za-z0-9]*",
            r'<span class="latin">\g<0></span>',
            match.group(2),
        )
        return match.group(1) + inner + match.group(3)

    return re.sub(r"(<h1[^>]*>)(.*?)(</h1>)", repl, fragment, flags=re.S)


def build_html(md_path, book_title):
    text = md_path.read_text()
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    body = decorate(body)
    body = mark_wide_tables(body)
    parts = re.split(r"(<h[12]>.*?</h[12]>)", body, flags=re.S)
    items = []
    if parts[0].strip():
        items.append(("pre", parts[0], ""))
    index = 1
    while index < len(parts):
        heading = parts[index]
        after = parts[index + 1] if index + 1 < len(parts) else ""
        level = "h1" if heading.startswith("<h1>") else "h2"
        items.append((level, heading, after))
        index += 2

    cover = {"kind": "cover", "heading": "", "chunks": []}
    rest = []
    took_title = False
    for level, heading, after in items:
        if level == "pre":
            cover["chunks"].append(heading)
            continue
        if level == "h1" and not took_title:
            cover["heading"] = heading
            cover["chunks"].append(heading)
            cover["chunks"].append(after)
            took_title = True
            continue
        kind = "part" if level == "h1" else "chapter"
        rest.append({"kind": kind, "heading": heading, "chunks": [heading, after]})
    sections = [cover] + rest

    rendered = []
    for sec in sections:
        title = strip_tags(sec["heading"])
        if sec["kind"] == "cover":
            inner = "\n".join(sec["chunks"])
            inner = re.sub(r"<h1>.*?</h1>", "", inner, count=1, flags=re.S)
            meta = ""
            if "<table" not in inner:
                meta = '<p class="meta">二〇二六年十月</p>'
            block = (
                '<section class="cover" style="page: cover">'
                f"<h1>{book_title}</h1>"
                f'<div class="rule"></div>'
                f"{meta}{inner}</section>"
            )
        elif sec["kind"] == "part":
            inner = "\n".join(sec["chunks"])
            block = f'<section class="part">{inner}</section>'
        else:
            inner = "\n".join(sec["chunks"])
            if title == "目录":
                inner = toc_links(inner)
                klass = "chapter toc"
            else:
                klass = "chapter"
            block = f'<section class="{klass}">{inner}</section>'
        rendered.append(block)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{book_title}</title>
<style>
{CSS}
</style>
</head>
<body>
{''.join(rendered)}
</body>
</html>
"""
    return tighten_latin(html)


def add_outline(pdf_path):
    """Write a bookmark tree so readers can jump by chapter."""
    import fitz

    doc = fitz.open(pdf_path)
    found = []
    for index, page in enumerate(doc):
        if index == 0:
            continue
        lines = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                size = max(span["size"] for span in spans)
                if size < 14.5:
                    continue
                text = "".join(span["text"] for span in spans).strip()
                if text:
                    lines.append((line["bbox"][1], text, size))
        lines.sort()
        merged = []
        for y, text, size in lines:
            if (
                merged
                and abs(y - merged[-1][0]) < 30
                and abs(size - merged[-1][2]) < 2
            ):
                merged[-1][1] += text
            else:
                merged.append([y, text, size])
        for _y, text, size in merged:
            found.append((index + 1, size, norm(text)))

    toc = []
    in_part = False
    seen = set()
    for page, size, title in found:
        if title in seen or title == "习题":
            continue
        seen.add(title)
        if size >= 20:
            toc.append([1, title, page])
            in_part = True
        else:
            toc.append([2 if in_part else 1, title, page])
    doc.set_toc(toc, collapse=0)
    doc.set_pagemode("UseOutlines")
    tmp = pdf_path.with_suffix(".outline.pdf")
    doc.save(tmp)
    doc.close()
    tmp.replace(pdf_path)
    return len(toc)


def print_pdf(html_path, pdf_path):
    subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def write_book(md_path, book_title, html_name, pdf_path):
    html_path = OUT / html_name
    html = build_html(md_path, book_title)
    html_path.write_text(html)
    if 'data-toc="' not in html:
        print_pdf(html_path, pdf_path)
        count = add_outline(pdf_path)
        print(pdf_path.name, pdf_path.stat().st_size, "bookmarks", count)
        return

    draft = OUT / "full-pass1.pdf"
    print_pdf(html_path, draft)
    pages = heading_pages(draft)
    html, missing = fill_toc(html, pages)
    if missing:
        print("TOC without page:", " | ".join(missing))
    html_path.write_text(html)
    print_pdf(html_path, pdf_path)

    printed = toc_numbers(pdf_path)
    actual = heading_pages(pdf_path)
    drifted = []
    for title, page in actual.items():
        shown = printed.get(title)
        if shown is not None and shown != page:
            drifted.append(f"{title}: toc {shown} body {page}")
    if drifted:
        html, missing = fill_toc(html, actual)
        html_path.write_text(html)
        print_pdf(html_path, pdf_path)
        print("TOC shifted, reprinted")
        if missing:
            print("TOC without page:", " | ".join(missing))
    count = add_outline(pdf_path)
    print(pdf_path.name, pdf_path.stat().st_size, "bookmarks", count)


def main():
    write_book(
        ROOT / "小学英语词汇整理手册-精简本.md",
        "小学英语词汇 · 精简本",
        "slim-book.html",
        ROOT / "小学英语词汇整理手册-精简本.pdf",
    )
    write_book(
        ROOT / "小学英语词汇整理手册.md",
        "小学英语词汇整理手册",
        "full-book.html",
        ROOT / "小学英语词汇整理手册.pdf",
    )
    write_book(
        ROOT / "初中英语学习辅导手册.md",
        "初中英语学习辅导手册",
        "junior-book.html",
        ROOT / "初中英语学习辅导手册.pdf",
    )
    write_book(
        ROOT / "自然拼读.md",
        "自然拼读",
        "phonics-book.html",
        ROOT / "自然拼读.pdf",
    )
    write_book(
        ROOT / "小学英语-KET-PET整理.md",
        "小学英语、PET、KET 整理",
        "ket-pet-book.html",
        ROOT / "小学英语-KET-PET整理.pdf",
    )


if __name__ == "__main__":
    main()
