#!/usr/bin/env python3
"""Rebuild the table of contents inside a handbook Markdown file.

Renumbering chapters or moving them between parts invalidates every TOC entry,
because the anchors are GitHub-style slugs of the heading text. Editing the TOC
by hand is how broken links creep in, so regenerate it instead.

The TOC is three levels deep (part -> chapter -> indented section) and does not
list the front matter, matching the convention the books settled on.

Usage:
    python scripts/rebuild_toc.py                      # every book with a TOC
    python scripts/rebuild_toc.py 小学英语辅导手册.md    # selected books
    python scripts/rebuild_toc.py --dry-run            # report only, do not write

The student book (学生本) has no 部分/第X章 structure, so it is rebuilt with its
own rule: `## 一、...` sections at level 1 and `### ...` subsections at level 2.
"""

import io
import re
import sys
from pathlib import Path

# <repo>/.workbuddy/skills/english-learn-books/scripts/rebuild_toc.py
ROOT = Path(__file__).resolve().parents[4]

STRUCTURED = [
    '小学英语辅导手册.md',
    '小学英语-KET-PET辅导手册.md',
    '初中英语学习辅导手册.md',
    '自然拼读.md',
]
LITE = ['小学英语辅导手册-学生本.md']


def slug(text):
    """Must stay identical to build_books.add_heading_ids, or links break."""
    out = text.strip().lower()
    out = re.sub(r'[`*_~\[\]()]', '', out)
    out = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', out)
    out = out.replace(' ', '-')
    out = re.sub(r'-+', '-', out)
    return out.strip('-')


def collect_structured(lines):
    """[(kind, title)] where kind is part / chap / sec."""
    out = []
    in_toc = False
    for l in lines:
        if l.strip() == '## 目录':
            in_toc = True
            continue
        # The TOC block ends at the first body heading: a part title or, in
        # books that have no parts, a chapter title.
        if in_toc and (re.match(r'^# 第[一二三四五六七八九十]+部分 ', l)
                       or re.match(r'^## 第[一二三四五六七八九十]+章 ', l)):
            in_toc = False
        if in_toc:
            continue
        m = re.match(r'^# (第[一二三四五六七八九十]+部分 .+)$', l)
        if m:
            out.append(('part', m.group(1)))
            continue
        m = re.match(r'^## (第[一二三四五六七八九十]+章 .+)$', l)
        if m:
            out.append(('chap', m.group(1)))
            continue
        m = re.match(r'^### (\d+\.\d+ .+)$', l)
        if m:
            out.append(('sec', m.group(1)))
    return out


def collect_lite(lines):
    out = []
    in_toc = False
    for l in lines:
        if l.strip() == '## 目录':
            in_toc = True
            continue
        # The TOC block ends at the first real section heading (## ...).
        if in_toc and re.match(r'^## [^#]', l):
            in_toc = False
        if in_toc:
            continue
        m = re.match(r'^## ([^#].+)$', l)
        if m and m.group(1) != '目录':
            out.append(('chap', m.group(1)))
            continue
        m = re.match(r'^### (.+)$', l)
        if m:
            out.append(('sec', m.group(1)))
    return out


def render(items):
    out = ['## 目录', '']
    seen_part = False
    for kind, title in items:
        if kind == 'part':
            if seen_part:
                out.append('')      # blank line separating part groups
            seen_part = True
            out += ['### [%s](#%s)' % (title, slug(title)), '']
        elif kind == 'chap':
            out.append('- [%s](#%s)' % (title, slug(title)))
        else:
            out.append('  - [%s](#%s)' % (title, slug(title)))
    out.append('')
    return out


def rebuild(path, lite=False, dry=False):
    text = io.open(path, encoding='utf-8').read()
    lines = text.split('\n')
    items = collect_lite(lines) if lite else collect_structured(lines)
    if not items:
        print('  跳过（未找到标题结构）:', Path(path).name)
        return False
    toc = render(items)

    start = None
    for i, l in enumerate(lines):
        if l.strip() == '## 目录':
            start = i
            break
    if start is None:
        # No TOC yet: insert after the first horizontal rule.
        start = lines.index('---') + 1
        while start < len(lines) and lines[start].strip() == '':
            start += 1
        end = start
    else:
        end = start + 1
        while end < len(lines):
            if lines[end].startswith('# ') or lines[end].strip() == '---':
                break
            end += 1

    new_lines = lines[:start] + toc + lines[end:]
    n_part = sum(1 for k, _ in items if k == 'part')
    n_chap = sum(1 for k, _ in items if k == 'chap')
    n_sec = sum(1 for k, _ in items if k == 'sec')
    print('  %s：%d 部分 / %d 章 / %d 节%s'
          % (Path(path).name, n_part, n_chap, n_sec, '（试运行，未写入）' if dry else ''))
    if not dry:
        io.open(path, 'w', encoding='utf-8').write('\n'.join(new_lines))
    return True


def main(argv):
    dry = '--dry-run' in argv
    args = [a for a in argv[1:] if not a.startswith('--')]
    if args:
        targets = [(a, a in LITE) for a in args]
    else:
        targets = [(str(ROOT / b), False) for b in STRUCTURED]
        targets += [(str(ROOT / b), True) for b in LITE]

    print('重建目录%s' % ('（试运行）' if dry else ''))
    for path, lite in targets:
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            print('  跳过（不存在）:', p.name)
            continue
        rebuild(p, lite=lite, dry=dry)
    if not dry:
        print('完成。目录链接是否有效请跑 check_books.py 复核。')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
