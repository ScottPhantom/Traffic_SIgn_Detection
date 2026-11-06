# D1 final evaluation R2 — Owner approval to open the sealed test once

Date: 2026-11-06 23:09 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed.

OWNER_AUTHORIZES_TEST_OPEN: D1-FINAL-EVALUATION-R1

The marker above is the scorer's fixed opening marker. It keeps the package id `D1-FINAL-EVALUATION-R1`,
which is also the package of the Q4 and label decision records. The approved contract is R2.

## Owner decision (verbatim)

The coordinating session asked: "Anh có duyệt mở test một lần theo contract R2 (0f8bbf10) không?"
The Owner answered: "Duyệt mở test R2".

Before asking, the coordinating session ran the real `preflight` from `detector/`, with nothing else:
- it passed the R3 lock/proof gate;
- it stopped at "Owner has not approved opening";
- `results/experiments/sealed_test_access_log.jsonl` did not exist.

Attempt 1 under R1 stopped before test access; see
`docs/review/d1_final_evaluation_r1_run_attempt_1_preflight_refusal.md` (SHA-256
`3321dae48b653610445acf45aed817c6fddad933604546b91a5c5576a4ffd9f2`). This approval replaces the R1
opening approval, which can no longer pass preflight because it binds the R1 contract hash.

## What is approved

**One** execution of the pinned command in the R2 contract:

```bash
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r2_plan.json
```

| Bound file | SHA-256 |
| --- | --- |
| `docs/review/d1_final_evaluation_r2_contract.md` | `0f8bbf104e523f243f5f0e3c6b23b4e9545bf98a353a1f6b560c62cc3cfa86ff` |
| `docs/review/generated/d1_final_evaluation_r2_plan.json` | `69f54ee3f6e6d10914d5347fa445d5457df43954dad063dbb0b90bb725b914a0` |
| `docs/review/d1_final_evaluation_r2_source_delta_independent_qa_record.md` (`Verdict: PASS`) | `56a5e0954549d046bc744b444389cde5d4a5afd5196f30c9ec3e095e66bd4df4` |
| `docs/review/d1_final_evaluation_r2_contract_independent_qa_record.md` (`Verdict: PASS`) | `f75cd0522631efbafe0c1d82c31d61b0bdc1025e9d00a9ddaaf3d65d2c01abe5` |

Plan reason (verbatim):
One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates.

The run uses the inputs already approved:
- the R3 lock: confidence 0.19, class-aware NMS IoU 0.70 (commit `82e6b6f`);
- the Q4 gates, with FP/image ≤ 0.40 (commit `8726d8c`);
- the current test labels (commit `00578c2`);
- the two pinned weights, seeds 20261018 and 20261019.

## Conditions

- The scorer's preflight must pass before any test byte is read. A refusal is recorded; nothing is
  retried with changed parameters without a new Owner decision.
- Once the access event is logged, the test counts as **opened**, even if a later step fails.
- No parameter, threshold, gate, weight or label may change after any test result is seen.
- The final report must:
  - give both FP verdicts, against the original marker 0.30 and the recalibrated marker 0.40;
  - state the current-label asymmetry beside the FP result;
  - pass an independent result QA before it is published or presented as an acceptance result.
- The results are offline test-set measurements, not a safety claim. Behaviour output stays
  simulation only.
- This approval does not authorize changing the app threshold, training, or pushing.
