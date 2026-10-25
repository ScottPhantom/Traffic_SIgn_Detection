# YOLO11n N1 R1-R3 long-resume contract

Status: **PROPOSED SUCCESSOR — SOURCE QA REQUIRED BEFORE EXECUTION**  
Date: 2026-10-25 (Asia/Ho_Chi_Minh)

## Objective

Resume the QA-passed `YOLO11N-N1-R1` one-class detector from the recoverable epoch-0002
checkpoint and train through epoch 100 on one NVIDIA L4. Reuse the existing CompactCNN and
VGG16-54 classifiers; do not retrain either classifier in this run.

## Immutable inputs

- Owner configuration authority:
  `docs/review/yolo11n_dual_track_r1_owner_decision_record.md`, SHA-256
  `b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c`.
- Train/validation archive SHA-256:
  `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05`.
- Archive manifest SHA-256:
  `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.
- Official `yolo11n.pt` SHA-256:
  `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Composite source-QA SHA-256:
  `5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a`.
- Live smoke independent-QA SHA-256:
  `2c1ab19b14456e75f37c454cb619c2dbad1509e1e8eb63a30bc897e603415eb4`.
- Machine-readable smoke proof:
  `docs/review/generated/yolo11n_n1_r1_r2_smoke_qa_proof.json`; its SHA-256 is pinned by the
  successor notebook after this contract and proof are committed.
- Drive state:
  `/content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`.
- Recovery pointer before long execution: `epoch-0002`, SHA-256
  `ed42322f480030cd05a5f1bffb30731dad9a75eba5e158883535e078c6debb6a`.

## Frozen execution

- Runner: `detector/colab/run_yolo11n_n1_r1_r1.py`, stage `detector`.
- `mode=resume`; omit `--stop-after` so the frozen target remains 100 epochs.
- Seed `20261018`; image size `1280`; batch `4`; `fliplr=0.0`; NMS IoU `0.70`.
- Exact one-GPU requirement: NVIDIA L4.
- Input remains train/validation only. No test export, `--final-eval`, test split or sealed-test
  path is permitted.
- The runner must validate the source-QA record, machine-readable smoke proof, epoch-0002
  checkpoint binding, state path, manifest and official weight before recording a long ATTEMPT.
- Checkpoints, SQLite log, text log, execution state and final result archive/manifest remain on
  Drive. Resume after an interruption must preserve prior attempts and use the latest valid
  checkpoint; it must not restart from epoch 1.
- `worker_rng_exact_replay=false` remains an explicit evidence limitation.

## Acceptance before execution

Independent source/notebook QA must confirm:

1. the proof exactly matches the QA-passed epoch-0002 state and both runtime digests;
2. the notebook pins an immutable source commit containing this proof and the unchanged runner;
3. the command parses as `mode=resume`, `stop_after=None` and cannot reach test/sealed-test code;
4. altered proof, checkpoint pointer, manifest, state path, source-QA hash, GPU type or config
   fails closed;
5. all scoped Ruff, tests, lock and Graft checks pass.

Only after that independent verdict is PASS may the long-resume cell be executed. This contract
does not authorize validation evaluation, threshold selection, sealed-test access, publication,
deployment or a safety claim.
