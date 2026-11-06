# D1 final evaluation — Owner decision on test-label handling

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`).
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's instruction in chat.
Append-only once committed. `sealed_test_accessed=false`.

## Question carried forward

`docs/review/d1_final_evaluation_r1_contract_draft_addendum_1_two_seeds.md` (SHA-256
`97ffd3f49c2cb44691fc41bf3af9c8c9832296eb9df341644a05323f7bedc8a7`) requires an Owner choice before
test access:
- (a) score the test with its current labels and state the asymmetry; or
- (b) a separately authorized, prediction-blind review of the test labels.

## Owner decision (verbatim)

The coordinating session asked: "Score the test with the current labels, or do a prediction-blind
label review first?" The Owner answered: "Nhãn hiện có".

Decision: **(a) current labels**.

Machine-readable record for the final scorer: `docs/review/generated/d1_final_test_label_decision_r1.json`,
SHA-256 `369399b80c7b4e72757150557e60a8249b96d9da2f3668596d5a50c9b49b2eae`.
- `mode`: `CURRENT_LABELS`; `package`: `D1-FINAL-EVALUATION-R1`.
- The coordinating session checked it with the scorer's own parser `_label_decision` (accepted).

## Asymmetry to state in the final report

The validation labels were partly corrected in R3 (`docs/review/d1_vrl_r3_owner_acceptance_record.md`,
SHA-256 `4d9482856771960240cdf727834e9283fb9ba072f88992c6204dcbb6405d7480`):
- 64 missing sign boxes were added;
- 40 ignore regions were added.

The candidates came from the pilot's background false positives. That correction lowered validation
FP/image for the pilot from 0.569 to 0.399.

The test labels have not had that review. Expected consequences:
- Real signs that are unlabeled in the test count as false positives. Test FP/image may therefore be
  **higher than on validation**, even with an unchanged model and threshold.
- Recall can move in either direction, so no direction is assumed.

Because the R3 candidates came from seed 20261018's predictions, validation may slightly favour that
seed. On the test, both seeds face the same uncorrected labels.

The final report must state this asymmetry next to the FP/image result. If a gate is missed, it must
**not** attribute the miss to label noise unless separate evidence shows that.

## Limits

- This decision does not authorize opening the test. That needs a separate Owner opening approval
  bound to a finalized, independently QA-passed final-evaluation contract.
- It does not change the threshold lock, the Q4 gates or the app threshold.
- No test label, image or roster was read to make this decision.
