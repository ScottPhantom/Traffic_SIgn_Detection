# D1 checkpoint/resume R4-R5 implementation record

Status: `PM_IMPLEMENTED_AWAITING_INDEPENDENT_QA`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Boundary: `APPEND_ONLY_TRAIN_VAL_ONLY_NO_LIVE_TRAINING_NO_SEALED_TEST`

R4-R5 preserves all prior candidates and QA records. It validates the generation name before any
snapshot path is constructed. Its preflight failure collector treats every pointer-read exception
as an unavailable checkpoint binding, rejects symlinked recovery components, and still writes the
terminal FAILED execution record plus append-only attempt. This covers syntactically valid but
non-object pointers, corrupt pointers and external recovery symlinks without importing untrusted
binding data.

The successor notebook uses a new isolated run label and remains unexecuted at
`CODE_COMMIT = "PENDING_AFTER_QA"`. Permanent regressions cover list/string/integer pointers,
recovery-symlink binding injection and traversal-like generation values.

Independent source QA PASS is required before commit/push and pinning. Any PASS authorizes only a
new two-runtime/two-epoch L4 smoke; the 100-epoch pilot remains **NO-GO** pending separate live-smoke
QA PASS.
