# D1 final evaluation R1 — independent source delta QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). This is a separate, append-only review of the successor delta after the initial source QA FAIL. The original record `docs/review/d1_final_evaluation_r1_source_independent_qa_record.md` remains unchanged at SHA-256 `fdc12a68d04d32bd909e5673fbea1316885ef326dbc2d8b98714e5228d7559db`. The reviewer did not write or operate the scorer. All probes used synthetic fixtures; no sealed-test payload was opened, listed, read, hashed or scored, and no real weight inference or training occurred. `sealed_test_accessed=false`.

## Exact bytes reviewed

- Successor scorer `detector/m1/d1_final_evaluation_r1.py`: SHA-256 `d154132733c24e6a63a81e7dc1014497202fe1aa72dbd46eeb2e57e1a6a804c8`.
- Successor synthetic test `detector/tests/test_d1_final_evaluation_r1.py`: SHA-256 `eb870803d735d54eada07d2d0380e6481a203c3fd441cc4855bf9a7a0fa452f4`.
- Both hashes match the successor section appended to `docs/review/d1_final_evaluation_r1_implementation_record.md`.

## Defect closure

After the R3 `read_for_final` call verifies the record, its proof, QA and Owner lock approval, the scorer now reads the same non-test lock record and compares the complete `{seed: weight_sha256}` mapping of its two candidates with the final plan. The check rejects a missing/extra candidate, malformed candidate identity or a swapped pair before any future sealed roster load. It leaves the pinned predecessor reader unchanged. The new test adds `swapped_seed_labels` to the preflight refusal matrix.

I independently reran a synthetic positive plan and then swapped only its two seed labels while rebinding the synthetic plan/contract/approval. The positive plan returned the expected ordered two weights; the swapped plan raised `RuntimeError: candidate seed-to-weight binding differs from verified R3 lock`. This reproduces the original failure scenario and verifies its closure without using a real lock or payload.

## Regression and scope checks

- `PYTHONPATH=detector uv run --no-sync pytest -q detector/tests/test_d1_final_evaluation_r1.py`: **21 passed** using synthetic fixtures. The pre-existing 20 cases remain passing.
- `uv run --no-sync ruff check detector/m1/d1_final_evaluation_r1.py detector/tests/test_d1_final_evaluation_r1.py`: PASS.
- `uv lock --check`: PASS.
- `graft check .`: graph in sync.
- Source inspection confirms the existing order remains preflight, validation-only latency, repeated preflight, one-time access-log append, then future sealed roster loading. The pure scorer and output path were not changed by this delta.

This verdict covers source preparation and the seed-to-weight repair only. It does not authorize a final contract, Owner test opening, a real execution, or a model result.

Verdict: PASS
