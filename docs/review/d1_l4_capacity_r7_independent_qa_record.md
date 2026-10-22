# D1 L4 capacity successor R7 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — APPEND-ONLY SUCCESSOR REQUIRED**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 0 Critical, 1 High, 0 Medium, 2 Low.**

R7 fixes both R6 blockers on the governed happy path. The verified Colab identity
`Python 3.12.3 / Torch 2.14.1+cu130 / CUDA 13.0 / Ultralytics 8.4.172` is portable across verifier
hosts, and the combined batch-index, timestamp and physical-range telemetry attack now fails.
Predecessor controls also continue to reject source/delegation, full-package, archive, SQLite/path,
OOM, effective-batch, selection and governance attacks.

R7 nevertheless remains NO-GO. Its CUDA/Torch relation is self-consistent rather than bound to the
previously verified L4 runtime: malformed or impossible CUDA strings and arbitrary NVIDIA driver
identities are accepted. Two lower-severity exactness defects remain: the public R7 type-check
helper rejects canonical R7 evidence unless invoked inside the package verifier's temporary patch
context, and total-VRAM equality uses a relative tolerance even though the producer records one
stable `nvidia-smi` value.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r7.py` | `e4d0b832df90fa97fd3f073694dfbaffade82ae6f4d352f9215a08a983d665a8` |
| `detector/colab/verify_d1_l4_capacity_r7.py` | `edb6c98ef4d38c73488d9fbf96cb7afb5e3a1bd696a7dfec75331b71423c194a` |
| `tests/test_d1_l4_capacity_r7.py` | `b0978d5aed9161730b5401bdeab98a9089d583e0f72b569b198369740da2ffe8` |
| `docs/review/d1_l4_capacity_r7_qa_remediation_report.md` | `cc7bc08da5b039e621fbe4cd65b43891ed0092e364c8be47f010003491c71a38` |

The R1–R6 independent QA records remain byte-identical at SHA-256
`37ce181cee90df4c020fc81a3558825226201b8368e6220903c4b1721b3398dd`,
`94c9c2a00fd3f5c6865fbfc463c7c9b1d6f392c79e474cd06f0d4945a2ff4dce`,
`46cedcedd57cc97b901a09b1bd0a73000cc6171720b5064fdeac0eabe47adeb9`,
`a928b9019736ddf5836feb924da9ec4dbe154f9380042c93da32c48526e06489`,
`895d1903871df9d5444899d1a5357eb5c29f1d3e16a99aa613f3e135b9755b40` and
`0522077771ddd2c81ef1570ac3eca71584104d1e3c1817917b1a640743fbd6c8`. Their historical FAIL
verdicts and implementation bytes were not modified. Existing PM changes and unrelated artifacts
were outside this QA scope and were preserved.

## Findings

### H-1 — CUDA/driver provenance is self-consistent but not bound to the verified L4 runtime

`verify_d1_l4_capacity_r7.py:42-45` removes dots from any non-empty `cuda_version` and accepts a
Torch local suffix constructed from the result. `contract.validate_environment_record` rejects
blank/place-holder CUDA and driver fields, but it does not require their canonical numeric shape or
the exact runtime already verified on L4. R7 also never independently constrains
`nvidia_driver`.

The portable positive and ordinary negative cases behaved correctly:

```text
canonical 2.14.1+cu130 / CUDA 13.0    ACCEPT
Torch 2.14.1 without CUDA suffix      REJECT
Torch 2.14.2+cu130                    REJECT
Torch 2.14.1+cu129 / CUDA 13.0        REJECT
```

However, these forged identities passed the same verifier:

```text
cuda_version=13..0, torch=2.14.1+cu130           ACCEPTED
cuda_version=1.3.0, torch=2.14.1+cu130           ACCEPTED
cuda_version=99.9, torch=2.14.1+cu999            ACCEPTED
cuda_version=13.0+evil, torch=2.14.1+cu130+evil  ACCEPTED
nvidia_driver=forged-driver                      ACCEPTED
nvidia_driver=x                                  ACCEPTED
```

The project's independently verified Colab record fixes the relevant runtime at CUDA `13.0`,
driver `580.82.07`, Python `3.12.3`, Torch `2.14.1+cu130` and Ultralytics `8.4.172`
(`docs/review/d1_checkpoint_resume_r4_r6_l4_artifact_independent_qa_record.md:92-98`). A capacity
package can therefore certify materially different or syntactically impossible accelerator
provenance while preserving all other hashes. This restores part of R5's high-severity environment
identity failure and directly undermines reproducibility.

**Required successor repair:** bind the capacity environment to the exact previously verified
Colab L4 runtime identity: CUDA `13.0`, driver `580.82.07`, Torch `2.14.1+cu130`, Ultralytics
`8.4.172`, numeric Python `3.12.x`, Linux/x86_64 and NVIDIA L4. If future Colab images legitimately
change CUDA or driver, create a new append-only owner-reviewed runtime decision rather than letting
self-consistent arbitrary strings pass. Add every accepted forged case above as a regression.

### L-1 — Direct R7 type-check helper retains the R6 host-coupled false rejection

`verify_type_strict_artifacts()` first calls the saved R6 implementation at
`verify_d1_l4_capacity_r7.py:140-154`. The R7 package verifier temporarily replaces R6's global
environment checker before reaching that call, so the official `verify_package()` route uses the
portable R7 logic. A direct call to the public R7 type-check helper does not install that context
and resolves the R6 verifier's old local-host Torch comparison.

A canonical-shaped 24-attempt/56-file R7 package with `Torch 2.14.1+cu130` produced:

```text
direct_type REJECTED RuntimeError plan environment identity differs: torch
official_package REJECTED CalledProcessError ... ffff...^{commit}
```

The second result is correct: the official route passed R7 type/environment checks and rejected
the deliberately nonexistent Git anchor. The first result is a helper/API consistency defect, not
an official CLI bypass.

**Required successor repair:** make each R7/R8 verification layer self-contained rather than
depending on caller-installed predecessor globals, or make the helper private and impossible to
invoke as an independent verifier. Add a canonical package test that calls the helper and official
entry consistently.

### L-2 — Stable total VRAM is compared approximately instead of exactly

`verify_d1_l4_capacity_r7.py:122-129` uses `math.isclose()` with its default relative tolerance for
both within-attempt and plan-to-sample total VRAM. The producer repeatedly parses the same
`nvidia-smi` field, so this identity is expected to be exact rather than a derived floating-point
metric.

The verifier accepted a sample total of `23034.00001 MiB` among samples and against a frozen plan
value of `23034.0 MiB`:

```text
tiny_total_vram_drift ACCEPTED
```

The difference is operationally negligible and cannot change the 20% headroom decision at this
scale, hence Low severity. It still contradicts the report's stated stable/equal identity replay.

**Required successor repair:** require exact numeric equality after finite non-boolean validation
for `memory_total_mib`, while retaining tolerance only for genuinely derived metrics.

## Predecessor and R7 attack matrix

| Attack class | Independent R7 result |
| --- | --- |
| Canonical observed Colab Torch/CUDA identity on M1 verifier host | Accepted as valid |
| Missing/wrong Torch public version or wrong CUDA suffix | Rejected |
| Malformed/self-consistent CUDA and arbitrary driver identity | **Accepted — H-1** |
| R6 combined batch-index, reversed/duplicate/outside time, negative power/temperature | Rejected |
| GPU utilization below 0/above 100, memory below 0/above total, temperature above 125 | Rejected |
| GPU UUID change or material total-VRAM drift | Rejected |
| Microscopic total-VRAM drift under `math.isclose` | **Accepted — L-2** |
| Exact environment/manifest/report/candidate/repetition types and governance booleans | Rejected when forged |
| Execution duplicate/non-finite/extra/wrong-type fields and invalid chronology | Rejected |
| Effective batch: one full step | Accepted as valid |
| Effective batch: one partial step only | Rejected |
| Effective batch: full plus one final partial | Accepted as valid |
| Effective batch: multiple or non-final partials | Rejected |
| Ultralytics trainer batch differs from plan; loader gap omitted | Rejected |
| Generic failure relabelled OOM | Rejected; controlled CUDA OOM remains accepted |
| Candidate omission, duplication/reordering, missing repetition, unstable CV or <20% headroom | Rejected |
| SQLite root/ancestor/file symlink and hard link | Rejected before external writes |
| R7 source roster/candidate entry | Exactly 15 unique files; candidate entry resolves to R7 |
| R7 builder after predecessor hardening install | Accepted without recursion; captured R6 builder used |
| Public predecessor monkey-patch after R7 import | Rejected; saved original checks remain active |
| Full self-consistent forged package | Complete 24-attempt/56-file package rejected at nonexistent Git commit anchor |
| Archive valid package | Accepted by archive verifier |
| Archive extra member, expected-member symlink and content mismatch | Rejected |
| Direct R7 type helper on canonical CUDA package | **False-rejected — L-1; official route unaffected** |

The full forged package contained all 24 attempts, 56 files, report/proposal, SQLite ledger, JSONL,
manifest and archive. It used the fifteen-file R7 source roster and canonical R7 telemetry, but the
official verifier rejected its nonexistent Git commit before certification. R7's captured
`BASE_BUILD_PLAN` also built the exact 24-row/15-source plan both before and after hardening was
installed; the earlier dynamic-recursion defect was not present in the frozen bytes.

## Preserved controls

- The experiment remains exactly 24 isolated attempts:
  `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}`.
- All repetitions remain mandatory. Throughput population CV must be at most 5%; peak VRAM must be
  at most 80%, preserving at least 20% measured headroom.
- Selection remains deterministic and resistant to omission/reordering/cherry-picking: among
  candidates within 95% of best median throughput, choose smaller batch, fewer workers, then lower
  VRAM.
- Effective-batch replay, loader-gap arithmetic and fail-closed OOM classification remain intact.
- SQLite no-follow/link/inode safeguards, exact execution JSONL, manifest inventory and archive
  member/content replay remain intact.
- Plan/report/proposal/manifest governance markers remain exact booleans. The proposal remains
  `PROPOSAL_NOT_OWNER_APPROVED`; the report remains explicitly not model-quality evidence.
- Static inspection found no test export, `--final-eval`, Pilot R3 import/notebook route or
  sealed-test access-log route in R7 production source.
- All synthetic evidence retained `sealed_test_accessed=false`; the sealed test was not opened.
- No Colab execution, training, upload, commit or push occurred. The live Pilot R3 was not read,
  mutated or coupled to this QA round.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Graft freshness/source trace | Source query refreshed R7 and saved about 17,635 tokens (about USD 0.01); final graph rebuilt/check OK |
| Root R1–R7 targeted tests | PASS, `86 passed, 1 skipped`; skip is root environment without Torch |
| Complete detector tests | PASS, `105 passed` |
| Repository verifier matrix | PASS, `52/52` |
| Scoped Ruff over R1–R7 source/tests | PASS |
| Root lock | PASS, `168 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before record | PASS |
| Portable canonical environment and R6 telemetry regression probes | PASS |
| Forged CUDA/driver identity probe | **Accepted — High blocker** |
| Direct R7 type-helper canonical-package probe | **False-rejected — Low finding** |
| Exact total-VRAM identity probe | **Tiny drift accepted — Low finding** |
| Full fake 24-attempt package | Rejected at independent Git anchor |
| Path/SQLite, execution, batch, OOM, selection, source/delegation and archive attacks | PASS |

Green unit, verifier and mechanical checks cannot reverse the accepted negative identity tests.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R7 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending append-only successor + independent QA PASS** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |
