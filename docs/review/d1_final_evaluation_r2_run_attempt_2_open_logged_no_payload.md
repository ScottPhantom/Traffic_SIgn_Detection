# D1 final evaluation — run attempt 2 (R2): opening logged, test payload not read

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session. Append-only once committed.

## What was run

After the R2 Owner opening approval was committed
(`docs/review/d1_final_evaluation_r2_owner_open_approval.md`, commit `239bcfe`), the coordinating
session ran the pinned R2 command exactly once, from `detector/`:

```bash
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r2_plan.json
```

## Outcome

Exit code 1. The run went through these steps in order:
1. preflight passed;
2. the validation-only latency loop ran (no output saved);
3. the second preflight passed;
4. `_open_once` appended the one-time access event;
5. `_real_test_roster` called `contract.check_contract("test")`, which raised:
   `data/processed/m1_yolo/data_test.yaml missing: run scripts/build_m1_yolo_dataset.py export-test --final-eval`.

The log is kept in the session scratchpad, SHA-256
`ed1aa35a1db43c13a8ff6fdcb22cc6113ed40aecbd66b003aa362368d331cc42`.

Access log `results/experiments/sealed_test_access_log.jsonl` (Git-ignored location, not committed),
SHA-256 `ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369`, one line:

```json
{"time": "20261106T231301", "action": "d1-final-evaluation-r1-open", "reason": "One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates. | plan_sha256=69f54ee3f6e6d10914d5347fa445d5457df43954dad063dbb0b90bb725b914a0 | contract_sha256=0f8bbf104e523f243f5f0e3c6b23b4e9545bf98a353a1f6b560c62cc3cfa86ff"}
```

## What was and was not accessed

- `check_contract("test")` failed before the scorer listed or read any test image or label.
  - Its earlier step, `export.verify`, checks the export manifest and split-list hashes from the
    source CSVs. Every validation run makes the same check.
  - The test export does not exist in `data/processed/m1_yolo/`, so there was no test payload there
    to read.
- No test prediction, metric or result was produced or seen. The output directory
  `results/experiments/d1_final_evaluation_r1` was not created.
- Formally, the one-time opening event **is recorded**. The R2 approval said the test counts as
  opened once the access event is logged.
  - The scorer refuses any further run while that entry exists (`_open_once` and preflight lines
    406–408).
  - The access log is append-only and must not be edited or deleted.

## Root cause

The scorer and both contracts assumed the test export already existed. Neither the preflight nor the
contract QA checked for `data_test.yaml` before the access event. The export needs a separate,
logged `export-test --final-eval` step that no approval covered.

## Consequence

The D1 final evaluation cannot be completed under the current records. Any continuation needs a new
Owner decision, because the formal one-time opening has been used even though no test data or
result was seen. Options:
- **(a)** Authorize a recovery package:
  - the test export (`export-test --final-eval`, logged);
  - a scorer successor that checks the export exists **before** logging the opening;
  - a scorer successor that accepts exactly this one recorded event, pinned by its hash, as a
    no-payload attempt;
  - with source QA, an R3 contract, its QA, and a new opening approval.
- **(b)** Stop the final evaluation here. Report validation results only and state that the test was
  not scored.

Whichever option is chosen, this attempt must be disclosed in any final report.
