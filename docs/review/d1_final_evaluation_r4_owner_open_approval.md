# D1 final evaluation R4 — Owner approval of one test-scoring run

Date: 2026-11-07 05:46 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed.

OWNER_AUTHORIZES_TEST_OPEN: D1-FINAL-EVALUATION-R1

This is the scorer's fixed opening marker. The package id stays `D1-FINAL-EVALUATION-R1`, so the Q4
and label records stay valid. The approved contract is **R4**.

## Owner decision (verbatim)

The coordinating session asked: "Do you approve the one R4 test-scoring run under contract d241011c?"
The Owner answered: "Duyệt chấm R4".

Before asking, the coordinating session checked the following:
- **Validation rehearsal.** It ran the full predict → save → score → report path. TP/FP per seed were
  555/155 and 512/131, which exactly matches the lock: mean recall 0.854968, mean FP/image 0.380319.
- **QA.** Both R4 QA verdicts are PASS.
- **Contract hash.** It matches the hash bound below.
- **Preflight.** A real preflight-only call stopped at "Owner has not approved opening".
- **Access log.** It is unchanged: 3 lines, SHA-256
  `a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45`.

The coordinating session also told the Owner that critical classes 7, 32 and 41 already fail their
class gate on validation.

## What is approved

**One** execution of the pinned R4 scorer command. The test export already exists from attempt 3 and is
not re-run.

```bash
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r4_plan.json
```

| Bound file | SHA-256 |
| --- | --- |
| `docs/review/d1_final_evaluation_r4_contract.md` | `d241011c21dcc6a56c525f538ec32a3c6d35ac5c78bc56aed6acb3e218b3d38d` |
| `docs/review/generated/d1_final_evaluation_r4_plan.json` | `2c463b61bbe73e482e28b1454023db438cc7d363f2ebc3525da942d37e74fc6f` |
| `docs/review/d1_final_evaluation_r4_source_delta_independent_qa_record.md` (`Verdict: PASS`) | `49513374d67ce39d58c68313f2554efaf6c6be7b0389896b3f675601f9ec27c3` |
| `docs/review/d1_final_evaluation_r4_contract_independent_qa_record.md` (`Verdict: PASS`) | `b1458c68cb39d1c9558cb6932f47ddf32b9049aeb8346bc7ec3afaeb1ec56694` |
| `docs/review/d1_final_evaluation_r4_val_rehearsal_record.md` | `69fe798b8190f4fd0f0e25fb352db175ac2ad885808c42138b26e58c3a499e5a` |
| `docs/review/d1_final_evaluation_r4_owner_authorization_2026-11-07.md` | `251f464f575e06562793118ffc1db6d72dddc9140cfa41920a2598fcc12f27bf` |

Plan reason (verbatim):
One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates, after R4 scorer recovery and validation rehearsal.

The inputs are unchanged:
- lock: confidence 0.19, class-aware NMS IoU 0.70 (`82e6b6f`);
- Q4: FP/image ≤ 0.40, other gates original (`8726d8c`);
- current test labels (`00578c2`);
- the two pinned weights.

## Conditions

- A preflight refusal is recorded. Nothing is retried with changed parameters without a new Owner
  decision.
- No parameter, threshold, gate, weight or label may change after any test result is seen.
- The final report must:
  - disclose attempts 1–3, including that attempt 3 ran a test prediction pass whose output was lost
    unseen;
  - give both FP verdicts (0.30 original, 0.40 recalibrated);
  - state the current-label asymmetry;
  - pass an independent result QA before it is published or presented as an acceptance result.
- The results are offline test measurements, not a safety claim. Behaviour output stays simulation
  only.
- This approval does not cover an app-threshold change, training, or a push.
