# Handover check — Codex → Claude, 2026-10-22

Status: `STEP_0_HANDOVER_CHECK_COMPLETE_NOTHING_COMMITTED`
Checked at: 2026-10-22 17:28–18:20 (`Asia/Ho_Chi_Minh`) by a Claude Code session.

This note records the state of the checkout when the unfinished Codex work was handed over. It
changes no package, record or pinned file.

## Repository state

- Branch `DEV/Rroject_Pineline`; HEAD `85a8025` = `origin/DEV/Rroject_Pineline` (0 ahead, 0 behind).
- The last Codex write was at 17:18:35. There were no writes between then and the start of the
  check at 17:28.
- **Not committed:** 9 modified tracked files (+460 / −79 lines) and 150 untracked files
  (147 MB). These include `results/experiments/…pilot_100e_seed_20261018_r2/weights/best.pt` and
  `last.pt`, about 76 MB each, which must stay out of the public repository per the D-01 checkpoint
  boundary (`docs/review/git_checkpoint_owner_decision_record.md`).

## Checks run

| Check | Result |
| --- | --- |
| `graft check .` | OK, the graph is in sync |
| `uv run ruff check src tests` | All checks passed |
| `uv lock --check` (root and `detector/`) | OK |
| `run_parallel_checks.py tests --jobs 6` (root) | 126 serial + 1,765 passed, 2 skipped, 7 xfailed, 0 failed |
| `uv run pytest -q` in `detector/` | 199 passed, 0 failed |
| `uv run ruff check .` in `detector/` | 19 errors, all in old notebooks (`colab/d1_train.ipynb`, `d1_train_pilot_r1…r4.ipynb`), none in new `.py` files |
| `run_parallel_checks.py verifiers --jobs 6` | **61/61 verifiers PASS**, including WP38, WP38-R1, M1-WP38-R1 R1–R4 and Colab bundle R1–R2 |
| Hash pins in the 30 new QA records | Every file reviewed as PASS still matches its pin; the corrected-val R10 result is `b33e2470…` |

Hash drift appears only for living documents that QA records pinned at review time:
`src/cpv301_autodrive/project_status.py`, `views.py`, `docs/product_roadmap.md` and
`scripts/run_parallel_checks.py`. No verifier depends on those pins; all 61 pass.

## Cleanup done with the user's approval (group A)

37 regenerable items (13 MB) were moved to the macOS Trash, not deleted, at
`~/.Trash/Traffic_Sign_Detector_cleanup_A_20261022_175655`:

- the leftover synthetic QA fixtures `tmp/r6_*`, `r7_*` and `r8_*` (20 directories);
- `__pycache__`, `.pytest_cache` and `.ruff_cache` outside the virtual environments;
- five `.DS_Store` files.

`data/`, both `.venv` directories, the Colab tarballs and the screenshots in `tmp/` were not
touched; they are left for the user's group-B decision. No tracked file was affected.

Group D added the navigation file `docs/review_index.md`. `.gitignore` needed no change for
caches, `tmp/` or `.DS_Store`.

## Open decisions for the user

1. Whether to add `results/experiments/**/weights/` to `.gitignore`. This is recommended because
   the repository is public.
2. Whether to commit locally in the five proposed groups:
   - WP38;
   - L4 capacity;
   - corrected-val R1–R10, its result and the error analysis;
   - web UI;
   - docs.

   A new push needs separate authorization.
3. Where D1-EA-R1 inference runs: local MPS (same device as R10) or Colab L4.
4. Group B (local data and Colab artefacts):
   - `tmp/m1_colab_train_val*.tar.gz` and its parts, about 2.2 GB;
   - `data/raw/*.zip`;
   - the superseded `data/processed/*` builds, which their verifiers may need.

## Boundary

No commit, push, upload, training, inference or sealed-test access. Gate 0 status and D-05 are as
recorded in `PROJECT_MEMORY.md`.

## Addendum: group B inventory (read-only, 2026-10-22)

The paths below were searched in `scripts/`, `detector/`, `src/` and `tests/` Python code. A path
with code references is read by a builder, verifier or test.

| Item | Size | Code refs | Recommendation |
| --- | ---: | ---: | --- |
| `tmp/m1_colab_train_val.tar.gz` (+ manifest) | 731 MB | 2 (bundle builders) | **Can delete.** It is superseded by the backend R1 bundle, the upload is recorded with QA PASS, and the builder can regenerate it. |
| `tmp/m1_colab_train_val_backend_r1.tar.gz` + `.part-00…07` | 731 MB + 731 MB | 2 | **Can delete the parts** once you confirm the Drive copy. The parts duplicate the tarball; keep one of the two until the next Colab upload. |
| `tmp/pdfs/`, `tmp/wp6_candidate/`, screenshots in `tmp/` | 7 MB | 0–1 | Can delete; the QCVN PDF is in `references/`. |
| `data/raw/archive.zip` | 612 MB | 2 (audit) | **Keep.** It is the hashed DATASET01 source archive, and `audit_dataset01.py` checks it. |
| `data/raw/traffic-signs-data.zip`, `data/processed/{train,valid,test}.p` | 270 MB | 0 / 3 | Keep while the E0 GTSRB baseline is used (the `.p` files are read by E0 evaluation). |
| `data/processed/*` (m1_yolo, wp38, wp35, crops, cascade) | 380 MB | 1–12 each | **Keep.** Their verifiers rebuild and compare them (for example `verify_materialised`). |

Estimated safe saving: about 1.5–2.2 GB, all inside `tmp/` and all git-ignored. Nothing in this
table has been deleted.
