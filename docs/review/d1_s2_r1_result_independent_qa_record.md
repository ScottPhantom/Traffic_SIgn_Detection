# D1-S2-R1 completed-run independent result QA

Checked: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex QA agent
`/root/s2_source_qa`. This reviewer did not operate either Colab training leg
or copy the Drive state. Boundary: read-only artifact and attestation checks.
No training, inference, R3 validation scoring, threshold lock, push, or sealed
payload access occurred in this review. `sealed_test_accessed=false`.

Verdict: PASS — the 100-epoch D1-S2-R1 run, two-runtime recovery, archive, checkpoint, logs and offline attestation verify; the result may enter the separately gated common R3 validation evaluator.

This is a run-integrity verdict. It is not a validation metric, seed comparison,
D-05 acceptance, test result, deployment claim, or safety validation.

## Authority and copy provenance

- Frozen source/Owner/contract commit A:
  `fc729d07664c70a8784ff735b72d7283e5261b6a`; notebook commit B:
  `192939f9fba60cd6ec3c7c61f740c1ff4758cf92`.
- Fresh live-smoke QA record SHA-256:
  `0976466a11f3a90e7fbd1e9eb76e398686fa1c45b835e1d4c1f1fcb45974888b`,
  with epoch-1 checkpoint binding
  `3795215c55c563962654d6b8c8784b581380d6bc7ee975d99ca72d9b0d8e9e43`.
- The synchronized Drive state is
  `M1_D1_Colab/runs/d1_s2_seed_20261019_r1` (Drive folder ID
  `1qmUE-A9N3ul0XhFpkImN8dLqU9ZXvUU-`). The ignored local copy is
  `tmp/d1_s2_seed_20261019_r1_state/`. The operator's
  `copy_integrity_manifest.json` hashes to
  `a983d014e99f6a11708cf2f452913605521ddbf18c2f5c84f6465d703bc943a8`.
  I independently rehashed all 14 copied files and the synchronized Drive
  source paths: every size and SHA-256 equals both the before and after entries
  in that manifest. I separately streamed the archive, result manifest and
  execution JSON from the connected Drive service and recomputed their SHA-256;
  all three equal the local source and copy hashes below.
- `graft check .` was OK. The current checkout has unrelated dirty work, which
  was preserved. No source or notebook file was edited in this QA.

## Result archive and manifest

| Artifact | Bytes | Recomputed SHA-256 |
| --- | ---: | --- |
| Result archive `<run>_result.tar.gz` | 41,303,680 | `c9367603c67650968514d00699d73bc0202fb7e1b69c4a6af413b34f60b2164e` |
| Result manifest `.tar.gz.manifest.json` | 1,986 | `b771a58996f75257f2a58adcb684273dff637be28b5d66606a66a721694e172e` |
| `colab_execution.json` | 4,485 | `61c3e5bc22f63cc08adc7fc3852e74096d1a02d84eed890ab66b212957c57966` |
| `execution_attempts.jsonl` | 973 | `40a144b49b427eb7ca258e55845e73d918cf007b59d1814c903617788d55ba27` |
| `colab_train.log` | 18,728,832 | `ef218102bc92a0fbab85c4c3a3898da551e28f344c912848e35853eb80089d20` |
| `DB_logger.db` | 24,813,568 | `21b980ff5b6f4e802f92d371cd977e59f236eb224148ce30f28f6fdbb9d99454` |

The manifest's archive name and hash match the actual file, its status is
`D1_COLAB_RESULT_PACKAGE`, terminal outcome `SUCCEEDED`, and seal flag false.
The archive has exactly eight unique regular members; no link or duplicate
member was observed. The member set equals the manifest set. Streaming each
member independently produced its declared size and SHA-256:

| Archive member | Bytes | SHA-256 |
| --- | ---: | --- |
| `<run>/weights/best.pt` | 19,289,370 | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` |
| `<run>/weights/last.pt` | 19,289,370 | `05935508454e77150a6accf15248e8d6e44ad6ce76f423b17155364f6c3ea40c` |
| `<run>/results.csv` | 12,672 | `237a6efd574e5d49c4c4611f09c2344ae75885d600c3bd70a069232f5860f4c0` |
| `<run>/args.yaml` | 2,099 | `fe7c963aa829982aa74a9776d91840c5593bdb4e36cc3fdd9314e503a520931e` |
| `<run>/run_contract.json` | 3,253 | `1f1c3f7f2fdeb15467aa69ddbe012b880b10324b5b505d772058ebd7e96c2050` |
| `colab_logs/colab_execution.json` | 4,485 | `61c3e5bc22f63cc08adc7fc3852e74096d1a02d84eed890ab66b212957c57966` |
| `colab_logs/colab_train.log` | 18,728,832 | `ef218102bc92a0fbab85c4c3a3898da551e28f344c912848e35853eb80089d20` |
| `colab_logs/DB_logger.db` | 24,813,568 | `21b980ff5b6f4e802f92d371cd977e59f236eb224148ce30f28f6fdbb9d99454` |

The archived log/execution/DB members are byte-identical to the selected
Drive-state files. The archived `results.csv` and `args.yaml` are byte-identical
to the epoch-100 checkpoint copies. The archived weights are final result
weights; the recovery snapshot weights are larger full checkpoints and have
their own hashes below. The manifest binds run attestation SHA-256
`807ba02a87da944e804fc61b314618bb77692c727fb577eec5f7a6395442c80c`.

## Two-runtime execution and checkpoint

- `colab_execution.json` has `experiment=package=D1-S2-R1`, `mode=resume`,
  `status=SUCCEEDED`, `error=null`, seed 20261019, frozen 100 epochs, clean
  checkout commit A and `sealed_test_accessed=false`. The nested training
  outcome and `recovery/training_outcome.json` both say `COMPLETED` at epoch
  100, resumed true, seal false. The 100-row `results.csv` runs continuously
  from epoch 1 through epoch 100, so this is not an early-stop outcome.
- The durable JSONL contains exactly two records and equals the embedded
  `execution_attempts` array: fresh `PAUSED_FOR_RESUME` at epoch 1 from
  04:28:53–04:32:34 UTC, then resume `SUCCEEDED` from
  04:44:11–09:51:50 UTC. Their runtime digests are respectively
  `09684dcb15069019dda3c53be5c76bd6751c999ae93a07a310d5d7aefe61bd12`
  and `0bd5a87026dc941c8c51cea20aea2030a008d32e80c69fc7ab55ebe4f8139640`.
  They differ and the intervals do not overlap. Both have the same run binding
  `36c67fb6435eae8042fd7a6a90807af7c0ac98105679ef89f1e39e84ae1bee85`
  and checkpoint binding
  `3795215c55c563962654d6b8c8784b581380d6bc7ee975d99ca72d9b0d8e9e43`.
  Fresh and resume log sections independently show `gpu_name: NVIDIA L4`
  and CUDA:0 `(NVIDIA L4, 22563MiB)`. No repair-packager marker is present.
- `recovery/latest.json` names `epoch-0100` and pins the checkpoint manifest
  SHA-256 `8b40348172f5df9c8e6bcc6abde48845418a2e196f0ce6a38f11a07c0cf02e90`,
  which equals the rehashed file. The manifest status is `RECOVERABLE`,
  completed epoch 100, and its canonical binding SHA-256 equals both attempts
  and the independent epoch-1 smoke record. All five snapshot files match
  their manifest byte lengths and hashes: full checkpoint `best.pt`
  `607f242b2eed3daa641e06ab5a383923393a3949e8d72ebbf728c8375b3ca039`,
  `last.pt` `2674dde04701ba4a09401ba3bf5c1836a14bf038869f1692c178e4df7fd45e44`,
  `results.csv` `237a6efd…f0c0`, `args.yaml` `fe7c963a…31e`, and
  `run_contract.json` `a8c31dfb…3eac7`.

## Pilot configuration, logs and seal

- The archived trained run contract records `git_dirty_files=0`, NVIDIA L4
  CUDA, Ultralytics `8.4.172`, pretrained `yolo11s.pt` SHA-256
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`,
  Owner authorization SHA-256
  `4f394487f7c8d51c31c268414bc16aabc1baa57a41822563459489d0940d2f0c`,
  pilot contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`,
  and governed export manifest SHA-256
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`.
  The authorization record itself rehashes to that pin. The 5,888-file
  train/val bundle binding states `test_included=false`; its archive SHA-256
  matches the frozen training bundle.
- I independently compared the archived train-argument dictionary with the
  pilot `run_contract.json` (whose SHA-256 is pinned above). Both have the
  same 16-key set; the only differences are new run `name` and seed
  `20261018→20261019`. The `project` and `data` paths are identical. The
  governed data contract and D-05 gate object also match exactly. The
  checkpoint `args.yaml` records the resolved `optimizer: AdamW`, as does
  the pilot; the passed `train_args` contain no optimizer override. It has epochs 100,
  patience 0, imgsz 1280, batch 4, workers 4, fraction 1.0,
  `fliplr=0.0` and deterministic true.
- SQLite `PRAGMA integrity_check` returned `ok`. All 97,156 database log
  messages equal all 97,156 text-log lines in order. Both leg sections have
  `Using 3712 train, 376 val images for fraction=1.0 at imgsz=1280`.
  A targeted scan found zero traceback headers and zero path candidates
  containing a test component. The archived result member paths are the
  five run files plus three logs; none is a sealed path. The execution,
  training outcome, archived run contract, result manifest and bundle binding
  record false/test-excluded flags as applicable. The sealed digest in the
  checkpoint binding is an identity pin, not payload access. No sealed
  test file was opened or scored here.

## Offline evaluator attestation and next gate

From `detector/` with `PYTHONPATH=.:colab`, I called only
`evaluate_d1_s2_r1_common_r1.verify_predecessors()` and
`verify_candidate(args)` on the pinned archive, manifest, local state,
authorization record and checkout. Eight predecessor source hashes passed.
The offline candidate verifier returned run-contract SHA-256
`1f1c3f7f2fdeb15467aa69ddbe012b880b10324b5b505d772058ebd7e96c2050`,
best-weight SHA-256 `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce`,
attestation SHA-256 `807ba02a87da944e804fc61b314618bb77692c727fb577eec5f7a6395442c80c`,
and `training_outcome=COMPLETED`. I did not call `run()` or `main()` and did
not load the weights for prediction.

The separately QA-passed S2 evaluator may now proceed only under its own
prerequisite gate and the post-training handoff §3. This result QA does not
establish R3 scores, seed variation, confidence threshold lock or D-05 GO.
