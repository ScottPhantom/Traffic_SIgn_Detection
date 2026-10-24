# VGG16-54 R1 R4 two-runtime smoke — independent artifact QA

Verdict: **PASS**

Reviewed: `2026-10-24T20:24:48+07:00`

Boundary: `ARTIFACT_QA_ONLY_NO_TRAIN_NO_RESUME_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Authority and reviewed anchors

The authoritative artifact source for this review is the Google Drive service, not the lagging
macOS Drive sync cache.

- Drive state-folder ID: `15FS0z37N4pAyMMrjdj36ibZOHgsZbZcS`.
- Immutable source commit:
  `2e1d981e70e02b19d1998fa17be8c8a0de033df0`.
- R4 launcher commit:
  `65c8db6a799c84c1ff2bd0a888d1f3d777f0b6bb`.
- R4 notebook SHA-256:
  `76c58b32cf0f9ab83bad8be074805dcf4e397b58a8bd6a36f31f6a91c345cd75`.
- R4 notebook-QA record SHA-256:
  `e040e10af58ca152cb8fecd2f2397f0a8fa03c201d46757b7c0a41ca9ea642eb`.
- Fresh epoch-1 QA proof SHA-256:
  `97b9dbbba6ebb99e30df733949684e9aef2e486f7e8357cee4b90968e42da580`.
- Owner configuration SHA-256:
  `b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a`.
- Train/validation bundle-manifest SHA-256:
  `bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b`.

The reviewed notebook and QA record match the exact bytes at the R4 launcher commit. The runtime
successor and its contracts match the exact source-commit objects.

## Google Drive service readback and macOS cache distinction

The Google Drive connector independently grounded the state folder and listed its exact hierarchy:
three top-level state files plus `recovery/`, two retained snapshot generations, five payload files
plus one manifest in each generation, and two weights in each weights folder. Service-reported
sizes agree with the manifests, including both epoch-2 weights at `176957595` bytes.

The service-side log files are:

- `colab_execution.json`, file ID `1P_rFHDeruXkRGxBKu8KrpMpttDvAPMCV`, 1784 bytes,
  modified `2026-10-24T13:16:48.970Z`, SHA-256
  `2215053883d9fbe2c3b534dfe6a4043edc306dc08c0454f1115ee42c25e2856a`;
- `train.log`, file ID `1C5T75Z33IZuZw5qfY8hu9gPyYLOGF033`, 2160 bytes,
  modified `2026-10-24T13:16:47.068Z`, SHA-256
  `d50cd8780042b79af89eb9660bc1c3e2c0c2817496d2820887ebc4ae1de5b5c0`;
- `DB_logger.db`, file ID `1Fr4G9DNUSBXT1WlXvOclfjcRy52ZZwDc`, 8192 bytes,
  modified `2026-10-24T13:16:47.104Z`, SHA-256
  `47aa6a1b1c153af0a1a7d9d770b5381067dc04c496c014e4fbdebf188a4fb447`.

The DB bytes were fetched directly from the Drive service, loaded into an in-memory SQLite
connection, and returned `PRAGMA integrity_check = ok`. The database has exactly eight rows. Its
eight payload strings are byte-identical to the eight direct-service `train.log` lines, in this
order:

```text
ATTEMPT -> FRESH -> CHECKPOINT -> SMOKE_STOP
        -> ATTEMPT -> RESUMED -> CHECKPOINT -> SMOKE_STOP
```

The two ATTEMPT objects are also exactly the two attempts persisted by the service-side execution
JSON. The final execution and final log/DB payload all report `SMOKE_STOP`, epoch `2`, and
`sealed_test_accessed=false`.

The macOS sync cache is demonstrably stale only for the DB bytes: its cached DB SHA-256 is
`43e5c25a7b95536e9f287132f964e5e6f112d5ca8a09d371505f1db61124f540` and exposes only the first
six rows. That older cache view caused the initial provisional FAIL. It is not the Drive service
object and is not used for this final verdict. The Drive file ID, service modification time,
directly fetched SHA-256, eight-row SQLite readback, and service-side log equality establish the
authoritative state.

## Two-runtime execution evidence

The execution has exactly two attempts:

1. fresh from completed epoch `0`, runtime digest
   `15f95cca74680341a2e90aeee1e6679050ddf3974ab525e6ad7366eb1000453f`;
2. resume from completed epoch `1`, runtime digest
   `648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5`.

The digests are distinct and use schema `sha256:d1-runtime-v1:tag+linux-boot-id`. Both attempts
record exactly `NVIDIA L4`, CUDA `13.0`, one device, capability `[8, 9]`, and total memory
`23659151360` bytes. Both have equal run/checkpoint binding
`fe334b1877454adb608628bde0c1a3287a31b861f5bb7b16635e96a8a1953bbe` and preserve
`sealed_test_accessed=false`.

The governed `verify_prior_smoke_state(...)` accepted the epoch-2 terminal state only when the
current digest equalled the reviewed resume digest. It rejects missing/extra attempts, malformed
GPU or digest evidence, binding drift and same-runtime resume.

## Checkpoint and ledger evidence

The Drive service directly returned `latest.json`, the two-event `checkpoint_io.jsonl` ledger and
the epoch-2 manifest. Their content agrees on:

- latest generation: `epoch-0002`;
- latest manifest SHA-256:
  `c33ddf55198d8ba802bd10c55595959374aa820ea71ab7c85f9d67d6dda60da9`;
- binding SHA-256:
  `fe334b1877454adb608628bde0c1a3287a31b861f5bb7b16635e96a8a1953bbe`;
- ledger event hashes:
  `f2d9a053bf3bf518f41dfcf8042365a322f0fcd4bed2124f1b0955b3ee6f8cb6` and
  `9a59fa355270f04dbce1539f22a8c7eedb2d2c080aba3baed25a6a76ac4f8bbe`;
- retention count `2` and `sealed_test_accessed=false`.

`EfficientCheckpointStore.verify_telemetry(...)` passed. Both retained manifests and all ten
snapshot payloads were independently re-hashed. Epoch-2 is:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `weights/last.pt` | 176957595 | `3d2c69cdfea6f1e50585bb737df2526482121b23b6dfc91ccee8df6e96438a80` |
| `weights/best.pt` | 176957595 | `3d2c69cdfea6f1e50585bb737df2526482121b23b6dfc91ccee8df6e96438a80` |
| `results.csv` | 283 | `14a5973e4d5b9d8c01874ea23dd9c83f805f86dbdefeff425dbcb47ff7776e28` |
| `args.yaml` | 422 | `ed915cdf09f632af9c2befc3d5d35d369049b8bcfbe3e7b533534328b6904189` |
| `run_contract.json` | 728 | `6ac248a26fa213371ee723f5a6c8a79014656a24666a3b7a3cbca465834df45c` |

The exact two-generation state roster has 17 files. All reviewed local materializations other than
the identified stale DB cache were regular single-link files with no symlink, hardlink, extra
attempt, cross-state path, non-finite JSON or sealed/final-evaluation route. Drive service listing
independently confirms the hierarchy and payload sizes.

## Adversarial and regression checks

- Governed VGG runtime, base VGG and checkpoint-store suite: `30/30` PASS.
- R2/R3/R4 launcher suite: `13/13` PASS.
- Strict checkpoint ledger, pointer, manifests and payload rehash: PASS.
- Direct Drive DB integrity, eight-row lifecycle and byte-equal text-log comparison: PASS.
- Final Graft check: `OK`.

These checks reject wrong proof schema/hash, duplicate/non-finite proof JSON, missing or extra
attempts, wrong status/epoch/GPU/digest/binding, same-runtime resume, unsafe links, invalid ledger
chain and checkpoint manifest/payload drift.

## Proof, verdict and boundary

The exact nine-field machine-readable proof is
`docs/review/generated/vgg16_54_r1_r4_two_runtime_smoke_qa_proof.json`, SHA-256
`898a440709dd477b9ec70569b52464047adb55de8ed48325eeef091f3e759132`.
The production `detector/vgg16_54/contract.py::verify_smoke_qa(...)` accepted this exact file and
hash against the reviewed bundle manifest.

`PASS`, zero blockers, for the governed two-runtime epoch-1/epoch-2 smoke.

This proof may be hash-pinned by a separately reviewed long-run successor. The long run must use
`mode=resume`, continue on the already reviewed resume runtime digest
`648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5`, preserve the exact binding
and state, and keep `sealed_test_accessed=false`.

This QA does not itself start or authorize an unreviewed launcher, mutate the Drive state, open the
sealed test, publish a model, upload, commit or push. Any long-run notebook/contract delta must
receive its own independent QA before execution.
