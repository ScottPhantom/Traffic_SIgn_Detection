# D1-S2-R1 Owner authorization record

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`).
Recorded from the Owner's written instruction in the coordinating chat, conveyed by Claude.
Boundary: exactly one additional pilot seed, `20261019`, on NVIDIA L4. `sealed_test_accessed=false`.

## Owner instruction (verbatim)

> Hãy giao thêm cho Codex công việc train Song Song trên Colab 1 seed pilot trước.

This answered the D-05 step proposing seeds `20261019` and `20261020` with the same pilot
configuration. The Owner selected one seed first.

OWNER_AUTHORIZES_TRAINING: D1-S2-R1

The authorized `D1-S2-R1` run changes only `seed` from `20261018` to `20261019` relative to the
pilot `run_contract.json` SHA-256
`9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`. It uses the
same YOLO11s-54 pretrained weight SHA-256
`85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`, the same
train/val export, 100 epochs, patience 0, imgsz 1280, batch 4, workers 4, fraction 1.0,
`fliplr=0.0`, deterministic training and optimizer `auto`.

Sequence: fresh NVIDIA L4 runtime with `--stop-after-epoch 1`; independent live smoke QA PASS;
then a distinct NVIDIA L4 runtime resumes to epoch 100. The notebook must clone the pinned,
clean commit under `/content/Traffic_Sign_Detector`. The bundle contains train/val only.

This record does not authorize seed `20261020`, the A2 train list, a configuration change,
sealed-test access, publication, deployment, or a push to GitHub. Push needs separate Owner
permission. No validation comparison or D-05 acceptance follows from this authorization.
