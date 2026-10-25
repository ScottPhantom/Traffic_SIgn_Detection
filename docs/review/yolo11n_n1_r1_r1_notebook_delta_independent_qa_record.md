# YOLO11n N1 R1-R1 notebook-delta independent QA record

Date: 2026-10-25 (Asia/Ho_Chi_Minh)  
Verdict: **PASS — STATIC NOTEBOOK DELTA ONLY**  
Reviewer: independent QA session `/root/yolo11n_dual_track_r1_source_qa`

## Pinned reviewed files

| File | SHA-256 |
| --- | --- |
| `scripts/build_yolo11n_n1_r1_r1_notebooks.py` | `86186acbd48e24d2ac6de38c83d7124cf554ed1e4c0849a2f81656997027788b` |
| `tests/test_yolo11n_n1_r1_r1_notebooks.py` | `ad30d0e0c79e90e2087eedd7ec9d9de286eefed7e023f5cd277b39b98582d5f8` |
| `detector/colab/yolo11n_n1_r1_r1_fresh.ipynb` | `316b59915eebc88670814ed37d7395f6f563eebc20afa8643e029203678fa048` |
| `detector/colab/yolo11n_n1_r1_r1_resume.ipynb` | `8b0b7233be58b352a3f251dc5ced529e13f222ef55140a19028b519d98f5a3ee` |

## Verified bindings

- Both notebooks pin source commit `2d5ccdd17d5cb778cb3f7fb2588446eef4816c91`, which is reachable on
  `origin/codex/yolo11n-dual-track-r1`.
- Both pin `docs/review/yolo11n_n1_r1_r1_source_independent_qa_record.md` with SHA-256
  `57eb794e7256f1797a2961286330a98baa9a87664c9c6d84b84fe9ffda332254`.
- Both invoke `run_yolo11n_n1_r1_r1.py` and target only
  `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`.
- Bundle, manifest and official `yolo11n.pt` hashes are unchanged from the Owner-approved R1
  package.
- Preflight requires exact `NVIDIA L4`. Fresh mode stops after epoch 1 and refuses an existing
  state. Resume mode stops after epoch 2, requires the epoch-1 pointer and a different runtime
  digest.
- Package and execution checks keep `test_included=false` and `sealed_test_accessed=false`.
- Neither notebook contains the old runner path, failed-state exact terminal path, test export,
  final evaluation, test split, smoke-proof option, or a long-run command.

## Reproduced checks

- Two independent rebuilds in a temporary directory were byte-identical to each other and to the
  reviewed repository notebooks.
- Targeted pytest: **2 passed**.
- Ruff: PASS.
- Static compiler, pin and route attacks: PASS.
- Graft graph: OK.

## Boundary

This PASS accepts only the static notebook delta. It does not certify a Colab runtime, checkpoint,
resume behavior, model quality, or long training. The remaining sequence is fresh epoch 1 on L4,
resume epoch 2 on a genuinely different L4, then independent artifact QA. Long training stays
blocked until those gates pass.

`sealed_test_accessed=false`.
