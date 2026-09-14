#!/usr/bin/env python3
"""Render public pages from approved aggregate CSVs, never a patient workbook.

The default is a read-only drift check. --write changes only the marked README
section and index.html; neither mode calculates statistics or changes figures.
"""
from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = '<!-- BEGIN APPROVED RESULTS -->'
END = '<!-- END APPROVED RESULTS -->'
TABLES = {
    'table1_ai_performance.csv': 'Extended Data Table 1: AI diagnostic performance',
    'table2_calcium_comparison.csv': 'Table 2: AI and calcium-score comparison',
}
FIGURE_ORDER = ([f'Fig2_{p}' for p in 'ABC'] + [f'Fig3_{p}' for p in 'ABCD']
                + [f'Fig4_{p}' for p in 'ABCD'] + [f'Fig5_{p}' for p in 'ABCDEFGHI'])
METHOD_NOTE = (
    'Point estimates are shown with 95% confidence intervals. AUC intervals use '
    'DeLong; individual binary-metric intervals use 1,000 percentile-bootstrap '
    'resamples. AUC comparisons use paired DeLong; sensitivity and specificity '
    'comparisons use two-sided exact McNemar tests; NPV differences use 10,000 '
    'paired-bootstrap resamples. Pooled external bootstrap resampling is '
    'stratified by institution. Significant comparisons are displayed as P < 0.05; '
    'exact P values remain in the aggregate statistics files. Non-significant '
    'P values are displayed to four decimal places, so 0.0912 corresponds to '
    '0.091 when rounded to the manuscript\'s three decimal places.'
)


def read_tables(root: Path) -> dict[str, list[list[str]]]:
    result = {}
    for name in TABLES:
        with (root / 'paper_plots' / name).open(newline='', encoding='utf-8-sig') as f:
            rows = list(csv.reader(f))
        if not rows or any(len(row) != len(rows[0]) for row in rows):
            raise ValueError(f'Empty or nonrectangular aggregate table: {name}')
        result[name] = rows
    return result


def markdown_table(rows: list[list[str]]) -> str:
    def row_line(row):
        return '| ' + ' | '.join(v.replace('|', r'\|').replace('\n', ' ') for v in row) + ' |'
    return '\n'.join([row_line(rows[0]), row_line(['---'] * len(rows[0]))]
                     + [row_line(row) for row in rows[1:]])


def generated_section(tables: dict[str, list[list[str]]]) -> str:
    sections = [START, '## Approved aggregate results', METHOD_NOTE]
    for name, title in TABLES.items():
        sections += [f'### {title}', f'[Download CSV](paper_plots/{name})', markdown_table(tables[name])]
    figure_rows = ['| Panel | Preview | Editable PDF | Editable SVG |', '| --- | --- | --- | --- |']
    for panel in FIGURE_ORDER:
        figure_rows.append(f'| {panel} | [PNG](paper_plots/{panel}.png) | '
                           f'[PDF](paper_plots/{panel}.pdf) | [SVG](paper_plots/{panel}.svg) |')
    sections += ['### Final standalone panels',
                 'Panel filenames retain the working figure numbering; they are not a new '
                 'numbering scheme for the assembled manuscript. PNG previews and editable '
                 'PDF/SVG versions contain the same approved figure content.',
                 '\n'.join(figure_rows),
                 '[Exact aggregate statistics](paper_plots/submission_sources/) · '
                 '[File checksums](paper_plots/submission_manifest.json)', END]
    return '\n\n'.join(sections)


def replace_section(readme: str, section: str) -> str:
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError('README must contain exactly one approved-results marker pair')
    a, b = readme.index(START), readme.index(END)
    if b < a:
        raise ValueError('README result markers are reversed')
    return readme[:a] + section + readme[b+len(END):]


def table_html(rows: list[list[str]]) -> str:
    head = ''.join(f'<th scope="col">{html.escape(v)}</th>' for v in rows[0])
    body = []
    for row in rows[1:]:
        cells = f'<th scope="row">{html.escape(row[0])}</th>'
        cells += ''.join(f'<td>{html.escape(v)}</td>' for v in row[1:])
        body.append(f'<tr>{cells}</tr>')
    return f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def render_index(tables: dict[str, list[list[str]]]) -> str:
    sections = []
    for name, title in TABLES.items():
        sections.append(f'<section class="table-card"><h2>{html.escape(title)}</h2>'
                        f'<p><a href="paper_plots/{name}">Download CSV</a></p>'
                        f'<div class="table-wrap">{table_html(tables[name])}</div></section>')
    cards = []
    for panel in FIGURE_ORDER:
        cards.append(f'<article><img loading="lazy" src="paper_plots/{panel}.png" alt="{panel}">'
                     f'<h2>{panel}</h2><p><a href="paper_plots/{panel}.pdf">PDF</a> · '
                     f'<a href="paper_plots/{panel}.svg">SVG</a></p></article>')
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OSOCAD: approved aggregate results</title>
<style>
body{margin:0;padding:28px;background:#f7f8fa;color:#222;font-family:Arial,Helvetica,sans-serif}
a{color:#0969da}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(360px,100%),1fr));gap:22px;margin-top:22px}
article,.table-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px;margin-bottom:18px}
img{width:100%;height:auto;display:block}h2{font-size:16px;margin:10px 0;word-break:break-word}p{line-height:1.5}
.table-wrap{overflow:auto;border:1px solid #e5e7eb;border-radius:6px;background:white}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #eceff3;border-right:1px solid #f1f3f5;padding:7px 9px;white-space:nowrap;text-align:center}
thead th{background:#f0f3f7}tbody th{text-align:left;background:#fbfcfd}
</style></head><body>
<h1>OSOCAD: approved aggregate results</h1>
<p>Public aggregate tables and approved standalone panels. This page is generated from the versioned CSV files, not from a patient-level workbook.</p>
<p><a href="README.md">Repository guide</a> · <a href="docs/REPRODUCIBILITY.md">Reproducibility scope</a> · <a href="PRIVACY.md">Privacy and data handling</a></p>
''' + f'<p>{html.escape(METHOD_NOTE)}</p>\n' + '\n'.join(sections) + '\n<section class="grid">' + '\n'.join(cards) + '</section>\n</body></html>\n'


def expected_pages(root: Path) -> dict[Path, str]:
    tables = read_tables(root)
    readme_path = root / 'README.md'
    return {readme_path: replace_section(readme_path.read_text(encoding='utf-8'), generated_section(tables)),
            root / 'index.html': render_index(tables)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true', help='Update only README result block and index.html')
    group.add_argument('--check', action='store_true', help='Check for display drift (default)')
    args = parser.parse_args(argv)
    expected = expected_pages(ROOT)
    drift = [p for p, text in expected.items() if not p.exists() or p.read_text(encoding='utf-8') != text]
    if args.write:
        for path in drift:
            path.write_text(expected[path], encoding='utf-8')
        print(f'Updated {len(drift)} public display files; aggregate CSVs and figures were not changed.')
        return 0
    if drift:
        print('Display drift: ' + ', '.join(p.name for p in drift))
        print('Review the aggregate inputs, then explicitly run this script with --write.')
        return 1
    print('PASS: README and index.html exactly match the approved aggregate CSVs.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
