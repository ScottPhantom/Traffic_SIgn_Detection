# PM handoff — Traffic_Sign_Detector

Ngày bàn giao: 2026-10-03 (Asia/Ho_Chi_Minh)  
PM cũ: Codex thread `01a0fce1-2474-7cf2-9c0e-6debbb6a1e4d`  
PM mới: Project Management and Structure  
Canonical checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`

Tài liệu này chốt thông tin PM cũ đã bàn giao và được PM mới đối chiếu với checkout Desktop.
Path iCloud cũ không còn tồn tại; mọi path hoặc kết quả từ checkout đó chỉ là lịch sử cho tới
khi được xác minh lại ở Desktop.

## 1. Mục tiêu và ranh giới

Mục tiêu dài hạn là webapp mô phỏng chuỗi camera/frame -> nhận diện biển báo -> trạng thái và
phản ứng xe mô phỏng. Hệ thống hiện đã có classifier ảnh crop, API, CLI, Streamlit MVP, behavior
rules mô phỏng, đánh giá baseline GTSRB và môi trường UV/Jupyter.

Chưa có và không được tuyên bố đã có:

- detector biển báo trong camera frame toàn cảnh;
- kiểm chứng trên giao thông Việt Nam;
- UNKNOWN/OOD đã calibration;
- video tracking hoặc temporal voting;
- lane detection, PID hay CARLA runtime;
- controller an toàn hoặc tích hợp xe thật;
- canonical `keras.applications.VGG16`.

## 2. Kiến trúc runtime hiện tại

```text
cropped image / webcam snapshot
  -> preprocess_image
     RGB -> resize bilinear 32x32 -> float32 / 255 -> add batch
  -> ModelService.load
     lazy-load HDF5 with Keras, compile=False
  -> ModelService.predict
     Softmax argmax -> Prediction(class_id, label, confidence, accepted)
  -> plan_behavior
     Prediction -> simulated VehicleCommand
  -> FastAPI JSON or Streamlit result/telemetry/history
```

Module contract:

- `config.py`: project root, model path, threshold, `.env`/`CPV301_*`; resolve relative paths
  from project root and validate threshold in `[0, 1]`.
- `labels.py`: 43 GTSRB labels.
- `inference.py`: preprocessing, `Prediction`, lazy `ModelService`.
- `api.py`: `GET /health`, `POST /v1/predict`, cached service. Health checks path/artifact and
  lazy-load state; it is not an inference proof.
- `behavior.py`: presentation-only behavior rules. Rejected prediction -> review/max 10 km/h;
  speed limit -> `min(cruise, limit)`; stop/no-entry/no-vehicles -> 0; yield -> max 10; turn ->
  max 20; caution -> max 15; otherwise continue.
- `web_app.py`: cached service; model is invoked at raw threshold 0 and the UI threshold slider is
  applied afterward; supports multiple uploads/webcam snapshot, history, telemetry and road card.
- `evaluation.py`: loads trusted/checksummed local pickle only, validates tensor/labels, runs the
  classifier and writes summary, per-class metrics, confusion matrix and high-confidence errors.
- `cli.py`: `info`, `predict`, `serve`, `web`, `evaluate`.

Target pipeline remains:

```text
camera/video -> detector ROI -> classifier -> temporal voting/tracking
             -> behavior planner -> lane/vehicle simulator -> Streamlit
```

## 3. Model, data and evidence

Model artifact:

- path: `models/VGG16_model.h5`;
- Drive ID: `18lQG_A4TkDgI27Qh9OLlTT-uVL8xrIlo`;
- size: 17,593,732 bytes;
- SHA-256: `745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565`;
- input/output: `(None, 32, 32, 3)` -> `(None, 43)`;
- observed architecture: VGG-inspired Sequential CNN, not canonical VGG16.

Processed GTSRB:

| Split | Shape | SHA-256 |
| --- | --- | --- |
| train | `(34799, 32, 32, 3)` uint8 | `5c319e00df7f45a18761e65dfd47341779c310798a71ea3f371659cc4a63da44` |
| valid | `(4410, 32, 32, 3)` uint8 | `7d92b991f95cf3bfcc6e35b88bad506b89e562992c1eb6c1034462a9604b6948` |
| test | `(12630, 32, 32, 3)` uint8 | `60b6450ffdb227042eb32f28d15fe77f98ad24dd550cc85eb445b8c0e502e470` |

Baseline `results/evaluation/gtsrb_test_baseline/`:

- accuracy `0.868171`;
- macro-F1 `0.792133`;
- weighted-F1 `0.870490`;
- balanced accuracy `0.794929`;
- top-label ECE, 10 bins: `0.040488`;
- mean confidence `0.908588`;
- 1,665 errors; 324 errors at confidence >= `0.90`;
- at demo threshold `0.50`: coverage `0.958116`, accepted accuracy `0.891001`;
- confirmed directional confusion: 117 `Keep right -> Keep left`, 86 `Turn right -> Turn left`.

The transition audit read the stored summary and checked model/test hashes; it did not rerun all
12,630 predictions. `horizontal_flip=True` in the training notebook is a confirmed semantic defect
for directional signs. The current model is therefore frozen as a research baseline and is NO-GO
for Vietnamese deployment or real control.

Candidate Vietnamese dataset outside the product checkout:

`/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/FALL 2026 KỲ 4/CPV301/Data/DATASET01/archive.zip`

- size 793,394,914 bytes;
- SHA-256 begins `052bc980`;
- 52 classes; 3,216 JPG and 3,221 TXT members;
- candidate YOLO/detection data only;
- not yet audited for license, provenance, taxonomy mapping, split integrity, or independent test;
- existing extracted folder is incomplete, so the ZIP is the recovery source if this milestone is
  authorized later.

## 4. Intentionally removed imported documents

`docs/drive_inventory.md` records a planning DOCX, a Slides export and three papers, but they are
not in the current checkout:

- `/Users/nguyentantai/.Trash/CPV301_Project_Planning_Group_01.docx`
- `/Users/nguyentantai/.Trash/Traffic_Sign_Categories.pptx`
- `/Users/nguyentantai/.Trash/papers/`

User clarification on 2026-10-03: these files were intentionally deleted by the user. Their absence
is expected. Do not restore, investigate, or keep this item as a project blocker.

## 5. Durable decisions

- Classifier-first sequencing; do not jump directly to CARLA.
- Streamlit is the current MVP UI; no Gradio implementation exists in this checkout.
- Python 3.12.13, UV, one real root `.venv/`, `uv_build` backend.
- TensorFlow 2.20.0 and NumPy 2.1.3 are pinned by the current environment.
- Ultralytics/PyTorch are optional detector-milestone dependencies, not base dependencies.
- CARLA is deferred until an OS/simulator binary/API version is chosen.
- Model/data/DB binaries remain local and ignored; preserve their provenance and hashes.
- Threshold 0.50 is demonstration behavior only; CPV-006 must calibrate on `valid.p`.
- Do not overwrite the current model; corrected training produces a new, accurately named artifact.

## 6. Milestones

| ID | State | Meaning |
| --- | --- | --- |
| CPV-001 | complete | reproducible UV environment/kernel/test gate |
| CPV-002 | MVP | Streamlit shell |
| CPV-003 | MVP | cropped-image and webcam-snapshot classification |
| CPV-004 | MVP | simulated behavior mapping |
| CPV-005 | complete baseline | closed-set GTSRB evaluation |
| CPV-006 | next | threshold calibration on validation data |
| CPV-007 | planned | video journey and temporal voting |
| CPV-008 | planned | full-scene detector -> crop -> classifier |
| CPV-009 | planned | lane/PID |
| CPV-010 | planned | CARLA integration |
| CPV-011 | planned | export, latency, deployment and hardening |

## 7. Environment and latest verification

Use only the Desktop checkout and the root `.venv/`. Prefer `uv run` rather than activation.
The project kernel is `cpv301-autodrive`, displayed as `Python (CPV301 AutoDrive)`.

Transition verification on 2026-10-03:

- UV resolved 167 packages; `uv lock --check` passed.
- Python 3.12.13, TensorFlow 2.20.0, Keras 3.15.1, Streamlit 1.65.0.
- Ruff passed for `src tests`.
- pytest: 8 passed with one Starlette TestClient/httpx deprecation warning.
- `cpv301 info` found the Desktop model and both notebooks; threshold is 0.5.
- both notebooks select the project kernel.
- Streamlit was observed live on port 8511 during the old-PM audit because another Streamlit
  process occupied 8501; this is transient observed state, not a permanent port decision.
- FastAPI was not launched live during that audit; its unit health test passed.

## 8. Repository-integrity gate

At handoff time:

- branch is `main`;
- repository has zero commits and no configured remote;
- all trackable project files are untracked;
- data/model/DB binaries and Graft graph are ignored;
- there is no recovery history, review baseline or tag yet.

The PM must review the initial tracked-file policy and secrets/large-file boundaries before asking
for an initial commit. Creating a commit, remote or push is a separate user-authorized action.

During this transition, the `.gitignore` typo `.cluade/` was corrected to `/.claude/` to match the
commented local-agent policy. Root `AGENTS.md` remains the tracked cross-agent contract.

## 9. Graft handoff

- binary: `/Users/nguyentantai/.nvm/versions/node/v25.9.0/bin/graft`;
- installed version: 0.13.0; version 0.21.1 was reported available but not installed;
- `.mcp.json` registers `graft mcp`;
- `.claude/skills/graft/SKILL.md` documents the Graft-first workflow;
- `graft/` is an ignored, regenerable local graph;
- transition build/check: 14 Python files, 58 nodes, 155 edges; wiring graph in sync;
- deep meaning layer was not built and is not required for current caller/callee/source routing.

Use `graft map` for orientation, `graft ask --source` for a flow, `graft grep` for exhaustive
occurrences, `graft skeleton` for a file API and `graft callers` for dependency/blast radius.
Finish source work with `graft build . && graft check .`.

## 10. PM priorities after transition

1. Review the initial tracked-file policy and establish a first commit/remote only when requested.
2. Implement CPV-006 calibration on `valid.p`; never optimize the rejection threshold on test.
3. Extract reproducible training, remove horizontal flip, fix generator steps, seed/config/name the
   corrected model, and set per-class acceptance gates.
4. Audit the Vietnamese candidate dataset before importing or making coverage claims.
5. Add detector, temporal logic, lane/PID and CARLA only after their preceding evidence gates pass.
