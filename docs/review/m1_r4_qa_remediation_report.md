# M1-R4 independent-QA remediation report

- Status: `M1_R4_AWAITING_INDEPENDENT_QA`
- Recorded at: `2026-10-19T00:06:23+07:00`
- QA input: `docs/review/m1_r3_independent_qa_record.md`
- QA input SHA-256: `6da1eb65ca5f28794d67e9ac518994f79d49e099546e151ce657802ed4a7b6d9`
- Prior verdict: `FAIL` — 0 Critical, 2 High, 0 Medium, 0 Low

This successor package preserves every prior independent QA record. It addresses only findings
H-4A and H-5, does not claim QA PASS, and does not authorize training, upload or sealed-test
access.

## R4 remediation

### H-4A — bind gates to primary counts and AP evidence

- `OperatingPoint` now retains integer image, ground-truth, class-agnostic true-positive and
  false-positive counts, plus integer class-aware hits per class.
- The evaluation JSON records those counts globally and per resolution. The validator recomputes
  precision, class-agnostic recall and FP/image from them with tolerance `1e-6`.
- Resolution rows must contain exact counts, internally reproduce their ratios, and sum exactly to
  the global operating-point counts.
- The confusion matrix independently derives GT support, class-agnostic matches and false
  predictions. All three must equal the operating-point counts.
- Every class gate now includes integer class-aware `hits`; support must match the confusion row
  total and recall must equal `hits / support`. Critical/gated/passed flags are then recomputed.
- Global mAP50 must equal the mean of the supported per-class AP50 values within `1e-6`, matching
  the Ultralytics aggregate definition.
- AP-small now requires zero classes and zero support together, and either forces value zero or
  requires positive primary support for a non-zero value.

### H-5 — bind latency to the final evaluation configuration

- `m1.cli latency` now accepts and records NMS IoU plus a threshold-lock binding, passes the NMS
  value into `YOLO.predict`, and fails if the supplied confidence/NMS differs from that run's
  committed lock candidate.
- A latency artifact used by `aggregate-final` must contain the complete live threshold-lock
  binding and exact confidence/NMS values.
- Final aggregation requires all three test reports and all three latency reports to use one image
  size. Per seed it requires identical weight, threshold lock, image size, confidence and NMS.
- Pilot latency may still be produced without a final lock, but such a provisional artifact is
  intentionally rejected by the final validator/aggregate.

### Regression coverage

- The R3 240-mutation domain/schema matrix remains represented by the detector suite.
- New attacks reject: confusion miss-all versus recall PASS; mAP50 versus per-class AP50 mismatch;
  class hits versus recall mismatch; AP-small non-zero without support; resolution-count drift;
  latency report without/tampering its lock; changed latency confidence/NMS; and mixed/smaller
  latency image size.
- Every aggregate configuration attack asserts that no output file is created.
- The complete positive test and latency reports still validate.

## Bound R4 files

| File | SHA-256 |
| --- | --- |
| `detector/m1/cli.py` | `fa776f4e567b42e44190248e37731a7c39d32ee1a107c0664082d6bb997a997c` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/tests/test_m1.py` | `97c5c97bfe866362b10c7e5bf044b2dbf52a621b80879374bbfb78aebda4c279` |
| `detector/m1/contract.py` | `cdf2ccbaf874e0cbdbcaf84d52d07926515301388972c1af5524a013a4ee027b` |
| `scripts/build_m1_yolo_dataset.py` | `3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93` |
| `scripts/build_dataset01_crops.py` | `1f1bfac322b03ede2d1e657faa2bf167b1059b978a7356f982586d5405f7bf27` |
| `tests/test_m1_yolo_dataset.py` | `8ccc91ecdd3b686167796b72f2ca9127bc1f55b85af1bddff6c236510f7dae03` |
| `tests/test_dataset01_crops.py` | `a5e64bc103706a4a2094f495e63d7f8ac2e435bad6e8e37038b4350e0a45a989` |
| `docs/review/generated/m1_yolo_export_manifest.json` | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` |
| `docs/review/generated/dataset01_crops_manifest.json` | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |

## PM validation before re-review

- Root M1/crop tests: `16/16` PASS.
- Detector tests: `53/53` PASS.
- Root and detector Ruff/lock gates: PASS.
- Package verifiers: `51/51` PASS in 85.5 seconds wall time.
- `m1.cli check`: PASS; Apple M1 Pro/arm64/MPS, export manifest and sealed-test stem hash
  `afa03d4b…` remain bound.
- `git diff --check`: PASS.
- Graft build/check: PASS, 2,226 nodes and 5,654 edges.
- The full historical root pytest suite was not run because known pinned successor-absence tests
  are stale after later work packages; the targeted root suite and all package verifiers ran.

## Evidence boundary and next gate

- No training, real prediction, latency benchmark, upload, commit, push or deployment occurred.
- No sealed-test image, label, export or metric was opened. No real run registry, threshold lock,
  test export, crop `test.p` or sealed-test access log exists.
- Source remains frozen at the hashes above pending a successor independent review. Pilot/Colab
  work remains blocked until that review returns PASS.
