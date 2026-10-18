# M1-R1 independent-QA remediation report

- Status: `M1_R1_AWAITING_INDEPENDENT_QA`
- Recorded at: `2026-10-18T23:23:48+07:00`
- QA input: `docs/review/m1_independent_qa_record.md`
- QA input SHA-256: `8c98a5d4d61f2be46c57ed9ea6a953f889896a5c26fb57a7315b2cc79966d169`
- Prior verdict: `FAIL` — 1 Critical, 3 High, 1 Medium, 0 Low

This is an append-only R1 package. It does not alter the original QA FAIL record and does not claim
QA PASS. No training, Colab upload, sealed-test export or sealed-test evaluation occurred.

## Finding closure implemented for re-review

### C-1 — sealed-test argument ordering and threshold binding

- All final-evaluation arguments are validated before weight binding, test logging, contract access,
  model construction, validation or frame loading.
- Test evaluation requires `--final-eval`, a non-blank `--reason`, `--conf`, `--bootstrap` and a
  clean Git-tracked `--threshold-lock` created from exactly the three D-05 val reports.
- Confidence and NMS IoU must equal the values bound to that run-weight SHA-256 in the lock.
- The access log records the weight SHA-256 and threshold-lock SHA-256 before test data is read.

### H-1 — materialised YOLO export not byte-bound

- The pinned WP1 image inventory now supplies the expected raw-image SHA-256 values.
- Verification checks exact YAML bytes, exact image/label rosters, every label byte, every image
  byte, and exact symlink targets when symlinks are used.
- WP35 is checked against its pinned lineage, is accepted only in train, and uses the deterministic
  WP33-to-YOLO label mapping.
- `materialise()` runs the byte verifier before returning success.

### H-2 — arbitrary or unpinned `.pt`

- Training accepts only `models/pretrained/yolo11s.pt` with Owner-approved SHA-256
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`.
- A completed training run records SHA-256 for both `best.pt` and `last.pt` in `run_contract.json`.
- Evaluate/latency accept only `<run>/weights/best.pt` or `last.pt`, require `TRAINED` status, an
  approved seed and an exact weight hash match to the run contract.

### H-3 — crop verifier ignored materialised files

- Crop verification now regenerates deterministic pickle bytes and requires exact `train.p`,
  `valid.p`, `train_index.csv`, `valid_index.csv` and `signnames.csv` bytes.
- Missing, modified or symlinked materialised crop outputs fail closed.
- `export()` verifies the written package before returning success.

### M-1 — single-seed verdict and incomplete report contract

- Single-seed reports expose diagnostic checks but always return `final_verdict=null` and
  `all_gates_passed=null`.
- `aggregate-final` requires exactly seeds `20261018`, `20261019`, `20261020`, the same committed
  val threshold lock, matching weight hashes and one M1-Pro MPS latency report per seed. Only this
  aggregate can emit the D-05 final verdict, using mean and population standard deviation.
- Evaluation reports now include project AP-small, precision/recall, per-class AP50 and recall with
  support, resolution breakdown, confusion matrix, error samples, UNKNOWN false-recognition,
  group-bootstrap confidence intervals and explicit unverified/low-support class lists.

## Bound R1 files

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset.py` | `fe1946cfe6a78213f3909e26d3cf27529e7ac696bc3b8eb6fd1ea554b08a8cc9` |
| `scripts/build_dataset01_crops.py` | `80f4a5e64894757c83b5c9d50e8265a4d1d9e09494dfabeaa733fa9388cdb263` |
| `detector/m1/contract.py` | `3647de5a61b590e352a4928e61b6645399c99d7974d9579c65e24418c4c16495` |
| `detector/m1/metrics.py` | `5be0503886760b2567a7d10ada38a2aad07d2964a8bdbb96019e1186274ab650` |
| `detector/m1/cli.py` | `e9d818fe87d8ee4bc46200ff5767b83f2beeca1b6e9246161cd8485440194e20` |
| `detector/tests/test_m1.py` | `a1adc5245e39cbf70c82a0bf9502adc3cf1890bc180e0f64c637850c517e43f5` |
| `tests/test_m1_yolo_dataset.py` | `189afb98036e73567cabf993949750be0622e2aaddabbdba0a945a09b453932c` |
| `tests/test_dataset01_crops.py` | `5048cc075305e7deb4613946963f529349f53d0e6c1a82a347edae61b82f4912` |
| `docs/review/generated/m1_yolo_export_manifest.json` | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` |
| `docs/review/generated/dataset01_crops_manifest.json` | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |

## PM validation before re-review

- Targeted root M1/crop tests: `15/15` PASS.
- Root Ruff: PASS; root `uv lock --check`: PASS (168 packages).
- Package verifiers: `51/51` PASS in 89.3 seconds wall time.
- Detector Ruff: PASS; detector `uv lock --check`: PASS (66 packages).
- Detector tests: `11/11` PASS.
- `m1.cli check`: PASS; test seal remains
  `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.
- Full historical root pytest was stopped after the known stale WP26 assertion that no WP27
  artifacts may exist. WP27/WP27-R1/WP27-R2 are legitimate later packages; the handoff already
  lists this family of seven stale tests as non-blocking technical debt. No M1-R1 test failed.
- Sealed artifacts remain absent: `images/test`, `data_test.yaml`, crop `test.p` and the sealed-test
  access log do not exist.
