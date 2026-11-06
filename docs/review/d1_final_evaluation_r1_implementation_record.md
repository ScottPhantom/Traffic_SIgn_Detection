# D1 final evaluation R1 — implementation record

Date: 2026-11-06. Scope: item 2 of `docs/codex_handoff_final_eval_scorer_2026-11-06.md`.

## Status and boundary

- Prepared an append-only successor scorer at `detector/m1/d1_final_evaluation_r1.py` and synthetic-only tests at `detector/tests/test_d1_final_evaluation_r1.py`.
- No final evaluation was run. No sealed test payload was opened, listed, read, or scored. No real weight inference or training occurred. No official final contract or Owner opening approval was created.
- The official contract in handoff item 3 remains pending a QA-passed R3 lock, Owner lock approval, Owner Q4 and label decisions, and independent source QA.
- `sealed_test_accessed=false` for this implementation and its tests.

## Implemented behavior

1. `preflight` verifies a committed plan, the R3 lock via its reader, exactly seeds `20261018` and `20261019`, a shared locked confidence/NMS setting, the validation-only bundle manifest, distinct Owner lock and opening approvals, the final contract hash, Q4 and label decisions, source and weight hashes, and an unused access-log allowance. It rejects incomplete or inconsistent inputs before the future payload loader is reached.
2. The future `execute` path measures Q5 latency on validation images, repeats preflight, appends the one-time access event through `contract.log_test_access` under a process lock, and only then invokes the sealed roster loader. It produces JSON and Markdown only after that path. It was not invoked for this record.
3. The pure `score_two_seeds` path reports per-seed and two-seed metrics, per-class recall and AP, Q2/Q3 gate checks, AP-small, resolution breakdown, error analysis, and D-02 paired group bootstrap intervals. The CI holds the two candidate weights fixed. Ordinary class gate failures are recorded for exclusion from simulated behavior; critical-class failures affect the gate.
4. `PREDICTION_BLIND_REVIEW` requires a separate PASS QA record and a pinned approved-label hash. Preflight checks this metadata without reading the reviewed labels. The future roster loader reads those labels only after the access event.

## Local validation

- `PYTHONPATH=detector uv run --no-sync pytest -q detector/tests/test_d1_final_evaluation_r1.py`: 20 passed, all with synthetic fixtures.
- `uv run --no-sync ruff check detector/m1/d1_final_evaluation_r1.py detector/tests/test_d1_final_evaluation_r1.py`: PASS.
- `uv lock --check`: PASS.
- `graft build . && graft check .`: graph check OK.
- Source SHA-256: `686d95c5eea63c88f3d68e5434f98a976aef418aff95d6f676d5947d8dc3866b`.
- Test SHA-256: `12167f408eab2bd8844b62dcb29f09481774752c8c1049e1a2ee4fe950698e19`.

Independent source QA is recorded separately. This record is implementation evidence, not authorization to open the sealed test or a final model verdict.

## Successor delta after independent QA FAIL

The first independent review identified a seed-to-weight binding gap: R3 `read_for_final` proves that each weight hash belongs to the locked candidate set, but does not bind the hash to its seed. The scorer now reads the already verified, non-test R3 record and compares the exact `(seed, weight SHA-256)` map with the final plan. A synthetic swapped-seed plan is a refusal case.

- Original independent QA: `docs/review/d1_final_evaluation_r1_source_independent_qa_record.md`, one `Verdict: FAIL` line, SHA-256 `fdc12a68d04d32bd909e5673fbea1316885ef326dbc2d8b98714e5228d7559db`.
- Successor source SHA-256: `d154132733c24e6a63a81e7dc1014497202fe1aa72dbd46eeb2e57e1a6a804c8`.
- Successor test SHA-256: `eb870803d735d54eada07d2d0380e6481a203c3fd441cc4855bf9a7a0fa452f4`.
- Focused synthetic tests: 21 passed. Ruff and `graft check .`: PASS. The lockfile check above remains PASS.

This delta requires a separate independent QA record before the source can be treated as QA-passed.
