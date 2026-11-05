# D1-A2-R1 Owner authorization record

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`), about 22:30
Recorded by: Claude Code (Opus 5.5), coordinating session, on the Owner's written instruction in chat.
Boundary: this record authorizes one L4 training run of D1-A2-R1 only. It is not a result, not a
D-05 acceptance, and not a sealed-test authorization. `sealed_test_accessed=false`.

## 1. Owner instruction (verbatim, from chat)

Asked about the step "Làm notebook A2, cho qua QA, commit", the Owner replied:

> Hãy giao cho codex làm, và train trong đêm nay.

## 2. What is authorized

OWNER_AUTHORIZES_TRAINING: D1-A2-R1

- **Experiment.** `D1-A2-R1`, as frozen in `docs/review/d1_a2_r1_run_contract.md`
  (SHA-256 `1ce153656f2c6c7a7700bdbf57f4d9c1205184ef07bf18a0fd912056e2f396e1`).
- **D-A2-1 choice.** All 975 images, rule id `A2_ALL_975_RAW_AND_WP35`, which is the implemented
  variant. The 339-frame variant is not authorized by this record.
  - Train list SHA-256: `90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2`
  - Roster SHA-256: `0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3`
  - Local list manifest SHA-256 (informational): `12f09435a923cfe9e11c6c62f63d1c9906e9840d75ed2908df755bc30b110cbd`
- **Configuration.** Exactly the contract §2 values: YOLO11s 54 classes, seed `20261018`,
  100 epochs, patience 0, imgsz 1280, batch 4, workers 4, fraction 1.0, CUDA device 0,
  `fliplr=0.0`. The train list is the single change from the pilot.
- **Hardware.** NVIDIA L4 on Google Colab.
- **Sequence (smoke first).**
  1. `mode=fresh` with `--stop-after-epoch 1`.
  2. Independent smoke QA of the live Drive artifacts, with verdict PASS.
  3. `mode=resume` on a distinct runtime, without a stop boundary, to epoch 100.
- **Operator.** Codex may operate the notebook and supervise the run. Independent QA steps must be
  done by a session or agent that did not write or operate the reviewed step.

## 3. What is not authorized

- Opening, exporting or scoring the sealed test `afa03d4b…`.
- Any change to D-05 gates, locked thresholds, the train list, the configuration or QA-passed
  source files. A source change needs a new contract, source QA and a new authorization.
- A second seed, the 339-frame variant, or a re-run chosen after seeing A2 validation results.
- Upload, publication or deployment of the A2 weights. Push to GitHub is a separate Owner decision.
- Any claim that A2 beats the pilot before result QA and the contract §4 evaluator.

## 4. Classification

- Verified artifact: the hashes in §2, read from the run contract and the source QA record.
- Proposal: none.
- Unknown: the real L4 time; the contract estimates about 5 L4-hours.
