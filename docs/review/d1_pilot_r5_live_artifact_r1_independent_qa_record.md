# D1 Pilot R5 live artifact R1 — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA mode: independent, read-only, fail-closed  
Verdict: **PASS**

## Scope and relationship to the prior record

This is an append-only remediation review. It does not modify or erase
`docs/review/d1_pilot_r5_live_artifact_independent_qa_record.md`, whose FAIL verdict correctly
records the earlier absence of a durable live-Colab receipt.

This R1 review covers:

- updated `docs/review/d1_pilot_r5_live_execution_report.md`;
- `r5_live_execution_receipt_20261021T152621Z.json` in the synced Drive state;
- `r5_live_verification_stdout_20261021T152621Z.json` in the synced Drive state;
- the immutable R5 source and training commit referenced by the receipt;
- the seven previously governed Pilot artifacts, read only to detect mutation.

QA did not run Colab, train or resume a model, evaluate validation or test data, access the sealed
test, modify Drive, edit PM source, commit, or push. The only project change made by QA is this new
record.

## Reviewed identities

| Evidence | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| updated live-execution report | — | `732a07b6231e91945e697896295b01f10f255d5eb564b4254036f8cecc5a97cb` |
| R5 execution receipt | 2,436 | `9e582110c9940b99e42f10b30c326979e16d9b41c9901cde7acd26c8823905a1` |
| normalized R5 stdout | 1,198 | `c16d57c98825146489fc3528a7c14a43ca12f6ec8006db66c9db5dee943a9935` |
| Pilot R5 source | — | `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b` |
| prior FAIL record retained | — | `105fb4848f97215edc0247b4b1db6aafd7bf79e7862cf3380efd041fd1907da8` |

The two Drive evidence files are regular, non-symlink files. Their independent readback hashes and
sizes exactly match both the remediation declaration and the updated report.

## Receipt schema and provenance binding

Strict JSON parsing rejected duplicate keys and non-finite constants. The receipt passed all of the
following exact checks:

- integer `schema_version=1`;
- status `D1_PILOT_R5_LIVE_EXECUTION_RECEIPT`;
- timezone-aware execution timestamp `2026-10-21T15:26:21.232272+00:00`, whose UTC second matches
  the `20261021T152621Z` filename suffix;
- runtime descriptor begins with `NVIDIA L4` and records a GPU identifier, driver `580.82.07`, and
  reported memory value;
- integer, non-Boolean `exit_status=0`;
- exact argv containing only Python, the R5 sidecar, detached repository root and exact Pilot R2
  Drive state directory;
- detached repository commit `939f6bbce9f5c955b13ebcc84addd5083d242355`;
- runner path `/content/run_d1_colab_pilot_r5.py` and SHA-256
  `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b`;
- top-level `sealed_test_accessed=false`.

Independent `git show` hashing of `detector/colab/run_d1_colab_pilot_r5.py` at commit
`6acc47f08dba385b730ac86d591cb55248d104d2` reproduced the runner hash exactly. The governed
training commit exists and matches the receipt.

## Receipt-to-stdout cross-binding

PASS. The receipt records stdout size 1,198 and SHA-256
`c16d57c98825146489fc3528a7c14a43ca12f6ec8006db66c9db5dee943a9935`; both match the current
normalized stdout file exactly. The receipt's embedded `result` object is structurally equal to the
strictly parsed stdout JSON.

The bound result requires:

- status `D1_PILOT_R5_PACKAGED_STATE_VERIFIED`;
- cleanup `CHECKOUT_ALREADY_CLEAN` with no removed path;
- latest generation `epoch-0100`;
- archive SHA-256 `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f`;
- manifest SHA-256 `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796`;
- runtime-evidence status `D1_RUNTIME_RETRY_EVIDENCE_VERIFIED`;
- type-strict attempt count 6;
- type-strict failed-resume count 4;
- distinct runtime digests exactly `true`;
- runtime and result `sealed_test_accessed=false`.

The archive, manifest and stdout paths all name the exact
`M1_D1_Colab/runs/pilot_seed_20261018_r2` state directory used by argv.

## Governed artifact immutability and semantic replay

The two receipt files are new append-only post-training evidence and are not represented as members
of the governed eight-file result archive. This is accurately disclosed in both receipt and report.

After the receipt files synchronized, QA rehashed the seven governed live files. Every size and
SHA-256 remained byte-identical to the previously accepted identities:

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `colab_execution.json` | 6,848 | `0f3f6bb9d96d4b852a97966f37048b659ffaa424868af05834e482c9ae01ccbc` |
| `execution_attempts.jsonl` | 3,584 | `eeedb9a8954ad4445b1ee65484d2b69cf30d106fa486f93c815b9241e7882b84` |
| `DB_logger.db` | 32,940,032 | `57e93f1c78365b4396600136ab16887d9bc6731a3343fe65787fd7390abd9bb8` |
| `colab_train.log` | 16,324,955 | `a3bdec9a5eb31b33126c75f20bdb9d9376b5e6ecc22ba422f54ecdb70107defe` |
| `recovery/latest.json` | 233 | `252b889a7b4136cba12609b11766e29e217f5ef1c93a2073d0e7dc9d2991eaf5` |
| result archive | 144,369,956 | `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f` |
| result manifest | 2,140 | `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796` |

QA then ran the exact reviewed R5 verifier locally and read-only against the current synced state,
using a clean detached clone of the governed training commit. The two extra receipt files did not
alter the verification surface. R5 returned the same epoch-0100, 6-attempt, 4-failure,
distinct-runtime, archive/manifest and sealed-false result bound by the receipt.

## Updated report review

PASS. The report's receipt filenames and hashes match the Drive files. It explicitly describes the
receipt-producing invocation as a second verification-only invocation, distinguishes the receipt
files from the governed result archive, and continues to avoid claims of model quality, sealed-test
evaluation, or authorization for another training seed. The earlier R4 notebook failure remains
classified as historical and is not used as PASS evidence.

The receipt is integrity-bound and independently reproducible evidence, not a cryptographic hardware
attestation. The report does not claim otherwise. Within the project's stated evidence contract,
the recorded L4 descriptor, code/commit pins, argv, exit status and fully bound result close the
specific durability blocker from the prior FAIL record.

## Validation summary

- receipt and stdout regular-file/readback checks: PASS;
- declared receipt and stdout SHA-256/size checks: PASS;
- strict receipt/stdout JSON schemas and duplicate-key rejection: PASS;
- receipt-to-stdout byte and parsed-result binding: PASS;
- timestamp-to-filename, argv-to-state, runner-to-Git and commit binding: PASS;
- all seven governed artifact identity checks after remediation: PASS;
- read-only R5 semantic replay after receipt addition: PASS;
- Graft wiring graph: `OK` and in sync with source;
- sealed test: not accessed; all bound layers require `sealed_test_accessed=false`.

## Verdict and authorization boundary

**PASS.** The append-only receipt remediation closes the sole live-execution durability blocker in
the prior FAIL record. The evidence now durably binds a Colab L4 descriptor, timestamp, exact
command, detached training commit, exact R5 source, exit status zero, normalized stdout bytes and
the complete verified Pilot result. The governed training artifacts remain unchanged.

This PASS closes only the R5 post-training live-artifact integrity gate. It does not establish model
quality and does not authorize test access, another training seed, validation evaluation, threshold
selection, artifact mutation, upload, commit, push, deployment or publication. Any next step still
requires its own existing authorization and gate.
