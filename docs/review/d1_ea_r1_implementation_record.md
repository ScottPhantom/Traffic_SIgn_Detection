# D1-EA-R1 — validation error evidence package — implementation record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: **IMPLEMENTED AND BUILT — REPRODUCES R10 — AWAITING INDEPENDENT QA**
Author: Claude Code session (took over the unfinished Codex work, see
`docs/claude_handoff_2026-10-22.md`)
Boundary: `VALIDATION_ONLY_DIAGNOSIS_NO_TRAINING_NO_SEALED_TEST_NO_VAL_PIXELS_IN_TRAIN`

This record does not authorize a smoke run, training, new seeds, sealed-test access, model
acceptance or a push.

## Purpose

`docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md` (independent QA
PASS, `docs/review/d1_corrected_val_r10_error_analysis_r1_independent_qa_record.md`) requires a
validation-only evidence package before any training change. The R10 report stores the confusion
matrix and bounded stem samples, but not every predicted box or a visual atlas. D1-EA-R1 adds
both, so that the root-cause hypotheses in the packet can be checked visually.

The owner chose to run the inference on local MPS, the R10 reference device, so that the
predictions reproduce R10 exactly. Training stays on Colab L4 (owner, 2026-10-22).

## Implemented source

| File | SHA-256 | Role |
| --- | --- | --- |
| `detector/m1/error_analysis_r1.py` | `6268c3fec6695fa568ed2f7ac59e824b1aad9fc537cf7df729a7040dd38d8192` | Pins, R10 reproduction check, prediction export, atlas, report, manifest; `build` / `verify` CLI. |
| `detector/tests/test_error_analysis_r1.py` | `5373f248bc30090093c5f8a6efd437b6f07f458a28734b63ae85e83ff607704b` | 10 synthetic tests (no model). |

No existing file was edited. The module imports the R10 chain (`corrected_val_r10` for the data
authority, `corrected_val_r1.load_corrected_frames` for inference) and `metrics` without changing
them.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| R10 report `results/experiments/…_r2/eval_val_wp38_r1_r4_r10.json` | `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5` |
| Weights `…_r2/weights/best.pt` (local only, not committed) | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| `detector/m1/corrected_val_r10.py` | `5897e951244a5e8761bda7202779fe30acb0d5da085686d49c96a04f69e5dfd3` |
| `detector/m1/corrected_val_r1.py` | `0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| Class map `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` |
| R10 result QA record | `9940b31c344e9e683d0bd3d6ddc25b8a31053bbeb83398801637be08df2d06a2` |
| Error-analysis packet R1 | `9ec8dd0d9e2866ef098ca3afada624ea5562837531f9b077981c45940ed0f78f` |
| Packet R1 QA record | `c4b8fa62bd158ba4f300b28cf14bb9c4d8f1147dbf410e4a57582f70fb565942` |

At build time the module also runs `corrected_val_r10.verify_corrected_data()`, which re-checks the
R9 pin chain, the WP38-R1 R4 integration authority, the materialised export and that no test split
is referenced. It then calls `contract.bind_run_weights`, which binds the weights to the committed
run registry.

## Contract

- **Diagnostic point:** conf 0.20, NMS IoU 0.70, imgsz 1280, device MPS. These are the R10 values;
  the module refuses to run if the report differs.
- **Reproduction gate (fail closed).** Nothing is written unless the raw MPS predictions reproduce
  the pinned R10 report exactly:
  - images, ground truth, true positives and false positives at conf 0.20;
  - the full 55×55 confusion matrix and its labels;
  - class-aware hits and support of every class listed in `gates.classes`.
- **Prediction table** (`docs/review/generated/d1_ea_r1_predictions.csv`). It has one row per
  prediction with confidence ≥ 0.20, in score order per image. Boxes and confidences are stored
  as exact `repr` floats, so `verify` can repeat the matching bit for bit. The disposition is
  `PAIRED` (with GT index, GT class and IoU) or `BACKGROUND`, taken from the same score-ordered
  class-agnostic one-to-one pairing as the R10 confusion matrix.
- **Missed ground truth** (`d1_ea_r1_missed_gt.csv`). It lists every unmatched GT box with the best
  IoU and class of any retained prediction.
- **Atlas** (`docs/review/assets/d1_ea_r1/`, git-ignored because it contains DATASET01 pixels). It
  has 30 tiles per page, with a green GT box and a red prediction box. Categories:
  - `background_fp`: every background false positive, sorted by predicted class;
  - `critical_7`, `critical_32`, `critical_41`: every GT box of the class that the pairing assigns
    to another class or leaves unmatched;
  - `pair_46_to_10` and `pair_8_to_12`: every pair of that confusion.

  The page and slot roster is `d1_ea_r1_atlas_index.csv`.
- **Round trip.** `build` renders every artifact from frames rebuilt out of its own prediction
  table, so `build` and `verify` read identical inputs.
- **Append-only.** `build` refuses if any output already exists.
- **Manifest** (`d1_ea_r1_manifest.json`). It records the pins, the reproduction summary, the
  Pillow version and the SHA-256 of every artifact, with `test_included=false`,
  `sealed_test_accessed=false`, `training_authorized=false` and
  `validation_pixels_in_training=false`.

## Commands

```bash
cd detector && uv run python -m m1.error_analysis_r1 build    # once, MPS inference
cd detector && uv run python -m m1.error_analysis_r1 verify   # no model; byte-compares everything
cd detector && uv run pytest -q -p no:cacheprovider tests/test_error_analysis_r1.py
```

## Local verification

- `ruff check` and `ruff format` are clean on both new files.
- `tests/test_error_analysis_r1.py`: 10 passed.
- **Build (2026-10-22, local MPS, about 3 min): reproduction gate PASS.**

  | Quantity | Count |
  | --- | ---: |
  | Images | 376 |
  | Ground-truth boxes | 560 |
  | Retained predictions | 697 |
  | Paired with ground truth | 483 |
  | Background false positives | 214 |
  | Unmatched ground truth | 77 |

  These equal R10 exactly, including the full confusion matrix (SHA-256 `6f932feb…`) and every
  gated class's hits. The build wrote 20 artifacts: 15 atlas pages, three CSVs, the report and the
  manifest (`d87f090e11d7acc547fb49eeb76935e2e0bcc743f3bc3fba56ab23a1cd8e07ab`).
- `verify` returns `valid=true` (no model; about 1 s).
- **Atlas coverage** (all from `d1_ea_r1_atlas_index.csv`):

  | Category | Items | Covers |
  | --- | ---: | --- |
  | `background_fp` | 214 | all 214 background false positives |
  | `critical_7` | 49 | 13 wrong-class pairs + 36 missed |
  | `critical_32` | 11 | 6 wrong-class + 5 missed |
  | `critical_41` | 10 | 8 wrong-class + 2 missed |
  | `pair_46_to_10` | 58 | all 58 pairs |
  | `pair_8_to_12` | 6 | all 6 pairs |

## Author's first visual review (hypotheses only, for QA and the owner)

I read background-FP pages 01, 02, 04 and 06 and critical-7 page 01, and checked raw crops of
1212, 1820, 1721, 0065 and 0339. Every statement below is a hypothesis to test, not a conclusion.

1. **About 31 % of background false positives are duplicates of a sign that is already matched.**
   66 of the 214 have IoU ≥ 0.5 with a ground-truth box that a higher-scoring prediction already
   paired with. Examples: 1721, where the same triangle is predicted as both 5 and 4; 1208–1245,
   where class 12/30 boxes sit on the same board.

   As a diagnostic only, I re-scored the exported predictions with class-agnostic NMS. Agnostic
   NMS at IoU 0.7 lowers FP/image from 0.569 to 0.434, and at IoU 0.5 to 0.378, with unchanged
   class-agnostic recall 0.8625. It also slightly lowers class-aware recall for class 7
   (0.595 → 0.559) and class 41 (0.571 → 0.524), because it can drop the correct-class box.

   This is a post-processing question that needs no training. Under D-05 Q4, NMS is chosen on val,
   but changing it still needs its own governed, QA-passed evaluation contract.
2. **Many of the 138 "no ground truth nearby" false positives look like real signs that are not
   labelled in validation.** 1212 labels only class 26, while classes 23, 10 and the 40/60 speed
   discs are clearly visible and predicted. 1820 labels only class 34, while the no-entry/keep-right
   pair (2/3) is visible. The P.130 and P.111 sequences in 1208–1225 and 1342–1357 show the same
   pattern. If this holds, FP/image is inflated by incomplete validation labels, as WP34 already
   found for empty frames. A validation label-completeness audit, a derived relabel in the
   WP33/WP34 style, should come before any hard-negative mining.
3. **Class 12 (R.415a lane allocation)** predictions often box one sub-panel of a multi-panel
   board that is labelled as a whole (1240–1245, 1350–1351): a box-extent convention issue.
4. **Class 7 (P.123a):** 36 of the 49 errors are misses on a tiny, blurred sign in one sequence
   (0279–0296), which suggests small-object limits. The 0336–0346 sign predicted as 17 (P.124a)
   carries a motorbike pictogram with a turn arrow. Its true QCVN code should be checked against
   the D-03 taxonomy before it is counted as a model error.

## Not concluded here

The visual root-cause review of the atlas and the independent QA of this package are separate
steps. No Track A or Track B change is decided by this record.
