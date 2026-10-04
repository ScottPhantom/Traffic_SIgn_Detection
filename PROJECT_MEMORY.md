# Project Memory — CPV301 AutoDrive

Last updated: 2026-10-03 (Asia/Ho_Chi_Minh)  
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`  
Role: PM — Project Management and Structure

This file is the compact, durable entry point for future Codex sessions. It records current facts,
decisions, risks, and routing. Detailed evidence stays in the canonical documents linked below so
this file does not become a second, drifting specification.

## Authority and evidence order

When sources disagree, use this order:

1. Current checkout code, tests, artifact readback, and task-specific Graft query.
2. Canonical project documents listed in this file.
3. Current PM handoff notes.
4. Older thread summaries or paths from the former iCloud checkout.

Always distinguish current verification from historical evidence. A green unit test proves only
the behavior it exercises; a local MVP, notebook output, or high confidence score does not prove
Vietnamese-domain accuracy, open-set recognition, full-scene detection, or safe control.

## Mission and present boundary

The long-term product is a local simulation in which a camera pipeline recognizes traffic signs,
maintains vehicle state, and visualizes the simulated response. The intended end-to-end pipeline is:

```text
camera/frame
  -> detector finds traffic-sign ROI
  -> classifier labels ROI
  -> temporal voting/tracking
  -> behavior planner
  -> lane/vehicle simulator
  -> Streamlit dashboard
```

Only the cropped-image classifier and a simulated behavior/UI shell are implemented today.
Detector, temporal voting/tracking, lane/PID, and CARLA integration remain roadmap work.

## Current implementation map

| Area | Current module/entry point | Verified status |
| --- | --- | --- |
| Configuration | `src/cpv301_autodrive/config.py` | Settings include model path and demo confidence threshold. |
| Labels | `src/cpv301_autodrive/labels.py` | GTSRB 43-class label mapping. |
| Inference | `src/cpv301_autodrive/inference.py` | RGB 32x32 preprocessing, model loading, Softmax prediction, threshold-based `accepted`. |
| API | `src/cpv301_autodrive/api.py` | Health endpoint and cropped-image prediction path. |
| Launcher | `main.py` | Root one-command launcher; delegates to `scripts/run-web.sh` so UV sync and the existing Streamlit CLI remain the single startup flow. |
| CLI | `src/cpv301_autodrive/cli.py` | Info, serve, predict, evaluate, and web entry points. |
| Evaluation | `src/cpv301_autodrive/evaluation.py` | GTSRB split loading, classifier metrics/artifacts, and calibration-error calculation. |
| Behavior | `src/cpv301_autodrive/behavior.py` | Maps a `Prediction` to a simulated `VehicleCommand`; it is not real control. |
| Web UI | `src/cpv301_autodrive/web_app.py` | Streamlit MVP for uploaded cropped images/webcam snapshots, result display, history, and simulated road state. |
| Tests | `tests/` | Inference, API, evaluation, behavior, and initial web rendering coverage. |

For exact callers, callees, spans, and function interactions, query Graft rather than relying on
this prose map.

## Verified current state

- Environment: one standard project `.venv/`, managed from `pyproject.toml` and `uv.lock`.
- Python constraint: `>=3.12,<3.13`; local model loading uses TensorFlow 2.20.
- Model artifact: `models/VGG16_model.h5`; RGB input `(None, 32, 32, 3)`, 43-way Softmax output.
- Architecture evidence: VGG-inspired sequential CNN, not `keras.applications.VGG16`.
- Full GTSRB test evaluation: 12,630 images, accuracy `0.8682`, macro-F1 `0.7921`, weighted-F1
  `0.8705`, balanced accuracy `0.7949`.
- Error evidence: 1,665 wrong predictions, including 324 errors at confidence at least `0.90`.
- Training defect: `horizontal_flip=True` can invert directional signs while preserving the label.
- Domain decision: NO-GO for Vietnamese traffic deployment and real vehicle control.
- Current demo threshold: `0.50`; validation calibration and UNKNOWN/OOD evaluation are unfinished.
- Current baseline artifacts and provenance must be preserved; a corrected retrain must use a new
  artifact name rather than overwriting the baseline.
- Git integrity is not established yet: branch `main` has zero commits, no remote, and all
  trackable project files are untracked. Do not claim version/recovery history exists.
- The planning DOCX, Slides PPTX and three papers are absent because the user intentionally deleted
  them. Their absence is expected; do not restore, investigate, or treat it as a blocker.
- Graft tier-0 wiring was rebuilt and checked on 2026-10-03: 16 Python files, 65 nodes, 167 edges,
  graph in sync. The optional deep meaning layer is not built.

## Product milestone status

- Completed/current MVP: reproducible UV environment, Streamlit shell, cropped-image/webcam-snapshot
  classification, simulated behavior mapping, and closed-set GTSRB classifier evaluation.
- Next: threshold calibration on `valid.p` with coverage, accepted-set accuracy, known rejection,
  and unknown false acceptance reported explicitly.
- Then: Vietnamese taxonomy/dataset with provenance; corrected reproducible training pipeline;
  independent classifier/OOD evaluation.
- Later: video journey and temporal voting; full-scene detector; lane/PID; CARLA; product hardening.

The detailed backlog and acceptance criteria live in `docs/product_roadmap.md`.

## Durable decisions

1. **Classifier-first sequencing.** Validate and repair the classifier before adding detector,
   temporal logic, lane control, or CARLA.
2. **Evidence-bounded naming.** Keep the downloaded filename for provenance, but describe the
   architecture as VGG-inspired CNN.
3. **No arbitrary UNKNOWN threshold.** Select rejection behavior from validation evidence and
   evaluate supported, unsupported, non-sign, and difficult-image groups separately.
4. **Separation of concerns.** Detector finds ROIs; classifier labels cropped ROIs; temporal logic
   stabilizes events; planner produces simulation intent; simulator/control executes it.
5. **Optional heavy dependencies.** Ultralytics/PyTorch enter only at the detector milestone;
   CARLA is added only after the simulator version/platform is fixed.
6. **One environment.** Use the root `.venv/`; do not recreate the former `venv` plus symlink
   arrangement that existed for the iCloud checkout.
7. **Graft-first source work.** Use Graft for orientation, symbol/API lookup, callers/callees, and
   blast radius; end source tasks with a fresh graph check.

## Current risks and technical debt

- No Vietnamese-domain dataset or independent Vietnamese evaluation exists in the project.
- A 52-class Vietnamese detection-data candidate exists outside the product checkout at
  `.../CPV301/Data/DATASET01/archive.zip`, but its license, provenance, taxonomy, extraction,
  split integrity, and evaluation use are unapproved. Do not import or make claims from it silently.
- No explicit unknown/non-sign benchmark or calibrated abstention policy exists.
- Full-scene detection, video tracking, and temporal voting are absent.
- Behavior rules can make unsafe-looking decisions if treated as control; they are UI simulation.
- The training procedure still needs extraction from the notebook and correction of augmentation
  and generator-step issues before retraining.
- Class imbalance and low recall in safety-relevant classes make aggregate accuracy insufficient.
- FastAPI test execution currently emits a Starlette deprecation warning for the `httpx`
  TestClient compatibility layer; tests still pass.
- Test coverage remains narrow: no model/API multipart end-to-end, corrupt-artifact, CLI,
  full-evaluation regression, browser E2E, or latency gate.

## Immediate PM gate

Before feature work expands:

1. Review the initial tracked-file policy and large-file/secret boundaries.
2. Create an initial commit, remote, or push only when the user explicitly requests it.
3. Then execute CPV-006 calibration and the corrected reproducible-training work.

## Canonical documents

- `README.md`: setup, run commands, project overview, and user-facing boundaries.
- `docs/product_roadmap.md`: milestones, status, acceptance criteria, and next sprint.
- `docs/initial_model_assessment.md`: quantitative evaluation, defects, and go/no-go decision.
- `docs/model_provenance.md`: artifact hash, architecture, training log, and evidence boundary.
- `docs/drive_inventory.md`: Drive IDs, hashes, imported files, and exclusions.
- `docs/pm_handoff_2026-10-03.md`: full old-PM handoff, repository-integrity findings, and
  Graft/environment details captured during the transition.
- `results/evaluation/gtsrb_test_baseline/`: reproducible baseline evaluation outputs.

## Known-good commands and latest readback

Run from the Desktop checkout:

```bash
python main.py
./scripts/bootstrap.sh
uv run cpv301 info
uv run cpv301 predict tmp/00000.png
uv run cpv301 evaluate
./scripts/run-web.sh
uv run ruff check src tests
uv run pytest -q
uv lock --check
```

Readback on 2026-10-03 in the Desktop checkout:

- Ruff: pass.
- pytest: `10 passed`; one Starlette deprecation warning.
- `uv lock --check`: pass; 167 packages resolved.
- `cpv301 info`: model exists at the Desktop checkout; threshold `0.5`; both project notebooks found.
- `python main.py --headless --port 8599`: Streamlit started and `/_stcore/health` returned `ok`;
  the temporary verification server was then stopped.

## Memory maintenance protocol

Update this file only when a fact will matter in a future session: a changed architecture boundary,
accepted decision, milestone state, verified command, blocker, or superseded risk. Do not append a
chat diary. Replace stale statements and point to the detailed evidence file.

At the end of material work:

1. Update the relevant canonical document.
2. Update this compact memory if the durable state changed.
3. Include the date and exact command/evidence for new verification claims.
4. Run the appropriate tests and Graft freshness check.
5. Leave unresolved proposals explicitly marked as proposed.
