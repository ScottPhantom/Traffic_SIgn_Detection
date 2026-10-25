# YOLO11n N1 R1 live smoke failure record

Date: 2026-10-25 (Asia/Ho_Chi_Minh)  
Status: `TERMINAL_FAILURE_PRESERVED_REPAIR_REQUIRED`  
Scope: N1 fresh smoke only; train/validation data only.

## Immutable inputs

- Source checkout: `45b7b1fab606032fcfb2956d0207171ae8b4c7f6`.
- Notebook checkout: `5ef9b2da16e4a2f8fc0ba03c9ee9226e7eab45f5`.
- Bundle SHA-256: `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05`.
- Bundle manifest SHA-256: `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.
- Original runner SHA-256: `b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753`.

## Observed execution

- NVIDIA L4 preflight passed and the bundle was extracted and verified.
- The fresh attempt used runtime digest
  `46e631e78638384ad4459d5da3dfa90c473f32e648915a4f643a1fdf8cebc508`.
- Ultralytics completed epoch 1 locally, but checkpoint publication failed closed with
  `checkpoint run identity differs`.
- Root cause: the original runner used run name `YOLO11N_N1_detector`, while the inherited
  checkpoint store accepts only `D1_[A-Za-z0-9_.-]+`.
- The failed state is preserved at
  `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1`; it has no trusted `latest.json` and must never
  be resumed or promoted to a smoke PASS.

## Preserved evidence

- `colab_execution.json`: SHA-256
  `5a34833342777d85ea2de26d91bde18e3f301e92684359626389ecbd3feaf4b1`;
  terminal status `FAILED`, seal false.
- `train.log`: SHA-256
  `3a0550fb37b9a11899b38a13d62d674c2a07b6f43f2000615b67904222988586`.
- Partial checkpoint manifest: SHA-256
  `b40fff8224631136bca53c05d005907317b9b586fd5d7e700a1f28caf39e1dfd`;
  its `.partial` generation is evidence only and is not recoverable.

## Repair boundary

The append-only R1-R1 repair must use a new state path,
`M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`, and a checkpoint-store-compliant run name.
It must pass source QA before a new notebook is built or executed. The failed R1 state remains
unchanged. No long training is authorized before the two-runtime smoke and independent artifact QA
both pass.

`sealed_test_accessed=false`; no sealed-test path was opened.
