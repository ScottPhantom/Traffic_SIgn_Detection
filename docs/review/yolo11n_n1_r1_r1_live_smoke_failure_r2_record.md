# YOLO11n N1 R1-R1 live smoke failure record R2

Date: 2026-10-25 15:28:42 (Asia/Ho_Chi_Minh)  
Status: `FAILED_BEFORE_STATE_CREATION`  
Scope: fresh smoke only, stop after epoch 1; no long training and no sealed-test access.

## Immutable inputs

- Notebook commit: `38c132b046bcc83fa2b69a04cc991f9bea62ac3b`.
- Source commit checked out by the notebook: `2d5ccdd17d5cb778cb3f7fb2588446eef4816c91`.
- Notebook: `detector/colab/yolo11n_n1_r1_r1_fresh.ipynb`.
- Runner: `detector/colab/run_yolo11n_n1_r1_r1.py`.
- Source-QA record supplied to the runner:
  `docs/review/yolo11n_n1_r1_r1_source_independent_qa_record.md`.
- Source-QA SHA-256: `57eb794e7256f1797a2961286330a98baa9a87664c9c6d84b84fe9ffda332254`.
- Train/validation archive SHA-256:
  `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05`.
- Archive manifest SHA-256:
  `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.

## Observed live evidence

- GPU: `NVIDIA L4`, UUID `GPU-bd05ef5d-01d5-6697-afea-a7a3b3012032`.
- Runtime digest:
  `e92eb6beebb741ef2a544ea8233e60228f53fd2179f8be6c8fb3ce67e1a0047b9`.
- Drive mounted successfully.
- Immutable checkout, L4 guard, archive hash and manifest hash all passed.
- The runner stopped before creating
  `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`.
- Reproduction in the Colab terminal produced:

```text
RuntimeError: training blocked: B0 source QA is not a PASS
```

## Root cause

The inherited `run_cascade_b0_r1.require_source_qa` accepts exactly one literal marker:
`Verdict: **PASS**`. The independently reviewed repair record instead contains
`Verdict: **PASS — SOURCE ONLY, PRE-COMMIT**`, so the guard rejects it before checking the
remaining hash bindings. That repair record also does not repeat all 16 source hashes from the
train/validation bundle that the inherited guard requires.

This is an execution-eligibility binding defect. It is not a dataset, GPU, checkpoint-identity or
training failure.

## Safety boundary and next action

- No R1-R1 checkpoint or `colab_execution.json` exists, so nothing from this attempt may be
  resumed or promoted.
- The old R1 failure state remains immutable evidence and was not reused.
- The sealed test was not exported, evaluated or opened; the verified input manifest keeps
  `sealed_test_accessed=false`.
- Repair append-only: create an independently reviewed composite QA record with the exact canonical
  PASS marker, all bundle-source hashes and the R1-R1 runner hash; then pin it from a new R1-R2
  notebook delta. Re-run fresh epoch 1 only after source and notebook QA PASS.
