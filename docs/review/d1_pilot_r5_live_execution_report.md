# D1 Pilot R5 live Colab execution report

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Execution environment: Google Colab, NVIDIA L4 runtime, account-authorized Drive mount  
Result: **PASS — completed Pilot artifacts verified; no training or sealed-test access**

## Scope

This append-only report records the live Colab execution of the independently QA-passed Pilot R5
finalizer against the completed Drive state at:

`M1_D1_Colab/runs/pilot_seed_20261018_r2`

R5 is a verification-only program. It did not train or resume a model, create a checkpoint,
repackage the result archive, export the sealed test, evaluate the sealed test, or change the
authenticated Drive artifacts.

## Immutable code identities

| Role | Commit or SHA-256 |
| --- | --- |
| governed training checkout | `939f6bbce9f5c955b13ebcc84addd5083d242355` |
| Pilot R3 commit | `e20a69541e3a6327739238fc71691109ce8f51d0` |
| Pilot R3 source SHA-256 | `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` |
| Pilot R4 commit | `2cc45b467456e9300df613839d94c5cb0bbdcbba` |
| Pilot R4 source SHA-256 | `ffcc88e2339b349775ca34e5e30531a102d0bcab1d45fa0dff9b1ea8bead25ad` |
| Pilot R5 commit | `6acc47f08dba385b730ac86d591cb55248d104d2` |
| Pilot R5 source SHA-256 | `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b` |

The Colab terminal cloned the repository, checked out the training commit detached, downloaded the
three sidecars from their immutable commits, and printed `OK` for all three SHA-256 checks before
executing R5.

## Live command boundary

R5 was invoked with only the detached repository root and the existing Drive state directory:

```text
python /content/run_d1_colab_pilot_r5.py \
  --repo-root /content/Traffic_Sign_Detector \
  --state-dir /content/drive/MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/pilot_seed_20261018_r2
```

No training, resume, packaging, dataset export, validation evaluation, or final-test option was
passed.

## Observed terminal result

The live terminal returned exit status zero and the following semantic result. A second,
verification-only invocation wrote an append-only execution receipt and normalized stdout to the
same Drive state directory so this claim is independently auditable after the terminal disappears:

- status: `D1_PILOT_R5_PACKAGED_STATE_VERIFIED`;
- cleanup: `CHECKOUT_ALREADY_CLEAN`;
- latest checkpoint generation: `epoch-0100`;
- attempt count: `6`;
- failed resume attempt count: `4`;
- distinct runtime digests: `true`;
- runtime-evidence status: `D1_RUNTIME_RETRY_EVIDENCE_VERIFIED`;
- execution status authenticated by R5: `SUCCEEDED`;
- training outcome authenticated by R5: `COMPLETED_FROM_FINAL_CHECKPOINT`;
- `sealed_test_accessed=false`.

Durable receipt identities:

| Evidence | Drive filename | SHA-256 |
| --- | --- | --- |
| execution receipt | `r5_live_execution_receipt_20261021T152621Z.json` | `9e582110c9940b99e42f10b30c326979e16d9b41c9901cde7acd26c8823905a1` |
| normalized R5 stdout | `r5_live_verification_stdout_20261021T152621Z.json` | `c16d57c98825146489fc3528a7c14a43ca12f6ec8006db66c9db5dee943a9935` |

The receipt records the exact argv, exit status `0`, R5 source SHA-256, detached training commit,
UTC execution time, L4 runtime descriptor, stdout size/hash, full parsed R5 result and
`sealed_test_accessed=false`. These two append-only files are post-training verification evidence;
they are deliberately not represented as members of the governed eight-file result archive.

The output was observed in the terminal attached to the existing Colab notebook tab. The notebook's
older R4 final cell still shows its historical two-attempt-verifier failure; that stale cell output
was not used as PASS evidence. The R5 terminal execution is the repair and authoritative live
verification for the six-attempt history.

## Authenticated artifact identities

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `colab_execution.json` | 6,848 | `0f3f6bb9d96d4b852a97966f37048b659ffaa424868af05834e482c9ae01ccbc` |
| `execution_attempts.jsonl` | 3,584 | `eeedb9a8954ad4445b1ee65484d2b69cf30d106fa486f93c815b9241e7882b84` |
| `DB_logger.db` | 32,940,032 | `57e93f1c78365b4396600136ab16887d9bc6731a3343fe65787fd7390abd9bb8` |
| `colab_train.log` | 16,324,955 | `a3bdec9a5eb31b33126c75f20bdb9d9376b5e6ecc22ba422f54ecdb70107defe` |
| `recovery/latest.json` | 233 | `252b889a7b4136cba12609b11766e29e217f5ef1c93a2073d0e7dc9d2991eaf5` |
| result archive | 144,369,956 | `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f` |
| result manifest | 2,140 | `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796` |

The archive contains the completed result package and its manifest binds eight packaged files.
R5 authenticated both the archive and manifest against the live execution and SQLite evidence.

## Gate interpretation

This execution closes the post-training artifact-integrity gate for the 100-epoch seed 20261018
pilot, subject to a separate independent QA review of this live-execution evidence. It does not
establish model quality and does not authorize another training seed or sealed-test access.

The next permitted sequence is:

1. independent QA of this report and the immutable R5/live artifact evidence;
2. validation-only evaluation of `best.pt`, threshold selection on validation, and M1 Pro latency;
3. a pilot quality report and independent QA;
4. an explicit GO/NO-GO decision for seeds `20261019` and `20261020`.

