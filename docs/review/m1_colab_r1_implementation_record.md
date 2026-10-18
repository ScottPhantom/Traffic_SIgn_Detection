# M1-Colab-R1 implementation record

Status: `PM_READY_AWAITING_INDEPENDENT_QA`
Prepared: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Scope: private Google Colab train/val path for D1; no sealed-test access

## Owner authority and unchanged boundaries

The Owner approved Google Colab, private upload of train and validation data, the official
Ultralytics `yolo11s.pt`, and preservation of logs in the style of the retained VGG16 notebook.
The sealed test is not authorized for upload and remains protected by the D-05 final-evaluation
path. The 54-class YOLO baseline remains the first D1 baseline; the approved one-class detector
plus classifier baseline still requires its own metric/gate addendum before any sealed-test use.

This is a successor implementation record. It does not edit the earlier Owner record, whose M1
export-manifest hash predates M1-R1 hardening. The current verified M1 export-manifest SHA-256 is
`8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`.

## Reference-notebook logging readback

The Owner-provided Colab notebook was inspected read-only in the signed-in private account. Its
logging pattern is:

- Google Drive is mounted and outputs are kept under `MyDrive/CPV391`;
- logger name `CPV_log_record`, INFO level, console output plus a custom SQLite handler;
- SQLite database `DB_logger.db`, table `logs`, with columns `id`, `timestamp`, `level`, `logger`,
  and `message`;
- formatter `%(asctime)s - %(levelname)s - %(message)s`;
- explicit training start/end messages and per-epoch loss/accuracy/validation metrics.

M1-Colab-R1 preserves that console/file/SQLite pattern. YOLO subprocess output is streamed into
the same logger, so each emitted epoch line is persisted. It also writes an atomic structured
`colab_execution.json` with command, parameters, completed steps, start/end timestamps, terminal
outcome, and `sealed_test_accessed=false`.

## Implemented files and controls

- `scripts/build_m1_colab_bundle.py`
  - derives the exact authorized roster from the pinned WP36-R1 split, WP33 labels, WP35 lineage,
    image inventory and current M1 export manifest;
  - builds a deterministic gzip tar containing only regular-file copies of train/val source images
    and WP35 train-only images/labels;
  - embeds and emits a manifest binding the repository commit, detector lock, class map, train/val
    stem hashes, sealed-test hash commitment, per-file size/SHA-256, split and kind;
  - rejects dirty source checkouts, unsafe paths, path traversal, links, duplicate/extra/missing
    members, byte/hash drift, commit drift, roster drift and any split policy other than train/val;
  - safely extracts only missing files and refuses to overwrite symlinks or differing files.
- `detector/colab/run_d1_colab.py`
  - verifies and extracts the private bundle, regenerates the governed YOLO train/val export,
    runs `uv sync --frozen`, verifies `m1.cli check`, optionally downloads only the
    Owner-approved official weight with its pinned SHA-256, and trains through `m1.cli`;
  - disables third-party tracking signals and relies on the detector contract's telemetry controls;
  - retains `weights/best.pt`, `weights/last.pt`, `results.csv`, `args.yaml`, `run_contract.json`,
    the text log, SQLite log and structured execution record in a hashed result package.
- `detector/colab/d1_train.ipynb`
  - mounts private Drive, reads the required Git commit from the bundle manifest, checks out that
    exact commit, installs/uses `uv`, and runs a one-epoch smoke by default;
  - reads back the Drive-persisted terminal outcome and result archive;
  - contains no `export-test` or `--final-eval` path.
- `detector/m1/contract.py` and `detector/m1/cli.py`
  - extend the exact environment contract with CUDA availability/version, GPU name, NVIDIA driver
    and runtime backend while preserving Apple M1 Pro final-latency validation;
  - final run registration now rejects a dirty training checkout and contradictory accelerator
    metadata.

## Current evidence

Pre-archive roster scan (measured locally):

- 1,912 governed raw train images;
- 376 governed raw validation images;
- 1,800 WP35 train-only images and 1,800 matching labels;
- 5,888 regular-file members total, plus the embedded manifest;
- train stem-list SHA-256 `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`;
- validation stem-list SHA-256 `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`;
- sealed-test stem-list commitment
  `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`;
- `test_included=false`; the train/val raw roster is disjoint from all 903 sealed-test stems.

Local checks before independent QA:

- root targeted M1/crop/Colab tests: `27 passed`;
- detector suite: `54 passed`;
- relevant Ruff checks: pass after repair;
- notebook JSON parse and both new CLIs' help paths: pass;
- source-byte scan validated all 5,888 governed SHA-256 values.

No upload, Colab execution, training, validation evaluation or sealed-test access occurred while
preparing this record. The actual upload archive must be built only after this source package is
independently QA-approved, committed and clean, because its embedded manifest binds that commit.

## Independent QA request

QA must fail closed on: any test member or path, symlink/link member, traversal path, unhashed or
extra member, manifest/source mismatch, commit mismatch, absent SQLite/file logs, incomplete
terminal outcome, missing required run artifacts, telemetry re-enablement, or missing
GPU/CUDA/driver evidence. QA should also verify that the notebook defaults to one epoch and that
no action in this package opens the sealed test.
