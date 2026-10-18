# D1 cascade crop classifier R1 independent QA record

Status: `QA_FAIL_D1_CASCADE_CLASSIFIER_R1`
Reviewer: `Codex independent QA session (did not author R1 and did not act as PM)`
Reviewed at: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Boundary: `QA_OF_D1_CASCADE_CLASSIFIER_R1_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `150777a49d010096fbe246a61a9589f2a27b9e00` plus the current uncommitted R1 worktree

This append-only record independently reviews only `detector/d1_cascade_classifier/`,
`detector/tests/test_d1_cascade_classifier.py`, the R1 implementation record and its routing
status. Independent QA changed no implementation, test, dataset, manifest, model, result or Owner
decision. Because the verdict is FAIL, `PROJECT_MEMORY.md` and `docs/product_roadmap.md` retain
their `AWAITING_INDEPENDENT_QA` state.

## Verdict

- **D1 cascade crop classifier R1: FAIL.** 0 Critical, 1 High, 1 Medium, 0 Low.
- The governed data, taxonomy, model, seed, augmentation, metric and latency constants checked out,
  but result output and run-provenance paths do not consistently fail closed on symlinks.
- This FAIL does not authorize a pilot, architecture selection, training, sealed-test access,
  upload, download, commit, push, deployment or publication. The cascade gate addendum remains
  `PROPOSAL_NOT_OWNER_APPROVED`.

## Findings

### QA-D1-CC-R1-001 — High — validation and latency report paths can overwrite files outside the run

`cmd_evaluate()` writes `eval_val.json` and `cmd_latency()` writes `latency_<device>.json` through
the generic `write_json()` helper. That helper creates a missing parent but performs no lexical
containment check, `lstat()` walk or final-component symlink rejection before `Path.write_text()`.

An isolated executable counterexample created a valid-shaped run directory, placed
`run/eval_val.json` as a symlink to `outside.json`, stubbed only model/data inference so that no
real training or evaluation occurred, and invoked the real `cmd_evaluate()` report-writing path.
The command returned normally and replaced the external target contents with the JSON evaluation
report (`eval_symlink_external_overwritten=True`). `cmd_latency()` reaches the same unguarded sink.

Impact: a pre-existing report symlink can escape the fixed results root and overwrite an arbitrary
file writable by the process. This contradicts the R1 implementation claim that new result paths
fail closed on symlink components and repeats the output-symlink failure class that previously
blocked the D1 cascade dataset R1 package.

Required remediation: preserve the lexical result path, reject every existing symlink component
and the final output entry with `lstat()` before writing, and add real-command negative controls
for evaluation and latency report symlinks that prove the external targets remain byte-identical.

### QA-D1-CC-R1-002 — Medium — run provenance accepts external symlink targets

`load_run_weights()` resolves the requested checkpoint and constrains that resolved checkpoint to
the results root, but it does not reject symlinks for `run_contract.json`, `history.json` or the
non-requested checkpoint artifact. Isolated contracts with correct schemas and hashes were
accepted when `run_contract.json` or `history.json` was a symlink to a file outside the results
root (`external_run_contract_symlink_accepted=run` and
`external_history_symlink_accepted=run`).

Impact: an apparently self-contained accepted run can depend on provenance/artifact files outside
its governed root. Hash verification prevents an incoherent content substitution at the instant of
verification, so this is lower severity than the external-write issue, but it violates the stated
fixed-root/fail-closed boundary.

Required remediation: reject symlinks and non-regular files for the run contract and every exact
artifact before reading or hashing them; cover contract, history, selected checkpoint and sibling
checkpoint symlinks in regression tests.

## Verified controls that did pass

- The reviewed crop manifest SHA-256 matched
  `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576`.
- The exact data roster was only `train.p`, `valid.p`, `train_index.csv`, `valid_index.csv` and
  `signnames.csv`. The governed check returned train `12,621`, validation `560` and
  `sealed_test_accessed=false`.
- Independent array/count reconciliation found all 54 train classes and exactly 19 validation
  classes. The 35 absent validation classes were
  `1,9,11,15,16,17,18,19,20,21,22,23,24,26,27,29,30,31,32,34,36,37,38,39,41,43,44,45,46,47,49,50,51,52,53`.
- Restricted pickle loading rejected an arbitrary `pathlib.Path` global. Exact manifest, index,
  array, dtype, shape, contiguity, class-count and sign-name checks passed on the governed package.
- Both architectures produced the contracted 54 outputs; the VGG constructor is explicitly
  `vgg16(weights=None, num_classes=54)`. Seeds are exactly `20261018`, `20261019`, `20261020`,
  loader workers are zero, and horizontal flipping/geometric augmentation is absent.
- Independent metric reconciliation confirmed top-1, supported-class macro-F1, supported-class
  balanced accuracy, 54 support/recall rows and 15-bin ECE behavior. Unsupported validation
  classes remain `None`/explicit rather than entering the supported-class averages.
- The latency contract is batch 1, 50 warm-ups and exactly 300 measured model forward plus
  Softmax/argmax iterations. This is classifier inference timing, not the proposed full-cascade
  latency evidence.
- The parser exposes only `check`, `train`, `evaluate` and `latency`; evaluation has no split or
  final-evaluation argument. The exact sealed-test access log
  `results/experiments/sealed_test_access_log.jsonl` and the classifier results directory were
  absent during QA.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R1 implementation record | `476cfc6b0f3572b41720ab7053ddac40827f251e4c7e1fd3329c7dac457d1f25` |
| Classifier `__init__.py` | `fda3d39a0603c715c111ce2eac8757932d27a0b45104a47b8802331d7336435b` |
| Classifier contract | `d17e51319104dad48e2cfd68342d8a1e12c1dce33c35d1a0b1aee5187663288f` |
| Classifier data adapter | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| Classifier model definitions | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| Classifier metrics | `612259aa52bf8794db3c717b7b6f481532f9bccc572034709cfcefc66d316078` |
| Classifier CLI | `45091eb2d1f01c9d05912ed347b90911fd16b16c82df6e8dc3fcc79f16dc0116` |
| Classifier tests | `f2cfe59af15381d0e386ca8df88d8265af098e2b976c71a6eeb5829fad00b4ee` |
| Crop manifest | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |
| Detector lock | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| Detector project config | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| Dual-baseline Owner decision | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` |
| Cascade gate addendum proposal | `56d100532278fc5a13d552c3a067821508d5b40f9a04704092ff88c8b371f403` |

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| Governed classifier `check` | PASS | 54 classes; train 12,621; val 560; sealed test false |
| R1 targeted tests | PASS | **16/16** |
| Entire detector suite | PASS | **70/70** |
| Classifier-scoped Ruff | PASS | `All checks passed!` |
| Entire detector Ruff | FAIL outside reviewed classifier scope | 6 findings only in uncommitted `colab/d1_cascade_train.ipynb` |
| Detector lock | PASS | 66 packages resolved |
| Symlink negative controls | FAIL | external report overwrite; external contract/history accepted |

The full detector Ruff failure is recorded for reproducibility but is not classified as a
classifier R1 finding because the notebook is a separate uncommitted package explicitly outside
this review. The classifier source and its test file are Ruff-clean.

## Final boundary

- No implementation, test, manifest, data, model, result or routing status was edited.
- No model was trained, evaluated or benchmarked; the report-write counterexample used synthetic
  in-memory stubs and a temporary directory.
- No sealed-test image, crop, label, metric or access log was read or produced.
- No upload, download, commit, push, deployment or publication occurred.
- A successor package requires independent QA; this R1 FAIL record remains append-only.
