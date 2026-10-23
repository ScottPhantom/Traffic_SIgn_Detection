# D1/CenterCam app R1 — independent QA

Date: 2026-10-23 (Asia/Ho_Chi_Minh)
Reviewer: independent Codex QA session `/root/qa_d1_centercam_app`
Verdict: **PASS for app integration and image-region contract**.
Findings: 0 Critical, 0 High, 0 Medium, 1 Low (cosmetic inherited scene issue).

## Exact reviewed inputs

| File | SHA-256 |
| --- | --- |
| src/cpv301_autodrive/centercam.py | 93c7a58c03288866b4fe573d8d38d3e20fbd746ea896ca72e56b9748ee9c722b |
| src/cpv301_autodrive/detector_d1.py | ec3c93a2721331a2958b0354a03daf051f4dcefc20c3498b4652659013119775 |
| src/cpv301_autodrive/views.py | 71f265b2b2cb3219fa790e04500cc77e1c541cc5d242aca2e45f698e08e8ed6e |
| tests/test_centercam.py | f79955fe706b16b6141809b4f390aec5d9fe7aa7e0cc2cbbf16e482a57cdc0aa |
| tests/test_detector_d1.py | d8fbc3c085243c24bcdafce5d897f42494ba0b94aa775bf6df6cb170b909c536 |
| docs/review/d1_centercam_app_r1_implementation_record.md | 0d211163a4f951b7ba32361d49e9afc40937db1605c520b03ecfa3681c919f65 |

The reviewer did not edit implementation or tests. Existing unrelated work was left intact.

## Independently reproduced checks

- `uv run pytest -q tests/test_centercam.py tests/test_detector_d1.py tests/test_web_app.py`:
  exit 0, all 60 cases passed on final source. This includes actual registered-checkpoint sample
  inference, AppTest navigation, empty/error UI, EXIF transformation, invalid-image plugin-error
  normalization, cached prediction reuse, geometry clipping and failed-class simulation guards.
- Scoped Ruff, root `uv lock --check`, and `git diff --check`: PASS.
- Additional reviewer-only checks: all 25 distinct unsupported/validation-failed class keys leave
  action/speed/steering unchanged; left/middle/right survives landscape/portrait/resizing across
  six frame sizes; RGB/RGBA/grayscale upload conversion is RGB; tiny-image road estimation declines
  normally. PASS.
- Shared-model concurrency attack: 20 calls through eight threads produced maximum simultaneous
  `model.predict` calls of one. PASS. The cache stores primitive values, avoiding class-instance
  pickle identities after a library reload.
- Exact-third middle boundaries and per-detection numbering are consistent across the annotated
  image, detection table, scene table and SVG. Image regions are independent of optional road
  heading. Same-pole grouping cannot change a region across a third boundary.
- Registered weights and class-map hashes are checked before use. Nonfinite/invalid classes,
  scores or boxes are dropped, clipping precedes geometry validation, and numbering follows the
  retained descending-confidence list. Classes 7/32/41 and 22 unsupported classes are display-only.
- Autoinstall/offline guards are set before Ultralytics load and for an already loaded checks
  module; the actual-checkpoint test verifies those checks flags are disabled.

## Browser evidence boundary

The implementation session performed the live browser interactions at
`http://127.0.0.1:8599/demo`; this reviewer did not drive that browser. The reviewer read the
author's exact evidence record, independently verified all four screenshot hashes, and visually
inspected `demo_final.jpg` and `invalid_upload_fixed.jpg`. Those show the four indexed detections
and region table, and the final normal corrupt-image error without a traceback respectively.
Other browser interactions (sample/upload1951, road overlay, zero detections, E0/D1 switching)
remain explicitly author-observed, supported by the pinned record and scoped tests.

| Local screenshot | SHA-256 |
| --- | --- |
| tmp/d1_centercam_app_r1/demo_final.jpg | b102d04c60acd17237c09c8e14b1e87e2d1acdf24e44b38ca194e7a97c75ee69 |
| tmp/d1_centercam_app_r1/upload_1951.jpg | f9d0da3aac21095ee25011a15246ba8e6db4ed18d31eb3515234fe10acf613ad |
| tmp/d1_centercam_app_r1/no_detection.jpg | abae01d626da1bce37bc4b7873904d2c21252462a932ecb3b3858d9c461e4651 |
| tmp/d1_centercam_app_r1/invalid_upload_fixed.jpg | 18ed655dd7131d4034698c636241e9a5a38c1a6daf36b25d9da9864b95eeb7a3 |

## Low finding and limits

**L1 (nonblocking):** `scene_svg` uses `places[place.pole_of or index].r` to calculate the drawn
pole endpoint. A shared pole whose parent index is zero uses the child's radius, because zero is
false. Unequal-sized adjacent signs can therefore have a slightly inconsistent pole length. It
does not change ID, image region, box, classification or simulation command. A future cosmetic
fix should explicitly test `pole_of is not None` and include a different-radius parent-zero case.

The full-root parallel test run was still pending when this scoped verdict was written; no
whole-repository PASS or historical-verifier PASS is claimed here. Final Graft freshness was
STALE after final source fixes; the implementation session must rebuild/check before handoff.

This verdict accepts the app functionality only. Road heading/depth are visual estimates, and
image side does not establish lane applicability. The model's validation/D-05 disposition remains
unchanged. No new training, sealed-test access, commit, push, cloud upload or dependency edit was
performed by this QA session.

## Closure readback

After the implementation session rebuilt Graft, this reviewer reran `graft check .`: exit 0,
graph OK/in sync, 4,237 nodes. The earlier freshness item above is closed. Source/test/report pins
remain those listed above; the full-root suite limitation still applies to this scoped verdict.
