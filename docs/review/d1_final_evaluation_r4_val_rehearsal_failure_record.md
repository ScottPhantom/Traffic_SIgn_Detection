# D1 final evaluation R4 — validation rehearsal stopped

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`). Status: `STOPPED_REHEARSAL_FAILED`.

This record covers only the R4 preparation on the pinned R3 validation bundle. No
`export-test` or real scorer `execute` command was run. The sealed test had already
been accessed in the historical R3 attempt 3; **this preparation made no new
sealed-test access**.

## Checks completed

- The R4 scorer source handles five noninteger derived keys by sorting on YOLO
  class ID, and writes each seed's predictions atomically before scoring.
- Synthetic scorer tests passed; Ruff on the changed scorer and test passed.
- MPS was available. The R3 validation bundle pin and both weight hashes were
  checked before either rehearsal reached inference.
- The access log remained three lines, SHA-256
  `a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45`.

## Failed validation rehearsal attempts

1. The first invocation exited 1 before any prediction. The scorer passed a
   repository-relative weight path to Ultralytics while running from `detector/`;
   `FileNotFoundError` named the pilot `best.pt`. The scorer was changed to use
   an absolute path. The empty output directory was retained at
   `results/experiments/d1_final_evaluation_r4_rehearsal_val_attempt1_path_error/`.
2. The second invocation exited 1 before any prediction. The validation roster
   was built with a `.jpg` suffix for every stem, but `1319` is a `.png` member
   of the pinned bundle. Ultralytics raised `FileNotFoundError` for `1319.jpg`.
   The empty output directory was retained at
   `results/experiments/d1_final_evaluation_r4_rehearsal_val_attempt2_image_extension_error/`.

There are no rehearsal predictions, metrics, JSON report, or Markdown report.
The second fault remains in the current working source. The source SHA-256 is
`ce721028bf646b01ee70cc238200e4022c806481391f0b7384e90840ce7cc152`;
the R4 draft plan SHA-256 is
`c499edbc2fa940f41dde2e8c841d4b1f33ddad00605975ba2675ca33871b9ad0`.

The handoff's rehearsal-failure stop condition applies. No R4 contract or
opening approval was created, no independent QA was requested, and no commit or
push was made. A successor must derive each validation image's actual path from
the pinned bundle manifest, add a mixed-extension test, update the scorer pin in
the R4 plan, and rerun the full validation rehearsal before source QA or contract
work resumes. Do not use the current draft plan for a real final evaluation.
