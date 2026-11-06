# Independent source QA — D1-S2-R1 common validation evaluator and paired seed CI

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`)
Reviewer: separate Codex QA agent `/root/s2_eval_source_qa`; not the source author or executor.
Scope: work **a** of `docs/codex_handoff_s2_eval_lock_final_2026-11-06.md`, source preparation only.

Verdict: PASS — source preparation only; S2 result QA and validation execution remain pending.

## Evidence reviewed

- `detector/colab/evaluate_d1_s2_r1_common_r1.py`, SHA-256 `e63f63f4c3fde7e744a253929e3fe9e4b3e8a8716334571e709bc9859d207cf2`.
- `detector/m1/s2_pilot_paired_ci_r1.py`, SHA-256 `41893b343dec4aa93a5a735a0047f827d0ffb360cf74f38fce13e5efa1873938`.
- Tests `detector/tests/test_evaluate_d1_s2_r1_common_r1.py` and `detector/tests/test_s2_pilot_paired_ci_r1.py`, SHA-256 `d06f31518b0f50b6d4178c6cf583f99a2857a0c88fd655dbf1cd21aff4c5bd25` and `c7cb00f025def14ba9edd08ca5b2f5d67381f697535c628967ec026bd1fc10fd`.
- Implementation record `docs/review/d1_s2_r1_evaluator_implementation_record.md`; its four source/test hashes match the bytes reviewed. Work-b contract and its QA are committed at HEAD `9d3f230` and match the evaluator pins `726932db…` and `e85c1ac3…`.
- Compared against the QA-passed A2 evaluator/CI, S2 launcher/trainer, R3 bundle binding and work-b contract. The pinned A2 evaluator, S2 launcher/trainer, A2/A3 CI modules, metrics and R6 archive verifier hashes match the current checkout.

## Review result

1. The S2 evaluator reuses the A2/A3 validation inference and common scorer, keeps the governed R3 bundle and pilot side, and changes candidate identity to `D1-S2-R1`, seed 20261019. It requires explicit archive, manifest, Owner authorization and checkout hashes. The offline attestation matches the S2 launcher's formula in a synthetic test. It refuses non-success, early stop, incomplete epoch 100, dirty checkout, changed train arguments, invalid governed data path, seal violation and mismatched authorization. The archived and live state checks must both pass before inference.
2. Before candidate validation, the evaluator independently requires work-b contract/QA bytes committed in Git and a separate hash-pinned S2 result-QA record with one PASS verdict binding the archive/manifest and `sealed_test_accessed=false`. The standalone paired-CI command repeats that gate and verifies the evaluator's prerequisite hashes. This closes the initially observed early-scoring path.
3. The paired CI uses 1,000 draws at seed 20261018 with intact nine D-02 groups and the same draw for S2 and pilot. It reports fixed-confidence 0.20 agnostic and correct-class recall, FP/image, both exact-class mAPs and derived keys 7/32/41 mapped to YOLO IDs 7/33/42. Pilot reproduction from pinned validation data was observed in the focused test: TP 547, FP 150, correct-class hits 457, mAP50 about 0.8521 and mAP50-95 about 0.6089. The output labels the contrast as seed variation.
4. Local gate rerun: `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_evaluate_d1_s2_r1_common_r1.py tests/test_s2_pilot_paired_ci_r1.py` passed **20/20**; scoped Ruff on the same four new files passed. No S2 inference or training was run by this QA.

## Limits and handoff gate

This verdict covers source structure, synthetic refusal tests and a read-only pilot anchor. It does **not** validate a completed S2 result, an S2 score, the CI interval's empirical behavior on S2, a threshold lock, or safety/deployment. When S2 completes, its archive/hash/log/state must first pass independent result QA; only then may the prepared evaluator run. A later independent result QA must check the generated S2 comparison and CI. `sealed_test_accessed=false`; the sealed test was not opened, listed, exported or scored.
