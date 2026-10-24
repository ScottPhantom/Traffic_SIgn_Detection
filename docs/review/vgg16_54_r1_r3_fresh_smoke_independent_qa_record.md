# VGG16-54 R1 R3 fresh epoch-1 smoke — independent artifact QA

Verdict: **PASS**

Reviewed: `2026-10-24T20:01:44+07:00`

Boundary: `ARTIFACT_QA_ONLY_NO_TRAIN_NO_RESUME_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Reviewed execution and source anchors

- Real synced Drive state:
  `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`.
- Launcher commit:
  `5af60930242f6ef6d830a8663d755f965ff8b0ab`.
- Exact R3 notebook SHA-256:
  `d0913e2269c69068faa3f7232c6d5ebcf226ff24a25368a18e3c57ec750d7c86`.
- R3 launcher-QA record SHA-256:
  `a769b7c3ce38683df1ff3359531eedba29cb174cb180fce94c11dc63fbb4fd1e`.
- Owner configuration SHA-256:
  `b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a`.
- Cascade B0 train/validation bundle-manifest SHA-256:
  `bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b`.

The current source files used by the artifact validators were byte-identical to their commit
objects at the immutable source commit. The notebook and its launcher-QA record were byte-identical
to their launcher-commit objects.

## Fresh-smoke terminal evidence

The execution is exactly `SMOKE_STOP` at epoch `1`, with
`sealed_test_accessed=false`. `execution_attempts` contains exactly one record. It is a fresh
attempt starting from completed epoch `0`, and the same complete ATTEMPT object is present in
`colab_execution.json`, the first line of `train.log`, and the first SQLite payload. The raw text
log line and SQLite payload are byte-identical; canonical JSON bytes also match the execution
object.

The event sequence in both logs is exactly:

```text
ATTEMPT -> FRESH -> CHECKPOINT -> SMOKE_STOP
```

The governed runtime evidence is:

- device: `NVIDIA L4`;
- CUDA runtime: `13.0`;
- device count: `1`;
- capability: `[8, 9]`;
- total memory: `23659151360` bytes;
- runtime schema: `sha256:d1-runtime-v1:tag+linux-boot-id`;
- fresh runtime digest:
  `15f95cca74680341a2e90aeee1e6679050ddf3974ab525e6ad7366eb1000453f`.

Run binding and checkpoint binding are equal to
`fe334b1877454adb608628bde0c1a3287a31b861f5bb7b16635e96a8a1953bbe`.
The frozen configuration reconstructs the exact Owner configuration hash and retains scratch
VGG16, 54 classes, seed `20261018`, maximum 100 epochs, minimum early-stop epoch 30, patience 15,
batch 256, workers 2, AdamW `1e-4` learning rate and weight decay, AMP, no horizontal flip and the
locked validation-selection rule.

## Checkpoint and checkpoint-I/O evidence

The latest pointer selects `epoch-0001`, binding
`fe334b1877454adb608628bde0c1a3287a31b861f5bb7b16635e96a8a1953bbe`, and manifest SHA-256
`797d8ff42960df888cf96b9e05e55e15dfba294a0637acce796cba3c86e8f855`.

`EfficientCheckpointStore.verify_telemetry(...)` passed against the real Drive state. The one-event
checkpoint-I/O ledger has a valid hash chain, epoch/generation/pointer/binding agreement, bounded
retention and `sealed_test_accessed=false`. Its event SHA-256 is
`f2d9a053bf3bf518f41dfcf8042365a322f0fcd4bed2124f1b0955b3ee6f8cb6`.

All five snapshot files were independently re-hashed:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `weights/last.pt` | 176957339 | `1d31f6c22fac7d025ac72bde3ac07e3c7f0ba615ce3769555dca934b4df7ce22` |
| `weights/best.pt` | 176957339 | `1d31f6c22fac7d025ac72bde3ac07e3c7f0ba615ce3769555dca934b4df7ce22` |
| `results.csv` | 184 | `84fedde5a0beb204765d27d384dacc2a9c678d5539026d84b51023df17c8c0b4` |
| `args.yaml` | 422 | `ed915cdf09f632af9c2befc3d5d35d369049b8bcfbe3e7b533534328b6904189` |
| `run_contract.json` | 728 | `6ac248a26fa213371ee723f5a6c8a79014656a24666a3b7a3cbca465834df45c` |

The exact 11-file state roster contains no symlink, non-regular file or multiple-link file. There
is exactly one recovery generation and no missing or extra attempt. Readable state artifacts
contain no D1-A3, pilot, Cascade-run, failed-R1-state, sealed-test export or final-evaluation route.
The earlier R2 terminal failure record established no state creation; the reviewed R2 suffix now
contains only this single R3 fresh attempt.

State-artifact SHA-256 anchors are:

- `colab_execution.json`: `df830ef0bc819b86bc5c099d467e01723adcc87599888ef85ebd9c53ad2539af`;
- `DB_logger.db`: `e355234ef81fbd930c16f4c2b67b5b18aedcad368af285158afbe89cb275a85a`;
- `train.log`: `f70eb1e8586e4956f0cb1c944e5c75eb2bc4be3a86d58cad84ba15e840be771a`;
- `recovery/checkpoint_io.jsonl`:
  `0c8e0b7be7b170b8362a6003904a44c1c1a009cd812085fd6f7f978cf6bd53b7`;
- `recovery/latest.json`: `257676a16fcb488c73f4b4080c718ca2d01fa5d3c36b5c2670f6913bfd34a9a8`.

## Adversarial and regression checks

The actual state passed the strict execution parser, exact ATTEMPT validator, resume precondition
validator, checkpoint ledger verifier, latest-pointer/manifest verifier and independent file
rehash. The focused VGG runtime, base VGG and checkpoint-store regression suite passed `30/30`.
Those validators reject symlinked, non-regular and multiple-link files; missing/extra attempts;
wrong status, epoch, GPU, runtime schema/digest or bindings; same-runtime resume; malformed ledger;
and checkpoint manifest or payload drift.

## Verdict and authorization boundary

`PASS`, zero blockers, for the R3 fresh epoch-1 smoke artifact.

The machine-readable proof is
`docs/review/generated/vgg16_54_r1_r3_fresh_smoke_qa_proof.json`. It authorizes only
`RESUME_EPOCH_2_ON_GENUINELY_NEW_L4_ONLY`: disconnect the fresh runtime, start a genuinely new
NVIDIA L4 whose runtime digest differs from
`15f95cca74680341a2e90aeee1e6679050ddf3974ab525e6ad7366eb1000453f`, and resume exactly through
epoch 2. The resume launcher must hash-pin and validate the proof's exact closed schema and all
bound Drive artifacts before invoking the governed runner.

This PASS does not authorize long training, model comparison/publication, commit, push, upload or
sealed-test access. Epoch-2 resume artifacts still require independent two-runtime smoke QA before
any run may continue toward the 100-epoch ceiling.
