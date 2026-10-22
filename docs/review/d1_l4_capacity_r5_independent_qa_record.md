# D1 L4 capacity successor R5 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — APPEND-ONLY SUCCESSOR REQUIRED**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 0 Critical, 1 High, 2 Medium, 1 Low.**

R5 closes the exact R4 blocker. Integer/float/string/null substitutes are rejected for the remaining
governance booleans across plan, report, proposal, manifest, plan/report environments, result and
telemetry. The inherited candidate/repetition OOM, proposal, train-argument and execution checks
also continue to reject boolean/numeric equality confusion at their previously reviewed fields.

The expanded attack sweep found four additional gaps. The independent environment anchor accepts a
boolean as the clean-worktree count and does not validate the exact environment schema or recorded
software identity types. Raw timing/GPU telemetry accepts non-canonical types and incomplete sample
schemas. The evidence manifest accepts an arbitrary terminal status. Finally, the candidate policy
validator accepts booleans for zero-valued aggregate numeric fields, although the full report's
canonical hash provides a downstream distinction for that last case. R5 remains NO-GO and must be
superseded append-only.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r5.py` | `84c3252105e42abc96a69dd53b149a1a307607b9b908ac41d7e65c7fdcaef913` |
| `detector/colab/verify_d1_l4_capacity_r5.py` | `46fa410f247c5501b21545646dfeba506d17e3c82cc357fb3ccadd93d6c4d2ac` |
| `tests/test_d1_l4_capacity_r5.py` | `9b79f9d087d500149baa89c9f956c7609bf6426a86bbfcd4cdbfe8c7825e3d26` |
| `docs/review/d1_l4_capacity_r5_qa_remediation_report.md` | `f1dedb4995ca81d98978dfb8525b6cda579243d6ccc7c065437ade17057d3a9d` |

The R1–R4 independent QA records remain byte-identical at SHA-256
`37ce181cee90df4c020fc81a3558825226201b8368e6220903c4b1721b3398dd`,
`94c9c2a00fd3f5c6865fbfc463c7c9b1d6f392c79e474cd06f0d4945a2ff4dce`,
`46cedcedd57cc97b901a09b1bd0a73000cc6171720b5064fdeac0eabe47adeb9`, and
`a928b9019736ddf5836feb924da9ec4dbe154f9380042c93da32c48526e06489`. Their historical FAIL
verdicts were not modified. Existing PM changes and unrelated artifacts were outside this QA scope
and were preserved.

## Findings

### H-1 — Environment anchor is neither exact-schema nor exact-type reproducibility evidence

R5 adds exact booleans for `mps_available` and `cuda_available`, but the inherited independent
anchor at `verify_d1_l4_capacity_r2.py:169-185` validates only a subset of the environment. In
particular, it compares `git_dirty_files != 0`, under which JSON boolean `false` is accepted as
integer zero. It does not require the exact environment key set or exact string types for Python,
platform, hardware, PyTorch, Ultralytics, CUDA and driver identity. It also permits extra keys.

An isolated call through the real inherited anchor with the R5 eleven-file source roster, while
replacing only Git/model/data external lookups with matching controlled anchors, produced:

```text
environment_git_dirty_bool_false_and_forged_identity ACCEPTED_BY_INHERITED_ANCHOR
```

The accepted record used `git_dirty_files: false`, `python: false`, forged Torch/Ultralytics values
and an extra environment key. The policy report also accepted the same dirty boolean and forged
versions:

```text
build_report_git_dirty_bool_and_forged_versions ACCEPTED
```

The repository already has a stricter reusable validator at `detector/m1/contract.py:444-488`; it
rejected the attack because identity fields were not exact non-empty strings. The capacity verifier
does not invoke an equivalent extended-L4 validation.

This does not bypass the Git commit/source, approved model or governed data anchors and does not
show sealed-test access. It does allow a verified capacity package to make false clean-worktree and
software-runtime claims, which directly undermines reproducibility and comparison of L4 benchmark
results.

**Required successor repair:** enforce an exact extended environment schema, reuse or mirror
`validate_environment_record(..., require_clean=True)`, require `git_dirty_files` to be exact
integer zero, require exact types for GPU UUID and finite VRAM, reject extra keys, and require plan
and report environments to match exactly before replay.

### M-1 — Raw timing and GPU telemetry replay accepts non-canonical types and schemas

The R2/R3 timing replay requires the top-level step key set and valid image/timing arithmetic, but
does not type-check or sequence-check `batch_index`. `planned_batch` and `trainer_batch_size` use
ordinary equality, so floating-point `4.0` passes as planned integer `4`. The inherited attempt
replay checks selected GPU sample values but not the exact sample schema, timestamp, temperature or
exact numeric types.

An otherwise valid attempt used boolean/string batch indices, floating-point planned/effective
batches, boolean GPU numeric fields and GPU samples with no `time` or `temperature_celsius`. Both
the raw attempt replay and the final effective-batch chain accepted it:

```text
r1_attempt_replay ACCEPTED
r3_effective_batch_chain ACCEPTED
telemetry_attack=batch_index_bool_or_str,planned_and_trainer_batch_float,
gpu_numeric_bool,gpu_missing_time_temperature
```

Images and timing components remained mathematically valid, so this is not an auto-batch, loader-gap
or throughput-selection bypass. It is a raw-evidence schema and reproducibility failure: evidence
claimed to be replayed exactly can omit or change fields the live runner always emits.

**Required successor repair:** require the exact step and GPU-sample schemas; exact integer,
floating-point and string types; consecutive expected batch indices; finite physical bounds; and
timezone-aware, chronologically ordered sample timestamps. Add the combined attack to the full
verifier chain.

### M-2 — Evidence manifest terminal status and exact schema are not verified

`verify_d1_l4_capacity_r1.py:342-390` checks the manifest self-hash, plan binding, sealed marker,
file hashes/inventory and archive bytes, but it never requires `status == "EVIDENCE_PACKAGED"` or
an exact top-level manifest schema. R3 checks only the schema-version type/value and R5 checks the
sealed boolean.

Two separately re-hashed manifests with valid file inventory and archives produced:

```text
manifest_status='FORGED_STATUS' ACCEPTED_BY_ARCHIVE_VERIFIER
manifest_status=False ACCEPTED_BY_ARCHIVE_VERIFIER
```

The archive verifier correctly rejected an extra member, a symbolic-link member and mismatched
member bytes, so the finding is limited to manifest schema/governance rather than archive-content
hashing.

**Required successor repair:** require the exact manifest key set and exact
`status="EVIDENCE_PACKAGED"`; type-check every file row and reject duplicate or non-canonical path
rows before opening the archive.

### L-1 — Candidate zero aggregates accept booleans in the standalone policy validator

`l4_capacity.validate_candidate()` compares recomputed numeric aggregates with a branch that treats
only exact integers/floats as numeric, then falls back to ordinary equality. For OOM and FAILED
candidates, replacing the nine zero aggregate fields with boolean `false` was accepted for both
statuses:

```text
OOM candidate_zero_aggregates_as_false ACCEPTED
FAILED candidate_zero_aggregates_as_false ACCEPTED
```

The raw repetition validator rejects booleans, and a post-aggregation mutation in the complete
package changes the canonical report evidence hash, so this probe did not yield a verified full
package. It is nevertheless inconsistent with the claimed exhaustive type-strict policy layer.

**Required successor repair:** exact-type validate every candidate aggregate before arithmetic or
equality comparison and add OOM/FAILED zero-value boolean regression cases.

## Predecessor and full-chain attack matrix

| Attack class | Independent R5 result |
| --- | --- |
| R4 report `not_model_quality_evidence: 1` | Rejected |
| Plan/report/proposal/manifest sealed marker integer substitutes | Rejected |
| Plan/report environment CUDA/MPS integer substitutes | Rejected |
| Result/telemetry/candidate/repetition OOM integer substitutes | Rejected |
| Train-argument and proposal-selection boolean integer substitutes | Rejected |
| Plan/report profile, identities, seeds and proposal numeric equality substitutes | Rejected |
| Execution wrong-type schema/status/time/hash/sealed fields | Rejected |
| Execution duplicate/non-finite/extra/non-increasing chronology | Rejected |
| Effective batch: one full step | Accepted as valid |
| Effective batch: one partial step only | Rejected |
| Effective batch: full plus one final partial | Accepted as valid |
| Effective batch: multiple or non-final partials | Rejected |
| Ultralytics effective trainer batch differs from plan | Rejected by the live callback |
| Loader wait omitted from throughput | Rejected; measured total preserves compute plus inter-batch gap |
| Generic failure relabelled OOM | Rejected; controlled CUDA OOM remains accepted |
| SQLite root/ancestor/file symlink and hard link | Rejected before external writes; external row count remained zero |
| Missing R5 source from roster | Rejected |
| Public predecessor type-check monkey-patch after R5 import | Rejected; saved predecessor and R5 checks remained active |
| Fake full package | Complete 24-attempt/56-file package with eleven-source roster and fake Git/model/data rejected at the fake Git commit anchor |
| Environment dirty/type/identity attack | **Accepted — H-1** |
| Raw step/GPU telemetry schema/type attack | **Accepted — M-1** |
| Manifest forged/boolean status | **Accepted — M-2** |
| Candidate zero aggregates as booleans | **Accepted by policy validator; downstream report hash still distinguishes — L-1** |

R5 uses an eleven-file append-only source roster: the governed capacity policy plus R1–R5
runner/verifier pairs. The actual candidate subprocess entry is R5. Current and claimed committed
source hashes must match through the inherited independent anchor. Since R5 is intentionally
uncommitted pending QA, a positive clean-commit R5 artifact cannot be produced; this FAIL blocks
that next gate.

## Preserved controls

- The fixed experiment remains exactly 24 isolated attempts:
  `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}`.
- All three repetitions remain mandatory. Throughput CV must be ≤ 5%, peak VRAM must be ≤ 80%, and
  therefore measured headroom remains at least 20%.
- Candidate selection remains deterministic and resistant to omission/reordering/cherry-picking:
  within 95% of best median throughput, choose smaller batch, fewer workers, then lower VRAM.
- OOM evidence uses the closed allowlist; data-loader, bundle, hash and generic runtime errors remain
  `FAILED`.
- SQLite no-follow, link-count and inode checks remain effective for creation and later writes.
- Archive member inventory, type and content hashes remain effective despite M-2's manifest-status
  gap.
- Static inspection found no test export, `--final-eval`, Pilot R3 import, pilot notebook route or
  sealed-test log route in R5 production source.
- All observed governance markers remained `sealed_test_accessed=false`; the sealed test was not
  opened.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Root R1–R5 targeted tests | PASS, `57 passed, 1 skipped`; skip is root environment without Torch |
| Complete detector tests | PASS, `105 passed` |
| Scoped Ruff over reviewed R1–R5 source/tests | PASS |
| Root lock | PASS, `168 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before record | PASS |
| Graft freshness/source trace | PASS, graph in sync |
| R5 boolean/numeric direct matrix | Intended R4/R5 fields rejected; environment and manifest gaps accepted as reported |
| Execution exact-type matrix | PASS |
| Effective-batch sequence matrix | PASS |
| Full fake 24-attempt package | Rejected at independent Git anchor |
| Environment anchor attack | **ACCEPTED — High blocker** |
| Raw telemetry attack | **ACCEPTED — Medium blocker** |
| Manifest governance attack | **ACCEPTED — Medium blocker** |
| Candidate aggregate type attack | **ACCEPTED — Low finding** |

Green unit and mechanical checks cannot reverse accepted negative tests.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R5 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending append-only successor + independent QA PASS** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |
