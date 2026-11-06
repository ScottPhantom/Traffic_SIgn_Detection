# D1 R3 two-seed threshold-lock successor — independent source QA

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: independent Codex agent
`/root/r3_lock_source_qa`. I did not author or edit the reviewed source, tests, or
implementation record. This review read only the R3 validation bundle and the
already-pinned pilot NMS CSVs. It did not read seed-20261019 predictions, infer,
train, create a real lock, or access the sealed test. `sealed_test_accessed=false`.

Verdict: PASS giới hạn — the source implements the frozen two-seed R3 selection and fail-closed binding gates tested here; real pilot/S2 archive and inference-QA integration remain unexecuted and require their own future result QA before any lock approval.

## Reviewed versions

| File | SHA-256 |
| --- | --- |
| `detector/m1/d1_threshold_lock_r3_successor.py` | `6e15865a7fe4bcbad27cbd5c66ff74eeb0f8d8df9b8070e6777f6ca2a845c454` |
| `detector/tests/test_d1_threshold_lock_r3_successor.py` | `b5ab720cd0addb12384ac989c4d09300a07e3fe34e36e747e1f0ce284269f14c` |
| `docs/review/d1_threshold_lock_r3_successor_implementation_record.md` | `e46a6623c03cca2922cf5ab975c7992cab876f2489be8fb25d2ff5bdead82618` |
| Frozen base contract | `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f` |
| Two-seed addendum | `cefbdc627266588735e0369c42b1fe426e85e78c38b3eaddef2f61ac9484a82b` |

The addendum's delta independent QA is PASS with its identified abbreviated-hash
errors corrected before commit. The current documents' hashes above are the
corrected committed bytes. Graft graph check was OK before source review.

## Contract checks

- **Inputs:** exactly seeds `20261018` and `20261019`, two distinct QA-pinned
  weights/contracts/attestations, identical R3 stems, GT, groups, class map,
  bundle and scorer hashes. Both reports are rebuilt from 11 pinned CSVs and
  compared with the supplied JSON. The bundle is validation-only: 376 images,
  624 GT boxes, nine groups, `sealed_test_accessed=false`.
- **Scoring:** frozen 31-confidence union grid and 11 NMS configurations.
  Each report records per-frame and total TP, FP, exact-class hits, recall,
  FP/image and full-candidate AP. The selection uses the arithmetic two-seed
  mean, per-seed values and their difference. It requires mean recall at least
  0.85, then minimizes FP/image with the frozen tie order. No eligible class-aware
  IoU 0.70 point means no lock.
- **NMS change:** source calls the pinned shared-draw 1,000-round nine-group
  bootstrap and nine leave-one-group-out folds. A change away from class-aware
  0.70 requires all three frozen CI/fold conditions. Otherwise the 0.70 point
  is retained. Tests cover each failed condition, success, shared draws and
  deterministic nine-fold output.
- **Binding:** eight-member archive verifier runs before report creation;
  archive, manifest, trained run contract, best-weight and attestation hashes
  are checked against the exact pilot/S2 run pins. Pilot's historical QA uses
  Markdown `**PASS**` and binds weight/contract/attestation; S2 QA binds
  archive/manifest/weight. Future inference authorization and independent
  result QA must bind confidence floor 0.001, candidate weight and all 11 CSV
  hashes. The writer uses schema 2 with a hashed R3 proof sidecar. Verification
  recomputes source reports/selection and requires each candidate report
  path/hash in the proof and identical settings. The final reader additionally
  requires the lock, proof, lock-result QA and Owner approval to match HEAD bytes
  and both approval documents to name the lock/proof hashes; it never opens test.

## Independent pilot recalculation and gates

I loaded the QA-pinned pilot `classaware_0.70` CSV directly with the common
validation scorer. At confidence 0.05 it returned **588 TP / 306 FP / 503
correct-class hits**, matching the QA JSON. At confidence 0.20 it returned
**547 / 150 / 457**, also matching; fine-grid confidence 0.19 returned
**555 / 155 / 461** as a source check only. The test suite invokes the real
seed-report builder on all 11 pilot CSVs, compares all 19 coarse-grid cells
and each configuration's full-candidate mAP50-95 to the QA JSON, and checks
the 0.19 fine point. It bypasses only future per-seed authorization metadata
for this historical one-seed scoring check; separate synthetic tests exercise
the metadata refusals.

- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_d1_threshold_lock_r3_successor.py`: **10 passed**.
- `cd detector && uv run --no-sync ruff check m1/d1_threshold_lock_r3_successor.py tests/test_d1_threshold_lock_r3_successor.py`: **passed**.

## Limits and next gates

The pilot archive is not available in this checkout, so QA did not execute
the archive verifier against a real pilot archive. The synthetic archive test
checks the new binding logic with a stubbed archive verifier; the real archive
verifier remains the already-pinned `run_d1_colab.verify_result_archive`.
No seed-20261019 NMS predictions or real two-seed lock were used. A future
execution still needs a named inference authorization covering use of the
predictions, independent inference-result QA, real report/lock result QA,
clean committed records and explicit Owner approval. This PASS is for source
readiness only; it is not a threshold lock or validation/test result.
