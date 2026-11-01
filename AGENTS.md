# CPV301 app release contract

Read `PROJECT_MEMORY.md` and `README.md` before changing the app. The release branch contains the current Streamlit runtime and only the public evidence that it reads. The research branch retains notebook, experiment, and append-only QA history.

- Keep one active implementation for each runtime feature. Put new code behind the existing module name rather than adding `_rN` successors to `src/`.
- Keep raw data, clips, trained checkpoints, secrets, and sealed test outside Git. Never silently replace a pinned checkpoint or class map.
- Report verified behavior separately from proposed work. Predictions and simulated vehicle behavior are not safety validated.
- Before handoff, run `uv lock --check`, `uv run ruff check src tests`, and `uv run pytest -q`; inspect all eight Streamlit pages without private weights.
- Do not push, publish, upload, or deploy without the owner's authorization.
