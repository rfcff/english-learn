#!/usr/bin/env python3
"""Validate the English handbooks in this repository.

Runs every structural check the books depend on, so an edit can be verified
without re-deriving the checks each time:

  * chapter numbers run 1..N with no gap or duplicate
  * inside each chapter, section numbers (N.M) and table numbers (N-M) run
    from 1 and carry the chapter prefix
  * Markdown tables have a consistent column count and a blank line before them
  * cross references (``12.3``, ``表 12-3``, ``第X章``, ``第X部分``) all resolve
  * table-of-contents links match a heading slug (GitHub rules)
  * heading levels never skip
  * no leftover placeholders, no duplicate chapter/table titles, no empty tables
  * the four-book chapter mapping still holds (see references/book-map.md)

Usage:
    python scripts/check_books.py              # check every book
    python scripts/check_books.py 自然拼读.md   # check selected books

Exit code is 1 when any check fails.
"""

import io
import re
import sys
from pathlib import Path

# <repo>/.workbuddy/skills/english-learn-books/scripts/check_books.py
ROOT = Path(__file__).resolve().parents[4]

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

# Books that carry 部分/章 structure, and the offsets that tie them together.
# Key = child book, value = (master book, [(child_lo, child_hi, offset), ...]).
# An offset is added to the child chapter number to get the master chapter number.
#
# The KET-PET book mirrors the master book minus the phonics part (master 1-8),
# so a single +8 offset covers its whole 41 chapters:
#   child 1-17  topic vocabulary   = master 9-25
#   child 18-30 memory methods     = master 26-38
#   child 31-36 grammar system     = master 39-44
#   child 37-41 KET / PET papers   = master 45-49
MAPPING = {
    '自然拼读.md': ('小学英语辅导手册.md', [(1, 8, 0)]),
    '小学英语-KET-PET辅导手册.md': ('小学英语辅导手册.md', [(1, 41, 8)]),
}

# Chapter titles that legitimately differ between the master and a child book.
TITLE_DIFF_OK = {
    (17, '时态', '三大时态'),
}

BOOKS = [
    '小学英语辅导手册.md',
    '小学英语-KET-PET辅导手册.md',
    '小学英语辅导手册-学生本.md',
    '自然拼读.md',
    '初中英语学习辅导手册.md',
]


def slug(text):
    """Reproduce build_books.add_heading_ids slug rules exactly."""
    out = text.strip().lower()
    out = re.sub(r'[`*_~\[\]()]', '', out)
    out = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', out)
    out = out.replace(' ', '-')
    out = re.sub(r'-+', '-', out)
    return out.strip('-')


def is_sep(line):
    """True for a Markdown table delimiter row."""
    if not line.startswith('|'):
        return False
    body = line.replace('|', '').replace('-', '').replace(':', '').replace(' ', '')
    return body == ''


def cn_to_n(text):
    return CN.index(text) if text in CN else -1


class Report:
    def __init__(self, name):
        self.name = name
        self.errors = []
        self.notes = []

    def err(self, msg):
        self.errors.append(msg)

    def note(self, msg):
        self.notes.append(msg)

    @property
    def ok(self):
        return not self.errors


def chapters_of(lines):
    """Return [(number, title, line_index)] for every ``## 第X章 ...``."""
    out = []
    for i, l in enumerate(lines):
        m = re.match(r'^## 第([一二三四五六七八九十]+)章 (.+)$', l)
        if m:
            out.append((cn_to_n(m.group(1)), m.group(2), i))
    return out


def parts_of(lines):
    out = []
    for i, l in enumerate(lines):
        m = re.match(r'^# (第[一二三四五六七八九十]+部分 .+)$', l)
        if m:
            out.append((m.group(1), i))
    return out


def check_numbering(rep, lines):
    chaps = chapters_of(lines)
    if not chaps:
        rep.note('无「第X章」结构（学生本按一、二、三编排）')
        return
    nums = [c[0] for c in chaps]
    if nums != list(range(1, len(nums) + 1)):
        missing = [i for i in range(1, len(nums) + 1) if i not in nums]
        dup = sorted({n for n in nums if nums.count(n) > 1})
        rep.err('章号不连续：共 %d 章，缺 %s，重 %s' % (len(nums), missing, dup))

    # Per-chapter section and table numbering.
    cur = None
    tabs, secs = {}, {}
    for l in lines:
        m = re.match(r'^## 第([一二三四五六七八九十]+)章', l)
        if m:
            cur = cn_to_n(m.group(1))
            tabs[cur], secs[cur] = [], []
        elif l.startswith('## ') or l.startswith('# '):
            cur = None
        if cur is None:
            continue
        mt = re.match(r'^表 (\d+)-(\d+)\u3000', l)
        if mt:
            tabs[cur].append((int(mt.group(1)), int(mt.group(2))))
        ms = re.match(r'^### (\d+)\.(\d+) ', l)
        if ms:
            secs[cur].append((int(ms.group(1)), int(ms.group(2))))
    for c in sorted(tabs):
        if tabs[c]:
            if any(a != c for a, b in tabs[c]):
                rep.err('第%d章 表号前缀与章号不符：%s' % (c, tabs[c]))
            if [b for a, b in tabs[c]] != list(range(1, len(tabs[c]) + 1)):
                rep.err('第%d章 表号不连续：%s' % (c, [b for a, b in tabs[c]]))
        if secs[c]:
            if any(a != c for a, b in secs[c]):
                rep.err('第%d章 小节号前缀与章号不符：%s' % (c, secs[c]))
            if [b for a, b in secs[c]] != list(range(1, len(secs[c]) + 1)):
                rep.err('第%d章 小节号不连续：%s' % (c, [b for a, b in secs[c]]))
    rep.note('%d 章，%d 张编号表' % (len(chaps), sum(len(v) for v in tabs.values())))


def check_tables(rep, lines):
    blocks = 0
    i = 0
    while i < len(lines):
        if lines[i].startswith('|') and i + 1 < len(lines) and is_sep(lines[i + 1]):
            ncol = lines[i].count('|')
            blocks += 1
            j = i
            while j < len(lines) and lines[j].startswith('|'):
                if lines[j].count('|') != ncol:
                    rep.err('表格列数不一致 第%d行（应 %d 列，实 %d 列）'
                            % (j + 1, ncol, lines[j].count('|')))
                j += 1
            rows = j - i - 2
            if rows <= 0:
                rep.err('空表 第%d行：%s' % (i + 1, lines[i][:48]))
            elif rows <= 1:
                rep.note('单行表 第%d行：%s' % (i + 1, lines[i][:48]))
            i = j
        else:
            i += 1
    for i in range(1, len(lines)):
        if (lines[i].startswith('|') and lines[i - 1].strip()
                and not lines[i - 1].startswith('|')):
            rep.err('表格前缺空行 第%d行' % (i + 1))
    rep.note('%d 张表' % blocks)


def collect_anchors(lines):
    secs, tabs, heads = set(), set(), set()
    for l in lines:
        m = re.match(r'^### (\d+\.\d+) ', l)
        if m:
            secs.add(m.group(1))
        m = re.match(r'^表 (\d+-\d+)\u3000', l)
        if m:
            tabs.add(m.group(1))
        m = re.match(r'^(#{1,6}) (.+)$', l)
        if m:
            heads.add(slug(m.group(2)))
    return secs, tabs, heads


def check_references(rep, lines, secs, tabs, heads):
    chap_nums = {c[0] for c in chapters_of(lines)}
    part_names = {p[0] for p in parts_of(lines)}
    bad = []
    for i, l in enumerate(lines):
        if l.startswith('#') or l.startswith('- [') or l.startswith('  - ['):
            continue
        if l.startswith('表 '):
            continue
        for m in re.finditer(r'(?<![\d.])(\d{1,2})\.(\d{1,2})(?![\d])', l):
            ref = '%s.%s' % m.groups()
            ctx = l[max(0, m.start() - 25):m.end() + 8]
            # Dates, versions and ratios are not section references.
            if re.search(r'\d{4}|年|月|版本|/', ctx):
                continue
            if ref not in secs:
                bad.append('第%d行 小节引用 %s 不存在' % (i + 1, ref))
        for m in re.finditer(r'表 (\d{1,2})-(\d{1,2})(?![\d])', l):
            if '%s-%s' % m.groups() not in tabs:
                bad.append('第%d行 表引用 %s 不存在' % (i + 1, m.group(0)))
        for m in re.finditer(r'第([一二三四五六七八九十]+)章', l):
            if chap_nums and cn_to_n(m.group(1)) not in chap_nums:
                bad.append('第%d行 章引用 %s 不存在' % (i + 1, m.group(0)))
        for m in re.finditer(r'第([一二三四五六七八九十]+)部分', l):
            ref = m.group(0)
            if part_names and not any(ref in p for p in part_names):
                # The KET/PET papers are described in terms of their own
                # “第六部分/第七部分”, which is not a part of this book.
                if not re.search(r'卷面|阅读|写作|七个部分|五个部分|前五个', l):
                    bad.append('第%d行 部分引用 %s 不存在' % (i + 1, ref))
    for b in bad:
        rep.err(b)
    rep.note('交叉引用 %d 处问题' % len(bad))


def check_toc(rep, lines, heads):
    links = []
    for i, l in enumerate(lines):
        for m in re.finditer(r'\]\(#([^)]+)\)', l):
            links.append((i + 1, m.group(1)))
    bad = [(n, a) for n, a in links if a not in heads]
    for n, a in bad:
        rep.err('第%d行 目录链接 #%s 无对应标题' % (n, a))
    rep.note('目录链接 %d 个' % len(links))


def check_headings(rep, lines):
    levels = []
    for i, l in enumerate(lines):
        m = re.match(r'^(#{1,6}) ', l)
        if m:
            levels.append((i + 1, len(m.group(1))))
    jumps = [(a, b, la, lb) for (a, la), (b, lb) in zip(levels, levels[1:]) if lb > la + 1]
    for a, b, la, lb in jumps:
        rep.err('标题跳级：第%d行 h%d → 第%d行 h%d' % (a, la, b, lb))


def check_placeholders(rep, lines):
    # “占位” is excluded: the books legitimately say that a formal subject
    # “占住主语的位置”, so it would be a false positive.
    pat = re.compile(r'@@|@CN|@C\d+@|@A\d+@|TODO|FIXME|待补|XXX|待定')
    for i, l in enumerate(lines):
        if pat.search(l):
            rep.err('第%d行 疑似占位符：%s' % (i + 1, l.strip()[:60]))


def check_table_heading_gap(rep, lines):
    """A heading directly after a table row is swallowed by the table.

    Markdown keeps parsing until a blank line, so `### N.M 习题` right after a
    `|...|` row renders as literal body text and never becomes a heading. This
    silently breaks the TOC entry, the bookmark, and the section numbering —
    and check_numbering cannot see it, because the heading no longer exists as
    far as Markdown is concerned.
    """
    for i in range(1, len(lines)):
        if lines[i].startswith('#') and lines[i - 1].startswith('|'):
            rep.err('第%d行 标题紧贴表格末行，会被当成正文：%s'
                    % (i + 1, lines[i].strip()[:40]))


def check_duplicates(rep, lines):
    seen = {}
    for i, l in enumerate(lines):
        if re.match(r'^## 第.+章 ', l) or re.match(r'^表 \d+-\d+\u3000', l):
            key = l.strip()
            if key in seen:
                rep.err('重复标题「%s」在第%d行与第%d行' % (key[:40], seen[key] + 1, i + 1))
            else:
                seen[key] = i


def check_book(path):
    text = io.open(path, encoding='utf-8').read()
    lines = text.split('\n')
    rep = Report(Path(path).name)
    check_numbering(rep, lines)
    check_tables(rep, lines)
    secs, tabs, heads = collect_anchors(lines)
    check_references(rep, lines, secs, tabs, heads)
    check_toc(rep, lines, heads)
    check_headings(rep, lines)
    check_placeholders(rep, lines)
    check_table_heading_gap(rep, lines)
    check_duplicates(rep, lines)
    return rep, chapters_of(lines)


def check_mapping(all_chaps):
    """Verify child books still line up with the master book."""
    errors = []
    for child, (master, ranges) in MAPPING.items():
        if child not in all_chaps or master not in all_chaps:
            continue
        c = {n: t for n, t, _ in all_chaps[child]}
        m = {n: t for n, t, _ in all_chaps[master]}
        for lo, hi, off in ranges:
            for n in range(lo, hi + 1):
                if n not in c:
                    continue
                target = n + off
                if target not in m:
                    errors.append('%s 第%d章 在 %s 找不到第%d章'
                                  % (child, n, master, target))
                elif c[n] != m[target]:
                    if (n, c[n], m[target]) not in TITLE_DIFF_OK:
                        errors.append('%s 第%d章「%s」≠ %s 第%d章「%s」'
                                      % (child, n, c[n], master, target, m[target]))
    return errors


def main(argv):
    targets = argv[1:] or [str(ROOT / b) for b in BOOKS]
    all_chaps = {}
    reports = []
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            print('跳过（不存在）:', p.name)
            continue
        rep, chaps = check_book(p)
        all_chaps[p.name] = chaps
        reports.append(rep)

    width = max((len(r.name) for r in reports), default=10)
    total_err = 0
    for rep in reports:
        mark = 'PASS' if rep.ok else 'FAIL'
        print('%s  %s' % (mark, rep.name))
        for n in rep.notes:
            print('%s    · %s' % (' ' * width, n))
        for e in rep.errors:
            print('%s    ! %s' % (' ' * width, e))
        total_err += len(rep.errors)

    map_err = check_mapping(all_chaps)
    print('%s  四书章节映射' % ('PASS' if not map_err else 'FAIL'))
    for e in map_err:
        print('           ! %s' % e)
    total_err += len(map_err)

    print()
    print('合计问题：%d' % total_err)
    return 1 if total_err else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
