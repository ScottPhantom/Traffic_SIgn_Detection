# D1 checkpoint/resume R3 two-runtime L4 smoke report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Owner account: `tainguyentan0908@gmail.com`  
Notebook: `https://colab.research.google.com/drive/1sdUdPoIfjTC3paUAHydOvlKL9AW5uEtK`  
Notebook code pin: `b9ce31f7278e41f51f6bd7430c2f97f653321618`  
Run label: `checkpoint_smoke_seed_20261018_r2`

## Scope and verdict

This record reports the live two-runtime NVIDIA L4 checkpoint/recovery smoke requested before the
100-epoch D1 pilot. It covers only train/val data and the two-epoch recovery drill. It does not
authorize the 100-epoch pilot and does not access the sealed test.

PM verdict: **PASS, awaiting independent QA**.

## Runtime separation and timeline

The first runtime completed epoch 1 and wrote a verified Drive checkpoint. Before the resume leg,
Colab showed the prior runtime as absent: the disconnect/delete command was disabled, and after a
save/reload the connection control explicitly offered a new L4 runtime. A new NVIDIA L4 runtime was
then allocated. Only the notebook line `MODE = "fresh"` was changed to `MODE = "resume"`.

The append-only `execution_attempts.jsonl` readback contained exactly:

| Leg | Started UTC | Finished UTC | Status |
| --- | --- | --- | --- |
| fresh | 2026-10-20T18:11:36+00:00 | 2026-10-20T18:15:20+00:00 | `PAUSED_FOR_RESUME` |
| resume | 2026-10-21T00:10:15+00:00 | 2026-10-21T00:14:20+00:00 | `SUCCEEDED` |

These correspond to 01:11:36–01:15:20 and 07:10:15–07:14:20 on 2026-10-21 in
Asia/Ho_Chi_Minh.

## Recovery evidence

- The new runtime mounted Drive and returned
  `{'mounted_bundle_preflight': 'PASS', 'source': 'verified_drive_parts', 'mode': 'resume'}`.
- The preflight found `recovery/latest.json` before the runner started.
- Checkout readback was clean at exact commit
  `b9ce31f7278e41f51f6bd7430c2f97f653321618`.
- The emitted command contained `--mode resume`, `--epochs 2`, seed `20261018`, image size `1280`,
  batch `4`, device `0`, and no fresh-only `--stop-after-epoch 1` argument.
- `training_outcome.json` readback reported `resumed=true`, `completed_epoch=2`,
  `status=COMPLETED`, and `sealed_test_accessed=false`.
- `recovery/latest.json` advanced from the fresh leg's `epoch-0001` to `epoch-0002`, with binding
  SHA-256 `7174618c578953e2c144700403c0652efaa508c61272c7fbaaac4a76e901c393` and checkpoint
  manifest SHA-256 `c46213dcc34ac6072fce91b5e4d60df7edc5696b82a2318556d81644bc275072`.

This proves continuation from the Drive recovery state rather than a new fresh run.

## Execution and result-package readback

`colab_execution.json` readback:

- `status=SUCCEEDED`;
- `mode=resume`;
- `epochs=2`;
- `sealed_test_accessed=false`;
- `error=null`;
- all governed workflow steps were present through `training_completed` and
  `checkpoint_verified`.

Result archive:

- name:
  `D1_yolo11s_wp33_afa03d4b_20261018_20261021T011243_checkpoint_smoke_r1_result.tar.gz`;
- size: `35,686,597` bytes;
- SHA-256: `eae79b0dbf808be95d74b6d119c6e5e42a122fb40daf334700acf92283c186ba`;
- recomputed archive hash matched the result manifest;
- result-manifest SHA-256:
  `c3972f0be87e4a9666d91f8120d6d05718f2b76209a6398a10eadadb76cd5971`;
- `terminal_outcome=SUCCEEDED` and `sealed_test_accessed=false`.

The result manifest bound exactly eight non-empty files:

1. `weights/best.pt` — 19,276,890 bytes;
2. `weights/last.pt` — 19,276,890 bytes;
3. `results.csv` — 434 bytes;
4. `args.yaml` — 2,154 bytes;
5. `run_contract.json` — 2,868 bytes;
6. `colab_logs/colab_execution.json` — 2,323 bytes;
7. `colab_logs/colab_train.log` — 443,514 bytes;
8. `colab_logs/DB_logger.db` — 606,208 bytes.

The SQLite database opened successfully and contained the expected `logs` table (plus
`sqlite_sequence`). The text log was non-empty. The runner's package validation had already
cross-checked both logs against `results.csv` before publishing the archive.

## Runtime identity

The packaged `run_contract.json` reported:

- `runtime_backend=cuda`, `cuda_available=true`;
- GPU `NVIDIA L4`;
- CUDA `13.0`, NVIDIA driver `580.82.07`;
- Python `3.12.3`;
- PyTorch `2.14.1+cu130`;
- Ultralytics `8.4.172`;
- detector lock SHA-256
  `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5`;
- `git_dirty_files=0` and the exact R3 implementation commit above.

## Gate disposition

| Gate | PM disposition |
| --- | --- |
| Fresh epoch 1 and Drive checkpoint | PASS |
| New-runtime recovery | PASS |
| Resume to epoch 2 | PASS |
| Result archive and manifest | PASS |
| SQLite and text logs | PASS |
| Sealed-test boundary | PASS, never accessed |
| Independent QA | PENDING |
| 100-epoch D1 pilot | NO-GO until independent QA PASS |

