"""Synthetic-only tests: no clinical inputs, checkpoint loading, or inference."""
import ast
import importlib.util
import inspect
from pathlib import Path
from statistics import NormalDist
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.stats import binomtest, norm
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "metrics"))
import diagnostic_statistics as stats


def functions_from(relative, names, **scope):
    """Exercise entrypoint function bodies without importing torch/training code."""
    scope.update(np=np, pd=pd, norm=norm, confusion_matrix=confusion_matrix,
                 delong_auc_covariance=stats.delong_auc_covariance,
                 compute_diagnostic_metrics=stats.compute_diagnostic_metrics)
    for node in ast.parse((ROOT / relative).read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module(body=[node], type_ignores=[]), relative, "exec"), scope)
    return scope


def matrix_oracle(y, score):
    positive, negative = score[y == 1], score[y == 0]
    credit = (positive[:, None] > negative) + 0.5 * (positive[:, None] == negative)
    return credit.mean(), credit.mean(axis=1), credit.mean(axis=0)


def count_metrics(y, p):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    div = lambda a, b: a / b if b else np.nan
    sens, spec = div(tp, tp + fn), div(tn, tn + fp)
    return dict(zip(stats.BINARY_METRICS, [sens, spec, (tp + tn) / len(y),
                                         (sens + spec) / 2, div(tp, tp + fp), div(tn, tn + fn)]))


class DiagnosticStatisticsTests(unittest.TestCase):
    def setUp(self):
        self.y = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        self.score = np.array([.1, .9, .4, .4, .8, .2, .3, .7, .6, .6, .2, .8])
        self.pred = (self.score >= .5).astype(int)

    def test_delong_ties_matches_independent_pairwise_oracle(self):
        other = self.score[::-1]
        aucs, covariance = stats.delong_auc_covariance(self.y, [self.score, other])
        oracle = [matrix_oracle(self.y, x) for x in [self.score, other]]
        expected = np.cov([x[1] for x in oracle], ddof=1) / 6 + np.cov([x[2] for x in oracle], ddof=1) / 6
        np.testing.assert_allclose(aucs, [x[0] for x in oracle], atol=1e-15)
        np.testing.assert_allclose(covariance, expected, atol=1e-15)
        auc, ci = stats.delong_auc_ci(self.y, self.score)
        half = NormalDist().inv_cdf(.975) * np.sqrt(expected[0, 0])
        np.testing.assert_allclose(ci, [max(0, auc - half), min(1, auc + half)])

    def test_delong_invariant_under_paired_row_permutation(self):
        order = np.random.default_rng(7).permutation(len(self.y))
        np.testing.assert_allclose(stats.delong_auc_ci(self.y, self.score)[1],
                                   stats.delong_auc_ci(self.y[order], self.score[order])[1])

    def test_degenerate_auc_and_invalid_inputs(self):
        self.assertEqual(stats.delong_auc_ci(self.y, self.y), (1.0, [1.0, 1.0]))
        self.assertEqual(stats.delong_auc_ci(self.y, np.ones(len(self.y))), (.5, [.5, .5]))
        for y, score in [([0, 0, 1], [.1, .2, .7]), ([0, 0], [.1, .2]),
                         ([0, 1, 0, 1], [.1, np.nan, .2, .8]), ([0, 1], [.1])]:
            with self.assertRaises(ValueError):
                stats.delong_auc_ci(y, score)

    def test_binary_bootstrap_matches_independent_count_oracle(self):
        centers = np.array(["A"] * 4 + ["B"] * 8)
        actual = stats.compute_diagnostic_metrics(self.y, self.pred, self.score, centers=centers, n_bootstrap=40)
        rng = np.random.default_rng(42)
        samples = []
        for _ in range(40):
            idx = np.concatenate([rng.choice(np.flatnonzero(centers == c), np.sum(centers == c), replace=True) for c in ["A", "B"]])
            self.assertEqual(np.sum(centers[idx] == "A"), 4)
            self.assertEqual(np.sum(centers[idx] == "B"), 8)
            samples.append(count_metrics(self.y[idx], self.pred[idx]))
        for metric in stats.BINARY_METRICS:
            values = [x[metric] for x in samples if np.isfinite(x[metric])]
            np.testing.assert_allclose(actual["ci"][metric], np.percentile(values, [2.5, 97.5]))

    def test_fixed_binary_defaults_and_missing_institution_rejected(self):
        self.assertEqual(inspect.signature(stats.compute_diagnostic_metrics).parameters["n_bootstrap"].default, 1000)
        self.assertEqual(inspect.signature(stats.compute_diagnostic_metrics).parameters["seed"].default, 42)
        for centers in [["A"], ["A", None], ["A", np.nan], ["", "B"]]:
            with self.assertRaises(ValueError):
                stats.bootstrap_groups(2, centers)

    def test_no_obsolete_ci_method_in_active_inference_exports(self):
        for relative in ["code/inference/infer_table2_diagnostic_performance.py", "code/metrics/export_checkpoint_table2_excel.py"]:
            source = (ROOT / relative).read_text()
            self.assertNotIn("Hanley", source)
            self.assertNotIn("Wilson", source)
            self.assertIn("DeLong", source)

    def test_inference_entrypoint_routes_to_shared_method(self):
        module = functions_from("code/inference/infer_table2_diagnostic_performance.py", ["compute_metrics"])
        result = module["compute_metrics"](self.y, self.pred, self.score, centers=np.repeat(["A", "B"], 6))
        expected = stats.compute_diagnostic_metrics(self.y, self.pred, self.score, centers=np.repeat(["A", "B"], 6))
        self.assertEqual(result, expected)

    def test_excel_entrypoint_routes_institution_labels_and_flattens_ci(self):
        module = functions_from("code/metrics/export_checkpoint_table2_excel.py", ["compute_metrics"])
        frame = pd.DataFrame({"y_true": self.y, "y_pred": self.pred, "prob_class1": self.score,
                              "bootstrap_institution": np.repeat(["A", "B"], 6)})
        result = module["compute_metrics"](frame)
        expected = stats.compute_diagnostic_metrics(self.y, self.pred, self.score, centers=frame.bootstrap_institution)
        for metric, ci in expected["ci"].items():
            self.assertEqual(result[f"ci_{metric}_low"], ci[0])
            self.assertEqual(result[f"ci_{metric}_high"], ci[1])

    def test_paired_delong_including_zero_variance_difference(self):
        test = functions_from("code/plotting/export_manuscript_tables.py", ["delong_test"])["delong_test"]
        self.assertEqual(test(self.y, self.score, self.score), 1.0)
        self.assertEqual(test(self.y, self.y, 1 - self.y), 0.0)
        aucs, cov = stats.delong_auc_covariance(self.y, [self.score, self.score[::-1]])
        expected = 2 * norm.sf(abs(aucs[0] - aucs[1]) / np.sqrt(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]))
        self.assertAlmostEqual(test(self.y, self.score, self.score[::-1]), expected)

    def test_paired_npv_bootstrap_defaults_and_identical_predictions(self):
        module = functions_from("code/plotting/export_manuscript_tables.py", ["npv", "generate_bootstrap_indices", "bootstrap_metric_diff_ci_p"])
        compare = module["bootstrap_metric_diff_ci_p"]
        self.assertEqual(inspect.signature(compare).parameters["n_bootstrap"].default, 10000)
        diff, low, high, p = compare(self.y, self.pred, self.pred, module["npv"], centers=np.repeat(["A", "B"], 6), n_bootstrap=30)
        self.assertEqual((diff, low, high, p), (0.0, 0.0, 0.0, 1.0))

    def test_nonidentical_paired_npv_matches_stratified_synthetic_oracle(self):
        module = functions_from("code/plotting/export_manuscript_tables.py", ["npv", "generate_bootstrap_indices", "bootstrap_metric_diff_ci_p"])
        comparator = np.array([0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0])
        centers = np.array(["A"] * 4 + ["B"] * 8)
        count, seed = 160, 42
        actual = module["bootstrap_metric_diff_ci_p"](
            self.y, self.pred, comparator, module["npv"], centers=centers,
            n_bootstrap=count, seed=seed,
        )
        # Independent implementation: direct negative-subset outcome proportions,
        # not the production confusion-matrix metric or its index generator.
        def oracle_npv(outcomes, prediction):
            negatives = outcomes[prediction == 0]
            return np.mean(negatives == 0) if len(negatives) else np.nan

        point = oracle_npv(self.y, self.pred) - oracle_npv(self.y, comparator)
        rng = np.random.default_rng(seed)
        differences = []
        for _ in range(count):
            indices = np.concatenate([
                rng.choice(np.arange(4), size=4, replace=True),
                rng.choice(np.arange(4, 12), size=8, replace=True),
            ])
            self.assertEqual(np.sum(centers[indices] == "A"), 4)
            self.assertEqual(np.sum(centers[indices] == "B"), 8)
            difference = (oracle_npv(self.y[indices], self.pred[indices])
                          - oracle_npv(self.y[indices], comparator[indices]))
            if np.isfinite(difference):
                differences.append(difference)
        differences = np.asarray(differences)
        low, high = np.quantile(differences, [.025, .975])
        p = (np.count_nonzero(np.abs(differences - point) >= abs(point)) + 1) / (len(differences) + 1)
        self.assertNotEqual(point, 0.0)
        np.testing.assert_allclose(actual, [point, low, high, p], atol=1e-14, rtol=0)

    def test_exact_mcnemar_positive_mask(self):
        compare = functions_from("code/plotting/export_manuscript_tables.py", ["mcnemar_exact_pvalue"])["mcnemar_exact_pvalue"]
        a, b = self.pred, np.zeros(len(self.y), dtype=int)
        discordant = np.sum(a[self.y == 1] != b[self.y == 1])
        self.assertEqual(compare(self.y, a, b, self.y == 1), binomtest(0, discordant, .5).pvalue)

    def test_public_output_tree_guard_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "paper_plots").mkdir()
            (root / "alias").symlink_to(root / "paper_plots", target_is_directory=True)
            for path in [root, root / "paper_plots", root / "paper_plots/a.csv", root / "alias/a.csv", root / "models/a.xlsx", root / "docs/a.xlsx", root / "README.md"]:
                with self.assertRaises(ValueError):
                    stats.require_analysis_output(path, root)
            self.assertEqual(stats.require_analysis_output(root / "outputs/a.csv", root), root / "outputs/a.csv")
            self.assertEqual(stats.require_analysis_output(root / "staging/a.csv", root), root / "staging/a.csv")

    def test_reanalysis_records_valid_resamples_and_not_frozen_claim(self):
        result = stats.compute_diagnostic_metrics(self.y, self.pred, self.score, n_bootstrap=40)
        meta = result["analysis_metadata"]
        self.assertEqual(meta["binary_requested_resamples"], 40)
        self.assertEqual(meta["seed"], 42)
        self.assertEqual(meta["rng"], "numpy.random.default_rng (PCG64)")
        self.assertEqual(set(meta["binary_valid_resamples"]), set(stats.BINARY_METRICS))
        self.assertTrue(all(0 < n <= 40 for n in meta["binary_valid_resamples"].values()))
        self.assertIn("not an exact reconstruction", meta["scope"])

    def test_invalid_binary_predictions_and_bootstrap_count(self):
        for prediction in [self.pred[:-1], np.full(len(self.y), 2), np.full(len(self.y), np.nan)]:
            with self.assertRaises(ValueError):
                stats.compute_diagnostic_metrics(self.y, prediction, self.score)
        with self.assertRaises(ValueError):
            stats.compute_diagnostic_metrics(self.y, self.pred, self.score, n_bootstrap=0)

    def test_figure_p_labels_accept_final_uppercase_and_keep_numeric_ns(self):
        import re
        parse = functions_from("code/plotting/redraw_calcium_sens_npv_from_excel.py", ["parse_p_display"], re=re)["parse_p_display"]
        for value in ["p < 0.001", "p = 1.7e-37 (p < 0.001)"]:
            self.assertEqual(parse(value), "P < 0.001")
        self.assertEqual(parse("p = 0.0911909 (ns)"), "P = 0.091")
        self.assertEqual(parse("p = 0.00390625"), "P = 0.004")
        self.assertEqual(parse("P = 0.073"), "P = 0.073")
        with self.assertRaises(ValueError):
            parse("P < 0.05")

    def test_staging_redraw_does_not_refresh_input_or_public_html(self):
        tree = ast.parse((ROOT / "code/plotting/redraw_calcium_sens_npv_from_excel.py").read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        calls = {n.func.id for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("refresh_figures_sheet", calls)
        self.assertNotIn("rebuild_html", calls)
        self.assertIn("require_analysis_output", calls)

    def test_frozen_table_export_copies_csv_without_reanalysis(self):
        path = ROOT / "code/plotting/export_manuscript_tables.py"
        spec = importlib.util.spec_from_file_location("submission_table_export", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "frozen.xlsx"
            with patch.object(sys, "argv", [str(path), "--output-xlsx", str(output)]), patch.object(module, "bootstrap_metric_diff_ci_p", side_effect=AssertionError("reanalysis not allowed")):
                module.main()
            for filename, sheet in [("table1_ai_performance.csv", "Table 1 AI performance"), ("table2_calcium_comparison.csv", "Table 2 Calcium comparison")]:
                expected = pd.read_csv(ROOT / "paper_plots" / filename, dtype=str, keep_default_na=False)
                actual = pd.read_excel(output, sheet_name=sheet, dtype=str, keep_default_na=False)
                pd.testing.assert_frame_equal(expected, actual)


if __name__ == "__main__":
    unittest.main()
