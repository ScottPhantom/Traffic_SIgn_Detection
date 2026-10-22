# D1 L4 capacity successor R6 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — APPEND-ONLY SUCCESSOR REQUIRED**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 0 Critical, 1 High, 1 Medium.**

R6 closes all four recorded R5 defects: the environment, manifest, GPU-sample and report-aggregate
schemas are now substantially stricter, and predecessor controls still reject the effective-batch,
OOM, SQLite, execution-journal, archive, source-roster and full-package forgery attacks. However,
the new environment verifier rejects the exact Torch identity recorded by the project's verified
Colab L4 run because it compares a CUDA build string against the local verifier host's package
metadata. The raw telemetry verifier also checks types and finiteness but still accepts impossible
batch-index chronology, reversed/duplicate sample time and negative physical measurements. R6 is
therefore NO-GO and must be superseded append-only.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r6.py` | `8cd0401705b83c86ec35d909f8c88729d80c7643fe2cca86a8fd2c72b22cc644` |
| `detector/colab/verify_d1_l4_capacity_r6.py` | `fd09f4e718c979b7224eff3280fd2005462b2103aaa2bd61d02f89538b83de83` |
| `tests/test_d1_l4_capacity_r6.py` | `6e1a47e7163ac09fd1b2fb987a00577b684bea46c0f5f3c9b3d851fe02c3c633` |
| `docs/review/d1_l4_capacity_r6_qa_remediation_report.md` | `a90ee29b65e2a3b759c38b9afd504c50a45dce5f7f2ad01c9bb5d4bc935af484` |

The R1–R5 independent QA records remain byte-identical at SHA-256
`37ce181cee90df4c020fc81a3558825226201b8368e6220903c4b1721b3398dd`,
`94c9c2a00fd3f5c6865fbfc463c7c9b1d6f392c79e474cd06f0d4945a2ff4dce`,
`46cedcedd57cc97b901a09b1bd0a73000cc6171720b5064fdeac0eabe47adeb9`,
`a928b9019736ddf5836feb924da9ec4dbe154f9380042c93da32c48526e06489` and
`895d1903871df9d5444899d1a5357eb5c29f1d3e16a99aa613f3e135b9755b40`. Their historical FAIL
verdicts were not modified. Existing PM changes and unrelated artifacts were outside this QA scope
and were preserved.

## Findings

### H-1 — Valid Colab Torch identity is coupled to the verifier host and falsely rejected

`verify_d1_l4_capacity_r6.py:72-82` compares the evidence field `torch` to
`importlib.metadata.version("torch")` on the machine running the verifier. The governed producer,
however, records `torch.__version__` in `detector/m1/contract.py`, which includes the CUDA local
version suffix on Colab. The project's independently verified L4 artifact records Python `3.12.3`,
Torch `2.14.1+cu130` and Ultralytics `8.4.172` in
`docs/review/d1_checkpoint_resume_r4_r6_l4_artifact_independent_qa_record.md:92-98`.

The current Python constraint correctly accepted `3.12.3`, but the exact environment probe on the
local QA host produced:

```text
2.14.1+cu130 REJECTED RuntimeError Colab torch=2.14.1+cu130 identity differs: torch
2.14.1 ACCEPTED
```

The local detector metadata is `2.14.1`; it is not the identity emitted by the valid Colab CUDA
runtime. Thus a canonical-shaped, previously observed Colab environment cannot pass independent
verification on the M1 QA host. This is a reproducibility/portability blocker, not proof of forged
evidence acceptance.

**Required successor repair:** validate the recorded Torch version against the pinned detector
dependency using a deliberately specified normalization rule that preserves and separately checks
the CUDA build/runtime identity. Do not bind evidence validity to the verifier host's platform
wheel string. Add a regression with the real `2.14.1+cu130` Colab record and a local `2.14.1`
verifier host.

### M-1 — Raw telemetry chronology and physical ranges are not replayed

`verify_d1_l4_capacity_r6.py:117-137` requires exact primitive types, exact GPU-sample keys and
finite numbers, but it does not require measured `batch_index` values to be positive, consecutive
or ordered. GPU timestamps only need to be individually parseable; they need not be ordered or
fall within the attempt interval. The verifier also applies no physical bounds to temperature or
power. Inherited replay does not consume those fields.

An otherwise canonical successful attempt was modified to contain:

```text
batch_index=[999,-1,999,0,0,5,2,2,1,1]
GPU time=[2026-10-21T05:00:00+00:00,
          2026-10-20T00:00:00+00:00,
          2026-10-20T00:00:00+00:00]
first power_watts=-5.0
first temperature_celsius=-999.0
```

After recomputing the raw/result binding, all three relevant layers accepted it:

```text
r6_types ACCEPTED_INVALID_TELEMETRY
r1_replay ACCEPTED_INVALID_TELEMETRY
r3_hardening ACCEPTED_INVALID_TELEMETRY
```

The attack does not alter effective batch, loader-gap arithmetic, throughput, peak VRAM or selection
in this construction. It does show that the claimed exact raw evidence can contain impossible or
non-chronological observations without detection.

**Required successor repair:** require the measured batch-index sequence produced by the governed
runner (including its warm-up offset), require GPU sample timestamps to be strictly chronological
and within the attempt start/finish interval, and replay the producer's physical range invariants
for utilization, memory, power and temperature. Add a combined full-attempt regression.

## Predecessor and R6 attack matrix

| Attack class | Independent R6 result |
| --- | --- |
| Exact extended environment schema; dirty boolean; extra key; exact Python 3.12 range | Rejected/accepted as intended |
| Canonical observed Colab Torch `2.14.1+cu130` on local QA host | **False-rejected — H-1** |
| Manifest false/forged status, extra key, malformed row and boolean size | Rejected |
| Candidate/repetition boolean counts, boolean/non-finite/string metrics | Rejected |
| Plan/report/proposal/manifest governance booleans and nested numeric equality confusion | Rejected |
| Execution wrong-type, duplicate/non-finite/extra fields and non-increasing chronology | Rejected |
| Effective batch: one full step | Accepted as valid |
| Effective batch: one partial step only | Rejected |
| Effective batch: full plus one final partial | Accepted as valid |
| Effective batch: multiple or non-final partials | Rejected |
| Ultralytics trainer batch differs from planned batch | Rejected by live callback/replay |
| Loader wait omitted from throughput | Rejected; total step time preserves compute plus inter-batch gap |
| Generic failure relabelled OOM | Rejected; controlled CUDA OOM remains accepted |
| SQLite root/ancestor/file symlink and database hard link | Rejected; external ledger remained unchanged |
| R6 source roster/candidate entry | Exactly 13 unique files; entry resolves to R6 |
| Missing/replaced source or public predecessor monkey-patch | Rejected; saved original checks and R6 roster remain active |
| Full self-consistent forged package | Complete 24-attempt/56-file package rejected at nonexistent Git commit anchor |
| Archive valid package | Accepted by archive verifier |
| Archive extra member, expected-member symlink and content mismatch | Rejected |
| Invalid step-index sequence, GPU chronology, negative power/temperature | **Accepted — M-1** |

R6 uses a thirteen-file append-only source roster: the governed capacity policy plus R1–R6
runner/verifier pairs. The candidate command resolves to `run_d1_l4_capacity_r6.py`; changing the
unused predecessor `runner` argument did not redirect it. The full forged package contained all 24
attempts, 56 files, report/proposal, SQLite ledger, JSONL, manifest and archive, but was rejected by
the independent fake Git commit anchor before it could be certified.

## Preserved controls

- The fixed experiment is exactly 24 attempts:
  `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}`.
- All three repetitions remain mandatory. Throughput CV must be at most 5% and peak VRAM at most
  80%, retaining at least 20% measured headroom.
- Candidate omission, duplication and reordering fail. Within 95% of best median throughput, the
  deterministic order remains smaller batch, fewer workers, then lower VRAM.
- Effective-batch validation accepts a single full batch or full batches plus one final partial,
  and rejects an all-partial, repeated-partial or non-final-partial sequence.
- OOM classification remains fail-closed. Data-loader, bundle, hash and generic failures are not
  silently relabelled as OOM.
- SQLite no-follow, one-link and inode checks; execution JSONL strict parsing; manifest inventory;
  and archive member/content verification remain effective.
- Static inspection found no test export, `--final-eval`, Pilot R3 import/notebook route or
  sealed-test access-log route in R6 production source.
- All synthetic evidence retained `sealed_test_accessed=false`; the sealed test was not opened.
- No Colab execution, training, upload, commit or push occurred in this QA round. Current Pilot R3
  was not read, mutated or coupled to the capacity candidate.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Graft freshness/source trace | PASS; graph in sync; source query saved about 19,239 tokens (about USD 0.01) |
| Root R1–R6 targeted tests | PASS, `70 passed, 1 skipped`; skip is root environment without Torch |
| Complete detector tests | PASS, `105 passed` |
| Scoped Ruff over reviewed R1–R6 source/tests | PASS |
| Root lock | PASS, `168 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before record | PASS |
| Exact environment probe | **Valid Colab Torch build false-rejected — High blocker** |
| Exact telemetry/full-attempt replay probe | **Invalid chronology/ranges accepted — Medium blocker** |
| Full fake 24-attempt package | Rejected at independent Git anchor |
| Path/SQLite, execution, batch, OOM, source-roster and archive attack matrix | PASS except M-1 |

Green unit and mechanical checks cannot reverse accepted negative tests or the valid-artifact false
rejection.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R6 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending append-only successor + independent QA PASS** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |
