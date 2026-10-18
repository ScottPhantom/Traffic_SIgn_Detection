# D1 cascade crop classifier R2 QA remediation report

Status: `D1_CASCADE_CLASSIFIER_R2_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

Supersedes implementation package R1; preserves the immutable R1 implementation record and
independent QA FAIL record.

Boundary: `REMEDIATION_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

## Prior verdict preserved

Independent QA issued `QA_FAIL_D1_CASCADE_CLASSIFIER_R1` with 0 Critical, 1 High, 1 Medium and
0 Low. The High finding showed that pre-existing `eval_val.json` and latency-report symlinks could
overwrite an external target. The Medium finding showed that otherwise-valid run provenance could
depend on external symlink targets for `run_contract.json`, `history.json` or a checkpoint.

R2 changes only the classifier contract implementation and its tests within the executable
package, plus this successor report and routing status. It does not edit or replace either R1
record.

## R2 remediation

### High — report writes fail closed and are atomic

- Output paths remain lexical absolute paths; `resolve()` is not used to erase symlink identity.
- Every existing component from the filesystem anchor through the results parent is inspected
  with `lstat()`. A symlink anywhere in that chain is rejected.
- A pre-existing final output must be a regular file. A FIFO, directory, device or symlink is
  rejected before any report bytes are written.
- JSON is encoded in memory, written and `fsync()`ed to a same-directory `mkstemp` file. Python's
  binary temporary-file flags include exclusive creation and `O_NOFOLLOW` on this platform.
  `os.replace()` atomically promotes the completed file. A raced-in final symlink is replaced as
  a directory entry and is never followed to its target.
- The real `evaluate` and `latency` CLI paths now have regression tests with external report
  targets. Both commands return failure and both external targets remain byte-identical.

### Medium — all run provenance is local, regular and non-linked

- `load_run_weights()` now preserves the lexical requested checkpoint path and checks containment
  under the lexical fixed results root before reading anything.
- The results root, run directory, weights directory and every existing component are rejected if
  linked.
- `run_contract.json`, `history.json`, selected checkpoint and sibling checkpoint must each be a
  regular non-symlink file inside the run. Every artifact remains schema-, path- and SHA-bound.
- Regression tests cover all four individual file symlinks, a symlinked run parent and a direct
  checkpoint outside the results root.

## R2 byte snapshot

| File | SHA-256 |
| --- | --- |
| R1 implementation record (unchanged) | `476cfc6b0f3572b41720ab7053ddac40827f251e4c7e1fd3329c7dac457d1f25` |
| R1 independent QA FAIL record (unchanged) | `ab545fd1fc13162fb5b0b3d6567ccd43a28ec39a02421eeefb72ac8de81204b8` |
| Classifier `__init__.py` | `fda3d39a0603c715c111ce2eac8757932d27a0b45104a47b8802331d7336435b` |
| Classifier CLI (unchanged) | `45091eb2d1f01c9d05912ed347b90911fd16b16c82df6e8dc3fcc79f16dc0116` |
| Classifier contract R2 | `e847db9ae322fe3a7ba11e8e77743ec32440027f5d29222f2c937d746a9cfc94` |
| Classifier data adapter (unchanged) | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| Classifier metrics (unchanged) | `612259aa52bf8794db3c717b7b6f481532f9bccc572034709cfcefc66d316078` |
| Classifier models (unchanged) | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| Classifier tests R2 | `02691842c0dd49c9d73a0b070c11c3d538a7395f4922c8f803d0098666e2f85e` |
| Crop manifest (unchanged) | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |
| Detector project config (unchanged) | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| Detector lock (unchanged) | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

## Verification

- R2 targeted classifier suite: `25/25` PASS.
- Complete detector suite: `79/79` PASS.
- Detector `m1`, classifier and tests Ruff: PASS.
- Detector lock: PASS, 66 packages.
- Root crop suite: `7/7` PASS; targeted Ruff and root lock (168 packages): PASS.
- Governed classifier `check`: PASS; train 12,621, validation 560,
  `sealed_test_accessed=false`.
- `git diff --check`: PASS.
- Exact sealed-test access log remains absent; no classifier results directory or model run was
  produced.

## Independent QA request

QA should reproduce both original R1 counterexamples against R2, then exercise pre-existing final
report links, parent-directory links, contract/history/best/last links, outside-root paths and
ordinary regular-file report replacement. R2 remains unavailable for a pilot until a separate QA
session issues PASS. Architecture choice, training, gate approval and sealed-test access all remain
outside this remediation.
