# YOLO11n N54 R1 — long-resume successor independent QA

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Verdict: **PASS for initial long-resume launch**  
Boundary: train/validation only; no new model run or sealed-test access in this review.

The independent reviewer inspected the append-only long notebook against the real QA-passed
epoch-2 state. The new notebook is a launcher; it does not change the pinned training source.
The training checkout remains immutable commit
`45b7b1fab606032fcfb2956d0207171ae8b4c7f6`, matching both smoke legs and the run binding.

| Reviewed artifact | SHA-256 |
| --- | --- |
| `scripts/build_yolo11n_n54_r1_long_notebook.py` | `4477ebe8c0ced1c6e7e09896386cdc3b7e2fd5eee9beb4b8ea2ff22fd765b26b` |
| `detector/colab/yolo11n_n54_r1_long.ipynb` | `9442361ac0693cd41dbeaeec9762a9a53451b0f3330cbef51fc322c8d259bce4` |
| `tests/test_yolo11n_n54_r1_long_notebook.py` | `f18b3c73b793a19e4e8660891bb07354d08021a3296fcbf331feb1334c6e2278` |
| `docs/review/generated/yolo11n_n54_r1_smoke_qa_proof.json` | `9189b52043157a5b536365fa714df8152bb05519b8bff723596f024a189bcd1e` |

The proof was uploaded to the Owner's private Drive as
`M1_D1_Colab/yolo11n_n54_r1_smoke_qa_proof.json`; a direct Drive fetch matched the local file
byte for byte. The notebook checks that SHA-256 and the epoch-2 pointer hash before running.
It uses `MODE=resume`, omits `--stop-after-epoch`, and passes the proof/hash to the pinned runner.
That runner requires a third distinct NVIDIA L4 runtime identity. There is no route to export,
evaluate, or open the sealed test.

The reviewer confirmed deterministic notebook generation, compilation of all code cells, 3/3
targeted tests, Ruff PASS, and a terminal verification cell for `SUCCEEDED`, epoch 100, eight
result members with exact hashes, SQLite integrity and `sealed_test_accessed=false`. The pinned
runner additionally validates checkpoint input and text/SQLite log parity while packaging.

Two limits are explicit. The terminal notebook cell does not independently verify every epoch-100
checkpoint member or full text/SQLite parity; independent result QA must do both after completion.
If training reaches epoch 100 but packaging fails, the pinned runner cannot retry the packaging
from the epoch-100 pointer because its initial smoke gate expects epoch 2. In that case, preserve
all artifacts and implement an append-only packaging-recovery successor; do not retrain from zero.

This PASS, the Owner's training instruction, and the smoke artifact QA allow the first long-resume
launch only. It does not certify training completion or validation performance.
