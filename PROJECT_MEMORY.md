# CPV301 app release memory

Status: GitHub default branch `app-release-r1`, 2026-11-01. This tree is a clean runtime snapshot derived from the Desktop checkout. The full experiment and QA archive remains on research branch `yolo11n-dual-track-r1`. This release has **not** received independent release QA; source/runtime smoke and clean GitHub clone replay passed.

## Runtime scope

`README.md` gives the install/run commands, active module map, checkpoint locations and hashes. `src/cpv301_autodrive/web_app.py` is the Streamlit entry; `app_pages/` contains eight pages. D1, S1, Dynamic Threshold, CenterCam, E0 simulation and Review 2 video prototype are present. Missing private weights or source clips produce user-facing states. Do not infer model acceptance from successful app startup.

`docs/review/generated/` contains only the public, runtime-read evidence. `docs/review/*.md` here contains the two QA records pinned by the DATASET01 authority view. The research branch retains the complete append-only audit trail; no historical record was deleted there.

## Gates

- D-01: no checkpoint in public Git.
- D-05: model and video behavior remain demo/simulation only.
- Sealed test: no access in release preparation. The graph authority contract records `sealed_test_accessed=false`; do not treat that as new test evaluation.
- Release QA: pending. A local test passing does not confer independent QA PASS.

## Change workflow

Use Graft for source relationships and `rg` for docs/config/generated artifacts; keep changes scoped. Run `uv lock --check`, `uv run ruff check src tests`, `uv run pytest -q`, then start the app from an isolated clone. Read back the exact files and status before claiming completion.
