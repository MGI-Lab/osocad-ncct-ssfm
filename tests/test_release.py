"""Release-packager tests using approved public assets and synthetic Git fixtures."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "code/validation"


def load_packager():
    """Load the script without requiring code/ to be an installed package."""
    spec = importlib.util.spec_from_file_location(
        "release_packager_under_test", VALIDATION_DIR / "package_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(VALIDATION_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(VALIDATION_DIR))
    return module


packager = load_packager()


class SuccessfulReleaseTests(unittest.TestCase):
    """Exercise the real validator, history audit, assets, and ZIP writer."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="release-packager-success-")
        directory = Path(cls.temporary.name)
        cls.first = directory / "release-first.zip"
        cls.second = directory / "release-second.zip"
        cls.first_report = packager.package(cls.first, ROOT)
        cls.second_report = packager.package(cls.second, ROOT)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_real_release_contains_70_hashed_artifacts_and_manifest(self):
        manifest_name = "paper_plots/submission_manifest.json"
        expected_manifest = (ROOT / manifest_name).read_bytes()

        with zipfile.ZipFile(self.first) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()), 71)
            self.assertEqual(archive.read(manifest_name), expected_manifest)

            manifest = json.loads(archive.read(manifest_name))
            entries = packager.manifest_entries(manifest)
            self.assertEqual(len(entries), 70)
            expected_names = {entry["path"] for entry in entries} | {manifest_name}
            self.assertEqual(set(archive.namelist()), expected_names)
            for entry in entries:
                digest = hashlib.sha256(archive.read(entry["path"])).hexdigest()
                self.assertEqual(digest, entry["sha256"], entry["path"])

            workbook_suffixes = {".xls", ".xlsx", ".xlsm", ".xlsb", ".ods"}
            self.assertFalse(
                any(Path(name).suffix.lower() in workbook_suffixes for name in archive.namelist())
            )

        self.assertEqual(self.first_report["status"], "PASS")
        self.assertEqual(self.first_report["approved_artifacts"], 70)
        self.assertEqual(self.first_report["archive_members"], 71)

    def test_two_real_release_archives_are_byte_deterministic(self):
        self.assertEqual(self.first.read_bytes(), self.second.read_bytes())
        self.assertEqual(self.first_report["sha256"], self.second_report["sha256"])


class ReleasePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-packager-policy-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_rejects_output_inside_repository(self):
        output = ROOT / f".synthetic-release-{uuid.uuid4().hex}.zip"
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            packager.package(output, ROOT)
        self.assertFalse(output.exists())

    def test_rejects_non_zip_suffix(self):
        output = self.directory / "release.tar"
        with self.assertRaisesRegex(ValueError, "must use .zip"):
            packager.package(output, ROOT)
        self.assertFalse(output.exists())

    def test_rejects_existing_output_file(self):
        output = self.directory / "existing.zip"
        output.write_bytes(b"synthetic-existing-release")
        with mock.patch.object(packager, "check_bundle", return_value={"status": "PASS"}), \
             mock.patch.object(packager, "audit_history", return_value=1):
            with self.assertRaises((FileExistsError, ValueError)):
                packager.package(output, ROOT)
        self.assertEqual(output.read_bytes(), b"synthetic-existing-release")

    def test_rejects_bundle_that_fails_validation(self):
        output = self.directory / "invalid.zip"
        with mock.patch.object(
            packager, "check_bundle", return_value={"status": "FAIL", "failures": ["synthetic"]}
        ), mock.patch.object(packager, "audit_history") as audit:
            with self.assertRaisesRegex(ValueError, "failed validation"):
                packager.package(output, ROOT)
        audit.assert_not_called()
        self.assertFalse(output.exists())

    def test_rejects_checksum_corruption_during_packaging(self):
        manifest = json.loads((ROOT / "paper_plots/submission_manifest.json").read_bytes())
        target = packager.manifest_entries(manifest)[0]["path"]
        original_safe_path = packager.safe_path
        corrupt = self.directory / "synthetic-corrupt-asset"
        corrupt.write_bytes((ROOT / target).read_bytes() + b"synthetic-corruption")

        def substitute_corrupt_asset(root, relative):
            if relative == target:
                return corrupt
            return original_safe_path(root, relative)

        output = self.directory / "corrupt.zip"
        with mock.patch.object(packager, "check_bundle", return_value={"status": "PASS"}), \
             mock.patch.object(packager, "audit_history", return_value=1), \
             mock.patch.object(packager, "safe_path", side_effect=substitute_corrupt_asset):
            with self.assertRaisesRegex(ValueError, "Approved asset changed"):
                packager.package(output, ROOT)


class GitHistoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-history-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "--quiet")
        self.git("config", "user.email", "synthetic@example.invalid")
        self.git("config", "user.name", "Synthetic Test")

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )

    def commit_all(self, message):
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)

    def test_rejects_empty_git_history(self):
        with self.assertRaisesRegex(ValueError, "nonempty, auditable Git history"):
            packager.audit_history(self.root)

    def test_rejects_workbook_from_history_after_worktree_removal(self):
        (self.root / "README.md").write_text("synthetic public fixture\n", encoding="utf-8")
        self.commit_all("initial synthetic fixture")
        workbook = self.root / "synthetic_history_only.xlsx"
        workbook.write_bytes(b"synthetic workbook marker")
        self.commit_all("add synthetic workbook")
        workbook.unlink()
        self.commit_all("remove synthetic workbook")

        self.assertFalse(workbook.exists())
        with self.assertRaisesRegex(ValueError, "Workbook found"):
            packager.audit_history(self.root)


if __name__ == "__main__":
    unittest.main()
