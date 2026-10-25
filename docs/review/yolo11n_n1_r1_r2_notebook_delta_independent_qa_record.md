# YOLO11n N1 R1-R2 notebook delta independent QA record

Date: 2026-10-25 (Asia/Ho_Chi_Minh)  
Verdict: **PASS**  
Reviewer: independent QA session `/root/yolo11n_dual_track_r1_source_qa`

## Scope

This review covers only the append-only R1-R2 fresh/resume smoke notebook delta and its deterministic
builder/tests. It is a static QA result; no Colab execution, training, upload, commit, push,
evaluation or sealed-test access occurred.

## Immutable source and QA binding

| Item | SHA-256 / commit |
| --- | --- |
| Source commit | `0ec545183bf29de035f440bb0307842ae132f4ca` |
| `docs/review/yolo11n_n1_r1_r2_source_independent_qa_record.md` | `5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a` |
| `scripts/build_yolo11n_n1_r1_r2_notebooks.py` | `e782711ed9bffbacac02ea42eb849402f150d8cc13c727501c5e678d60e86cc0` |
| `tests/test_yolo11n_n1_r1_r2_notebooks.py` | `3adfa274d4aa351c644aaf06ec13ae4c999d69ff912992c69d4d114629eeabe4` |
| `detector/colab/yolo11n_n1_r1_r2_fresh.ipynb` | `a2ee432045ebdaf76a82d4112e4608ac35903124d315e53bcd6075725af8fcaa` |
| `detector/colab/yolo11n_n1_r1_r2_resume.ipynb` | `45d57c2684db25fec573242293ba8403a98ee0487c9c8855fab49744d51d5c63` |

The source commit is reachable from `origin/codex/yolo11n-dual-track-r1`. Readback from that commit
reproduced the composite source-QA hash above and repair-runner SHA-256
`cd3edab0adee25c8642f840edb36d899687ba952bdfcbaca853568f65dcd72e6`.
The composite record has exactly one canonical unqualified PASS verdict and the real
`require_source_qa` path accepts it against the extracted real bundle.

## Delta and reproducibility evidence

- The R1-R2 notebooks differ from the R1-R1 notebooks only in the title/status and the immutable
  source commit, source-QA SHA-256 and source-QA path. Runner
  `run_yolo11n_n1_r1_r1.py`, state `yolo11n_n1_seed_20261018_r1_r1`, bundle, manifest, official
  `yolo11n.pt` hash and all execution commands are byte-preserved.
- Two builds in an isolated temporary mirror produced identical result metadata and identical
  notebook bytes. Both generated notebooks were byte-identical to the reviewed repository files.
- Both notebooks require exact `NVIDIA L4`, detached checkout of the pinned commit, a clean checkout,
  the pinned composite QA file, train/validation-only manifest policy and
  `sealed_test_accessed=false`.
- Fresh is fixed to epoch 1 and refuses an existing state. Resume is fixed to epoch 2, requires one
  prior fresh attempt and rejects reuse of the same hostname-plus-boot-id runtime digest.
- Every code cell is unexecuted, output-free and compiles. There is no old source-QA binding, test
  export, final-evaluation option, test split route, smoke-proof argument or unrestricted/long-run
  command.

## Checks reproduced

- Scoped Ruff: PASS.
- Targeted notebook tests in the isolated mirror: 2 passed, zero failures.
- Static adversarial checks: stale QA binding injection and missing immutable QA-path injection were
  both rejected by the real builder guard.
- Exact pin, metadata, code-cell, smoke-sequence, different-runtime, sealed-test closure and
  forbidden-route assertions: PASS.
- Graft graph check after freshness-aware query: OK.

## Boundary

This PASS approves only the static R1-R2 notebook delta. It does not authorize commit, push,
upload, Colab execution, epoch-1/epoch-2 smoke, long training, evaluation, publication, model
acceptance, deployment or sealed-test access. `sealed_test_accessed=false`.
