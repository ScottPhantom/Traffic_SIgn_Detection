# D1 two-seed provisional threshold R1 — independent source QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh), by a Codex agent separate from the source author and execution agent. This is source and pinned-input preflight QA only; no model inference or training was run.

Verdict: PASS

## Reviewed byte bindings (SHA-256)

| File | SHA-256 |
| --- | --- |
| `docs/codex_handoff_two_seed_provisional_threshold_2026-11-06.md` | `678cc4037298cebb3b73ed69d35e8a70bf55ebfa0caaebfe6cabc158701296e8` |
| `docs/review/d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md` | `f71a7eea772e191b8db6bf6074b450aa71fa3c8bbeb443b69983eb610e627be4` |
| `detector/m1/two_seed_provisional_threshold_r1.py` | `a8f93f0da02ba1decafcbcbb3b21bd12daae1b47f1845cf1cf5d3f951e6fadf3` |
| `detector/tests/test_two_seed_provisional_threshold_r1.py` | `56abab9a135a349e45add5b3c88828a47fa903719347272cdbfa34a87f0855d0` |

## Findings and checks

- The authorization record confines the work to one seed-20261019 validation R3 inference sweep. Preflight requires the independent S2 run-result and evaluation-result QA records to PASS, checks the authorization hash, and combines the sweep module's pinned input hashes. Read-only preflight returned `PREFLIGHT PASS: 36 pinned files; sealed_test_accessed=false`.
- The source reuses the 11 QA-pinned pilot prediction CSVs and the existing NMS inference and scorer. It checks the S2 `best.pt` against its pinned archive, runs class-aware IoU 0.70 first, and stops before writing sweep output or running the other configurations unless the conf-0.20 counts and mAP match the independently QA-checked S2 validation result.
- The grid is the frozen threshold-lock grid: 0.05–0.95 in steps of 0.05, united with 0.15–0.30 in steps of 0.01. Each of the 11 configurations has 31 confidence cells. Selection uses the mean of the two seeds, recall at least 0.85, minimum FP/image, and the documented tie order. If a different NMS setting fails any of the three CI/CV conditions, `decide_change` returns the class-aware IoU 0.70 fallback.
- The paired 1,000-draw bootstrap uses the same nine-group draw for both seeds and both compared settings, averages seed metrics within each draw, then takes the candidate-minus-reference difference. Leave-one-group-out selection fits on eight groups and measures the ninth; per-frame statistics are cached and sliced by group. The code records each seed's recall at the provisional choice.
- Synthetic tests cover selection/tie behavior, two-seed means, fallback and paired bootstrap draws. `PYTHONPATH=. uv run --no-sync pytest -q tests/test_two_seed_provisional_threshold_r1.py`: 5 passed. Ruff on the new source and test, root `uv run ruff check src tests`, and root `uv lock --check`: passed. `graft build . && graft check .`: graph in sync.
- Output is explicitly `PROVISIONAL_TWO_SEED_NOT_A_LOCK`, `thresholds_locked=false`, and `sealed_test_accessed=false`. The source does not train, modify the app or D-05, call a threshold-lock command, or read a sealed-test member.

## Limit

This PASS permits only the pinned seed-20261019 validation inference sweep. It does not establish baseline equivalence, a selected threshold, performance gain, or result integrity. A separate agent must independently recompute the selected cell, the 0.20 / 0.70 reference cell and the paired FP/image CI from the produced artifacts before any result report or commit. If any source, test or authorization hash above changes, this QA requires a delta review.
