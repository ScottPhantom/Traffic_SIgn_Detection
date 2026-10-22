# D1 L4 capacity successor R4 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — APPEND-ONLY SUCCESSOR REQUIRED**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 0 Critical, 0 High, 1 Medium, 0 Low.**

R4 closes the R3 nested plan/telemetry identity and schema-version finding. It rejects boolean or
float substitutions for integer plan, telemetry, result, report and proposal fields; rejects an
unsupported telemetry schema version; preserves the effective-batch, loader timing, OOM, SQLite,
archive and independent-anchor controls; and extends the source-at-commit roster to the R4 pair.

One exact-type governance gap remains. The real R4 type checker accepts integer `1` for the report's
top-level `not_model_quality_evidence` marker even though the canonical report requires boolean
`true`. Python also considers `1 == True`, so plain semantic equality does not distinguish the two.
The canonical evidence hash is an additional downstream distinction, but it does not repair the
claimed type-strict schema check or make an accepted negative type test acceptable. R4 therefore
remains NO-GO and must be superseded append-only.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r4.py` | `fc93ccbd12ed6a1a421d2406979e1ab211bc1e6a3b5f3cad0612960a12de57f4` |
| `detector/colab/verify_d1_l4_capacity_r4.py` | `69481565793ee8f6eb2bcd6555e52cd7ce55438471084ac521e06e1b171114f2` |
| `tests/test_d1_l4_capacity_r4.py` | `2bec2f7ab0c389b578f2bfdfe3dfa67ee674b78ac293fe5b9a35190226dbea1d` |
| `docs/review/d1_l4_capacity_r4_qa_remediation_report.md` | `0a848e57322bacd27c8aad5d3c2cf063c02080046c10745e24f558fad30c1c5b` |

The R1, R2 and R3 independent QA records remain byte-identical at SHA-256
`37ce181cee90df4c020fc81a3558825226201b8368e6220903c4b1721b3398dd`,
`94c9c2a00fd3f5c6865fbfc463c7c9b1d6f392c79e474cd06f0d4945a2ff4dce`, and
`46cedcedd57cc97b901a09b1bd0a73000cc6171720b5064fdeac0eabe47adeb9`. Their historical FAIL
verdicts were not modified. Existing PM changes, the append-only R5 work begun after R4 was frozen,
and unrelated untracked artifacts were outside this QA scope and were preserved.

## Finding

### M-1 — Report model-quality disclaimer is not exact-boolean checked

`verify_d1_l4_capacity_r4.py:46-94` invokes the predecessor type checks and adds strict nested
profile, identity, candidate, repetition and proposal checks. It does not check the top-level
`report["not_model_quality_evidence"]` field. The canonical builder emits boolean `true` at
`detector/m1/l4_capacity.py:463`, while inherited replay ultimately compares report dictionaries at
`verify_d1_l4_capacity_r1.py:316` using Python equality.

An independent minimal artifact tree with every checked field valid except
`not_model_quality_evidence: 1` produced:

```text
report_not_model_quality_evidence_int_1 ACCEPTED
python_semantic_equality True
```

This is not evidence of sealed-test access, a model-quality result, or an exploitable forged full
package; the canonical report hash remains an additional downstream binding. It is evidence that
R4's claimed exact-type governance layer accepts a non-canonical boolean-valued field and lacks a
regression test for it.

**Required successor repair:** require the report field to have exact type `bool` and exact value
`True`, audit all remaining boolean-valued governance fields for the same equality confusion, and
add both direct and full verifier-chain regression attacks.

## R1–R3 attack replay

| Attack class | Independent R4 result |
| --- | --- |
| R3 plan `repeat: true` equality confusion | Rejected |
| R3 telemetry `repeat: true` equality confusion | Rejected |
| Telemetry integer schema version other than `1` | Rejected |
| Result identity boolean/float substitutions | Rejected |
| Train-argument integer/boolean substitutions | Rejected |
| Plan/report profile integer/boolean substitutions | Rejected |
| Proposal integer/float/boolean substitutions | Rejected |
| Effective batch: one full step | Accepted as valid |
| Effective batch: one partial step only | Rejected because no full planned batch was observed |
| Effective batch: full plus one final partial | Accepted as valid |
| Effective batch: multiple or non-final partials | Rejected |
| Ultralytics effective trainer batch differs from plan | Rejected by inherited live callback |
| Loader wait omitted from throughput | Rejected: injected timing preserved `compute=2`, loader gap `3`, total `5` seconds |
| Predecessor-validator delegation bypass | Rejected; the saved verifier references and R4 checks remained active |
| Fake full package | Complete 24-attempt/56-file package with nine-source roster, fake Git/model/data, extra optimizer and invalid batch-16 evidence was rejected at the independent Git anchor |
| Missing R4 files from source roster | Rejected; R4 requires the nine-file append-only roster |
| Extra optimizer | Rejected by inherited exact train-argument roster |
| Generic failure relabelled OOM | Rejected; controlled CUDA OOM remained accepted |
| SQLite root/ancestor/file symlink and hard link | All rejected before an external write; external row count remained zero |
| Execution duplicate/non-finite/extra/chronology attacks | Rejected |
| Execution exact type matrix | Wrong-type schema, status, timestamp, plan/report hash and sealed marker values were rejected |
| Report `not_model_quality_evidence: 1` | **Accepted by R4 type checker — M-1** |

The R4 source-at-commit design extends the exact roster to nine files: the governed capacity policy
plus the R1, R2, R3 and R4 runner/verifier pairs. The claimed repository must be the governed
checkout, and each current source hash must match `git show <commit>:<path>`. Since this source
candidate is intentionally uncommitted pending QA, a positive clean-commit R4 package cannot be
produced; the current FAIL prevents that next gate.

## Preserved controls

- The fixed experiment remains 24 isolated attempts:
  `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}`.
- Eligibility still requires all three repetitions, throughput CV ≤ 5%, and peak VRAM ≤ 80%, which
  preserves at least 20% measured headroom.
- Selection remains deterministic and non-cherry-pick: among candidates within 95% of the best
  median throughput, choose smaller batch, fewer workers, then lower VRAM.
- OOM evidence uses the closed R2 predicate; generic loader, bundle, hash and runtime errors remain
  `FAILED`.
- SQLite uses no-follow exclusive creation plus component, file-type, hard-link and inode checks on
  later opens.
- Static inspection found no `export-test`, `--final-eval`, Pilot R3 import, pilot notebook route or
  test-export path in R4 production source. The capacity work remains train/val-only and independent
  of the live Pilot R3.
- All observed governance markers remained `sealed_test_accessed=false`; the sealed test was not
  opened.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Root R1–R4 targeted tests | PASS, `48 passed, 1 skipped`; skip is root environment without Torch |
| Complete detector tests | PASS, `105 passed` |
| Scoped Ruff over reviewed R1–R4 source/tests | PASS |
| Root lock | PASS, `66 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before record | PASS |
| Graft freshness/source trace | PASS, graph in sync |
| Effective-batch sequence matrix | PASS |
| Execution exact-type field matrix | PASS |
| Full fake 24-attempt package | Rejected at independent Git anchor |
| Report model-quality disclaimer type probe | **ACCEPTED — Medium blocker** |

Green unit and mechanical checks cannot reverse the accepted negative test.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R4 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending append-only successor + independent QA PASS** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |
