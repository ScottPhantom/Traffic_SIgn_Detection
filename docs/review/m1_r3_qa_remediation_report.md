# M1-R3 independent-QA remediation report

- Status: `M1_R3_AWAITING_INDEPENDENT_QA`
- Recorded at: `2026-10-18T23:55:46+07:00`
- QA input: `docs/review/m1_r2_independent_qa_record.md`
- QA input SHA-256: `0e776459cc9397d3940198db8fe22716c2de707e20e91b8b5b1c5fb3b0816b07`
- Prior verdict: `FAIL` — 0 Critical, 1 High, 0 Medium, 0 Low

This successor package preserves the initial, R1 and R2 independent QA records. It addresses only
R2 finding H-4, does not claim QA PASS, and does not authorize training, upload or sealed-test
access.

## R3 remediation

### Exact final-report schemas

- Final test reports now require the exact top-level schema produced by `m1.cli evaluate`.
- All nested objects used as evidence have exact schemas: operating point, AP-small, every
  resolution row, UNKNOWN evidence, confusion matrix, error samples, group bootstrap and all
  single-seed/class gate rows. Unknown and missing keys fail closed.
- The report's complete weight and threshold-lock objects must equal the live bindings returned by
  the clean committed run registry and threshold lock; partial or augmented self-claims do not
  bind.
- Latency reports now require the exact CLI schema, exact environment schema, 50 warm-ups, 300
  measurements, batch 1, Apple M1 Pro/arm64/macOS/MPS and the current detector lock hash.

### Numeric domains and cross-field consistency

- Every AP, mAP, precision, recall, confidence, NMS and rate is a finite non-boolean number in
  `[0,1]`.
- FP/image and latency statistics are finite and non-negative. Counts and supports are
  non-negative integers; booleans are rejected as integers.
- mAP50-95 cannot exceed mAP50; UNKNOWN rate must reconcile with its counts; latency statistics
  must have consistent ordering and their `passed` flag is recomputed from p95.
- Confusion labels and matrix dimensions are bound to the governed class map. Per-class AP and
  class-gate rosters must equal classes with test support; each support must equal the
  corresponding confusion-row total.
- Critical/gated/passed flags, unverified/low-support rosters, all single-seed checks and the
  single-seed summary flag are recomputed from validated primary metrics and D-05.
- Aggregation additionally requires identical class and unverified rosters across all three
  validated reports. The final mean/std and every global/class gate are therefore computed only
  from validated inputs.

### Adversarial regression coverage

- Unit attacks cover negative, greater-than-one, non-finite and boolean values for every
  rate-valued field consumed by `_mean_std` or a class/global gate.
- FP/image and p95 attacks cover negative, non-finite and boolean values while preserving their
  valid unbounded-above domain.
- A literal JSON exponent overflow (`1e999`), unknown top-level fields and latency schema
  extensions are rejected.
- An invalid report is proven to fail before the aggregate output path is created.
- A complete synthetic positive test-report and latency-report pair still validates.

## Bound R3 files

| File | SHA-256 |
| --- | --- |
| `detector/m1/cli.py` | `c27e3289a49dd4838126456f472d57565ace9e8836100c2d4775c936626bb80a` |
| `detector/tests/test_m1.py` | `7006f07f1b53e0dd96d8b7a63da00d46a10f40fe9e21fc3824430244309ab113` |
| `detector/m1/contract.py` | `cdf2ccbaf874e0cbdbcaf84d52d07926515301388972c1af5524a013a4ee027b` |
| `detector/m1/metrics.py` | `5be0503886760b2567a7d10ada38a2aad07d2964a8bdbb96019e1186274ab650` |
| `scripts/build_m1_yolo_dataset.py` | `3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93` |
| `scripts/build_dataset01_crops.py` | `1f1bfac322b03ede2d1e657faa2bf167b1059b978a7356f982586d5405f7bf27` |
| `tests/test_m1_yolo_dataset.py` | `8ccc91ecdd3b686167796b72f2ca9127bc1f55b85af1bddff6c236510f7dae03` |
| `tests/test_dataset01_crops.py` | `a5e64bc103706a4a2094f495e63d7f8ac2e435bad6e8e37038b4350e0a45a989` |
| `docs/review/generated/m1_yolo_export_manifest.json` | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` |
| `docs/review/generated/dataset01_crops_manifest.json` | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |

## PM validation before re-review

- Root M1/crop tests: `16/16` PASS.
- Detector tests: `43/43` PASS.
- Root and detector Ruff/lock gates: PASS.
- Package verifiers: `51/51` PASS in 85.3 seconds wall time.
- `m1.cli check`: PASS; it reports Apple M1 Pro, arm64, MPS, the current export hash and sealed-test
  stem hash `afa03d4b…`.
- `git diff --check`: PASS.
- Graft build/check: PASS, 2,222 nodes and 5,641 edges. The changed validators have only the final
  aggregate plus the R3 regression tests as callers/consumers.
- The full historical root pytest suite was not run because known pinned successor-absence tests
  are stale after later work packages; the current targeted root and all 51 package verifiers ran.

## Evidence boundary and next gate

- No training, prediction, latency benchmark, upload, commit, push or deployment occurred in R3.
- No sealed-test file, label, image or metric was opened. No real run registry, threshold lock,
  test export, crop `test.p` or sealed-test access log exists.
- Source remains frozen at the hashes above until an independent session finishes the R3 attack
  matrix and writes an append-only verdict.
- Pilot/Colab work remains blocked until that verdict is PASS.
