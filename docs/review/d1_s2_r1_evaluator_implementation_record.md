# D1-S2-R1 common validation evaluator and paired seed CI — implementation record

Status: `SOURCE_PREPARED_NOT_RUN_ON_S2_AWAITING_INDEPENDENT_SOURCE_QA`
Date: 2026-11-06 (`Asia/Ho_Chi_Minh`)
Scope: work **a** in `docs/codex_handoff_s2_eval_lock_final_2026-11-06.md`.

## Boundary

This is source preparation and synthetic/read-only validation. No S2 inference, training, validation result, threshold lock, sealed-test access, upload or push occurred. `sealed_test_accessed=false`. The running S2 notebook and Drive state were not touched. The S2 result QA is a future prerequisite, not a result claimed here.

## New source and tests

| Path | SHA-256 | Purpose |
| --- | --- | --- |
| `detector/colab/evaluate_d1_s2_r1_common_r1.py` | `e63f63f4c3fde7e744a253929e3fe9e4b3e8a8716334571e709bc9859d207cf2` | Candidate S2 archive/manifest/best.pt attestation and common validation evaluation; pilot/bundle/scorer imported from A2 predecessor |
| `detector/m1/s2_pilot_paired_ci_r1.py` | `41893b343dec4aa93a5a735a0047f827d0ffb360cf74f38fce13e5efa1873938` | Paired 9-group, 1,000-draw seed-19 minus seed-18 CI, with fixed 0.20 operating points and exact-class mAP |
| `detector/tests/test_evaluate_d1_s2_r1_common_r1.py` | `d06f31518b0f50b6d4178c6cf583f99a2857a0c88fd655dbf1cd21aff4c5bd25` | Synthetic attestation and refusal tests, including seal, early stop, dirty checkout, governed data path, QA gate and pilot reproduction |
| `detector/tests/test_s2_pilot_paired_ci_r1.py` | `c7cb00f025def14ba9edd08ca5b2f5d67381f697535c628967ec026bd1fc10fd` | Input binding, CI QA gate, derived-key and output-shape tests |

The paired-CI source pins the evaluator byte hash. Recheck the two hashes together after any change.

## Binding and refusal path

The evaluator first requires committed work-b contract bytes (`726932db…`) and its independent QA (`e85c1ac3…`). It also requires a hash-pinned, separate S2 result-QA record with one `Verdict: PASS`, the S2 experiment, archive and manifest hashes, and `sealed_test_accessed=false`. Without these, the evaluator refuses to run.

After the prerequisite gate, the evaluator verifies the pinned A2 common-evaluator predecessor and S2 launcher/trainer. It verifies S2 archive and manifest SHA-256, the eight-file package and attestation, `D1-S2-R1`, seed 20261019, 100 epochs, successful terminal outcome, clean NVIDIA L4 checkout, pilot-equivalent train args except seed/run identity, governed export, Owner authorization, archived and live state parity, epoch-0100, and seal false. Only then does it extract the hashed `best.pt` and run the imported R3 validation method. The pilot path and its 376-image/624-box validation roster remain pinned. Outputs are write-once `s2_predictions.csv` and `comparison_s2_r1.json`.

The CI program reads only the resulting pinned CSV/JSON and the governed R3 bundle. It independently rechecks the committed work-b bytes and hash-pinned S2 result-QA PASS, plus its own A2/A3 CI and metrics source pins. It verifies used validation members against the bundle manifest, reproduces the stored operating points and AP, and rechecks pilot TP 547, FP 150, correct-class hits 457, mAP50 0.8521 and mAP50-95 0.6089. It reports agnostic recall, correct-class recall, FP/image, both mAPs, and derived keys 7/32/41 mapped to YOLO IDs 7/33/42. Its difference is **seed variation**, not evidence of an architectural improvement.

## Checks and next gate

- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_evaluate_d1_s2_r1_common_r1.py tests/test_s2_pilot_paired_ci_r1.py`: **20 passed**.
- `cd detector && uv run ruff check colab/evaluate_d1_s2_r1_common_r1.py m1/s2_pilot_paired_ci_r1.py tests/test_evaluate_d1_s2_r1_common_r1.py tests/test_s2_pilot_paired_ci_r1.py`: **PASS**.
- Pinned predecessor hash check: **PASS**, read-only.

An independent agent must review the source and record one `Verdict:` line. Even after source QA PASS, **do not execute on S2** before its completed-run result QA PASS. No S2 score is present in this record.
