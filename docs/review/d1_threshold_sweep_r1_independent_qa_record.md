# D1 threshold sweep R1 — independent result QA

Date: 2026-11-06 (Asia/Ho_Chi_Minh)
Reviewer: separate Codex agent; did not author the sweep script or generate its result artifacts.
Verdict: PASS — validation-only diagnostic package; no threshold is locked.

## Reviewed artifact binding

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/threshold_sweep_r1.py` | `d40d7ffb573ea1592c4c0c4853a1b741773c1729530db4bf9ff88c5ccc176825` |
| `detector/tests/test_threshold_sweep_r1.py` | `d2bbb49e0594002f158e4cd33318df0cfd8ebdbb7c124711b39fa08e911a599a` |
| `docs/review/generated/d1_threshold_sweep_r1.json` | `b7d14488597cfbc63f2a5550a086e51a584d222ba33bd0b48eb6415baef875fb` |
| `docs/review/generated/d1_threshold_sweep_r1.csv` | `4fa19319c093b1442f59f6b63e2eb9f227fd7601e88f59768ea505e2becd2fda` |
| `docs/review/d1_threshold_sweep_r1_report.md` | `9ba04b49706f8bda4952560501259e1210d132cfeb43455ca075ab950d28e660` |

The 11 SVG SHA-256 values are listed below. All input prediction, result, QA, scorer and R3 bundle hashes were checked by the package's `verify` command; the source contains only previously saved, pinned validation predictions. The pilot curve is read from the QA-passed NMS R1 `classaware_0.70` cells, SHA-256 `6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057`. The R3 roster has 376 images, 624 GT boxes, and 9 D-02 groups. No seed-20261019/S2 path appears in the script's input specification.

## Independent recalculation

I read the pinned pilot CSV in `tmp/yolo11n_n1_extract_r2` (SHA-256 `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893`) and the A2 prediction CSV (SHA-256 `c45dcf1dd5446b7e5afe3458afcd43f75b8b7b5afc5434d244d80a0e3e1dd7f1`). I rebuilt GT boxes from the 376 validation label files and image dimensions. A separate greedy matcher sorted predictions by descending score, matched IoU ≥ 0.5, and counted class-agnostic TP/FP and correct-class hits. It did not call `m1.metrics.operating_point` or the new sweep's `point` function.

| Model | Confidence | Independently derived TP / FP / correct-class hits | Published JSON |
| --- | ---: | ---: | ---: |
| Pilot | 0.05 | 588 / 306 / 503 | 588 / 306 / 503 |
| Pilot | 0.20 | 547 / 150 / 457 | 547 / 150 / 457 |
| Pilot | 0.50 | 421 / 74 / 355 | 421 / 74 / 355 |
| A2 | 0.05 | 529 / 213 / 449 | 529 / 213 / 449 |
| A2 | 0.20 | 475 / 92 / 406 | 475 / 92 / 406 |
| A2 | 0.50 | 380 / 46 / 347 | 380 / 46 / 347 |

The pilot and A2 0.20 anchors match their QA references. I also checked all 200 JSON cells for recall, precision and FP-per-image arithmetic; the derived-key mapping is 7→7, 32→33, 41→42. Diagnostic selections satisfy the stated recall-first, minimum-FP rule, with explicit `NO_POINT_MEETS_RECALL_0_85` for A2. All 30 report interpolations at FP/image 0.20, 0.25 and 0.30, both selection-table values and marker calls match JSON after rounding.

## CSV, SVG and execution checks

The CSV has exactly 200 rows, one for every model and confidence point, and its numeric cells match JSON. I parsed all 11 SVGs as XML and checked `viewBox="0 0 1100 520"`, Vietnamese `aria-label`, text size ≥22 px and size <50 KB. All model recall/FP polyline coordinates and selected-point markers reproduce the JSON within 0.051 px rounding; the tradeoff figure's ten named curves do likewise. Plot mappings reach x=40–1080 and y=20–500. The SVGs were checked structurally and numerically, not through a rendered slide review.

| SVG suffix | SHA-256 |
| --- | --- |
| `n1_compact` | `6e6a43dc9d58a52c6b7d1842bc8bed97a2edcedd692d3e1d4ff21547f034c704` |
| `n1_compact_r2` | `17de9d501f97ff5546c9d99c1f045eceff6eb1533b75cfcd53799c2c78899c04` |
| `n1_vgg16_54` | `2bb83a2580abac054a924e36400a04139d6b93f42ddca686f1fdbeb20ed466c1` |
| `pilot_classifier_fusion` | `c2a8439b6437864d60997a9ab271d443fc6d74f822903037bc613fc25f86cac6` |
| `s1_compact_b0` | `39f3d84b4f9e33be64ea2b084edf7eb5665be039573a7b0957ca3899ae05932f` |
| `s1_compact_r2` | `5b39cec9593b721c20fa51b8f7e36305bd68a97d5c73c302a767a829a9af460c` |
| `s1_vgg16_54` | `585f93e7f61ec4060453340b2a3a77ae96929f2bb662820a38a940b4ef614962` |
| `tradeoff` | `3c1e791d7e062623f1a152257f3f6253857280abcb4eb670852b9ead359c3ca6` |
| `yolo11s_54_a2` | `baddc892738833d22a90940fc07c0761c5e51b323a11f9c3a47cee1cdb2332f2` |
| `yolo11s_54_a3` | `86e13f593d08b2d812a6dbfc2506b42c4a66fa5cf4251d7e29e9a1e0c92ae22a` |
| `yolo11s_54_pilot` | `42f0659389f01256f91ca0ba6092b561a7cf3e2024ce01c5fa4a2673c328d296` |

`PYTHONPATH=. uv run --no-sync pytest -q tests/test_threshold_sweep_r1.py`: 4 passed. Scoped Ruff on the script and test: all checks passed. `PYTHONPATH=. uv run --no-sync python -m m1.threshold_sweep_r1 verify`: `VERIFY PASS: 13 artifacts, sealed_test_accessed=false`. `graft build . && graft check .`: graph in sync.

## Boundary and limitations

This review read only validation R3 and existing prediction artifacts; it did not run model inference or training, open the sealed test, lock a threshold, alter the app, or read S2 predictions. The output flags say `sealed_test_accessed=false`, `thresholds_locked=false`, `model_inference_run=false` and `training_run=false`. These are descriptive single-seed validation curves, with linearly interpolated operating points at matched FP/image; they do not prove that a threshold or model generalizes, and the SVGs still need a deck-level visual inspection after insertion.
