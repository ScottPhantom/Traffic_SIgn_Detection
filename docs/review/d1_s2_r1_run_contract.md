# D1-S2-R1 frozen run contract

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Status: source implementation pending independent QA.
`sealed_test_accessed=false`.

## Authority and single change

- Pilot `run_contract.json` SHA-256:
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`.
- Pilot run:
  `D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2`.
- Pretrained `yolo11s.pt` SHA-256:
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`.
- Governed export manifest SHA-256:
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`.
- Train/val bundle archive on Drive: `m1_colab_train_val_backend_r1.tar.gz`, 766,226,800 bytes,
  SHA-256 `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`.
  Sidecar SHA-256 `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2`.
  These are the pilot/A2 train/val-only bundle pins, not a new export. The bundle's embedded
  manifest and the governed export verifier must pass on Colab.

Train arguments must have the exact pilot key set. After excluding only `name` and `project`
(run identity), the sole permitted differing value is `seed`: `20261018` to `20261019`.
In particular, `data` stays the pilot export `data.yaml`, not the A2 list. `optimizer` is
absent from the passed train-args dictionary, so Ultralytics 8.4.172 uses its default `auto`.
The inherited `contract.check_contract()` binds the same train/val export and the sealed
test digest, without opening the sealed payload.

Frozen values: YOLO11s 54 classes; 100 epochs; patience 0; imgsz 1280; batch 4;
workers 4; fraction 1.0; `fliplr=0.0`; deterministic `True`; device `0` on NVIDIA L4;
pretrained `True`; tag `s2_r1`; `sealed_test_accessed=false`.

## Execution gates

1. A repo-relative, SHA-matching Owner record with the exact `D1-S2-R1` authorization line
   must be present in the clean checkout before any state is written.
2. Independent source QA PASS, then commit A with source, tests, contract, authorization and QA.
3. Notebook pins commit A, clones it clean at `/content/Traffic_Sign_Detector`; independent
   notebook QA PASS, then commit B.
4. Push only with separate Owner permission. Fresh L4 smoke stops after epoch 1. Independent
   QA must read the live Drive artifacts, confirm a clean checkout, the 3,712/376 train/val log,
   exact pilot train args except seed/run identity, and `sealed_test_accessed=false`.
5. Only after smoke QA PASS, resume in a distinct L4 runtime to epoch 100. Refusal is a stop;
   no in-place repair of QA-passed source. The execution record and handoff carry archive,
   manifest, weight, results CSV and runtime digest hashes. Claude owns result QA and common
   validation scoring; this run does not score R3 or compare with the pilot.

No sealed-test export, opening or scoring. No seed `20261020`. No weights or data in Git.
