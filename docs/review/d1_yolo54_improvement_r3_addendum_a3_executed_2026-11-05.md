# D1 YOLO54 improvement R3 — addendum 1: A3 already executed

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Status: `R3_A3_ROW_CLOSED_EXECUTED_VIA_D1_A3_R2_CRITERIA_NOT_MET`
Boundary: documentation only. No training, inference, threshold change, D-05 change or app change.
`sealed_test_accessed=false`, `training_authorized=false`.
Author: Claude Code (Opus 5.5), coordinating session.

This addendum is append-only. It does not edit
`docs/review/d1_yolo54_improvement_r3_contract.md`
(SHA-256 `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f`). It records what
happened to the contract's §5 A3 row after the contract was written, so that no reader treats A3
as a pending run.

## 1. What happened (verified artifacts)

| Date | Event | Evidence |
| --- | --- | --- |
| 2026-10-23 | R3 contract freezes A3 as `A3_schedule_40e_cos` (pilot args + `epochs 40`, `cos_lr True`), status `WAITING_FOR_L4_AND_OWNER_AUTHORIZATION`, executable through `m1.yolo54_improvement_r2` | contract §5, lines 170–213 |
| 2026-10-24 | Owner approves A3 separately: YOLO11s 54 classes, 40 epochs, `cos_lr=True`, seed 20261018, L4 training, no sealed test | `d1_a3_r1_owner_decision_record.md` (`fa5c61ba…48ee9b2`) |
| 2026-10-24 | Run contract D1-A3-R1, then launcher repair D1-A3-R2 (same experiment, new launcher `detector/colab/run_d1_colab_a3_r2.py`) | `d1_a3_r1_run_contract.md` (`ed6754f3…8cd71c33`), `d1_a3_r2_run_contract.md` (`2cf71027…4115a47e`) |
| 2026-10-25 | 40-epoch run `SUCCEEDED` (recovery pointer `epoch-0040`); common-validation result with independent result QA PASS | `d1_a3_r2_common_validation_report_r1.md` (`2c893e02…4e5494`), QA record (`624e3994…916058`), result JSON `results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/comparison_a3_r1.json` (`98b8947e…c2c73`) |

So the R3 A3 row was not skipped and is not a near-duplicate waiting to run: it was **executed
through the Owner-approved D1-A3 track** rather than through `m1.yolo54_improvement_r2`.

### Differences from the R3 §5 wording (verified, recorded, not judged material)

- **Launcher.** `run_d1_colab_a3_r2.py` + `m1/resumable_train_a3_r1.py`, not
  `python -m m1.yolo54_improvement_r2 train A3_schedule_40e_cos`.
- **Patience.** The D1-A3 contracts set `patience 30`; R3 §5 inherits the pilot's `patience 0`.
  The run completed all 40 epochs, and the D1-A3-R1 contract rejects an early-stopped result, so
  early stopping did not cut the run short.
- **Evaluator.** R3 §5 names a not-yet-built D1-VRE-R2 successor. A3 was scored by the append-only
  common evaluator `evaluate_d1_a3_r2_common_r1.py` (Ultralytics IoU matching/AP plus the m1 D-05
  operating points), on the same 376-frame / 624-box R3 roster.

## 2. A3 against the R3 §5 success criteria (descriptive, single seed)

The values come from the QA-passed result JSON above. Pilot values on the same common path are
quoted from the same file.

| R3 §5 criterion | A3 measured | Pilot | Met? |
| --- | --- | --- | --- |
| mAP50-95 not below the pilot reference 0.6261 | 0.5633 | 0.6089 on the common path; 0.6261 on the D1-VRE-R2 path | **No.** A3 is below both references. The two pilot numbers come from different scorers and must stay separately labelled. |
| FP/image at the highest grid confidence whose recall reaches the pilot's 0.8766, versus 0.3989 | The grid is 0.05–0.95. A3's highest detection recall on the grid is 0.8670 at conf 0.05 | 0.8766 at conf 0.20, FP/image 0.3989 | **No.** No grid point reaches 0.8766, so the comparison point does not exist. At A3's own recall ≥ 0.85 point (conf 0.05), FP/image is 0.5452. |
| Overall recall ≥ 0.85 | 0.8670 at conf 0.05 | 0.8766 at conf 0.20 | Yes |
| Paired CIs reported | Only per-model bootstrap at conf 0.20 (A3 recall 0.674–0.931, FP/image 0.114–0.401); no paired A3 − pilot difference CI | — | **Not reported** |

Outcome: **A3 does not meet the R3 §5 success criterion.** This agrees with the disposition of
the D1-A3-R2 report: keep the 100-epoch pilot, and preserve A3 and its artifacts for review. It is
not a causal test of `cos_lr`, because epochs and schedule both differ.

**Observation on the contract text (not a correction of results).** R3 §5 states that "both runs
change exactly one thing from the pilot". The A3 row changes two arguments (`epochs` 100→40 and
`cos_lr` False→True). Any later schedule ablation should name a single change.

## 3. Effect on R3

- **§5 A3 row.** Closed. Status is `EXECUTED_VIA_D1_A3_R2_CRITERIA_NOT_MET`, replacing
  `WAITING_FOR_L4_AND_OWNER_AUTHORIZATION` for A3 only. Do **not** run
  `m1.yolo54_improvement_r2 train A3_schedule_40e_cos` as a new experiment. Re-running the same
  configuration would only add a second seed, and that needs its own Owner decision and contract.
- **§5 A2 row.** Unchanged:
  - still not authorized;
  - still needs a trainer and data-delta successor;
  - the choice between repeating all 975 images or only the 339 raw frames is still open.
- **§8 Promotion.** "Training A2 or A3" now concerns A2 only.
- **Unchanged.** A0, A0b, A1, the D-05 gates, the sealed-test boundary and every pinned hash.

## 4. Classification of claims

- **Verified artifact.**
  - the dates, hashes and run status in §1;
  - every metric in §2, read from the QA-passed JSON.
- **Verified current behavior.** The live app on `yolo11n-dual-track-r1` does not state
  "A2/A3 chờ GPU L4". That wording exists only as uncommitted edits in the worktree
  `.claude/worktrees/centercam-yolo54-r1`, which is not the app source of record.
- **Proposal.** That a further schedule ablation, if wanted, should change one argument only.
- **Unknown.** Whether a paired A3 − pilot CI would exclude 0. It was not computed.
