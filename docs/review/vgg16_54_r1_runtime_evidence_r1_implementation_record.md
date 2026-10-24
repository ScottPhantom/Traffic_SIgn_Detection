# VGG16-54 R1 runtime evidence R1 implementation record

Status: `SOURCE_CANDIDATE_AWAITING_INDEPENDENT_QA`

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Boundary: `SOURCE_ONLY_NO_GPU_RUN_NO_UPLOAD_NO_DOWNLOAD_NO_SEALED_TEST`

## Reason for successor

The first fresh epoch-1 artifact was otherwise valid but independent artifact QA correctly failed
it because the ATTEMPT evidence did not persist an L4 identity or a per-runtime digest. That state
remains immutable evidence under `vgg16_54_seed_20261018_r1` and must never be used as the first
leg of the governed two-runtime smoke.

## Append-only correction

- Require the exact device name `NVIDIA L4` before entering the original training runner.
- Derive a privacy-preserving runtime digest from a package-specific tag and Linux boot ID by
  reusing the already tested D1 runtime-identity implementation.
- Persist the identity schema/digest, GPU name, CUDA version, device count, compute capability,
  total memory, run-binding SHA and checkpoint-binding SHA in the ATTEMPT. The shared event writer
  copies the ATTEMPT into text log, SQLite and `colab_execution.json`.
- Before resume, validate the complete fresh ATTEMPT and reject an identical runtime digest.
- Before a long run, require the current runtime to match the independently reviewed epoch-2
  resume runtime.
- Use the isolated successor state
  `M1_D1_Colab/runs/vgg16_54_seed_20261018_r2`; never rewrite R1.
- Continue to require the original Owner approval and source-QA proof, plus a new exact source-QA
  proof for the append-only successor bytes.

No sealed-test route is introduced. No claim about model quality is made by this source package.
