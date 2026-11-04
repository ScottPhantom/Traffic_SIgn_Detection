# D1 YOLO54 improvement R3 — independent QA brief

Package: `D1-YOLO54-IMPROVEMENT-R3` (the Owner's "YOLO54 Improvement R2 — Source & Evaluation
Readiness"; contract §0 explains the name). Status: `YOLO54_IMPROVEMENT_R3_AWAITING_INDEPENDENT_QA`.
The author session does **not** claim QA PASS.

## Locations

- **Package (worktree, uncommitted).**
  `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/.claude/worktrees/centercam-yolo54-r1`,
  branch `claude/centercam-yolo54-r1`, on top of `b901255`.
- **Evidence root (read-only).** The main checkout
  `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`. It holds the uncommitted D1-VRE-R2
  artifacts, the R3 labels and the pilot export. Do not write there, and do not stash, reset or
  clean it.

## File roster

The package files are pinned in `docs/review/generated/d1_yolo54_improvement_r3_manifest.json`,
and the evidence pins are in `PINNED` within the module. The manifest's own SHA-256 is in the
handoff message. This brief cannot pin itself.

## What QA must check

1. **Evidence binding.**
   - Every `PINNED` hash matches the evidence root.
   - The manifest matches the package files.
   - The analysis JSON `evidence_pins` equal `PINNED`.
   - No QA record is pinned.
2. **Scientific validity.**
   - The A0b exactness argument: class-wise NMS plus no image at `max_det`, so per-class
     thresholding of post-NMS candidates equals re-inference.
   - The fixed search space (4 classes × 3 values, plus 1 combined probe).
   - Overfit and degenerate-CI disclosure.
   - The diagnostic-only status.
   - The record's readings: no configuration lifts classes 7/32/41 to 0.70 together, and FP/image
     never falls below 0.399.
3. **Metric compatibility with D1-VRE-R2.**
   - The `reproduce` gate: the fixed point, per-class hits, bootstrap CI and Q4 selection.
   - The paired bootstrap draws must be identical to `metrics.group_bootstrap`.
   - Matching, IoU 0.5 and the gate references must come from `m1.metrics` and `m1.contract`.
4. **Pre-NMS versus post-NMS.**
   - A0 must return `A0_REQUIRES_VALIDATION_ONLY_REINFERENCE` and never set
     `agnostic_nms_verified` or `nms_grid_evaluated` to true.
   - The re-inference contract must be a proposal only.
5. **No validation leakage.**
   - The A2 roster reads train labels only; check that the verification against the export
     manifest and WP35 lineage is correct.
   - No validation label, crop or prediction feeds training.
   - A1 is blocked.
6. **No sealed-test access.**
   - The guard refuses any `test` path component.
   - No test directory is listed or created.
   - `sealed_test_accessed` is false everywhere.
7. **Path attacks.** The guard must refuse:
   - symlinks anywhere in the chain;
   - hardlinks (`st_nlink`);
   - absolute paths, `..` and resolved escape;
   - unexpected directory entries.
8. **Fail-closed behavior.** Each of these must fail:
   - a changed hash;
   - a roster other than 376/624;
   - a changed group map;
   - a source change between preflight and write;
   - NaN or Inf;
   - a boolean or integer standing in for the other in the schema;
   - a CSV schema error;
   - an image reaching `max_det`.
9. **Determinism.** Rebuild with `analyse(<evidence root>)` and compare
   `canonical(document)` byte for byte with the analysis JSON.
10. **A2/A3 freeze.**
    - Each run changes exactly one thing.
    - `training_authorized=false` and status `WAITING_FOR_L4_AND_OWNER_AUTHORIZATION`.
    - The artifact names match the pilot runner R5.
    - The A3 criterion supersedes R2's non-inferiority wording.
    - A2 has no executable trainer path yet, and that gap is disclosed.
11. **No interaction with Cascade B0.**
    - Nothing touches Colab, Drive or Cascade files.
    - No Codex-held file is edited.
    - No commit or push.

## Suggested commands

```bash
cd /Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/.claude/worktrees/centercam-yolo54-r1/detector
```

```bash
uv run ruff check m1/yolo54_improvement_r3.py tests/test_yolo54_improvement_r3.py
```

```bash
CPV301_EVIDENCE_ROOT=/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector uv run pytest -o addopts="" -q tests/test_yolo54_improvement_r3.py
```

```bash
uv run python -m m1.yolo54_improvement_r3 check --evidence-root /Users/nguyentantai/Desktop/app/Traffic_Sign_Detector
```

## Output expected from QA

Write exactly one file:
`docs/review/d1_yolo54_improvement_r3_independent_qa_record.md` in the worktree. It must:

- pin the hashes it reviewed;
- list findings by severity (Critical, High, Medium, Low);
- contain exactly one line that starts with `Verdict:`. PASS requires 0 Critical and 0 High.

Only after PASS may the status become `YOLO54_IMPROVEMENT_R3_SOURCE_READY`. Even then, no training,
test access, upload, commit or push is allowed without the Owner's authorization.
