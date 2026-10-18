# M1 pretrained-weights owner decision

- Status: `OWNER_APPROVED_OFFICIAL_YOLO11S_PRETRAINED_DOWNLOAD`
- Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)
- Recorded at: `2026-10-18T22:18:24+07:00`
- Owner response: `Q1: Có`
- Supersedes: the unresolved response recorded in
  `docs/review/m1_pretrained_weights_owner_response_record.md`

## Approved scope

The Owner explicitly authorized downloading the official Ultralytics COCO pretrained weight
`yolo11s.pt` for the M1/D1 detector work. This approval does not authorize downloading unrelated
files, publishing model weights, opening the sealed test, or uploading the sealed test to Colab.

## Download evidence

- Source URL reported by Ultralytics 8.4.172:
  `https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt`
- Local path, excluded from Git: `models/pretrained/yolo11s.pt`
- Size: `19313732` bytes
- SHA-256: `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`
- Load verification: Ultralytics loaded task `detect`, with the expected 80 COCO class names.
- Telemetry integrations were disabled through `m1.contract.disable_telemetry()` before model load.

## Bound inputs

- `docs/codex_next_tasks_2026-10-18.md` SHA-256:
  `dbb6a7c58beaefdbc2137ec8a0ebb3a3adf5f2e15a7dd1a47131d08a6ec74385`
- Prior unresolved response record SHA-256:
  `cb86650809b04c8841ad9055b4b33b0a4adab894c2c5e500b8c0b7cc48cdcec8`
- `detector/pyproject.toml` SHA-256:
  `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e`
- `detector/uv.lock` SHA-256:
  `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5`
- Repository checkpoint at decision time:
  `eae9146e471fff261d674a4ec9653ee073301b37`
