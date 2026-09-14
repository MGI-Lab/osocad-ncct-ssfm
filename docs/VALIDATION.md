# Submission validation — 14 September 2026

This reviewed update starts from public commit
`30f0bf7ae22b682ac18f18d5fcf072eae7142702`. It aligns the final 16 panel assets
with the current manuscript numbering and accepted composite styling. The
`v1.0.1` submission release is a new snapshot; the `v1.0.0` tag and Release are
not moved or replaced. Publication status is recorded on the repository's
Release page. No DOI archive is claimed.
The update does not use Code Ocean.

## Checks completed

- The two display CSVs, their README/HTML renderings, and aggregate source
  statistics agree at the stated precision. Ten stale AUC interval cells have
  been synchronized; all 66 pre-existing performance point estimates remain
  unchanged. Real-world sections are now present in both tables.
- All 16 current panels have manuscript-matched PNG/PDF/SVG filenames. Their
  physical width is 88 mm;
  PNG resolution is 600 dpi. PDF/SVG labels remain editable, using the approved
  Liberation Sans typography at 5–7 pt. Fifteen redundant standalone titles
  were removed; every curve, point, bar, axis, legend and numerical label was
  preserved. A baseline rerender first matched all 16 prior PNGs pixel-for-pixel.
- The 58 approved data/figure artifacts match the submission manifest.
  Checksum corruption, a missing figure, and an unreviewed extra result file
  are each rejected by regression tests. A source archive without `.git` also
  passes the bundle check.
- Before release-packaging tests were added, all 32 unit tests passed in Python
  3.10.12 with the pinned validation packages.
  The same 32 tests also pass with NumPy 2.2.6, pandas 2.3.3, SciPy 1.15.3,
  scikit-learn 1.7.2, and openpyxl 3.1.5. The second environment is a numerical
  compatibility check, not a repeat of clinical experiments or figure rendering.
- Release preparation adds nine standard-library packaging tests. The complete
  41-test suite passed for `v1.0.0` in Python 3.10 with the pinned validation
  packages. The current README regrouping adds one presentation-mapping test,
  bringing the current suite to 42 tests. The frozen `v1.0.0` tag-triggered
  workflow ran the then-current 14 submission tests and nine packaging tests;
  it does not rerun the dependency-based statistical suite or clinical analyses.
  Packaging verifies the 58 approved assets plus their manifest, rejects an
  existing output file and workbook-containing reachable history, and produces
  byte-identical archives on two runs in the same tested environment.
- Statistical tests use explicitly synthetic fixtures, including an independent
  paired NPV bootstrap calculation with nonidentical predictions and
  institution-stratified resampling. Export tests use approved aggregate tables.
- The packaged checkpoint checksum is unchanged. Structural inspection does
  not execute its pickle payload or run model inference.
- Static checks of the reachable public history and candidate files did not
  identify direct patient identifier headers, private institutional paths, or
  credential-like strings. Before this update, the rebuilt public history had
  five reachable commits and no workbook in any reachable tree. Four known
  pre-remediation commit API URLs returned 404 at the earlier audit time.

## Limits and outstanding publication decisions

No training, clinical inference, or clinical bootstrap analysis was rerun.
Matching formulas, aggregate values, and checkpoint metadata is not proof of
end-to-end reproduction. The required restricted inputs and complete inference
environment remain separate from this public bundle.

Privacy checks do not establish deletion from GitHub's internal caches, other
people's clones, previous downloads, or backups. They are not a model memorization
audit or a substitute for institutional approval of the publication assets.

The submission release does not create a DOI, software license, or data access
agreement. Those separate decisions still require author and, where applicable,
institutional approval. See [the submission checklist](SUBMISSION_CHECKLIST.md).
