# D1 cascade crop classifier R2 independent QA record

Status: `QA_PASS_D1_CASCADE_CLASSIFIER_R2`

Reviewer: `Codex independent QA session (did not author R2 and did not act as PM)`

Reviewed at: `2026-10-19` (`Asia/Ho_Chi_Minh`)

Boundary: `QA_OF_D1_CASCADE_CLASSIFIER_R2_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

Reviewed checkpoint: `150777a49d010096fbe246a61a9589f2a27b9e00` plus the current uncommitted R2 worktree

This append-only record independently reviews only `detector/d1_cascade_classifier/`,
`detector/tests/test_d1_cascade_classifier.py`, the immutable R1 records, the R2 remediation
report and their routing status. Independent QA changed no implementation, test, dataset,
manifest, model, result or Owner decision.

## Verdict

- **D1 cascade crop classifier R2: PASS.** 0 Critical, 0 High, 0 Medium, 0 Low.
- R2 closes both R1 findings. The real validation and latency commands reject pre-existing report
  symlinks without changing their external targets. Run loading rejects linked
  `run_contract.json`, `history.json`, selected and sibling checkpoints, a linked run parent and
  checkpoints outside the fixed results root.
- This is package/control approval only. It does not select an architecture, authorize a pilot,
  approve the cascade gate addendum, authorize sealed-test access, or establish any trained-model
  result. No model run, training, evaluation benchmark, upload, download, commit or push occurred.

## R2 remediation acceptance

### Report-write finding

- `write_json()` preserves the lexical path, requires the parent below the lexical fixed results
  root, rejects every existing symlink component with `lstat()`, and rejects a non-regular final
  entry before writing.
- JSON is encoded before the write, written and `fsync()`ed through a same-directory `mkstemp`,
  then promoted with `os.replace()`. A regular pre-existing report was replaced successfully with
  no temporary residue; a FIFO was rejected.
- Independent real-command controls invoked `evaluate` and `latency` with synthetic in-memory
  inference only. Both returned failure for a report symlink, left the symlink in place and left
  the external target byte-identical.

### Run-provenance finding

- `load_run_weights()` keeps the requested checkpoint lexical, requires the run below the fixed
  results root, rejects linked path components, and requires the contract, history, selected
  checkpoint and sibling checkpoint to be regular non-symlink files.
- Independent isolated runs rejected each of those four file links, a linked run directory and a
  direct checkpoint outside the results root. All external bytes remained unchanged.
- Schema, artifact path/hash, current data contract, model/config/environment and canonical
  binding checks remain enforced after the path checks.

## Contract and semantic readback

- Governed manifest SHA-256 is
  `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576`.
- The exact governed roster is `train.p`, `valid.p`, `train_index.csv`, `valid_index.csv` and
  `signnames.csv`. The executable check independently read 12,621 train samples across all 54
  classes and 560 validation samples across 19 classes.
- The 35 classes absent from validation are
  `1,9,11,15,16,17,18,19,20,21,22,23,24,26,27,29,30,31,32,34,36,37,38,39,41,43,44,45,46,47,49,50,51,52,53`.
  Unsupported classes remain explicit `None` rows and do not enter supported-class macro-F1 or
  balanced-accuracy averages.
- An independent hand oracle reconciled top-1 `0.75`, supported-class macro-F1
  `0.7777777777777777`, supported-class balanced accuracy `0.8333333333333334`, all 54 per-class
  rows and 15-bin ECE `0.25`.
- Approved architectures remain exactly `compact_cnn` and `vgg16_scratch`; both contract to 54
  outputs and the VGG constructor uses `weights=None`. Approved seeds remain exactly
  `20261018`, `20261019`, `20261020`; loader workers are zero and horizontal flip/geometric
  augmentation is absent.
- The CLI surface is exactly `check`, `train`, `evaluate`, and `latency`. Evaluation exposes no
  split or final-evaluation argument and always loads the governed validation arrays.
- A sealed-test-named path was rejected before filesystem access. The exact access log
  `results/experiments/sealed_test_access_log.jsonl` and classifier results directory were absent
  before and after QA; governed readback reported `sealed_test_accessed=false`.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| R1 implementation record (unchanged) | `476cfc6b0f3572b41720ab7053ddac40827f251e4c7e1fd3329c7dac457d1f25` |
| R1 independent QA FAIL record (unchanged) | `ab545fd1fc13162fb5b0b3d6567ccd43a28ec39a02421eeefb72ac8de81204b8` |
| R2 remediation report | `8ebd1980478c36acc73f776f1d21de645dc4700a3d486d3bf3b7cc7595f66715` |
| Classifier `__init__.py` | `fda3d39a0603c715c111ce2eac8757932d27a0b45104a47b8802331d7336435b` |
| Classifier CLI | `45091eb2d1f01c9d05912ed347b90911fd16b16c82df6e8dc3fcc79f16dc0116` |
| Classifier contract R2 | `e847db9ae322fe3a7ba11e8e77743ec32440027f5d29222f2c937d746a9cfc94` |
| Classifier data adapter | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| Classifier metrics | `612259aa52bf8794db3c717b7b6f481532f9bccc572034709cfcefc66d316078` |
| Classifier models | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| Classifier tests R2 | `02691842c0dd49c9d73a0b070c11c3d538a7395f4922c8f803d0098666e2f85e` |
| Crop manifest | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |
| Detector project config | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| Detector lock | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| Dual-baseline Owner decision | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` |
| Cascade gate addendum proposal | `56d100532278fc5a13d552c3a067821508d5b40f9a04704092ff88c8b371f403` |

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| Governed classifier `check` | PASS | 54 classes; train 12,621; val 560; sealed test false |
| R2 targeted classifier suite | PASS | **25/25** |
| Complete detector suite | PASS | **79/79** |
| Root crop suite | PASS | **7/7** |
| Independent R2 attack matrix | PASS | **14/14** output/provenance assertions |
| Detector Ruff, including the notebook package | PASS | `All checks passed!` |
| Root `src`/`tests` Ruff | PASS | `All checks passed!` |
| Detector lock | PASS | 66 packages resolved |
| Root lock | PASS | 168 packages resolved |
| Git whitespace check | PASS | `git diff --check` returned 0 before the QA record edit |
| Graft freshness | PASS | wiring graph in sync; optional deep meaning layer not built |

The extra full-root pytest invocation reached terminal after exercising its image-heavy clean-room
rebuilds through WP29. A focused cached-failure readback reproduced seven historical lifecycle
assertions whose premise is that successor WP27/WP28/WP29/WP30 artifacts do not yet exist. Those
successor artifacts are intentionally present in the current project state, so this broad-root
gate is not green. None of the seven failures imports or exercises the D1 classifier R2 package;
the task-specific root crop suite and the complete detector suite both pass. This repository-wide
test debt is recorded here rather than misclassified as a D1 R2 finding.

## Final boundary

- No implementation, test, dataset, manifest, model or result was edited.
- No architecture was selected and no model was trained, evaluated or benchmarked.
- No sealed-test image, crop, label, metric or access log was read or produced.
- No upload, download, commit, push, deployment or publication occurred.
- The cascade metric/gate addendum remains `PROPOSAL_NOT_OWNER_APPROVED`; this PASS does not make
  the second baseline eligible for sealed-test use.
