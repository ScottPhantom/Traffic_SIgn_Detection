# YOLO11n N54 R1 — independent smoke artifact QA

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Verdict: **PASS**  
Scope: fresh epoch 1 and resume epoch 2 only; train/validation data only.

An independent read-only QA agent inspected the private Google Drive state synced at
`M1_D1_Colab/runs/yolo11n_n54_seed_20261018_r1`. The coordinator then read
`colab_execution.json` and `recovery/latest.json` directly through the Google Drive connector
at 2026-10-25 15:07 UTC. Their content agreed with the local synchronized copies. This
review did not run training, alter checkpoints, or access the sealed test.

## Artifact findings

- `colab_execution.json` has `PAUSED_FOR_RESUME` and two successful attempts:
  `fresh_epoch_1` completed epoch 1, then `resume_epoch_2` completed epoch 2.
- The attempts used different NVIDIA L4 GPU UUIDs and runtime digests:
  `ffbc4d2a9c03011e1d7c9f983163de46a646b61873f214d73d937966ad439621` and
  `137c13c7b4893dbeadb02842ab3d21e37be66a7bc30824eaa8a545fff67299e7`.
  Their common run binding is
  `2cde4feb9aa3c93a42efa7b0fbaf5253dfd516519e879a346bca978dae8e9432`.
- `recovery/latest.json` selects `epoch-0002`, with manifest SHA-256
  `887cebc2323c2cdc5db6a458bdfebb6db7647ff79a046e74478dd54070ba15d3`.
  The pointer file SHA-256 is
  `3e223f7cb010c83da168e239e1b1d9016129e44bffb2a36261b6234f9acc68a3`.
- All five declared checkpoint members at epochs 1 and 2 match their sizes and SHA-256 hashes.
  The epoch-2 `results.csv` has a header and rows for epochs 1 and 2, with no replay of epoch 1.
- SQLite `PRAGMA integrity_check` returned `ok`; its 1,525 messages match the 1,525 text-log
  lines in order. The append-only attempts JSONL agrees with the execution record.
- The independently recomputed run-binding digest matches the execution record. Every reviewed
  `sealed_test_accessed` field is `false`.

## Gate and limits

The machine-readable proof in `docs/review/generated/yolo11n_n54_r1_smoke_qa_proof.json`
binds this QA result to the exact epoch-2 Drive state. The long runner must verify that proof,
its SHA-256, the epoch-2 pointer, and a third distinct L4 runtime before starting. This QA PASS
does not certify epoch 100, validation quality, or sealed-test results.
