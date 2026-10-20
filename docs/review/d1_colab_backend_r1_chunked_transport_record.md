# D1 Colab backend R1 chunked transport record

Status: `LOCAL_CHUNKED_TRANSPORT_READY_AWAITING_INDEPENDENT_QA_AND_UPLOAD_AUTHORIZATION`

Recorded: `2026-10-20`

Boundary: `TRANSPORT_ONLY_NO_DATASET_CHANGE_NO_TRAINING_NO_SEALED_TEST_ACCESS`

## Observed upload outcome

The exact successor sidecar uploaded successfully to the private Drive folder. The single
`766226800`-byte archive did not: Drive repeatedly restarted its resumable transfer, reached as
high as 99%, then ended the first attempt with `Hoàn tất tải lên (1 không thành công)`. One explicit
retry again oscillated near completion without creating an archive row and was cancelled. No
partial archive is visible in the folder and no existing Drive file was overwritten or deleted.

## Append-only transport alternative

The already QA-approved archive bytes are unchanged. They were split mechanically into eight
ordered parts of at most 95 MiB. Concatenating the parts in lexical order hashes to the original
archive SHA-256 `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641` and size
`766226800` bytes.

| Part | Bytes | SHA-256 |
| --- | ---: | --- |
| `part-00` | `99614720` | `53f30f08406fbef5b8451610b2fd44a1f2be42ca6d50f612b68e5ace285e66ff` |
| `part-01` | `99614720` | `8451fe932760179d4b2e1a9cbdd21fd58744bc6b8f3d2a90e431cece7f546544` |
| `part-02` | `99614720` | `867c935bf152ddfc3e7919547dccf3682291326b60b956a8100fc1a59b60e98d` |
| `part-03` | `99614720` | `046fc8ae5d4e0a91196ccd6a6afa422fb1254baea7ae30bc3cab39602b534907` |
| `part-04` | `99614720` | `6d3751d858232fada5d57e8e892f3e272cd5b9e34efb184971b3f4786842665d` |
| `part-05` | `99614720` | `938106e4d34743e9b79109feb98d573f317afad44289f792f070f22e3924159b` |
| `part-06` | `99614720` | `3497c1a10314c74d4b81ba9a5a49653b16ba2e2d52b424fd7655623547cb6408` |
| `part-07` | `68923760` | `5f5ca85bc392310b2b5693ad9d0723f046eca9fd7980b45c944f22a3b3bc0eea` |

The machine-readable local manifest is
`tmp/m1_colab_train_val_backend_r1.tar.gz.parts.json`. The part payloads and manifest remain under
ignored `tmp/` and are not committed.

## Notebook control

The successor notebook now accepts either the exact single archive or all eight exact parts. On
the part path it verifies the mounted sidecar and every part before use, concatenates only into
runtime-local `/content/m1_colab_train_val_backend_r1.tar.gz`, verifies the reconstructed archive
size and SHA-256, and only then opens the embedded manifest. It never writes into Drive parts.

## Remaining boundary

Independent QA must pass the new transport controls before the eight parts are uploaded. Uploading
the eight replacement transport files is a new external write scope and requires Owner
confirmation. The one-epoch smoke remains unrun.
