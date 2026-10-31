#!/usr/bin/env python3
"""Typeset the handbooks as printed books and write PDFs via headless Chrome."""

import html as html_lib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/tmp/pylibs")

import markdown

ROOT = Path(__file__).resolve().parent.parent


def find_chrome():
    """Locate a headless-capable Chrome/Chromium binary for the current OS."""
    if os.name == "nt":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    else:
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    raise SystemExit("No Chrome/Chromium/Edge found; cannot print PDF.")


def find_markdown_lib():
    """Import markdown from the isolated virtualenv if the default env lacks it."""
    try:
        return __import__("markdown")
    except ImportError:
        pass
    home = Path(os.path.expanduser("~"))
    guesses = [
        home / ".workbuddy/binaries/python/envs/default/Lib/site-packages",
        home / ".workbuddy/binaries/python/envs/default/lib/python3.13/site-packages",
    ]
    for path in guesses:
        if path.exists():
            sys.path.insert(0, str(path))
            return __import__("markdown")
    raise SystemExit("markdown module not found; install it in the isolated venv.")


markdown = find_markdown_lib()

OUT = Path(tempfile.gettempdir()) / "english-learn-pdf"
OUT.mkdir(exist_ok=True)
CHROME = find_chrome()
IMG = ROOT.as_uri() + "/images/"

CN_DIGIT = {ch: i for i, ch in enumerate("零一二三四五六七八九")}

# GB/T 18358-2009: 订口 13mm、切口 10mm、天头 15mm、地脚 17mm；
# 版心 152×228mm → 成品 175×260mm。
CSS = r"""
@page {
  size: 175mm 260mm;
  margin-top: 15mm;
  margin-bottom: 17mm;
  @bottom-center {
    content: counter(page);
    font-family: "Times New Roman", "Arial", "Songti SC", sans-serif;
    font-size: 9pt;
    font-weight: 600;
    color: #1a4f82;
  }
}
@page:left {
  margin-left: 10mm;
  margin-right: 13mm;
  @bottom-left { content: none; }
  @bottom-right { content: none; }
  @bottom-center {
    content: counter(page);
    font-family: "Times New Roman", "Arial", "Songti SC", sans-serif;
    font-size: 9pt;
    font-weight: 600;
    color: #1a4f82;
    padding-left: 1.5mm;
  }
}
@page:right {
  margin-left: 13mm;
  margin-right: 10mm;
  @bottom-left { content: none; }
  @bottom-right { content: none; }
  @bottom-center {
    content: counter(page);
    font-family: "Times New Roman", "Arial", "Songti SC", sans-serif;
    font-size: 9pt;
    font-weight: 600;
    color: #1a4f82;
    padding-right: 1.5mm;
  }
}
@page:first {
  margin: 15mm 10mm 17mm 13mm;
  @bottom-left { content: none; }
  @bottom-right { content: none; }
  @bottom-center { content: none; }
}
@page cover {
  size: 175mm 260mm;
  margin: 15mm 10mm 17mm 13mm;
  @bottom-left { content: none; }
  @bottom-right { content: none; }
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
  margin: 52mm 0 0;
  text-align: center;
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-size: 26pt;
  font-weight: 600;
  letter-spacing: 0.12em;
  line-height: 1.45;
  color: #1a4f82;
}
.latin { letter-spacing: 0; }
.cover .rule {
  width: 36mm;
  border: none;
  border-top: 3.2pt solid #1f6fb2;
  margin: 8mm auto 0;
  height: 0;
}
.cover .meta {
  text-align: center;
  margin-top: 8mm;
  letter-spacing: 0.32em;
  font-size: 11pt;
  color: #1a4f82;
}
.cover p { text-align: center; }
.cover table {
  width: 88%;
  margin: 18mm auto 0;
  font-size: 10pt;
}

section.part h1 {
  margin: 72mm 0 0;
  text-align: center;
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-size: 22pt;
  font-weight: 600;
  letter-spacing: 0.2em;
  color: #1a4f82;
}
section.part h1::after {
  content: "";
  display: block;
  width: 22mm;
  margin: 8mm auto 0;
  border-top: 3.2pt solid #1f6fb2;
}

h2 {
  margin: 0 0 0.75em;
  padding: 5pt 8pt 4.5pt;
  font-size: 16pt;
  letter-spacing: 0.04em;
  color: #fff;
  background: #1f6fb2;
}
h3 {
  margin: 1.05em 0 0.35em;
  padding: 1pt 0 1pt 6pt;
  font-size: 12pt;
  letter-spacing: 0.04em;
  color: #1a4f82;
  border-left: 3.2pt solid #1f6fb2;
}
p.exercise {
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-weight: 600;
  font-size: 12pt;
  line-height: 1.35;
  letter-spacing: 0.04em;
  margin: 1.05em 0 0.35em;
  padding: 1pt 0 1pt 6pt;
  text-indent: 0;
  text-align: left;
  color: #c45c12;
  border-left: 3.2pt solid #e07b2a;
  break-after: avoid;
  page-break-after: avoid;
}
section.toc {
  column-count: 2;
  column-gap: 8mm;
  column-rule: 0.5pt solid #dfe8f0;
}
section.toc h2, section.toc h3 {
  break-after: avoid;
  page-break-after: avoid;
}
section.toc ul { break-inside: avoid; page-break-inside: avoid; }
section.toc h3 {
  border-left: none;
  padding-left: 0;
  color: #1a4f82;
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
  border-bottom: 0.6pt dotted #8eb4d4;
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
  padding: 0.15em 0.4em 0.15em 0.75em;
  border-left: 3pt solid #1f6fb2;
  background: #f3f8fc;
  color: #1c1916;
  break-inside: avoid;
  page-break-inside: avoid;
}
blockquote p { margin: 0.15em 0; }

p.tablecap {
  text-align: center;
  text-indent: 0;
  margin: 0.85em 0 0.2em;
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-size: 10.5pt;
  font-weight: 600;
  color: #1a4f82;
  break-after: avoid;
  page-break-after: avoid;
}

/* 三线表：顶线、栏目线、底线；无竖线、无行间横线（课本 / CY/T 170） */
table {
  width: 100%;
  max-width: 100%;
  table-layout: auto;
  border-collapse: collapse;
  border-spacing: 0;
  margin: 0.15em auto 0.9em;
  font-size: 10pt;
  line-height: 1.45;
  border-top: 1.5pt solid #1c1916;
  border-bottom: 1.5pt solid #1c1916;
}
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td {
  border: none;
  padding: 3.6pt 6pt;
  vertical-align: middle;
  text-align: center;
  font-weight: 400;
  overflow-wrap: break-word;
  word-break: normal;
  line-break: strict;
}
th {
  font-family: "Hiragino Sans GB", "STHeiti", sans-serif;
  font-weight: 600;
  font-size: 10pt;
  letter-spacing: 0.04em;
  color: #1c1916;
  background: transparent;
  border-bottom: 0.75pt solid #1c1916;
  padding-top: 4.5pt;
  padding-bottom: 4pt;
  white-space: nowrap;
}
span.ipa { white-space: nowrap; font-family: "Times New Roman", "Songti SC", serif; color: #4e5964; }
tbody tr:last-child td { border-bottom: none; }
table.vocab td:first-child {
  font-family: Arial, "Helvetica Neue", "Hiragino Sans GB", "Songti SC", sans-serif;
  font-weight: 700;
  color: #1a4f82;
  white-space: nowrap;
}
table.wide { font-size: 10pt; line-height: 1.35; }
table.wide th { white-space: normal; }
table.wide th, table.wide td { padding: 2.6pt 3.2pt; }

figure {
  margin: 0.7em 0 0.9em;
  break-inside: avoid;
  page-break-inside: avoid;
}
img {
  display: block;
  max-width: 100%;
  max-height: 200mm;
  margin: 0 auto;
}
figcaption {
  margin-top: 0.35em;
  text-align: center;
  font-family: "Hiragino Sans GB", "STHeiti", "Songti SC", sans-serif;
  font-size: 10.5pt;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #1a4f82;
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


def mark_vocab_tables(html):
    """Mark word tables so headwords can keep textbook styling."""

    def repl(match):
        table = match.group(0)
        first = re.search(r"<tr\b.*?</tr>", table, re.S)
        if not first:
            return table
        heads = [
            strip_tags(cell)
            for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", first.group(0), re.S)
        ]
        if heads[:4] != ["词条", "音标", "释义", "说明"]:
            return table
        table = table.replace("<table>", '<table class="vocab">', 1)
        return table.replace('<table class="wide">', '<table class="vocab wide">', 1)

    return re.sub(r"<table\b.*?</table>", repl, html, flags=re.S)


def protect_cell_text(html):
    """Keep a mark with its word, and keep each phonetic transcription intact."""

    def repl(match):
        inner = match.group(2)
        inner = re.sub(r"([★○◆●]) ", "\\1\u00a0", inner)
        inner = re.sub(
            r"/[^/<>\s]+/",
            lambda token: f'<span class="ipa">{token.group(0)}</span>',
            inner,
        )
        return match.group(1) + inner + match.group(3)

    return re.sub(r"(<td[^>]*>)(.*?)(</td>)", repl, html, flags=re.S)


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


def collect_headings(doc):
    """Collect (page, size, title) for every heading line in the body.

    Three levels are wanted: part titles (h1, ~22pt), chapter titles (h2, 16pt)
    and section titles (h3, 12pt). Body text sits at 10.5pt, so a 10.8pt floor
    separates headings from prose. Two things must be excluded: the printed
    table of contents (its entries repeat every heading) and the orange
    “习题” paragraphs, which share the h3 size but are not headings.
    """
    ORANGE = 0xC45C12

    toc_start = None
    toc_end = None
    for index, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                text = "".join(s["text"] for s in line["spans"]).strip()
                if text == "目录":
                    toc_start = index
    if toc_start is not None:
        for index in range(toc_start + 1, doc.page_count):
            page = doc[index]
            hit = False
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block["lines"]:
                    size = max((s["size"] for s in line["spans"]), default=0)
                    if size >= 20:
                        toc_end = index
                        hit = True
                        break
                if hit:
                    break
            if hit:
                break
    if toc_end is None:
        toc_end = toc_start + 1 if toc_start is not None else 0

    found = []
    for index, page in enumerate(doc):
        if index == 0:
            continue  # cover: its 12pt subtitle would read as a heading
        if toc_start is not None and toc_start <= index < toc_end:
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
                if size < 10.8:
                    continue
                if any(span.get("color") == ORANGE for span in spans):
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
    return found


def heading_pages(pdf_path):
    import fitz

    doc = fitz.open(pdf_path)
    found = {}
    for page, size, title in collect_headings(doc):
        found.setdefault(title, page)
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


def add_heading_ids(html):
    """Give every heading the slug id that the table of contents links to.

    The TOC is authored in Markdown with GitHub-style anchors such as
    ``#第一章-人体部位``. Headless Chrome keeps those ``href`` values but the
    headings themselves carry no ``id``, so every TOC entry pointed at nothing
    and the printed PDF had no clickable links. Adding the same slug to each
    heading makes them resolve; PyMuPDF then carries them over as PDF links.
    """

    def slug(text):
        out = strip_tags(text).strip().lower()
        out = re.sub(r"[`*_~\[\]()]", "", out)
        out = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", out)
        out = out.replace(" ", "-")
        out = re.sub(r"-+", "-", out)
        return out.strip("-")

    seen = {}

    def repl(match):
        tag, attrs, inner = match.group(1), match.group(2), match.group(3)
        if 'id="' in attrs:
            return match.group(0)
        base = slug(inner) or "section"
        # Duplicate slugs get a numeric suffix, matching GitHub's behaviour.
        if base in seen:
            seen[base] += 1
            anchor = f"{base}-{seen[base]}"
        else:
            seen[base] = 0
            anchor = base
        return f'<{tag}{attrs} id="{anchor}">{inner}</{tag}>'

    return re.sub(
        r"<(h[1-4])([^>]*)>(.*?)</\1>", repl, html, flags=re.S
    )


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


def measure_text(text):
    """Estimate rendered width in em units.

    CJK characters occupy a full em; Latin letters and digits about half.
    Punctuation and spaces are narrower. The result drives column widths, so
    overestimating slightly is safer than underestimating.
    """
    width = 0.0
    for ch in text:
        code = ord(ch)
        if code == 0x00A0:
            width += 0.3
        elif 0x2E80 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF or 0xFF00 <= code <= 0xFFEF:
            width += 1.0
        elif 0x0250 <= code <= 0x02AF:
            # IPA symbols are roughly Latin width
            width += 0.55
        elif ch in "ijlI.,;:!|'` ":
            width += 0.28
        elif ch in "mwMW":
            width += 0.85
        elif ch.isupper():
            width += 0.68
        else:
            width += 0.52
    return width


def _is_cjk(code):
    return (
        0x2E80 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0xFF00 <= code <= 0xFFEF
    )


def longest_tokens(cell_html):
    """Widths of the runs inside a cell that truly cannot be broken.

    IPA transcriptions are wrapped in ``span.ipa`` with ``white-space: nowrap``,
    so each of them counts whole. Latin words, numbers and dates cannot break
    either. Chinese is different: a line may break between any two characters,
    so a CJK run only needs room for a couple of characters (plus any closing
    punctuation that sticks to them), not for the whole sentence. Treating a
    sixteen-character Chinese cell as unbreakable used to starve the narrow
    columns of exactly the tables that had room to spare.
    """
    atomic = re.findall(r'<span class="ipa">([^<]*)</span>', cell_html)
    rest = re.sub(r'<span class="ipa">[^<]*</span>', " ", cell_html)
    rest = strip_tags(rest)
    widths = [measure_text(t) for t in atomic]
    for token in re.split(r"[\s,;，；、]+", rest):
        if not token:
            continue
        run = 0.0
        best = 0.0
        saw_cjk = False
        for ch in token:
            if _is_cjk(ord(ch)):
                saw_cjk = True
                run = 0.0
            else:
                run += measure_text(ch)
                best = max(best, run)
        if saw_cjk:
            # Any CJK run can wrap; keep room for two characters so a line
            # never ends up holding a single lonely glyph.
            best = max(best, 2.0)
        else:
            best = max(best, measure_text(token))
        widths.append(best)
    return widths


def set_column_widths(html, avail_em=43.0):
    """Give every table explicit column widths based on its own content.

    Browsers lay out ``table-layout: auto`` from *minimum* content widths. With
    Chinese text that minimum is almost nothing, so a column holding ``I`` or
    ``me`` gets the same share as one holding ``形容词性物主``, and long cells
    wrap while short ones sit in empty space. Measuring the real content fixes
    that: each column first claims the width of its longest unbreakable token,
    then the leftover page width is shared in proportion to how much text the
    column actually carries.

    ``avail_em`` is the table's real rendered width in em. Cover tables are
    narrower than the text block (88%), so they must be measured against a
    smaller budget or their narrow columns get squeezed into wrapping.
    """
    pad = 1.2        # horizontal cell padding, in em

    def repl(match):
        table = match.group(0)
        tag_match = re.match(r"<table\b[^>]*>", table)
        if not tag_match:
            return table
        rows = re.findall(r"<tr\b.*?</tr>", table, flags=re.S)
        if not rows:
            return table

        raw_rows = []
        for row in rows:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)
            if cells:
                raw_rows.append(cells)
        columns = max(len(row) for row in raw_rows)
        if columns < 2:
            return table

        demand = [0.0] * columns
        floor = [0.0] * columns
        for row in raw_rows:
            for index, cell in enumerate(row):
                if index >= columns:
                    continue
                text = strip_tags(cell)
                demand[index] = max(demand[index], measure_text(text))
                for token in longest_tokens(cell):
                    floor[index] = max(floor[index], token)

        floors = [min(f, 10.0) + pad for f in floor]
        total_floor = sum(floors)
        if total_floor >= avail_em:
            # Not enough room even after capping long columns. Keep every
            # short column intact (its tokens must not wrap) and squeeze only
            # the capped long-text columns, which can break mid-run in CJK.
            short = [i for i in range(columns) if floor[i] <= 10.0]
            long = [i for i in range(columns) if floor[i] > 10.0]
            reserved = sum(floors[i] for i in short)
            if reserved >= avail_em:
                # Even the short columns alone overflow; fall back to an even
                # proportional split and accept wrapping everywhere.
                scale = avail_em / total_floor
                widths = [f * scale for f in floors]
            else:
                widths = [0.0] * columns
                for i in short:
                    widths[i] = floors[i]
                leftover = avail_em - reserved
                total_long = sum(floors[i] for i in long) or 1.0
                for i in long:
                    widths[i] = leftover * floors[i] / total_long
        else:
            soft = [min(d + pad, 16.0) for d in demand]
            extra_need = [max(0.0, soft[i] - floors[i]) for i in range(columns)]
            spare = avail_em - total_floor
            total_extra = sum(extra_need)
            widths = list(floors)
            if total_extra > 0:
                for i in range(columns):
                    widths[i] += spare * extra_need[i] / total_extra

        share = [100.0 * w / avail_em for w in widths]

        colgroup = "<colgroup>" + "".join(
            f'<col style="width:{s:.2f}%">' for s in share
        ) + "</colgroup>"

        tag = tag_match.group(0)
        if "table-layout" not in tag:
            tag = tag[:-1] + ' style="table-layout:fixed">'
        return tag + colgroup + table[tag_match.end():]

    return re.sub(r"<table\b.*?</table>", repl, html, flags=re.S)


def build_html(md_path, book_title):
    text = md_path.read_text()
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    body = decorate(body)
    body = mark_wide_tables(body)
    body = mark_vocab_tables(body)
    body = protect_cell_text(body)
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
            # Cover tables render at 88% of the text block; measure against that.
            inner = set_column_widths(inner, avail_em=43.0 * 0.88)
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
            inner = set_column_widths("\n".join(sec["chunks"]))
            block = f'<section class="part">{inner}</section>'
        else:
            inner = set_column_widths("\n".join(sec["chunks"]))
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
    html = add_heading_ids(html)
    return tighten_latin(html)


def add_outline(pdf_path):
    """Write a bookmark tree so readers can jump by chapter."""
    import fitz

    doc = fitz.open(pdf_path)
    found = collect_headings(doc)

    toc = []
    seen = set()
    has_part = any(re.match(r'^第[一二三四五六七八九十]+部分', t) for _p, _s, t in found)
    last = 0
    for page, size, title in found:
        if title in seen or title == "习题":
            continue
        seen.add(title)
        if re.match(r'^第[一二三四五六七八九十]+部分', title):
            level = 1
        elif re.match(r'^第[一二三四五六七八九十]+章', title):
            level = 2 if has_part else 1
        elif size >= 14.5:
            level = 2 if has_part else 1
        else:
            level = 3 if has_part else 2
        # PDF outlines may only deepen one level at a time.
        level = min(level, last + 1)
        last = level
        toc.append([level, title, page])
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
        ROOT / "小学英语辅导手册-学生本.md",
        "小学英语辅导手册 · 学生本",
        "slim-book.html",
        ROOT / "小学英语辅导手册-学生本.pdf",
    )
    write_book(
        ROOT / "小学英语辅导手册.md",
        "小学英语辅导手册",
        "full-book.html",
        ROOT / "小学英语辅导手册.pdf",
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
        ROOT / "小学英语-KET-PET辅导手册.md",
        "小学英语 · KET · PET 辅导手册",
        "ket-pet-book.html",
        ROOT / "小学英语-KET-PET辅导手册.pdf",
    )


if __name__ == "__main__":
    main()
