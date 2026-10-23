# D1/CenterCam app R1 — implementation and browser evidence

Date: 2026-10-23 (Asia/Ho_Chi_Minh)
Status: IMPLEMENTED_AWAITING_INDEPENDENT_QA
Author: Codex implementation session; independent verdict belongs in a separate QA record.

## Scope and preserved work

Continues Claude's uncommitted `detector_d1.py`, `views.py`, `centercam.py` and detector tests
on top of HEAD `46e7b14`. Existing unrelated environment, dataset, evaluator and documentation
changes were preserved. No dependency file was changed. No model training, sealed DATASET01 test
access, commit, push or cloud upload was performed. Browser uploads below were to localhost only.

## Image-position contract

The box centre determines the image region: x < width/3 is trái, width/3 <= x <= 2*width/3 is
giữa, x > 2*width/3 is phải. Exact boundary centres belong to the middle. The same function drives
the detection table and illustrative scene. Positions use original displayed-image pixels;
uploads apply EXIF transpose before inference/display. Invalid/out-of-frame/non-finite or
zero-area boxes are rejected by the position API. Detector output is clipped to the frame and
invalid candidates are discarded before numbering. IDs follow descending confidence consistently
through annotation, both tables and scene. Same-pole grouping cannot overwrite an image region.

Road heading from Canny/Hough remains a separate optional overlay. It does not change the image
region or scene's region when enabled in the app. Image side is not lane applicability or a
physical measured roadside. The scene's near/far cue uses box height and is explicitly unmeasured.

## Detector and UI

- Registered best.pt and governed class map are hash checked. Settings remain 1280 px, class-wise
  NMS IoU 0.70, default confidence 0.20; user slider is demo-only.
- A shared cached detector serializes `predict()` with a lock. The bounded 16-entry data cache
  stores primitive (class id, confidence, xyxy) records keyed by image PNG bytes/confidence.
  A cruise-speed or road-overlay rerun reuses predictions. Primitive records avoid stale-class
  pickling failures after module reloads.
- Unsupported keys and validation-failing keys 7/32/41 are display-only. Remaining classes can
  illustrate a command; none is described as D-05 accepted. Table status distinguishes support,
  validation failure and simulation-only use.
- Missing/bad checkpoints, unavailable inference dependencies and model errors render errors.
  Corrupt uploads render a normal image error. EXIF orientation is retained in display coordinates.
- D1 explicitly disables Ultralytics automatic installation and offline checks before loading the
  checkpoint, including flags for an already imported checks module. During the first corrupt-file
  browser test, Ultralytics tried (and failed) to install optional pi-heif; no dependency was added.
  That path is now blocked. Missing HEIF ImportError is normalized to an invalid-image error.
- Caption cites VRE-R2/R3 validation: mAP50 0.884 and FP/image 0.399, with model-guided relabel bias
  and no D-05 acceptance. This app change does not improve or retrain the model.

## Exact implementation reviewed

| File | SHA-256 |
| --- | --- |
| src/cpv301_autodrive/centercam.py | 93c7a58c03288866b4fe573d8d38d3e20fbd746ea896ca72e56b9748ee9c722b |
| src/cpv301_autodrive/detector_d1.py | ec3c93a2721331a2958b0354a03daf051f4dcefc20c3498b4652659013119775 |
| src/cpv301_autodrive/views.py | 71f265b2b2cb3219fa790e04500cc77e1c541cc5d242aca2e45f698e08e8ed6e |
| tests/test_centercam.py | f79955fe706b16b6141809b4f390aec5d9fe7aa7e0cc2cbbf16e482a57cdc0aa |
| tests/test_detector_d1.py | d8fbc3c085243c24bcdafce5d897f42494ba0b94aa775bf6df6cb170b909c536 |

## Verification

Author scoped command:
`uv run pytest -q -o addopts='' tests/test_centercam.py tests/test_detector_d1.py tests/test_web_app.py`
returned **60 passed in 10.51s** on the final implementation. Cases include original-image geometry,
resize/portrait invariance, exact thirds, invalid boxes, clipping, class mapping, failed-class
simulation guard, actual sample inference, EXIF uploads, optional-plugin failure, empty/error UI,
cache reuse across cruise changes and multipage navigation.

`uv run ruff check src tests`, `uv lock --check` and `git diff --check` passed. Graft was rebuilt;
final freshness readback is required at handoff. Full root tests were moved from a slow serial
pytest run (interrupted; no full-pass claim) to `run_parallel_checks.py tests --jobs 6`; its result
will be reported separately. No old 61/61 verifier claim is promoted by this scoped app review.

## Actual browser observations (author, Codex in-app browser)

App: http://127.0.0.1:8599/demo, started locally and restarted after module edits.

1. Sample 1231, conf 0.20: four detections. Table IDs 1..4 correspond to R.415a (middle, 38.4%),
   P.111a+P.111b (left, 12.1%), P.130 (left, 12.4%), S.505a (middle, 38.6%). Duplicate-board note
   links #4 to #1. Scene and table preserve those region labels.
2. Sample 1951 and the same file uploaded through the localhost uploader: one P.127 detection,
   confidence 0.970, right region, x centre 80.9%. Class41 is display-only and cruise remains50.
3. Optional road overlay on 1951: estimated heading x234 px; image classification remains right.
   Sample1807 declines road estimation and still reports its box at58.9% as middle.
4. Sample1231 at confidence0.95: zero detections, normal empty message and continued cruise50.
5. Uploaded invalid.png after D1 had loaded: initial Ultralytics optional-plugin traceback found
   and fixed. Final fresh-server retest shows “Không thể đọc ảnh: File ảnh bị hỏng hoặc định dạng
   không được hỗ trợ.” with normal navigation and no traceback.
6. Switched D1 → E0 → D1: baseline uploader renders, then D1 returns to the working sample view.
   The final D1 tab is kept open as a deliverable.

Screenshots are local git-ignored evidence, never uploaded externally:

| Path | SHA-256 |
| --- | --- |
| tmp/d1_centercam_app_r1/demo_final.jpg | b102d04c60acd17237c09c8e14b1e87e2d1acdf24e44b38ca194e7a97c75ee69 |
| tmp/d1_centercam_app_r1/upload_1951.jpg | f9d0da3aac21095ee25011a15246ba8e6db4ed18d31eb3515234fe10acf613ad |
| tmp/d1_centercam_app_r1/no_detection.jpg | abae01d626da1bce37bc4b7873904d2c21252462a932ecb3b3858d9c461e4651 |
| tmp/d1_centercam_app_r1/invalid_upload_fixed.jpg | 18ed655dd7131d4034698c636241e9a5a38c1a6daf36b25d9da9864b95eeb7a3 |

The independent reviewer must distinguish author browser observations from independently run tests.
Acceptance here concerns app integration/image geometry only; D1 model acceptance stays NO-GO.
