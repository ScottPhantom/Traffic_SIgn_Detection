# D1 pilot — corrected validation R10 evaluation report

Date: 2026-10-22  
Status: `CORRECTED_VALIDATION_COMPLETE_SINGLE_SEED_NO_GO`

## Evaluated authorities

- Run: `D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2`
- Seed: `20261018`
- Weights: `best.pt`
- Weight SHA-256: `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`
- Corrected validation: WP38-R1 through QA-passed M1 integration R4
- Frames / boxes: 376 / 560
- Corrected frames / boxes: 39 / 29, `CCW_90`, raw data unchanged
- R10 report: `eval_val_wp38_r1_r4_r10.json`
- R10 report content authority:
  `sha256:b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5`
- Report size/mode/link count: 168005 bytes / `0400` / 1
- Test included: `false`
- Sealed test accessed: `false`

## Corrected-validation results

| Metric | Corrected R10 | D-05 single-seed check | Result |
| --- | ---: | ---: | --- |
| mAP50 | 0.868918 | >= 0.60 | PASS |
| mAP50-95 | 0.625317 | >= 0.40 | PASS |
| Detection recall | 0.862500 | >= 0.85 | PASS |
| FP / image | 0.569149 | <= 0.30 | **FAIL** |
| Precision at selected point | 0.692970 | diagnostic | — |
| Selected confidence | 0.20 | selected on validation | — |
| Unknown false-recognition | 4 / 10 = 0.40 | diagnostic | — |

The single-seed gate remains **NO-GO** because FP/image fails and supported critical classes fail.
This is validation evidence only, not a D-05 final verdict.

## Supported-class gate results

Critical classes with at least 20 validation boxes:

| Class | Support | Recall | Required | Result |
| --- | ---: | ---: | ---: | --- |
| 7 | 111 | 0.594595 | >= 0.70 | **FAIL** |
| 32 | 29 | 0.620690 | >= 0.70 | **FAIL** |
| 41 | 21 | 0.571429 | >= 0.70 | **FAIL** |

Non-critical gated classes 6, 8, 10, 12, 34 and 46 pass their recall requirement. Ten observed
classes have support below 20 and are reported without a gate. Thirty-five classes have no
validation support and remain unverified; the correction does not create evidence for them.

## Orientation-correction effect

The earlier validation artifact mixed 337 landscape `960x540` frames with 39 incorrectly oriented
`540x960` frames. Those 39 frames had recall 0.241379 and FP/image 0.948718. R10 evaluates all 376
frames as governed `960x540` images after the WP38-R1 correction.

| Metric | Original pilot val | Corrected R10 | Change |
| --- | ---: | ---: | ---: |
| mAP50 | 0.829204 | 0.868918 | +0.039714 |
| mAP50-95 | 0.588819 | 0.625317 | +0.036497 |
| Detection recall | 0.857143 | 0.862500 | +0.005357 |
| FP/image | 0.550532 | 0.569149 | +0.018617 (worse) |
| Precision | 0.698690 | 0.692970 | -0.005720 |
| Unknown false-recognition | 6/10 | 4/10 | -2 recognitions |

The correction materially improves aggregate AP and eliminates the invalid portrait slice, but it
does not resolve the operational false-positive problem or the critical-class recall failures.
Because the selected confidence changed from 0.15 to 0.20, class-level hit counts must be compared
as operating-point outcomes, not as a pure isolated measure of image rotation.

## Disposition and next gate

- Preserve this result as the corrected single-seed validation baseline.
- Do not open the sealed test.
- Do not start seeds `20261019` or `20261020` under the current unchanged configuration: repeating a
  configuration that already fails FP/image and three supported critical classes is not yet a
  justified final-candidate batch.
- Before any retraining, prepare a validation-only error-analysis and improvement decision packet
  focused on FP sources and classes 7, 32 and 41. Candidate changes must be frozen in a new
  experiment contract and independently QA-passed.
- A new training run still requires the existing governance/Owner authorization boundary; this
  report alone does not authorize training, test access, deployment or safety claims.
