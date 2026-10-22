# D1 corrected-validation evaluator R1 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex independent source-QA session`  
Boundary: `READ_ONLY_NO_MODEL_INFERENCE_NO_EVALUATION_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 2 High, 0 Medium and 0 Low findings.**

The static validation contract, R4 authority hashes, registered pilot checkpoint, 376/39 roster,
CCW90 geometry, validation-only parser, metric construction and one-image-at-a-time prediction
flow are correct at preflight. The evaluator is not safe to execute yet because it loses those
input identities after preflight and its final report write is neither exclusive nor no-follow.

This FAIL preserves the reviewed R1 bytes and authorizes only an append-only remediation package.
It does not authorize running corrected validation, training, upload, commit/push, sealed-test
access, final evaluation, model acceptance or deployment.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r1.py` | `0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5` |
| `detector/tests/test_corrected_val_r1.py` | `b05f314885877c72e4d57b84dbedd8e194f1f97dab7a93d35439ab7ff8d0c3a0` |
| `docs/review/d1_corrected_val_r1_implementation_record.md` | `81c127352ad91b2bece370d77b7e4fe3e46cc3ea0056c46aa3b180362dd9898f` |
| R4 integration independent QA PASS record | `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591` |
| pinned R4 exporter | `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426` |
| pinned R4 integration manifest | `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

All requested source and dependency hashes matched before and after QA.

## Properties independently verified

### Authority, data and registered checkpoint preflight

- `verify_corrected_data()` pins and hashes the exact R4 exporter, R4 manifest and R4 independent
  QA PASS record before loading the exporter.
- The real R4 verifier and descriptor-bound materialised verifier both passed on the current
  candidate. The dependency regression suite passed **11/11**.
- The current materialised contract reports exactly 376 validation frames and 39 corrected frames,
  with `test_included=false`, `sealed_test_accessed=false`, and no test route in `data.yaml`.
- The real registered pilot `best.pt` was bound read-only through `contract.bind_run_weights()`:
  seed `20261018`, weight SHA-256
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`, run-contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`, attestation SHA-256
  `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc`, and committed registry
  SHA-256 `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`.

These are valid preflight facts. H-1 below explains why they are not retained as use-time facts.

### Validation-only surface and metric parity

- The parser exposes exactly `check` and `evaluate`; `evaluate` has no split selector.
- Source contains no training call, `export-test`, `--final-eval`, or `split="test"`. Ultralytics
  validation is hard-coded to `split="val"` and `conf=0.001`.
- The report uses the same metric functions as the governed existing evaluator: mAP50,
  mAP50-95, AP-small, per-class AP50, validation threshold selection, resolution breakdown,
  UNKNOWN false recognition, confusion matrix, error samples, group bootstrap and gate report.
- `cli.iter_image_predictions()` receives one image path per call with `stream=True`, consumes
  exactly one result, rejects zero/multiple results and never preloads all full-resolution images.
  Retaining 376 compact `Frame` records is bounded independently of image pixel payload size.

### CCW90 UNKNOWN-box geometry

`contract.unknown_boxes()` currently returns one governed UNKNOWN box on each corrected stem
`1319..1328` (10 boxes). The evaluator's corrected-stem set is exactly `1319..1357`; therefore it
rotates all ten affected UNKNOWN boxes and applies a harmless empty transform to the remaining
corrected stems.

The normalized transform is implemented before pixel conversion:

```text
x' = y
y' = 1 - x
w' = h
h' = w
```

An independent mock-roster test used 376 images and a 10×20 image for stem `1319`. Source box
`[0.25, 0.40, 0.10, 0.20]` became normalized `[0.40, 0.75, 0.20, 0.10]`, then pixel XYXY
`[3.0, 14.0, 5.0, 16.0]`. No model inference was performed.

## Findings

### QA-D1-CORR-VAL-R1-001 — High — verified data and weight identities are not bound to use

`evaluate()` finishes the R4 materialised verification and registered-weight hash/registry check,
closes those reads, then passes only pathname strings to two new `YOLO` instances and later reopens
all validation images and labels by pathname. The long validation/prediction interval has no
retained descriptor, private immutable snapshot, identity revalidation or post-use hash binding.

Consequently, a same-user concurrent replacement after lines 199-200 can make the evaluator:

- validate different YAML/images/labels than the descriptor-bound R4 tree it records;
- load different `best.pt` bytes than the registered hash stored in the report; or
- replace the validated train/validation-only pathname with another tree after the no-test check.

The R4 verifier itself remains correct: its descriptors bind the tree only during its own replay.
The downstream evaluator discards that identity before Ultralytics consumes the files. This can
produce scientifically misbound metrics and undermines the claimed validation-only use-time
boundary.

Required append-only repair:

- load the model and validation data from evaluator-owned, exclusive, no-follow snapshots whose
  bytes/identities are derived from the verified registered weight and R4 materialised tree;
- keep the snapshots private for the full evaluation, bind their hashes/rosters into the report,
  and reject any identity change before reporting success;
- add adversarial tests that replace the public weight, YAML, root, image and label after preflight
  but before their mocked consumers open them.

### QA-D1-CORR-VAL-R1-002 — High — report no-overwrite policy is check/write TOCTOU

The evaluator checks `out.exists()`/`out.is_symlink()` before model construction, but writes only
after the entire validation and prediction workflow. `cli.write_json()` then calls
`Path.write_text()`, which overwrites an existing regular file and follows a symlink.

Independent mock attack, without model inference:

1. preflight observed an absent report;
2. mocked `YOLO.val()` created `eval_val_wp38_r1_r4.json` as a symlink to a separate owner file;
3. evaluation continued through mocked metrics;
4. `evaluate()` returned `CORRECTED_VALIDATION_COMPLETE` while the symlink remained and the owner
   file had been overwritten with the generated JSON.

The existing overwrite test covers only a report already present before `evaluate()` starts and
does not exercise the check/write interval.

Required append-only repair:

- serialize first, then create the final report at write time with exclusive/no-follow semantics
  (`O_CREAT|O_EXCL|O_NOFOLLOW` where available), validate the parent identity, write/fsync/close,
  and never use a replace operation over an owner path;
- add adversarial tests for a regular file, symlink, parent swap and nested-path swap introduced
  after preflight but before the final write;
- verify that every attack preserves the owner file and returns failure without a success claim.

## Mechanical evidence

```text
graft check .
graft ask "Trace corrected_val_r1 validation-only evaluator authority binding..." --source .
graft ask "Trace contract.bind_run_weights and cli.write_json used by corrected_val_r1.evaluate..." --source .
graft ask "Trace iter_image_predictions and all metrics called by corrected_val_r1..." --source .
cd detector && uv run ruff check m1/corrected_val_r1.py tests/test_corrected_val_r1.py
cd detector && uv run pytest -q tests/test_corrected_val_r1.py
cd detector && uv run ruff check m1 tests && uv run pytest -q && uv lock --check
uv lock --check
uv run pytest -q tests/test_m1_wp38_r1_integration_r4.py
```

Observed results:

- exact corrected-evaluator tests: **5/5 PASS**;
- full detector suite: **113/113 PASS**;
- R4 integration dependency tests: **11/11 PASS**;
- detector Ruff and both lock checks: **PASS**;
- Graft: graph synchronized after freshness-aware source query;
- exact sealed-test access log: absent before and after review.

The green tests establish the intended nominal behavior but do not cover either High attack.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R1 and this FAIL evidence | **YES** |
| Build append-only evaluator R2 | **YES** |
| Run R1 on the pilot `best.pt` | **NO-GO** |
| Train or retrain any model | **NO-GO** |
| Access/export/upload sealed test | **NO-GO** |
| Commit/push this package for operational use | **NO-GO** |
| Final evaluation/model acceptance/deployment | **NO-GO** |

Only a fresh independent QA PASS on an append-only repair may authorize the Owner workflow to run
corrected validation on the already trained pilot `best.pt`. Such a PASS would still not authorize
training or any sealed-test action.
