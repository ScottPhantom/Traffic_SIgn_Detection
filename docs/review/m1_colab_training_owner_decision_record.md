# M1 Colab training and private upload owner decision

Status: `OWNER_APPROVED_COLAB_PRIVATE_TRAIN_VAL_UPLOAD`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)

The owner selected Google Colab for D1 training and authorized upload of the M1 **train and
validation** exports to a private Google Drive location. The sealed test set is not authorized for
upload and remains local until the single logged final evaluation defined by D-05.

The Colab path must preserve training logs and run artifacts in the same auditable spirit as the
owner-provided VGG16 notebook reference:
`https://colab.research.google.com/drive/1Bkd__8i2shudylgL-RVmQJ-Zze-0yr3O?usp=drive_link`.
The exact logging behavior of that notebook must be read and documented before implementation;
this record does not invent unobserved notebook behavior.

Every Colab run must retain the M1 `run_contract.json`, exact environment versions, GPU/CUDA
identity, command/config, epoch metrics, checkpoints and terminal outcome. Ultralytics telemetry
remains disabled. Uploading or executing the Colab package is a later explicit task; no upload was
performed when this record was written.

Relevant inputs:

- M1 YOLO export manifest SHA-256: `d9beec1d69f56d3223c1a204d4606c8c4dd25dd72d841e2048fc424c0bb05fcc`
- Detector lock SHA-256: `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5`
- D-05 owner record SHA-256: `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`
