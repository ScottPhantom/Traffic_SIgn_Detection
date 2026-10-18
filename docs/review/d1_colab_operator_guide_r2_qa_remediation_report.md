# D1 Colab operator guide R2 QA remediation report

Status: `R2_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

R1 independent QA verdict: `FAIL — 0 Critical, 1 High, 1 Medium, 1 Low`

## Remediation

- High: the guide now requires hashing the exact archive and sidecar mounted from Drive before
  any cell reads the archive manifest or chooses a repository commit. The preflight binds exact
  paths, sizes and SHA-256 values, and must remain ordered immediately after Drive mount.
- Medium: an OOM recovery at batch 4 is now a new candidate configuration. It must pass smoke QA
  and, if approved, remain fixed for pilot and all final seeds. The guide no longer mandates a
  silent return to batch 8.
- Low: the pilot sequence now states that any adjusted gate needs an append-only successor
  decision and explicit Owner approval before sealed-test access.

R1 QA evidence remains immutable in
`docs/review/d1_colab_operator_guide_independent_qa_record.md`. R2 changes only the operator guide,
this remediation report and routing status; it does not modify the notebook, runner, bundle,
model, dataset, test seal or Owner authorization.
