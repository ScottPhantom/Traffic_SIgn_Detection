# D1 checkpoint/resume R4-R6 implementation record

Status: `PM_IMPLEMENTED_AWAITING_INDEPENDENT_QA`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Boundary: `APPEND_ONLY_TRAIN_VAL_ONLY_NO_LIVE_TRAINING_NO_SEALED_TEST`

R4-R6 preserves all prior candidates and QA records. It installs one exact-type runtime-evidence
validator across direct, archive, live and packaging execution paths. `colab_execution.json` now
passes only when `type(schema_version) is int` and the value is exactly `2`; JSON float `2.0`,
boolean `true`, string `"2"` and `null` are rejected before inherited semantic validation.

The successor notebook uses a new isolated run label and remains unexecuted at
`CODE_COMMIT = "PENDING_AFTER_QA"`. Permanent tests cover all four invalid representations directly
and exercise both archive and live verifier installation.

Independent source QA PASS is required before commit/push and pinning. Any PASS authorizes only a
new two-runtime/two-epoch L4 smoke; the 100-epoch pilot remains **NO-GO** pending separate live-smoke
QA PASS.
