# YOLO11n dual-track R1 — independent notebook and bundle QA

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Scope: immutable-commit N54/N1 fresh/resume smoke notebooks and train/validation bundles  
Verdict: **PASS**

## Boundary

This was an independent read-only static/pre-execution review. It did not edit the reviewed files,
upload data, start Colab, train a model, commit, push or access the sealed test. The PASS authorizes
the Owner-approved private upload and the two smoke legs only: fresh through epoch 1, then resume
on a genuinely new NVIDIA L4 through epoch 2. It does not authorize either 100-epoch long run.

## Immutable bindings

- Remote source branch: `codex/yolo11n-dual-track-r1`.
- Immutable source commit: `45b7b1fab606032fcfb2956d0207171ae8b4c7f6`.
- Source independent-QA record SHA-256:
  `bcf7470d931d23445785c1103e3c919aca4c696b22738079756572892ce4f632`.
- Official `yolo11n.pt` SHA-256:
  `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.

Reviewed notebook source pins:

| File | SHA-256 |
| --- | --- |
| `scripts/build_yolo11n_dual_track_r1_notebooks.py` | `2ea86527893905791d0e1de35a31999f56bab23b6cdeec9311384b7e94c104f6` |
| `tests/test_yolo11n_dual_track_r1_notebooks.py` | `37f4e332bccac0e1c56c6642c487aab0e3c2cb167f10adaa7352fda042318b8a` |
| `detector/colab/yolo11n_n54_r1_fresh.ipynb` | `5d008c1405e458cf2799d1634cfe8dfe1933059ea452f8b9f622218dfff9454e` |
| `detector/colab/yolo11n_n54_r1_resume.ipynb` | `86dee6f2014cc7ef6e5f527a3b811b7e412fdce20cc024555e5acbfeda4e0ff2` |
| `detector/colab/yolo11n_n1_r1_fresh.ipynb` | `ddb4d1af3cd46f171ce550b82b423d1bc3dfded054d8de63456fb807d00952a9` |
| `detector/colab/yolo11n_n1_r1_resume.ipynb` | `a9a5cc3f2a9f68da3a5968800b2598f06514fc50b957a96f14753a6314b50b4c` |

## Bundle verification

### N54

- Reconstructed archive SHA-256:
  `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`.
- Sidecar SHA-256:
  `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2`.
- All eight Drive parts match their exact sizes and hashes and concatenate to the archive above.
- The archive has 5,888 regular payload members and contains only the governed train/validation
  inputs; no sealed-test path is present.

### N1

- Archive SHA-256:
  `5798ad93f552e1f7c36b46a3470fc9f8f85c5125df753786d63e228822299d05`.
- Embedded manifest SHA-256:
  `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`.
- The archive has 8,579 regular payload members, no test path, exact `yolo11n.pt`, no
  `yolo11s.pt`, `test_included=false` and `sealed_test_accessed=false`.
- Actual extracted-root `check` returned train `3,712` images / `12,621` boxes and validation
  `376` images / `624` boxes with `sealed_test_accessed=false`.

## Findings and remediation readback

The first review found three pre-execution blockers, all remediated before this PASS:

1. N54 initially expected a single Drive archive even though the private Drive holds the verified
   eight-part representation. The notebook now verifies and reconstructs those exact parts.
2. N1 initially looked for the source-QA record inside a bundle that does not contain it. It now
   reads the exact record from the clean immutable Git checkout.
3. N1 initially created its virtual environment under the extracted bundle and checked runtime
   uniqueness only after training. It now installs/runs from the immutable Git checkout, preserves
   the extracted input roster, and rejects a same-runtime resume before dependency sync or training.

Final checks independently passed:

- exact NVIDIA L4 preflight and clean detached checkout;
- fresh epoch 1 / resume epoch 2 boundaries and distinct-runtime enforcement;
- deterministic notebook regeneration and compilation of all 24 unexecuted code cells;
- targeted Ruff, three notebook tests, Graft freshness and lock validation;
- absence of `export-test`, `--final-eval`, test payloads and any sealed-test route.

## Authorized next gate

Upload the four notebooks, this QA record and the N1 train/validation bundle to the Owner's private
Drive. Then execute one track at a time: fresh epoch 1 on an NVIDIA L4, disconnect/delete that
runtime, and resume epoch 2 on a genuinely new NVIDIA L4. Submit the resulting state artifacts to
independent smoke artifact QA. Long training remains blocked until that artifact QA passes.
