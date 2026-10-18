# D1 Colab operator guide R5 independent QA record

Status: `QA_PASS_D1_COLAB_OPERATOR_GUIDE_R5_ALL_R1_R4_FINDINGS_CLOSED`

Reviewer: `Codex independent QA session (did not author the guide or R5 remediation)`

Reviewed at: `2026-10-19T05:54:53+07:00`

Boundary: `DOCUMENT_AND_LOCAL_CONTROL_QA_ONLY_NO_COLAB_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

Reviewed checkpoint: `3a72bf64893221cca25987bf49a84df0fef4484f` plus the current uncommitted R5 guide/routing worktree

## Verdict

- **PASS — 0 Critical, 0 High, 0 Medium, 0 Low.**
- R5 closes the R4 executable-sequence finding for both pilot and final validation evaluation.
  Every governed weight is placed as a complete verified run under the canonical repository-level
  `results/experiments/`, registered, independently reviewed and committed unchanged in a clean
  run registry before `evaluate --split val` can run.
- The final sequence registers exactly the three D-05 `best.pt` files in one command, runs exactly
  three governed validation evaluations producing `eval_val.json`, then creates one confidence/NMS
  threshold lock from those reports. Independent QA and a clean unchanged commit of the lock remain
  mandatory before sealed-test access.
- All R1–R4 findings are closed in the guide itself. No new operator, path, authorization, logging,
  retry, verifier, cascade or classifier finding was found.
- This PASS approves only the reviewed R5 operator documentation against the current local controls.
  It does not prove that a Colab cell, smoke, pilot, three-seed training, validation evaluation,
  run registry, threshold lock or sealed-test evaluation has occurred.

## Historical finding closure

### R1 mounted-byte trust chain — CLOSED

Guide lines 86–122 require the exact archive and sidecar mounted from Drive to be hashed at their
exact paths, byte sizes and SHA-256 values immediately after mount and before any embedded manifest
is read or repository revision is selected. It says to stop on mismatch, retain the preflight for
every **Run all**, and never replace expected values with newly observed values. The guide correctly
limits the prior upload evidence to local-source cryptographic verification plus Drive UI readback.

### R1 batch/OOM consistency — CLOSED

Guide lines 270–282 and 303–310 treat batch 4 after batch-8 OOM as a new smoke candidate. It must
pass review and, if accepted, remains fixed for pilot and all final seeds. Failed state is preserved,
a new run label is required and no resume or silent batch-8 restoration is instructed.

### R1/R2 D-05 successor authorization — CLOSED

Guide lines 315–336 forbid editing or overwriting D-05. Any gate adjustment requires a new
append-only successor decision record and explicit Owner approval before sealed-test access. The
final sequence preserves this wait.

### R3 premature threshold lock — CLOSED

Guide lines 369–390 distinguish the pre-seed training-configuration lock from the final
confidence/NMS lock. The exact three D-05 seeds are trained first; all three packages are verified,
registered and evaluated on validation; only then may one final threshold lock be created. A
pilot-only lock and a second lock after test access are explicitly forbidden.

### R4 missing run-registry gate — CLOSED

The guide now covers the registry gate in both places where validation evaluation occurs:

- Pilot, lines 315–336: verify the result package; extract the complete `D1_*` run to
  `<repo>/results/experiments/`; run `register-runs` on pilot `best.pt`; obtain independent review;
  git-track and commit the registry unchanged; confirm it is clean; only then evaluate validation
  and read the generated `eval_val.json`.
- Final seeds, lines 392–447: place all three complete verified runs under the same canonical root;
  invoke one `register-runs` call with exactly three `best.pt` paths; independently review and
  commit the successor registry unchanged; confirm path-clean status; then invoke three validation
  evaluations and feed their three `eval_val.json` files to one `lock-thresholds` command.

The commands run from `detector/` and correctly address the repository-level results directory as
`../results/experiments/...`. This matches `contract.RESULTS_DIR = REPO_ROOT / "results/experiments"`.
It also preserves the already committed pilot registry: final `register-runs` first requires the
existing registry to be tracked and clean, retains its entries and adds the final attestations.

## Implementation and command reconciliation

- `register-runs --weights` accepts the documented pilot path and the documented list of three
  final paths. `inspect_run_weights` requires complete canonical runs, independently re-hashes
  `best.pt` and `last.pt`, checks the run contract, D-05 seed, model/data/environment bindings and
  rejects runs outside `<repo>/results/experiments/`.
- `register-runs` writes `<repo>/docs/review/generated/d1_run_registry.json` and deliberately emits
  `ready_for_evaluation=false` plus the independent-review/commit instruction reproduced by the
  guide.
- Validation `evaluate` calls `bind_run_weights` before reading validation data. The registry must
  be git-tracked, committed and clean, and the selected run attestation must be present. Each
  successful call writes `<run>/eval_val.json`, matching the guide.
- `lock-thresholds --reports` has exact arity three. It rejects non-validation reports, wrong seeds,
  duplicate weights and broken report/weight/run bindings, and writes the documented repository
  threshold-lock path.
- The threshold lock must then be independently reviewed, git-tracked, committed and clean.
  `bind_threshold_lock` rechecks that state, exact D-05 seed set, three distinct weights and three
  report hashes before any test evaluation can use it.
- Test evaluation additionally requires `--final-eval`, a nonblank reason, `--conf`,
  `--threshold-lock` and `--bootstrap`; confidence and NMS must equal the committed per-seed lock.
  None of those sealed-test actions are authorized or performed by this guide QA.

## Other contract readback

- The notebook remains seven cells total, with six unexecuted code cells and no outputs. The guide
  orders the inserted mounted-byte preflight before the original manifest/checkout cell.
- Drive names, bundle sizes/hashes, bound commit, L4 setup, smoke defaults, seeds, runner steps,
  SQLite schema, lifecycle evidence and the exact eight-file result roster match the current
  notebook, runner, verifier, upload record and D-05 decision.
- The standalone verifier command and expected `D1_COLAB_RESULT_PACKAGE`, `SUCCEEDED` and
  `sealed_test_accessed=false` fields are correct. No real result archive exists yet.
- Failure handling preserves run evidence and requires a new state directory. It does not instruct
  resume, deletion, hash bypass or sealed-test use.
- The cascade remains validation-only because its gate addendum is not Owner-approved. The
  classifier has two implementation candidates but no selected architecture or QA-approved Colab
  notebook; the legacy 43-class GTSRB model is not an eligible 54-class substitute.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R5 operator guide | `cd82ba1f37a61926cbdd85e116c7882fadd91c84f13d1603979689e63eb90cc1` |
| R5 remediation report | `5d07cbabaa8aace554a426e09df8d7a0b81a36a8e17e2cc8a497e8b1691cfb0a` |
| Immutable R1 QA record | `70b4e0384a3faaf44e66ba1c86266d035ba622a0e358589734d66423ea84da86` |
| Immutable R2 QA record | `63bdbf3300a9d84e915bd1d5196b0b83729e06186a87ae6dc867dcd644df60d0` |
| Immutable R3 QA record | `9e1efd670cd9305e28efaa910e9929892c3d95b39b5fc2e73535405dfddcc25d` |
| Immutable R4 QA record | `c421cff95dd3ff2cf698146c94d5760bbfc1eae6d5ab207cef644622dfa47600` |
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
| `register-runs`, `evaluate`, `lock-thresholds` CLI parse/help | PASS; `lock-thresholds` requires exactly three reports |
| Bound archive verifier at detached commit `1842a1b…` | PASS: `VERIFIED`, 5,888 files, train/val only, expected stem hashes, `test_included=false` |
| Preserved local archive/sidecar byte readback | PASS: exact sizes and SHA-256 values |
| Notebook JSON/readback | PASS: six unexecuted code cells, zero outputs |
| `git diff --check` | PASS |
| Graft freshness and task-specific command/path queries | PASS: graph synchronized at 2,516 nodes and 6,372 edges |
| Exact sealed-test access log | ABSENT |

The full historical root pytest suite was not rerun because this is a document-only successor
review; the task-specific root tests, complete detector suite, exact bound-bundle verifier, Ruff,
locks, CLI parsing and implementation readback cover the affected workflow. No Colab cell ran, no
Google Drive object was changed or downloaded, no model was trained, no sealed-test artifact was
opened, and no commit, push, upload, deployment or publication occurred.
