# App release R1 provenance and gates

Prepared locally on 2026-11-01 from `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, research commit `d4de74d6e2fa0eebc9205639eee02b7fbec3acf6` (current branch `yolo11n-dual-track-r1`). The Desktop checkout contained modified tracked files and untracked current app modules. This release candidate copied the live app snapshot without changing or deleting that checkout.

The candidate uses stable module names for the current D1/CenterCam, dataset authority and Review 2 video code. Historical numbered implementations, notebooks, training scripts, model outputs and complete append-only QA records remain in the research checkout. This rename is a source refactor, **not** a new model result or independent QA verdict.

The release package includes 54-class map, DT validation summary and the minimum DATASET01 split/graph evidence needed by the app. Its private inputs are intentionally absent: checkpoints, raw/processed images, PHENIKAA video, E0 `.h5`, and sealed test. A clean clone must start all pages and explain absent inputs; inference requires the owner's pinned private artifacts.

## Local verification

- `uv sync --locked --no-dev`: PASS (103 runtime packages installed).
- `uv lock --check`: PASS.
- `uv run ruff check src tests`: PASS.
- `uv run pytest -q`: 2 passed.
- Streamlit AppTest: 8/8 pages, no unhandled exceptions; expected missing-weight message in D1/S1/E0.
- `cpv301 web --port 8629 --headless`: health endpoint returned `ok`.
- Class map: 54 classes; DATASET01 authority reports `sealed_test_accessed=false`; graph builds 3,216 nodes from public evidence.
- Isolated local clone of commit `6ef4e66` at `/tmp/cpv301-release-clone-r1`: `uv sync --locked --no-dev` PASS; Streamlit AppTest 8/8 pages without exception; class map 54 and seal metadata false; `cpv301 web --port 8630 --headless` returned `ok` at `/_stcore/health`. No private model/video files were copied into that clone.
- Separate bounded inference replay against hash-checked private checkpoints in the original checkout and the local validation image `1231.jpg`: D1 returned four boxes at 0.20; S1 returned two boxes at 0.20. This checks wiring after renaming and is not an accuracy estimate or a sealed-test run.

The Owner explicitly authorized pushing this branch and making it the GitHub default. The branch and default were read back on GitHub, and a fresh `--depth 1 --single-branch` clone from the public URL checked out commit `2027e1c`: `uv sync --locked --no-dev` PASS, all eight pages without exceptions, 54-class map, seal metadata false, and `python main.py --port 8631 --headless` returned `ok` at `/_stcore/health`. The next documentation commit supersedes that exact commit without changing runtime code.

Independent QA of the renamed app/source and exact asset set remains pending. This file does not make a classroom video or safety approval claim.

On 2026-11-01, the Owner requested removal of the automation prefix from branch names. GitHub branches are now `app-release-r1` (default), `vgg16-54-r1`, and `yolo11n-dual-track-r1`. Each rename retained its commit SHA; the existing `DEV/Rroject_Pineline` branch was not changed. Local checkouts and upstream references were updated. Historical QA records in the research checkout keep their original branch names as a record of what was reviewed at that time.
