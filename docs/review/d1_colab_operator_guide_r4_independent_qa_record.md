# D1 Colab operator guide R4 independent QA record

Status: `QA_FAIL_D1_COLAB_OPERATOR_GUIDE_R4`

Reviewer: `Codex independent QA session (did not author the guide or R4 remediation)`

Reviewed at: `2026-10-19T05:51:58+07:00`

Boundary: `DOCUMENT_AND_LOCAL_CONTROL_QA_ONLY_NO_COLAB_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

Reviewed checkpoint: `3a72bf64893221cca25987bf49a84df0fef4484f` plus the current uncommitted R4 guide/routing worktree

## Verdict

- **FAIL — 0 Critical, 0 High, 1 Medium, 0 Low.**
- R4 closes the R3 threshold-order finding in the guide itself: the pre-seed lock is now explicitly
  a training-configuration lock, all three approved seeds precede validation evaluation, and one
  final confidence/NMS lock is created from exactly three validation reports before sealed-test
  access.
- All earlier mounted-byte, batch-consistency and append-only D-05 findings also remain closed.
- One new executable-sequence gap remains. The guide tells the Owner to evaluate the three final
  weights on validation, but omits the mandatory `m1.cli register-runs` step and independent
  review/clean commit of the run registry. The current `evaluate --split val` implementation
  refuses every unregistered run before reading validation data.
- Mechanical gates and the exact bound-bundle verifier pass, but they do not make the documented
  final-seed validation sequence executable.
- Per the delegated boundary, this review changes only this append-only QA record. It does not edit
  the guide, notebook, runner, verifier, source, tests, prior records, project memory or roadmap,
  and it does not mark R4 PASS.

## Historical finding closure

### QA-D1-OP-GUIDE-001 — High — CLOSED

Guide lines 86–122 still require exact size and SHA-256 verification of the archive and sidecar
mounted from Drive immediately after mount and before embedded-manifest access or repository
checkout. It says to stop on mismatch, retain the preflight for every **Run all**, and never replace
the expected values with newly observed values. The preserved local archive and sidecar match the
documented bytes and upload record exactly.

### QA-D1-OP-GUIDE-002 — Medium — CLOSED

Guide lines 270–282 and 303–310 still treat batch 4 after batch-8 OOM as a new smoke candidate that
must pass review and remain fixed for the pilot and all final seeds if accepted. Recovery uses a
new run label/state directory and preserves failed evidence. No silent batch restoration or resume
path remains.

### QA-D1-OP-GUIDE-003 / R2 residual Low — CLOSED

Guide lines 315–325 still forbid editing or overwriting D-05 and require any gate adjustment to be
a new append-only successor decision record with explicit Owner approval before the sealed test.
The final sequence repeats that wait.

### QA-D1-OP-GUIDE-R3-001 — Medium — CLOSED in R4

Guide lines 358–394 now establish the correct threshold order:

1. smoke review and one-seed pilot validation review;
2. optional append-only gate successor plus explicit Owner approval;
3. lock only the final training configuration, not confidence/NMS;
4. train the exact seeds `20261018`, `20261019`, `20261020` with that configuration;
5. verify every result package and evaluate all three distinct weights on validation;
6. invoke `m1.cli lock-thresholds` once with exactly the three governed validation reports;
7. independently review and commit the unchanged threshold lock before any `export-test` or
   `evaluate --split test --final-eval` action.

The guide explicitly rejects a pilot-only threshold lock and a second lock after the test has been
seen. This matches `cmd_lock_thresholds`: `--reports` has exact arity three, the seed set must equal
the D-05 seeds, all weight hashes must be distinct, and the resulting record binds all three report
hashes, run contracts and run attestations. The contradictory R3 double-lock sequence is gone.

## New finding

### QA-D1-OP-GUIDE-R4-001 — Medium — final-seed validation evaluation omits the mandatory committed run registry

Guide lines 367–379 move directly from training and standalone result-package verification to
evaluating all three weights on validation and then creating the threshold lock. The guide contains
no `register-runs` instruction and never tells the operator to independently review, git-track and
commit the unchanged run registry before those validation evaluations.

That omission makes the literal sequence fail closed. In `m1.cli`:

- validation `evaluate` enters `_evaluation_preflight`, which calls `contract.bind_run_weights`;
- `bind_run_weights` requires `docs/review/generated/m1_run_registry.json` to be git-tracked,
  committed and clean, and requires the selected run attestation to be present in that registry;
- `register-runs` inspects the supplied weights and writes the registry, but explicitly returns
  `ready_for_evaluation=false` with the next step to independently review and commit the registry
  unchanged;
- `lock-thresholds` again calls `bind_run_weights` for every validation report, so omitting the
  registry cannot be bypassed at the later lock step.

The controls prevent an unsafe acceptance, but an Owner following the guide cannot produce even
the first governed final-seed validation report. This is a material operator workflow blocker, so
it is Medium rather than a documentation-only Low.

Required remediation in a successor guide revision:

1. After all three result packages pass the standalone verifier and the canonical run artifacts
   are available locally, run `m1.cli register-runs --weights` with the three final `best.pt`
   paths.
2. Independently verify that the registry contains exactly the intended three distinct D-05 runs,
   their seeds, both checkpoint hashes, run-contract hashes and governed source bindings.
3. Add the registry to git and commit it unchanged; confirm the registry file itself is tracked and
   clean before evaluation.
4. Only then run `m1.cli evaluate --split val` once for each registered weight and retain the three
   `eval_val.json` reports.
5. Feed exactly those three reports to the single `lock-thresholds` command already documented,
   then retain the existing threshold-lock QA/clean-commit barrier before sealed-test access.

The R1–R4 FAIL records must remain immutable; request independent QA again on a successor guide.

## Other contract readback

- The R4 guide preserves the train/validation-only boundary, exact mounted-byte preflight, bound
  notebook commit, one-epoch smoke, unique run labels, exact runner steps, SQLite schema and
  fail-closed recovery semantics.
- The notebook remains seven cells total with six unexecuted code cells and no outputs. The
  required inserted hash preflight is ordered before the original manifest/checkout cell.
- The guide's standalone verifier command, exact eight-file result roster, terminal
  `SUCCEEDED`/`sealed_test_accessed=false` checks and instruction not to select `best.pt` before
  verifier PASS remain consistent with the runner and verifier.
- The cascade remains validation-only because its gate addendum is not Owner-approved. The
  classifier still has two candidates but no selected architecture or QA-approved Colab notebook;
  the legacy 43-class GTSRB model remains ineligible as a 54-class substitute.
- No real result package, run registry, three-seed validation reports, threshold lock or final
  model exists. This review does not promote the documented future sequence to completed evidence.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R4 operator guide | `43a661613a3f11000041cba5065ed5495248e709e4a4b7c9b8eb7f03a8ca7fb1` |
| R4 remediation report | `54a00208a243ba2bbdea4da76d06b259b18fcf167cd67249cce184885fc912e8` |
| Immutable R1 QA record | `70b4e0384a3faaf44e66ba1c86266d035ba622a0e358589734d66423ea84da86` |
| Immutable R2 QA record | `63bdbf3300a9d84e915bd1d5196b0b83729e06186a87ae6dc867dcd644df60d0` |
| Immutable R3 QA record | `9e1efd670cd9305e28efaa910e9929892c3d95b39b5fc2e73535405dfddcc25d` |
| R2 remediation report | `0906a8b00b6a33d2065327f5a569e34bc69e5aab273b9c799db28612c9c07214` |
| R3 remediation report | `98ee3c8977b11f1606c4e6ff802fbd2652104789cd40e79f3fc215e25447aa00` |
| Notebook | `4f7e5df089efaa01be8045c232dd02cb1a4a44e97a399530778c6e639b4babca` |
| Runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| Standalone verifier | `678de7f84e54c568dd3d7001873541a6226eeb2da0e5b2f725fdcde49fb994ab` |
| M1 CLI | `86c92e642cd733a7cdd9151f85acf09267cd3b35f4ccad81ff64a207d19f2672` |
| M1 contract | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |

## Proportional validation

| Gate | Result |
| --- | --- |
| `tests/test_m1_colab.py` | PASS, **22/22** |
| Complete detector pytest | PASS, **79/79** |
| Root Ruff (`src tests scripts main.py`) | PASS |
| Detector Ruff (`m1 tests colab`) | PASS |
| Root lock | PASS, 168 packages resolved |
| Detector lock | PASS, 66 packages resolved |
| Bound archive verifier at detached commit `1842a1b…` | PASS: `VERIFIED`, 5,888 files, train/val only, expected stem hashes, `test_included=false` |
| Preserved local archive/sidecar byte readback | PASS: exact sizes and SHA-256 values |
| `git diff --check` | PASS |
| Graft freshness and task-specific flow queries | PASS: graph synchronized at 2,516 nodes and 6,372 edges |
| Exact sealed-test access log | ABSENT |

The full historical root pytest suite was not run because this is a document-only successor review;
the task-specific root tests, complete detector suite, bound-bundle verifier, Ruff, locks and exact
implementation readback cover the affected workflow. No Colab cell ran, no Google Drive object was
changed or downloaded, no model was trained, no sealed-test artifact was opened, and no commit,
push, upload, deployment or publication occurred.
