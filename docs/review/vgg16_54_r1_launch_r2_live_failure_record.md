# VGG16-54 R1 R2 live fresh-smoke failure record

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Status: `TERMINAL_FAILURE_BEFORE_STATE_CREATION`

The exact QA-approved R2 notebook SHA
`79bed40e4854717872cf6be0037e3e20e29bacda95e2ce49611899357be03aa4` mounted the private
Drive, verified all three pinned proof hashes, verified `nvidia-smi`, checked out immutable source
commit `2e1d981e70e02b19d1998fa17be8c8a0de033df0`, completed `uv sync --frozen`, and extracted
the reviewed train/validation bundle. Its runner command then terminated before training with:

```text
ModuleNotFoundError: No module named 'colab'
```

The cause is script-path invocation: running `python colab/run_vgg16_54_r1_r1.py` places the
`detector/colab` directory, rather than `detector`, at the front of `sys.path`. Local pytest had
masked this because detector pytest config adds `.` to Python's import path.

The Drive state `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2` did not exist after the failure.
No ATTEMPT, checkpoint or epoch was created. The sealed test was not accessed.

The append-only R3 launcher changes only the invocation to
`python -m colab.run_vgg16_54_r1_r1`; source, proofs, configuration and R2 state contract remain
unchanged. R3 requires independent notebook QA before another fresh L4 smoke.
