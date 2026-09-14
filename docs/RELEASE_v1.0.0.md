# v1.0.0 — Manuscript submission snapshot

This release freezes the approved final result tables, 20 standalone publication
panels in PNG/PDF/SVG, aggregate statistical sources, model code, and packaged
classifier checkpoint. No numerical result or figure was recalculated for this
release. The two CSV filenames retain the repository's existing compatibility
names; their manuscript table mapping is documented in README.

AUC confidence intervals and paired AUC comparisons use DeLong. Individual binary
metric confidence intervals use 1,000 percentile-bootstrap resamples. NPV
comparisons use 10,000 paired-bootstrap resamples; sensitivity, specificity and
accuracy comparisons use exact McNemar tests. Pooled external resampling is
institution-stratified. The exact P values remain in aggregate source files.

The attached figures/tables archive contains only the approved manifest-listed
assets and their checksum manifest. GitHub's source archives contain the complete
public repository at this tag. Patient-level workbooks and clinical input data
are not included. No Excel workbook exists in this tagged tree or its reachable
public history; this does not assert that a workbook was never uploaded before
the earlier history remediation.

Validation covers artifact hashes, displayed values, page synchronization,
synthetic statistical tests, and release packaging. Clinical inference, model
training and clinical bootstrap analyses were not rerun. A full clinical replay
requires the authorized study inputs and matching environment. See the
reproducibility and availability documents in the tagged source archive.

This is a published submission snapshot, not a DOI archive or an authorization
to share restricted data. It does not certify deletion of prior downloads,
third-party clones/backups, or internal GitHub caches. Code Ocean is not used.
