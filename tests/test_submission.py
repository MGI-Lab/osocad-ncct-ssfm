"""Synthetic file fixtures and negative checks; no study data are generated."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load('builder_under_test', 'code/plotting/build_github_english_release.py')
validator = load('validator_under_test', 'code/validation/verify_submission.py')


class DisplayTests(unittest.TestCase):
    def test_table_has_rectangular_sections(self):
        for rows in builder.read_tables(ROOT).values():
            self.assertTrue(all(len(row) == len(rows[0]) for row in rows))

    def test_readme_only_replaces_marked_section(self):
        original = f'Before\n{builder.START}\nold\n{builder.END}\nAfter\n'
        replacement = f'{builder.START}\nnew\n{builder.END}'
        self.assertEqual(builder.replace_section(original, replacement), f'Before\n{replacement}\nAfter\n')

    def test_markers_required(self):
        for text in ['no markers', builder.START*2 + builder.END, builder.END + builder.START]:
            with self.assertRaises(ValueError):
                builder.replace_section(text, 'replacement')

    def test_html_escapes_values(self):
        rendered = builder.table_html([['Metric', 'Value'], ['Synthetic', '<script> & P < 0.05']])
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_render_is_deterministic_and_includes_20_figures(self):
        tables = builder.read_tables(ROOT)
        first = builder.render_index(tables)
        self.assertEqual(first, builder.render_index(tables))
        self.assertEqual(first.count('<img '), 20)
        self.assertIn('Fig5_I.png', first)

    def test_readme_panels_follow_current_manuscript_assembly(self):
        section = builder.generated_section(builder.read_tables(ROOT))
        expected = (
            ('Figure 2', (('a', 'Fig2_A'), ('b', 'Fig3_A'), ('c', 'Fig3_D'),
                          ('d', 'Fig4_A'), ('e', 'Fig5_E'), ('f', 'Fig5_F'))),
            ('Figure 3', (('a', 'Fig5_A'), ('b', 'Fig5_B'), ('c', 'Fig5_C'),
                          ('d', 'Fig5_D'), ('e', 'Fig5_G'), ('f', 'Fig5_H'))),
            ('Extended Data Figure 2', (('a', 'Fig2_B'), ('b', 'Fig3_B'),
                                        ('c', 'Fig4_C'), ('d', 'Fig5_I'))),
        )
        self.assertEqual(builder.MANUSCRIPT_PANEL_GROUPS, expected)
        self.assertEqual(section.count('[PNG]('), 16)
        self.assertEqual(len({source for _, rows in expected for _, source in rows}), 16)
        for title, rows in expected:
            self.assertIn(f'#### {title}', section)
            for label, source in rows:
                self.assertIn(f'| {label} | [PNG](paper_plots/{source}.png)', section)
        for unused in ['Fig2_C', 'Fig3_C', 'Fig4_B', 'Fig4_D']:
            self.assertNotIn(f'paper_plots/{unused}.png', section)
        self.assertNotIn('Receiver operating characteristic', section)
        self.assertNotIn('Predicted probability distributions', section)

    def test_modified_value_changes_both_displays(self):
        tables = builder.read_tables(ROOT)
        before_html, before_md = builder.render_index(tables), builder.generated_section(tables)
        tables['table1_ai_performance.csv'][1][1] = '0.000 (0.000 - 0.000)'
        self.assertNotEqual(before_html, builder.render_index(tables))
        self.assertNotEqual(before_md, builder.generated_section(tables))

    def test_rejects_ragged_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'paper_plots').mkdir()
            for name in builder.TABLES:
                shutil.copyfile(ROOT/'paper_plots'/name, root/'paper_plots'/name)
            path = root/'paper_plots/table1_ai_performance.csv'
            path.write_text('Metric,Value\nSynthetic\n')
            with self.assertRaises(ValueError):
                builder.read_tables(root)

    def test_manifest_path_cannot_escape(self):
        for path in ['../private.csv', '/tmp/private.csv']:
            with self.assertRaises(ValueError):
                validator.safe_path(ROOT, path)

    def test_manifest_path_cannot_use_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'linked.csv').symlink_to(ROOT/'README.md')
            with self.assertRaises(ValueError):
                validator.safe_path(root, 'linked.csv')

    def test_final_bundle_passes(self):
        report = validator.check_bundle(ROOT)
        self.assertEqual(report['status'], 'PASS', report['failures'])


class FrozenBundleNegativeTests(unittest.TestCase):
    """Copy public assets only; never mutate the working publication bundle."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ['paper_plots', 'models']:
            shutil.copytree(ROOT / directory, self.root / directory)
        code = self.root / 'code/plotting'
        code.mkdir(parents=True)
        shutil.copyfile(ROOT / 'code/plotting/build_github_english_release.py', code / 'build_github_english_release.py')
        for filename in ['README.md', 'index.html']:
            shutil.copyfile(ROOT / filename, self.root / filename)

    def test_archive_without_git_passes(self):
        report = validator.check_bundle(self.root)
        self.assertEqual(report['status'], 'PASS', report['failures'])

    def test_changed_frozen_figure_fails_checksum(self):
        path = self.root / 'paper_plots/Fig5_I.png'
        path.write_bytes(path.read_bytes() + b'synthetic-corruption-test')
        report = validator.check_bundle(self.root)
        self.assertEqual(report['status'], 'FAIL')
        self.assertIn('Checksum: paper_plots/Fig5_I.png', report['failures'])

    def test_missing_figure_fails(self):
        (self.root / 'paper_plots/Fig5_I.png').unlink()
        report = validator.check_bundle(self.root)
        self.assertEqual(report['status'], 'FAIL')
        self.assertIn('Exists: paper_plots/Fig5_I.png', report['failures'])

    def test_unreviewed_result_file_fails(self):
        (self.root / 'paper_plots/unreviewed_synthetic.csv').write_text('Synthetic ID,Value\na,0\n')
        report = validator.check_bundle(self.root)
        self.assertEqual(report['status'], 'FAIL')
        self.assertIn('No unreviewed result file: paper_plots/unreviewed_synthetic.csv', report['failures'])


if __name__ == '__main__':
    unittest.main()
