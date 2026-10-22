# CPV301 AutoDrive — verified project status 2026-10-22

## Outcome

The dataset correction, local integration and corrected-validation baseline are independently QA
PASS. The project is still **not ready to start another 100-epoch run**: R10 improves AP and overall
recall, but FP/image and the supported critical-class gates still fail.

## Verified completed work

- WP38-R1 corrected exactly validation stems `1319..1357` (39 frames, 29 boxes) from stored
  540x960 orientation to lossless 960x540 PNG derivatives while keeping raw bytes and WP36-R1
  membership unchanged. Independent QA: PASS.
- Integration R4 materialized locally with 3,712 train and 376 validation images, exactly 39
  corrected validation frames, no test payload and `sealed_test_accessed=false`. Independent QA:
  PASS; record SHA-256 `27425608…`.
- Colab bundle R2 verifies an exact 5,927-file train/val-only roster. Independent QA: PASS; record
  SHA-256 `436a0f18…`.
- Dataset Graph now reports the accepted WP36-R1 map: 3,216 raw nodes, 1,912 train, 376 val, 903
  sealed test, 25 quarantined raw frames, 54 capture groups, zero mixed groups and 39 corrected
  markers in group `D02-C0034`.
- Corrected R10 evidence is content-bound and result-QA PASS: mAP50 0.8689, mAP50-95 0.6253,
  agnostic recall 0.8625, FP/image 0.5691 at confidence 0.20. Result content SHA-256 is
  `b33e2470…`; result QA record SHA-256 is `9940b31c…`.
- The earlier baseline was mAP50 0.8292, mAP50-95 0.5888, recall 0.8571 and FP/image 0.5505.
  Correcting orientation improved AP and overall recall, but did not solve false positives.

## Current blocker

R1–R8 are preserved immutable QA FAIL records. R9 source QA passed, but its live attempt failed
closed because a valid JSON round trip changed tuple/list and numeric/string-key representations;
the R9 preview is not an accepted result. R10 retains exact intended canonical bytes, content URI,
descriptor/inode/mode/link binding and compares documents in normalized JSON space. Source QA and
the real R10 artifact/report both passed independent QA.

The active blocker is now model quality: FP/image 0.5691 exceeds 0.30, while critical classes 7,
32 and 41 have recall 0.5946, 0.6207 and 0.5714. The next package must analyze validation false
positives and those supported critical classes, then freeze a new improvement experiment contract
for independent QA before any training.

## Local versus Drive

- Local: WP38-R1 integration R4 and bundle R2 are verified and QA PASS.
- Drive: still contains the earlier `m1_colab_train_val_backend_r1` package; no WP38 corrected
  bundle was found.
- No official corrected archive has been created, committed, pushed or uploaded.

## Authorization state

- New 100-epoch training: **NO-GO**.
- Seeds `20261019` and `20261020`: **NO-GO**.
- Corrected-validation model inference: **COMPLETE / QA PASS for seed 20261018 R10**.
- Validation-only error analysis and improvement packet: **NEXT**.
- Sealed test export/evaluation: **NO-GO; not accessed**.
- Commit/push/upload corrected bundle: requires explicit Owner authorization.
