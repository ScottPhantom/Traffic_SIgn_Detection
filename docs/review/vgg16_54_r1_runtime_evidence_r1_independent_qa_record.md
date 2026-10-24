# VGG16-54 R1 runtime evidence R1 — independent source QA

Verdict: **PASS**

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Boundary: `SOURCE_QA_ONLY_NO_TRAIN_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Reviewed snapshot

- Runtime contract SHA-256:
  `93b2b35d10ca253347e7be4f693b1f4af17fa1f578fb54ea2cc0a54bdbaffdd0`.
- Successor runner SHA-256:
  `46eddeab153f8c775a44a1cc3e3cae5340c2cd4d4c5e5dc68f47b5ba556b259e`.
- Runtime-identity dependency SHA-256:
  `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112`.
- Focused test SHA-256:
  `c9e9d9c750f09745cbfe6912f922f99909ceff38051a2aac3f20f3fcc742c301`.
- Implementation record SHA-256:
  `1ec9a2d329eb7a6c255e117bb84c77faaa8ecf94a1fc4050928113f202fa60ea`.

## Findings

- Runtime startup fails closed unless CUDA is available and device zero reports exactly
  `NVIDIA L4`. Empty CUDA metadata, a T4 device and a malformed Linux boot ID were rejected.
- The privacy-preserving runtime digest is deterministic for the same package tag and Linux boot
  ID and differs when the boot ID differs. The raw boot ID is not persisted.
- The governed shared event writer persisted an identical ATTEMPT object into `train.log`, the
  SQLite `logs` table and `colab_execution.json.execution_attempts`. The object includes the
  runtime identity, GPU/CUDA metadata, run-binding SHA, checkpoint-binding SHA and
  `sealed_test_accessed=false`.
- The successor state suffix is
  `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`. The failed R1 suffix is rejected and was not
  mutated.
- Fresh mode is restricted to the epoch-1 smoke (`stop_after=1`). Resume smoke rejects the fresh
  runtime digest and accepts only a distinct runtime. A long run requires `mode=resume`, the
  reviewed two-attempt epoch-2 terminal state and the exact reviewed resume-runtime digest.
- Missing, malformed and repeated runtime digests; wrong GPU/CUDA values; wrong run/checkpoint
  bindings; symlinked, duplicate-key and non-finite execution/proof JSON; source drift; and a
  long-run runtime substitution were all rejected.
- The successor source proof is hash-bound to exactly three single-link, non-symlink source files.
  The original Owner approval and base VGG16 source-QA proof remain mandatory inputs.
- Neither the successor runner nor its contract exposes a sealed-test or final-evaluation route.

## Verification

- Focused Ruff: PASS.
- Thirty focused/regression tests covering the runtime successor, base VGG16 contract and
  checkpoint-store successor: PASS.
- Independent adversarial matrix: 17/17 attacks rejected.
- Shared-event persistence readback across text, SQLite and execution JSON: PASS.
- Boot-scoped identity and exact L4 negative tests: PASS.
- `uv lock --check`: PASS.
- Final `graft check .`: `OK`, 4,913 nodes.

## Authorization

This PASS authorizes only use of these exact source bytes to prepare and run the future fresh
epoch-1 L4 smoke in the isolated R2 state after all original Owner/base-source proofs and this
successor proof are pinned. It does not authorize resume smoke, long training, result publication,
upload, commit, push or sealed-test access. Resume smoke requires a separately observed new L4
runtime and the valid epoch-1 artifact; long training requires independent two-runtime smoke QA.

No training, upload, download, commit, push or sealed-test access occurred during this review.
