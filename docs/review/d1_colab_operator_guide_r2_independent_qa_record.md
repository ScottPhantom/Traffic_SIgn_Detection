# D1 Colab operator guide R2 independent QA record

Status: `QA_FAIL_D1_COLAB_OPERATOR_GUIDE_R2`

Reviewer: `Codex independent QA session (did not author the operator guide or R2 remediation)`

Reviewed at: `2026-10-19T05:45:34+07:00`

Boundary: `DOCUMENT_AND_LOCAL_CONTROL_QA_ONLY_NO_COLAB_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

Reviewed checkpoint: `3a72bf64893221cca25987bf49a84df0fef4484f` plus the current uncommitted R2 guide/routing worktree

## Verdict

- **FAIL — 0 Critical, 0 High, 0 Medium, 1 Low.**
- R2 closes the R1 High finding: the operator must hash the exact mounted Drive archive and
  sidecar at the exact expected paths, sizes and SHA-256 values before any cell reads the embedded
  manifest or chooses executable repository code.
- R2 closes the R1 Medium finding: batch 4 after an OOM is a new smoke candidate and cannot
  silently revert to batch 8 for the pilot or any of the three final seeds.
- R2 closes the authorization part of the R1 Low finding: the guide now requires explicit Owner
  approval before a changed gate can precede sealed-test access.
- One residual Low finding remains because the guide does not require the gate-successor record to
  be append-only, even though the R2 remediation report claims that it does. The guide therefore
  does not yet reproduce the complete delegated acceptance condition.
- Per the delegated boundary, this review changes only this append-only QA record. It does not edit
  the guide, R1 QA record, remediation report, notebook, runner, verifier, source, tests, project
  memory or roadmap, and it does not mark R2 PASS.

## R1 finding reproduction

### QA-D1-OP-GUIDE-001 — High — CLOSED in R2

The notebook's original order remains mount in cell 1, configuration in cell 2 and embedded
manifest/commit selection in cell 3. Guide lines 91–122 now require a new preflight cell immediately
after mount and require it to stay in the operating notebook so **Run all** checks both mounted
files before cell 3. The preflight binds:

- archive path `/content/drive/MyDrive/CPV391/M1_D1_Colab/m1_colab_train_val.tar.gz`, size
  `766226824`, SHA-256
  `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191`;
- sidecar path
  `/content/drive/MyDrive/CPV391/M1_D1_Colab/m1_colab_train_val.tar.gz.manifest.json`, size
  `1499866`, SHA-256
  `2c43d5fdff3de32af3fa3b9621f7f73cf1646c2f51801c5844ae89e8f4ae8d3b`.

The guide says to continue only after `PASS`, to stop on either size/hash mismatch and not to
replace the expected values with newly observed values. It also accurately limits the prior upload
evidence to local-source cryptographic verification plus external Drive UI readback. This closes
the original mounted-byte trust-chain finding in the documented cell order.

### QA-D1-OP-GUIDE-002 — Medium — CLOSED in R2

Guide lines 303–310 make the reviewed smoke batch the pilot batch and require every final seed to
use the same validation-locked configuration. Batch 8 remains the default only after a successful
batch-8 smoke. A batch-4 OOM recovery must itself pass smoke review and, if accepted, remains batch
4 for the pilot and all three final seeds. The failure table likewise calls batch 4 a new candidate
configuration. No silent batch-8 restoration remains.

### QA-D1-OP-GUIDE-003 — Low — authorization CLOSED; append-only property still OPEN

Guide lines 322–324 require every gate adjustment to become a successor decision with explicit
Owner approval before sealed-test access, and the sequence at lines 357–368 repeats the Owner
approval wait. This matches the authorization boundary in D-05.

However, neither location says that the successor decision/record must be **append-only**. The R2
remediation report states that the guide now requires an "append-only successor decision," but the
guide itself says only `successor decision` and `gate successor`. An operator could satisfy the
literal guide by editing/replacing the existing D-05 record instead of preserving it and adding a
new decision. That is an unsafe ambiguity at the exact governance boundary under review.

Required remediation: in the operator guide itself, require any gate change to be recorded in a
new append-only successor decision that preserves the existing D-05 Owner decision, and require
explicit Owner approval of that successor before any sealed-test access. The R2 FAIL record must
remain immutable; request independent QA again on a successor guide revision.

## Other contract readback

- The guide preserves the train/validation-only scope and forbids `export-test`, `--final-eval`,
  test-driven threshold selection, assert bypasses, horizontal flip, taxonomy changes, unapproved
  weight substitution and run-directory reuse.
- The Drive filenames, bound commit, L4 setup, one-epoch smoke defaults, three seed values,
  validation-first order and test-seal boundary agree with the notebook, upload record and D-05.
- The runner records text, SQLite and execution logs in the supplied Drive state directory, checks
  the train/val bundle and stem bindings, runs frozen detector sync, verifies the approved
  pretrained weight and packages only after a successful run.
- The standalone verifier requires the exact eight-file roster: both checkpoints, `results.csv`,
  `args.yaml`, `run_contract.json`, execution JSON, text log and SQLite log. It checks schema,
  names, sizes, hashes, terminal success, `sealed_test_accessed=false` and run attestation.
- Recovery advice requires a new run label/state directory and preservation of failed evidence;
  it does not instruct resume, deletion, hash bypass or sealed-test use.
- The notebook remains seven cells, all unexecuted with no outputs. No Colab runtime, model run or
  result package is claimed.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R2 operator guide | `9700aacf21c5aff7663b262fcb622445c101bca7b1c8704fff4b97a348533bdb` |
| Immutable R1 QA record | `70b4e0384a3faaf44e66ba1c86266d035ba622a0e358589734d66423ea84da86` |
| R2 remediation report | `0906a8b00b6a33d2065327f5a569e34bc69e5aab273b9c799db28612c9c07214` |
| Notebook | `4f7e5df089efaa01be8045c232dd02cb1a4a44e97a399530778c6e639b4babca` |
| Runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| Standalone verifier | `678de7f84e54c568dd3d7001873541a6226eeb2da0e5b2f725fdcde49fb994ab` |
| Private upload record | `3fda6ac5f9d775668e21decf22619faa6d5fdb94f6eabbf9bca436f17de568f7` |
| M1-Colab-R3 QA record | `4b3ddcfebcb7b055dc42c229cd890234bf6decd32e8fe2a965d372732a5503c0` |
| D-05 Owner decision | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` |

## Proportional validation

| Gate | Result |
| --- | --- |
| `tests/test_m1_colab.py` | PASS, **22/22** |
| Complete detector pytest | PASS, **79/79** |
| Package verifier matrix | PASS, **52/52** |
| Root Ruff (`src tests scripts main.py`) | PASS |
| Detector Ruff (`m1 tests colab`) | PASS |
| Root lock | PASS, 168 packages resolved |
| Detector lock | PASS, 66 packages resolved |
| Notebook JSON/readback | PASS; seven unexecuted cells, no outputs |
| `git diff --check` | PASS |
| Graft freshness | PASS; wiring graph synchronized at 2,516 nodes and 6,372 edges |
| Exact sealed-test access log | ABSENT |

The full historical root pytest suite was also started, reached 23% with no displayed failure and
was manually stopped after the task-specific 22-test gate, complete detector suite and all 52
package verifiers had passed. Its exit `130` is an interrupted run and is not reported as either a
full-suite PASS or a test failure.

No Colab cell ran, no Google Drive object was changed or downloaded, no model was trained, no
sealed-test artifact was opened, and no commit, push, upload, deployment or publication occurred.
