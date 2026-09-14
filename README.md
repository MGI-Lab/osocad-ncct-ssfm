# Opportunistic screening of obstructive coronary artery disease from non-contrast chest CT by a self-supervised foundation model

This repository contains the model code, a packaged classifier checkpoint,
approved aggregate result tables, and standalone publication panels.
Patient-level study data are not included.

No Excel workbooks are present in the current public tree or in the Git history
reachable from its current public branches and tags (checked 14 September 2026).
This describes the rebuilt public history, not a claim that no workbook was ever
uploaded before the earlier history remediation. See [PRIVACY.md](PRIVACY.md).

## Submission results and reproducibility

The approved aggregate CSVs in `paper_plots/` are the publication display source.
The README result section and `index.html` are generated from those files.
The approved figures are preserved without recalculation or redesign.

| Repository file | Manuscript content |
| --- | --- |
| `paper_plots/table1_ai_performance.csv` | Extended Data Table 1: AI performance in seven cohorts/settings |
| `paper_plots/table2_calcium_comparison.csv` | Table 2: AI versus non-gated and gated Agatston scores |
| `paper_plots/submission_sources/` | Aggregate statistics, including exact P values |
| `paper_plots/submission_manifest.json` | Approved figure/table checksums |

The two CSV filenames are retained for compatibility. Their numbers are not
the manuscript table numbers. Standalone panel filenames also retain the
working figure numbering; see the panel descriptions in
[Reproducibility](docs/REPRODUCIBILITY.md).

Check the public result bundle without installing the model environment:

```bash
python code/validation/verify_submission.py
python code/plotting/build_github_english_release.py --check
```

After an approved change to the aggregate tables, explicitly refresh the
display pages and review the diff:

```bash
python code/plotting/build_github_english_release.py --write
```

That command does not read a workbook, recalculate metrics, alter a figure,
or modify a checkpoint. Statistical and clinical-data reproduction are separate
checks; passing a display check does not prove end-to-end model reproduction.
See [Reproducibility](docs/REPRODUCIBILITY.md) and the
[submission checklist](docs/SUBMISSION_CHECKLIST.md).
Completed checks and their limits are recorded in
[submission validation](docs/VALIDATION.md).

## Repository layout

- `code/training/`: dataset, model, and training launcher.
- `code/inference/`: checkpoint inference and cohort evaluation.
- `code/metrics/`: diagnostic-performance estimation and local table export.
- `code/plotting/`: public display generation and local figure utilities.
- `code/validation/`: checks for the approved publication bundle.
- `models/best.pth`: packaged classifier; its checksum and recorded internal-validation metrics are in `models/MODEL_INDEX.tsv`.
- `paper_plots/`: approved aggregate tables and PNG/PDF/SVG panels.

## Study data

Keep study data and all patient-level generated outputs outside the public
repository. The examples below describe relative input paths; they do not
provide study records or permission to distribute them.

```text
data/
├── internal/
│   ├── images/<patient_id>/*.{png,jpg,jpeg}
│   └── json/{train.json,validation.json}
├── external/
│   ├── images/<patient_id>/*.{png,jpg,jpeg}
│   └── json/{external_shuguang.json,external_huangshan.json}
└── prospective/
    ├── images/<patient_id>/*.{png,jpg,jpeg}
    └── json/forward_ct.json
```

The existing inference commands accept local study inputs. Do not commit those
inputs or their patient-level predictions. See [PRIVACY.md](PRIVACY.md) and
[data access requirements](docs/AVAILABILITY.md). Real-world aggregate results
are included in the tables; a public real-world patient dataset is not supplied.

## Model use

The packaged classifier and its relative-path configuration are
`models/best.pth` and `models/data_config.json`. Training from the pretrained
backbone also requires `models/pytorch_model.bin`, which is not included in
this repository. Its approved source and redistribution terms must be confirmed
before claiming that the public package reproduces training from scratch.

The existing training grid uses the following settings. A grid describes the
training launcher, not the provenance of every published cohort prediction.

| Setting | Value |
| --- | --- |
| Backbone | ViT-Tiny (`vit_tiny_patch16_224`) |
| Input | Heart-ROI PNG slices, WL/WW 40/400 |
| Image size | 224 × 224 |
| Target/max slices | 32 / 32 |
| Batch size | 16 |
| Loss | Focal loss, gamma = 2.0 |
| Optimizer | AdamW |
| Weight decay | 0.1 |
| Scheduler | Cosine annealing |
| Learning rates | `1e-5`, `2e-5` |
| Transformer layers searched | `4`, `6`, `8`, `16` |
| Dropout | 0.2 |
| Epoch limit | 1000 |
| Data workers | 4 |
| GPUs per run | 1 |

Only run training or inference with authorized local data and the appropriate
model environment. These operations are not part of the public bundle check.

```bash
python code/training/launch.py

python code/inference/eval_external.py \
  --model-path models/best.pth \
  --result-dir outputs/external_evaluation
```

The plotting/export utilities use staged local outputs. They must not overwrite
the frozen publication files or modify their input workbooks. Use each command's
`--help` for its required input and output paths.

To export the approved aggregate CSVs to a local Excel workbook without
recalculation:

```bash
python code/plotting/export_manuscript_tables.py \
  --output-xlsx outputs/frozen_tables/manuscript_tables.xlsx
```

## Access, versioning, and citation

Code is hosted at <https://github.com/MGI-Lab/osocad-ncct-ssfm>.
The submission version is `v1.0.0`; its publication status and downloadable assets
are shown on the [GitHub Release page](https://github.com/MGI-Lab/osocad-ncct-ssfm/releases/tag/v1.0.0).
The version retains the approved final numerical results and 20 standalone panels.
Code Ocean is not used. A version DOI, software licensing, and any controlled-data
access commitment remain separate decisions requiring the authors' approval.
This repository does not claim an unpublished DOI or grant institutional data
access. See [the submission checklist](docs/SUBMISSION_CHECKLIST.md).

<!-- BEGIN APPROVED RESULTS -->

## Approved aggregate results

Point estimates are shown with 95% confidence intervals. AUC intervals use DeLong; individual binary-metric intervals use 1,000 percentile-bootstrap resamples. AUC comparisons use paired DeLong; sensitivity and specificity comparisons use two-sided exact McNemar tests; NPV differences use 10,000 paired-bootstrap resamples. Pooled external bootstrap resampling is stratified by institution. Significant comparisons are displayed as P < 0.05; exact P values remain in the aggregate statistics files. Non-significant P values are displayed to four decimal places, so 0.0912 corresponds to 0.091 when rounded to the manuscript's three decimal places.

### Extended Data Table 1: AI diagnostic performance

[Download CSV](paper_plots/table1_ai_performance.csv)

| Metrics | Training Cohort (n=2056) | Internal Validation (n=513) | External Center 1 (n=470) | External Center 2 (n=277) | External Combined (n=747) | Prospective Cohort (n=410) | Real-world Cohort (n=2,388) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AUC | 0.887 (0.872 - 0.902) | 0.879 (0.849 - 0.908) | 0.845 (0.810 - 0.880) | 0.838 (0.786 - 0.891) | 0.848 (0.820 - 0.876) | 0.886 (0.845 - 0.927) | 0.848 (0.830 - 0.866) |
| Sensitivity (%) | 79.3 (76.0 - 82.3) | 77.4 (70.9 - 83.5) | 83.6 (79.1 - 88.2) | 76.7 (67.7 - 85.7) | 81.8 (77.6 - 85.6) | 84.3 (77.1 - 91.1) | 75.7 (72.6 - 79.1) |
| Specificity (%) | 80.6 (78.6 - 82.6) | 78.8 (74.2 - 83.2) | 71.7 (65.7 - 77.2) | 77.0 (71.2 - 82.6) | 74.1 (69.5 - 78.4) | 75.5 (70.5 - 80.3) | 79.8 (77.8 - 81.8) |
| Accuracy (%) | 80.2 (78.5 - 81.8) | 78.4 (74.9 - 81.9) | 77.9 (74.3 - 81.3) | 76.9 (71.8 - 81.2) | 77.5 (74.2 - 80.5) | 77.8 (73.7 - 82.0) | 78.6 (77.0 - 80.3) |
| Balanced Acc. (%) | 79.9 (78.1 - 81.7) | 78.1 (74.2 - 81.8) | 77.6 (73.9 - 81.1) | 76.9 (71.3 - 81.9) | 78.0 (74.8 - 80.7) | 79.9 (75.7 - 84.5) | 77.8 (75.9 - 79.7) |
| PPV (%) | 66.7 (63.4 - 69.9) | 64.0 (57.6 - 71.0) | 76.1 (71.0 - 81.2) | 60.0 (50.5 - 68.2) | 71.4 (66.8 - 75.9) | 55.2 (48.1 - 62.7) | 60.2 (57.0 - 63.5) |
| NPV (%) | 88.8 (87.0 - 90.5) | 87.7 (83.8 - 91.2) | 80.2 (74.6 - 85.4) | 88.0 (83.2 - 92.6) | 83.7 (80.3 - 87.2) | 93.1 (89.8 - 96.1) | 89.1 (87.5 - 90.7) |

### Table 2: AI and calcium-score comparison

[Download CSV](paper_plots/table2_calcium_comparison.csv)

| Metrics | Proposed AI Model (NCCT) | Non-gated Agatston Score (NCCT) | Gated Agatston Score (Dedicated CSCT) | Comparison with Non-gated Score | Comparison with Gated Score |
| --- | --- | --- | --- | --- | --- |
| External Validation Cohorts |  |  |  |  |  |
| AUC | 0.848 (0.820 - 0.876) | 0.824 (0.795 - 0.853) | 0.868 (0.842 - 0.894) | P < 0.05 | P < 0.05 |
| Sensitivity (%) | 81.8 (77.6 - 85.6) | 40.6 (35.4 - 45.9) | 57.9 (52.9 - 63.8) | P < 0.05 | P < 0.05 |
| Specificity (%) | 74.1 (69.5 - 78.4) | 97.1 (95.5 - 98.6) | 92.3 (89.7 - 94.8) | P < 0.05 | P < 0.05 |
| NPV (%) | 83.7 (80.3 - 87.2) | 67.4 (64.1 - 71.0) | 73.5 (70.2 - 77.3) | Delta +16.4 pp (+13.0 to +19.7); P < 0.05 | Delta +10.3 pp (+7.2 to +13.3); P < 0.05 |
| Prospective Cohort |  |  |  |  |  |
| AUC | 0.886 (0.845 - 0.927) | 0.857 (0.814 - 0.901) | 0.898 (0.860 - 0.936) | P = 0.0727 | P = 0.3214 |
| Sensitivity (%) | 84.3 (77.1 - 91.1) | 60.2 (51.0 - 69.9) | 75.9 (67.6 - 83.5) | P < 0.05 | P < 0.05 |
| Specificity (%) | 75.5 (70.5 - 80.3) | 94.4 (91.5 - 96.8) | 91.7 (88.8 - 94.9) | P < 0.05 | P < 0.05 |
| NPV (%) | 93.1 (89.8 - 96.1) | 86.9 (83.2 - 90.6) | 91.4 (88.3 - 94.4) | Delta +6.2 pp (+3.4 to +9.2); P < 0.05 | Delta +1.6 pp (-0.1 to +3.7); P = 0.0912 |
| Real-world Cohort (n=2,388) |  |  |  |  |  |
| AUC | 0.848 (0.830 - 0.866) | 0.813 (0.793 - 0.832) | 0.866 (0.850 - 0.883) | P < 0.05 | P < 0.05 |
| Sensitivity (%) | 75.7 (72.6 - 79.1) | 43.1 (39.5 - 46.8) | 69.1 (65.7 - 72.5) | P < 0.05 | P < 0.05 |
| Specificity (%) | 79.8 (77.8 - 81.8) | 95.2 (94.2 - 96.3) | 87.7 (85.9 - 89.2) | P < 0.05 | P < 0.05 |
| NPV (%) | 89.1 (87.5 - 90.7) | 80.6 (78.8 - 82.2) | 87.6 (85.8 - 89.0) | Delta +8.4 pp (+7.1 to +9.8); P < 0.05 | Delta +1.5 pp (+0.5 to +2.6); P < 0.05 |

### Final standalone panels

Panel labels below follow the current manuscript assembly. Linked filenames retain their earlier working identifiers; PNG previews and editable PDF/SVG versions contain the same approved figure content. The current assembly uses 16 of the 20 assets frozen in `v1.0.0`; the other four remain preserved in that release but are not part of the groupings below.

#### Figure 2

| Manuscript panel | Preview | Editable PDF | Editable SVG |
| --- | --- | --- | --- |
| a | [PNG](paper_plots/Fig2_A.png) | [PDF](paper_plots/Fig2_A.pdf) | [SVG](paper_plots/Fig2_A.svg) |
| b | [PNG](paper_plots/Fig3_A.png) | [PDF](paper_plots/Fig3_A.pdf) | [SVG](paper_plots/Fig3_A.svg) |
| c | [PNG](paper_plots/Fig3_D.png) | [PDF](paper_plots/Fig3_D.pdf) | [SVG](paper_plots/Fig3_D.svg) |
| d | [PNG](paper_plots/Fig4_A.png) | [PDF](paper_plots/Fig4_A.pdf) | [SVG](paper_plots/Fig4_A.svg) |
| e | [PNG](paper_plots/Fig5_E.png) | [PDF](paper_plots/Fig5_E.pdf) | [SVG](paper_plots/Fig5_E.svg) |
| f | [PNG](paper_plots/Fig5_F.png) | [PDF](paper_plots/Fig5_F.pdf) | [SVG](paper_plots/Fig5_F.svg) |

#### Figure 3

| Manuscript panel | Preview | Editable PDF | Editable SVG |
| --- | --- | --- | --- |
| a | [PNG](paper_plots/Fig5_A.png) | [PDF](paper_plots/Fig5_A.pdf) | [SVG](paper_plots/Fig5_A.svg) |
| b | [PNG](paper_plots/Fig5_B.png) | [PDF](paper_plots/Fig5_B.pdf) | [SVG](paper_plots/Fig5_B.svg) |
| c | [PNG](paper_plots/Fig5_C.png) | [PDF](paper_plots/Fig5_C.pdf) | [SVG](paper_plots/Fig5_C.svg) |
| d | [PNG](paper_plots/Fig5_D.png) | [PDF](paper_plots/Fig5_D.pdf) | [SVG](paper_plots/Fig5_D.svg) |
| e | [PNG](paper_plots/Fig5_G.png) | [PDF](paper_plots/Fig5_G.pdf) | [SVG](paper_plots/Fig5_G.svg) |
| f | [PNG](paper_plots/Fig5_H.png) | [PDF](paper_plots/Fig5_H.pdf) | [SVG](paper_plots/Fig5_H.svg) |

#### Extended Data Figure 2

| Manuscript panel | Preview | Editable PDF | Editable SVG |
| --- | --- | --- | --- |
| a | [PNG](paper_plots/Fig2_B.png) | [PDF](paper_plots/Fig2_B.pdf) | [SVG](paper_plots/Fig2_B.svg) |
| b | [PNG](paper_plots/Fig3_B.png) | [PDF](paper_plots/Fig3_B.pdf) | [SVG](paper_plots/Fig3_B.svg) |
| c | [PNG](paper_plots/Fig4_C.png) | [PDF](paper_plots/Fig4_C.pdf) | [SVG](paper_plots/Fig4_C.svg) |
| d | [PNG](paper_plots/Fig5_I.png) | [PDF](paper_plots/Fig5_I.pdf) | [SVG](paper_plots/Fig5_I.svg) |

[Exact aggregate statistics](paper_plots/submission_sources/) · [File checksums](paper_plots/submission_manifest.json)

<!-- END APPROVED RESULTS -->
