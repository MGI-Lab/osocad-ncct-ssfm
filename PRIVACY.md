# Privacy and data handling

This public repository contains source code, a packaged model checkpoint,
aggregate result tables, and publication figures. It must not contain patient-
or examination-level records, DICOM files or metadata, institutional filesystem
paths, or workbooks with case-level predictions.

Keep study data outside the public publication set, preferably outside the
checkout. Temporary local outputs in ignored `outputs/` or `staging/` directories
must never be committed or included in a release.
The included `.gitignore` excludes common private and generated locations, but
it is not a substitute for institutional privacy, ethics, and data-sharing
review.

The legacy workbook-preview utility requires an explicit `--workbook` path.
It does not modify the workbook. Do not commit private input workbooks.

## Publication boundary

Only reviewed aggregate statistics and approved publication figures belong in
`paper_plots/`. The allowed result files are listed in
`paper_plots/submission_manifest.json`. Do not copy an entire local results,
source-data, or handoff directory into this repository. Names such as
"deidentified" do not by themselves establish that a case-level file is safe
to publish. Figures must also be checked for labels or metadata that identify
participants.

Keep patient-level inputs and newly generated outputs out of published files.
Ignoring a file prevents some accidental additions; it does not erase a file
that was already committed. Run `python code/validation/verify_submission.py`
and inspect the staged file list before publishing any update.

## History and other copies

The current public history was rebuilt during an earlier privacy remediation.
The public branch/tag history audited on 14 September 2026 contains no Excel
workbooks. This is a statement about currently reachable commits, not about
every upload that may have occurred before the history was rebuilt.
That statement applies to this repository, not to every copy ever downloaded.
Old clones, forks, cached commit views, pull-request references, workflow
artifacts, and Git LFS storage require separate checks where applicable.
Do not merge or push an old pre-remediation history back into the public branch.
Collaborators should use a fresh clone of the cleaned public history for future
publication work and retain restricted research materials only in approved
institutional storage, outside that public checkout.

Known former workbook download endpoints checked on 14 September 2026 returned
HTTP 404. This is a time-bounded access check, not proof that all old copies or
server-side objects have been deleted.

If sensitive content is found, stop publication and report the finding to the
repository maintainers and the responsible institutional data/privacy team.
Agree on the exact removal scope before rewriting history. GitHub Support may
be needed for cached views or references that maintainers cannot remove.
Never include patient identifiers in a public issue or remediation report.

See [GitHub's sensitive-data removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
