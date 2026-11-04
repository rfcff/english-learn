"""Shared constants and helpers for the english-learn-books scripts.

Imported by build_books.py, check_books.py, rebuild_toc.py and
check_layout.py. Every script is launched as ``python <dir>/script.py``, so
Python puts this directory on sys.path and a plain ``import booklib`` works
from any working directory.

The single most important item here is ``slug``: the TOC anchors written by
rebuild_toc.py, the heading ids injected by build_books.add_heading_ids and
the anchor validation in check_books.py must agree character-for-character,
so they all import this one implementation. Duplicating it in three files
was a standing invitation to drift.
"""

import html as html_lib
import re
from pathlib import Path

# <repo>/.workbuddy/skills/english-learn-books/scripts/booklib.py
ROOT = Path(__file__).resolve().parents[4]

# Book metadata — the single source of truth for all five scripts.
# (markdown file, book title shown on cover, print HTML name, PDF name)
BOOKS = [
    ('小学英语辅导手册-学生本.md', '小学英语辅导手册 · 学生本',
     'slim-book.html', '小学英语辅导手册-学生本.pdf'),
    ('小学英语辅导手册.md', '小学英语辅导手册',
     'full-book.html', '小学英语辅导手册.pdf'),
    ('初中英语学习辅导手册.md', '初中英语学习辅导手册',
     'junior-book.html', '初中英语学习辅导手册.pdf'),
    ('自然拼读.md', '自然拼读',
     'phonics-book.html', '自然拼读.pdf'),
    ('小学英语-KET-PET辅导手册.md', '小学英语 · KET · PET 辅导手册',
     'ket-pet-book.html', '小学英语-KET-PET辅导手册.pdf'),
    ('药品生产质量管理规范(GMP)单词手册.md', '药品生产质量管理规范（GMP）单词手册',
     'gmp-book.html', '药品生产质量管理规范(GMP)单词手册.pdf'),
]
BOOK_NAMES = [b[0] for b in BOOKS]

# rebuild_toc.py: books with 部分/章 structure get the three-level TOC;
# the student book (flat `## 一、…` sections) gets the lite TOC.
LITE = ['小学英语辅导手册-学生本.md']
STRUCTURED = [n for n in BOOK_NAMES if n not in LITE]

# Chinese numerals as an index table (check_books: 第X章 → number).
CN = [''] + [
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
    '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八',
    '二十九', '三十', '三十一', '三十二', '三十三', '三十四', '三十五', '三十六',
    '三十七', '三十八', '三十九', '四十', '四十一', '四十二', '四十三', '四十四',
    '四十五', '四十六', '四十七', '四十八', '四十九', '五十',
    '五十一', '五十二', '五十三', '五十四', '五十五', '五十六', '五十七', '五十八',
    '五十九', '六十',
]

CN_DIGIT = {ch: i for i, ch in enumerate("零一二三四五六七八九")}


def cn_to_n(text):
    """Index into CN, or -1. Covers the numerals the books actually use."""
    return CN.index(text) if text in CN else -1


def cn_to_int(token):
    """Parse arbitrary Chinese numerals (build_books: 第X章 / 图 N-M)."""
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


def slug(text):
    """GitHub-style anchor for a heading.

    rebuild_toc.py writes TOC links with this, build_books.add_heading_ids
    stamps heading ids with this, check_books.py validates anchors against
    this. One implementation, no drift.
    """
    out = text.strip().lower()
    out = re.sub(r'[`*_~\[\]()]', '', out)
    out = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', out)
    out = out.replace(' ', '-')
    out = re.sub(r'-+', '-', out)
    return out.strip('-')


def strip_tags(fragment):
    text = re.sub(r"<[^>]+>", "", fragment)
    return html_lib.unescape(text).strip()


def head_text(cell):
    """Plain text of a table cell, HTML stripped."""
    return strip_tags(cell)


def header_period(header):
    """Shortest repeating unit length of a plain-text header row, else None.

    ``单词|音标|意思|单词|音标|意思`` → 3 (k=2), ``现在|过去`` ×3 → 2, a header
    with no repetition → None. build_books.set_column_widths splits the row
    into k equal groups on this, and check_layout re-derives the same k to
    verify each group got its 1/k share — one implementation, no drift.
    """
    n = len(header)
    for u in range(1, n // 2 + 1):
        if (n % u == 0 and n // u >= 2 and header[0]
                and all(header[j] == header[j % u] for j in range(n))):
            return u
    return None


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def resolve(arg):
    """Interpret a CLI path against the repo root, like every script does."""
    p = Path(arg)
    return p if p.is_absolute() else ROOT / p
