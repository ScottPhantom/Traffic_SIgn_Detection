# D1 final evaluation R1 — independent source QA (initial review)

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Scope: item 2 of `docs/codex_handoff_final_eval_scorer_2026-11-06.md`. Reviewer is independent of the source author. This review used source inspection and synthetic fixtures only. No sealed-test payload was opened, listed, read, hashed or scored; no real weight inference or training occurred. `sealed_test_accessed=false`.

## Reviewed bytes and checks

- `detector/m1/d1_final_evaluation_r1.py` SHA-256 `686d95c5eea63c88f3d68e5434f98a976aef418aff95d6f676d5947d8dc3866b`.
- `detector/tests/test_d1_final_evaluation_r1.py` SHA-256 `12167f408eab2bd8844b62dcb29f09481774752c8c1049e1a2ee4fe950698e19`.
- Read the implementation record, task handoff, D-05 two-seed amendment, amended draft final contract, amended threshold-lock contract, and only source dependencies needed to inspect the lock reader, metrics and access logger.
- `graft check .`: OK. Focused synthetic test command `PYTHONPATH=detector uv run --no-sync pytest -q detector/tests/test_d1_final_evaluation_r1.py`: 20 PASS. `uv run --no-sync ruff check detector/m1/d1_final_evaluation_r1.py detector/tests/test_d1_final_evaluation_r1.py`: PASS. `uv lock --check`: PASS. These checks do not cover the defect below.

## Blocking defect — seed identity is not bound to its locked weight

`preflight()` requires the two seed numbers and two distinct weight hashes (`d1_final_evaluation_r1.py:260-268`), but then passes each **hash alone** to the R3 reader (`:293-304`). The QA-passed reader `d1_threshold_lock_r3_successor.read_for_final()` checks only that the hash belongs to *some* locked candidate (`:591-593`) and returns the shared selection. Neither step checks that the plan's seed 20261018 uses the locked seed-20261018 weight, or that seed 20261019 uses its own weight.

I demonstrated the gap using the existing synthetic fixture: after swapping only the two `seed` fields in the plan's weight entries and regenerating its synthetic plan/contract/approval bindings, `preflight(..., committed=False, reader=_reader)` still returned `Approved` with the weights assigned to the opposite seeds. This is a controlled source-path test, not a sealed-test operation. The production reader has the same membership-only check, so the committed path likewise lacks a seed-to-hash comparison. A future run could report each seed and `difference_19_minus_18` under the wrong identity even if the aggregate mean is unchanged. The handoff requires the exact two candidate identities and per-seed reporting.

Required repair: compare each plan `(seed, weight_sha256)` to the corresponding candidate pair from the **verified** R3 lock, and add a synthetic swapped-pair rejection test. Keep the pinned predecessor reader unchanged; an append-only scorer successor/delta can perform this check.

## Scope of the finding

The intended call order in `execute()` is preflight, validation-only latency, repeated preflight, access-log append under a process lock, then sealed roster loading. The synthetic tests exercise many refusal gates and log ordering, but they do not establish a safe final run while the candidate identity binding fails. This record does not authorize test access, an official final contract or a model verdict.

Verdict: FAIL
