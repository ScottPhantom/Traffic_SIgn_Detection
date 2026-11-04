# D1 YOLO54 improvement R3 — source and evaluation readiness contract

Status: `YOLO54_IMPROVEMENT_R3_AWAITING_INDEPENDENT_QA`
Boundary: `VALIDATION_ONLY_ANALYSIS_NO_TRAINING_NO_INFERENCE_NO_SEALED_TEST`
Author: Claude Code, worktree branch `claude/centercam-yolo54-r1`, 2026-10-23.
Implementation: `detector/m1/yolo54_improvement_r3.py`; tests:
`detector/tests/test_yolo54_improvement_r3.py`; output:
`docs/review/generated/d1_yolo54_improvement_r3_analysis.json`.

## 0. Name and predecessors

The Owner's brief calls this package **"YOLO54 Improvement R2 — Source & Evaluation Readiness"**.
The name `yolo54_improvement_r2` is already used on this branch by the single-change trainer
successor. That successor has independent QA PASS
(`docs/review/d1_yolo54_improvement_r2_independent_qa_record.md`) and is committed as `b901255`.
Following the append-only rule, the readiness package is therefore the successor **R3**. R1 and R2
are not edited.

| Predecessor | Kept | Superseded by R3 |
| --- | --- | --- |
| `d1_improvement_experiments_r1_contract.md` (`4b144ee1…`, Owner proposal) | Track A IDs A0–A3, the data rules, the promotion rule | A0, A0b, A2 and A3 are made concrete here |
| `yolo54_improvement_r2` (trainer, QA PASS) | the guarded A3 ablation `A3_schedule_40e_cos` (`epochs 40`, `cos_lr True`) | the A3 **success criterion**: §5 replaces R2's non-inferiority wording with the Owner's |

## 1. Absolute boundaries

The package does none of the following:

- train, run smoke or inference, or load a model;
- use Colab, write to Drive, or touch the running Cascade B0 runtime, notebook or artifacts;
- upload, commit or push.

It reads none of the following:

- validation pixels;
- the sealed test. No path with a `test` component is ever opened or listed, and
  `sealed_test_accessed=false` throughout.

All inputs are read-only. The evidence lives in the main checkout, where the D1-VRE-R2 artifacts
are uncommitted. The package writes only to this worktree:

- the analysis JSON;
- the manifest;
- these documents.

## 2. Evidence binding

`yolo54_improvement_r3.PINNED` holds the SHA-256 of every evidence authority. Every pinned file is
checked before analysis and again before the write. The main ones:

| Evidence | SHA-256 |
| --- | --- |
| D1-VRE-R2 report `eval_val_vrl_r3_vre_r2.json` | `559c6c6a…7c87` |
| D1-VRE-R2 predictions `predictions_conf0001.csv` (1,999 rows) | `87884c53…c893` |
| D1-VRE-R2 module / contract / source QA / result report / result QA | `2a0823fa…` / `751d78fe…` / `1530942a…` / `96255be8…` / `95db91cb…` |
| Pilot `best.pt` / `run_contract.json` / `args.yaml` | `5d5815a9…` / `9f8fc94c…` / `a457c6d5…` |
| YOLO11s COCO pretrained | `85a76fe8…` |
| R3 labels (376 files, 624 boxes) roster; VRL-R3 manifest; owner acceptance | `dc72ebd9…`; `87dd0fd9…`; `4d948285…` |
| WP36-R1 split frames (validation group mapping) | `8e197d9c…` |
| M1 export manifest (pilot training data); WP35 lineage | `8a8df5f2…`; `e802fc26…` |
| Class map; run registry; D-05 owner decision | `7cda296a…`; `ba5ab04f…`; `c81f37ed…` |
| EA-R1 evidence report / QA; improvement experiments R1 contract | `981f3c09…` / `273c6356…`; `4b144ee1…` |
| Shared `metrics.py` / `contract.py` / `cli.py` | `d24570f8…` / `901e7e37…` / `3e0c13b3…` |

The input guard refuses any of the following:

- an absolute path or one containing `..`;
- any path component containing `test`;
- a symlink anywhere in the chain;
- a hardlinked or non-regular file;
- a resolved path outside the root;
- an unexpected entry in a label directory.

Parsing is strict:

- **R3 labels.** Exactly 376 files with roster hash `dc72ebd9…` and 624 boxes.
- **Group mapping.** Every frame must be a WP36-R1 `val` frame.
- **Prediction CSV:**
  - exact header and exactly 1,999 rows;
  - integer rank and class, with ranks contiguous and scores descending;
  - finite values only, with conf in [0.001, 1];
  - no image may reach `max_det`.
- **Report flags.** These must be JSON `false`, not `0`.

**Compatibility gate.** Before any analysis, the shared `m1.metrics` matcher must reproduce the
D1-VRE-R2 primary result exactly, and the package refuses otherwise. The values checked are:

- the fixed point at conf 0.20: TP 547, FP 150, recall 0.8766, FP/image 0.3989, precision 0.7848,
  and every per-class hit count;
- the 1000-round group-bootstrap CI;
- the D-05 Q4 grid selection (0.20).

The faster paired bootstrap used by A0b must also reproduce `metrics.group_bootstrap` at 0.20
exactly.

## 3. A0 — post-processing NMS

**Finding (verified current evidence).** The D1-VRE-R2 candidates come from `model.predict` with:

- `conf=0.001`;
- class-wise NMS at IoU 0.70 (agnostic off);
- `max_det=300`.

They are **post-NMS** outputs. Boxes that class-wise NMS suppressed are absent. So neither of these
can be reconstructed exactly from the CSV:

- agnostic NMS;
- a class-wise IoU grid {0.5, 0.6, 0.7}.

Status: **`A0_REQUIRES_VALIDATION_ONLY_REINFERENCE`**, with `agnostic_nms_verified=false` and
`nms_grid_evaluated=false`. A0 has **not** been run.

**Re-inference contract** (proposal; it cannot run without a written Owner authorization record and
a source QA of its own successor module):

- the pinned pilot `best.pt` on the 376 R3 validation frames only;
- local MPS, 1280 px, batch 1, D1-VRE-R2 roster checks, and the NMS time limit lifted as in
  D1-VRE-R2;
- the raw head output captured **before** NMS, through a wrapped `non_max_suppression` that records
  its input, at `conf ≥ 0.001`;
- R10 and D1-VRE-R2 reproduced first, at class-wise IoU 0.70, from the captured candidates.

From the captured candidates, the following are computed offline:

- agnostic NMS at IoU {0.5, 0.6, 0.7};
- class-wise IoU {0.5, 0.6};
- each with the per-class recall guard of the Owner proposal.

The criterion is that FP/image falls by ≥ 0.10, recall stays ≥ 0.85, and no gated class (class 46
included) drops below its reference.

The outputs, written append-only under `results/experiments/<pilot>/d1_yolo54_a0_r1/`, are the
candidate table and its report. The package has no training, no threshold lock, and no sealed test.

## 4. A0b — class-wise confidence (diagnostic)

**Exactness.** Class-wise NMS keeps or drops a box based only on higher-scoring boxes of the same
class. No image reaches `max_det`: the maximum is 29 candidates per image, which is checked. So
applying a per-class threshold to the saved candidates equals re-running inference with that
threshold. A0b therefore needs no inference.

**Pre-registered search space** (fixed in code before any class-wise result was seen):

- only the focus classes 7, 32, 41 and 46 (validation support 111, 29, 26 and 104) may be lowered;
- each may go to {0.05, 0.10, 0.15}, one class at a time;
- one combined probe sets all four to 0.10;
- every other class stays at 0.20;
- that gives 13 configurations, plus the global grid 0.05–0.95.

**Reported for every configuration, beside the global 0.20 baseline:**

- overall recall, FP/image, precision, TP and FP;
- recall, hits and support of classes 7, 32, 41 and 46;
- every gated class (support ≥ 20) against its D-05 reference;
- the absolute 95 % CI and the **paired** group-bootstrap 95 % CI of the difference from the
  baseline (1000 rounds, seed 20261018, D-02 group resampling, identical draws for both arms);
- screening flags.

**Status: always `DIAGNOSTIC_PENDING_OWNER_D05_Q4_INTERPRETATION`.**

- `official_threshold=null`, `selected_config=null`, `gate_pass_claimed=false` and
  `threshold_lock_written=false`.
- No configuration is selected, and point estimates are not a selection rule.
- D-05 Q4 does not say whether thresholds may be class-wise. That reading is the Owner's.

**Overfit and uncertainty.** Every configuration is scored on the same 376 frames it would be chosen
on. The bootstrap has only **9 D-02 groups**. Where a class's validation boxes sit in very few
groups, its paired CI is degenerate: for example, class 32 gives [0.138, 0.138]. Such a CI shows
there is too little group variation to estimate uncertainty. It is not precision.

## 5. A2 and A3 — frozen run specifications (not authorized)

Both runs change exactly one thing from the pilot. The pilot is:

- YOLO11s, 54 classes, pretrained `85a76fe8…`;
- the M1 export `8a8df5f2…`: WP36-R1 train stems `6ac76750…` (1,912 frames, raw label hash
  `d907fb9f…`) plus 1,800 WP35 train-only images (lineage `e802fc26…`);
- 1280 px, batch 4, 100 epochs, patience 0, seed 20261018 first, workers 4, fraction 1.0,
  `fliplr=0`, deterministic, `optimizer=auto` (AdamW, lr0 0.000172 in `args.yaml`).

Validation is scoring only, on the R3 labels (376 images, 624 GT). Validation is never used to
train.

| | A2 — repeat factor 7/32/41 | A3 — schedule |
| --- | --- | --- |
| Single change | Every train image whose label holds class 7, 32 or 41 is listed twice in the train list; no new pixels | `epochs 40`, `cos_lr True`; no repeat factor |
| Data delta (computed, train only) | 975 of 3,712 train images repeated (339 raw frames, 636 WP35); 4,687 list entries; roster `0ce6afdc84ff…69aa3`; train boxes 7: 83 raw + 145 WP35, 32: 86 + 52, 41: 171 + 439 | none |
| Exact train args | pilot args plus `data = <A2 train list>` | pilot args with `epochs 40`, `cos_lr True` |
| Success on R3 | Recall of classes 7, 32 and 41 each up by ≥ 0.05; FP/image up by ≤ 0.03; overall recall ≥ 0.85; paired CIs reported | mAP50-95 not below the pilot reference 0.6261; FP/image at the highest grid confidence whose recall reaches the pilot's 0.8766, compared with the pilot's 0.3989; overall recall ≥ 0.85; paired CIs reported |
| Executable path | **Not yet.** The R2 trainer forbids changing `data`. A2 needs a trainer and data-delta successor that writes the train list, verifies the roster `0ce6afdc…`, and binds it into the recovery binding (proposal) | `python -m m1.yolo54_improvement_r2 train A3_schedule_40e_cos …` (QA-passed source) |

**Common to both runs:**

- **Label authority.** The D1-VRL-R3 owner acceptance `4d948285…` (validation). The M1 export
  manifest is the train-label authority.
- **Checkpoint and resume.** Per-epoch mirror and verified resume through `m1.resumable_train` and
  `checkpoint_store`, into the run's own Drive folder.
- **Logs.**
  - `DB_logger.db` (SQLite);
  - `colab_train.log` (text);
  - `colab_execution.json`;
  - `execution_attempts.jsonl`.
- **Run contract.** `run_contract.json`.
- **Result archive.** `<run>_result.tar.gz` plus `.manifest.json`, with the same names as the pilot
  runner R5.
- **Evaluation.** Through **one** evaluator: a D1-VRE-R2 successor that accepts registered ablation
  weights. It is not built yet; the shared evaluators are Codex-held.
- **Flags.** `sealed_test_accessed=false` and `training_authorized=false`.
- **Status.** `WAITING_FOR_L4_AND_OWNER_AUTHORIZATION`.

A2 and A3 are not started. No second Colab account is used, and Cascade B0's GPU is not taken.

The A2 rule repeats WP35 images as well as raw frames. If the Owner prefers raw frames only, the
roster changes (339 raw frames), and the change must be decided before A2 is frozen for running.

## 6. A1 — hard-negative mining

Status: **`A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`**, always, in this
package.

- The train split may contain unlabelled real signs, so a prediction that matches no ground truth is
  never treated as background.
- No training data is written.
- A1 can only follow a QA-passed human train-label-completeness review package. R3 defines none.

## 7. Output, manifest and determinism

- **The analysis is written once:**
  - as canonical JSON (sorted keys, compact separators, no NaN or Inf, finite-checked);
  - with `O_CREAT | O_EXCL | O_NOFOLLOW`;
  - after every pin is re-verified; a change between preflight and write refuses.
- **Determinism.** A rebuild from the same evidence is byte-identical, which the author checked.
- **Manifest.** `docs/review/generated/d1_yolo54_improvement_r3_manifest.json` pins:
  - the module, tests, contract, implementation record, QA brief and analysis JSON;
  - every evidence pin;
  - the schema version.

  It never pins a QA record.

## 8. Promotion

The package becomes `YOLO54_IMPROVEMENT_R3_SOURCE_READY` only after an independent QA PASS. Even
then, the following still need their own explicit Owner authorization:

- training A2 or A3;
- running the A0 re-inference;
- opening the sealed test;
- uploading, committing or pushing.
