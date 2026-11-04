# D1 YOLO54 improvement R3 — implementation record (source and evaluation readiness)

Date: 2026-10-23 (`Asia/Ho_Chi_Minh`) · Status: `YOLO54_IMPROVEMENT_R3_AWAITING_INDEPENDENT_QA`
Author: Claude Code. Worktree branch `claude/centercam-yolo54-r1`, on top of `b901255`.
Uncommitted. Contract: `docs/review/d1_yolo54_improvement_r3_contract.md`.

This package is the Owner's "YOLO54 Improvement R2 — Source & Evaluation Readiness". It is named R3
because `yolo54_improvement_r2` is already the QA-passed trainer successor (contract §0).

## 1. Files

New files; none is edited:

- `detector/m1/yolo54_improvement_r3.py`
- `detector/tests/test_yolo54_improvement_r3.py`
- `docs/review/d1_yolo54_improvement_r3_contract.md`
- this record
- `docs/review/d1_yolo54_improvement_r3_qa_brief.md`
- `docs/review/generated/d1_yolo54_improvement_r3_analysis.json`
- `docs/review/generated/d1_yolo54_improvement_r3_manifest.json`

Not touched:

- the R1 and R2 modules and records;
- `PROJECT_MEMORY.md` and `docs/product_roadmap.md`;
- the root `pyproject.toml` and `uv.lock`;
- every Codex-held file;
- the main checkout, which was only read through the evidence root, with no write, stash, reset or
  cleanup;
- Colab, Drive and the Cascade B0 runtime.

## 2. Claims by evidence class

### VERIFIED_CURRENT_EVIDENCE

Reproduced by this package from pinned artifacts.

- **Matcher compatibility with D1-VRE-R2.** The shared `m1.metrics` matcher, given the pinned
  predictions and R3 labels, reproduces D1-VRE-R2 exactly. The package refuses otherwise. The
  values reproduced are:
  - TP 547, FP 150, recall 0.8766, FP/image 0.3989, precision 0.7848;
  - every per-class hit count;
  - the 1000-round group-bootstrap CI (recall 0.814–0.951, FP/image 0.145–0.816);
  - the D-05 Q4 grid selection of 0.20.
- **Paired bootstrap.** The paired bootstrap used for A0b reproduces `metrics.group_bootstrap`
  exactly at 0.20.
- **Candidate stage.** The D1-VRE-R2 candidates are **post class-wise-NMS** outputs: `conf 0.001`,
  IoU 0.70, `max_det 300` (`cli.iter_image_predictions`). There are at most 29 candidates per image,
  and 9 D-02 validation groups.
- **A0b results** (offline, exact for class-wise thresholds; contract §4). At conf 0.20 the baseline
  is recall 0.8766 and FP/image 0.3989.

  | Configuration | Recall | FP/img | ΔFP/img (paired 95 % CI) | Class 7 | Class 32 | Class 41 | Class 46 |
  | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
  | Global 0.20 (baseline) | 0.877 | 0.399 | — | 0.595 | 0.621 | 0.462 | 0.529 |
  | Global 0.25 | 0.838 | 0.356 | −0.043 (−0.066, −0.023) | 0.541 | 0.552 | 0.462 | 0.490 |
  | Global 0.30 | 0.806 | 0.317 | — | — | — | — | — |
  | Class 7 at 0.05 | 0.897 | 0.412 | +0.013 (0.000, 0.022) | **0.703** | 0.621 | 0.462 | 0.529 |
  | Class 32 at 0.10 | 0.880 | 0.407 | +0.008 (0.000, 0.017) | 0.595 | **0.724** | 0.462 | 0.529 |
  | Class 32 at 0.15 | 0.878 | 0.399 | 0.000 | 0.595 | 0.655 | 0.462 | 0.529 |
  | Class 41 at 0.05 | 0.878 | 0.402 | +0.003 (0.000, 0.011) | 0.595 | 0.621 | 0.538 | 0.529 |
  | Class 46 at 0.05 | 0.881 | 0.420 | +0.021 (0.000, 0.049) | 0.595 | 0.621 | 0.462 | 0.625 |
  | All four at 0.10 | 0.899 | 0.426 | +0.027 (0.007, 0.040) | 0.676 | 0.724 | 0.500 | 0.587 |

  The full 13 class-wise configurations and the global grid are in the analysis JSON. Readings,
  **diagnostic only**:
  - No configuration brings classes 7, 32 and 41 all to their 0.70 reference at once. Class 41
    reaches at most 0.538.
  - Lowering any threshold can only raise FP/image, so no class-wise configuration fixes the FP
    failure (FP/image stays ≥ 0.399).
  - A single global threshold first reaches FP/image ≤ 0.30 at 0.35, where recall is 0.776, below
    0.85.
  - Post-processing alone therefore does not close the D-05 gap.
- **A2 data delta** (train only, computed). Labels are verified against the pilot M1 export
  manifest (`8a8df5f2…`): raw train stems `6ac76750…`, raw labels `d907fb9f…`, and 1,800 WP35
  labels against their lineage sources. Results:
  - 975 of 3,712 train images hold class 7, 32 or 41 (339 raw, 636 WP35);
  - 4,687 train-list entries;
  - repeat roster `0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3`.

### IMPLEMENTED_NOT_EXECUTED

- **The A2/A3 run specifications** (`run_specs`): pilot arguments plus one change,
  `training_authorized=false`, status `WAITING_FOR_L4_AND_OWNER_AUTHORIZATION`. Not run.
- **The A3 trainer path** `m1.yolo54_improvement_r2 train A3_schedule_40e_cos` exists and passed QA.
  Not run.

### UNMEASURED

- **A0 agnostic NMS and the class-wise NMS IoU grid.** These need pre-NMS candidates, which do not
  exist. Status `A0_REQUIRES_VALIDATION_ONLY_REINFERENCE`.
- **Any A2 or A3 effect.** No training has run.
- **The uncertainty of class-wise effects where a class's validation boxes sit in very few
  groups.** For example, class 32's paired CI is the degenerate [0.138, 0.138]: the bootstrap has
  no group variation for that class.

### PROPOSAL

- The A0 validation-only re-inference contract (contract §3).
- An A2 trainer and data-delta successor that writes and binds the repeat train list. The R2
  trainer forbids changing `data`.
- The evaluator successor that scores registered ablation weights on R3 through the D1-VRE-R2
  protocol.

### BLOCKED

- **A1:** `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`.

### REQUIRES_OWNER_DECISION

1. **D-05 Q4.** May confidence thresholds be class-wise? Until then, every A0b result stays
   `DIAGNOSTIC_PENDING_OWNER_D05_Q4_INTERPRETATION`.
2. **Next run.** A2 or A3 first when L4 is free?
3. **A0 re-inference.** Authorize the validation-only re-inference (MPS, about 1 h)?
4. **A2 roster.** Repeat WP35 images (975 images) or raw frames only (339)?
5. **Commit and push** of this package.

## 3. Author verification

Commands run in the worktree.

| Check | Result |
| --- | --- |
| `uv run ruff check` and `ruff format --check` on the two new Python files | clean |
| `CPV301_EVIDENCE_ROOT=<main checkout> uv run pytest -o addopts="" -q tests/test_yolo54_improvement_r3.py` (from `detector/`) | **45 passed**, including the real-evidence reproduction test |
| `cd detector && uv run pytest -q -o addopts=""` | 317 passed, 1 skipped, **16 failed**. Every failure is a pre-existing environment gap in this worktree, where git-ignored data is absent: `data/processed/m1_yolo/data.yaml`, the R4 integration labels and the classifier crops. The failing tests import no R3 code. |
| `uv lock --check` (`detector/` and root) | both resolve without change |
| `git diff --check`, plus a trailing-whitespace scan of the untracked files | clean |
| `graft build` and `graft check` | OK |
| `python -m m1.yolo54_improvement_r3 build --evidence-root <main checkout>` | wrote the analysis JSON. An independent `analyse` rebuild is byte-identical. |
| Root gate `uv run ruff check src tests && uv run pytest -q` (worktree root) | ruff: all checks passed. pytest: 768 failed, 1149 passed, 22 skipped, 7 xfailed (15 min 37 s). Those failures come from this worktree, where git-ignored raw/processed data is absent, plus the known root dependency drift handled by ROOT-ENV-R1 (Codex). None of them is attributable to R3, and the root suite was not run before the change for a direct comparison. The R3 package adds no root `src` or `tests` file. |

## 4. Proposed memory and roadmap text (not applied)

`PROJECT_MEMORY.md` and `docs/product_roadmap.md` are Codex-held during Cascade B0, so this text is
proposed only:

> YOLO54 improvement R3 (source/evaluation readiness, Claude worktree): A0 needs a validation-only
> re-inference (saved D1-VRE-R2 candidates are post-NMS). A0b class-wise thresholds are diagnostic
> only: no configuration lifts classes 7/32/41 to 0.70 together, and none lowers FP/image below
> 0.399. A2 (repeat roster `0ce6afdc…`) and A3 are frozen, `training_authorized=false`. A1 is
> blocked. Pending: Owner reading of D-05 Q4, A2 vs A3 priority, A0 re-inference authorization,
> independent QA.
