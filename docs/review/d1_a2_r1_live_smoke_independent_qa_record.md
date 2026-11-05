# D1-A2-R1 live smoke independent QA record

Checked: 2026-11-05 22:57 (`Asia/Ho_Chi_Minh`).
Reviewer: separate Codex agent `/root/a2_notebook_qa`; this agent did not operate the L4 smoke.
Boundary: read-only result QA of the fresh epoch-1 smoke. No training, resume, Colab UI edit, source edit, commit, push, weight upload, validation evaluation, or sealed-test access.

Verdict: PASS — the live fresh smoke reached a hash-valid `epoch-0001` checkpoint and `PAUSED_FOR_RESUME`; the independent smoke gate for a distinct L4 resume is satisfied.

## Evidence source and state

- Read the actual Google Drive folder `M1_D1_Colab/runs/d1_a2_seed_20261018_r1` through the connected Drive API: [state folder](https://drive.google.com/drive/folders/1-gcR1zmbH86wtAmwUi12C2Ix6bL8W9pu). Read `colab_execution.json`, `recovery/latest.json`, `recovery/training_outcome.json`, the `epoch-0001` manifest and `run_contract.json` from that cloud folder. Streamed the cloud checkpoint files, SQLite database and text log to SHA-256 without modifying them. The Mac Drive sync copy matched those hashes and was used for read-only SQLite and log-parity checks. The Colab MCP browser connection was unavailable; this verdict uses direct Drive cloud artifacts, not a notebook UI status claim.
- `colab_execution.json` SHA-256 `225b9b3a94735a4880227f042cc545984da74b5cb9d2e8c4f0dcff43044ad30c`: `experiment=package=D1-A2-R1`, `mode=fresh`, `status=PAUSED_FOR_RESUME`, `error=null`, `training_outcome.completed_epoch=1`, `sealed_test_accessed=false`. It records the fresh attempt from 2026-11-05 15:46:09 to 15:50:35 UTC.
- `recovery/latest.json` SHA-256 `035ffe607be95c8b7be8b3a4c432a19874e8a057a324d68082dceb5c64baddb0` points to `epoch-0001`, binding SHA-256 `873163a4d18f4ca7ebb995739eb2a79c29028ca85e6d89de626eb1b2de71b06d`, manifest SHA-256 `c7ce3f7ba5bad811ac01c1ab0dee659406fdf04de95c9d218246e515480ec72d`.
- The cloud `checkpoint_manifest.json` itself hashes to the pointer value. It declares `completed_epoch=1`, `status=RECOVERABLE`, five files, and the same binding SHA. The file contents streamed directly from Drive match all five declared sizes and SHA-256 values:

| Checkpoint file | Bytes | SHA-256 |
| --- | ---: | --- |
| `weights/last.pt` | 76,222,627 | `aaf3cf8904bca0a2dbd872a09be2fd67a5705c202e585694e823be8d75ccc071` |
| `weights/best.pt` | 76,222,627 | `aaf3cf8904bca0a2dbd872a09be2fd67a5705c202e585694e823be8d75ccc071` |
| `results.csv` | 315 | `436fa60926e231fb7edb6328046587f0806b4f35d2c733e3d5eea2c7abc52d17` |
| `args.yaml` | 1,926 | `b4ba8813ed7e35baaa3ae3a3f7d930e4e63bd3a72b4d7732312b042f405f5da9` |
| `run_contract.json` | 3,658 | `084dc0898576daf303e31f38a7c49a4c529cb0c3a296394784e5929cf2e8f677` |

## Contract and runtime checks

- The checkpoint binding names commit A `f3f7571794a5db04ad302fecf8014546ec1eb255`, approved model hash `85a76fe8…502d5`, A2 rule `A2_ALL_975_RAW_AND_WP35`, list hash `90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2`, roster hash `0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3`, 4,687 entries, and authorization hash `1a11b283da34848dc873b577b42240a5182b795654f5a3db9349369ae78221c9`.
- The snapshot `run_contract.json` reports `environment.git_dirty_files=0`, `environment.git_commit=f3f7571794a5db04ad302fecf8014546ec1eb255`, `gpu_name=NVIDIA L4`, `runtime_backend=cuda`, `ultralytics=8.4.172`, and `sealed_test_accessed=false`.
- Compared the snapshot `train_args` key for key with the pinned pilot `run_contract.json` (SHA-256 `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`): the only differences are `data` (A2 runtime YAML) and `name` (new run identity). `a2_data.data_yaml_changed_keys=["train"]`; seed 20261018, 100 epochs, imgsz 1280, batch 4, workers 4, fraction 1.0, patience 0, device `0`, deterministic, pretrained and `fliplr=0` remain as frozen.
- `colab_train.log` streamed from Drive has SHA-256 `6ad9c6319fb524e5b550019d34a6c93108f8e34c3e03c694b0926c6ad041f3bc` and explicitly says `Using 4687 train, 376 val images for fraction=1.0 at imgsz=1280`; it ends `Terminal outcome PAUSED_FOR_RESUME`. `DB_logger.db` streamed SHA-256 is `232826411b0ef769c3ba2dd02b5bfeaafb13043d4eb036fe39c6300b567bb5de`; SQLite `PRAGMA integrity_check=ok`, and all 1,489 database log messages equal all 1,489 text-log lines in order.
- The fresh runtime digest is `df394f3746757031cbe274863c38cb8b8000d4a81a69ac7e547d29356f78c80b` (`sha256:d1-runtime-v1:tag+linux-boot-id`). The next `resume` attempt must use a different NVIDIA L4 runtime digest and the same hash-valid checkpoint binding.
- `sealed_test_accessed=false` in execution, training outcome and run contract; the extracted bundle binding says `test_included=false`. The sealed split was not opened or scored. The Drive folder has no result archive yet, as expected after epoch 1.

This PASS applies only to the smoke and permits the authorized distinct-runtime `MODE=resume` leg. It is not an epoch-100 result, metric claim, D-05 acceptance, or validation of real vehicle behavior.
