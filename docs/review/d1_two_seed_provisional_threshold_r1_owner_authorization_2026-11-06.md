# D1 two-seed provisional threshold R1 — Owner authorization

Date: 2026-11-06 (Asia/Ho_Chi_Minh). The coordination handoff records the Owner's words:

> "lấy trung bình trên 19 trước vì không đủ thời gian chạy 3 seed."

The Owner subsequently asked Codex in chat to execute
`docs/codex_handoff_two_seed_provisional_threshold_2026-11-06.md` after the
independent completed-run QA for seed 20261019 passed.

Authorization is bounded to **one validation R3 inference sweep** with the
QA-pinned seed-20261019 `best.pt`: eight class-aware NMS IoUs 0.45–0.80 and
three class-agnostic IoUs 0.80/0.85/0.90. The 11 pilot prediction CSVs are
reused without inference. This is a two-seed, in-sample provisional diagnostic
for presentation; it is not the frozen three-seed threshold lock.

No training, sealed-test access, app or D-05 change, threshold-lock command,
upload or push is authorized by this record. `sealed_test_accessed=false`;
`thresholds_locked=false`.
