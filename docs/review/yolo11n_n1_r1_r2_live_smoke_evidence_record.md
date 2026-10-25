# YOLO11n N1 R1-R2 live smoke evidence record

Recorded: 2026-10-25 16:11:09 +07:00  
Scope: train/validation-only detector smoke; no classifier retraining; no sealed-test access.  
Verdict: **EVIDENCE ONLY — PENDING INDEPENDENT ARTIFACT QA**

## Immutable inputs

- Git branch: `codex/yolo11n-dual-track-r1`
- Notebook commit: `c74f6d5d94ac8cd88b6f6259f87969ead817ec27`
- Training source commit pinned by both notebooks: `0ec545183bf29de035f440bb0307842ae132f4ca`
- Composite source-QA SHA-256: `5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a`
- Upload archive SHA-256: `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05`
- Upload manifest SHA-256: `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`
- Official `yolo11n.pt` SHA-256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`
- State directory: `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`

## Live execution observations

The fresh notebook completed with runner return code 0 and printed:

```text
{'status': 'SMOKE_PASS', 'track': 'n1', 'epoch': 1, 'seal': False}
```

The resume notebook used a newly allocated NVIDIA L4, completed with runner return code 0 and
printed:

```text
{'status': 'SMOKE_PASS', 'track': 'n1', 'epoch': 2, 'seal': False}
```

The authoritative Drive state records two attempts with distinct runtime digests:

| Attempt | Mode | Runtime digest |
| --- | --- | --- |
| 1 | `fresh` | `639d59924049977c060b1dddd8d10b140fb0691a604e47c25f3ce735a14cd58f` |
| 2 | `resume` | `c3f1f5a671417276449cc06ecf9db377e76ea22b67e14281e25ad90ceea41517` |

`colab_execution.json` records `status=SMOKE_STOP` and `sealed_test_accessed=false`. The SQLite
event sequence is:

```text
ATTEMPT(fresh) -> FRESH -> CHECKPOINT(epoch=1) -> SMOKE_STOP(epoch=1)
ATTEMPT(resume) -> RESUMED -> RECOVERY_RESTORED(next_epoch=2)
-> CHECKPOINT(epoch=2) -> SMOKE_STOP(epoch=2)
```

This proves the second runtime restored epoch 1 and continued to epoch 2; it did not start a new
fresh run. The recovery event explicitly records `worker_rng_exact_replay=false`, which must remain
visible in QA and in any later long-run contract.

## Drive artifact readback

- `detector/recovery/latest.json`: generation `epoch-0002`
- latest binding SHA-256: `098766d77d0b5146f560cb3e0125c6af0c5d5815f165e29c0224b290db6e1275`
- latest checkpoint-manifest SHA-256: `6d437c376e4aeaa8d438c06618c9c6bd9b32d5fcd31b59c55f4b693cd9c2ab3e`
- epoch-0002 `last.pt`: 21,325,280 bytes, SHA-256
  `85e3e1a19f1ee0261d27ef63ca9e08b93b91dcb215ef84e416489e321988b790`
- epoch-0002 `best.pt`: 21,322,147 bytes, SHA-256
  `30ad0f1f89bab3a3a7b3f917d01a35dcf31262a7cd6401a0a1ad3d7ea17bec80`
- epoch-0002 `results.csv`: 436 bytes, SHA-256
  `315595e5eee26350028f1f0eddb5985ca126f6566b1e60412168e820ebd7d450`
- epoch-0002 `args.yaml`: 1,833 bytes, SHA-256
  `8ea9dd34e44f8c72d7cfda7037534327cf32fea068e5ca35dc17a71941508199`
- epoch-0002 `run_contract.json`: 668 bytes, SHA-256
  `0a5e3203f49a2250c378f9b12563017b19b78409f000c497c0acf83a003d656e`
- SQLite `DB_logger.db`: `PRAGMA integrity_check = ok`
- `colab_execution.json` SHA-256:
  `9bd2546a29d990ac1707e6ca1eff15d55c373f0eac88b7c79749ab1c52084d8f`
- `detector/recovery/latest.json` SHA-256:
  `ed42322f480030cd05a5f1bffb30731dad9a75eba5e158883535e078c6debb6a`
- `DB_logger.db` SHA-256:
  `02763a04c67ad134c9725ad9e1a9facec60855bcd6c69a9b658b3ae9eac7f5e5`
- `train.log` SHA-256:
  `899f5b7bfb2f2d2594081193f631ae649a4b0bd02e975ee6e3c39a9f966efb47`

## Boundary

This record does not authorize the 100-epoch N1 run, validation evaluation, threshold selection,
sealed-test access, publication, or deployment. Advancement requires independent artifact QA PASS.
