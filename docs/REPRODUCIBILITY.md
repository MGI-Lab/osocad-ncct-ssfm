# Reproducibility scope

The repository separates approved publication outputs from local reanalysis.
This prevents a new bootstrap run or an older workbook from silently replacing
the submission tables.

## What the public bundle check verifies

Run these commands from the repository root with Python 3.10 or later:

```bash
python code/validation/verify_submission.py
python code/plotting/build_github_english_release.py --check
```

No clinical data or model packages are needed. The checks compare file hashes,
table dimensions, AUC estimates and intervals against the aggregate DeLong
source, all 24 manuscript comparison displays against their exact statistics,
and both generated pages against the same two CSVs. They also reject unreviewed
files in `paper_plots/` and check common private-data extensions and path patterns.
They are not a substitute for institutional privacy review.

The file manifest records the figures and tables approved for this version.
Do not regenerate its hashes merely to make a changed file pass. An intentional
result change needs a new numerical review and an explicit manifest update.

## Statistical contract

| Quantity | Method |
| --- | --- |
| AUC 95% CI | Two-sided analytic DeLong, clipped to [0, 1] |
| Individual sensitivity, specificity, accuracy, balanced accuracy, PPV, NPV 95% CI | Percentile bootstrap, 1,000 replications |
| AUC comparison on the same patients | Two-sided paired DeLong |
| Sensitivity comparison | Two-sided exact McNemar among positive cases |
| Specificity comparison | Two-sided exact McNemar among negative cases |
| Accuracy comparison, when requested locally | Two-sided exact McNemar on all cases |
| NPV difference | Paired bootstrap, 10,000 replications; absolute percentage-point difference and two-sided P value |

For pooled external validation, bootstrap sampling preserves each institution's
sample count. Other validation settings use patient-level resampling. Pairwise
bootstrap comparisons use the same resampled indices for both models.

The approved display uses `P < 0.05` for significant results and four decimal
places otherwise. The exact P values are retained in
`paper_plots/submission_sources/Table3_exact_statistics.csv`. A displayed
`P = 0.0912` is the same underlying prospective NPV comparison reported as
`P = 0.091` at three decimal places in the manuscript. Neither number denotes
the rejected 1,000-replication NPV-comparison candidate.

`Table3_exact_statistics.csv` contains all comparisons for the four reported
metrics, plus the real-world gated-versus-non-gated AUC comparison shown in the
figure. It does not publish historical Accuracy/PPV comparisons that are outside
this table's scope. No row is selected by statistical significance.

Some retained panel-level source files also contain Holm-adjusted exploratory
values. The approved figures and tables display the raw comparisons, not a
new adjustment applied during this synchronization. Use the exact-statistics
CSV and `all_cohort_auc_delong.csv` as the structured interfaces; panel-level
metadata retain their earlier layout-specific fields.

## Frozen outputs versus new local calculations

The public display generator reads only aggregate CSVs. It does not use a
patient workbook or fit a model. Final panels are approved PNG/PDF/SVG assets,
not outputs recomputed by that generator.

The local diagnostic-statistics helper uses seed 42 and NumPy's default random
generator for new binary bootstrap calculations. The same method and replication
count alone do not guarantee the same bootstrap endpoints: input order, sampling
implementation, missing-value handling, software version, and RNG state also
matter. New local calculations must stay in a separate output directory and
must not be described as exact reproduction of the frozen clinical results
until they have been checked against the study inputs.

Tests use small, explicitly synthetic fixtures to verify formulas and failure
paths. Synthetic fixtures are not study observations and are not substituted
for any publication value.

Run the numerical and bundle regression tests in a separate Python 3.10
environment:

```bash
python -m venv .venv-validation
. .venv-validation/bin/activate
python -m pip install -r requirements-validation.txt
python -m unittest discover -s tests -v
```

These pins cover the validation tests and aggregate Excel export only. They do
not claim to reconstruct the complete training or GPU inference environment.

## Checkpoint boundary

The packaged `models/best.pth` has the checksum recorded in `MODEL_INDEX.tsv`.
The recorded internal-validation AUC is 0.8786231884057971 and accuracy is
0.783625730994152; these round to the approved 0.879 and 78.4%.
Its metadata identify epoch 14. Structural inspection identifies 16 transformer
layers and positional embeddings for 32 slices plus the classification token.
Metadata agreement is not a replay of inference.

This synchronization did not retrain the model, rerun clinical inference, or
recalculate the frozen clinical bootstrap results. End-to-end reproduction
requires the authorized input cohort, its labels and ordering, the preprocessing
pipeline, all inference settings, and the matching environment. The public
repository does not supply the study patient data or a real-world inference
configuration. The separate pretrained backbone required by the training code
is also not bundled.

Do not change weights, thresholds, labels, preprocessing, or prediction files to
force agreement with a manuscript number. Investigate any mismatch, retain both
outputs, and document the cause before changing an approved result.

## Panel descriptions

These are working asset identifiers, not a renumbering of the assembled article.

| Asset | Content |
| --- | --- |
| Fig2_A/B/C | Internal AI ROC, predicted probabilities, exploratory t-SNE |
| Fig3_A/B/C/D | Pooled external ROC, predicted probabilities, exploratory t-SNE, center-specific performance |
| Fig4_A/B/C/D | Prospective ROC, three-setting performance, predicted probabilities, exploratory t-SNE |
| Fig5_A/B | External three-model ROC and sensitivity/NPV comparison |
| Fig5_C/D | Prospective three-model ROC and sensitivity/NPV comparison |
| Fig5_E/F | Real-world AI ROC and four-setting performance |
| Fig5_G/H/I | Real-world three-model ROC, sensitivity/NPV comparison, predicted probabilities |

The panels keep the approved sans-serif typography, physical size, plot types,
colors, and labels. All 20 panels have PNG previews and editable PDF/SVG versions.
No case-level source CSV, t-SNE coordinate table, or original study workbook is
included in this publication bundle.
