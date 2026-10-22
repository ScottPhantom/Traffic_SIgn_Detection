# D1 L4 capacity successor R8 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_PASS — SOURCE CANDIDATE READY FOR THE NEXT OWNER-CONTROLLED PREPARATION GATE**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS: 0 Critical, 0 High, 0 Medium, 0 Low.**

R8 closes all three R7 findings. It binds evidence to the exact previously verified Colab L4
runtime, rejects malformed and merely self-consistent CUDA/Torch identities, applies the same R8
checks through the direct helper and official package route, restores every temporary predecessor
callback after success and failure, and requires exact total-VRAM identity.

The full R1–R8 adversarial corpus found no remaining blocker in the reviewed scope. This PASS
applies only to the frozen R8 source candidate. It does not authorize a Colab capacity run, select
a final training configuration, approve a commit/push, interact with the live Pilot R3, or access
the sealed test.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r8.py` | `1dadc023d91db9ccb213c2b8d451a2280cce9cb3a9242787ac083573d780c3dd` |
| `detector/colab/verify_d1_l4_capacity_r8.py` | `8fb123f067e6e9d4b54ade9ed317bd5835e65960e2d7c8b287b78e48455f06d8` |
| `tests/test_d1_l4_capacity_r8.py` | `2f188b3cd5dbae7bf216a21ddd5d7c828e9d5134a0b7339a77c0e055b7ae2c93` |
| `docs/review/d1_l4_capacity_r8_qa_remediation_report.md` | `d29d0f0496dae60ddd675c597644f9ff86447178fb0a1099ddc137beba454a89` |

The R1–R7 independent QA records remain byte-identical at SHA-256:

| Record | SHA-256 |
| --- | --- |
| R1 | `37ce181cee90df4c020fc81a3558825226201b8368e6220903c4b1721b3398dd` |
| R2 | `94c9c2a00fd3f5c6865fbfc463c7c9b1d6f392c79e474cd06f0d4945a2ff4dce` |
| R3 | `46cedcedd57cc97b901a09b1bd0a73000cc6171720b5064fdeac0eabe47adeb9` |
| R4 | `a928b9019736ddf5836feb924da9ec4dbe154f9380042c93da32c48526e06489` |
| R5 | `895d1903871df9d5444899d1a5357eb5c29f1d3e16a99aa613f3e135b9755b40` |
| R6 | `0522077771ddd2c81ef1570ac3eca71584104d1e3c1817917b1a640743fbd6c8` |
| R7 | `8efc7c0b6104a22cf7abaecbf6df9be7355e6149623e5bf6bfafaa46f1b21aa6` |

Their historical FAIL verdicts and implementation bytes were not modified. Existing PM changes
and unrelated artifacts were outside this QA scope and were preserved.

## R7 finding closure

### H-1 — exact verified L4 runtime identity: closed

The canonical environment was accepted only with all of these identities:

```text
Python       3.12.3 (numeric 3.12.x)
Platform     Linux / x86_64
GPU          NVIDIA L4
Torch        2.14.1+cu130
CUDA         13.0
Driver       580.82.07
Ultralytics  8.4.172
```

Independent mutations all failed closed: CUDA `13..0`, `1.3.0`, `99.9`, `13.0+evil`; a
self-consistent forged Torch `2.14.1+cu999`; suffix injection
`2.14.1+cu130+evil`; missing or wrong Torch public/local version; driver `forged-driver` and
`580.95.05`; wrong Ultralytics; Python 3.13; Darwin/arm64; and a T4 GPU. A future legitimate
runtime change therefore requires an append-only, Owner-reviewed successor rather than passing by
self-consistency alone.

### L-1 — direct-helper/package consistency and restoration: closed

A complete canonical-shaped 24-attempt/56-file R8 package passed the direct type helper. The
official package verifier traversed the same R8 checks and then rejected the intentionally
nonexistent Git commit anchor, as expected. All four temporarily installed predecessor callbacks
were restored after the successful direct-helper return, after the official-route exception, and
after an independently forced helper exception. Public predecessor monkey-patches applied after
R8 import did not bypass the saved-original checks.

### L-2 — exact total-VRAM identity: closed

Canonical stable total VRAM passed. Changing one sample by only `0.00001 MiB` failed as
within-attempt drift; changing every sample by the same tiny amount failed against the frozen plan.
Tolerance remains available only for derived metrics, not the device-identity field.

## Full attack matrix

| Attack class | Independent R8 result |
| --- | --- |
| Exact verified L4 runtime identity | Accepted |
| Malformed/injected CUDA and arbitrary or alternate driver identity | Rejected |
| Wrong/missing Torch public version, CUDA suffix or Ultralytics version | Rejected |
| Wrong Python family, operating system, architecture or GPU | Rejected |
| Direct helper versus official package environment checks | Consistent through the independent Git-anchor boundary |
| Temporary predecessor callbacks after success and forced exceptions | Restored exactly |
| Exact within-attempt and plan-bound total VRAM | Canonical accepted; microscopic drift rejected |
| Raw step/GPU schema, exact types, finite values, ranges and timestamps | Forged evidence rejected |
| Batch-index reversal/duplication/gap and GPU sample chronology | Rejected |
| Environment, manifest, plan, report, proposal, candidate and repetition schemas | Extra/missing/wrong-type fields rejected |
| Execution JSONL duplicate/non-finite/extra/wrong-type fields and chronology | Rejected |
| Effective batch: one full step | Accepted |
| Effective batch: only a partial step | Rejected |
| Effective batch: full steps plus one final partial | Accepted |
| Effective batch: multiple or non-final partials | Rejected |
| Ultralytics auto batch reduction / trainer batch differs from plan | Rejected |
| Loader gap omitted from elapsed measurement | Rejected |
| Controlled CUDA OOM allowlist | Accepted as OOM evidence |
| Generic/data-loader/value failure relabelled as OOM | Rejected |
| Missing/duplicate/reordered grid candidate | Rejected |
| Missing repetition, unstable throughput CV or less than 20% VRAM headroom | Rejected |
| Selection tamper or benchmark cherry-pick | Rejected; deterministic order replayed |
| SQLite root, ancestor or file symlink and database hard link | Rejected before external writes |
| R8 source roster and candidate entry | Exactly 17 unique files; entry resolves to R8 |
| R8 builder after hardening installation | Exact 24-row/17-source plan; no recursion |
| Public predecessor monkey-patch after R8 import | Rejected; saved original checks remained active |
| Full self-consistent forged package | 24 attempts/56 files rejected at nonexistent Git commit anchor |
| Archive extra member, expected-member symlink or content mismatch | Rejected; canonical archive accepted |
| Sealed-test/Pilot route in R8 production source | Absent |

The forged package included the complete fixed factorial roster, report/proposal, SQLite ledger,
execution JSONL, manifest, archive and the seventeen-file source-at-commit roster. The independent
Git anchor—not an earlier structural shortcut—was the first failing official-package boundary.

## Preserved protocol and governance controls

- The experiment remains exactly 24 isolated attempts:
  `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}`.
- All three repetitions remain mandatory. Population throughput CV must be at most 5%; measured
  peak VRAM must be at most 80%, preserving at least 20% headroom.
- Selection remains deterministic and resists omission, reordering and cherry-picking: among
  candidates within 95% of best median throughput, choose smaller batch, fewer workers, then lower
  VRAM.
- Effective-batch replay, loader-gap arithmetic and fail-closed OOM classification remain intact.
- SQLite no-follow/link/inode safeguards, exact execution JSONL, manifest inventory and archive
  member/content replay remain intact.
- Plan/report/proposal/manifest governance markers remain exact booleans. The proposal remains
  `PROPOSAL_NOT_OWNER_APPROVED`; the report remains explicitly not model-quality evidence.
- Static inspection found no test export, `--final-eval`, Pilot R3 import/notebook route or
  sealed-test access-log route in R8 production source.
- Every synthetic artifact retained `sealed_test_accessed=false`; the sealed test was not opened.
- No Colab execution, training, upload, commit or push occurred. The live Pilot R3 was not read,
  mutated or coupled to this QA round.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Graft freshness/source trace | R8 source query refreshed the graph and saved about 15,698 tokens (less than USD 0.01); final graph rebuilt/check OK |
| Root R1–R8 targeted tests | PASS, `96 passed, 1 skipped`; skip is the root environment without Torch |
| Complete detector tests | PASS, `105 passed` |
| Repository verifier matrix | PASS, `52/52` in 101.8 seconds wall time |
| Root Ruff and lock | PASS; `168 packages` |
| Detector Ruff and lock | PASS; `66 packages` |
| `git diff --check` before record | PASS |
| Exact runtime-identity and total-VRAM mutation probes | PASS |
| Direct-helper/official-package/restoration probes | PASS |
| Full fake 24-attempt package | Rejected at independent Git anchor |
| Path/SQLite, execution, batch, OOM, selection, source/delegation and archive attacks | PASS |

The green mechanical checks support but do not replace the independent adversarial probes above.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R8 source candidate | **PASS** |
| Next preparation gate | **READY FOR OWNER DECISION** |
| Commit/push and clean commit-pinned notebook | **NO-GO until explicitly Owner-authorized and performed** |
| Colab capacity execution | **NO-GO until the current Pilot releases L4 and preparation evidence is reverified** |
| Capacity result/configuration selection | **NO-GO; no capacity measurements exist yet** |
| Owner final-config approval | **NO-GO pending measured proposal and Owner decision** |
| Configuration-bound two-runtime resume smoke | **Required after Owner selects the proposed configuration** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |
