# D1 Colab backend R1 QA remediation report

Status: `R1_AWAITING_INDEPENDENT_QA`

Date: `2026-10-20` (`Asia/Ho_Chi_Minh`)

## Scope

R1 addresses the observed pre-epoch Colab failure caused by the inherited
`module://matplotlib_inline.backend_inline` backend. The primary and cascade workflows now force
`MPLBACKEND=Agg` for governed subprocesses. Tests reproduce the inherited bad value and require all
headless/telemetry environment controls.

## Required independent checks

1. Confirm the exact observed failure is preserved in the incident record and is not described as
   CUDA OOM or a training result.
2. Confirm both primary `check`/`train` and cascade outer/internal subprocess paths receive the
   headless environment.
3. Confirm an inherited inline backend cannot override `Agg`.
4. Confirm the cascade primary-runner byte pin matches the repaired file.
5. Re-run primary Colab, cascade Colab, detector, verifier, Ruff, lock and Graft gates.
6. Confirm the failed Drive run is not deleted/reused and the sealed-test access log remains absent.

This package changes no dataset, taxonomy, split, D-05 gate, model weight or sealed-test state. A
real Colab smoke remains required after QA and successor-bundle delivery.
