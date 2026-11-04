# D1 YOLO54 improvement R2 — independent QA record

Reviewer: Claude Code, independent QA session (reviewed R1, did not author R1 or R2) · Date:
2026-10-23 · Worktree `.claude/worktrees/centercam-yolo54-r1`, branch `claude/centercam-yolo54-r1`,
HEAD `b661b8c`, with the R2 files uncommitted. Boundary respected: source read-only, no `train`,
no Ultralytics run, no GPU, no sealed test, no commit or push.

## 1. Hashes

Package under review (all three match the requested values):

| File | SHA-256 | Match |
| --- | --- | --- |
| `detector/m1/yolo54_improvement_r2.py` | `bab53b5ea9bdcb5c43f6afdfeed26de9cb548eb544ebeddfd9aaa16c0c92480f` | yes |
| `detector/tests/test_yolo54_improvement_r2.py` | `0d36296c063f9b3e0484c309026e049a73f3ef67b0b6fe7a1a241598f58767a7` | yes |
| `docs/review/d1_yolo54_improvement_r2_contract.md` | `eff3398f4411d2185f43ffc201424105b395dc3c1f4143155011594f3dfce074` | yes |

R1 files are unchanged from `b661b8c`: `git diff --stat b661b8c` is empty for each of them, and the
hashes equal the R1 QA values.

| File | SHA-256 |
| --- | --- |
| `detector/m1/yolo54_improvement_r1.py` | `4aa81004d531ea611c47d214f33face1a0e6f615f54d94aa0e5d55ab17482a12` |
| `detector/tests/test_yolo54_improvement_r1.py` | `bb6b41eadeea9df97f3a65d96bd9d737c6169cd2ded727c2d918273e53149604` |
| `docs/review/d1_yolo54_improvement_r1_contract.md` | `ba6f0f2e803e2dabc280197180b95137511e671d0e74cda9cfa1762226ebbdfd` |
| `docs/review/d1_yolo54_improvement_r1_independent_qa_record.md` | `72222efba7aeed6c1e60b2467dedfb0de9fe1a5cd508ac35c4ceabbe54c85371` |

`resumable_train.py`, `checkpoint_store.py` and `contract.py` are also unchanged against
`b661b8c`.

## 2. Commands and results

| Command (from `detector/` unless noted) | Result |
| --- | --- |
| `uv run ruff check m1/yolo54_improvement_r2.py tests/test_yolo54_improvement_r2.py` | `All checks passed!`, exit 0 |
| `uv run ruff format --check` (same two files) | `2 files already formatted`, exit 0 |
| `uv run pytest -o addopts="" -q tests/test_yolo54_improvement_r2.py tests/test_yolo54_improvement_r1.py tests/test_resumable_train.py tests/test_checkpoint_store.py` | `74 passed in 0.68s` (matches the author's evidence) |
| `uv run python -m m1.yolo54_improvement_r2 list` | exit 0; A4 now includes `warmup_bias_lr: 0.0`; A3, A5 and A6 are as in R1 |
| `uv run python -m m1.yolo54_improvement_r2 plan A3_schedule_40e_cos` | exit 0; full `train_args` of 17 keys incl. `workers 4`, `fraction 1.0`, `plots false`, `epochs 40`, `cos_lr true`, `fliplr 0.0`; `runtime_placeholders [data, name, device]`; `success_kind screening`, `screening_conf 0.2`; tag `…_r2` |
| `graft check .` (worktree root) | `graph check: OK` |
| QA reproduction script (scratchpad `qa_repro_r2.py`, `PYTHONPATH=.`) | results Q1–Q5 below |

QA reproductions use the real `CheckpointStore` with a real `save`, not a hand-written pointer.

- **Q1, store refusals.** After `save(epoch=1)` under the R2 A5 binding, `load_latest` accepts R2
  A5. It refuses R2 A6, R1 A5 and R2 A5 with `device="cpu"`, each with "checkpoint binding differs
  from requested training configuration". After a real save under the R1 A5 binding, R2 A5 is
  refused. R1 and R2 use the **same** Drive folder for a given key (`same_drive_folder_r1_r2:
  true`); only the binding separates them.
- **Q2, pinned-runtime types.** `fraction=1` (int, equal to the pilot) is accepted.
  `workers=True`, `fraction=True` and `seed="20261018"` are refused. After a refused call
  (`workers=8`), `args.epochs` and `args.tag` are unchanged (100, `""`): the guards run before
  any mutation.
- **Q3, nesting.** A second R2 `execute` inside a running R2 `execute` is refused, and the patch
  and `_ACTIVE` are restored. R2 does **not** detect a running **R1** `execute` (see I1).
- **Q4, `plan` versus the real trainer (A4).** No key is missing or extra. Values differ only for
  `data`, `name` and `project`.
- **Q5, LR lambdas** (Ultralytics 8.4.172 `engine/trainer.py:268–274`, `one_cycle`). At lambda
  index 20 the linear schedule over 100 epochs gives 0.802 and the cosine schedule over 40 gives
  0.505. At index 19, the lambda used while training the 20th epoch, they give 0.812 and 0.544.
  Both readings support "≈ 0.8 vs ≈ 0.5".

## 3. R1 finding closure

| R1 finding | Status in R2 | Evidence |
| --- | --- | --- |
| M1 `fraction`/`workers`/`device` unguarded | **Resolved** | `PINNED_RUNTIME` refuses non-pilot `imgsz`/`batch`/`seed`/`workers`/`fraction` before any mutation (Q2); CLI test `--fraction 0.25` → exit 1; `device` is in the binding and a device change is refused on resume (Q1). |
| M2 A3 mis-grounded | **Resolved** | Hypothesis restated as an LR-near-peak mechanism; non-inferiority criterion; "cost result, not an accuracy gain" note. Margins 0.616 = 0.626 − 0.01 and 0.419 = 0.399 + 0.02 match the code text. LR numbers verified (Q5). |
| L1 A4 implicit `warmup_bias_lr`/beta1 | **Resolved** | `warmup_bias_lr` is in the optimizer category, pinned at 0.0, and tested. The beta1 change is disclosed. Wording residue: L3. |
| L2 `plan` not exact | **Resolved, with a residue** | Built from the real `train_arguments`; the key set equals the real one (Q4). `project` is runtime-bound but not listed as a placeholder (L1 below). |
| L3 evidence wording | **Resolved** | A5 says "minority (19 of 45)"; A6 labels the R10 basis and says it has not been recounted on R3. |
| L4 noise margin / conf point | **Resolved, with a residue** | Every criterion is labelled screening at conf 0.20; a CI promotion rule is added. The evaluator capability it needs is not stated (L2 below). |
| L5 test gaps | **Resolved** | New tests for workers/fraction (incl. CLI), store refusal, R1≠R2 binding, nested refusal, and the wider import check. The store test is weaker than claimed (L4 below); QA's real-save run (Q1) confirms the behaviour. |
| L6 write scope | **Resolved** | §2 names both the Drive folder and the new `results/experiments/<run>` directory. |
| Info, nested patch | **Resolved for R2-in-R2** | Q3; cross-package nesting remains (I1). |

## 4. Findings

Critical: none. High: none. Medium: none.

### Low

- **L1 — `project` is runtime-bound but not a declared placeholder.** `plan` passes the local
  `contract.RESULTS_DIR`, so `train_args.project` shows the reviewer's checkout path
  (`/Users/…/centercam-yolo54-r1/results/experiments`). On Colab it would be
  `/content/Traffic_Sign_Detector/results/experiments`. Contract §1 L2 says only `data`, `name`
  and `device` are bound at train time.
  *Reproduction:* `plan A3_schedule_40e_cos`, then Q4 (`value_diffs` includes `project`).
  *Fix:* add `project` to `runtime_placeholders`, or substitute a placeholder.
- **L2 — The promotion CI rule needs an evaluator capability that does not exist yet.** §4 asks
  for a "group-bootstrap 95 % CI of the delta against the pilot, computed by the same evaluator".
  For A3 that includes ΔmAP50-95, and for A5 ΔAP-small. D1-VRE-R2 bootstraps only recall and
  FP/image, per model and unpaired (`d1_vre_r2_contract.md:91`, `d1_vre_r2_result_report.md:54,
  88`). The rule therefore requires a **paired-delta** bootstrap, including mAP-type metrics, in
  the evaluator successor, and the contract does not list that as a successor requirement.
  *Fix:* state it as an explicit requirement of the evaluator successor (paired by D-02 group,
  same seed, 1000 rounds).
- **L3 — Source attribution for beta1.** The A4 hypothesis says "AdamW with lr0 0.000172 and beta1
  0.9 (args.yaml)", and §3 says "args.yaml gives: `optimizer auto` → AdamW". `args.yaml` records
  `optimizer: AdamW`, `lr0: 0.000172` and `momentum: 0.937`. The 0.9 beta1 and the `auto` input
  come from Ultralytics `trainer.py:1180` and the trainer defaults, not from `args.yaml`.
  *Fix:* cite `trainer.py:1179–1182` for beta1 and `auto`.
- **L4 — The store-refusal test uses a hand-written pointer.**
  `test_checkpoint_store_refuses_to_resume_under_another_ablation` writes `latest.json` with a
  zero manifest hash, and the "accepting" A5 case ends on a missing manifest. It proves the
  binding-hash comparison, not the full save → load path. QA's real-save run (Q1) confirms the
  intended behaviour.
  *Fix (optional):* save a real generation with dummy artifacts, as in Q1.
- **L5 — The "R1 must not be used to train" rule is documentation only.** R1 stays executable and
  writes to the same Drive folder per key. No corruption path was found: a fresh run refuses an
  existing `latest.json`, a cross-package resume is refused (Q1), and pruning only touches
  generations that verify under the caller's own binding. Still, nothing in code stops an R1
  run in an empty folder.
  *Fix (optional):* make R1 `execute` refuse, in an append-only way, or give R2 its own run root.

### Informational

- **I1.** R2's `_ACTIVE` guard is module-local, so an R2 `execute` started inside a running R1
  `execute` would wrap R1's patched functions and stack both overrides. This is unreachable from
  either CLI, which is one process and one command.
- **I2.** The epoch-index convention changes the LR values slightly (0.81/0.54 against 0.80/0.51),
  but the "≈ 0.8 vs ≈ 0.5" statement holds either way.
- **I3.** `plan` still imports `numpy` transitively through `m1.cli`. The test checks
  `ultralytics`, `torch`, `cv2` and `PIL` are absent, and they are.

## 5. Verdict

All R1 findings are resolved, and nothing material is overclaimed. No new Critical, High or
Medium defect was found in the guard order, the CLI path, binding separation from R1, or store
refusal. Counts: 0 Critical, 0 High, 0 Medium, 5 Low, 3 Informational. This verdict authorises
no training, smoke, GPU use or sealed-test access.

Verdict: **PASS**
