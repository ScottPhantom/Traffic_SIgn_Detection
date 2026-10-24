# VGG16-54 R1 — independent source QA R1

Verdict: **FAIL**

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Boundary: `READ_ONLY_SOURCE_QA_NO_GPU_RUN_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Reviewed snapshot

- Source manifest SHA-256:
  `af81e205356dbe43975e900f8ba9ddff6d270bf2547bfa01700a5f5314dc8c16`.
- VGG configuration SHA-256:
  `b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a`.
- Runner SHA-256:
  `4d6092d1c10e3ae4aca95ab422fd3e9c980bf438a666b91bd6f9f3855cdafaec`.
- VGG test SHA-256:
  `6d8e62fc8628dce16a1519313a36799fcc49db8d790f6f300195146b90ec2bb3`.

The independent reviewer reproduced the earlier smoke-boundary defect and confirmed that the
reviewed runner revision rejects fresh smoke from a nonzero epoch and resume smoke from any
checkpoint other than epoch 1. Targeted Ruff, lock and 26 checkpoint/VGG tests passed. Twelve of
twelve proof hash/schema/seal/symlink attacks were rejected. The bundle was read back as 3,712
train frames / 12,621 train boxes and 376 validation frames / 624 validation boxes, with no test
member and `sealed_test_accessed=false`.

## Blocking finding H-1 — telemetry was checked too late

The reviewer changed `checkpoint_io_seconds` to `-1` in `checkpoint_io.jsonl`. On the reviewed
snapshot, `EfficientCheckpointStore.restore_latest(...)` still restored the checkpoint. The
tamper was rejected only at the next `save(epoch=2)`. Because the runner restored, loaded and
trained before that save, a corrupt ledger did not fail closed before GPU work.

Required remediation: verify the full chained telemetry before any restore copy or model load,
and add a regression proving no destination is created from a tampered ledger.

## Blocking finding G-1 — mandatory full suite was not green

The full detector suite reached 100% with one failure:
`tests/test_val_reeval_r2.py::test_real_inputs_pass_check_without_model`. The failure occurred
because the real D1-VRE-R2 output already existed and the test called `preflight()` against the
shared repository output path. This was classified as a pre-existing output-state/test-isolation
problem, not a VGG runtime regression. The QA brief nevertheless requires a green full detector
suite.

Required remediation: isolate only that test's output-path check with `tmp_path`/`monkeypatch`;
do not delete, overwrite or rename the real evaluation result.

## Authorization

No machine-readable source-QA PASS proof was created. This FAIL does not authorize a Colab smoke,
long training, publication, sealed-test access, upload, commit or push.
