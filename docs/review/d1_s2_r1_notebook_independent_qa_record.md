# D1-S2-R1 notebook independent QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: separate Codex QA agent
`/root/s2_source_qa`; this agent did not author the notebook, source package, or
operate Colab. Boundary: notebook source/static controls only. No GPU run, Drive
write, Git push, R3 scoring, or sealed-test access occurred. `sealed_test_accessed=false`.

Verdict: PASS — the notebook is ready for the separately authorized push and live L4 smoke; this verdict does not establish a smoke or training result.

## Identity and source pin

- Notebook: `detector/colab/d1_train_s2_r1.ipynb`, SHA-256
  `9648aa569d8403db33c450f19ed4828c1cd92ed6eea9a5d7721828d52a46900a`.
- `CODE_COMMIT` is the full commit A
  `fc729d07664c70a8784ff735b72d7283e5261b6a`. Local Git history shows
  that commit contains the S2 source, tests, frozen contract, Owner record and
  independent source QA. The committed Owner record hashes to
  `4f394487f7c8d51c31c268414bc16aabc1baa57a41822563459489d0940d2f0c`,
  matching the notebook constant. Commit A was not asserted to be on GitHub;
  availability from Colab depends on the separately authorized push.
- Pilot `run_contract.json` SHA-256 pin is
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`.
  The notebook's post-run assertions give the pilot's exact 16 train-arg keys,
  changing only seed to 20261019 and allowing the S2 run name. The `data`
  value remains the pilot export YAML, not an A2 list. Model/export hashes are
  checked against the frozen pilot values.

## Static execution controls

1. Cell 4 requires `NVIDIA L4`, refuses an existing
   `/content/Traffic_Sign_Detector`, clones the repository, detaches to
   `CODE_COMMIT`, checks observed `HEAD`, and requires empty
   `git status --porcelain --untracked-files=all`. No cell copies or writes
   source into the clone after checkout. The Owner record is read from that
   clean clone and checked by its full SHA-256 before launch.
2. Cells 2–3 pin the same train/val-only Drive archive and sidecar as the
   successful A2 notebook: archive 766,226,800 bytes / SHA-256
   `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`;
   sidecar 1,499,866 bytes / SHA-256
   `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2`.
   The eight fallback part names, sizes and hashes equal the A2 pins, and the
   sizes sum to the archive size. Each part and the reassembled archive are
   hashed before the launcher receives the bundle path. The inherited launcher
   must still verify the archive's internal manifest live.
3. The unique Drive state suffix is
   `M1_D1_Colab/runs/d1_s2_seed_20261019_r1`. `MODE` is limited to
   `fresh`/`resume`. Fresh refuses an existing state and passes
   `--stop-after-epoch 1`; resume requires a recovery pointer and passes no
   stop boundary. A second execution needs a new runtime because the notebook
   refuses an existing local clone, and the inherited R2 runner separately
   rejects a repeated runtime digest. The exact checkout path is reused on
   resume so absolute dataset paths stay valid.
4. The command invokes only `run_d1_colab_s2_r1.py`, passes the same Owner
   record/hash and pinned checkout, CUDA device 0, and requests the inherited
   approved pretrained weight hash check. The notebook contains no A2 list,
   seed 20261020 command, test-export flag, evaluation command or R3 scoring.
5. The final cell checks S2 experiment/package, false sealed-test flags,
   clean Git commit, L4, Owner/pilot/model/export pins, the exact train-arg
   dictionary, and the log substring `Using 3712 train, 376 val images`.
   Fresh requires `PAUSED_FOR_RESUME` with `epoch-0001`; resume requires
   `SUCCEEDED`, completed epoch 100 and `epoch-0100`, plus one result archive
   and its manifest. The A2 live smoke record documents the analogous
   `Using 4687 train, 376 val images for fraction=1.0 at imgsz=1280` log
   format; the S2 `3712` assertion remains a live check.

## Local checks and limits

- Notebook JSON parses as format 4.5, seven cells, no saved outputs; all code
  cells parse as Python. `uv run ruff check colab/d1_train_s2_r1.ipynb` PASS.
- `uv run pytest -q tests/test_s2_r1_train.py tests/test_s2_r1_colab.py`:
  23 passed. `uv lock --check`: PASS, 66 packages. `graft check .`: OK.
- This static review cannot establish that the archive and sidecar are present
  on Drive, commit A is reachable from Colab, an L4 is allocated, the epoch-1
  artifact is valid, or a distinct runtime actually resumes. Independent live
  smoke QA must inspect the Drive checkpoint, execution log, run contract and
  runtime identity before the 100-epoch resume. Git push remains a separate
  Owner decision.
