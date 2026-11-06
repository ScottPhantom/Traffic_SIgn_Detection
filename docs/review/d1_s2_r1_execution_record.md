# D1-S2-R1 Colab execution record

Recorded: 2026-11-06 (`Asia/Ho_Chi_Minh`). Scope: operation and artifact
integrity of the authorized seed-20261019 pilot repeat. Independent result QA
and common R3 validation scoring are separate gates. `sealed_test_accessed=false`.

## Source and smoke gate

- Code/authorization/contract/source-QA commit A:
  `fc729d07664c70a8784ff735b72d7283e5261b6a`.
- Notebook/notebook-QA commit B:
  `192939f9fba60cd6ec3c7c61f740c1ff4758cf92`. The authorized non-force
  push of these and preceding commit `729547b` completed before Colab use.
- Independent live-smoke QA:
  `docs/review/d1_s2_r1_live_smoke_independent_qa_record.md`, one
  `Verdict: PASS`, for the fresh epoch-1 pause only.
- Fresh NVIDIA L4 attempt: 2026-11-06 11:28:53–11:32:34 local,
  `PAUSED_FOR_RESUME`, `epoch-0001`; runtime digest
  `09684dcb15069019dda3c53be5c76bd6751c999ae93a07a310d5d7aefe61bd12`.
- Resume NVIDIA L4 attempt: 2026-11-06 11:44:11–16:51:50 local,
  `SUCCEEDED`, completed epoch 100; runtime digest
  `0bd5a87026dc941c8c51cea20aea2030a008d32e80c69fc7ab55ebe4f8139640`.
  The two digests differ. The attempt list contains exactly these two entries.

## Terminal state and artifact integrity

- Drive state: `M1_D1_Colab/runs/d1_s2_seed_20261019_r1`;
  [folder](https://drive.google.com/drive/folders/1qmUE-A9N3ul0XhFpkImN8dLqU9ZXvUU-).
- The synchronized `colab_execution.json` reports `status=SUCCEEDED`,
  `training_outcome.completed_epoch=100`, `error=null`, clean source commit
  `fc729d0`, the frozen pilot/bundle/authorization pins, and
  `sealed_test_accessed=false`. `recovery/training_outcome.json` says
  `COMPLETED`, epoch 100, resumed true, seal false. `recovery/latest.json`
  names `epoch-0100`, binding
  `3795215c55c563962654d6b8c8784b581380d6bc7ee975d99ca72d9b0d8e9e43`,
  and checkpoint manifest SHA-256
  `8b40348172f5df9c8e6bcc6abde48845418a2e196f0ce6a38f11a07c0cf02e90`.
- The result archive was opened from the synchronized Drive copy. Its eight
  members have exactly the paths, byte lengths and SHA-256 values declared in
  the manifest. `results.csv` has 100 rows, epochs 1–100. These are operator
  integrity checks, not independent result QA.

| Result artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `D1_yolo11s_wp33_afa03d4b_20261019_20261106T113001_s2_r1_result.tar.gz` | 41,303,680 | `c9367603c67650968514d00699d73bc0202fb7e1b69c4a6af413b34f60b2164e` |
| Result manifest (`.tar.gz.manifest.json`) | 1,986 | `b771a58996f75257f2a58adcb684273dff637be28b5d66606a66a721694e172e` |
| Archived `weights/best.pt` | 19,289,370 | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` |
| Archived `weights/last.pt` | 19,289,370 | `05935508454e77150a6accf15248e8d6e44ad6ce76f423b17155364f6c3ea40c` |
| Archived `results.csv` | 12,672 | `237a6efd574e5d49c4c4611f09c2344ae75885d600c3bd70a069232f5860f4c0` |

The result manifest also binds `args.yaml`, `run_contract.json`,
`colab_execution.json`, `colab_train.log` and `DB_logger.db`; its run
attestation SHA-256 is
`807ba02a87da944e804fc61b314618bb77692c727fb577eec5f7a6395442c80c`.
The epoch-100 recovery weights are full checkpoint files, not byte-identical
to the smaller result-archive weights, so their hashes must not be interchanged.

## Local evidence copy and handoff boundary

The selected synchronized state was copied byte for byte to the Git-ignored
`tmp/d1_s2_seed_20261019_r1_state/`: archive, manifest, execution JSON,
attempt JSONL, SQLite and text logs, recovery pointer and outcome, and all
six files under `recovery/snapshots/epoch-0100/`. The copy contains 14 source
files totaling 237,332,952 bytes. Every source SHA-256 was computed before
copy and matched the destination SHA-256 afterward. The ignored
`copy_integrity_manifest.json` records each size and both digests; its own
SHA-256 is `a983d014e99f6a11708cf2f452913605521ddbf18c2f5c84f6465d703bc943a8`.

The final epoch's built-in train/val row records precision 0.70355, recall
0.62988, mAP50 0.65822 and mAP50-95 0.47887. These are Ultralytics per-epoch
metrics and are not the governed R3 common-validation score or a D-05 decision.

An independent reviewer must verify archive/hash/log/state/configuration
binding and issue a separate result-QA record before the S2 evaluator is run.
No R3 inference, pilot comparison, threshold lock, weight upload or sealed-test
access was performed in this execution record.
