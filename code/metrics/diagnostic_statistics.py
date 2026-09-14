"""Statistics for explicitly requested local reanalysis, not frozen figure exports.

AUC intervals use DeLong; binary intervals use 1,000 percentile resamples.
Input order, generator and seed are part of a bootstrap calculation. Reanalysis
must not be presented as byte-for-byte reproduction of frozen manuscript tables.
"""
from pathlib import Path
from statistics import NormalDist

import numpy as np

BINARY_BOOTSTRAP_RESAMPLES = 1000
PAIRED_BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 42
BINARY_METRICS = ("sensitivity", "specificity", "accuracy", "balanced_acc", "ppv", "npv")


def binary_array(values, name):
    values = np.asarray(values)
    if values.ndim != 1 or not len(values) or not np.isin(values, [0, 1]).all():
        raise ValueError(f"{name} must be a nonempty one-dimensional binary array")
    return values.astype(int)


def delong_auc_covariance(y_true, scores):
    """Paired DeLong structural components, including half credit for ties."""
    y = binary_array(y_true, "y_true")
    scores = np.atleast_2d(np.asarray(scores, dtype=float))
    if scores.ndim != 2 or scores.shape[1] != len(y) or not np.isfinite(scores).all():
        raise ValueError("Scores must be finite and paired with all outcomes")
    positive, negative = scores[:, y == 1], scores[:, y == 0]
    m, n = positive.shape[1], negative.shape[1]
    if min(m, n) < 2:
        raise ValueError("DeLong variance requires at least two positive and two negative observations")
    v_pos, v_neg = [], []
    for pos, neg in zip(positive, negative):
        sn, sp = np.sort(neg), np.sort(pos)
        v_pos.append((np.searchsorted(sn, pos, side="left") + np.searchsorted(sn, pos, side="right")) / (2 * n))
        v_neg.append(1 - (np.searchsorted(sp, neg, side="left") + np.searchsorted(sp, neg, side="right")) / (2 * m))
    v_pos, v_neg = np.asarray(v_pos), np.asarray(v_neg)
    covariance = np.atleast_2d(np.cov(v_pos, ddof=1)) / m + np.atleast_2d(np.cov(v_neg, ddof=1)) / n
    return v_pos.mean(axis=1), covariance


def delong_auc_ci(y_true, score):
    if np.asarray(score).ndim != 1:
        raise ValueError("A single-model AUC interval requires one score per observation")
    aucs, covariance = delong_auc_covariance(y_true, score)
    auc = float(aucs[0])
    half = NormalDist().inv_cdf(0.975) * np.sqrt(max(float(covariance[0, 0]), 0.0))
    return auc, [max(0.0, auc - half), min(1.0, auc + half)]


def binary_point_metrics(y_true, y_pred):
    y, p = binary_array(y_true, "y_true"), binary_array(y_pred, "y_pred")
    if len(y) != len(p):
        raise ValueError("Predictions and outcomes must have the same length")
    tn = int(np.sum((y == 0) & (p == 0)))
    fp = int(np.sum((y == 0) & (p == 1)))
    fn = int(np.sum((y == 1) & (p == 0)))
    tp = int(np.sum((y == 1) & (p == 1)))
    divide = lambda a, b: a / b if b else float("nan")
    sensitivity, specificity = divide(tp, tp + fn), divide(tn, tn + fp)
    return {"n": len(y), "tn": tn, "fp": fp, "fn": fn, "tp": tp,
            "sensitivity": sensitivity, "specificity": specificity,
            "accuracy": (tp + tn) / len(y), "balanced_acc": (sensitivity + specificity) / 2,
            "ppv": divide(tp, tp + fp), "npv": divide(tn, tn + fn)}


def bootstrap_groups(n, centers=None):
    indices = np.arange(n)
    if centers is None:
        return [indices]
    # Preserve missing values rather than coercing np.nan to the string "nan".
    centers = np.asarray(centers, dtype=object)
    if centers.ndim != 1 or len(centers) != n or any(x is None or x != x or str(x).strip() == "" for x in centers):
        raise ValueError("One nonmissing institution label is required per observation")
    return [indices[centers == center] for center in np.unique(centers)]


def compute_diagnostic_metrics(y_true, y_pred, y_score, centers=None,
                               n_bootstrap=BINARY_BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    y, p = binary_array(y_true, "y_true"), binary_array(y_pred, "y_pred")
    result = binary_point_metrics(y, p)
    auc, auc_ci = delong_auc_ci(y, y_score)
    groups = bootstrap_groups(len(y), centers)
    if not isinstance(n_bootstrap, int) or n_bootstrap < 1:
        raise ValueError("n_bootstrap must be a positive integer")
    rng = np.random.default_rng(seed)
    estimates = {key: [] for key in BINARY_METRICS}
    for _ in range(n_bootstrap):
        idx = np.concatenate([rng.choice(group, size=len(group), replace=True) for group in groups])
        sample = binary_point_metrics(y[idx], p[idx])
        for key in BINARY_METRICS:
            if np.isfinite(sample[key]):
                estimates[key].append(sample[key])
    result["auc"] = auc
    result["ci"] = {"auc": auc_ci}
    result["ci"].update({key: np.percentile(values, [2.5, 97.5]).tolist() if values else [float("nan"), float("nan")]
                         for key, values in estimates.items()})
    result["analysis_metadata"] = {
        "auc_ci": "DeLong (two-sided 95%)",
        "binary_ci": "Percentile bootstrap (2.5th and 97.5th percentiles)",
        "binary_requested_resamples": n_bootstrap,
        "binary_valid_resamples": {key: len(values) for key, values in estimates.items()},
        "seed": seed,
        "rng": "numpy.random.default_rng (PCG64)",
        "sampling": "institution-stratified participant resampling" if centers is not None else "participant resampling",
        "input_order": "Caller-supplied order preserved",
        "scope": "Local reanalysis; not an exact reconstruction of frozen manuscript bootstrap intervals",
    }
    return result


def require_analysis_output(path, package_root):
    """Never let local reanalysis overwrite the frozen public submission tree."""
    path, root = Path(path).resolve(), Path(package_root).resolve()
    if path == root or root in path.parents:
        allowed = (root / "outputs", root / "staging")
        if not any(path == parent or parent in path.parents for parent in allowed):
            raise ValueError("Repository outputs are restricted to outputs/ or staging/; frozen/source paths are protected")
    return path
