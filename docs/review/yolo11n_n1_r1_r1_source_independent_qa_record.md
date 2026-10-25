# YOLO11n N1 R1-R1 source independent QA record

Date: 2026-10-25 (Asia/Ho_Chi_Minh)  
Verdict: **PASS — SOURCE ONLY, PRE-COMMIT**  
Reviewer: independent QA session `/root/yolo11n_dual_track_r1_source_qa`

## Scope and boundary

This review covers only the append-only repair for the failed N1 fresh smoke. It does not authorize
long training, result publication, sealed-test access, or promotion of the failed R1 state. The old
runner and failed Drive state remain immutable evidence.

## Pinned reviewed files

| File | SHA-256 |
| --- | --- |
| `detector/colab/run_yolo11n_n1_r1_r1.py` | `cd3edab0adee25c8642f840edb36d899687ba952bdfcbaca853568f65dcd72e6` |
| `detector/tests/test_yolo11n_n1_r1_r1.py` | `b1258334cb47b853baf46ceff84aee5b524fcefc4e7786c7f219cc47c96e6216` |
| `docs/review/yolo11n_n1_r1_live_smoke_failure_record.md` | `815fa72cd9c3a5b31f8bd7cbfd3a7fc4c2a094045ac6dfdf4f3bee7762b7512e` |

References verified unchanged:

| File | SHA-256 |
| --- | --- |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/colab/run_yolo11n_n1_r1.py` | `b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753` |

## Findings

- The observed terminal failure is real: the original name `YOLO11N_N1_detector` violates the
  checkpoint contract `D1_[A-Za-z0-9_.-]+$`.
- The successor uses exactly `D1_yolo11n_n1_detector`; both the production regex and an actual
  `CheckpointStore.save/load_latest` round trip accept it.
- The successor state is isolated at
  `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1_r1`; it rejects the old R1 state.
- Owner-frozen configuration is unchanged: YOLO11n, pretrained hash, seed `20261018`, 100 detector
  epochs, image size 1280, batch 4, `fliplr=0`, and reuse of the existing classifiers.
- The CLI remains `check|detector`; no classifier retraining, `export-test`, `--final-eval`, or test
  route was introduced.
- The old source-QA record cannot authorize the repair runner. The successor requires a new QA
  record containing the exact repair-runner SHA-256.
- Long training still fails closed without the independent smoke/resume proof.
- Failure artifacts and SQLite events show `ATTEMPT`, `FRESH`, `FAILED`; every inspected seal field
  is false.

## Reproduced checks

```text
cd detector && uv run ruff check colab/run_yolo11n_n1_r1_r1.py tests/test_yolo11n_n1_r1_r1.py
cd detector && uv run pytest -q tests/test_yolo11n_n1_r1.py tests/test_yolo11n_n1_r1_r1.py tests/test_checkpoint_store.py tests/test_checkpoint_store_r2.py
```

Result: lint PASS; **26 tests passed**; Graft graph OK. No blocker was found.

## Next gate

After this record is committed, a new notebook must pin the immutable repair commit and this QA
record hash, target only the R1-R1 state, and undergo notebook-delta QA. Only then may the new L4
fresh epoch-1 smoke start. A second, genuinely different L4 must resume to epoch 2, followed by
independent artifact QA. Long training remains blocked until those gates pass.

`sealed_test_accessed=false`.
