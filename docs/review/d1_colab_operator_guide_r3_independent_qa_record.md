# D1 Colab operator guide R3 independent QA record

Status: `QA_FAIL_D1_COLAB_OPERATOR_GUIDE_R3`

Reviewer: `Codex independent QA session (did not author the guide or R3 remediation)`

Reviewed at: `2026-10-19T05:49:43+07:00`

Boundary: `DOCUMENT_AND_LOCAL_CONTROL_QA_ONLY_NO_COLAB_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

Reviewed checkpoint: `3a72bf64893221cca25987bf49a84df0fef4484f` plus the current uncommitted R3 guide/routing worktree

## Verdict

- **FAIL — 0 Critical, 0 High, 1 Medium, 0 Low.**
- R3 explicitly closes the only residual R2 finding: the guide forbids editing or overwriting the
  current D-05 record and requires a new append-only successor decision record plus explicit Owner
  approval before sealed-test access.
- The earlier mounted-byte and batch-consistency findings also remain closed in the guide itself.
- One new operator-sequence finding remains: the final-seed diagram says to lock a threshold before
  the three final seed runs exist, even though the governed CLI can create that lock only from the
  three seed-specific validation reports and distinct weights. The diagram then says to lock the
  threshold a second time after training.
- Mechanical gates and the exact bound bundle verifier are green, but they do not make the literal
  final-seed instructions executable or unambiguous.
- Per the delegated boundary, this review changes only this append-only QA record. It does not edit
  the guide, notebook, runner, verifier, source, tests, prior QA/remediation records, project memory
  or roadmap, and it does not mark R3 PASS.

## Historical finding closure

### QA-D1-OP-GUIDE-001 — High — CLOSED in the guide

Guide lines 86–122 require the Owner to hash the exact mounted Drive archive and sidecar, at their
exact paths, byte sizes and SHA-256 values, immediately after Drive mount and before the notebook
reads the embedded manifest or selects executable repository code. The guide says to continue only
after `PASS`, retain the preflight in the operating notebook for every **Run all**, stop on any
mismatch and never replace the expected values with newly observed values.

The preserved local source readback matches the guide and upload record:

- archive: `766226824` bytes,
  `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191`;
- sidecar: `1499866` bytes,
  `2c43d5fdff3de32af3fa3b9621f7f73cf1646c2f51801c5844ae89e8f4ae8d3b`.

The guide also correctly says the upload record is local-source cryptographic evidence plus Drive
UI readback, not a cryptographic readback of the remote object. This closes the original trust-chain
finding in the operator-facing text.

### QA-D1-OP-GUIDE-002 — Medium — CLOSED in the guide

Guide lines 270–282 and 303–310 treat batch 4 after a batch-8 OOM as a new smoke candidate. It must
pass smoke review, receive QA/Owner acceptance and then remain the batch for the pilot and all three
final seeds. Batch 8 remains the default only if the batch-8 smoke passes. The guide also requires a
new run label/state directory and preservation of failed evidence rather than resume or deletion.
No silent return from batch 4 to batch 8 remains.

### QA-D1-OP-GUIDE-003 / R2 residual Low — CLOSED in the guide

Guide lines 315–325 explicitly forbid editing or overwriting the current D-05 record. Any gate
adjustment must be a new **append-only successor decision record**, and the Owner must explicitly
approve that record before the sealed test opens. Lines 358–369 repeat the append-only successor and
Owner-approval wait in the end-to-end sequence. This matches D-05 Q4 and closes the residual R2
wording ambiguity in the guide itself.

## New finding

### QA-D1-OP-GUIDE-R3-001 — Medium — final-seed threshold-lock order is contradictory and not executable

Guide lines 358–369 declare this order:

```text
pilot validation report
→ optional append-only successor approval
→ lock configuration and threshold in the repository
→ train three seeds
→ lock threshold in the repository
→ consider the one sealed-test evaluation
```

The first threshold-lock step cannot produce the governed final lock. Current
`m1.cli lock-thresholds` requires exactly three validation reports, the exact D-05 seed set
`20261018`, `20261019`, `20261020`, and three distinct run weights. The contract then binds the
lock to those three reports, weights, run contracts and attestations. D-05 selects models using
pooled validation evidence across seeds and requires confidence/NMS to be chosen on validation and
locked before the test opens. The canonical next-task sequence likewise trains the three seeds
before locking confidence/NMS from their validation reports.

The implementation therefore fails closed if an operator attempts the literal pre-training lock,
but the guide can still cause the Owner to create an informal pilot-only threshold artifact, stop
mid-workflow, or misunderstand which of the two stated locks is authoritative. This is a material
operator error rather than a sealed-test bypass, so it is Medium.

Required remediation in a successor guide revision:

1. After pilot review and any append-only gate successor approval, lock only the final **training
   configuration** used by all three seeds.
2. Train the three approved seeds with that identical configuration; download and independently
   verify every result package.
3. Evaluate all three final weights on validation and retain one governed validation report per
   seed.
4. Create the single final threshold lock from exactly those three validation reports with
   `m1.cli lock-thresholds`; independently review it and commit it cleanly before any sealed-test
   access.
5. Keep the sealed test closed until that single three-seed lock and all other final-evaluation
   prerequisites pass.

The R1, R2 and R3 FAIL records must remain immutable; request independent QA again on a successor
guide revision.

## Other contract readback

- The guide preserves the train/validation-only boundary and forbids `export-test`, `--final-eval`,
  test-driven tuning, assert bypasses, horizontal flip, taxonomy changes, unapproved weight
  substitution and run-directory reuse.
- The notebook remains seven cells total, with six unexecuted code cells and no outputs. Its order
  is Drive mount, configuration, embedded-manifest/commit selection, `uv`, governed runner and
  terminal readback. The required inserted preflight is explicitly ordered before manifest access.
- Drive paths, bundle names, bound commit, L4 selection, smoke defaults, seed values, runner steps,
  five state-directory outputs and the exact eight-file result roster agree with the current
  notebook, runner, verifier, upload record and D-05 decision.
- The SQLite schema in the guide exactly matches the runner: `id`, `timestamp`, `level`, `logger`,
  `message`. Packaging requires a valid database, exact columns, INFO records from
  `CPV_log_record`, ordered workflow/training/terminal events and persisted subprocess output.
- The standalone local verifier command is valid. It accepts only the exact eight-file roster,
  regular tar members, matching sizes/hashes, `D1_COLAB_RESULT_PACKAGE`, `SUCCEEDED`,
  `sealed_test_accessed=false` and a syntactically valid run-attestation hash. No real result archive
  exists yet; therefore only its synthetic tests and CLI help were run, and no model-result claim is
  made.
- Failure guidance preserves run evidence, uses a fresh label/state directory and restarts from the
  beginning. It does not instruct resume, deletion of Drive evidence, hash bypass or test access.
- The cascade caveat is accurate: its R2 package/control received QA PASS, but its gate addendum is
  still unapproved, so it remains validation-only. The classifier caveat is also accurate: two
  candidates exist, no architecture or Colab notebook has been approved, and the 43-class GTSRB
  model must not substitute for the 54-class WP33 classifier.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R3 operator guide | `46c19ffc5ce80fde34fb1e1bb47d4acb5e1c24362bfbd1c11b341a66dc389cd8` |
| Immutable R1 QA record | `70b4e0384a3faaf44e66ba1c86266d035ba622a0e358589734d66423ea84da86` |
| Immutable R2 QA record | `63bdbf3300a9d84e915bd1d5196b0b83729e06186a87ae6dc867dcd644df60d0` |
| R2 remediation report | `0906a8b00b6a33d2065327f5a569e34bc69e5aab273b9c799db28612c9c07214` |
| R3 remediation report | `98ee3c8977b11f1606c4e6ff802fbd2652104789cd40e79f3fc215e25447aa00` |
| Notebook | `4f7e5df089efaa01be8045c232dd02cb1a4a44e97a399530778c6e639b4babca` |
| Runner | `0d04c869d0181c68a4d60a93b05967c4db5b5e31cfc44cf653bfcbd43f225786` |
| Standalone verifier | `678de7f84e54c568dd3d7001873541a6226eeb2da0e5b2f725fdcde49fb994ab` |
| M1 CLI | `86c92e642cd733a7cdd9151f85acf09267cd3b35f4ccad81ff64a207d19f2672` |
| M1 contract | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |
| Private upload record | `3fda6ac5f9d775668e21decf22619faa6d5fdb94f6eabbf9bca436f17de568f7` |
| M1-Colab-R3 QA record | `4b3ddcfebcb7b055dc42c229cd890234bf6decd32e8fe2a965d372732a5503c0` |
| D-05 Owner decision | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` |

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
| Standalone result verifier CLI/help and notebook JSON | PASS; no real result archive exists |
| `git diff --check` | PASS |
| Graft freshness/orientation/task queries | PASS; wiring graph synchronized at 2,516 nodes and 6,372 edges |
| Exact sealed-test access log | ABSENT |

The full historical root pytest suite was not run because the task-specific 22-test gate, complete
detector suite, exact bound-bundle verifier, Ruff, locks and document/control readbacks cover this
document-only review. No Colab cell ran, no Google Drive object was changed or downloaded, no model
was trained, no sealed-test artifact was opened, and no commit, push, upload, deployment or
publication occurred.
