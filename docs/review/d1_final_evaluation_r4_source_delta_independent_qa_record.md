# D1 final evaluation R4 — independent source delta QA

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex agent from the R4 implementer. Scope: scorer delta, synthetic tests, R4 plan pins and completed **validation R3** rehearsal only. This is not an approval to open or evaluate the sealed test.

Verdict: PASS

## Evidence reviewed

- The R4 plan SHA-256 is `2c463b61bbe73e482e28b1454023db438cc7d363f2ebc3525da942d37e74fc6f`. Its scorer pin matches the current source SHA-256 `2be9ad7da62268f418d1138bb01d2f81a2dfb20aa7c711ddcda4237a927ce75a`. All six executable source pins in the plan matched their files. The test SHA-256 is `fce4ece4a74e996dbdc13ff3aeb56f3dfbd3b6f46c6f5ff39b28fb51975c1e45`.
- The validation bundle manifest SHA-256 is `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`. Its 376 validation image members comprise 337 `.jpg` and 39 `.png`. The new roster builder selects the actual manifest member for each unique stem and refuses duplicate stems, unsupported suffixes, missing files and symlinks. The focused synthetic test covers both extensions and a duplicate-stem refusal.
- The scorer sorts derived class keys by YOLO ID, avoiding `int()` on the five subclass keys (`16:2.0`, `16:2.2`, `16:2.5`, `43:2.5`, `43:2.7`). A focused test calls `score_two_seeds` with the real class map and synthetic predictions for all five keys. The access-history gate pins the exact three recorded line hashes and refuses changed history; the R4 opening action is distinct.
- `_predict_score_report` uses one code path for the rehearsal and a future separately authorized run: it predicts each fixed seed, saves its raw box/class/confidence/stem predictions and a hash/weight manifest atomically, then scores and writes JSON and Markdown. The fault-injection test confirms both prediction files survive a scoring exception. No path for scoring saved prediction files was added.
- Independent rerun: `PYTHONPATH=. uv run --no-sync pytest -q tests/test_d1_final_evaluation_r1.py` passed all 32 tests; `uv run --no-sync ruff check m1/d1_final_evaluation_r1.py tests/test_d1_final_evaluation_r1.py` passed; `uv lock --check` passed.

## Validation rehearsal readback

The completed process exited 0 and wrote all six files to `results/experiments/d1_final_evaluation_r4_rehearsal_val/`. The result JSON SHA-256 is `48c2c45aac6e3ff14a2fbd934fafe1f32b8fb7b216ea08c7dc1534df428bf7db`; Markdown SHA-256 is `451a6c6f84f4b2e9161a24756bd2f6dea13d3f3d16eccf8f10081ee86b980ea0`. The JSON binds the R4 plan hash, split `val`, 376 images, 624 GT boxes, `conf=0.19`, class-aware NMS IoU `0.70`, no access event and `sealed_test_accessed=false`.

| Seed | TP | FP | Recall | FP/image | Raw prediction SHA-256 | Raw boxes |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 20261018 | 555 | 155 | 0.8894230769 | 0.4122340426 | `4b7b366ada672cea432202d6735345864c3d541173d44ed7e86f8a0f081a6b63` | 1,999 |
| 20261019 | 512 | 131 | 0.8205128205 | 0.3484042553 | `60a71ee5f3a88ae53dd048d4aacbcc3490f5146deee5676233028526b14f8642` | 2,611 |

I independently recomputed the two-seed arithmetic mean from these operating-point counts: recall `(555+512)/(2×624) = 0.8549679487` and FP/image `(155+131)/(2×376) = 0.3803191489`. Both match the locked sanity targets. Each prediction manifest hash matches the corresponding file, and each payload and manifest weight SHA-256 matches its plan seed binding. This QA checks result arithmetic and artifact integrity; it does not re-score saved predictions or claim test performance.

The access log still has exactly three lines, SHA-256 `a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45`. No sealed-test payload was accessed in this R4 preparation. The historical R3 attempt 3 did access the test and remains disclosed in its separate record. Contract QA, a separate Owner opening approval, and independent result QA remain mandatory before any test result can be published.
