# D1 Pilot R3 recovery notebook-pin independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS_PIN_PACKAGE_NO_LIVE_RESUME`  
Reviewer: `Codex independent source-QA session`  
Boundary: `READ_ONLY_NO_DRIVE_NO_COLAB_NO_TRAINING_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS with 0 Blocker, High, Medium or Low findings on Repair R1.** The exact package may be
committed and pushed. A live resume is allowed only after both the R3 source commit and notebook-pin
commit are present on the tracking remote and the raw sidecar/notebook hashes are read back.

| Reviewed artifact | SHA-256 |
| --- | --- |
| `detector/colab/d1_train_pilot_r3.ipynb` | `67d8d24a3f432b17085069d7d7545a3673bdd3fa6771be094f698c6e99e8ee81` |
| `scripts/build_d1_pilot_notebook_r3.py` | `cfd9d0517ead578d1eb6092be73718bb10fbe77fdfa46802f1b559a5c40378ce` |
| `tests/test_d1_pilot_r3_notebook.py` | `8bf195327cb07f0efd9c97a4383458f1adddec54297f4e636ca0ec93f8055d1c` |
| `docs/review/d1_pilot_r3_notebook_pin_implementation_record.md` | `12d38ef1d0faf4e4bdc7b65cec8ebeb581655285c3383770a8155dbab5043ee0` |
| pinned R3 recovery runner | `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` |

## Initial finding and closure

The first notebook candidate failed with one High finding: the verified sidecar path could be
replaced before cell 5 executed it or cell 6 imported it. The independent probe wrote a malicious
replacement and observed its marker execute.

Repair R1 creates the sidecar using `O_EXCL | O_NOFOLLOW`, rejects symlink/non-regular files, reads
through an `O_NOFOLLOW` descriptor and verifies exact SHA-256 at every use. Cell 5 executes the
captured verified bytes through `python -` stdin. Cell 6 compiles and executes captured verified
bytes in memory. Neither use re-opens an unchecked path.

Independent reproduction confirmed:

- post-download replacement is rejected and `INJECTED_EXECUTED` remains absent;
- replacing the path after capture cannot affect the bytes executed by cell 5 or cell 6;
- wrong download bytes fail before write;
- a symlink destination fails with its target unchanged;
- an absent sidecar is created as a regular mode-0600 file with exact bytes.

## Other controls and gates

- Frozen Pilot R2 source hash, replacement cardinalities and deterministic rebuild: PASS.
- `MODE="resume"`; no fresh branch or `--stop-after-epoch`: PASS.
- Training checkout exact commit `939f6bb...` and clean check: PASS.
- R3 sidecar implementation commit `e20a695...` and exact runner hash: PASS.
- Exact seed/epochs/imgsz/batch/patience/device/tag/state label: PASS.
- No `export-test`, `--final-eval` or processed-test path: PASS.
- Terminal requirements for `SUCCEEDED`, epoch 100, `epoch-0100`, one archive,
  retry-aware verifier and `sealed_test_accessed=false`: PASS.
- Focused R3 notebook + R3 + R2 tests: `37 passed, 1 intentional skip`.
- Scoped Ruff, locks, detector suite, verifier runner, Graft and diff check: PASS.

The reviewer did not access Drive or Colab. Sealed-test access and final evaluation remain NO-GO.
