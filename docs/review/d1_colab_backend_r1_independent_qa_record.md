# D1 Colab backend R1 independent QA record

Status: `QA_PASS_D1_COLAB_BACKEND_R1`

Reviewer: `Codex independent QA session (did not author the backend remediation)`

Reviewed at: `2026-10-20T10:41:03+07:00`

Boundary: `LOCAL_SOURCE_AND_CONTROL_QA_ONLY_NO_COLAB_RERUN_NO_TRAINING_NO_UPLOAD_NO_DOWNLOAD_NO_SEALED_TEST_ACCESS_NO_COMMIT_NO_PUSH`

Reviewed checkpoint: `30b2d65408c9e414fb8a3708158cb4492da8a0bf` plus the current uncommitted backend R1 worktree

## Verdict

- **PASS — 0 Critical, 0 High, 0 Medium, 0 Low.**
- The primary and cascade Colab runners overwrite an inherited
  `module://matplotlib_inline.backend_inline` value with `MPLBACKEND=Agg` and retain all three
  telemetry-disable controls.
- The primary runner passes that environment to both `m1.cli check` and `m1.cli train`. The
  cascade outer workflow passes it to the `_train` subprocess; the internal Ultralytics execution
  inherits that exact subprocess environment.
- All three cascade `load_pinned_module` call sites that load the primary runner use the single
  `M1_RUNNER_SHA256` constant. Its value equals the exact repaired primary-runner bytes.
- This PASS approves only the local remediation and controls. It does not prove a successor bundle,
  Colab rerun, epoch, checkpoint, result package, validation metric or accepted model exists.

## Incident-boundary reconciliation

The canonical incident record preserves the observed T4 smoke as
`OBSERVED_FAILED_BEFORE_FIRST_EPOCH`. It records the completed bundle, split/export, lock,
pretrained-weight and `m1.cli check` steps, while `training_completed` is absent. The recorded
terminal error is the rejected inline Matplotlib backend, not CUDA OOM, corrupt data, a split/hash
failure or a training result. It records `sealed_test_accessed=false` and requires preservation of
`runs/smoke_seed_20261018` without deletion or reuse.

The operator guide likewise requires a new run label and a successor QA-approved runner/bundle.
Both runners reject a non-empty state directory. The exact repository sealed-test access log was
absent before and after this review.

## Source and bypass audit

### Primary runner

- `colab_subprocess_environment()` starts from `os.environ.copy()` and then overwrites
  `WANDB_DISABLED=true`, `DO_NOT_TRACK=1`, `ULTRALYTICS_HUB=false` and `MPLBACKEND=Agg`; an inherited
  inline backend therefore cannot win.
- One constructed environment is supplied explicitly to the governed `m1.cli check` subprocess and
  again to the `m1.cli train` subprocess.
- Bundle extraction, dataset export and `uv sync --frozen` do not import or invoke the detector
  check/train path and do not provide a backend bypass.

### Cascade runner

- The cascade helper applies the same four environment overrides.
- The outer workflow supplies it to the only governed training subprocess, the pinned cascade
  script's `_train` command. That command performs Ultralytics training in-process and therefore
  inherits `Agg` and the telemetry flags.
- Package creation, archive verification and workflow logging load the primary runner with the same
  exact `M1_RUNNER_SHA256` constant. No old primary SHA literal remains in the cascade runner.
- During the review, the first snapshot still had the old primary SHA literal in `run_workflow`.
  The PM replaced it with the shared constant before the final reviewed snapshot and added a
  regression assertion that the real primary bytes match the constant and the retired literal is
  absent. The final snapshot was fully re-tested after that correction.

No CLI flag, environment merge after the helper, alternate check/train launcher or sealed-test path
was found that bypasses these controls.

## Reviewed byte pins

| Item | SHA-256 |
| --- | --- |
| Primary runner | `6a508eebcb83915201569bc74913a3dd546b288caf2331a9b3e4bd7a567500bc` |
| Cascade runner | `6572931946b4f2418607cf621ca108b21d633e34226648d497e82909ad3dad95` |
| Primary regression tests | `3fdd9611af6c3bab270150145c50f5415fe3e3aa81a798feee920eff51dd1ae2` |
| Cascade regression tests | `645b6f8a0bf071dba6ab72ec1f624847e25adadc66ab770605f15879a05d18f5` |
| Incident record | `90a4ff944beb7f4e2767c12b9f0dde987ec4c5e1f700218a9a5e3404d5742313` |
| R1 remediation report | `df9995a5ea96fa3ab50dffdbc568a9091635059feb3a98b8f16dd3eb1157f50d` |

## Validation

| Gate | Result |
| --- | --- |
| `tests/test_m1_colab.py` | PASS, **23/23** |
| `tests/test_d1_cascade_colab.py` | PASS, **33/33** |
| Combined affected tests | PASS, **56/56** |
| Complete detector pytest | PASS, **79/79** |
| Root Ruff and root lock | PASS; lock resolved **168 packages** |
| Detector Ruff | PASS |
| Repository verifier matrix | PASS, **52/52** |
| `git diff --check` | PASS |
| Graft rebuild/check | PASS, graph synchronized at **2,521 nodes / 6,379 edges** |
| Exact `results/experiments/sealed_test_access_log.jsonl` | ABSENT |

No Colab cell was executed, no Drive object was changed, no dataset/model/result was uploaded or
downloaded, no model was trained, no sealed-test artifact was opened, and no commit or push was
performed by this QA session.
