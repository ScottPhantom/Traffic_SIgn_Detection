# D1-S2-R1 independent live smoke QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex QA agent
`/root/s2_source_qa`; the smoke was operated by `/root`, not this reviewer.
Boundary: read-only independent fetch and hash of the live Drive state after
the fresh NVIDIA L4 attempt. No resume, training command, Drive write, Git
push, R3 evaluation, or sealed-test opening occurred during this review.
`sealed_test_accessed=false`.

Verdict: PASS — the live fresh smoke has a verified epoch-0001 recovery state and may proceed to the separately operated resume on a distinct NVIDIA L4 runtime under the frozen D1-S2-R1 contract.

## Live state identity

- Drive run folder ID: `1qmUE-A9N3ul0XhFpkImN8dLqU9ZXvUU-`; state suffix
  `M1_D1_Colab/runs/d1_s2_seed_20261019_r1`. The folder contained
  `colab_execution.json`, `execution_attempts.jsonl`, `colab_train.log`,
  `DB_logger.db` and `recovery/`. Its recovery folder contained
  `training_outcome.json`, `latest.json` and one snapshot folder
  `epoch-0001`. No result archive is expected at this pause.
- `colab_execution.json` reports `D1-S2-R1`, `mode=fresh`, seed `20261019`,
  epochs 100, imgsz 1280, batch 4, CUDA device 0, status
  `PAUSED_FOR_RESUME`, `error=null`, completed epoch 1, and the only attempt
  as fresh/paused. It pins clean source commit
  `fc729d07664c70a8784ff735b72d7283e5261b6a`, Owner record SHA-256
  `4f394487f7c8d51c31c268414bc16aabc1baa57a41822563459489d0940d2f0c`,
  pilot contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`,
  and train/val archive SHA-256
  `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`.
  Bundle verifier recorded 5,888 files and `test_included=false`.
- The first runtime digest is
  `09684dcb15069019dda3c53be5c76bd6751c999ae93a07a310d5d7aefe61bd12`.
  It agrees across `colab_execution.json` and the sole durable attempt.
  The resume must produce a different digest; that outcome remains unknown.

## Independent byte checks

The reviewer fetched the raw Drive bytes through the connected Drive service,
streamed them independently, and recomputed SHA-256. Drive metadata alone was
not used as a hash proof.

| Live file | Bytes | Recomputed SHA-256 |
| --- | ---: | --- |
| `colab_execution.json` | 3,952 | `918924a5cc61f741d86861e7cce24034cc18e2a7e444026a2750a084eca21581` |
| `execution_attempts.jsonl` | 490 | `072612efa81416e7d0d28bee706d726800f1fd060d448f453cd56778638f6192` |
| `colab_train.log` | 221,616 | `2ae229f8ca9b1882aeaf4344cd2ac6e4fdf5f68a954c5643c87e797e483047d5` |
| `DB_logger.db` | 307,200 | `4b9e6c4284a3e27fb2046dfa1b3e4acf65d70d69f7b0787e4adefd7d5a599409` |
| `recovery/training_outcome.json` | 304 | `582a5657b28303af23a73aa8e96a6ba50d8e18af1d3c6067b6ceb033c798b6fe` |
| `recovery/latest.json` | 233 | `fbab903b39de6f9b6ac8c062e9f48ed4003b967494d03bcb49e1cc953852bb10` |
| `epoch-0001/checkpoint_manifest.json` | 2,346 | `7914707bdf5576bf2227f0072154e8a3d7fbc98148582c76b0da6651cfb1efc7` |
| `epoch-0001/run_contract.json` | 2,699 | `a8c31dfbb00cb257361011f7a43dc32a014bc89d8d5065180ea1d7d35163eac7` |
| `epoch-0001/args.yaml` | 1,914 | `ea9bdbf44935d0e70099acc13b61838a219a23906a85fd3ea3ba542fe8abdaaf` |
| `epoch-0001/results.csv` | 318 | `4f157dac99a7495bc895be864cfa039565f4c2c26678e95c74e230f9fb94ffc0` |
| `epoch-0001/weights/best.pt` | 76,222,627 | `91fbb24204ccfc3c09d1c48cb62b23ce924f9e121ab0b228edbee9699d506ea0` |
| `epoch-0001/weights/last.pt` | 76,222,627 | `91fbb24204ccfc3c09d1c48cb62b23ce924f9e121ab0b228edbee9699d506ea0` |

`latest.json` names `epoch-0001`, matches the manifest's recomputed SHA-256
and binding digest `3795215c55c563962654d6b8c8784b581380d6bc7ee975d99ca72d9b0d8e9e43`.
The reviewer recomputed that binding digest using the predecessor's canonical
Python JSON serialization and matched it. All five snapshot payload file sizes
and hashes match the manifest. `results.csv` has the header plus one epoch-1
row; `training_outcome.json` independently says paused, epoch 1, resumed false,
seal false.

## Configuration, log and sealed boundary

- The live snapshot `run_contract.json` records `git_dirty_files=0`, pinned
  commit A, CUDA, `gpu_name=NVIDIA L4`, PyTorch `2.14.1+cu130`, Ultralytics
  `8.4.172`, pretrained weight SHA-256
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`,
  governed export manifest SHA-256
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`,
  and the Owner/pilot pins above.
- Independently comparing the live `train_args` with the local pilot artifact
  gave the same 16-key set and changed keys exactly `{name, seed}`. The `name`
  is the new run identity; seed is `20261019` instead of `20261018`. The
  `data` path, `project` path, 100 epochs, patience 0, imgsz 1280, batch 4,
  workers 4, fraction 1.0, deterministic `True`, pretrained `True` and
  `fliplr=0.0` match. `args.yaml` explicitly says `optimizer: auto` and the
  same seed/configuration. The train/val split digests and D-05 gate object
  also match the pilot.
- The live text log records `Using 3712 train, 376 val images for fraction=1.0
  at imgsz=1280`, CUDA:0 NVIDIA L4, clean Git environment, a false sealed
  flag and terminal `PAUSED_FOR_RESUME`. SQLite `PRAGMA integrity_check` was
  `ok`; all 1,238 SQLite log messages equaled all 1,238 text-log lines in
  order. The execution record, outcome, snapshot contract and bundle binding
  all state false/test-excluded as applicable. The sealed digest in the
  checkpoint binding is an identity pin; this review did not fetch or score
  sealed payload. No sealed-test access log was present in the listed run
  state. A repository-global access-log absence was not independently probed.

## Next gate

The coordinating operator may disconnect this runtime and resume with the
same notebook and state on a **new** NVIDIA L4 runtime at exactly
`/content/Traffic_Sign_Detector`. This QA does not establish a distinct
second runtime, epoch 100, result archive, validation scores, D-05 acceptance,
or any sealed-test permission. Trainer/launcher refusal requires stopping;
the QA-passed source and notebook should remain unchanged.
