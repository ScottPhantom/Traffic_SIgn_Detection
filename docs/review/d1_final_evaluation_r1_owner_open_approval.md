# D1 final evaluation R1 — Owner approval to open the sealed test once

Date: 2026-11-06 22:41 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed.

OWNER_AUTHORIZES_TEST_OPEN: D1-FINAL-EVALUATION-R1

## Owner decision (verbatim)

The coordinating session asked: "Do you approve opening the sealed test once, to score both seeds
under contract de92d8c6?" The Owner answered: "Duyệt mở test".

Before asking, the coordinating session told the Owner:
- the test can be opened only once;
- the FP marker is likely to fail.

## What is approved

**One** execution of the pinned command in the final-evaluation contract, run from `detector/`:

```bash
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r1_plan.json
```

| Bound file | SHA-256 |
| --- | --- |
| `docs/review/d1_final_evaluation_r1_contract.md` | `de92d8c61599e60989438765f372d8b4bbbb4d801b9f565a46dc69557f1f05d8` |
| `docs/review/generated/d1_final_evaluation_r1_plan.json` | `9c90ee71f5106ab1d28bdeb46ef4877d1028333e5e6532198337e0f451c96f77` |
| `docs/review/d1_final_evaluation_r1_contract_independent_qa_record.md` (`Verdict: PASS giới hạn`) | `2db4de4d376cbc997af77f938a5bde6623f44baa95bcbb1117ffbc408e9336e5` |

Plan reason (verbatim):
One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates.

The run uses the inputs already approved:
- the R3 lock: confidence 0.19, class-aware NMS IoU 0.70 (commit `82e6b6f`);
- the Q4 gates, with FP/image ≤ 0.40 (commit `8726d8c`);
- the current test labels (commit `00578c2`);
- the two pinned weights, seeds 20261018 and 20261019.

## Conditions

- The scorer's own preflight must pass before any test byte is read. If it refuses, the refusal is
  recorded and nothing is retried with changed parameters without a new Owner decision.
- After the access event is logged, the test counts as **opened**, even if a later step fails.
  The one-time rule then applies to this package.
- No parameter, threshold, gate, weight or label may change after any test result is seen.
- The final report must:
  - state both the original FP marker 0.30 and the recalibrated marker 0.40, with both verdicts;
  - state the current-label asymmetry beside the FP result;
  - pass an independent result QA before it is published or presented as an acceptance result.
- The results are offline measurements on the test set. They are not a safety claim, and behaviour
  output stays simulation only.
- This approval does not authorize changing the app threshold, training, or pushing.
