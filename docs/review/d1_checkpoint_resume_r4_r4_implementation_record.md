# D1 checkpoint/resume R4-R4 implementation record

Status: `PM_IMPLEMENTED_AWAITING_INDEPENDENT_QA`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Boundary: `APPEND_ONLY_TRAIN_VAL_ONLY_NO_LIVE_TRAINING_NO_SEALED_TEST`

R4-R4 preserves all prior candidates and QA records. Its successor runner closes the two R4-R3
findings by requiring exact non-boolean integer types for pointer/manifest versions, completed epoch
and artifact sizes, and by replacing preflight failure recording with a corrupt-pointer-tolerant
implementation. A malformed `recovery/latest.json` can no longer prevent the runner from writing
`colab_execution.json` and appending a FAILED attempt; the checkpoint binding is recorded as `null`
when it cannot be safely recovered.

The successor notebook has a new isolated run label and remains unexecuted at
`CODE_COMMIT = "PENDING_AFTER_QA"`. Permanent regressions cover all three boolean/int confusion
cases and durable evidence when both the prior JSONL and latest pointer are malformed.

Independent source QA PASS is required before commit/push and pinning. Any PASS authorizes only a
new two-runtime/two-epoch L4 smoke; the 100-epoch pilot remains **NO-GO** pending separate live-smoke
QA PASS.
