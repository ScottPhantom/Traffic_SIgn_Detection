# D1-A2-R1 Colab execution record

Recorded: 2026-11-06 (Asia/Ho_Chi_Minh).
Scope: execution and artifact integrity of the authorized A2 run. Result QA and validation comparison remain separate gates. No sealed-test access or evaluation was performed.

## Source and smoke gate

- Code commit A: `f3f7571794a5db04ad302fecf8014546ec1eb255`.
- Notebook and independent notebook-QA commit B: `b5dc02fe62ad350b902d36c299f8847e8efab1aa`.
- Independent live-smoke QA: `docs/review/d1_a2_r1_live_smoke_independent_qa_record.md`, committed as `40ce2c3f5609ad72caa7e854553897a26060afa0`, `Verdict: PASS` for the epoch-1 smoke only.
- Fresh L4 attempt: 2026-11-05 15:46:09–15:50:35 UTC (22:46:09–22:50:35 local), `epoch-0001`, `PAUSED_FOR_RESUME`; runtime digest `df394f3746757031cbe274863c38cb8b8000d4a81a69ac7e547d29356f78c80b`.
- Resume L4 attempt: 2026-11-05 16:03:48–23:38:33 UTC (23:03:48–06:38:33 local); runtime digest `0e86ec57c90fe2ce5bc40dc0e9bee0ee2166a825a8606b87e9ce93706c8e1a98`. The two runtime digests differ.

## Terminal outcome and direct Drive-mount verification

- State directory: `/content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/d1_a2_seed_20261018_r1`.
- The live Colab run cell returned exit code 0. Its verification cell read `colab_execution.json` and `recovery/latest.json`, asserted `status=SUCCEEDED`, `training_outcome.completed_epoch=100`, `generation=epoch-0100`, clean checkout, the A2 list/roster and authorization bindings, 4,687 train images in `colab_train.log`, and `sealed_test_accessed=false`.
- The direct Drive-mount execution record shows `mode=resume`, `status=SUCCEEDED`, start/end times above and `sealed_test_accessed=false`. Its final result manifest declares `terminal_outcome=SUCCEEDED`, eight files and `sealed_test_accessed=false`.
- The archive was opened on the live runtime. All eight members matched their declared byte sizes and SHA-256 values. `DB_logger.db` passed `PRAGMA integrity_check=ok`; the database contains a `logs` table. The text log was readable and had 122,015 lines. This is an integrity check, not independent result QA or a log-parity verdict.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `D1_yolo11s_wp33_afa03d4b_20261018_20261105T224723_a2_r1_result.tar.gz` | 42,528,074 | `ea7dba03b0a53cfea41fd876544715d783e56abf4837568df4e74f256a66a609` |
| Result manifest (`.tar.gz.manifest.json`) | 1,986 | `7a4e18563ee0c16a8dd01506e48a5c9fe379e205b3af96db25b4cf933a07d343` |
| Archived `weights/best.pt` | 19,289,370 | `9781f7d840e48a140d6031dc2b388359093a06a2b6f8912ba31b6a300c0ebb0b` |
| Archived `weights/last.pt` | 19,289,370 | `e602547ee5a875854e0a751ca5c66ae8da36550bec694e1f72d0ae0ead530df7` |
| Archived `results.csv` | 12,699 | `bdd84912be32fa500264e820abcb2c010fe7cb36c49653d49bb7282d554cd7b0` |

The result manifest also binds `args.yaml`, `run_contract.json`, `colab_execution.json`, `colab_train.log` and `DB_logger.db`. The run attestation SHA-256 is `3047b09db7a993b2260a9e8a88746b1cc474f3218a1eff55d3bbf368536a28c0`.

## Handoff boundary

At the time of this record, direct Colab Drive mount and the notebook show the complete result, while the connected Google Drive folder listing and Mac sync have not yet exposed the result archive. The cloud listing does show the final-sized text and SQLite logs. An independent reviewer must read the synchronized archive and manifest, verify their hashes and the epoch-100 checkpoint, check SQLite/text parity and runtime evidence, then issue a separate result-QA verdict. No A2 validation scoring, pilot comparison, D-05 decision, weight upload or sealed-test access was performed here.

`sealed_test_accessed=false`.
