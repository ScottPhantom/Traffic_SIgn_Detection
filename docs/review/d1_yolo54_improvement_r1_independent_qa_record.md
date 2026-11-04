# D1 YOLO54 improvement R1 — independent QA record

Reviewer: Claude Code, independent QA session (did not author the package) · Date: 2026-10-23 ·
Worktree `.claude/worktrees/centercam-yolo54-r1`, branch `claude/centercam-yolo54-r1`, HEAD
`d8f7806` (package files untracked). Boundary respected: no `train`, no GPU, no training, no
sealed test, no commit or push, no edit to `src/`, root `tests/` or the main checkout.

## 1. Reviewed files and hashes

Package under review (all three match the requested values):

| File | SHA-256 | Match |
| --- | --- | --- |
| `detector/m1/yolo54_improvement_r1.py` | `4aa81004d531ea611c47d214f33face1a0e6f615f54d94aa0e5d55ab17482a12` | yes |
| `detector/tests/test_yolo54_improvement_r1.py` | `bb6b41eadeea9df97f3a65d96bd9d737c6169cd2ded727c2d918273e53149604` | yes |
| `docs/review/d1_yolo54_improvement_r1_contract.md` | `ba6f0f2e803e2dabc280197180b95137511e671d0e74cda9cfa1762226ebbdfd` | yes |

Wrapped files, unchanged against HEAD `d8f7806` (`git diff --stat` empty):

| File | SHA-256 |
| --- | --- |
| `detector/m1/resumable_train.py` | `0a963d4bc246613402283531b6280836606ac1f5b35b5d215b3959a1354aa6e7` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/m1/contract.py` | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |
| pilot `args.yaml` (read-only, main checkout `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/`) | `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` |

Installed Ultralytics in `detector/.venv`: `8.4.172`.

Graft: `graft check .` reports the new module and test as changed (STALE for those two files).
QA changed no source, so it did not rebuild `graft/`.

## 2. Commands and results

All run from `detector/`.

| Command | Result |
| --- | --- |
| `uv run ruff check m1/yolo54_improvement_r1.py tests/test_yolo54_improvement_r1.py` | `All checks passed!`, exit 0 |
| `uv run pytest -o addopts="" -q tests/test_yolo54_improvement_r1.py` | `24 passed in 0.36s` |
| `uv run python -m m1.yolo54_improvement_r1 list` | exit 0; A3 `{cos_lr: true, epochs: 40}`, A4 `{lr0: 0.01, momentum: 0.937, optimizer: "SGD"}`, A5 `{multi_scale: 0.25}`, A6 `{hsv_v: 0.6}` |
| `uv run python -m m1.yolo54_improvement_r1 plan A5_multi_scale` | exit 0; `changed {multi_scale: 0.25}`; `train_args` batch 4, deterministic true, epochs 100, fliplr 0.0, imgsz 1280, multi_scale 0.25, patience 0, pretrained true, seed 20261018; checkpoint dir `/content/drive/MyDrive/M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1/A5_multi_scale`; `training_started false`, `sealed_test_accessed false` |
| Extra: `uv run pytest -o addopts="" -q tests/test_resumable_train.py tests/test_checkpoint_store.py` | `14 passed in 0.34s` (wrapped trainer still green) |
| Extra: QA reproduction script (scratchpad `qa_repro.py`, run with `PYTHONPATH=.`) | results R1–R5 below |
| Extra: `plan` import/open audit (audit hook on `open`, all four ablations) | no `ultralytics`/`torch`/`cv2`/`PIL`/`yaml` module loaded; no new module during `plan`; only non-source file opened: `/System/Library/CoreServices/SystemVersion.plist` (stdlib `platform`); `numpy` is loaded at import time via `m1.cli` |

QA reproduction outputs:

- **R1, cross-ablation resume against the real `CheckpointStore`.** Saved epoch 1 with the A5
  binding, then `load_latest` with: the same A5 binding → `ACCEPTED`; the A6 binding → `REFUSED:
  checkpoint binding differs from requested training configuration`; the unpatched pilot binding →
  `REFUSED` (same message).
- **R2, CLI arguments `execute` does not guard.** `fraction=0.5`, `workers=0`, `device="cpu"` each
  reach both `train_args` and the binding unchanged (0.5 / 0 / `cpu`); no refusal.
- **R3, patch restoration on `KeyboardInterrupt`** raised inside `resumable_train.execute`: `True`.
- **R4, keys of the real `train_arguments` missing from `plan()["train_args"]`:** `data`,
  `device`, `exist_ok`, `fraction`, `name`, `plots`, `project`, `workers`.
- **R5, A3:** `train_args.epochs 40`, `binding.epochs 40`, `fliplr 0.0`.

## 3. Attack results by question

1. **Single category; protected keys.** Every registered ablation's keys are a subset of one
   whitelisted category, and `validate` refuses forbidden keys, mixed categories, bool or > 0.5
   `multi_scale`, `optimizer=auto`, and epochs outside [1, 100] (tests plus code reading).
   `_apply` re-applies `fliplr=0.0` last in both `train_args` and the binding. `imgsz`, `batch` and
   `seed` are refused by `execute` before training; `data`/`split`/`classes` come only from the
   unchanged `contract.check_contract()`, and the model is pinned by `bind_training_model`. One
   gap: the CLI `--fraction` changes the training subset without refusal (finding M1).
2. **Overrides in `train_args` and the recovery binding.** Yes. Both module-level functions are
   replaced for the duration of `resumable_train.execute`. That function resolves them as module
   globals at lines 109, 148 and 168, so the fresh `run_contract.json`, the `model.train` arguments
   and the checkpoint binding all carry the overrides plus the `ablation` key. A cross-ablation
   resume and a pilot-binding resume are refused by the real store (R1). The checkpoint directory
   must also be the ablation's own folder.
3. **Monkeypatch restoration.** `try/finally` restores both functions on success, on `Exception`
   (test) and on `KeyboardInterrupt` (R3). The patch is process-global and not reentrant, which is
   acceptable for one sequential Colab process (I2).
4. **"Before" values.** Pilot `args.yaml`: `optimizer: AdamW`, `lr0: 0.000172`, `hsv_v: 0.4`,
   `multi_scale: 0.0`, `cos_lr: false`, `fliplr: 0.0`, `imgsz 1280`, `batch 4`, `epochs 100`,
   `patience 0`, `seed 20261018`. The contract matches. "auto resolved to AdamW, lr0 0.000172"
   is confirmed by Ultralytics `engine/trainer.py:1179–1181`: `round(0.002*5/(4+54), 6) = 0.000172`,
   written back to `args`. **`multi_scale 0.25` in 8.4.172** is a float fraction
   (`cfg/default.yaml:40`, `CFG_FRACTION_KEYS`), and `models/yolo/detect/train.py:120–128`
   samples `randrange(960, 1632) // 32 * 32`, i.e. 960–1600 px. `True` coerces to 1.0, giving up to
   2560 px. The note is correct.
5. **Hypotheses and criteria.** The numbers trace to `docs/review/d1_vre_r2_result_report.md`
   (624 GT; mAP50-95 0.6261, AP-small 0.2891, FP/image 0.399; class 7 66/111 = 0.595, class 32
   18/29 = 0.621, class 41 12/26 = 0.462; "45 misses, 19 ≤ 17 px"), to
   `d1_ea_r1_hypothesis_correction_r1.md` (R10: 17 of 36 class-7 misses dark/backlit in
   1777–1798) and to the pilot `results.csv` (val mAP50-95 peak 0.58877 at epoch 20, 0.53189 at
   epoch 100). The L4 hour estimates agree with 138 s/epoch. All success criteria use metrics the
   VRE-R2 protocol already reports. Grounding weaknesses: M2, L3, L4.
6. **What is not built.** Stated honestly: §4 says the evaluator successor is not built and why;
   §5.3 says notebook/runner wiring, bundle pins and runtime-digest history are a follow-up. D-05,
   thresholds and the sealed test are declared untouched, and nothing in the module reads them.
   The L4 queue order is stated, and no training is started.
7. **`plan` imports and data.** Confirmed: no Ultralytics or torch, no data or label file opened,
   no new module loaded during `plan` (audit above). The existing subprocess test checks
   `ultralytics` only. `numpy` is imported transitively at module import (I1).

## 4. Findings

Critical: none. High: none.

### Medium

- **M1 — `train --fraction` (and `--workers`, `--device`) bypass the pilot-equivalence guard.**
  The contract lists `fraction` as forbidden and says each run uses "the same export as the
  pilot", but `execute` checks only `imgsz`, `batch`, `seed` and the checkpoint directory. A run
  with `--fraction 0.5` trains on half the data. It is recorded consistently in the binding and the
  run contract, so it is visible, but it is not refused. `workers` can also alter dataloader RNG
  streams under `deterministic=True`.
  *Reproduction:* R2. `imp.execute(ns(..., "A6_photometric_value", fraction=0.5))` with a stubbed
  `resumable_train.execute` produces `train_args["fraction"] == 0.5` and no error.
  *Fix:* refuse `args.fraction != 1.0` in `execute` (and either pin `workers=4` or record it as an
  allowed runtime knob), and add a test.

- **M2 — A3's mechanism is mis-grounded.** The hypothesis says a shorter cosine schedule "avoids
  the late overfit". The evaluated pilot weight is `best.pt` (VRE-R2 contract line 46), and the
  pilot's fitness-best epoch is already epoch 20, the peak. Late overfit therefore does not affect
  the evaluated model. The plausible mechanism is that the LR decays to a low value near the peak
  (at epoch 20 of the linear 100-epoch schedule the LR is still ≈ 0.8 × lr0). The success
  criterion is in effect a non-inferiority-at-40 %-cost test.
  *Reproduction:* parse the pilot `results.csv`: `max(mAP50-95)` and
  `max(0.1·mAP50 + 0.9·mAP50-95)` both fall at epoch 20 (0.58877).
  *Fix:* restate the A3 hypothesis as "cost reduction with non-inferior R3 metrics; cosine decay
  may sharpen the epoch-~20 optimum", so a null result is not misread.

### Low

- **L1 — A4 changes two undisclosed optimizer-category values.** Under `auto`, Ultralytics forces
  `warmup_bias_lr = 0.0` and momentum/beta1 0.9 (`trainer.py:1180–1182`; `args.yaml` shows
  `warmup_bias_lr: 0.0`, but its `momentum: 0.937` is not the effective beta1). Explicit SGD uses
  the defaults `warmup_bias_lr 0.1` (`default.yaml:100`) and momentum 0.937. This stays in one
  category, but the "Change from pilot" column omits it. *Fix:* disclose it, or pin
  `warmup_bias_lr` explicitly.
- **L2 — `plan` is not the "exact settings".** It omits 8 keys that the real
  `train_arguments` emits (R4), and it rebuilds the base by hand, so it could drift from
  `resumable_train`. *Fix:* build `plan.train_args` from `resumable_train.train_arguments` with
  placeholder `bound`/`results_dir`, or reword to "changed and pinned settings".
- **L3 — Evidence wording.** A5 says 11–35 px signs "dominate the class-7/41 misses". For class 7
  that holds for 19 of 45 only (VRE-R2: "the rest are mid-size to large"). A6 cites R10 counts
  (17/36) while success is measured on R3 (45 misses), and the R3 dark/backlit count is not given.
  *Fix:* cite the R3 figures or label the R10 basis explicitly.
- **L4 — Success thresholds have no noise margin.** At one seed, +0.05 recall is ≈ 1.3 boxes for
  class 41 (n = 26) and ≈ 5.6 boxes for class 7 (n = 111). A3's "at recall ≥ 0.85" does not name
  an operating point (conf 0.20 or a tuned one). The hard D-05 references in §5.4 mitigate this.
  *Fix:* require the group-bootstrap interval of the delta to exclude 0, or say these are
  screening criteria; state the conf point.
- **L5 — Test gaps.** The cross-ablation test compares binding dicts only and does not exercise
  `CheckpointStore.load_latest` refusal (QA did, R1). No test covers `fraction`/`workers`. The
  no-import test checks only `ultralytics`.
- **L6 — Write-scope wording.** §1 says the package "writes only to a new Drive run root". The
  wrapped trainer also creates a new run directory under the repository `results/experiments/` and
  writes `run_contract.json` there. It refuses an existing directory, so nothing is overwritten.

### Informational

- **I1.** `plan` loads `numpy` transitively (`m1.cli`). No model code is loaded and no data file
  is opened.
- **I2.** The patch is process-global and not reentrant. Do not call `execute` from threads or
  nested in one process. This is fine for the intended one-run-per-Colab-process use.
- **I3.** On `--resume`, Ultralytics `check_resume` (trainer.py ~1020–1063) restores the checkpoint
  args and ignores most overrides. The binding check keeps that consistent with the ablation.
- **I4.** Graft is STALE for the two new files. Rebuild with `graft build . && graft check .`
  before handing off source changes.

## 5. Verdict

0 Critical and 0 High, so the package passes as a preparation-only successor. M1 should be fixed,
and M2 restated, in an append-only successor before any smoke or long run is authorised. This
verdict authorises no training, smoke, GPU use or sealed-test access.

Verdict: **PASS**
