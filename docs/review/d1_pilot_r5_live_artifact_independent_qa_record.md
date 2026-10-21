# D1 Pilot R5 live artifact — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA mode: independent, read-only, fail-closed  
Overall verdict: **FAIL — live Colab execution receipt is not independently durable**  
Underlying source and Drive artifact verdict: **PASS**

## Scope and authorization boundary

This review covered:

- `docs/review/d1_pilot_r5_live_execution_report.md`;
- the immutable Pilot R3/R4/R5 source and R5 QA records;
- the current synced Drive directory
  `M1_D1_Colab/runs/pilot_seed_20261018_r2`.

QA did not train or resume a model, evaluate validation or test data, open the sealed test, modify
the Drive state, run Colab, upload, commit, or push. The only project change made by QA is this
append-only record.

## Reviewed identities

| Item | SHA-256 |
| --- | --- |
| live-execution report | `0d62efc1483a937c62b7447ba436361222ae868b1be4f74e4213736af6bfd09a` |
| Pilot R5 source | `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b` |
| R5 notebook builder | `fff3ea340255aedbb8f4a233ce4b442bf163aa9ca725118049af28972c9761b4` |
| R5 notebook | `106ac040fc07a6d7aaf207bff321fa367ccac713f8b2d5c59ced8998913392fe` |
| R5 source tests | `812e5e497379b06e38068d7b29d9a1611c4b73a510ef787173e8452b3c44fd56` |
| R5 notebook tests | `4a5a78803acf906baeff4963d477510d9f8f03beec794f1ad8a5ef06f8e4e170` |
| R5 finalizer QA record | `4a22d0d3fb8bcce5eb7f66f7d7757d26de8d796bc1117144a5b5a7147287e4db` |
| R5 notebook QA record | `a63748b1416fdb37353abc1e4c9dcc6de3365fa1beb766dc590d348d02338e4a` |

The report's code pins were independently reproduced from Git objects:

| Role | Commit | Source SHA-256 | Result |
| --- | --- | --- | --- |
| governed training checkout | `939f6bbce9f5c955b13ebcc84addd5083d242355` | commit identity | PASS |
| Pilot R3 | `e20a69541e3a6327739238fc71691109ce8f51d0` | `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` | PASS |
| Pilot R4 | `2cc45b467456e9300df613839d94c5cb0bbdcbba` | `ffcc88e2339b349775ca34e5e30531a102d0bcab1d45fa0dff9b1ea8bead25ad` | PASS |
| Pilot R5 | `6acc47f08dba385b730ac86d591cb55248d104d2` | `d4c7ab9b96fe92dd3eb6034fd1fb1144df7de35fbda88138f9b1d938f167d13b` | PASS |

## Independently verified current Drive state

All seven reviewed files were regular files at the synced Drive location; no symlink was found at
the state-directory top level. Their current sizes and hashes exactly match the report and R5 pins:

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `colab_execution.json` | 6,848 | `0f3f6bb9d96d4b852a97966f37048b659ffaa424868af05834e482c9ae01ccbc` |
| `execution_attempts.jsonl` | 3,584 | `eeedb9a8954ad4445b1ee65484d2b69cf30d106fa486f93c815b9241e7882b84` |
| `DB_logger.db` | 32,940,032 | `57e93f1c78365b4396600136ab16887d9bc6731a3343fe65787fd7390abd9bb8` |
| `colab_train.log` | 16,324,955 | `a3bdec9a5eb31b33126c75f20bdb9d9376b5e6ecc22ba422f54ecdb70107defe` |
| `recovery/latest.json` | 233 | `252b889a7b4136cba12609b11766e29e217f5ef1c93a2073d0e7dc9d2991eaf5` |
| result archive | 144,369,956 | `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f` |
| result manifest | 2,140 | `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796` |

Independent parsing found:

- execution status `SUCCEEDED` and `error=null`;
- training outcome `COMPLETED_FROM_FINAL_CHECKPOINT` at epoch 100;
- latest generation `epoch-0100`;
- six execution attempts in both the execution record and append-only journal;
- attempt statuses: one `PAUSED_FOR_RESUME`, four `FAILED`, then one `SUCCEEDED`;
- one fresh attempt followed by five resume attempts;
- five unique valid runtime digests across the six attempts, satisfying distinct-runtime evidence;
- result manifest status `D1_COLAB_RESULT_PACKAGE`, terminal outcome `SUCCEEDED`, eight packaged
  files, and `sealed_test_accessed=false`;
- execution record `sealed_test_accessed=false`.

The manifest binds the byte-identical live execution record and SQLite database. Its packaged text
log is not the same byte sequence as the current live text log; this is expected by the reviewed R5
contract, which authenticates the current text log separately. The report does not claim those two
text-log copies are identical.

## Independent semantic reproduction

QA created a clean temporary detached clone of training commit
`939f6bbce9f5c955b13ebcc84addd5083d242355` and ran the exact reviewed R5 source read-only against
the current synced Drive directory. This was a local verification invocation, not a Colab run, and
did not change Drive artifacts.

The result was:

- status `D1_PILOT_R5_PACKAGED_STATE_VERIFIED`;
- cleanup `CHECKOUT_ALREADY_CLEAN`;
- latest generation `epoch-0100`;
- retry-evidence status `D1_RUNTIME_RETRY_EVIDENCE_VERIFIED`;
- attempt count 6;
- failed resume count 4;
- distinct runtime digests `true`;
- archive and manifest hashes exactly as listed above;
- `sealed_test_accessed=false`.

This independently establishes that the current source and current artifacts produce the semantic
result stated in the report. Focused R5 source/notebook tests also passed **22/22**, Ruff passed, the
root lock check passed, and Graft reported the wiring graph in sync.

## Blocking evidence gap

The report additionally states that a specific Google Colab NVIDIA L4 terminal invocation returned
exit status zero, printed `OK` for all three sidecar hashes, and produced the stated R5 result. That
ephemeral execution event is not independently auditable from the supplied durable artifacts:

- the current browser inventory exposes no open Colab tab from which QA can read the terminal;
- R5 is deliberately verification-only and writes no signed or hash-pinned execution receipt;
- the Drive execution record, attempt journal, SQLite database, text log, archive, and manifest all
  predate R5 verification and are not changed by R5;
- the current Drive text log contains the historical R3/R4 process evidence and R4 traceback, but
  no R5 PASS marker or R5 invocation transcript;
- therefore the exact same current Drive hashes would exist whether or not that specific R5 Colab
  terminal command had actually run.

The report correctly avoids claiming model quality, sealed-test evaluation, or authorization for a
new seed. Its artifact statements are accurate. However, under a fail-closed independent-QA rule,
the PM-observed terminal statement cannot be promoted to independently verified live-Colab evidence
without a durable receipt. Local semantic reproduction does not prove the reported L4 environment
or that particular terminal exit code.

## Required remediation

Before this live-execution evidence gate can PASS, provide an append-only durable receipt from a
verification-only Colab run that binds, in one transcript or structured record:

1. timestamp and NVIDIA L4 runtime identity;
2. detached training commit and the exact R3/R4/R5 sidecar hashes;
3. exact R5 command and state-directory path;
4. complete R5 JSON stdout and process exit code;
5. receipt SHA-256, read back after it is saved outside the governed artifact directory.

Alternatively, amend the report to classify the Colab terminal execution explicitly as a PM
observation without independent durable proof and use the independently reproduced current-artifact
result only for a narrower artifact-integrity gate. Either remediation requires a new independent
QA record. This QA does not authorize another Colab invocation or any Drive write.

## Verdict and authorization boundary

**FAIL** for the claimed live-Colab execution-evidence gate because the ephemeral Colab/L4 command
and exit status lack an independently inspectable durable receipt.

**PASS** for the immutable source identities, current Drive artifact identities, terminal training
state, retry history, checkpoint/archive/manifest/SQLite/text-log consistency, and the independently
reproduced R5 semantic result. No sealed test was opened; all reviewed evidence says
`sealed_test_accessed=false`.

This record does not authorize validation evaluation, threshold selection, another training seed,
sealed-test access, artifact mutation, Colab execution, upload, commit, push, deployment, or
publication.
