# M1 independent QA record

Status: `QA_FAIL_M1_BLOCKERS_REQUIRE_REPAIR_BEFORE_TRAINING`
Reviewer: `Codex independent QA session (did not author the M1 package and did not act as PM)`
Reviewed at: `2026-10-18T22:23:33+07:00`
Boundary: `QA_OF_M1_PACKAGE_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `eae9146e471fff261d674a4ec9653ee073301b37`

This record reports independent QA of the M1 YOLO export, the DATASET01 crop export and the
separate detector package. It changes no builder, test, manifest, owner record, pin, dataset,
model weight, roadmap or project-memory file. The pre-existing owner follow-up changes in the
working tree were preserved.

## Verdict

- **M1: FAIL.** 1 Critical, 3 High, 1 Medium, 0 Low.
- The current train/validation bytes are internally consistent and the requested mechanical gates
  pass, but the package is not fail-closed at three security/governance boundaries: sealed-test
  evaluation, materialised-dataset integrity and pretrained-weight identity.
- **Do not start the pilot or any final evaluation from this package.** PM must repair C-1 and
  H-1 to H-3, add regression attacks, and request a new independent QA run. M-1 must be repaired
  before the three-seed candidate can be judged or the sealed test can be opened.
- This verdict is QA of the package only. It does not revoke the owner's Gate-0/D-05 decisions,
  approve either D1 baseline, approve Colab upload, or approve deployment/publication.

## Package bytes reviewed

| Item | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset.py` | `0c18242d27486c225b3bd8f9fc75660c20e72a8ee58b238c5cf0a5b6ac1ccec7` |
| `scripts/build_dataset01_crops.py` | `8096de4ffadd31ac31869f072a997a21c31eb2275a16c852fe5204bc1ad4429d` |
| `tests/test_m1_yolo_dataset.py` | `ba18617c823caca960736f5a6fd2597799be02e2c88acf25ad30c1719d4ae740` |
| `tests/test_dataset01_crops.py` | `8a65f981af6a42c84f967f4c60a689400d952531d7f5b3630586f0851ec60360` |
| `detector/m1/contract.py` | `0c8ddb549f1256c3ade3eeab72bebd08141945067938b97870bc43e4cb161c37` |
| `detector/m1/metrics.py` | `d9078eecd2e42f5c77b3cac37a500f430e3e9f732cafccd7ca5d3e2f78c43a65` |
| `detector/m1/cli.py` | `8dc0787fc1c1b7362ac61318ba30ad6d6824e7bba1db20c71d3bddc81c2b42a5` |
| `detector/tests/test_m1.py` | `820e7fd4b59484322a0f4d2c8f4a35056d31da02d5560b3fc91a501f3d41c7dc` |
| M1 export manifest | `d9beec1d69f56d3223c1a204d4606c8c4dd25dd72d841e2048fc424c0bb05fcc` |
| DATASET01 crop manifest | `daa6eb632b102d3056d16086303ff7eacf7ed395e47e42dcf8ccdb99e3bb9024` |
| `detector/pyproject.toml` | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| D-05 owner record | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` |

## Verified controls and readback

1. **Repository and Graft.** The branch is `DEV/Rroject_Pineline`, HEAD and origin are both
   `eae9146`. `graft check .` reports the wiring graph in sync. Graft located the two builders,
   `detector/m1/{contract,metrics,cli}.py` and their tests before source readback.
2. **Split and labels.** The M1 manifest verifies against its pinned WP33 and WP36-R1 inputs.
   The class map has exactly 54 unique WP33 `CLASS` keys with YOLO ids `0..53`; `UNKNOWN` and
   `16:UNREADABLE` are absent. The split guard rejects the existing split-list tamper test and
   binds train `6ac76750...`, val `ae3f3509...` and sealed test `afa03d4b...`.
3. **Current materialised train/val export.** Train has 3,712 image/label pairs: 1,912 governed
   DATASET01 frames plus 1,800 WP35 images. Val has 376 DATASET01 pairs and zero WP35 entries.
   Image and label stem sets agree; all images are live symlinks; all targets exist; the raw
   train and val aggregate label hashes equal the committed manifest.
4. **DATASET01 crops.** The committed manifest re-derives 12,621 train crops
   (5,415 DATASET01 + 7,206 WP35 boxes) across 54 classes and 560 val crops across 19 classes.
   WP35 is train-only. The crop geometry tests cover the 10 percent/minimum-5-pixel border and
   frame-edge clipping.
5. **Augmentation and telemetry.** Training arguments force `fliplr=0.0`. A synthetic train
   capture confirmed the argument reaches `YOLO.train`. Current Ultralytics settings have
   `sync`, ClearML, Comet, DVC, MLflow, Ray Tune, TensorBoard and W&B all disabled. Train,
   evaluate and latency call `disable_telemetry()` before constructing a YOLO model.
6. **Metrics.** Greedy matching is descending-score, one prediction to one unmatched ground-truth
   box at IoU 0.5. Independent synthetic checks reproduced identity IoU 1.0, wrong-class rejection
   for class-aware recall, acceptance for class-agnostic recall, duplicate-prediction FP handling,
   threshold selection at recall at least 0.85 with minimum FP/image and deterministic resampling
   of complete D-02 groups. `select_threshold` breaks equal-FP ties toward the higher confidence.
7. **Pretrained weight artifact.** `models/pretrained/yolo11s.pt` exists, is 19,313,732 bytes and
   has SHA-256 `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`.
   `git check-ignore` resolves it through `/models/pretrained/`, and `git ls-files` confirms that
   it is not tracked. With offline mode and telemetry already false, Ultralytics loaded this exact
   local file as task `detect` with 80 COCO names.
8. **Sealed-test state.** QA did not open, export or inspect sealed-test frames or labels. Both
   detector test directories/YAML, the crop `test.p` and
   `results/experiments/sealed_test_access_log.jsonl` remained absent before and after QA.

## Executable gates

- Root Ruff: `uv run ruff check src tests scripts/build_m1_yolo_dataset.py
  scripts/build_dataset01_crops.py` -> PASS.
- Root lock: `uv lock --check` -> PASS, 168 packages resolved.
- Root targeted M1/crop tests: `13/13` passed.
- Package verifiers: `uv run python scripts/run_parallel_checks.py verifiers --jobs 8` ->
  **51/51 passed** in 104.8 s wall time.
- Detector Ruff: `uv run ruff check m1 tests` -> PASS.
- Detector lock: `uv lock --check` -> PASS, 66 packages resolved.
- Detector tests: `7/7` passed.
- `YOLO_OFFLINE=true uv run python -m m1.cli check` -> PASS; it reported commit `eae9146`,
  Python 3.12.13, Torch 2.14.1, Ultralytics 8.4.172, MPS available, the expected lock hash and
  the expected three split hashes.
- Final `graft check .` after this record was added -> PASS; the wiring graph remains in sync.

## Findings

### C-1 — Sealed test is read before the required locked confidence is validated

`detector/m1/cli.py:194-224` checks `--final-eval` and a reason, writes the access log, runs
Ultralytics validation on `split=test`, and loads every test frame. Only after those operations
does it reject a missing `--conf`. A synthetic QA attack used no real data and observed this exact
order:

```text
access_log -> contract_test -> telemetry_disabled -> model_init -> val_test -> load_frames
-> refusal: --conf (locked on val) is required
```

Thus a simple omitted option consumes the one-shot sealed evaluation before the CLI reports
failure. A supplied confidence is also accepted as an arbitrary float; it is not checked against
a signed/hash-bound val threshold artifact. This violates D-05 Q2/Q4.

**Required repair:** validate all final-evaluation preconditions before logging or touching the
test export: require a reviewed val-lock artifact, bind its confidence/NMS values and candidate
weight SHA-256, verify its hash/run lineage, and only then authorize the single test read. Record
test seal, weight hash, locked thresholds and terminal outcome. Add attacks for missing, changed,
NaN/out-of-range and non-val-locked confidence values; all must stop before model construction or
test enumeration.

### H-1 — Detector contract accepts tampered materialised training data

`detector/m1/contract.py:61-92` verifies the committed source-derived manifest and only the count
and names of non-WP35 label files. It does not bind `data.yaml` content/path, image roster or
symlink targets, label bytes, WP35 roster/bytes, or unexpected `wp35_*` files. On a temporary
copy, QA redirected `data.yaml` to the copy and replaced `labels/train/0072.txt` with a different
valid YOLO row. `check_contract()` still returned success and returned the tampered YAML path.

This means the source manifest can remain green while training consumes altered WP33 labels,
altered images, additional WP35-prefixed data, or a redirected dataset.

**Required repair:** create and enforce an exact materialised-export contract. Canonically bind
the YAML, exact train/val image and label rosters, every label byte, every raw symlink target and
source hash, and every WP35 image/label hash. Reject missing files, extras, redirected links,
non-canonical YAML and any byte mismatch before importing/loading YOLO. Add one attack test per
surface, including an extra `wp35_*` pair.

### H-2 — Training does not enforce the approved local `yolo11s.pt` identity

`detector/m1/cli.py:53-100` treats any string ending in `.pt` as pretrained. It does not require a
local file, resolve the owner-approved path, hash it, reject a mismatch, or prevent Ultralytics
from resolving/downloading a model name. The run contract records only the unverified string.
A fully synthetic attack passed `does-not-exist-yolo11s.pt`; the CLI proceeded to model loading
and training, and the resulting contract contained no model SHA-256.

The actual local file is correct and untracked, but that fact is not an enforced training
invariant.

**Required repair:** before YOLO import/construction, require the resolved local approved file
`models/pretrained/yolo11s.pt`, verify size and SHA-256
`85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`, and fail offline on any
missing/mismatch/non-local input. Record resolved path, size and SHA-256 in `run_contract.json`.
If from-scratch YAML remains supported, make it an explicit separate mode and record it as such.
Add missing/mismatched/arbitrary-name/symlink-substitution regression attacks.

### H-3 — Crop `verify` does not verify the exported crop package

`scripts/build_dataset01_crops.py:205-215` rebuilds arrays from sources and compares only the
committed manifest bytes. It accepts no output directory and never opens or hashes `train.p`,
`valid.p`, their index CSV files or `signnames.csv`. Therefore a missing or corrupted
materialised crop package can still report `valid=true`; the existing pickle test checks only a
few keys and the val sample count when `valid.p` happens to exist.

**Required repair:** make verification require an explicit/default output path and fail closed on
an absent output. Bind an exact output roster and file hashes, then independently load/check every
array hash, dtype, shape, index row and sign-name byte against the manifest. Reject extra files.
Add deletion, byte-flip, array-label, index, sign-name and extra-file attacks.

### M-1 — The CLI can present a single run as passing the D-05 gate and lacks the approved final report

`cmd_evaluate` returns `all_gates_passed` for one weight file, while D-05 judges the candidate on
the mean of seeds `20261018`, `20261019` and `20261020` with standard deviation. The JSON report
does not aggregate seeds and does not contain all mandatory Q6 evidence: AP-small, precision,
class recall/support in the exported report, per-resolution results, confusion/error samples,
UNKNOWN false-recognition rate, or explicit unverified train-only classes. NMS is fixed at 0.7,
not selected and locked with confidence as D-05 Q4 requires.

**Required repair:** label per-seed output as non-final, add a candidate aggregator over the exact
three approved seeds and their weight/run hashes, report mean and standard deviation, and produce
the complete D-05 Q6 evidence. Bind both confidence and NMS to the reviewed val-lock artifact.
Only the aggregate final-evaluation layer may emit a D-05 PASS/FAIL.

## Limits and governance

- No training, checkpoint creation, upload, download, deployment, commit, push or publication was
  performed.
- No actual model prediction, latency benchmark, Colab execution, CUDA environment or three-seed
  aggregation was run. The local COCO weight was only hash-checked and loaded offline.
- The raw sealed test was not accessed; therefore no test metric or final model claim exists.
- Graft is a wiring/source-navigation check, not proof of metric validity. The passing verifier
  and unit-test counts prove only the exercised paths; the attacks above demonstrate why they do
  not clear M1.
- The approved D-02 groups remain AI-inferred, val remains small/shifted, 22 classes have no
  sealed-test evidence, and low-light/night performance remains unknown. Even after package
  repair, a passing experiment would be research/simulation evidence, not driving-safety
  validation.
