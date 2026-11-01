# App release R1 provenance and gates

Prepared locally on 2026-11-01 from `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, research branch `codex/yolo11n-dual-track-r1`, HEAD `d4de74d6e2fa0eebc9205639eee02b7fbec3acf6`. The Desktop checkout contained modified tracked files and untracked current app modules. This release candidate copied the live app snapshot without changing or deleting that checkout.

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

Still required before public GitHub release: isolated clone replay and independent QA of the renamed app/source and the exact asset set. The owner must authorize push/publication under the repository agent contract. This file does not make a classroom video or safety approval claim.
