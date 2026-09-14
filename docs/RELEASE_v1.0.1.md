# v1.0.1 — Manuscript panel alignment

This release freezes the 16 standalone panels used by the current manuscript
assembly together with the approved aggregate result tables and statistics.

- Filenames now match `Figure2_A–F`, `Figure3_A–F`, and
  `ExtendedDataFigure2_A–D`.
- Fifteen redundant standalone titles were removed to match the accepted
  composite layouts. Curves, points, bars, axes, legends, numerical labels and
  confidence intervals were not changed.
- A deterministic baseline rerender matched all 16 previous PNG assets
  pixel-for-pixel before the title-only revision.
- Aggregate result values and statistical methods are unchanged from `v1.0.0`.
- The `v1.0.0` tag and Release remain immutable and preserve the earlier
  20-panel working-number package for audit.

The attached archive contains only the 58 manifest-approved figure/table/statistic
assets plus the manifest. It contains no patient workbook, case-level source table,
clinical identifier, Git metadata, or private audit file. This is a publication
asset snapshot, not an end-to-end replay of training or clinical inference.
