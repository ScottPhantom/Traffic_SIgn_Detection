# D1 corrected validation R9 — live execution failure record

Date: 2026-10-22 15:56 +07:00  
Status: `FAILED_CLOSED_AFTER_INFERENCE`

## Scope

R9 was run once against the registered pilot checkpoint after its independent source QA PASS:

```text
results/experiments/
  D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/
  weights/best.pt
```

The checkpoint SHA-256 was reverified as
`5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` before execution.

## Observed failure

Ultralytics completed validation inference over 376 images and 560 instances on Apple M1 Pro MPS.
The process then exited non-zero with:

```text
{"status": "FAILED", "error": "corrected-validation consumed document differs from intended payload"}
```

The fail-closed report is a regular single-link mode-`0400` file:

```text
eval_val_wp38_r1_r4_r9.json
bytes: 168005
sha256: 92f45c8ef6bf1fde4b9e48e932fb9da95127c06132057e56e3fab7ea3e70ff5b
```

Readback confirmed `test_included=false` and `sealed_test_accessed=false`. The file contains the
preview values `mAP50=0.8689176985300303` and `mAP50-95=0.6253165213036037`, but the R9 command
failed and therefore these are **not accepted corrected-validation results**.

## Cause and disposition

R9 correctly proved that the descriptor-consumed raw bytes equal the independently computed
canonical intended bytes. Its additional comparison incorrectly compared the parsed JSON document
against the pre-serialization Python object. Valid JSON normalization can change tuple to list and
non-string object keys to strings, making those objects unequal without any byte or semantic
substitution.

R9 remains immutable. An append-only R10 must compare the consumed document with
`json.loads(canonical_intended_bytes)` while retaining the exact raw-byte, binding, descriptor,
sealed-test and validation-only checks. The failed R9 artifact is preserved and must not be
overwritten or promoted as a successful evaluation.
