#!/usr/bin/env python3
"""Read-only checks for the approved public result bundle (standard library only).

These checks detect display drift and common accidental publication mistakes.
They are not clinical reproduction, image de-identification, or a full-history
privacy audit. They never update checksums to make a changed file pass.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METRICS = ['AUC', 'Sensitivity (%)', 'Specificity (%)', 'Accuracy (%)', 'Balanced Acc. (%)', 'PPV (%)', 'NPV (%)']
COHORTS = ['Training', 'Internal', 'External center 1', 'External center 2',
           'External', 'Prospective', 'Real world']
AUC_COHORT_NAMES = {'External Combined': 'External', 'Prospective Cohort 410': 'Prospective',
                    'Real-world Cohort': 'Real world'}
MODEL_NAMES = ['AI Model', 'Non-gated Agatston', 'Gated Agatston']
SOURCE_NAMES = {'Table3_exact_statistics.csv', 'panel_statistics.csv', 'all_cohort_auc_delong.csv',
                'all_cohort_auc_comparisons_delong.csv', 'ai_figure_metrics.csv',
                'calcium_figure_metrics.csv', 'real_world_three_method_metrics.csv',
                'real_world_binary_comparisons.csv'}


def builder_module(root):
    spec = importlib.util.spec_from_file_location('public_page_builder', root / 'code/plotting/build_github_english_release.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink():
        raise ValueError('Unsafe manifest path')
    if root.resolve() not in path.resolve().parents:
        raise ValueError('Manifest path escapes repository')
    return path


def load_dicts(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def estimate(row, percentage=False):
    factor, digits = (100, 1) if percentage else (1, 3)
    return f'{float(row["value"])*factor:.{digits}f} ({float(row["low"])*factor:.{digits}f} - {float(row["high"])*factor:.{digits}f})'


def manifest_entries(manifest):
    return (manifest['tables'] + manifest['aggregate_statistics']
            + [figure[extension] for figure in manifest['figures'] for extension in ['png', 'pdf', 'svg']])


def check_bundle(root: Path) -> dict:
    root = root.resolve()
    errors, checks = [], []
    def check(condition, name):
        checks.append({'name': name, 'pass': bool(condition)})
        if not condition:
            errors.append(name)
    manifest = json.loads((root / 'paper_plots/submission_manifest.json').read_text())
    builder = builder_module(root)
    entries = manifest_entries(manifest)
    expected_paths = [entry['path'] for entry in entries]
    check(len(entries) == len(set(expected_paths)), 'No duplicate manifest paths')
    check({Path(row['path']).name for row in manifest['aggregate_statistics']} == SOURCE_NAMES, 'Aggregate source allowlist')
    check([row['panel'] for row in manifest['figures']] == builder.FIGURE_ORDER, 'All 20 approved panels present in order')
    for entry in entries:
        path = safe_path(root, entry['path'])
        check(path.is_file(), f'Exists: {entry["path"]}')
        if path.is_file():
            check(hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], f'Checksum: {entry["path"]}')
    tables = builder.read_tables(root)
    ai = tables['table1_ai_performance.csv']
    comparison = tables['table2_calcium_comparison.csv']
    check(len(ai) == 8 and len(ai[0]) == 8 and [r[0] for r in ai[1:]] == METRICS, 'Seven AI metrics and seven cohort columns')
    check(len(comparison) == 16 and len(comparison[0]) == 6, 'Three cohort comparison sections')
    interval_pattern = re.compile(r'^(\d+(?:\.\d+)?) \((\d+(?:\.\d+)?) - (\d+(?:\.\d+)?)\)$')
    for row in ai[1:] + [r[:4] for r in comparison[1:] if r[0] in METRICS]:
        for cell in row[1:]:
            match = interval_pattern.fullmatch(cell)
            valid = bool(match)
            if match:
                value, low, high = map(float, match.groups())
                valid = all(map(math.isfinite, [value, low, high])) and 0 <= low <= value <= high <= (1 if row[0] == 'AUC' else 100)
            check(valid, f'Valid estimate/interval: {row[0]} / {cell}')

    auc_rows = load_dicts(root / 'paper_plots/submission_sources/all_cohort_auc_delong.csv')
    auc_map = {(r['cohort'], r['method']): r for r in auc_rows}
    check(len(auc_map) == 13, 'Thirteen unique cohort/model DeLong entries')
    for column, cohort in enumerate(COHORTS, start=1):
        source = auc_map[(cohort, 'AI Model')]
        check(source['ci_method'] == 'DeLong' and ai[1][column] == estimate(source), f'AI AUC linked to DeLong source: {cohort}')
    cohort_offsets = {'External Combined': 1, 'Prospective Cohort 410': 6, 'Real-world Cohort': 11}
    for cohort, offset in cohort_offsets.items():
        check([r[0] for r in comparison[offset+1:offset+5]] == ['AUC', 'Sensitivity (%)', 'Specificity (%)', 'NPV (%)'], f'Comparison row order: {cohort}')
        for column, model in enumerate(MODEL_NAMES, start=1):
            source = auc_map[(AUC_COHORT_NAMES[cohort], model)]
            check(comparison[offset+1][column] == estimate(source), f'Comparison AUC linked to DeLong source: {cohort}/{model}')

    exact = load_dicts(root / 'paper_plots/submission_sources/Table3_exact_statistics.csv')
    exact_map = {(r['Cohort'], r['Metric'], r['Comparison']): r for r in exact}
    for cohort, offset in cohort_offsets.items():
        for row_offset, metric in enumerate(['AUC', 'Sensitivity', 'Specificity', 'NPV'], start=1):
            for column, model in [(4, 'Non-gated Agatston'), (5, 'Gated Agatston')]:
                record = exact_map[(cohort, metric, f'AI Model vs {model}')]
                p = float(record['Raw P value'])
                display = 'P < 0.05' if p < 0.05 else f'P = {p:.4f}'
                check(0 <= p <= 1 and display == record['Display'], f'Exact/display P: {cohort}/{metric}/{model}')
                if metric == 'NPV':
                    difference, low, high = (100*float(record[k]) for k in ['Difference (first method - second method)', 'Difference 95% CI Low', 'Difference 95% CI High'])
                    display = f'Delta {difference:+.1f} pp ({low:+.1f} to {high:+.1f}); {display}'
                    check(record['CI method'] == 'paired bootstrap', f'NPV difference interval method: {cohort}/{model}')
                check(comparison[offset+row_offset][column] == display, f'Comparison display linked to exact statistics: {cohort}/{metric}/{model}')

    for path, expected in builder.expected_pages(root).items():
        check(path.is_file() and path.read_text(encoding='utf-8') == expected, f'Generated display in sync: {path.name}')
    published = set(expected_paths) | {'paper_plots/submission_manifest.json'}
    for path in (root / 'paper_plots').rglob('*'):
        if path.is_file():
            check(path.relative_to(root).as_posix() in published, f'No unreviewed result file: {path.relative_to(root)}')
    for name in SOURCE_NAMES | set(builder.TABLES):
        path = root / 'paper_plots' / ('submission_sources/' if name in SOURCE_NAMES else '') / name
        headers = list(load_dicts(path)[0])
        check(not any(re.search(r'patient.?id|accession|exam.?id|dicom|hospital.?number|patient.?name', h, re.I) for h in headers), f'No direct identifier header: {name}')
    with (root / 'models/MODEL_INDEX.tsv').open(newline='') as stream:
        for record in csv.DictReader(stream, delimiter='\t'):
            path = safe_path(root, record['package_path'])
            check(hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'Checkpoint matches recorded checksum')
    # A source archive has no Git metadata; check all its files instead.
    # Neither mode scans remote caches or establishes complete de-identification.
    if (root / '.git').exists():
        process = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True, check=True)
        candidates = set(process.stdout.decode().split('\0')) - {''}
    else:
        candidates = {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()}
    for relative in sorted(candidates):
        path = safe_path(root, relative)
        check(not re.search(r'\.(xlsx?|xlsm|xlsb|ods|dcm|dicom|nii(?:\.gz)?)$', relative, re.I), f'No private-format publication candidate: {relative}')
        if path.is_file() and path.suffix in {'.py', '.md', '.json', '.csv', '.tsv', '.html', '.svg', '.txt', '.yml'}:
            value = path.read_text(encoding='utf-8', errors='replace')
            check(not re.search(r'/(?:mnt[0-9]*/|home/ubuntu/)|[A-Za-z]:\\(?:Users|data)\\', value), f'No institutional absolute path: {relative}')
    return {'status': 'PASS' if not errors else 'FAIL', 'checks': len(checks),
            'failures': errors, 'approved_artifacts': len(entries), 'clinical_reproduction': 'not_run',
            'privacy_scope': 'candidate files and common identifier/path patterns only; not a full privacy audit'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        report = check_bundle(args.root)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        report = {'status': 'FAIL', 'failures': [str(exc)]}
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
