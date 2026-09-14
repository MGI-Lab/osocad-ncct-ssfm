# Submission version checklist

Code Ocean is not part of this submission route. Use the reviewed GitHub version
and, after author approval, a version-specific Zenodo archive.

## Before publishing the update

1. Review the diff against the current privacy-remediated public branch. Never
   merge the old pre-remediation repository history into it.
2. Run `python code/validation/verify_submission.py`, the page drift check, and
   the test suite. Review every intended publication file, not just README.
3. Confirm the privacy review's boundaries. A clean current tree does not prove
   that remote caches, old clones, downloaded workbooks, or backups were erased.
4. Confirm that the model and manuscript claims match the actual reproduction
   evidence. List any checks requiring restricted inputs instead of calling them
   complete.
5. Obtain approval for the repository diff, software/weight licensing, and the
   Data Availability wording. No code update can grant institutional data access.

## Freeze and archive

- Once approved, create a submission tag/release such as `v1.0.0-submission` on
  the reviewed commit. The name here is a proposal, not an existing release.
- Record the commit, asset manifest, method settings, and verification report.
  Do not move the submitted tag to a later commit; use a new version for revisions.
- Archive only the approved publication files in Zenodo. Inspect the archive's
  file list before publication. Do not upload a local worktree, `.git` directory,
  patient workbook, private audit log, or unreviewed model asset.
- Use the archived version's DOI in the manuscript and reference list once it
  exists. A repository URL is not a DOI, and no DOI is claimed by this update.

See [Zenodo's software archiving guide](https://help.zenodo.org/docs/github/archive-software/).
Creating a public release or archive is a separate publication action and is not
performed by the validation commands.

## Submission form

| Field | Entry |
| --- | --- |
| Did you develop code central to this work? | Yes |
| Would you like to use the Code Ocean service? | No |
| DOI or URL | The verified repository/version URL, or its DOI after archiving |
| Submit as a supplementary software file | Select only if a software file is actually attached |

Before final submission, use an unauthenticated browser to check that the stated
URL resolves to the intended version and that the linked files can be downloaded.
An accessible page alone does not establish that the clinical results can be
reproduced without the restricted study inputs.
