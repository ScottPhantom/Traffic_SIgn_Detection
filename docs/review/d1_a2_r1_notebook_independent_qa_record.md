# D1-A2-R1 notebook independent QA record

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`).
Reviewer: separate Codex QA agent `/root/a2_notebook_qa`; this agent did not author the notebook or operate Colab.
Boundary: notebook source and static checks only. No training, Drive write, Colab execution, push, result evaluation, or sealed-test access. `sealed_test_accessed=false`.

Verdict: PASS — the A2 notebook is ready for the separately gated fresh L4 smoke; live artifact QA and resume are not covered by this verdict.

## Reviewed authority and identity

- Notebook: `detector/colab/d1_train_a2_r1.ipynb`, SHA-256 `9c1b93b0eacf6aa786847d6b19310813fc97904e040f05654b12fefea09f3669`.
- Contract: `docs/review/d1_a2_r1_run_contract.md`, SHA-256 `1ce153656f2c6c7a7700bdbf57f4d9c1205184ef07bf18a0fd912056e2f396e1`.
- A2 launcher: `detector/colab/run_d1_colab_a2_r1.py`, SHA-256 `a6bb6e684701b5a95bd03b71bac777693ec08f1ccb853c98edb2cefdcec2d6de`.
- Source QA records: `d1_a2_r1_source_independent_qa_record.md` SHA-256 `40996d151b5feac9c84fcb13db642a0101686409fee4c314207c2bb170fca8a1`, and `d1_a2_r1_source_independent_qa_record_r2.md` SHA-256 `ea84adcc28e24bd2a6648a0c8328d1de6d9441b9efbf3cee0d259554000a3ef3`.
- Owner authorization: `docs/review/d1_a2_r1_owner_authorization_2026-11-05.md`, SHA-256 `1a11b283da34848dc873b577b42240a5182b795654f5a3db9349369ae78221c9`; present in Git commit `f3f7571794a5db04ad302fecf8014546ec1eb255`, regular file with one link and a filename without the forbidden `test` substring.
- `graft check .`: graph in sync. The local branch HEAD is commit A `f3f7571794a5db04ad302fecf8014546ec1eb255`. The notebook itself is not yet committed, as expected before commit B.

## Notebook delta and controls

1. The code cell pins full `CODE_COMMIT=f3f7571794a5db04ad302fecf8014546ec1eb255`, clones the GitHub repository, checks out that commit detached, checks `HEAD`, and requires `git status --porcelain --untracked-files=all` to be empty. There is no base64 overlay or source write. This addresses source-QA C1; the separate notebook commit B is a launcher artifact and is not used as the training checkout.
2. Authorization is read from the clean clone and checked against the full approved SHA before launch. The notebook passes that same path, hash and `--expected-checkout` to the A2 launcher. This addresses source-QA C2; launcher and trainer must still recheck it live.
3. The notebook requires `NVIDIA L4`, state suffix `M1_D1_Colab/runs/d1_a2_seed_20261018_r1`, CUDA device `0`, and `MODE` in `{fresh,resume}`. Fresh adds `--stop-after-epoch 1`; resume does not. It refuses an existing state directory for fresh and requires a recovery pointer for resume. It also refuses reusing an existing local clone, forcing a new runtime for the second leg.
4. The notebook leaves the launcher defaults frozen by the A2 source (seed 20261018, 100 epochs, imgsz 1280, batch 4, workers 4, fraction 1.0, patience 0 and tag `a2_r1`). It passes the Owner-approved `--download-approved-weight` flag; the inherited launcher verifies the approved `yolo11s.pt` SHA before training. No D-05 value or train-list rule is changed.
5. The training tarball pin is `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`, 766,226,800 bytes, matching `docs/review/d1_colab_backend_r1_successor_bundle_record.md` and the A3 notebook precedent. The sidecar pin is `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2`, 1,499,866 bytes. All eight fallback part names, sizes and SHA values match the A3 notebook; their sizes sum to the tarball size. The `8e6ffe77…` value in contract §4 is the extracted bundle manifest for the future **validation evaluator**, not the tarball SHA to pass as `--bundle` for training. The inherited launcher checks bundle content against the governed train/val export.
6. The post-run cell checks fresh `PAUSED_FOR_RESUME` and `epoch-0001`, or resumed `SUCCEEDED` and `epoch-0100`, together with `git_dirty_files=0`, commit, A2 list/roster and authorization hashes, `sealed_test_accessed=false`, a `4687` training-log marker, and one result archive plus manifest on success. Source-QA C3 still requires independent inspection of the live Drive records, actual `train_args`, checkpoint manifest, log and seal before resume.

## Checks and limits

- JSON notebook format 4.5 parsed; seven cells, zero saved outputs, and every code cell parsed as Python.
- `cd detector && uv run ruff check colab/d1_train_a2_r1.ipynb`: PASS.
- `cd detector && uv run pytest -q tests/test_a2_repeat_list_r1.py tests/test_resumable_train_a2_r1.py tests/test_run_d1_colab_a2_r1.py`: exit 0, 80 tests passed.
- `cd detector && uv lock --check`: PASS (66 packages). The Owner-approved Ruff gate for six A2 Python files passed in the coordinating session. The known notebook-wide Ruff failures in older notebooks were not treated as changes to this QA scope.
- Static review cannot establish Colab access, GPU allocation, Drive bundle presence, real duplicate handling, epoch-1 artifacts, or successful 100-epoch packaging. Those remain unknown until live smoke and result QA.

This verdict permits commit B of the notebook plus this record, followed by the Owner-authorized non-force push of `yolo11n-dual-track-r1`. It does not itself authorize skipping live-smoke QA, opening sealed test, or claiming an A2 metric improvement.
