# YOLO11n N1 R1-R2 live smoke independent artifact QA record

Date: 2026-10-25 (Asia/Ho_Chi_Minh)  
Verdict: **PASS**  
Reviewer: independent QA session `/root/yolo11n_dual_track_r1_source_qa`

## Scope and authoritative state

This review independently read the locally synchronized Google Drive state at
`M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`. The implementation, source records,
notebooks, checkpoints and logs were not modified. No training, upload, commit, push, evaluation
or sealed-test access occurred.

The implementation-authored evidence record
`docs/review/yolo11n_n1_r1_r2_live_smoke_evidence_record.md` recomputed to
`6d726ee53a8e426c53d6631b211ff6f86f7a9189aa1c514745f84d5fa82e869b`; its claims were not
accepted until reproduced from the state files below.

## Immutable execution bindings

| Item | Verified value |
| --- | --- |
| Notebook commit | `c74f6d5d94ac8cd88b6f6259f87969ead817ec27` |
| Training source commit | `0ec545183bf29de035f440bb0307842ae132f4ca` |
| Composite source-QA record | `5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a` |
| Notebook-delta QA record | `30f23f6621c0bf8de223b9374ec8e777d1ac4f81c44c3bdee0668b6a100532e7` |
| Fresh notebook | `a2ee432045ebdaf76a82d4112e4608ac35903124d315e53bcd6075725af8fcaa` |
| Resume notebook | `45d57c2684db25fec573242293ba8403a98ee0487c9c8855fab49744d51d5c63` |
| Train/validation bundle | `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05` |
| Bundle manifest | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |
| Official `yolo11n.pt` | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` |

Both Git commits are reachable from `origin/codex/yolo11n-dual-track-r1`. Git-object readback of
the notebook commit reproduced both notebook hashes and the notebook-delta QA hash. The notebooks
pin the source commit, composite source-QA path/hash, repaired runner, isolated state, exact L4
guard, train/validation-only manifest policy and epoch-1/epoch-2 smoke stops. The real composite
source-QA record contains one canonical unqualified PASS verdict and remains accepted by the real
runner guard against the extracted real bundle.

## Event and resume evidence

The text log and SQLite payloads contain the same nine JSON records in this exact order:

```text
ATTEMPT(mode=fresh)
FRESH
CHECKPOINT(epoch=1)
SMOKE_STOP(epoch=1)
ATTEMPT(mode=resume)
RESUMED
RECOVERY_RESTORED(next_epoch=2, worker_rng_exact_replay=false)
CHECKPOINT(epoch=2)
SMOKE_STOP(epoch=2)
```

Runtime digests are distinct:

- fresh: `639d59924049977c060b1dddd8d10b140fb0691a604e47c25f3ce735a14cd58f`
- resume: `c3f1f5a671417276449cc06ecf9db377e76ea22b67e14281e25ad90ceea41517`

`colab_execution.json` embeds those same two ATTEMPT payloads, terminates at
`status=SMOKE_STOP`, `event=SMOKE_STOP`, `epoch=2`, and has the same final timestamp as the last
text/SQLite event. The resume checkpoint `args.yaml` points `model` and `resume` to the restored
`weights/last.pt`; its `results.csv` retains epoch 1 and appends epoch 2. This, together with the
recovery event and checkpoint payload, proves continuation to epoch 2 rather than a fresh restart.

Both optimizer-bearing `last.pt` files were read back. Their Ultralytics epochs are zero-based
`0` and `1`; their recovery payloads report completed epochs `1` and `2`, preserve the same run
binding, contain scheduler/RNG/loader-generator state, and explicitly set
`worker_rng_exact_replay=false`. Exact worker-process RNG replay is therefore not claimed.

## Checkpoint and binding verification

`latest.json` selects `epoch-0002` with binding SHA-256
`098766d77d0b5146f560cb3e0125c6af0c5d5815f165e29c0224b290db6e1275` and checkpoint-manifest
SHA-256 `6d437c376e4aeaa8d438c06618c9c6bd9b32d5fcd31b59c55f4b693cd9c2ab3e`.
The real `CheckpointStore.load_latest` accepted the state and returned completed epoch 2.

Both generations use run `D1_yolo11n_n1_detector`, status `RECOVERABLE`, the same canonical
binding and the same byte-identical `run_contract.json`. The contract binds detector stage,
manifest `8e6ffe77...`, seed `20261018`, 100-epoch target, YOLO11n, 1280-pixel input, batch 4,
official weight hash, zero horizontal flip and reuse—not retraining—of the existing classifiers.

| Generation | Artifact | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| epoch-0001 | `checkpoint_manifest.json` | 1,680 | `856564d054bb4ee92d4b47e38700f0060f70c83ab987d0bea2a011a562371952` |
| epoch-0001 | `weights/last.pt` | 21,325,088 | `29bfdc17a0ea3deca31e55df8c1634d3d06eeca9bb8b77e6f3b03cd98b034f0b` |
| epoch-0001 | `weights/best.pt` | 21,321,891 | `c1ec1f6fd349cc03832b98b7ff7bc3886d6665d8953a0738fd31cfa258a19b66` |
| epoch-0001 | `results.csv` | 316 | `1b3c3813bd0b5f8f181330b6d5c9f196d36fd41ad8268ee6e4b12f8b6534fada` |
| epoch-0001 | `args.yaml` | 1,755 | `3627aef8fc09087521daf7556d7f271616f30ded4d7db06dbbe5f9015ac018ee` |
| epoch-0001 | `run_contract.json` | 668 | `0a5e3203f49a2250c378f9b12563017b19b78409f000c497c0acf83a003d656e` |
| epoch-0002 | `checkpoint_manifest.json` | 1,680 | `6d437c376e4aeaa8d438c06618c9c6bd9b32d5fcd31b59c55f4b693cd9c2ab3e` |
| epoch-0002 | `weights/last.pt` | 21,325,280 | `85e3e1a19f1ee0261d27ef63ca9e08b93b91dcb215ef84e416489e321988b790` |
| epoch-0002 | `weights/best.pt` | 21,322,147 | `30ad0f1f89bab3a3a7b3f917d01a35dcf31262a7cd6401a0a1ad3d7ea17bec80` |
| epoch-0002 | `results.csv` | 436 | `315595e5eee26350028f1f0eddb5985ca126f6566b1e60412168e820ebd7d450` |
| epoch-0002 | `args.yaml` | 1,833 | `8ea9dd34e44f8c72d7cfda7037534327cf32fea068e5ca35dc17a71941508199` |
| epoch-0002 | `run_contract.json` | 668 | `0a5e3203f49a2250c378f9b12563017b19b78409f000c497c0acf83a003d656e` |

Every manifest member's observed byte size and SHA-256 matches its manifest record.

## State logs, seal and input boundary

| State artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `colab_execution.json` | 1,934 | `9bd2546a29d990ac1707e6ca1eff15d55c373f0eac88b7c79749ab1c52084d8f` |
| `detector/recovery/latest.json` | 233 | `ed42322f480030cd05a5f1bffb30731dad9a75eba5e158883535e078c6debb6a` |
| `DB_logger.db` | 8,192 | `02763a04c67ad134c9725ad9e1a9facec60855bcd6c69a9b658b3ae9eac7f5e5` |
| `train.log` | 2,228 | `899f5b7bfb2f2d2594081193f631ae649a4b0bd02e975ee6e3c39a9f966efb47` |

SQLite `PRAGMA integrity_check` returns `ok`. Its nine ordered payload strings are byte-identical to
the nine `train.log` lines, and their stage/event fields match the SQLite columns. All nine event
payloads, both embedded attempts and final execution state record `sealed_test_accessed=false`.

The real 8,579-member input manifest records `test_included=false` and
`sealed_test_accessed=false`; no manifest member has a `test` path component. No test export,
final-evaluation route or sealed-test artifact exists in this smoke state.

## Tamper and regression checks

On a private temporary copy of the recovery state, the real checkpoint loader accepted the
unaltered baseline and rejected each of the following:

- latest-pointer manifest hash drift;
- requested run-binding/config drift;
- checkpoint member byte/size drift;
- a symlink substituted for a checkpoint member.

Focused checkpoint-store and N1 R1/R1-R1 regression tests passed: 26 tests, zero failures. The
authoritative Drive state remained unchanged.

Representative commands used:

```text
sqlite3 <state>/DB_logger.db 'pragma integrity_check;' 'select ... from logs order by rowid;'
uv run python <strict JSON, event-parity, manifest/member and CheckpointStore audit>
cd detector && uv run python <optimizer/recovery payload readback>
cd detector && uv run pytest -q tests/test_checkpoint_store.py tests/test_checkpoint_store_r2.py tests/test_yolo11n_n1_r1.py tests/test_yolo11n_n1_r1_r1.py
git show <commit>:<artifact> | shasum -a 256
```

## Authorization boundary

This PASS validates only the completed fresh-epoch-1 and different-runtime resume-epoch-2 smoke
artifacts. It permits these exact hashes to be used in an append-only, machine-readable smoke-QA
proof and a separately reviewed long-resume successor under the Owner's existing N1 authorization.
It does not itself authorize a commit, push, upload, 100-epoch execution, validation evaluation,
threshold selection, sealed-test access, publication, model acceptance or deployment.
`sealed_test_accessed=false`.
