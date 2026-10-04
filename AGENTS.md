# Traffic_Sign_Detector agent contract

This repository uses repo-local, durable project memory. Keep instructions short, keep claims
evidence-bounded, and preserve the distinction between an implemented module and a roadmap item.

## Start every task

1. Read `PROJECT_MEMORY.md`.
2. Read only the canonical document(s) routed from that memory file for the task at hand.
3. Use Graft before reading or changing source code:
   - `graft check .` for freshness.
   - `graft map .` for first orientation or architecture work.
   - `graft ask "<question>" --source .` to locate and understand a flow.
   - `graft grep`, `graft skeleton`, or `graft callers` when exhaustive occurrences, an API
     surface, or dependency/blast-radius information is needed.
4. If `graft check .` reports `STALE`, use freshness-aware Graft queries for the current task and
   run `graft build . && graft check .` before handing off source changes.

Do not reconstruct source relationships by broadly scanning the repository when Graft can answer
the question. Raw search remains appropriate for Markdown, configuration, generated artifacts, and
other files Graft does not index.

## Project-management rules

- Treat the current Desktop checkout as authoritative. Paths or outcomes from the earlier iCloud
  checkout are historical until reverified here.
- Classify every claim as one of: verified current behavior, verified artifact/result, proposal,
  or unknown. Never silently promote a proposal to implemented status.
- `models/VGG16_model.h5` is a retained Drive filename. The observed artifact is a small
  VGG-inspired sequential CNN, not canonical VGG16.
- The present classifier accepts cropped 32x32 traffic-sign images from GTSRB. It is not a
  full-scene detector and has no validated Vietnamese deployment claim.
- `confidence_threshold=0.50` is a demo threshold, not a calibrated UNKNOWN/OOD guarantee.
- Behavior output is simulation only. Do not connect the current predictions to a real vehicle or
  describe them as safety validated.
- Preserve downloaded data, model artifacts, provenance, evaluation outputs, and unrelated user
  changes. Upload, deploy, submit, push, or publish only with explicit user authorization.

## Close every material task

1. Run validation proportional to the change. The default code gate is:
   `uv run ruff check src tests && uv run pytest -q && uv lock --check`.
2. For source changes, rebuild/check Graft and inspect the task-specific blast radius when relevant.
3. Update `PROJECT_MEMORY.md` only for durable state, decisions, risks, or verified commands.
4. Update the canonical detailed document instead of duplicating it in memory:
   - product status/backlog: `docs/product_roadmap.md`
   - model evidence and go/no-go: `docs/initial_model_assessment.md`
   - artifact/model origin: `docs/model_provenance.md`
   - imported-source inventory: `docs/drive_inventory.md`
5. Read back the changed files and report what was actually verified.

