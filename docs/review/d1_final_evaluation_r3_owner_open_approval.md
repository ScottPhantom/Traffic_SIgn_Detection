# D1 final evaluation R3 — Owner approval to export and score the sealed test once

Date: 2026-11-07 00:01 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed.

OWNER_AUTHORIZES_TEST_OPEN: D1-FINAL-EVALUATION-R1

The marker is the scorer's fixed opening marker; the package id stays `D1-FINAL-EVALUATION-R1`, which
also keeps the Q4 and label records valid. The approved contract is **R3**.

## Owner decision (verbatim)

The coordinating session asked: "Anh có duyệt xuất dữ liệu test và chấm một lần theo contract R3
(7f1f1d95) không?" The Owner answered: "Duyệt mở test R3".

Before asking, the coordinating session checked:
- both R3 QA records (PASS);
- the contract hash;
- a real `preflight`-only call from `detector/`, which stopped at "Owner has not approved opening";
- the access log: still one line, SHA-256
  `ffef1b183ec8b4a20661c4bca71efa3cab64692c445432bc38eb3b3f2773b369`.

## What is approved

One run of the pinned two-command sequence in the R3 contract, starting at the checkout root:

```bash
uv run --no-sync python scripts/build_m1_yolo_dataset.py export-test --final-eval \
  --reason "One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates."
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r3_plan.json
```

| Bound file | SHA-256 |
| --- | --- |
| `docs/review/d1_final_evaluation_r3_contract.md` | `7f1f1d95188980ba91ffc5594d46eec2df35c97842632eba2187a3cd9047a60c` |
| `docs/review/generated/d1_final_evaluation_r3_plan.json` | `2a8462225b88cbc4d32c0f359fe83d81bb49528f3b70d9f6616b8e9bd7c48c5f` |
| `docs/review/d1_final_evaluation_r3_source_delta_independent_qa_record.md` (`Verdict: PASS`) | `72574be8bd72ed05e1d8e865e5ef2cbe46bd9df4c2360be1e1ddfbe7d176dbc6` |
| `docs/review/d1_final_evaluation_r3_contract_independent_qa_record.md` (`Verdict: PASS`) | `7f3bebaa3836217a05d5c6413b7c13308be556998bd598ce2216b855a0a03e09` |
| `docs/review/d1_final_evaluation_recovery_owner_authorization_2026-11-06.md` | `60ae0c3bae98169562004061f168c7e8d3c57981ae3fed1a261f0efbd70cbb76` |

Plan reason (verbatim):
One-time D1 final evaluation of seeds 20261018 and 20261019 under the approved R3 lock and D-05 gates.

Inputs, unchanged:
- lock: confidence 0.19, class-aware NMS IoU 0.70 (`82e6b6f`);
- Q4 gates: FP/image ≤ 0.40, other gates original (`8726d8c`);
- current test labels (`00578c2`);
- the two pinned weights.

## Conditions

- If the export fails, the scorer is not run, and the failure is recorded.
- If the scorer's preflight refuses, the refusal is recorded. Nothing is retried with changed
  parameters without a new Owner decision.
- Once the R3 access event is logged, this is the one-time opening. No parameter, threshold, gate,
  weight or label may change after any test result is seen.
- The final report must:
  - disclose attempts 1 and 2;
  - give both FP verdicts (0.30 original, 0.40 recalibrated);
  - state the current-label asymmetry;
  - pass an independent result QA before it is published or presented as an acceptance result.
- The results are offline test measurements, not a safety claim. Behaviour output stays simulation
  only.
- No app-threshold change, no training, no push.
