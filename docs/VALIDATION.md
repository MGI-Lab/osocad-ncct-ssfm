# Submission validation — 14 September 2026

This reviewed update is based on public commit
`b00b22f3951eb9e56e374dd2925cd89e3f8c05cb`. Publication of the repository update,
including replacement of the old panels with the final 20 panels, was approved
on 14 September 2026. This is not a tagged release or a DOI archive.
The update does not use Code Ocean.

## Checks completed

- The two display CSVs, their README/HTML renderings, and aggregate source
  statistics agree at the stated precision. Ten stale AUC interval cells have
  been synchronized; all 66 pre-existing performance point estimates remain
  unchanged. Real-world sections are now present in both tables.
- All 20 approved panels have PNG/PDF/SVG files. Their physical width is 88 mm;
  PNG resolution is 600 dpi. PDF/SVG labels remain editable, using the approved
  Liberation Sans typography at 5–7 pt. The final Fig5_I label revision is
  preserved. No clinical plot was recalculated or redesigned in this update.
- The 70 approved data/figure artifacts match the submission manifest.
  Checksum corruption, a missing figure, and an unreviewed extra result file
  are each rejected by regression tests. A source archive without `.git` also
  passes the bundle check.
- All 32 unit tests pass in Python 3.10.12 with the pinned validation packages.
  The same 32 tests also pass with NumPy 2.2.6, pandas 2.3.3, SciPy 1.15.3,
  scikit-learn 1.7.2, and openpyxl 3.1.5. The second environment is a numerical
  compatibility check, not a repeat of clinical experiments or figure rendering.
- Statistical tests use explicitly synthetic fixtures, including an independent
  paired NPV bootstrap calculation with nonidentical predictions and
  institution-stratified resampling. Export tests use approved aggregate tables.
- The packaged checkpoint checksum is unchanged. Structural inspection does
  not execute its pickle payload or run model inference.
- Static checks of the reachable public history and candidate files did not
  identify direct patient identifier headers, private institutional paths, or
  credential-like strings. The pre-update public history had one reachable commit; the four
  known old commit API URLs returned 404 at the audit time.

## Limits and outstanding publication decisions

No training, clinical inference, or clinical bootstrap analysis was rerun.
Matching formulas, aggregate values, and checkpoint metadata is not proof of
end-to-end reproduction. The required restricted inputs and complete inference
environment remain separate from this public bundle.

Privacy checks do not establish deletion from GitHub's internal caches, other
people's clones, previous downloads, or backups. They are not a model memorization
audit or a substitute for institutional approval of the publication assets.

The update does not create a release, DOI, software license, or data access
agreement. Those separate decisions still require author and, where applicable,
institutional approval. See [the submission checklist](SUBMISSION_CHECKLIST.md).
