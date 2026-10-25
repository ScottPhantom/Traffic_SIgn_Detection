# YOLO11n dual-track R1 private-upload record

Status: `UPLOAD_VERIFIED_SMOKE_NOT_COMPLETE`

Recorded: `2026-10-25T14:44:42+07:00`

Boundary: `PRIVATE_TRAIN_VAL_UPLOAD_ONLY_NO_SEALED_TEST_ACCESS_NO_LONG_TRAINING`

## Authorization and immutable source

The Owner authorized the complete QA-passed YOLO11n dual-track R1 package to be committed and
pushed to a successor branch, the notebooks and train/validation bundle to be uploaded to private
Google Drive, and bounded two-runtime smoke execution through epoch 2. The Owner did not authorize
sealed-test access or long training before live artifact QA passes.

- Successor branch: `codex/yolo11n-dual-track-r1`.
- Successor source commit: `45b7b1fab606032fcfb2956d0207171ae8b4c7f6`.
- Notebook commit: `5ef9b2da16e4a2f8fc0ba03c9ee9226e7eab45f5`.
- Source independent-QA record SHA-256:
  `bcf7470d931d23445785c1103e3c919aca4c696b22738079756572892ce4f632`.
- Notebook/bundle independent-QA record SHA-256:
  `62437883b8576cbf7ba650f13bbe6b215b7c9aefc2bfc4a5eec2043449a509b2`.

Both commits were read back from the remote successor branch. The official `yolo11n.pt` weight is
not in Git; its approved SHA-256 remains
`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.

## Private Drive readback

The following exact files were copied into the existing private project folder. The local Drive
mount was read back byte-for-byte, each file received a Drive item identifier, and the Drive web UI
displayed all six names under the project folder. The record intentionally omits the private account
identifier, folder URL and object identifiers from the public repository.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `yolo11n_n1_r1.tar.gz` | `823358941` | `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05` |
| `yolo11n_n54_r1_fresh.ipynb` | `9905` | `5d008c1405e458cf2799d1634cfe8dfe1933059ea452f8b9f622218dfff9454e` |
| `yolo11n_n54_r1_resume.ipynb` | `9914` | `86dee6f2014cc7ef6e5f527a3b811b7e412fdce20cc024555e5acbfeda4e0ff2` |
| `yolo11n_n1_r1_fresh.ipynb` | `7604` | `ddb4d1af3cd46f171ce550b82b423d1bc3dfded054d8de63456fb807d00952a9` |
| `yolo11n_n1_r1_resume.ipynb` | `7613` | `a9a5cc3f2a9f68da3a5968800b2598f06514fc50b957a96f14753a6314b50b4c` |
| `yolo11n_dual_track_r1_notebook_independent_qa_record.md` | `4340` | `62437883b8576cbf7ba650f13bbe6b215b7c9aefc2bfc4a5eec2043449a509b2` |

The N1 archive contains only train and validation inputs: `3712` train images, `12621` train boxes,
`376` validation images and `624` validation boxes. Its embedded manifest SHA-256 is
`8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`; it declares
`test_included=false` and `sealed_test_accessed=false`. The N54 notebook reuses the previously
verified eight-part train/validation transport and sidecar; it does not upload or reconstruct a
test split.

## Smoke boundary observed at record time

The N54 fresh notebook was opened from the exact notebook commit on an NVIDIA L4 and the static
third-party-notebook warning was accepted after source QA. Two calls to
`drive.mount('/content/drive')` each timed out with `ValueError: mount failed`. No successor run
directory, `colab_execution.json`, checkpoint, SQLite log or text log was created. No training
command ran. No code path exported, opened or evaluated the sealed test.

The next step is to establish a healthy fresh L4 Drive mount, run the N54 fresh leg through epoch 1,
then use a distinct L4 runtime for resume through epoch 2. N1 must complete the same two-runtime
sequence. Independent live-artifact QA is mandatory before any long run.
