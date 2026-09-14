#!/usr/bin/env python3
"""Package only approved figures/tables; no publishing, reanalysis or history edits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from verify_submission import ROOT, check_bundle, manifest_entries, safe_path

EXPECTED_APPROVED_ARTIFACTS = 58
EXPECTED_ARCHIVE_MEMBERS = 59


def audit_history(root):
    commits = subprocess.check_output(['git', '-C', str(root), 'rev-list', '--all'], text=True).splitlines()
    if not commits:
        raise ValueError('Release requires a nonempty, auditable Git history')
    for commit in commits:
        paths = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', '-z', commit], text=True).split('\0')
        if any(Path(path).suffix.lower() in {'.xls', '.xlsx', '.xlsm', '.xlsb', '.ods'} for path in paths):
            raise ValueError('Workbook found in the currently reachable Git history')
    return len(commits)


def package(output, root=ROOT):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Release archive must be outside the repository')
    if output.suffix.lower() != '.zip':
        raise ValueError('Release archive must use .zip')
    report = check_bundle(root)
    if report['status'] != 'PASS':
        raise ValueError('Submission bundle failed validation')
    commit_count = audit_history(root)
    manifest_path = root / 'paper_plots/submission_manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    entries = manifest_entries(manifest)
    if len(entries) != EXPECTED_APPROVED_ARTIFACTS:
        raise ValueError(f'Expected exactly {EXPECTED_APPROVED_ARTIFACTS} approved figure/table artifacts')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never replace a previously produced release asset.
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for entry in entries:
            payload = safe_path(root, entry['path']).read_bytes()
            if hashlib.sha256(payload).hexdigest() != entry['sha256']:
                raise ValueError('Approved asset changed during packaging')
            info = zipfile.ZipInfo(entry['path'], date_time=(2026, 9, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)
        info = zipfile.ZipInfo('paper_plots/submission_manifest.json', date_time=(2026, 9, 14, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        if manifest_path.read_bytes() != manifest_bytes:
            raise ValueError('Submission manifest changed during packaging')
        archive.writestr(info, manifest_bytes)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != EXPECTED_ARCHIVE_MEMBERS:
            raise ValueError('Release archive integrity check failed')
    return {'status': 'PASS', 'approved_artifacts': EXPECTED_APPROVED_ARTIFACTS,
            'archive_members': EXPECTED_ARCHIVE_MEMBERS,
            'current_reachable_history_commits': commit_count,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'bytes': output.stat().st_size, 'clinical_reproduction': 'not_run'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.output), indent=2))


if __name__ == '__main__':
    main()
