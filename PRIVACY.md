# Privacy and data handling

This public repository contains source code, a packaged model checkpoint,
aggregate result tables, and publication figures. It must not contain patient-
or examination-level records, DICOM files or metadata, institutional filesystem
paths, or workbooks with case-level predictions.

Keep all study data and generated case-level outputs outside the repository.
The included `.gitignore` excludes common private and generated locations, but
it is not a substitute for institutional privacy, ethics, and data-sharing
review.

Plotting utilities that consume a workbook use the local path supplied through
the `RESULTS_WORKBOOK` environment variable. Do not commit that workbook.
