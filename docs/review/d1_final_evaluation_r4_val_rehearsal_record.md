# D1 final evaluation R4 — validation R3 rehearsal

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`). Status: `VALIDATION_REHEARSAL_PASSED`.

This is a new append-only record following
`d1_final_evaluation_r4_val_rehearsal_failure_record.md`; that earlier failure
record remains unchanged. The command below used the R3 validation bundle and
two pinned weights on MPS. It did not call the real test opener or test scorer:

```bash
cd detector/
PYTHONPATH=. uv run --no-sync python -m m1.d1_final_evaluation_r1 \
  --plan docs/review/generated/d1_final_evaluation_r4_plan.json \
  --rehearse-validation
```

Exit status: 0. The pinned bundle manifest SHA-256 is
`8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.
Its 376 validation image members have 337 `.jpg` and 39 `.png` paths. The
roster used each actual member path. The common setting was confidence 0.19,
class-aware NMS IoU 0.70, inference candidate floor 0.001, image size 1280,
and MPS. Ground truth contained 624 boxes in 376 images.

| Seed | Weight SHA-256 | TP | FP | Agnostic recall | FP/image |
| --- | --- | ---: | ---: | ---: | ---: |
| 20261018 | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` | 555 | 155 | 0.88942308 | 0.41223404 |
| 20261019 | `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce` | 512 | 131 | 0.82051282 | 0.34840426 |
| Two-seed mean | — | — | — | **0.85496795** | **0.38031915** |

The TP/FP counts exactly match the R3 threshold-lock sanity target (555/512,
155/131), as do mean recall 0.85497 and FP/image 0.38032 after rounding. These
are validation results, not test results or acceptance claims. Q5 latency and
a final verdict were not measured in the rehearsal.

## Output readback

All files are under the Git-ignored
`results/experiments/d1_final_evaluation_r4_rehearsal_val/`. Predictions were
saved before scoring. The prediction manifests bind each file hash and weight
hash; the JSON report binds the R4 plan hash
`2c463b61bbe73e482e28b1454023db438cc7d363f2ebc3525da942d37e74fc6f`.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `predictions_seed_20261018.json` | 449226 | `4b7b366ada672cea432202d6735345864c3d541173d44ed7e86f8a0f081a6b63` |
| `predictions_seed_20261018_manifest.json` | 248 | `b55a0ff6752b85d4dfd331599233d03b5e3fc66d2c0a87058c76489cd9c61255` |
| `predictions_seed_20261019.json` | 586313 | `60a71ee5f3a88ae53dd048d4aacbcc3490f5146deee5676233028526b14f8642` |
| `predictions_seed_20261019_manifest.json` | 248 | `687cd2c687579025ac6aa25b28ea0b30343a11233736b91dd9cc68e9b0261c13` |
| `d1_final_evaluation_r1.json` | 115517 | `48c2c45aac6e3ff14a2fbd934fafe1f32b8fb7b216ea08c7dc1534df428bf7db` |
| `d1_final_evaluation_r1.md` | 979 | `451a6c6f84f4b2e9161a24756bd2f6dea13d3f3d16eccf8f10081ee86b980ea0` |

The output JSON reports `split=val` and `sealed_test_accessed=false` for this
rehearsal. The sealed test had been opened in historical R3 attempt 3; this
R4 preparation made **no new sealed-test access**. The append-only access log
remained exactly three lines with SHA-256
`a8f45f5092ff7c7f8dea66bde0620b9108d7f61174d885bb3c424a8cdf477e45`.

Scorer source SHA-256:
`2be9ad7da62268f418d1138bb01d2f81a2dfb20aa7c711ddcda4237a927ce75a`.
Test source SHA-256:
`fce4ece4a74e996dbdc13ff3aeb56f3dfbd3b6f46c6f5ff39b28fb51975c1e45`.
The focused scorer suite passed 32 tests; Ruff and `uv lock --check` passed.
Independent source QA is still required before the R4 contract is finalized.
