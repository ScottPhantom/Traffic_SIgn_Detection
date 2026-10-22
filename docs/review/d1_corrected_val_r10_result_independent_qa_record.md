# D1 corrected-validation R10 result independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_RESULT_QA_PASS`  
Reviewer: `Codex fresh independent artifact-and-report QA session`  
Boundary: `RESULT_ARTIFACT_AND_REPORT_ONLY_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST`

## Verdict

**PASS — the immutable R10 corrected-validation artifact and its evaluation report are mutually
consistent, arithmetically correct, and accurately bounded as a single-seed validation NO-GO.**

No Critical, High, Medium or Low result/report finding was found. This decision accepts only the
observed R10 validation artifact as the corrected single-seed baseline. It does not authorize more
training, the two remaining seeds, sealed-test access, final model acceptance, deployment or any
safety claim.

`test_included=false` and `sealed_test_accessed=false` in the R10 result, its data authority and its
private-snapshot roster. No sealed-test file was opened during this review.

## Immutable reviewed inputs

| Input | SHA-256 | Other observed authority |
| --- | --- | --- |
| `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/eval_val_wp38_r1_r4_r10.json` | `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5` | 168005 bytes, mode `0400`, link count 1 |
| `docs/review/d1_corrected_val_r10_evaluation_report.md` | `a66dbf8a963fbfaa64d0de317cbe97e14264b60bc6c0b0f28bac399e2b15bb6c` | exact report reviewed |
| `docs/review/d1_corrected_val_r10_independent_qa_record.md` | `7cd42e9263f01fd9adf1e8456f3d8c384c3e21c83725caae552d9ea40c4ada8e` | pinned R10 source-QA PASS; not re-adjudicated here |
| original `eval_val.json` | `e6fe9eb58e4d06e3815d94be477f5b450625042c25b08995c1217ffd26dc8895` | comparison authority for reported deltas |

## Artifact binding and publication checks

The live R10 pathname was opened read-only and independently hashed and stated. Its reconstructed
binding was:

```text
content_uri=sha256:b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5
sha256=b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5
size=168005
device=16777230
inode=120231919
mode=0400
nlink=1
```

The content URI, digest, byte count, mode and link count exactly match the evaluation report. The
result JSON is the consumed payload rather than a self-embedded `ReportBinding`; the binding above
was therefore recomputed from the published file, not trusted from a field inside that file.

The artifact's private-snapshot roster has 754 sorted records and recomputes exactly to its stored
SHA-256 `03baa63f4fb10f7ce3c9134c93df6e75ccf1cc6fcb47a877e3394ce98fa812b9`
using canonical compact, sorted-key JSON. Its use-time declaration binds the consumer to
`exclusive_private_snapshot`, records `source_hashes_verified_before_consumer=true` and
`snapshot_destroyed_after_evaluation=true`, and repeats the same roster digest.

The retained current sources were independently compared to the roster. `best.pt` and all 752
validation image/label records match their roster digest and size. The remaining roster entry is
the evaluation-private `data.yaml`, which is deliberately generated with the destroyed private
snapshot root and is therefore not byte-identical to the persistent integration `data.yaml`; this
is the specified `_build_private_snapshot()` behavior, not an authority mismatch.

## Weight and corrected-data authority

- The result binds seed `20261018`, the registered pilot run, and `best.pt` SHA-256
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`.
  The live weight file has that digest. The run contract digest is
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`, and the
  run-registry digest is
  `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`; both
  match the result and the registry entry binds the same seed and best-weight digest.
- The result pins the WP38-R1 integration R4 exporter, manifest and independent QA record to
  `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426`,
  `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` and
  `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591`.
  All three live files match those digests.
- The pinned integration manifest states validation `376` frames / `560` boxes / `19` classes,
  with exactly `39` frames / `29` boxes from group `D02-C0034` corrected `CCW_90` and
  `raw_mutated=false`. It also states `test_included=false`, `sealed_test_accessed=false` and
  `training_authorized=false`. These values match the result and evaluation report.

## Metrics, gates and arithmetic

The R10 result contains `status=CORRECTED_VALIDATION_COMPLETE`, `split=val`, seed `20261018`, and a
single `960x540` resolution bucket covering all 376 frames and 560 ground-truth boxes.

| Quantity | Stored evidence | Independent arithmetic/report check |
| --- | ---: | --- |
| mAP50 | 0.8689176985300303 | report 0.868918; D-05 single-seed check PASS |
| mAP50-95 | 0.6253165213036037 | report 0.625317; check PASS |
| detection recall | 0.862500 | `483 / 560 = 0.862500`; check PASS |
| FP/image | 0.5691489361702128 | `214 / 376 = 0.5691489361702128`; check **FAIL** against 0.30 |
| precision | 0.6929698708751794 | `483 / (483 + 214) = 0.6929698708751794` |
| confidence | 0.20 | matches report |
| unknown false-recognition | 4 / 10 = 0.40 | matches report |

The 19 observed class supports sum to 560. The result and report agree that supported critical
classes 7 (`66/111 = 0.594595`), 32 (`18/29 = 0.620690`) and 41
(`12/21 = 0.571429`) fail the 0.70 requirement. Supported non-critical gated classes 6, 8, 10,
12, 34 and 46 pass. Ten observed classes have support below 20, and 35 classes have no validation
support and remain unverified. The artifact records `single_seed_checks_passed=false` and
`final_verdict=null`, correctly separating this validation decision from a final D-05 verdict.

## Comparison with the original validation artifact

All changes printed in the evaluation report reproduce from the two immutable JSON artifacts:

| Metric | Original | Corrected R10 | Exact computed delta | Reported rounded delta |
| --- | ---: | ---: | ---: | ---: |
| mAP50 | 0.8292039144342593 | 0.8689176985300303 | +0.039713784095770976 | +0.039714 |
| mAP50-95 | 0.5888191737174719 | 0.6253165213036037 | +0.03649734758613177 | +0.036497 |
| detection recall | 0.8571428571428571 | 0.8625000000000000 | +0.005357142857142949 | +0.005357 |
| FP/image | 0.5505319148936170 | 0.5691489361702128 | +0.018617021276595813 | +0.018617, worse |
| precision | 0.6986899563318777 | 0.6929698708751794 | -0.005720085456698332 | -0.005720 |
| unknown recognized as known | 6 / 10 | 4 / 10 | -2 recognitions | -2 recognitions |

The original resolution evidence is also reported accurately: its 39 `540x960` frames contain 29
boxes, 7 true positives, recall `0.2413793103448276`, 37 false positives and FP/image
`0.9487179487179487`; the remaining 337 frames are `960x540`. R10 has only one `960x540` bucket
after the governed correction. The report appropriately warns that the selected confidence also
changed from 0.15 to 0.20, so class hit-count changes are not attributed solely to rotation.

## Report disposition review

The report accurately labels the result
`CORRECTED_VALIDATION_COMPLETE_SINGLE_SEED_NO_GO`: aggregate AP and recall pass, but FP/image and
three supported critical-class recalls fail. Its next-step language is appropriately fail-closed:
preserve the baseline, do not open sealed test, do not launch seeds `20261019` and `20261020` under
the unchanged configuration, prepare validation-only error analysis and a new QA-passed experiment
contract, and retain the Owner/governance boundary for any future training. It makes no training,
test, deployment or safety authorization.

## Commands and evidence

Read-only commands used in this review included:

```text
graft check .
graft ask "Locate the R10 corrected-validation result/report authority..." --source .
graft ask "In corrected validation R4-R10, how is the private snapshot data.yaml produced..." --source .
shasum -a 256 <R10 JSON> <evaluation report> <R10 source-QA record> <original eval_val.json>
stat -f '%z %Sp %l %i %d' <R10 JSON>
jq <targeted authority, metric, gate, class and resolution fields> <R10 JSON>
jq <targeted metric and resolution fields> <original eval_val.json>
jq <orientation_correction, splits and policy fields> <integration R4 manifest>
uv run python - <<'PY'  # read-only hash, stat, roster, arithmetic and delta checks
PY
```

Observed results: Graft freshness `OK`; all supplied pins matched; binding/stat fields matched;
weight/run/data authority pins matched; snapshot roster digest matched; every arithmetic and rounded
delta check matched; class support/gate lists matched; test and sealed flags remained false. No
model inference, evaluation rerun, training, upload, commit, push or sealed-test access occurred.

## Bounded disposition

| Action | Result-QA disposition |
| --- | --- |
| Preserve the R10 JSON and evaluation report as immutable evidence | **YES** |
| Accept R10 as the corrected single-seed validation baseline | **YES** |
| Treat this as a passing final candidate or final D-05 result | **NO-GO** |
| Start unchanged seeds `20261019` / `20261020` | **NO-GO** |
| Prepare validation-only error analysis and a separately governed improvement contract | **YES** |
| Train/retrain without the existing Owner authorization and QA gate | **NO-GO** |
| Access or export sealed test | **NO-GO** |
| Deploy or make a safety claim | **NO-GO** |

