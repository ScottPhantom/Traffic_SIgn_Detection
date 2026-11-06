# Codex handoff: independent QA of the D1 final-evaluation R4 result — 2026-11-07

- Writer: Claude, coordinating session.
- Branch `yolo11n-dual-track-r1`.
- QA target: `docs/review/d1_final_evaluation_r4_result_report.md`
  (status `AWAITING_INDEPENDENT_RESULT_QA`).
- The presentation is today; prioritise speed and correctness.

## 0. Boundaries

- **Do not run the scorer again**: no `execute`, no new inference on the test. The access log must
  stay at 4 lines, SHA-256 `4ae685690893dc1520f6a9356bf2d2e74c3d218c64204ce022b8aff4836180e0`.
- QA may **read** these, which is necessary to recompute and is covered by the R4 opening:
  - the saved predictions in `results/experiments/d1_final_evaluation_r1/`;
  - the test labels already exported in `data/processed/m1_yolo/labels/test` and `data_test.yaml`.

  Do not change or copy them elsewhere.
- Do not change the gates, the threshold, the labels or the report (except through a separate QA
  record).
- No push.
- The QA must be done by an agent that did not write the report or run the scorer, and the record must
  have exactly one `Verdict:` line.

## 1. Checks

1. **Hashes.** The 6 output files, the access log and the opening approval match the hashes in the
   report.
2. **Recompute independently** from the 2 prediction files, using a separate greedy IoU ≥ 0.50 matcher
   and the test labels:
   - TP/FP per seed: 1552/410 and 1535/359;
   - recall and FP/image, per seed and as the two-seed mean;
   - recall of the 10 critical classes.

   Also recompute mAP50/mAP50-95 with the QA-pinned AP scorer (`evaluate_cascade_b0_r1.average_precision`),
   or state clearly that it was not recomputed.
3. **Verdicts.** Check every gate verdict:
   - FP fails **both** markers, 0.40 and 0.30;
   - all 10 critical classes fail;
   - latency p95 47.68 ms passes;
   - the overall verdict is FAIL.
4. **Disclosures.** The report has the label asymmetry, attempts 1–3 (including that attempt 3 made
   predictions and lost them unseen), and the CI limits.
5. **Wording.** The report does not attribute a gate miss to label noise and makes no safety claim.
   The validation → test drop is marked as cause not established.

## 2. Output

- `docs/review/d1_final_evaluation_r4_result_independent_qa_record.md`, with one `Verdict:` line.
- If PASS: commit that record together with the report
  (`docs/review/d1_final_evaluation_r4_result_report.md`, if not yet committed). Report the SHA to the
  Owner.
- If there is an error: write it in the QA record; do not edit the report.
