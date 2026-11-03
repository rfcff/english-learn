#!/usr/bin/env python3
"""Verify PDF layout rules against the HTML that build_books.py would produce.

Layout rules enforced here (see references/typesetting.md 三):

  * Repeating-group tables — whose header is one short pattern tiled k times,
    e.g. ``单词|音标|意思×2`` or ``现在|过去|现在|过去|现在|过去`` (k=3) — must give
    every group an equal 1/k share of the row, with inner columns sized from
    that group's own content.
  * Every ``<colgroup>`` must sum to 100% (otherwise the browser redistributes
    the shortfall proportionally and group halves drift out of balance).

It renders the HTML stage only (no Chrome, no PDF), so it is fast.

Usage:
    python scripts/check_layout.py              # all five books
    python scripts/check_layout.py 小学英语辅导手册-学生本.md
"""

import re
import sys

import booklib
import build_books as bb
from booklib import ROOT

BOOKS = [(md, title) for md, title, _html, _pdf in booklib.BOOKS]


def table_header(body):
    row = re.search(r'<tr\b.*?</tr>', body, flags=re.S)
    if not row:
        return []
    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row.group(0), flags=re.S)
    return [booklib.head_text(c) for c in cells]


def check_book(md_name, title):
    problems = []
    html = bb.build_html(ROOT / md_name, title)
    n_grouped = 0
    for m in re.finditer(r'<table\b[^>]*>\s*<colgroup>(.*?)</colgroup>(.*?)</table>',
                         html, flags=re.S):
        widths = [float(x) for x in re.findall(r'width:([\d.]+)%', m.group(1))]
        header = table_header(m.group(2))
        total = sum(widths)
        if not widths or abs(total - 100.0) > 0.6:
            problems.append('colgroup 求和 %.1f%%（应 100%%）表头=%s'
                            % (total, '|'.join(header[:3])))
            continue
        u = booklib.header_period(header)
        if u is not None:
            k = len(widths) // u
            n_grouped += 1
            share = 100.0 / k
            for g in range(k):
                got = sum(widths[g * u:(g + 1) * u])
                if abs(got - share) > 0.6:
                    problems.append('重复组表第%d/%d组占 %.1f%%（应 %.1f%%）表头=%s'
                                    % (g + 1, k, got, share, '|'.join(header)))
    return n_grouped, problems


def main(argv):
    targets = BOOKS if len(argv) <= 1 else [
        b for b in BOOKS if b[0] == argv[1]
    ]
    failed = False
    for md_name, title in targets:
        n_grouped, problems = check_book(md_name, title)
        if problems:
            failed = True
            print('FAIL  %s' % md_name)
            for p in problems:
                print('      ! %s' % p)
        else:
            print('PASS  %s（重复组表 %d 张各组均分）' % (md_name, n_grouped))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
