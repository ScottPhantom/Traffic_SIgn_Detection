# M1-R2 independent-QA remediation report

- Status: `M1_R2_AWAITING_INDEPENDENT_QA`
- Recorded at: `2026-10-18T23:45:27+07:00`
- QA input: `docs/review/m1_r1_independent_qa_record.md`
- QA input SHA-256: `feaad72c4dfdf237e97c7d40c65a15e796bf889a50210cab2b9bad067c0faa84`
- Prior verdict: `FAIL` — 1 Critical, 3 High, 0 Medium, 1 Low

This R2 package preserves both earlier QA FAIL records. It does not claim QA PASS and does not
authorize training, upload or sealed-test access.

## R2 remediation

### C-1 strict committed threshold lock

- JSON parsing rejects duplicate keys, `NaN` and Infinity.
- The lock requires an exact top-level schema, `sealed_test_seen=false`, the current export hash
  and test seal, exactly three candidates, exact approved seeds, distinct weights, finite conf/NMS
  in `[0,1]`, exact run-contract/run-attestation bindings and three live val-report hashes.
- Every candidate is rebound through the clean committed run registry before the lock is accepted.

### H-1 WP35 source binding

- The verifier checks both WP35 source image and source label bytes against the lineage SHA-256
  before deriving expected exported labels. Coherent source/export label mutation now fails.

### H-2 independent checkpoint trust anchor

- `run_contract.json` must now match an exact complete schema and all M1 invariants: approved
  pretrained hash, export/class/split hashes, detector lock, D-05 gates, seed, deterministic
  training, `fliplr=0`, and both produced weight hashes.
- A checkpoint is not usable from its neighbouring contract alone. `register-runs` produces
  `docs/review/generated/d1_run_registry.json`; evaluation/latency require this registry to be
  Git-tracked and clean and to contain the exact canonical run attestation.
- Registry creation does not itself approve a run: it reports `ready_for_evaluation=false` until
  independently reviewed and committed unchanged.

### H-3 exact crop roster

- The crop package accepts exactly `train.p`, `valid.p`, their two index CSV files and
  `signnames.csv`; missing, modified, symlinked or extra files fail closed. A future sealed-test
  crop package must use a separately defined post-final-evaluation state.

### M-1 real three-seed aggregate and Q6 schema

- Every test/latency report seed must equal the seed returned from the committed run registry.
- Final aggregation requires three distinct seeds, weight hashes, run directories and run
  attestations, plus one real committed threshold lock rebound per candidate.
- Test reports must contain non-null bootstrap evidence, resolution breakdown, confusion matrix,
  error samples, UNKNOWN evidence, named AP-small method and class support/unverified evidence.
- Latency reports must identify `Apple M1 Pro`, `arm64`, macOS, MPS available and `device=mps`;
  the same three registered weights must match the test reports.

## Bound R2 files

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset.py` | `3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93` |
| `scripts/build_dataset01_crops.py` | `1f1bfac322b03ede2d1e657faa2bf167b1059b978a7356f982586d5405f7bf27` |
| `detector/m1/contract.py` | `cdf2ccbaf874e0cbdbcaf84d52d07926515301388972c1af5524a013a4ee027b` |
| `detector/m1/cli.py` | `37b885796b31dc780090750878856f0796f76f0f1074ea1919058e79393bc846` |
| `detector/m1/metrics.py` | `5be0503886760b2567a7d10ada38a2aad07d2964a8bdbb96019e1186274ab650` |
| `detector/tests/test_m1.py` | `7adaa700dae2852f4ec0bb6a4649b961b7457f4e385266fa684b3d797a35750d` |
| `tests/test_m1_yolo_dataset.py` | `8ccc91ecdd3b686167796b72f2ca9127bc1f55b85af1bddff6c236510f7dae03` |
| `tests/test_dataset01_crops.py` | `a5e64bc103706a4a2094f495e63d7f8ac2e435bad6e8e37038b4350e0a45a989` |
| `docs/review/generated/m1_yolo_export_manifest.json` | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` |
| `docs/review/generated/dataset01_crops_manifest.json` | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |

## PM validation before re-review

- Root M1/crop tests: `16/16` PASS.
- Detector tests: `14/14` PASS.
- Root and detector Ruff/lock gates: PASS.
- Package verifiers: `51/51` PASS in 85.0 seconds wall time.
- `m1.cli check`: PASS; reports hardware chip `Apple M1 Pro`, MPS available, current export hash
  and sealed-test stem hash `afa03d4b…`.
- Graft build/check: PASS, 2,206 nodes and 5,597 edges.
- No run registry or threshold lock exists yet because no detector run exists. No test export,
  crop test file or sealed-test access log exists.
