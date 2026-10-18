# Project Memory — CPV301 AutoDrive

Last updated: 2026-10-18 (Asia/Ho_Chi_Minh)
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`  
Role: PM — Project Management and Structure

This file is the compact, durable entry point for future Codex sessions. It records current facts,
decisions, risks, and routing. Detailed evidence stays in the canonical documents linked below so
this file does not become a second, drifting specification.

## Authority and evidence order

When sources disagree, use this order:

1. Current checkout code, tests, artifact readback, and task-specific Graft query.
2. Canonical project documents listed in this file.
3. Current PM handoff notes.
4. Older thread summaries or paths from the former iCloud checkout.

Always distinguish current verification from historical evidence. A green unit test proves only
the behavior it exercises; a local MVP, notebook output, or high confidence score does not prove
Vietnamese-domain accuracy, open-set recognition, full-scene detection, or safe control.

## Mission and present boundary

The long-term product is a local simulation in which a camera pipeline recognizes traffic signs,
maintains vehicle state, and visualizes the simulated response. The intended end-to-end pipeline is:

```text
camera/frame
  -> detector finds traffic-sign ROI
  -> classifier labels ROI
  -> temporal voting/tracking
  -> behavior planner
  -> lane/vehicle simulator
  -> Streamlit dashboard
```

The product runtime still contains only the cropped-image classifier and a simulated behavior/UI
shell. An M1 detector training package now exists in the separate `detector/` project, but no VN
detector checkpoint has been trained or accepted. Detector runtime integration, temporal
voting/tracking, lane/PID, and CARLA integration remain roadmap work.

## Current implementation map

| Area | Current module/entry point | Verified status |
| --- | --- | --- |
| Configuration | `src/cpv301_autodrive/config.py` | Settings include model path and demo confidence threshold. |
| Labels | `src/cpv301_autodrive/labels.py` | GTSRB 43-class label mapping. |
| Inference | `src/cpv301_autodrive/inference.py` | RGB 32x32 preprocessing, model loading, Softmax prediction, threshold-based `accepted`. |
| API | `src/cpv301_autodrive/api.py` | Health endpoint and cropped-image prediction path. |
| Launcher | `main.py` | Root one-command launcher; delegates to `scripts/run-web.sh` so UV sync and the existing Streamlit CLI remain the single startup flow. |
| CLI | `src/cpv301_autodrive/cli.py` | Info, serve, predict, evaluate, and web entry points. |
| Evaluation | `src/cpv301_autodrive/evaluation.py` | GTSRB split loading, classifier metrics/artifacts, and calibration-error calculation. |
| Behavior | `src/cpv301_autodrive/behavior.py` | Maps a `Prediction` to a simulated `VehicleCommand`; it is not real control. |
| Web UI | `src/cpv301_autodrive/web_app.py` | Streamlit app with three lazy tabs (`st.tabs(key="main_view", on_change="rerun")`): "Tiến độ dự án" (default; Gate 0, D-01…D-05, M0…M6 from `project_status.py`, which mirrors the roadmap and must be updated with it), "DATASET01" (pipeline animation, graph with D-02 groups, class and group tables via `dataset01_view.py`) and "Mô phỏng (baseline E0)" (cropped-image/webcam classification, history, simulated road; its sidebar settings render only in this tab). |
| DATASET01 view | `src/cpv301_autodrive/dataset01_view.py` + `assets/dataset01_graph.html`, `assets/dataset01_pipeline.html` | Streamlit tab "DATASET01" with four sections: 8-step animated pipeline (frames → proxy edges → review → WP32 cross-block → 54 D-02 groups → D-03/WP33 relabel → 4 D-04 buckets → WP35 enrichment), graph (vendor split, D-02 group colour mode), class table/chart and group table/chart. Wraps the pinned `dataset_graph.py` without changing it. |
| Dataset graph | `src/cpv301_autodrive/dataset_graph.py` + `assets/dataset_graph.html` | Read-only payload from the WP1 inventory, WP5 edge CSV and edge/sequence overlay annotations; fails closed on overlapping overlays or unknown outcomes. `EDGE_OVERLAYS` is a hand-maintained list: add each new edge WP (and flip `qa_passed` after independent QA). WP28-R2/WP29 are shown as awaiting QA. |
| Tests | `tests/` | Inference, API, evaluation, behavior, and initial web rendering coverage. |

For exact callers, callees, spans, and function interactions, query Graft rather than relying on
this prose map.

## Verified current state

- Environment: one standard project `.venv/`, managed from `pyproject.toml` and `uv.lock`.
- Python constraint: `>=3.12,<3.13`; local model loading uses TensorFlow 2.20.
- Model artifact: `models/VGG16_model.h5`; RGB input `(None, 32, 32, 3)`, 43-way Softmax output.
- Architecture evidence: VGG-inspired sequential CNN, not `keras.applications.VGG16`.
- Full GTSRB test evaluation: 12,630 images, accuracy `0.8682`, macro-F1 `0.7921`, weighted-F1
  `0.8705`, balanced accuracy `0.7949`.
- Error evidence: 1,665 wrong predictions, including 324 errors at confidence at least `0.90`.
- Training defect: `horizontal_flip=True` can invert directional signs while preserving the label.
- Domain decision: NO-GO for Vietnamese traffic deployment and real vehicle control.
- Current demo threshold: `0.50`; validation calibration and UNKNOWN/OOD evaluation are unfinished.
- Current baseline artifacts and provenance must be preserved; a corrected retrain must use a new
  artifact name rather than overwriting the baseline.
- Git is initialized and has history. Readback 2026-10-10: branch `DEV/Rroject_Pineline`,
  HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1`, tracking
  `origin/DEV/Rroject_Pineline`; remote is
  `https://github.com/ScottPhantom/Traffic_SIgn_Detection.git`. Re-read before repository
  actions because branch/remote state is time-sensitive.
- The planning DOCX, Slides PPTX and three papers are absent because the user intentionally deleted
  them. Their absence is expected; do not restore, investigate, or treat it as a blocker.
- Graft was rebuilt after M0-WP27-R2 on 2026-10-16: 78 Python files and 1,477 nodes; graph check
  is in sync and the R2 verify blast radius is limited to its CLI `main`. The optional deep meaning layer is not built.
- Candidate DATASET01 archive was audited read-only on 2026-10-10: SHA-256
  `052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76`, ZIP integrity pass,
  3,216 JPG + 3,216 YOLO labels, 52 observed classes and 8,334 boxes.
- The existing DATASET01 extraction is incomplete (1,046 images vs 3,216 labels). It contains
  25 empty-label negatives, severe imbalance (3 to 1,071 boxes/class), no validation split, and
  1,031/3,178 consecutive numeric filename pairs crossing train/test (32.44% leakage proxy).
- DATASET01 source candidate is identified by exact remote/local hashes; license version, original
  image ownership, physical-sign/video/scene groups and approved GTSRB↔Vietnam taxonomy remain
  unresolved. Training stays blocked until Gate 0 in `docs/product_roadmap.md` passes.
- M0-WP1 immutable staging now exists at
  `.../DATASET01/staging/052bc980a7206f8d/`. Audit verified 6,437/6,437 raw ZIP members
  byte-identical, 3,216/3,216 image-label pairing, 100% image decode, 52 classes, 8,334 boxes
  and 25 empty-label negatives. Technical audit PASS does not authorize training.
- Source preservation proof reports `unchanged=true`: archive hash/size/mtime and the old
  `archive/` tree hash `05c9955d77862f08f2a43436d9cdea63caa1cb3e56b939000737f93a248c753b`
  match before/after staging.
- Exact local/remote hashes identify Hugging Face
  `thanhhiepvos/vietnam_traffic_sign@d869116` as the source candidate. License remains BLOCKED:
  repository metadata says CC-BY-SA 3.0 while card prose says CC-BY-SA 4.0.
- `docs/vietnam_taxonomy_mapping.md` is a 52-class DRAFT with support/mapping proposals;
  it is not approved. No final `group_id` or group-aware split has been created.
- M0-WP1 fail-closed audit regression suite has 14 passing tests: raw/ZIP mismatch, corrupt image,
  invalid YOLO variants, bbox boundary warning/no-clamp, source mutation, normalization
  idempotency/refuse-overwrite and manifest tamper detection.
- M0-WP2 decision packet is **QA PASS / DECISION-READY** at
  `docs/review/m0_wp2_decision_packet.md`. Milestone `QA-M0-WP2-R2` reviewed HEAD
  `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` with an uncommitted worktree and reported
  `0 blockers`. This PASS approves only the WP2 decision packet; in that hash-pinned WP2 snapshot,
  D-01…D-05 and G0.4 bbox 0248 remain `PENDING`. WP10 now supersedes G0.4 by append-only overlay;
  Gate 0 remains BLOCKED and `training_authorized=false`.
- WP2 grouping evidence is explicitly `PROXY_ONLY`: 1,691 strong candidate edges, 1,172 uncertain
  edges, 315 adjacency-only edges and 589 candidate sequences containing 2,280 images. These are
  reviewer queue IDs, not video/scene/physical-sign group truth or final `group_id` values.
- WP2 has a 52-row taxonomy reviewer CSV, 52-row rare-class risk table and bbox 0248 overlay. The
  bbox line-1 geometry is x-max `978.00048 px` on a 960 px image (`18.00048 px` right overflow);
  raw image and label remain unchanged.
- D-04 now has 20 class-keyed records for the verified `box_count < 50` scope. Every record has
  independent disposition/status/reviewer/time/rationale/evidence/history fields and is currently
  `PENDING` with a null option. The aggregate cannot resolve until every in-scope class resolves.
  RESOLVED records fail closed on blank/untrimmed reviewer or rationale, invalid/missing-timezone
  timestamps, invalid/blank evidence references and malformed history; history uses a concrete
  previous-state snapshot plus change actor/time, with runtime-enforced strict append order.
- WP2 taxonomy/rare builders now reject duplicate, missing or extra class IDs and incomplete
  support sources unless the unique set is exactly `0..51`.
- M0-WP3 reviewer evidence is **QA PASS** at
  `docs/review/wp3_provenance_and_fallback_report.md`. It retains exact primary-source URLs,
  revisions, retrieval time and snapshot hashes; the Kaggle relation and every fallback remain
  `CANDIDATE`, while licensor authority, image ownership and capture/group lineage remain
  `UNKNOWN`. The outreach file is explicitly `DRAFT — NOT SENT`. Milestone `QA-M0-WP3-R1`
  reviewed HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` on an uncommitted worktree and
  reported `0 blockers`. This PASS approves only the WP3 evidence/reviewer package; it does not
  approve any dataset, license, taxonomy, group ID, split, model or experiment.
- The deterministic WP3 generator produced 24 proxy-only grouping contact sheets for all 589 WP2
  sequences and 13 bbox-overlay taxonomy pages covering class IDs `0..51`. Every grouping record
  is `PROXY_ONLY_NOT_GROUP_TRUTH`; every taxonomy row is `UNAPPROVED`. Text now wraps without
  truncation; the layout audit covers all 589 grouping and 52 taxonomy rows with complete text and
  in-canvas bounds. It verified source hashes for 2,325 rendered/referenced images and wrote a
  47-artifact manifest totaling 21,576,108 bytes. Two builds reproduced manifest SHA-256
  `8b2e9ef3b2418623eb92673f3c58591e29f5ed7479bca2b03582c12ef0191dcd` with zero mismatch.
- WP3 manifest schema v2 is portable across output roots: it uses logical root IDs plus relative
  paths and contains no local absolute output path. Its fail-closed verifier checks all 47
  artifacts, 9 source inputs and 5 explicit controls, including decision state, source
  preservation/tree hash, WP1/WP2 manifests and the provenance snapshot.
- WP3 did not modify WP1/WP2 control manifests or `decision_status.json`: their SHA-256 values
  remain `28adbf21...`, `506ec141...`, and `87d81262...` respectively. Their historical snapshot
  keeps D-01…D-05 and G0.4 `PENDING`; WP10 now supersedes G0.4 append-only. Gate 0 remains
  `BLOCKED`; `training_authorized=false`.
- M0-WP4 QCVN taxonomy evidence is **QA PASS, package only; taxonomy not approved**. Milestone
  `QA-M0-WP4-R2` reviewed HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` on the current
  uncommitted worktree and reported `0 blockers`. The prior QA
  reviews rejected the first package for missing target-box overlays and a verifier that could
  accept re-hashed semantic citation changes, then rejected the first repair because required
  boundary stem `0248` was absent from the class-49 atlas. All three repair gaps are now addressed.
  The official Government Circular 51/2024/TT-BGTVT and attached 403-page QCVN 41:2024/BGTVT are pinned under
  `references/qcvn41_2024/` with retrieval metadata and SHA-256 values `dc822815...` and
  `b6b99d0a...`. `scripts/build_wp4_qcvn_taxonomy_audit.py` validates the PDF hashes/page counts,
  cited code/name/section/figure tokens, WP1/WP2/WP3/control hashes and source-image lineage before
  producing the reviewer package. A separately pinned 52-row evidence index has SHA-256
  `62233e56a47c9c7116805d2b9d38846f2a20696b952507752810a83192abd7aa`, binds 39 cited-page
  text/render fingerprints, and records the class-31 negative-search scope as pages 80–154 for
  `camera`, `giám sát`, and `surveillance`.
- The WP4 worksheet contains class IDs `0..51` exactly once: 31 `EXACT`, 14 `PARTIAL`, 6
  `MISMATCH`, and 1 `NOT_FOUND`; all 52 rows are `UNAPPROVED`. In particular, S.505a is a
  supplementary `Loại xe` plate rather than an independent `Only` sign; `B.8a` is an annex
  section/figure and its sign code is P.108a; `P.124b1` is unsupported and the evidence candidate
  is P.124b; class 31 has no asserted QCVN candidate. The separate vNext file is proposal-only and
  the canonical taxonomy was not relabeled.
- The repaired WP4 package includes a 13-page/52-row atlas with visible class/code/stem tags and
  target bbox overlays in all 156 slots. Its 156-row lineage reconstructs label line/index,
  normalized/source/context/render/atlas geometry and re-hashes raw images/labels. Sampling reserves
  known audited boundary case `0248` first for class 49, then preserves WP3 deterministic order for
  the remaining slots. `0248` is class-49 slot 1, raw 960x540, label line 1/index 0; its bbox is
  `(927.00048, 158.99976, 978.00048, 213.99984)` with `18.00048 px` right overflow and
  `source_bbox_within_image=false`. The atlas uses gray hatch virtual padding plus a cyan source
  boundary, without clamp or raw mutation.
  Visual readback covered official PDF pages 1/83/87/88/106/114/117/152 and atlas pages
  001/006/007/008/009/012/013. The 20-artifact/13-source manifest SHA-256 is
  `c60c09018900071cc66d8bc01db32300f4efc6a4316bda9f506819026400db1c`; the WP4-specific suite
  passed 26 tests, including exact required-0248 coverage, deterministic rebuild, geometry/pixel
  reconstruction, rejection of substitute out-of-frame stem `0809`, path escape,
  missing/tampered index, and re-hashed wrong page/code/name/section/figure/token/fingerprint/
  negative-scope failures. QA PASS applies only to the WP4 evidence package; all 52 taxonomy rows
  remain `UNAPPROVED`, D-03 remains `PENDING`, Gate 0 remains `BLOCKED`, and
  `training_authorized=false`.
- M0-WP5 provisional grouping adjudication is **QA PASS PARTIAL, not complete group truth**.
  Milestone `QA-M0-WP5-R1` reviewed HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1`
  plus the current uncommitted tree and reported `0 blockers`. The first QA review found one
  blocker: the verifier accepted deleted roster entries and forged count fields even though every
  remaining hash matched. Manifest schema v2 now derives and enforces an exact 11-item
  source/control allowlist and exact 137-item non-manifest artifact roster; the count explicitly
  excludes the manifest itself to avoid recursive self-hashing. `scripts/build_wp5_provisional_grouping_review.py` deterministically
  covers all 3,178 adjacency edges in a 128-page pair atlas, prioritizes all 1,031 cross-split
  edges first, and links all 589 proxy sequences to the 24 QA-approved WP3 contact sheets. Six
  pairs were actually visually reviewed (five cross-split): four are
  `SAME_CAPTURE_CANDIDATE` and two are `NOT_RELATED`; 3,172 edges, including 1,026 cross-split
  edges, and all 589 sequences remain explicitly `PENDING`. The high-confidence reviewed edges
  yield four capture components/eight images and two physical-sign components/four images, all
  labeled `PROVISIONAL_COMPONENT_NOT_GROUP_TRUTH`; no final grouping or split was created.
  D02-A creator/session metadata remains preferred; D02-B requires full manual review plus an
  independent second reviewer. D-02 stays `PENDING`, Gate 0 stays `BLOCKED`, and training stays
  unauthorized. The repaired manifest SHA-256 is
  `f8d620a3cbb3b500153f6685b94a9936a8f83eb6f5399ce0a2e8be77982d4b80`.
- M0-WP6 frozen-E0 compute/runtime and evaluation-readiness preflight is **QA PASS for the local
  read-only package only**. Milestone `QA-M0-WP6-R2` reviewed HEAD
  `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` plus the current uncommitted tree and reported
  `0 blockers`. This is not D-05 approval or an experiment result. The observed host is an
  Apple M1 Pro with 16 GB memory and 16-core Metal GPU hardware, but TensorFlow 2.20/Keras 3.15.1
  exposes only `/device:CPU:0`; the measured backend is `TENSORFLOW_CPU_ONLY`. Batch-1 timing over
  20 warm-ups plus 300 measured predictions (three repeats of 100, preprocessing +
  `model.predict`) produced p50 `21.7390 ms`, p95 `25.0992 ms`, mean `22.4386 ms` and population
  std `5.3250 ms` (observed max `106.9830 ms`). These numbers are host-specific diagnostics and
  are not an acceptance gate. After QA showed that R1 could regenerate a self-issued attestation
  from forged evidence, R2 pins the reviewed attestation file SHA-256 directly in verifier source.
  `build` now writes only an unpinned candidate under `tmp/` and cannot modify the official package
  or trust anchor. Promotion requires a reviewed manual source-anchor change followed by the
  explicit `promote-pinned` command. Verification checks this independent source anchor before
  trusting attestation content, then reconstructs exact model semantics and re-observes the live
  TensorFlow device/runtime.
  The exact 20-source/3-artifact manifest verifies with SHA-256
  `656afe56bf342a0d4d0110dcd6b1d601f9f35633d03c65c98d54d3d454760bb0`; the source-pinned
  attestation SHA-256 is `5102dc7493cd32f0f958430b3d0dd25b0e288ba10052b81ee17236b4acfb3c56`,
  its observation digest is `c01ce409b094fa46b76117ea2833c95241e737b219967561618eb450bf3b3887`,
  and the deterministic non-timing fingerprint is
  `40ca8550b29d228885e05d7f31c1e34febb08c0117715f9848fa973b42509ed3`.
  All frozen model/GTSRB/evaluation/control hashes remained unchanged. The frozen control snapshot
  keeps D-01…D-05 and G0.4 `PENDING`; WP10 now supersedes G0.4 append-only. Gate 0 remains
  `BLOCKED`, `training_authorized=false`, and no calibration, OOD
  threshold selection, model mutation, split mutation or training occurred.
  Nonblocking technical debt: an official-artifact symlink escape fails closed by raising
  `ValueError` rather than returning structured `valid=false`; QA confirmed no acceptance bypass.
- M0-WP7 cross-split visual adjudication pilot Batch A is **QA PASS as double-reviewed
  provisional evidence only**. Milestone `QA-M0-WP7` independently reviewed HEAD
  `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` plus the current uncommitted tree and reported
  `0 blockers`, 100/100 blind capture-outcome agreement and 20/20 atlas pages reviewed. It is a
  separate overlay and does not edit the QA-approved WP5 artifacts. The exact first 100 unique
  canonical WP5 rows with `cross_split=True` and `review_status=PENDING` were selected in WP5
  order (`edge_000006`…`edge_000307`), excluding all six previously reviewed edges. PM/Codex
  directly inspected both source images for all 100 pairs on a dedicated 20-page bbox/context
  atlas and recorded 98 `SAME_CAPTURE_CANDIDATE` plus 2 `NOT_RELATED` outcomes; independent QA
  agreed with all 100. Confidence is 99 `HIGH` and 1 `MEDIUM`; physical-sign review yielded 97
  `SAME_PHYSICAL_SIGN_CANDIDATE` and 3 `NOT_RELATED`, including `edge_000153` as same-capture but
  physical-sign `NOT_RELATED` at `MEDIUM`. Capture and physical-sign hypotheses remain separate; no
  creator/session/physical-sign identity metadata exists. The package status is
  `WP7_AWAITING_QA_BATCH_A_PM_PROVISIONAL_REVIEW`, manifest SHA-256 is
  `73ed4095a1f59b72f010fd87b63c4a7f0b16bcf8e0c667ec77576ec827e5d7f2`, and verifier reports
  `valid=true` for 9 sources and 25 non-manifest artifacts. Canonical WP5 remains unchanged at
  3,172 `PENDING` edges, including 1,026 canonical cross-split pending edges; the reviewed overlay
  covers 100 Batch-A pairs and leaves 3,072 edges plus 926 cross-split edges outside Batch A.
  All 589 sequences remain `PENDING`. QA PASS does not create final `group_id`, transitive group
  truth, split, relabel or training authorization. D02-A remains preferred, D02-B budget is
  unapproved, D-02 stays `PENDING`, Gate 0 stays `BLOCKED`, and `training_authorized=false`.
- M0-WP8-R1 provisional 52-class taxonomy recommendation is **QA PASS / PROPOSAL PACKAGE ONLY**. It
  converts the pinned WP4 evidence into exactly 52 `UNAPPROVED` reviewer rows with independent
  native-taxonomy, GTSRB-analysis, sign-policy and UNKNOWN-routing decisions. Native counts are
  23 `KEEP_CURRENT`, 19 `CORRECT_CODE_OR_NAME_PROPOSAL`, 9 `SEMANTIC_REVIEW_REQUIRED` and 1
  `OUT_OF_SCOPE_PROPOSAL`; GTSRB counts are 11 `DIRECT_ANALYSIS_ONLY`, 13
  `PARTIAL_ANALYSIS_ONLY`, 27 `NONE` and 1 `REVIEW_REQUIRED`. The required conflict register is
  classes `3/22/23/25/28/30/31/34/47/51`. The machine matrix binds 156 WP4 representatives and
  their image/label hashes plus bbox references; the 13-page decision atlas preserves each pinned
  WP4 page at left and adds the recommendation panel at right. R1 corrects class 14 to
  `ATOMIC_SIGN` because P.106a is the fixed truck prohibition while numeric weight belongs to
  P.106b; classes 6/42/50 now explicitly propose English-name corrections rather than
  `KEEP_CURRENT`. GTSRB and UNKNOWN routing are unchanged. All 13 pages were visually read back
  with complete text and evidence. The exact 21-source/19-artifact manifest verifies
  `valid=true` with SHA-256
  `9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348`; 32 WP8 tests reject
  roster/count/path/symlink and coherently re-hashed matrix, report, layout, atlas, contract and
  critical-row/R1 semantic rollback tampering. The full repository gate passed 210 collected tests,
  Ruff, `uv lock --check` with 168 packages and `git diff --check`. WP8 does not resolve D-03,
  relabel data, create a split or authorize training; D-03 remains `PENDING`, Gate 0 remains
  `BLOCKED`, and `training_authorized=false`.
- Independent WP8-R1 QA returned **PASS with 0 blockers** after checking QCVN semantics, confirming
  no semantic drift in the 48 non-R1 rows, rebuilding all 19 non-manifest artifacts byte-identically
  in a clean room, passing 32/32 WP8 tests and 210/210 full-suite tests, and matching all pinned
  hashes. This QA approves only the proposal/evidence package: all 52 rows remain `UNAPPROVED`,
  D-03 remains `PENDING`, Gate 0 remains `BLOCKED`, and training remains unauthorized. Nonblocking
  debt is the Starlette `TestClient` deprecation and an optional unbuilt Graft deep layer.
- M0-WP9-R1 bbox-0248 adjudication is **QA PASS / DECISION-SUPPORT PACKAGE ONLY**. The pinned raw image
  hash is `07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd`; the raw label hash is
  `f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77`. Label line 1 / index 0,
  class 49 maps to pixel bbox `(927.00048, 158.99976, 978.00048, 213.99984)` and exceeds the
  960-pixel image boundary by `18.00048 px`. Full-frame, boundary-zoom and proxy-only adjacent
  frames 0247/0249 show that the target sign itself is image-edge truncated, not merely enclosed by
  an oversized annotation. PM recommendation is
  `QUARANTINE_FROM_TRAINING_PENDING_OWNER_DECISION`; raw stays immutable and the separate clipped
  candidate is review-only, never an approved training label. The exact 17-source/5-artifact
  manifest verifies `valid=true` with SHA-256
  `cea9423616de0bf4649d71e40f395b4cdc18ff3ea2f80e9829ea4063f009656f`; 30 WP9 tests include a
  byte-identical clean-room rebuild and reject raw/source, semantic, roster/count, path and symlink
  tampering. The full repository gate passes 240/240 tests, Ruff, `uv lock --check` with 168
  packages and `git diff --check`; Graft is synchronized at 34 Python files, 575 nodes and 1,596
  edges. The optional Graft deep layer remains unbuilt and is nonblocking. Independent R1 QA
  concluded PASS with 0 blockers after the stale routing closure was corrected; this PASS validates
  only the WP9 package and does not mutate its historical artifacts.
- The owner approved G0.4 option `APPROVED_QUARANTINE` on `2026-10-11` (`Asia/Saigon`). M0-WP10 is
  **QA PASS / OWNER-APPROVED QUARANTINE ENFORCEMENT** with `0 blockers`. Its append-only overlay leaves the
  hash-pinned historical `decision_status.json` unchanged and applies to the entire stem `0248`,
  including both label rows. Raw image/label stay immutable; stem 0248 is excluded from split
  generation and training; the WP9 derived clip is `REVIEW_EVIDENCE_ONLY_NOT_TRAINING_LABEL`.
  Class 49/taxonomy remains in scope; only sample 0248 is quarantined. The registry verifier/API/CLI
  rejects candidate stem lists or split manifests containing 0248 and fails closed if the overlay,
  registry, pinned lineage or raw hashes are missing/invalid. The exact 10-source/3-artifact
  manifest verifies `valid=true` with SHA-256
  `9c9581e2026f036a79fc1c58bce5f1b87e4c4f0786ee50a49f890e94d0e529e5`; 48 WP10 tests include a
  byte-identical clean-room rebuild and candidate/tamper/path/symlink coverage. The full repository
  gate passes 288/288 tests, Ruff, `uv lock --check` with 168 packages and `git diff --check`;
  Graft was synchronized at 36 Python files, 627 nodes and 1,720 edges for the reviewed package.
  Independent milestone `QA-M0-WP10` subsequently returned PASS with `0 blockers`; this closure is
  recorded only in routing/status documents, so the hash-pinned WP10 artifacts retain their
  historical `AWAITING_QA` strings unchanged. G0.4 is now formally closed and is no longer a
  separate Gate 0 blocker. D-01…D-05 remain `PENDING`, Gate 0 remains `BLOCKED`, and split/training
  authorization remain false.
- M0-WP11 D-04 rare-class decision support is **QA PASS / PACKAGE ONLY / PENDING OWNER DECISION**.
  Independent milestone `QA-M0-WP11` returned PASS with `0 blockers`; this closure is recorded only
  in routing/status documents, so the hash-pinned WP11 artifacts retain their historical
  `AWAITING_QA` strings unchanged. Its deterministic 52-class matrix keeps the current D-04 policy
  `box_count < 50` as exactly 20
  classes, separate from the WP8 analytic flag `image_count < 100` covering 29 classes. The
  recommendation matrix contains 5 `COLLECT_MORE`, 15 `OWNER_REVIEW_REQUIRED` and 32
  `KEEP_NATIVE_PENDING_D03`; all owner states and all WP8 taxonomy rows remain `PENDING`/
  `UNAPPROVED`, with no automatic semantic merge.
- WP11 pins and renders all eight available extreme-support instances: class 44 (`W.233`) has
  3 images/3 boxes on stems `0670`–`0672`, and class 51 (`W.246c`) has 5 images/5 boxes on stems
  `0530`–`0534`. Their image/label hashes, exact label lines, normalized boxes and pixel boxes are
  recorded in the lineage CSV and two-page atlas. Raw train/test counts remain descriptive only;
  effective independent support is `UNKNOWN_PENDING_D02`, and adjacency/grouping proxies are not
  group truth.
- WP11 applies the QA-passed G0.4 registry without changing WP10: whole stem `0248` is ineligible,
  class 49 changes from 120 images/221 boxes to 119 eligible images/219 eligible boxes, its
  taxonomy remains present, and the WP9 derived clip is not a training sample. The exact
  28-source/9-artifact manifest verifies `valid=true` with SHA-256
  `61b5bfbb92ac872ae4d5bfc6d508426f59b4065d4cd2f43f3f979e664095b465`; 48 targeted tests cover
  deterministic/clean-room rebuild, exact rosters, drift, omission, class-49 eligibility,
  semantic-merge/governance rollback, path/symlink rejection and visual completeness. D-04 remains
  `PENDING_OWNER_DECISION`, Gate 0 remains `BLOCKED`, and `training_authorized=false`. The full
  repository gate passes 336/336 tests, Ruff, `uv lock --check` with 168 packages and
  `git diff --check`; Graft is synchronized at 38 Python files, 688 nodes and 1,875 edges. The
  optional Graft deep layer remains unbuilt and nonblocking.
- M0-WP12-R1 D02-B Batch B is **QA PASS / DOUBLE-REVIEWED PROVISIONAL EVIDENCE ONLY**. It keeps
  the exact next 250 canonical WP5 pending cross-split rows after WP7 (`edge_000315`…
  `edge_001033`) as a separate overlay: 500 endpoint rows, 1,553 boxes, no stem `0248`, 50 atlas
  pages and no mutation of WP5/WP7/WP10/WP11. PM outcomes are capture 240 same-capture/8
  not-related/2 unresolved (`edge_000535`, `edge_000539`), physical-sign 235 same-sign/14
  not-related/1 unresolved (`edge_000539`), and confidence 243 high/7 medium.
- Independent QA accepted the 250 decisions visually with 0 blind capture disagreements and
  reviewed 50/50 pages, but returned FAIL on the pre-repair verifier because atlas bytes/layout
  were not independently regenerated and review notes were not source-pinned. R1 preserves every
  decision while adding an exact 51-file atlas roster, isolated byte regeneration of index/50
  JPEG pages, byte/deep layout comparison, and trusted review-notes SHA-256
  `27adbf366cfbfd2c03c1025e82bd6cef26e1b353e1e50340ddc6d7a5f9ed75b4` with exact outcome/
  unresolved-ID contracts. The coherent `edge_000539` rollback is rejected after full downstream
  rebuild. The pre-repair manifest `0b5c90de...` is superseded by R1 SHA-256
  `8e576954bc3de456704aecdb67e8625d8621ca017fb08e3b866635db6afcc0f0`, with 12 sources,
  56 non-manifest artifacts and 55 targeted tests passing. The full repository gate passes
  391/391 tests, Ruff, `uv lock --check` (168 packages) and `git diff --check`; Graft is in sync at
  40 Python files/755 nodes/2,082 edges. Independent `QA-M0-WP12-R1` subsequently returned PASS
  with `0 blockers`: 18/18 adversarial attacks were rejected, clean-room regeneration was
  byte-identical, and the targeted/full suites remained 55/55 and 391/391. The hash-pinned package
  retains its historical `AWAITING_QA` status string; closure is recorded only in routing docs.
- M0-WP13 D02-B Batch C is **QA PASS / DOUBLE-REVIEWED PROVISIONAL EVIDENCE ONLY**. It selects
  the exact next 250 canonical WP5 pending cross-split rows after the non-overlapping WP7 and WP12
  rosters (`edge_001041`…`edge_001882`, WP5 review order 356…605): 500 endpoints, 1,079 boxes,
  no stem `0248`, 50 atlas pages and no canonical WP5/prior-package mutation. PM read back all
  50/50 post-annotation pages. Capture outcomes are 241 same-capture candidates and 9 not-related;
  physical-sign outcomes are 240 same-sign candidates and 10 not-related; all 250 are HIGH
  confidence. `edge_001802` deliberately separates capture continuity from physical identity.
  Manifest SHA-256 is `5db80e215f318a6b782d813b4560c20e35e4f3e51ef0423d7298f4818ea3db65` with 16 sources and
  56 non-manifest artifacts. The 60-test WP13 suite passes, including exact WP7/WP12 exclusion,
  fail-closed path/type/symlink/roster/layout/byte/semantic attacks, trusted-note rollback rejection
  and clean-room byte determinism. Full repository validation passes 450/450 tests, Ruff,
  `uv lock --check` (168 packages) and `git diff --check`; Graft is synchronized at 42 Python files,
  799 nodes and 2,188 edges. Independent `QA-M0-WP13` subsequently returned PASS with `0 blockers`:
  18/18 CLI attacks were rejected, coherent and count-preserving semantic rollback attempts failed,
  56/56 artifacts rebuilt byte-identically, and all 50/50 atlas pages plus 250/250 decision panels
  were independently inspected. The hash-pinned package retains its historical `AWAITING_QA`
  status string; closure is recorded only in routing docs.
- M0-WP14 D02-B Batch D is **QA PASS / DOUBLE-REVIEWED PROVISIONAL EVIDENCE ONLY**. It selects
  the exact next 250 canonical WP5 pending cross-split rows after the non-overlapping WP7, WP12 and
  WP13 rosters (`edge_001894`…`edge_002664`, WP5 review order 606…855): 500 endpoints, 1,413
  boxes, 365 unique stems, no stem `0248`, 50 atlas pages and no canonical/prior-package mutation.
  PM read back all 50/50 post-annotation pages. Capture outcomes are 246 same-capture candidates
  and 4 not-related (`edge_001968`, `edge_002032`, `edge_002453`, `edge_002568`); physical-sign
  outcomes are 238 same-sign candidates and 12 not-related (the same four plus `edge_002107`,
  `edge_002108`, `edge_002161`, `edge_002162`, `edge_002172`, `edge_002173`, `edge_002262`,
  `edge_002263`); all 250 are HIGH confidence. The trusted notes SHA-256 is
  `ac63ad6fafc767a81263ad181fa3a96a19d8c493e648d145abedc641bc09b84e`; manifest SHA-256 is
  `ea4667c2ea18bc6fff23ce23beffe5b27372e494160fa9d6ffbc86c3cb3f2dc5` with 20 sources and
  56 non-manifest artifacts. The 65-test targeted suite passes, including exact prior-batch
  exclusion, 18 attack classes, trusted-note coherent rollback, count-preserving exact-ID swap
  rejection and clean-room byte determinism. Full repository validation passes 516/516 tests,
  Ruff, `uv lock --check` (168 packages) and `git diff --check`; Graft is synchronized at 44
  Python files, 845 nodes and 2,298 edges. Independent `QA-M0-WP14` subsequently returned PASS
  with `0 blockers`: 18/18 CLI attacks were rejected, coherent rebuild and count-preserving exact-ID
  swap attacks failed, 56/56 artifacts rebuilt byte-identically, and all 50/50 atlas pages plus
  250/250 decision panels were independently inspected. The hash-pinned package retains its
  historical `AWAITING_QA` status string; closure is recorded only in routing docs. This is not
  D-02 approval, group truth, split assignment or training authorization.
- M0-WP15 D02-B Batch E is **QA PASS / DOUBLE-REVIEWED PROVISIONAL EVIDENCE ONLY**.
  It selects the exact final 176 canonical WP5 pending cross-split rows after the non-overlapping
  WP7/WP12/WP13/WP14 prefix (`edge_002665`…`edge_003178`, WP5 review order 856…1,031): 352
  endpoints, 992 boxes, no stem `0248`, 36 atlas pages with exact 35×5 + 1×1 pagination and no
  canonical/prior-package mutation. PM read back all 36/36 post-annotation pages. Capture outcomes
  are 176 same-capture candidates; physical-sign outcomes are 173 same-sign candidates and 3
  not-related (`edge_002798`, `edge_002847`, `edge_002901`); all 176 are HIGH confidence. Trusted
  notes SHA-256 is `740fe42e79ec6e2a8c921ac254c31172188c5860898b81f205a494843f6e0bd7`;
  manifest SHA-256 is `032aee9da985c5dcb772ddd1c73fa9e4e6794e1beb5107fdb49b0168948a241d`
  with 24 sources and 42 non-manifest artifacts. The 69-test targeted suite and 585-test full suite
  pass with 18 attack classes, coherent rollback, count-preserving exception swap rejection,
  clean-room byte determinism, Ruff, `uv lock --check` (168 packages) and `git diff --check`.
  Graft is synchronized at 46 Python files, 892 nodes and 2,415 edges. Independent `QA-M0-WP15`
  subsequently returned PASS with 0 blockers and 0 functional/package findings after hashing all
  704 raw bindings, reading 36/36 pages and 176/176 panels, rejecting 18/18 attacks and rebuilding
  42/42 artifacts byte-identically. The package retains its hash-pinned historical `AWAITING_QA`
  status; closure is recorded only in routing docs.
- WP7+WP12+WP13+WP14+WP15 overlays now cover 1,026 pairs without changing canonical WP5: 3,172
  edges remain `PENDING`; 2,146 pending edges/zero cross-split edges remain outside all five
  overlays; all 589 sequences remain `PENDING`. All five overlays are independently QA-passed
  provisional evidence, and zero canonical pending cross-split rows remain outside them.
  D02-A remains preferred, D02-B budget is unapproved, D-02 remains `PENDING`, Gate 0 remains
  `BLOCKED`, and no final/transitive group truth, `group_id`, split or training authorization exists.
- M0-WP16-R1 D02-C Sequence Batch A is **QA PASS / SCHEMA-HARDENED / PROVISIONAL EVIDENCE
  ONLY**. It selects the exact first 100 quarantine-eligible canonical
  WP5 `PENDING`
  sequences in canonical order: `proxy_sequence_0001`…`proxy_sequence_0101` excluding the whole
  `proxy_sequence_0050`, because that row contains quarantined stem `0248`. The exclusion registry
  keeps row 50 intact at `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; no selected member is `0248`. The package covers 100 sequences
  and 339 unique member frames, leaving 489 outside the overlay while all 589 canonical rows remain
  `PENDING`. PM directly inspected all 100 prepared pages/all 339 member frames before pinning and
  post-build pages 1/50/100. Outcomes are 100 `CONTINUOUS_CANDIDATE`; physical-sign outcomes are
  40 `SAME_PHYSICAL_SIGN_CANDIDATE` and 60 `MULTIPLE_SIGNS`; all are HIGH confidence. Trusted
  notes SHA-256 is `d673ac00d0345fcf1fc0b46c2e9e3396ba97d3bd17259ce7a4d370756ed38e9d`;
  Initial QA found 0 package-content blockers and passed the existing rollback, swap and clean-room
  checks, but reported one real P3: an otherwise-valid staged manifest accepted an unknown
  top-level key. R1 now enforces an exact 31-field top-level manifest schema and has explicit
  regressions for benign unknown, governance-looking unknown and missing keys. The inherited
  collection validator already exact-checks every nested source/artifact record, so historical
  verifiers were not changed. R1 manifest SHA-256 is
  `f3e3fb7a13631ef60b9046f745c07cb39ff3df501c18d5e15e79ee2e505964bc` with 19 sources, 107
  non-manifest artifacts and 19,105,566 artifact bytes; 106/107 artifacts remain byte-identical
  to pre-R1, with only the generated report changed, and only the builder source changed. The
  32-test targeted suite passes with 21 attack classes, coherent rollback, count-preserving
  decision-ID swap rejection and clean-room byte determinism. Full validation passes 617/617 tests, Ruff,
  `uv lock --check` (168 packages), `git diff --check`; all WP5, WP7 and WP10–WP16 CLI verifiers
  return `valid=true`. Graft is synchronized at 48 Python files, 943 nodes and 2,564 edges. Package
  status remains `WP16_AWAITING_QA_SEQUENCE_BATCH_A_PM_PROVISIONAL_REVIEW`. Independent
  `QA-M0-WP16-R1` returned PASS with 0 blockers and no new P0/P1/P2/P3 findings after 32/32
  targeted tests, 617/617 full-suite tests, 21 attack classes and clean-room 107/107. Closure is
  recorded only in routing docs so the hash-pinned package stays unchanged. This is not D-02
  approval, group truth, split or training authorization.
- M0-WP17 D02-C Sequence Batch B is **QA PASS / PROVISIONAL EVIDENCE ONLY**. Its derivation first
  proves WP16 is the exact 100-sequence eligible prefix, then
  selects the exact next 100 canonical PENDING sequences: `proxy_sequence_0102`…
  `proxy_sequence_0201`, no gaps, no WP16 overlap and no quarantined stem `0248`. Canonical
  `proxy_sequence_0050` remains intact at `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`. The package covers 344 unique member frames and 1,312 bbox
  occurrences. PM directly inspected 100/100 prepared atlas pages and all 344 frames, then read
  back built pages 1/50/100. Outcomes are 100 `CONTINUOUS_CANDIDATE`, 91 `MULTIPLE_SIGNS`, 9
  `SAME_PHYSICAL_SIGN_CANDIDATE` and 100 `HIGH`. Trusted notes SHA-256 is
  `cdefee98149db85d4600cf7f69ee004d6f769ecc23bc6c57dce898732c2e4248`; manifest SHA-256 is
  `374ada61066f70f8ff3ba282dba41229ad2c161303146edd83aba583591b144b`, with 21 sources, 107
  non-manifest artifacts and 18,636,827 artifact bytes. The 28-test targeted suite passes with 21
  attack classes and clean-room 107/107 byte determinism; full validation passes 645/645 tests,
  Ruff, `uv lock --check` (168 packages) and `git diff --check`. All WP5/WP7/WP10–WP17 CLI
  verifiers pass. Graft is synchronized at 50 Python files, 970 nodes and 2,631 edges. WP16+WP17
  cover 200/589 canonical sequences; 389 remain outside while all 589 remain PENDING. Status is
  `WP17_AWAITING_QA_SEQUENCE_BATCH_B_PM_PROVISIONAL_REVIEW`; D-02 and Gate 0 remain blocked and
  training remains unauthorized. Independent QA returned PASS with 0 blockers and no severity
  findings after 21/21 attack rejections, clean-room 107/107 and full-suite 645/645. Closure is
  routing-only; the historical hash-pinned package/report were not rewritten.
- M0-WP18 D02-C Sequence Batch C is **QA PASS / PROVISIONAL EVIDENCE ONLY**. Read-only derivation
  proves WP16+WP17 are the exact first-200 eligible prefix,
  then selects exact `proxy_sequence_0202`…`proxy_sequence_0301`, with no gap, overlap or stem
  `0248`. The whole quarantined `proxy_sequence_0050` stays canonical `PENDING`, unreviewed and
  intact. PM directly inspected 100/100 prepared atlas pages and all 400 unique frames; outcomes
  are 100 `CONTINUOUS_CANDIDATE`, 70 `MULTIPLE_SIGNS`, 30
  `SAME_PHYSICAL_SIGN_CANDIDATE`, all `HIGH`, covering 944 bbox occurrences. Trusted notes
  SHA-256 is `69eb2da7c8dadcb5d27aadc46fa90e7941a1798ac4dca790110e4f8484d0d915`;
  manifest SHA-256 is `35bf843db7eb626404c81477efb509b2e4881a2cc7ea81fcee3187fcfab93649`,
  with 23 sources, 107 non-manifest artifacts and 20,715,246 artifact bytes. Targeted validation
  passes 29/29 tests with 22 attack classes (including predecessor-prefix tamper) and clean-room
  107/107; full validation passes 674/674 tests, Ruff, lock and diff. Every WP5/WP7/WP10–WP18
  verifier passes and Graft is synchronized at 52 Python files, 997 nodes and 2,698 edges. The
  three overlays cover 300/589 canonical sequences; 289 remain outside (288 eligible plus the
  quarantined sequence), while all 589 canonical rows remain `PENDING`. Status is
  `WP18_AWAITING_QA_SEQUENCE_BATCH_C_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 remain blocked and
  training remains unauthorized. Independent QA returned PASS with 0 blockers and no severity
  findings after 22/22 attack rejections, clean-room 107/107 and full-suite 674/674. Closure is
  routing-only; the historical hash-pinned package/report were not rewritten.
- M0-WP19 D02-C Sequence Batch D is **QA PASS / PROVISIONAL EVIDENCE ONLY**. Read-only derivation
  proves WP16+WP17+WP18 are the exact first-300 eligible
  prefix, then selects exact `proxy_sequence_0302`…`proxy_sequence_0401`, with no gap, overlap or
  stem `0248`. The whole quarantined `proxy_sequence_0050` stays canonical `PENDING`, unreviewed
  and intact. PM directly inspected 100/100 prepared atlas pages and all 422 unique frames;
  outcomes are 100 `CONTINUOUS_CANDIDATE`, 61 `MULTIPLE_SIGNS`, 39
  `SAME_PHYSICAL_SIGN_CANDIDATE`, all `HIGH`, covering 824 bbox occurrences. Trusted notes
  SHA-256 is `627e0598d077ccb568c252b7980833cd317803398385fce61e467c3e2de483b1`;
  manifest SHA-256 is `6796c3a16b2af347f0a74a06cde4477b214d97233d0d38848d9077933c7f712f`,
  with 25 sources, 107 non-manifest artifacts and 20,702,974 artifact bytes. Targeted validation
  passes 29/29 tests with 22 attack classes, including predecessor-prefix tamper and clean-room
  107/107. Full validation passes 703/703 tests; every WP5/WP7/WP10–WP19 verifier, Ruff, lock and
  diff pass. Graft is synchronized at 54 Python files, 1,024 nodes and 2,765 edges. The four overlays cover
  400/589 canonical sequences; 189 remain outside (188 eligible plus the quarantined sequence),
  while all 589 canonical rows remain `PENDING`. Status is
  `WP19_AWAITING_QA_SEQUENCE_BATCH_D_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 remain blocked and
  training remains unauthorized. Independent QA returned PASS with 0 findings after targeted
  29/29 and full-suite 703/703. Closure is routing-only; the historical hash-pinned package/report
  were not rewritten.
- M0-WP20 D02-C Sequence Batch E is **QA PASS / PROVISIONAL EVIDENCE ONLY**. Read-only derivation
  proves WP16…WP19 are the exact first-400 eligible prefix,
  then selects exact `proxy_sequence_0402`…`proxy_sequence_0501`, with no gap, overlap or stem
  `0248`. The whole quarantined `proxy_sequence_0050` stays canonical `PENDING`, unreviewed and
  intact. PM directly inspected 100/100 prepared atlas pages and all 406 unique frames; outcomes
  are 100 `CONTINUOUS_CANDIDATE`, 81 `MULTIPLE_SIGNS`, 19
  `SAME_PHYSICAL_SIGN_CANDIDATE`, all `HIGH`, covering 1,287 bbox occurrences. Trusted notes
  SHA-256 is `04a70bfa693c105da29ac263ab8f24a1e030b489b8379078c79e0dd3f21e6f8b`;
  selection SHA-256 is `b99abd53de497e74e42a75396be9f565c391977c4f35f633975cba3081c3bfc3`;
  manifest SHA-256 is `4523c698ff948ee2adaf879195662caec25ac80280cceb0aaaf91ae72fe89a6c`,
  with 27 sources, 107 non-manifest artifacts and 20,410,750 artifact bytes. Targeted validation
  passes 29/29 tests with 22 attack classes, including WP19-prefix tamper and clean-room 107/107;
  full validation passes 732/732 tests. Every WP5/WP7/WP10–WP20 verifier, Ruff, lock and diff pass;
  Graft is synchronized at 56 Python files, 1,051 nodes and 2,832 edges. Five overlays cover
  500/589 canonical sequences; 89 remain outside (88 eligible plus the quarantined sequence),
  while all 589 canonical rows remain `PENDING`. Status is
  `WP20_AWAITING_QA_SEQUENCE_BATCH_E_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 remain blocked and
  training remains unauthorized. Independent QA subsequently returned PASS with 0 findings and
  full-suite 732/732. Closure is routing-only; the hash-pinned package/report remain unchanged.
- M0-WP21 D02-C Final Eligible Sequence Batch is **QA PASS / PROVISIONAL EVIDENCE ONLY**.
  Read-only derivation proves WP16…WP20 are the exact first-500
  quarantine-eligible prefix, then selects the complete residual `eligible[500:]` suffix:
  `proxy_sequence_0502`…`proxy_sequence_0589`, 88 sequences with no gap, overlap or stem `0248`.
  Whole quarantined `proxy_sequence_0050` stays canonical `PENDING`, unreviewed and intact. PM
  directly inspected 88/88 prepared atlas pages and all 363 unique frames; outcomes are 88
  `CONTINUOUS_CANDIDATE`, 60 `MULTIPLE_SIGNS`, 28 `SAME_PHYSICAL_SIGN_CANDIDATE`, all `HIGH`,
  covering 1,068 bbox occurrences. Trusted notes SHA-256 is
  `8acdfdb0041214f933eb4933cbddfd97bc90868361c4b9351975b6dacbb3e8c1`; selection SHA-256 is
  `40c7c7d9c94767b2b6d82bd9d2d134aa74af0afd7f62ce5ed470e55ab9efbc68`; manifest SHA-256 is
  `7ed7e1355ae1dfc88ec81b7f580aad3bf0874b59832708652ad1ba02265d4e4c`, with 29 sources, 95
  non-manifest artifacts and 17,536,294 artifact bytes. Targeted validation passes 29/29 tests
  with 22 attack classes, including WP20-prefix tamper and clean-room 95/95; full validation
  passes 761/761 tests. Every WP5/WP7/WP10–WP21 verifier, Ruff, lock and diff pass; Graft is
  synchronized at 58 Python files, 1,078 nodes and 2,899 edges. Six overlays cover all 588
  quarantine-eligible canonical sequences; only the quarantined sequence remains outside, while
  all 589 canonical rows remain `PENDING`. Status is
  `WP21_AWAITING_QA_FINAL_ELIGIBLE_SEQUENCE_BATCH_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 remain
  blocked, split/training remain unauthorized, and no final/transitive group truth exists.
  Independent QA returned PASS with 0 findings after confirming 588/588 eligible coverage,
  761/761 full tests, every verifier/pin/preservation check and clean-room 95/95. Closure is
  routing-only; the hash-pinned package/report retain their historical `AWAITING_QA` status.
- M0-WP22 D02-D Remaining-Edge Manual Reconciliation Batch A is **INDEPENDENT QA PASS /
  PROVISIONAL EVIDENCE ONLY**. Exact derivation proves a 2,146-row unique
  non-cross-split PENDING residual after the six WP5-reviewed rows and all 1,026 QA-passed
  cross-split overlays. It excludes exact quarantine edges `edge_000242`/`edge_000243`, then
  selects the first 250/2,144 review-eligible rows in canonical order: `edge_000002`…
  `edge_000378`, 500 endpoints, 903 bbox occurrences and no stem `0248`. PM directly inspected
  all 50 atlas pages/250 panels; outcomes are 240 same-capture/same-physical-sign candidates and
  10 `NOT_RELATED`, all `HIGH`. WP16–WP21 sequence evidence is pinned context only and never
  derives an edge decision. Trusted notes SHA-256 is
  `c49c00bc85bbc0bc1cfc4683d9dbbd6403705a42600a1251e46e7ade949c6a27`; selection SHA-256 is
  `af70edc35a2a925f4e23bd8ce2e481c7fdf6e18f1c904c963561c412ac74d6aa`; manifest SHA-256 is
  `7086371d65d1389c26541a3621745e0eadb9df7bfe62ca3dab34ffbb45e3b487`, with 52 sources, 56
  non-manifest artifacts and 54,312,346 bytes. Official verify is `valid=true`; 45/45 targeted
  and 806/806 full tests pass, including 18 attack classes and clean-room 56/56; Ruff, lock, diff
  and all historical WP5/WP7/WP10–WP22 verifiers pass. Graft is check-clean at 60 Python files,
  1,121 nodes and 2,998 edges; the optional deep layer remains unbuilt. Canonical WP5 remains
  3,172 PENDING;
  1,896 residual rows remain outside overlays, including the two quarantine edges, and all 589
  canonical sequences remain PENDING. Status is
  `WP22_AWAITING_QA_REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 remain blocked,
  split/training remain unauthorized, and no final/transitive group truth exists.
  Independent QA later returned PASS with 0 findings after confirming exact selection, decisions,
  hashes, preservation checks, all verifiers, 806/806 full tests and clean-room 56/56. Closure is
  routing-only; the hash-pinned WP22 package/report retain their historical `AWAITING_QA` status.
- M0-WP23 D02-D Remaining-Edge Manual Reconciliation Batch B is **INDEPENDENT QA FAIL /
  HISTORICAL PROVISIONAL EVIDENCE ONLY**. After exact WP22-prefix removal, derivation proves
  a 1,896-row unique non-cross-split PENDING residual, excludes exact quarantine edges
  `edge_000242`/`edge_000243`, and selects the next 250/1,894 review-eligible rows in canonical
  order: `edge_000379`…`edge_000760`, WP5 orders 1,285…1,534, 500 endpoints and 1,556 bbox
  occurrences. PM directly inspected all 50 atlas pages/250 panels; outcomes are 233
  same-capture/same-physical-sign candidates and 17 `NOT_RELATED`, all `HIGH`. WP16–WP21 sequence
  evidence remains pinned context only and never derives an edge decision. Trusted notes SHA-256
  is `c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8`; selection SHA-256 is
  `e6913b2eeba22c990cef393490f8d8cb2caaa6745b2045e6edf64c3a6f9973a6`; annotations SHA-256 is
  `2720ac892a9f0ebe46dc027a722702031a8519aaa856965d560da99d85e2c7be`; manifest SHA-256 is
  `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd`, with 56 sources, 56
  non-manifest artifacts and 54,019,044 bytes. Official verify is `valid=true`; 45/45 targeted
  tests and 851/851 full tests pass, including 18 attack classes and clean-room 56/56 byte
  determinism; Ruff, lock and diff pass. Graft is check-clean at 62 Python files, 1,164 nodes and
  3,097 edges. Canonical WP5
  remains 3,172 PENDING; 1,646 residual rows remain outside overlays, including the two quarantine
  edges, and all 589 canonical sequences remain PENDING. Status is
  `WP23_AWAITING_QA_REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 remain blocked,
  split/training remain unauthorized, and no final/transitive group truth exists. Independent QA
  later returned **FAIL** with exactly one High finding and no Critical/Medium/Low findings:
  `edge_000664` was incorrectly marked `NOT_RELATED` despite raw-frame evidence of the same camera
  advancing slightly in one scene with the same five annotated class IDs `7 10 17 19 44`.
  Technical/integrity checks remained PASS. The entire initial package is retained byte-for-byte
  as the correction audit trail.
- M0-WP23-R1 is **INDEPENDENT QA PASS / PROVISIONAL EVIDENCE ONLY**. It pins the
  initial failed manifest and applies one append-only correction overlay to `edge_000664`, changing
  only its decision/rationale to `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, `HIGH`.
  The exact 250-edge selection, 500 endpoints, 1,556 bbox occurrences, source lineage and raw
  hashes remain unchanged; corrected tallies are 234 same and 16 `NOT_RELATED`, all 250 `HIGH`.
  The 16 remaining `NOT_RELATED` rows retain explicit discontinuous-scene/non-matching-sign
  rationales. Official verify is `valid=true` with 62 sources, 56 artifacts and 54,306,219 artifact
  bytes. Initial→R1 manifest SHA-256 is
  `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd` →
  `8b1ca3c9953209d5fc86a8b2265228e27adb63cb430d5c5f5f1375d8d6f86783`; correction-overlay
  SHA-256 is `f12ce41c8290bab9808522b24fa96e460f53ff81ba0b466240c21635b77994b8`.
  All 16 historical/current WP5/WP7/WP10–WP23 CLI verifiers pass. The R1 targeted suite passes
  28/28 with exactly 18 attack classes, semantic regression coverage and clean-room 56/56; full
  repository validation passes 879/879. Ruff, `uv lock --check` (168 packages) and
  `git diff --check` pass. Visual readback of R1 atlas pages 39, 1, 25 and 50 confirms the corrected
  decision, R1 boundary, bbox context and layout.
  Independent delegated QA subsequently returned PASS with 0 findings. This is routing evidence;
  the immutable package retains historical status `WP23_R1_AWAITING_QA_REVIEW`. D-02/Gate 0
  remain blocked, all 3,172 edges and 589 sequences remain canonical `PENDING`, and no
  final/transitive group truth, split or training authorization exists.
- M0-WP24 D02-D Remaining-Edge Manual Reconciliation Batch C is **INDEPENDENT QA PASS /
  PROVISIONAL EVIDENCE ONLY**. Read-only derivation removes the exact QA-passed
  WP22 and WP23-R1 prefixes from the canonical non-cross-split PENDING queue, proves a 1,646-edge
  residual, preserves `edge_000242`/`edge_000243` as quarantined, and selects the exact next 250
  eligible rows: `edge_000763`…`edge_001154`, WP5 orders 1,535…1,784. Coverage is 500 endpoints,
  323 unique stems, 1,581 endpoint bbox occurrences and 1,044 unique-stem bbox occurrences;
  train/test endpoints are 470/30, proxy tiers are 132 strong/96 uncertain/22 adjacency-only,
  and 55 nonempty sequence IDs occur. There are zero cross-split rows and no stem `0248`.
  PM directly inspected all 50 atlas pages/250 pair panels. Provisional outcomes are 243
  `SAME_CAPTURE_CANDIDATE`/`SAME_PHYSICAL_SIGN_CANDIDATE` and 7 `NOT_RELATED`, all `HIGH`.
  Manifest SHA-256 is `e5f49a4c5840a6e682f2a7d0cc418183ec6f52d7b745b9f397b570d6770ceaea`;
  selection is `19194c430c03fcaa507646ca0065776e1279471e1b2ed240f05506f74f3b5c9d`;
  annotations are `82d480a5f0aee86d92236c73a7651b0ed4068385c69a5bdb571ddc071dd10f6f`;
  trusted notes are `086f1c58acbe1434b5bf295576d24e4279fccb59e01f56ba5f3aafaec4508ab1`.
  Official verify is `valid=true` with 67 sources, 56 artifacts and 50,037,488 artifact bytes.
  WP24 targeted tests pass 46/46, the combined WP22/WP23/WP23-R1/WP24 suites pass 164/164,
  and the full repository gate passes 925/925 with Ruff, `uv lock --check` (168 packages) and
  `git diff --check`. Graft is check-clean at 66 Python files, 1,238 nodes and 3,265 edges. Status
  is `WP24_AWAITING_QA_REVIEW`; 1,396 residual PENDING edges remain
  outside overlays including the two quarantine edges. D-02 remains `PENDING`, Gate 0 remains
  `BLOCKED`, split/training remain unauthorized, and no final/transitive group truth exists.
  Independent delegated QA returned PASS with 0 findings; this closure is routing-only and the
  hash-pinned package retains its historical status byte-for-byte.
- M0-WP25 D02-D Remaining-Edge Manual Reconciliation Batch D is **INDEPENDENT QA FAIL /
  IMMUTABLE HISTORICAL PACKAGE / PROVISIONAL EVIDENCE ONLY**. Independent read-only derivation removes the exact
  QA-passed WP22/WP23-R1/WP24 prefixes, proves a 1,396-edge residual, preserves
  `edge_000242`/`edge_000243` as quarantined, and selects the exact next 250 eligible rows:
  `edge_001155`…`edge_001502`, WP5 orders 1,785…2,034. Coverage is 500 endpoints, 307 unique stems,
  1,090 endpoint bbox occurrences and 671 unique-stem bbox occurrences; train/test endpoints are
  468/32, proxy tiers are 142 strong/79 uncertain/29 adjacency-only, and 58 nonempty sequence IDs
  occur. There are zero cross-split rows, no stem `0248` and no `proxy_sequence_0050`; the whole
  quarantined sequence remains intact outside selection. PM directly inspected all 50 atlas
  pages/250 pair panels. Provisional outcomes are 240 `SAME_CAPTURE_CANDIDATE`/
  `SAME_PHYSICAL_SIGN_CANDIDATE` and 10 `NOT_RELATED`, all `HIGH`. Manifest SHA-256 is
  `1d7b04d6432424297f2e14178dd59936526dec7d6293872fbda0010bb460e5e9`; selection is
  `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`; annotations are
  `990d314a462a2279d9600f2b6b5e2b12c1da73dd7425e7ec07a388d883487cc5`; trusted notes are
  `b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8`. Official verify is
  `valid=true` with 72 sources, 56 artifacts and 51,739,615 artifact bytes. WP25 targeted tests
  pass 46/46 with 18 fail-closed attack classes, a same-count decision-ID swap check and
  clean-room 56/56 byte determinism. Combined remaining-edge suites pass 210/210 and the full
  repository gate passes 971/971; all 18 historical/current WP5/WP7/WP10–WP25 verifiers pass.
  Ruff, lock and diff pass; Graft is check-clean at 68 Python files, 1,278 nodes and 3,356 edges.
  Historical package status remains `WP25_AWAITING_QA_REVIEW`; 1,146 residual PENDING
  edges remain outside overlays including the two quarantine edges. All 589 sequences and the
  canonical WP5 rows remain `PENDING`; D-02/Gate 0 remain blocked; split/training remain
  unauthorized; no final/transitive group truth exists.
- Independent QA returned **FAIL** with exactly one `P1` and zero `P0`/`P2`/`P3` findings:
  `edge_001358` (batch position 144, WP5 order 1928, page 029 slot 4, stems 1365→1366) was
  incorrectly marked `NOT_RELATED`. Raw frames/labels show the same road scene and same class-5
  physical sign with a small camera movement. Class-5 bbox center/size changes from
  `(0.388021, 0.303704)/(0.036458, 0.055556)` to
  `(0.406250, 0.313889)/(0.037500, 0.046296)`; same dimensions, `uncertain`, MAE `12.005787`,
  dHash `18`, histogram cosine `0.99375935`. Technical/integrity gates remained PASS and initial
  WP25 is preserved byte-for-byte as the QA-fail audit trail.
- M0-WP25-R1 is **INDEPENDENT QA PASS / PROVISIONAL EVIDENCE ONLY**. The
  append-only one-row overlay changes only `edge_001358` to `SAME_CAPTURE_CANDIDATE` /
  `SAME_PHYSICAL_SIGN_CANDIDATE`, `HIGH`; the other 249 decisions are unchanged. Effective
  tallies are 241 same, 9 `NOT_RELATED`, 250 `HIGH`. The exact 250-edge selection is byte-identical
  to initial WP25 (SHA-256
  `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`); 500 source-lineage
  endpoints, 1,090 bbox occurrences, zero cross-split rows, stem-0248 quarantine and all of
  `proxy_sequence_0050` remain unchanged.
- WP25-R1 official verify is `valid=true` with 78 sources, 56 artifacts and 52,026,143 artifact
  bytes. Manifest SHA-256 is `96a19417256c312c1ec005f13c5abccf85a1718d12ab0c729cb234baebfe9fe8`;
  annotations are `90e6016abcbba10df96c32625e84df3284a9c8a55daccae25771fe2159db8807`;
  correction overlay is `a1385c5a295b927887ffe73c29987d1c3487812d7d25b1a3aa9688c25f39ecd9`;
  QA correction record is `e1e641ee6b36abd257d284d3231c6672934b6ed906964536352b5a8de706439d`.
  Targeted tests pass 29/29 with 18 attack classes and clean-room 56/56; combined remaining-edge
  compatibility passes 239/239; full repository validation passes 1,000/1,000. All 19 supported
  current/historical CLI verifiers, Ruff, `uv lock --check` (168 packages) and `git diff --check`
  pass. Graft is check-clean at 70 Python files, 1,313 nodes and 3,435 edges. Visual readback of
  page 029 slot 4 confirms the corrected panel/bbox/rationale. Status is
  `WP25_R1_AWAITING_QA_REVIEW`. Independent QA returned PASS with zero findings after direct raw
  frame/label readback, exact oracle checks, 18/18 fail-closed attacks, clean-room 56/56,
  targeted 29/29, remaining-edge compatibility 239/239, full suite 1,000/1,000 and all 19
  supported CLI verifiers. Closure is routing-only; the hash-pinned R1 package retains its
  historical status, while initial WP25 remains the immutable QA-fail audit trail.
- M0-WP26 D02-D Remaining-Edge Manual Reconciliation Batch E is **INDEPENDENT QA PASS WITH ZERO
  FINDINGS / PROVISIONAL EVIDENCE ONLY**. Independent derivation pins the QA-passed
  WP22→WP23-R1→WP24→WP25-R1 prefix and selects exact `eligible[1000:1250]`: 250 rows
  `edge_001505`…`edge_001850`, WP5 orders 2,035…2,284, stems 1512→1513…1867→1868. Pre-batch
  residual is 1,146 rows including two quarantine edges / 1,144 eligible; post-batch residual is
  896 including quarantine / 894 eligible. Coverage is 500 endpoints, 305 unique stems, 997
  endpoint bbox occurrences, 600 unique-stem bbox occurrences, train/test 472/28, proxy tiers
  160 strong/68 uncertain/22 adjacency-only and 55 nonempty sequence IDs. There are zero
  cross-split rows, zero stem `0248` and zero `proxy_sequence_0050` rows.
- PM directly inspected all 50 prepared atlas pages/250 pair panels and re-read every exceptional
  annotated page. Provisional outcomes are 240 `SAME_CAPTURE_CANDIDATE` and 10 `NOT_RELATED`;
  physical-sign outcomes are 239 `SAME_PHYSICAL_SIGN_CANDIDATE` and 11 `NOT_RELATED`, all
  `HIGH`. `edge_001644` is intentionally same-capture/different-physical-sign; ten other exact
  exceptional IDs are hash-pinned in the builder and trusted notes. Official verify is
  `valid=true` with 83 sources, 56 artifacts and 48,503,108 artifact bytes. Manifest SHA-256 is
  `4e0ddff49a83baac0c41e6be28f376d09f2d887fd0742ac2efd439e46fdf62e7`; selection is
  `70f9a1a77172eac59761d642cce2689c9bb5a5ba07dc87cea426f0814be51582`; annotations are
  `be125fcc5b97ad9c0439b09543d00b62edcc1611c0bc750ae6bf7252b6d4ee70`; trusted notes are
  `47178a56aa80d5da39e146e1319dea6015e4361161b1a1fe45b91e973dcdf64d`. Package status remains
  `WP26_AWAITING_QA_REVIEW`. Final PM validation passes 47/47 targeted WP26 tests, 286/286
  remaining-edge compatibility tests and 1,047/1,047 full-suite tests in durable `screen` with
  exit code 0. All 24 CLI package verifiers, Ruff, `uv lock --check` (168 packages) and
  `git diff --check` pass. Graft is rebuilt/check-clean at 72 Python files, 1,354 nodes and 3,528
  edges. Independent QA subsequently returned PASS with 0 findings. Closure is routing-only and
  the hash-pinned WP26 package remains byte-identical at its historical awaiting-QA status; it did
  not approve D-02, split, training or final/transitive group truth.
- Initial M0-WP27 D02-D Remaining-Edge Manual Reconciliation Batch F is **INDEPENDENT QA FAIL /
  IMMUTABLE AUDIT RECORD / PROVISIONAL EVIDENCE ONLY**. It selects exact `eligible[1250:1500]` after the
  QA-passed WP22/WP23-R1/WP24/WP25-R1/WP26 prefix: 250 rows `edge_001851`…`edge_002213`, WP5
  orders 2,285…2,534, stems 1868→1869…2238→2239. Pre-batch residual is 896 rows including two
  quarantine edges / 894 eligible; post-batch residual is 646 including quarantine / 644
  eligible. Coverage is 500 endpoints, 306 unique stems, 1,069 endpoint bbox occurrences, 650
  unique-stem bbox occurrences, train/test 476/24, proxy tiers 127 strong/84 uncertain/39
  adjacency-only and 56 nonempty sequence IDs. There are zero cross-split rows, zero stem `0248`
  and zero `proxy_sequence_0050` rows.
- PM directly inspected all 50 prepared atlas pages/250 pair panels and re-read all 12 annotated
  exceptional pages. Capture outcomes are 247 `SAME_CAPTURE_CANDIDATE` and 3 `NOT_RELATED`;
  physical-sign outcomes are 229 `SAME_PHYSICAL_SIGN_CANDIDATE` and 21 `NOT_RELATED`, all
  `HIGH`. Sequence context is support only and does not create a decision or group truth.
  Official verify is `valid=true` with 88 sources, 56 artifacts and 49,363,156 artifact bytes.
  Manifest SHA-256 is `9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`;
  selection is `3f8915b661bc53df3e2a736bb0dce0481ce95c4ed2c2cdce7e144dfe8b8aadbf`;
  annotations are `ce35afc20a4b8ee2f1fefb86210ea61838123dd4a7b9e58969a33e57bb4d4de9`;
  trusted notes are `2635a14140fb4d7dd82c2a0118707db1553babfafb322285ac36722d5f6a7ff8`.
  Package status remains the historical `WP27_AWAITING_QA_REVIEW`. Independent QA found exactly
  one P2 and zero P0/P1/P3: layout `pair_count=250`/`page_count=50` retained inherited stale status
  `PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`, and the historical verifier
  explicitly accepted/required that literal. Other semantic/raw/coverage checks passed; all
  initial bytes remain immutable.
- M0-WP27-R1 is **PM COMPLETE / AWAITING INDEPENDENT QA** as an append-only layout-status
  correction. It changes only effective layout `/status` to exact
  `PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`; corrected-layout SHA-256 is
  `d7af4b260985215ff70ca8567369f75f96bc63f4bfe8b58f6d5849b77e00e7f3`, semantic-delta SHA-256
  is `a3bb4ced80bae9b3c4124af7e53e16fe1673ca3f1794fdd249f9218accc8fe6e`, and effective-roster
  SHA-256 is `c4b25036ea12820f7d0a9434d93bcea1b2e0461f7dc83878964a69255c8bc741`.
  The roster preserves 55/56 initial artifacts at exact path/hash; selection, lineage,
  annotations, index and all 50 JPEG pixels are unchanged. Official verify is `valid=true` with
  151 sources, 4 correction artifacts, 56 effective artifacts and exactly one changed artifact;
  manifest SHA-256 is `6992625b062649ba979a39eb7e4ef8fd00eadad666558fb40886d520390d96fc`.
  Targeted R1 tests pass 47/47, including exact-status/count types, inherited-176 rollback,
  substitution, path/symlink/ID-swap, coherent rehash/manifest refresh and clean-room 4/4.
  Applicable WP22…WP27-R1 compatibility passes 379/379 after deselecting only immutable WP26's
  obsolete no-WP27 assertion. All 27 verifier entrypoints, Ruff, lock and diff checks pass; Graft
  is rebuilt/check-clean at 76 files, 1,438 nodes and 3,744 edges.
  Status is `WP27_R1_AWAITING_INDEPENDENT_QA`; canonical WP5 remains 3,172 PENDING, all 589
  sequences remain PENDING, 646 residual edges remain including two quarantine / 644 eligible,
  D-02/Gate 0 remain blocked, split/training remain unauthorized, and WP28 has not started.
- M0-WP27-R1 subsequently **FAILED independent QA** with exactly one P2 and zero P0/P1/P3
  (independently reproduced): its `semantic_diff` compared JSON leaves with `==` and `verify()` did
  not pin corrected-layout bytes, so a type-confused layout (`pair_count=250.0`, `slot=true`,
  float bounds, ...) plus a coherent refresh of the R1 delta/roster/report/manifest verified
  `valid=true`. The shipped R1 bytes are correct; R1 stays byte-identical as an immutable
  QA-fail record.
- M0-WP27-R2 is **INDEPENDENT QA PASS (0 P0/P1/P2, 2 non-blocking P3) / VERIFIER HARDENING
  ONLY**. It only adds files and changes zero predecessor bytes: QA record
  `docs/review/wp27_r2_qa_correction_record.md`, `scripts/build_wp27_r2_verifier_hardening.py`,
  34 targeted tests, type-strict audit `d04e74dd…` and manifest
  `01e2993888761793943bdfe0ea3c0d96d58c00b1965fc8cabcc402b7fa77b426`. R2 pins every R1 file by
  constant, requires the effective layout to equal the canonical serialization of
  `corrected_layout(initial)`, a type-strict diff of exactly `/status`, exact `int` type for all
  3,704 count/position/bounds fields, and R1 plus initial WP27 verifiers `valid=true`. The
  effective Batch F layout remains `d7af4b26…`. PM gates: R2 verify `valid=true` (11/2), targeted
  34/34, full suite 1,174/1,174 exit 0 (only immutable WP26 no-WP27 assertion deselected),
  compatibility WP22…WP27-R2 413/413, 28/28 verifier entrypoints with exact CLI contracts (WP4
  reports `status=PASS`), Ruff/lock (168)/diff PASS. A clean-context QA agent ran its own attack
  harness and two clean-room rebuilds (byte-identical). P3s: R2 manifest tolerates duplicate JSON
  keys/non-canonical formatting (inherited); the audit's probe list is declared, proven by tests.
  Closure is routing-only; it does not approve D-02, group truth, split, Gate 0 or training.
- WP28-R2 Batch G and WP29 Batch H are **INDEPENDENT QA PASS (0 P0/P1/P2, 0 new P3)** on
  2026-10-17, recorded append-only in `docs/review/wp28_r2_wp29_independent_qa_record.md`
  (independent selection derivation, 1,000 raw re-hashes, WP28-R2 evidence-binding fixes, all
  50/50 WP29 pages read). Both packages keep their historical `*_AWAITING_QA_REVIEW` strings.
- M0-WP30 final Batch I is **PM COMPLETE / AWAITING INDEPENDENT QA**. It selects the complete
  residual eligible suffix `eligible[2000:]`: 144 edges `edge_002973`…`edge_003176`, 172 stems,
  888 endpoint boxes, 29 pages (5×28 + 4), no stem `0248`. PM read all 29/29 pages: capture 140
  same / 4 not-related (`edge_003047`, `edge_003092`, `edge_003128`, `edge_003153`, scene
  changes); physical 139 same / 5 not-related (those four plus `edge_002977`, out-of-order frames
  as WP29 `edge_002967`, MEDIUM). Verify `valid=true`, 123 sources/35 artifacts, manifest
  `c906e22f…`. After WP30 zero review-eligible edges remain; only `edge_000242`/`edge_000243`
  (quarantine) stay outside overlays. D-02/Gate 0 still blocked; no group truth or split.
- Initial WP30 **FAILED independent QA** (`docs/review/wp30_independent_qa_record.md`): one P1 —
  `edge_003047` (3084/3085) recorded NOT_RELATED capture although the same ride companions
  continue across the scene change — plus one cosmetic P3 (inherited WP12 error strings); 143/144
  decisions agreed. Initial WP30 stays byte-identical as an immutable QA-fail record.
- M0-WP30-R1 is **INDEPENDENT QA PASS (0 P0/P1/P2, 0 new P3)** per
  `docs/review/wp30_r1_independent_qa_record.md` (2026-10-17): append-only one-row overlay
  `docs/review/wp30_r1_edge_decision_correction.csv` changes only `edge_003047` to
  SAME_CAPTURE / NOT_RELATED / MEDIUM; every selection row and evidence ref is rebound to the R1
  atlas (WP28-R1 lesson). Totals: capture 141/3, physical 139/5, confidence 142 HIGH / 2 MEDIUM.
  Verify `valid=true`, 130 sources/35 artifacts, manifest `6de144e8…`; 35/35 package verifiers pass.
  Lesson: a scene discontinuity between adjacent stems is not evidence of a different capture
  without checking for shared riders (stems ~2995–3129 are one ride with out-of-order segments).
- **D-04 part 1 OWNER APPROVED (2026-10-17)**: the 12 one-group rare classes WP34 proposed to drop
  are instead trained with enriched data (`docs/review/d04_owner_decision_part1_record.md`):
  status `EVAL_PENDING_REAL_INDEPENDENT_DATA`, no automatic vehicle behaviour until evaluated on
  real images from another location, synthetic data training-only, their background groups must
  go to the training split. Other 42 classes still pending; G0.8 BLOCKED.
- M0-WP35 is **INDEPENDENT QA PASS** (`docs/review/wp35_independent_qa_record.md`: 0 P0/P1/P2, 4 P3:
  verify passes when the output folder is absent; cut check only covers labelled signs; rotated boxes
  ~8 % loose, so never measure box precision on them; 43:2.7/44 concentration and extra copies of
  common classes from the same 10 groups). WP35 builder rebuilt after the owner rejected sign pasting (D-04 part 1 revision, 2026-10-17):
  only the original frames that contain each class are transformed — rotation ±5°, zoom-in crop
  55–95 % with offset (never cutting a labelled sign, no padding/mirroring), brightness/contrast/
  gamma/saturation/hue ±4, haze, blur, noise, JPEG 50–95, no flip; boxes transformed with the image;
  fallback to no rotation / photometry only for edge signs (99 of 1,800). 150 images per class in
  git-ignored `data/processed/wp35_enrichment/`; labels keep the frame's other train-eligible boxes.
  Deterministic (seed 20261017). Limit: same physical sign as the source; no new instances.
- **DATASET01 GTSRB-style package (2026-10-18, owner request)**, built by `scripts/build_dataset01_crops.py`.
  - Same layout as the German pickles: a dict with `features` (N, 32, 32, 3) uint8, `labels` uint8, `sizes`, `coords`. `sizes` and `coords` are uint16 because crops can exceed 255 px.
  - Crops keep a 10 % border (at least 5 px), clipped to the frame, and are resized bilinear to 32×32.
  - Output goes to the git-ignored `data/processed/dataset01_crops/`:
    - `train.p` holds 12,621 crops (5,415 DATASET01 + 7,206 from WP35 images);
    - `valid.p` holds 560 crops covering 19 classes;
    - `signnames.csv` lists the 54 classes with M1 class-map ids;
    - `*_index.csv` gives each crop's provenance.
  - A committed manifest `docs/review/generated/dataset01_crops_manifest.json` holds the SHA-256 of every array.
  - `test.p` is sealed: it is written only by `export-test --final-eval --reason`, which is logged.
  - Verifier `dataset01-crops`; 6 tests.
  - Limits:
    - WP35 crops repeat the same physical signs and also add extra copies of common classes;
    - 22 classes have no test crops and 35 have no valid crops;
    - 724 crops come from signs under 16 px.
  - This is for the later classifier track (E1–E4). It does not change the detector-first order.
- **M1 started (2026-10-18).** Owner approved adding PyTorch + Ultralytics (stable, exact pins).
  - Done: `scripts/build_m1_yolo_dataset.py`.
    - It holds a committed manifest `docs/review/generated/m1_yolo_export_manifest.json` and the class map `m1_yolo_classes.csv`.
    - The 54 WP33 classes map to YOLO ids in taxonomy order.
    - A split guard checks the WP36-R1 list hashes, the `use` column and the test seal.
    - `export` writes train (1,912 + 1,800 WP35) and val (376) to the git-ignored `data/processed/m1_yolo/`. Images are symlinks.
    - The sealed test is written only by `export-test --final-eval --reason`, which logs to `results/experiments/sealed_test_access_log.jsonl`.
    - Verifier `m1-yolo`; 7 tests.
  - Numpy conflict (verified): ultralytics 8.4.172 on macOS excludes numpy ≤ 2.3.4, but the root pins numpy 2.1.3 for TF E0.
    The owner chose a **separate uv project `detector/`** (2026-10-18).
    - `detector/pyproject.toml` + `detector/uv.lock` with exact pins: torch 2.14.1, torchvision 0.29.1, ultralytics 8.4.172. They resolve to numpy 2.5.4 and opencv-python 5.0.0.93.
    - It has its own `.venv`. The root pyproject/uv.lock, E0 and WP6 are unchanged; their hashes still match the WP6 pins.
  - Detector package `detector/m1/` (run from `detector/` with `uv run python -m m1.cli check|train|evaluate|latency`):
    - `contract.py`:
      - fails closed on the D-05 record hash, the root export manifest and the exported stem lists;
      - holds the D-05 seeds, gates, critical classes and the forced `fliplr=0`;
      - disables Ultralytics telemetry/integrations;
      - logs sealed-test access.
    - `metrics.py`: greedy IoU matching, class-aware and class-agnostic recall, FP/image, val threshold selection (recall ≥ 0.85 with the fewest FP), D-02 group bootstrap and latency stats.
    - `cli.py`:
      - train writes `results/experiments/<run>/run_contract.json`;
      - evaluate refuses the test without `--final-eval --reason` and needs a val-locked `--conf`;
      - latency runs 50 warm-up + 300 measured iterations, batch 1, on MPS.
    - Tests: `uv run pytest` in `detector/`, 7 pass.
  - Smoke-verified on MPS (in the scratchpad, not results/): 1 epoch from scratch on 5 % of the data at 320 px; train, evaluate and latency all ran. Scores were 0 as expected. p95 latency was 15.6 ms at 320 px.
  - Caveats:
    - MPS ops such as scatter_reduce and index_put are non-deterministic (`warn_only`), so runs are not bit-reproducible. Report the seed spread instead.
    - Ultralytics checks PyPI for updates (read-only).
    - **Pretrained COCO weights need a download, which needs owner approval.** Without them, training starts from scratch.
  - Lesson: **README.md is hash-pinned by WP27-R1.** Do not edit it; status goes in the roadmap, memory and app. A README status edit broke the wp27-r1/r2 verifiers and was reverted byte-exact.
- **D-05 OWNER APPROVED → GATE 0 OPEN (2026-10-18)** for the VN full-frame detector track:
  `docs/review/d05_owner_decision_record.md` (all Q1–Q6 recommendations, no overrides; proposal
  pinned `3b0e9bca…`). Authorizes M1 package + 1-seed pilot. Not authorized: PyTorch/Ultralytics
  lock change (separate owner approval), opening the sealed test before final evaluation,
  classifier/OOD gates, deployment. Earlier entry:
- **D-05 PROPOSAL (2026-10-18)**: `docs/review/d05_proposal.md`, detector-first, awaiting owner.
  Recommends D05-B (pilot 1 seed, final 3 seeds), test gates mAP50 ≥ 0.60, mAP50-95 ≥ 0.40,
  class-agnostic recall ≥ 0.85, FP/image ≤ 0.30, per-class recall ≥ 0.70 for 10 critical classes
  and ≥ 0.50 for other classes with ≥ 20 test boxes; group bootstrap CI; val only for pooled
  selection + confidence/NMS; one pre-test gate recalibration allowed; latency p95 ≤ 100 ms batch 1
  on M1 Pro MPS. Facts: val has boxes in only 19 classes (9 with ≥ 20); test 32 classes (22 ≥ 20);
  repo has no PyTorch yet (M1 needs an approved dependency change).
- **G0.9 PASS (2026-10-18)**: WP37-R1 independent QA PASS, 0 findings
  (`docs/review/wp37_r1_independent_qa_record.md`); current dataset card `docs/dataset01_card_r1.md`.
  Gate 0 criteria now 9/9 PASS; Gate 0 opens only after the owner approves D-05 (metric
  thresholds, latency, seeds — set on val). Training still not authorized.
- M0-WP37-R1 was **PM COMPLETE, AWAITING INDEPENDENT QA** (`scripts/build_wp37_r1_dataset_card.py`,
  card `docs/dataset01_card_r1.md` = current dataset card; WP37 pinned and must still reproduce).
  Fixes WP37 QA (PASS, 1 P2, 4 P3): luma buckets are scene content + exposure, the 7 DARK frames
  (1843–1851) are daylight tree-canopy scenes, and the dataset has **no verified low-light/night
  frame**; actual decode sizes (540×960 decoded at full size) and edge strength per resolution;
  ≈37 % small boxes; D-01 attribution exact, creator name unverified, augmentation parent UNKNOWN;
  reviewer observation limited to "most frames", device UNKNOWN.
- M0-WP37 is **INDEPENDENT QA PASS with 1 P2** (`docs/review/wp37_independent_qa_record.md`); G0.9
  waits for WP37-R1. Earlier entry: M0-WP37 G0.9 dataset card was **PM COMPLETE, AWAITING INDEPENDENT QA**
  (`scripts/build_wp37_dataset_card.py`; card `docs/dataset01_card.md`, which supersedes the card
  part of `docs/dataset01_audit.md`). Adds D-01 attribution/license terms, D-02 group lineage per
  group, D-03/D-04 class table with split boxes, WP36-R1 hashes, and measured capture proxies
  (luma/edge on a 480×270 grey JPEG draft; Pillow version pinned in manifest). Finding: the group
  split shifts capture conditions — all 39 portrait 540×960 frames and all 7 DARK frames are in
  val, val has no 1920×1080, val is darker (median luma 106 vs train 118, test 130). EXIF/GPS 0,
  so place/time/weather/device stay UNKNOWN. 48/48 verifiers pass.
- **G0.7 PASS (2026-10-18)**: owner accepted WP36-R1 as the official split
  (`docs/review/g07_owner_acceptance_record.md`; manifest `06425994…`). Sealed test list
  `afa03d4b…` (903 frames, 16 groups): only for an explicit logged final evaluation; any change
  needs a new split version + owner decision. M1 loader checks list hashes and `use`; full verify
  in CI. Gate 0 now 8/9 (G0.1–G0.8); remaining: G0.9 dataset card and D-05 thresholds (on val).
- M0-WP36-R1 is **INDEPENDENT QA PASS** (`docs/review/wp36_r1_independent_qa_record.md`: 0 P0/P1/P2, 1 P3 — `check-candidate` re-runs the full build (~11 s); M1 loader should check manifest + list hashes and leave full verify to CI). Optimal for the owner ordering per QA. Awaiting owner acceptance for G0.7. Was PM COMPLETE (`scripts/build_wp36_r1_group_split.py`,
  report `docs/review/wp36_r1_group_split_report.md`; WP36 pinned byte-identical). Owner chose the
  literal G0.7 ranking (`docs/review/g07_owner_decision_r1_record.md`): ≥2 test groups outranks the
  ±3 band. Result: usable train 1,912 / val 376 / test 903 (59.9 / 11.8 / 28.3 %), 17 classes with
  ≥2 test groups, only class 22 unmet (no val; 25 keeps its test). Test seal `afa03d4b…`. P3 fixes:
  usable-frame ratio, temp-dir candidate check, and an R1 `check-candidate` loader guard that
  rejects quarantined stems, background outside train and list-hash drift — M1 must use it.
  47/47 verifiers pass.
- M0-WP36 G0.7 split is **PM COMPLETE, AWAITING INDEPENDENT QA** (`scripts/build_wp36_group_split.py`,
  report `docs/review/wp36_group_split_report.md`). Owner approved split rules option A
  (`docs/review/g07_owner_decision_record.md`): one-free-group classes 17/18/19/30/40/45/50 → test,
  class 38 → TRAIN_ONLY_UNVERIFIED, ~70/15/15 ±3, class requirements rank above ratio. Result
  (seed 20261018, 120 restarts, deterministic): usable frames train 2,114 /
  val 372 / test 705 (66.2 / 11.7 / 22.1 %); 15 forced-train groups; 24 quarantined negatives
  excluded; 0544 train background; test seal `01bdb989…` in `wp36_split_manifest.json`. Two structural
  conflicts need the owner: option A forces C0048 (411 frames) into test, so test ≥ ~20 % and the
  ±3 band cannot hold; classes 22 and 25 compete for C0032 → class 25 has no test (only unmet
  requirement). `verify` valid; 46/46 verifiers pass. Independent QA PASS (`docs/review/wp36_independent_qa_record.md`: 0 P0/P1, 1 P2, 3 P3). P2-1: objective ranks the ±3 band above the owner's criterion 3 (≥2 test groups); literal ranking gives 17 deep classes, ~59.8/11.6/28.6 %, and class 22 (no val) unmet instead of 25. Owner must choose before sealing. P3: objective uses registry not usable frames; check-candidate does not reject quarantined stems (M1 loader must check the WP36 manifest list hashes); verify writes a temp file into the repo. Not yet G0.7 PASS.
- **D-04 part 2 OWNER APPROVED (2026-10-18)** → **G0.8 PASS**, Gate 0 now 7/9 (G0.1–G0.6, G0.8):
  `docs/review/d04_owner_decision_part2_record.md`, tables `d04_owner_decisions_part2.csv` (42 rows:
  27 TRAIN_VAL_TEST / 6 TRAIN_AND_TEST_NO_VAL / 9 TRAIN_ONLY_UNVERIFIED; dominated 11/14/28/38 marked
  weak evidence) and `d04_owner_negative_frames.csv` (0544 background; 24 quarantined until a
  derived relabel). Remaining before training: G0.7 split, G0.9 dataset card, D-05 thresholds.
- M0-WP34-R1 is **INDEPENDENT QA PASS** (`docs/review/wp34_r1_independent_qa_record.md`: 0 P0/P1/P2,
  2 wording P3, fixed; QA addendum confirms PASS with 0 open P3 on final notes `487b78e4…`). Earlier entry:
  M0-WP34-R1 was **PM COMPLETE, AWAITING INDEPENDENT QA** (`scripts/build_wp34_r1_d04_support_and_negatives.py`,
  report `docs/review/wp34_r1_d04_support_and_negative_audit_report.md`; initial WP34 pinned and
  byte-identical). Verify `valid=true`, 29 artifacts, notes `487b78e4…`. Part A: 27 KEEP_FULL /
  6 KEEP_TRAIN_AND_TEST_NO_VAL / 9 KEEP_TRAIN_ONLY_UNVERIFIED / 12 OWNER_TRAIN_WITH_ENRICHMENT
  (owner part 1); 42 classes PENDING; P.117 (3 keys) and W.239b (2 keys) marked as height
  families; box-share dominance > 80 % flagged for 11, 14, 28, 38. Part B (re-reviewed at 1,600 px
  with raw zooms): **only 0544 is a true negative → DETECTOR_BACKGROUND**; the other 24 are
  QUARANTINE_UNTIL_RELABELLED (1703–1708 = 39 40, cls10 hidden; 2766 = 13; 2793–2797 = 50;
  2015–2017/2031/2051 = 32; 2999 = 6 13 38). Disagrees with QA on 2723: a distant blue cls46 disc
  is visible where 2724 labels it, so it is quarantined (LOW confidence) instead of background.
- M0-WP34 **FAILED independent QA** (`docs/review/wp34_independent_qa_record.md`: 1 P1, 1 P2, 4 P3).
  P1: 2015–2017, 2031, 2051 show a cls32 (P.123b) disc → not true negatives; only 0544 and 2723
  remain usable as background. 2793–2797 should be UNLABELLED (cls50). P2: per-key D-04 rule splits
  the P.117/W.239b height family (train-only "2.0 m" would mislabel 2.2/2.5 m); offer family-level
  options. P3: wrong class fields (1703–1708 → 39 40; 2766 → 13), UNCLEAR handling, ambiguous
  group-share column, downscaled atlas. Support counts re-derived exactly. Needs WP34-R1.
  Original entry: WP34 was PM complete.
  Part A, D-04 support on WP33 labels × D-02 groups (rule: ≥3 groups KEEP_FULL; 2 groups
  KEEP_TRAIN_AND_TEST_NO_VAL; 1 group ≥30 images KEEP_TRAIN_ONLY_UNVERIFIED; else
  DROP_FROM_V1_COLLECT_MORE → UNKNOWN eval): 27 / 6 / 9 / 12 of 54 classes; owner status PENDING.
  Part B, negative audit: of the 25 empty-label frames only 7 are true negatives; 13 contain an
  unlabelled sign (0060, 0061, 0187, 1514, 1515, 1703–1708, 2766, 2999) and 5 are unclear
  (2793–2797). Proposed: only true negatives may be detector background.
- **G0.5 PASS (2026-10-17)**: owner confirmed the D-03 records (part 1, part 2 + revision) authored
  in the linked side session; WP33 derived labels are **INDEPENDENT QA PASS**
  (`docs/review/wp33_independent_qa_record.md`: 0 P0/P1/P2, 4 P3; no disagreement on class 23 or
  height values). Training labels must come from `wp33_derived_boxes.csv`, never raw class ids.
  Gate 0 now 6/9 PASS (G0.1–G0.6); still blocked by D-04/G0.8, G0.7 split, G0.9 card, D-05.
- M0-WP33 D-03 derived label set (`scripts/build_wp33_derived_labels.py`) was **PM COMPLETE**: box table `docs/review/generated/wp33_derived_boxes.csv` (8,334 boxes, 8,290
  train-eligible), taxonomy `wp33_derived_taxonomy.csv` (54 trainable keys before D-04). Owner
  revised class 23 from "split P.111a–d" to one combined class P.111a+P.111b, since all 465 boxes
  show moped + motorised three-wheeler in one circle. Heights split: P.117 2.0/2.2/2.5 m, W.239b
  2.5/2.7 m; 4 unreadable (2088:2, 2278:2, 2279:2, 0776:7 ex-class-18) excluded. Class 31 → UNKNOWN
  eval only. Raw labels read-only and hash-checked. Atlases in `docs/review/assets/wp33/`.
- **D-03 decisions COMPLETE (2026-10-17)**, part 2 `docs/review/d03_owner_decision_part2_record.md`:
  12 one class; 19/35/36/49 separate composite classes; 23 split into P.111a–d; 25/28/30 kept as
  renamed S.505a supplementary classes; 31 routed to UNKNOWN (eval only); speed limits one class
  per value; height signs 16/43 split by value; UNKNOWN = threshold rejection, no trained class.
  G0.5 stays BLOCKED until a derived label set implements: P.111a–d relabel, height-value
  relabel, and the stem 0776 line 7 class-18 fix (raw immutable).
- **D-03 part 1 OWNER APPROVED (2026-10-17)**: 42 low-risk WP8 rows reviewed class by class
  (`docs/review/d03_owner_decision_part1_record.md`, table
  `docs/review/generated/d03_owner_decisions_part1.csv`): 40 accepted as proposed, classes 3 and
  24 keep current names. Follow-up: stem 0776 line 7 labelled class 18 is a height-limit sign
  (fix in derived labels only). Pending: rows 12,19,23,25,28,30,35,36,49 (semantic), 31 (out of
  scope), parameterized/S.505a/UNKNOWN policies. G0.5 still BLOCKED.
- **D-01 OWNER RISK ACCEPTED (2026-10-17)**: owner accepted the license risk instead of waiting
  for the author. Conditions: project research/coursework/simulation use only; attribute
  `thanhhiepvos/vietnam_traffic_sign@d869116` + archive hash everywhere; derivatives only under
  CC-BY-SA 4.0; no redistribution of raw images/labels outside the project; attribute and re-check
  before any model release; re-open on author reply/takedown. Record
  `docs/review/d01_owner_decision_record.md`, builder `scripts/build_d01_owner_decision.py`. G0.1 PASS.
- **D-02 OWNER APPROVED (2026-10-17): option D02-P1** — the 54 WP31-R2 capture groups are the
  DATASET01 `group_id`. Append-only record `docs/review/d02_owner_decision_record.md`, overlay
  `docs/review/generated/d02_owner_decision_overlay.json`, registry
  `docs/review/generated/d02_group_id_registry.csv` (3,215 stems; 0248 has no group), builder
  `scripts/build_d02_owner_decision.py` (pins WP31-R2 lineage; `check-candidate` rejects a split
  that shares a group across splits, contains 0248 or unknown stems). G0.6 is now PASS. Gate 0
  still BLOCKED by D-01, D-03, D-04, D-05 and G0.7 (group-aware split not yet generated).
- M0-WP31-R2 is **INDEPENDENT QA PASS** (`docs/review/wp31_r2_independent_qa_record.md`: 0 P0/P1,
  1 P2, 1 P3). Capture level (D02-P1, 54 groups) is fit to offer the owner. Scene level (D02-P2)
  only after the report discloses that R2 also splits R1 scene S0059 at `edge_002901` (re-merge
  rule is not monotone; QA found the split correct) and labels the R1 re-merge count (P3).
  Original R2 entry: `scripts/build_wp31_r2_group_id_proposal.py` was PM complete: fixes the R1 scene P2 by joining BOTH bounding scenes of all 12 negative runs; capture
  groups identical to R1 (54); scene groups 61; documents R1 P3-1 (WP32 NO_LINKs on the nine
  C0079 edges do not override upstream SAME_PHYSICAL records) and P3-2 (scene ≈ capture).
- Independent QA (`docs/review/wp31_r1_wp32_independent_qa_record.md`): **WP32 PASS** (71/71 agreed,
  1 P3: atlas shows decisions). **WP31-R1 PASS at capture level**; scene level has one P2: the
  scene rule attaches negatives to the preceding scene, but 1514/1515, 2015–2017 and 2051 visually
  belong to the following scene (scene-level leak); P3s: WP32 NO_LINKs do not override upstream
  SAME_PHYSICAL edges (C0079), and scene groups add little over capture groups. Capture groups
  (D02-P1) are QA-ready for the owner; scene groups (D02-P2) need a fix first.
- M0-WP32 cross-block link review and M0-WP31-R1 corrected group_id proposal were **PM COMPLETE**
  (2026-10-17). WP32 (`scripts/build_wp32_cross_block_link_review.py`)
  generated 54 cross-group candidates (near-duplicate 32×18 thumbnail MAE < 0.35 or same-class box
  geometry) plus 9 flagged C0079 edges and 8 C0079 sub-sequence pairs; PM read all 18 pages / 71
  pairs: 52 same/same, 11 same-capture/different-sign (all 9 C0079 edges: the visor sub-sequence
  shows a different cls23 pole), 7 not related, 1 same/unresolved. Notes pinned. WP31-R1
  (`scripts/build_wp31_r1_group_id_proposal.py`) pins every input (incl. initial WP31 and WP32),
  applies WP32 links (31 capture merges) and re-merges interleaved sibling scenes sharing a class:
  capture 54 groups (largest 513, 16.0%), scene 63 (largest 468, 14.6%), only 4 effective scene
  cuts; 23 classes have < 3 independent groups (class 49 = 1, class 29 = 1). Every group mixes
  vendor train/test. Limits: cross-block candidates only cover near-identical views.
- M0-WP31 D-02 group_id proposal **FAILED independent QA** (`docs/review/wp31_independent_qa_record.md`:
  0 P0, 2 P1, 1 P2, 2 P3). P1-1: filename blocks of different rides interleave, so adjacency-only
  linking puts one ride/physical sign in several capture groups (cls49 junction across C0004…C0020,
  cls29 sign across C0062…C0072); class-support counts are overstated. P1-2: scene re-merge skips
  interleaved siblings (C0079 cls23, C0082 cls6) and WP27-R2/WP14 edges around 2070–2112 are
  internally inconsistent. P2: verifier does not pin its sources. Next: cross-block linking review
  before any D-02 option is leak-safe. Original WP31 entry follows.
- M0-WP31 D-02 group_id proposal was **PM COMPLETE / AWAITING INDEPENDENT QA AND OWNER D-02**
  (`scripts/build_wp31_group_id_proposal.py`, report `docs/review/wp31_group_id_proposal_report.md`).
  Deterministic re-derivation from the QA-passed overlays (WP5…WP30-R1) via `dataset_graph`;
  verify re-renders all 7 artifacts byte-for-byte. Capture level `D02-C`: 85 groups, largest 513
  frames (16.0%), 80 mixed train/test. Scene level `D02-S`: 99 groups, 40 effective cuts at
  physical-sign NOT_RELATED edges, non-adjacent out-of-order scenes re-merged by boundary-frame
  class overlap, largest 239 (7.4%). 18 classes have < 3 independent groups (input for D-04).
- Data-structure finding (WP31): WP5 has **no proxy edge** next to the 25 empty-label frames
  (inventory split `unassigned`, not test), leaving 12 negative runs / 37 consecutive pairs never
  reviewed. WP31 bridges them at capture level (leak-safe) and lists them in
  `docs/review/generated/wp31_unreviewed_negative_gaps.csv`; they should be reviewed visually before
  D-02 is finalized. `dataset_graph` still maps non-train to test, so its view counts the 25
  negatives as test.
  Known test hygiene risk: WP9/WP10/WP11 tests call `build(REPO_ROOT, …)` and rewrite repo
  artifacts during the full suite; their verifiers still pass afterwards (deterministic bytes).

## Product milestone status

Snapshot 2026-10-18 (details in the dated entries under "Verified current state").

- **M0 Data governance: Gate 0 criteria 9/9 PASS.**
  - G0.1 license: D-01 risk accepted.
  - G0.2–G0.4: staging, pairing, 0248 quarantine.
  - G0.5 taxonomy: D-03 + WP33, 54 trainable classes, class 31 → UNKNOWN.
  - G0.6 groups: D-02, 54 capture groups.
  - G0.7 split: WP36-R1 owner-accepted; test sealed `afa03d4b…`.
  - G0.8 rare classes: D-04 parts 1+2.
  - G0.9 dataset card: WP37-R1, `docs/dataset01_card_r1.md`.
- **Gate 0 OPEN (2026-10-18)**: D-05 approved (`docs/review/d05_owner_decision_record.md`).
  Training of the VN detector is authorized under D-05 once M1 exists; no VN model trained yet.
- **Next, by owner priority (detector first):**
  1. PyTorch/Ultralytics are owner-approved in the separate `detector/` project. Initial M1 QA,
     M1-R1 and M1-R2 all FAILed fail-closed. R2 closed the prior registry/threshold/data-roster
     bypasses. R3 closed primitive numeric/schema attacks but QA found two High cross-field gaps:
     metric/gate claims could contradict confusion/AP evidence, and latency could use a different
     image size/conf/NMS. M1-R4 adds primary integer counts, confusion/AP reconciliation and an
     exact per-seed latency-to-test configuration binding, with 53 detector tests. M1-R4 received
     independent QA PASS with 0 findings (`docs/review/m1_r4_independent_qa_record.md`, SHA-256
     `2c5416ebfb041ea13ec5f6eab0582c37d0e5257f07b6cdc73dd097466a30d0e9`). The M1 QA blocker is
     closed; next is the Owner-authorized source checkpoint, then the private train/val Colab path.
  2. Owner selected Colab with private train/val upload and dual baselines. Q1 was clarified as
     `Có` on 2026-10-18. Official Ultralytics `yolo11s.pt` was downloaded locally, kept outside
     Git, loaded successfully and pinned by SHA-256 `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`.
  3. M4/D1 starts with a 1-seed pilot on val, then 3 seeds, then one sealed-test evaluation. The 54-class baseline stays under current D-05; the one-class-plus-classifier baseline needs a gate addendum before sealed-test use.
  4. The detector prototype in the app comes after that. The classifier track (E1–E4), video and CARLA come later.
- Existing MVP is unchanged: UV environment, Streamlit (project status, DATASET01 tab and E0 simulation), cropped GTSRB classifier E0 (frozen control) and simulated behaviour.

## Durable decisions

1. **Detector-first sequencing (owner, 2026-10-17; supersedes classifier-first).** The VN
   full-frame detector (M1 → M4/D1) comes before the classifier study (E1–E4) and the in-app
   prototype. Temporal logic, lane control and CARLA come after the detector passes D-05.
2. **Evidence-bounded naming.** Keep the downloaded filename for provenance, but describe the
   architecture as VGG-inspired CNN.
3. **No arbitrary UNKNOWN threshold.** Select rejection behavior from validation evidence and
   evaluate supported, unsupported, non-sign, and difficult-image groups separately.
4. **Separation of concerns.** Detector finds ROIs; classifier labels cropped ROIs; temporal logic
   stabilizes events; planner produces simulation intent; simulator/control executes it.
5. **Optional heavy dependencies.** Ultralytics/PyTorch enter only at the detector milestone;
   CARLA is added only after the simulator version/platform is fixed.
6. **One environment.** Use the root `.venv/`; do not recreate the former `venv` plus symlink
   arrangement that existed for the iCloud checkout.
7. **Graft-first source work.** Use Graft for orientation, symbol/API lookup, callers/callees, and
   blast radius; end source tasks with a fresh graph check.
8. **Data gate before training.** Do not train on DATASET01 until provenance/license, staging
   integrity, taxonomy, negatives and group-aware train/val/test splits pass Gate 0.
9. **Frozen control.** E0 is a reference-only GTSRB artifact. Every new run receives a new
   experiment ID, config, dataset/split hash and output path.
10. **Group-aware evaluation.** Adjacent frames or the same physical sign/scene must not cross
    splits. Filename proximity is only a leakage proxy; true group metadata is required.
11. **Matched evidence.** Do not call E1–E4 or a detector “better” without an independent holdout
    on the same taxonomy/protocol and the required per-class/calibration/latency metrics.

## Current risks and technical debt

- License/ownership of DATASET01 is unconfirmed by the author (D-01 risk accepted; re-open on any claim).
- Group truth is AI-inferred (D-02). The same physical sign may appear in two groups, so test scores may be optimistic.
- Validation set:
  - It is small: 376 frames, with boxes in only 19 classes.
  - Its capture conditions differ from train and test: all portrait frames are in val, and val has no 1920×1080 frames.
  - Model selection must use pooled metrics.
- 22 classes have no sealed test (12 enriched, 9 train-only, class 38). They stay "unverified" until real independent images exist.
- There is no verified low-light/night frame. Night/rain performance is UNKNOWN.
- 24 negatives with unlabelled signs are quarantined until a derived relabel exists. Only 0544 is background.
- About 37 % of boxes are smaller than 0.1 % of the image area; detector input size must handle small signs.
- PyTorch/Ultralytics are installed only in the separately pinned `detector/uv.lock`; the root
  TensorFlow lock remains the E0 environment. Independent M1 QA is still pending.
- 7 obsolete "no successor package" tests fail because later WPs now exist.
- More than 130 files are changed and uncommitted.
- Behaviour output is simulation only. The E0 classifier is GTSRB-only and is not valid for Vietnam.

## Immediate PM gate

Gate 0 is **OPEN** for the VN detector track (D-05 approved 2026-10-18). Before the first training run:

1. Independently QA the M1 YOLO export, Dataset01 crop export and detector package.
2. Use only the locally pinned official `yolo11s.pt`; do not publish it or silently replace it.
3. Implement the owner-approved private Colab train/val path with auditable logging; the sealed
   test remains local and unopened.
4. M1 must enforce:
   - the WP36-R1 `check-candidate` / list hashes;
   - test access only in a logged final evaluation;
   - WP33 labels, with WP35 images train-only;
   - no horizontal flip.

Owner follow-up records dated 2026-10-18:
`m1_pretrained_weights_owner_response_record.md`,
`m1_pretrained_weights_owner_decision_record.md`,
`m1_colab_training_owner_decision_record.md`, `d1_dual_baseline_owner_decision_record.md`,
`m1_dependency_decision_record.md` and `git_checkpoint_owner_decision_record.md` under
`docs/review/`.

Do not commit, push, deploy, upload or publish unless the user requests that action separately.

## Canonical documents

- `README.md`: setup, run commands, project overview, and user-facing boundaries.
- `docs/product_roadmap.md`: milestones, status, acceptance criteria, and next sprint.
- `docs/initial_model_assessment.md`: quantitative evaluation, defects, and go/no-go decision.
- `docs/model_provenance.md`: artifact hash, architecture, training log, and evidence boundary.
- `docs/drive_inventory.md`: Drive IDs, hashes, imported files, and exclusions.
- `docs/dataset01_audit.md`: M0-WP1 dataset card, staging proof, technical audit, provenance and
  current G0.1–G0.9 status.
- `docs/vietnam_taxonomy_mapping.md`: unapproved 52-class Vietnam↔GTSRB mapping worksheet.
- `docs/review/m0_wp2_decision_packet.md`: historical decision-ready evidence/options for D-01…D-05
  and G0.4 bbox 0248; D-01…D-05 remain pending, while WP10 append-only overlay supersedes G0.4.
- `docs/review/wp3_provenance_and_fallback_report.md`: WP3 primary-source provenance escalation,
  fallback candidate audit and claim classifications; evidence package QA PASS, decisions remain
  pending.
- `docs/review/dataset_owner_outreach_draft.md`: unsent outreach questionnaire; sending requires
  separate explicit user authorization.
- `docs/review/experiment_acceptance_template.md`: unapproved metric/latency/seed-budget bundles.
- `docs/review/wp7_cross_split_review_batch_a_report.md`: separate 100-pair PM visual-review
  pilot awaiting independent QA; not final group truth and not a WP5 status mutation.
- `docs/review/wp8_taxonomy_recommendation_report.md`: complete 52-row PM recommendation matrix,
  required conflict register and proposal-only D-03 boundary; M0-WP8-R1 QA PASS with 0 blockers,
  but only as a proposal/evidence package: all 52 rows remain `UNAPPROVED`, D-03 remains `PENDING`,
  Gate 0 remains `BLOCKED`, and `training_authorized=false`.
- `docs/review/wp10_g04_quarantine_report.md`: owner-approved whole-stem 0248 quarantine,
  append-only decision lineage and fail-closed candidate split/training exclusion; QA PASS with
  `0 blockers`, while the immutable package retains its historical pre-QA status strings.
- `docs/review/wp11_d04_rare_class_report.md`: deterministic 52-class/20-class-scope D-04
  decision-support package with complete class-44/class-51 lineage and atlas; independent QA PASS
  with `0 blockers`, package only, while all owner decisions remain pending.
- `docs/review/wp12_cross_split_review_batch_b_report.md`: repaired 250-pair D02-B Batch-B
  double-reviewed provisional review package; M0-WP12-R1 QA PASS with 0 blockers, not group truth.
- `docs/review/wp13_cross_split_review_batch_c_report.md`: next 250-pair D02-B Batch-C
  double-reviewed provisional package; M0-WP13 QA PASS with 0 blockers, not group truth.
- `docs/review/wp14_cross_split_review_batch_d_report.md`: exact next 250-pair D02-B Batch-D PM
  provisional package; 50/50 PM readback complete and independent QA pending, not group truth.
- `docs/review/wp24_remaining_edge_batch_c_report.md`: exact next 250-edge D02-D Batch-C PM
  provisional package after QA-passed WP22/WP23-R1 prefixes; awaiting independent QA, not group
  truth.
- `docs/review/generated/`: reproducible grouping proxy, taxonomy, rare-class and bbox evidence.
- `docs/pm_handoff_2026-10-03.md`: full old-PM handoff, repository-integrity findings, and
  Graft/environment details captured during the transition.
- `results/evaluation/gtsrb_test_baseline/`: reproducible baseline evaluation outputs.
- `results/experiments/E0_GTSRB_baseline/manifest.json`: frozen-control hashes, metrics and
  evidence boundary for E0.
- `results/data_audit/DATASET01_052bc980a7206f8d/`: audit JSON/CSV, manifests, provenance,
  grouping proxy and source-preservation proof.

## Known-good commands and latest readback

Run from the Desktop checkout:

```bash
python main.py
./scripts/bootstrap.sh
uv run cpv301 info
uv run cpv301 predict tmp/00000.png
uv run cpv301 evaluate
uv run python scripts/audit_e0_compute_readiness.py verify --repo-root .
uv run python scripts/build_wp7_cross_split_review_batch.py verify --repo-root . --raw-root '<DATASET01 staging raw>'
uv run python scripts/build_wp8_taxonomy_recommendation.py verify --repo-root .
./scripts/run-web.sh
uv run ruff check src tests
uv run pytest -q
uv lock --check
uv run python scripts/run_parallel_checks.py verifiers
uv run python scripts/run_parallel_checks.py tests
```

Local DATASET01 copy (2026-10-17): `data/raw/DATASET01/` (git-ignored) is an rsync copy of the
iCloud `CPV301/Data/DATASET01` folder (archive.zip, archive/, staging/). Readback: 13,927/13,927
files, 0 SHA-256 mismatches, archive SHA-256 `052bc980…cbaa76`. The iCloud original is kept and
stays the path the hash-pinned tests/verifier defaults and WP1 provenance record; do not delete or
move it. `run_parallel_checks.py verifiers` now defaults to the local raw root; 33/33 verifiers
pass against it.

Parallel checks (added 2026-10-17; new files only, no pinned builder/test/`pyproject.toml`/`uv.lock`
byte changed, so WP6's pins still verify):

- `verifiers` runs 33 package verifier CLIs (WP3–WP29, including R1/R2 and QA-fail records) as
  separate processes, `--jobs` default `cpu_count-2`; WP4 passes on `status=PASS`, all others on
  `valid=true`. Readback: 33/33 PASS in 67.5 s wall vs 451 s summed (jobs=8).
- `tests` runs the WP9/WP10/WP11 suites serially first (they `build(REPO_ROOT, …)`), then the rest
  via `uv run --with pytest-xdist==3.8.0 … -n N --dist loadfile`. `tests/conftest.py` fails those
  three suites fast under xdist. Readback: 1,328 passed/6 failed (serial 11 s + parallel 781 s);
  the 6 are the known immutable "no successor WPxx exists" assertions in WP26/WP27/WP27-R1/WP28/
  WP28-R1/WP28-R2, which fail identically when run serially.
- CUDA/MPS are intentionally not used for WP work: ~90% of verify time is Pillow CPU atlas
  re-rendering whose bytes are hash-pinned; a GPU path would change pixels. TensorFlow 2.20 here
  sees CPU only (WP6); GPU becomes relevant only for post-Gate-0 training.

Readback on 2026-10-03 in the Desktop checkout:

- Ruff: pass.
- pytest: `10 passed`; one Starlette deprecation warning.
- `uv lock --check`: pass; 167 packages resolved.
- `cpv301 info`: model exists at the Desktop checkout; threshold `0.5`; both project notebooks found.
- `python main.py --headless --port 8599`: Streamlit started and `/_stcore/health` returned `ok`;
  the temporary verification server was then stopped.

Readback on 2026-10-10:

- Repository gate after M0-WP2 QA repair: Ruff pass on `src tests scripts`; pytest `53 passed` with the
  existing Starlette deprecation warning; `uv lock --check` pass with 167 packages resolved.
- Git: `DEV/Rroject_Pineline` at `dee2b82`, tracking `origin/DEV/Rroject_Pineline`.
- Graft: rebuilt after the WP5 manifest repair to 26 Python files, 351 nodes and 943 edges; `graft check .` is in sync;
  deep layer not built. WP5 build/verify are reached only from the WP5 CLI `main()` entrypoint and
  have no caller from the runtime API/Streamlit source modules.
- DATASET01: `shasum -a 256 archive.zip` matches the recorded hash; `unzip -tq archive.zip`
  reports no errors; archive counts are 3,216 JPG and 3,216 labels.
- Dataset audit: 52 observed classes, 8,334 boxes, 25 empty labels, 2,552 train, 639 test,
  no validation, and 1,031/3,178 cross-split numeric-neighbor pairs.
- M0-WP1: technical audit PASS; source preservation `unchanged=true`; normalized copies are
  separated under staging `generated/`; Gate 0 remains BLOCKED and no final split/training ran.
- QA repair: audit-specific suite `14 passed`; WP2-specific suite `29 passed`; current WP1 manifest
  verifies `valid=true` with zero mismatches; source comparison readback remains `unchanged=true`.
- M0-WP2 builder readback: 589 candidate sequences, 52 unique taxonomy rows, 52 unique rare-class
  rows, 20 class-keyed D-04 records and a bbox review artifact. D-04 aggregate and every class
  remain pending; the 12-artifact WP2 manifest verifies without mismatch. Two consecutive builds
  reproduced manifest SHA-256 `506ec141bef032282f90b3d35741ece49a43fed617c3dea93863d4c32330a505`;
  generated Draft 2020-12 schema validation returned zero errors. Validation details are recorded
  in the WP2 packet handoff and must be refreshed after future edits.
- M0-WP3 re-review repair readback: 589 proxy-only grouping rows/24 contact sheets, 52 unapproved
  taxonomy rows/13 atlas pages and 2,325 source-lineage rows re-hashed against raw. All 37 JPEG
  reviewer sheets passed Pillow decode; grouping batches 001/017/024 and taxonomy pages 008/013,
  plus crowded taxonomy page 011, were visually read back with complete metrics/conflict flags.
  The portable 47-artifact manifest verifies 9 source inputs and 5 controls with `valid=true`, zero
  mismatches, 21,576,108 bytes, and deterministic SHA-256
  `8b2e9ef3b2418623eb92673f3c58591e29f5ed7479bca2b03582c12ef0191dcd`. Cross-root manifest-byte
  reproducibility and artifact/source/control tamper failures are regression-tested.
- Repository gate after WP3 re-review repair: Ruff pass on `src tests scripts`; pytest `77 passed`
  with the existing Starlette deprecation warning; `uv lock --check` pass with 167 packages
  resolved.
- M0-WP4 repair readback: pinned QCVN PDF 403 pages/SHA-256 `b6b99d0a...`; independently pinned
  52-row evidence index SHA-256 `62233e56...` with 39 page fingerprints; worksheet 52 unique rows
  with counts 31 exact/14 partial/6 mismatch/1 not-found; all 52 rows `UNAPPROVED`. Atlas 13 pages
  now has 156/156 visible target bbox overlays and 156-row reconstructable lineage across 152 unique
  source stems. Required `0248` is class-49 slot 1 with exact raw hashes, line 1/index 0 and
  18.00048-px right overflow rendered across a cyan source boundary into gray hatch padding.
  Manifest schema v2 SHA-256 `c60c0901...` verifies 13 sources and 20 artifacts. WP4 targeted tests
  passed 26 cases, including required-0248/substitute rejection, re-hashed semantic citation/index
  and pixel/geometry tamper failures. Full repository gate on 2026-10-10: Ruff passed on
  `src tests scripts`, all 103
  collected tests passed with the existing Starlette deprecation warning, `uv lock --check`
  resolved 168 packages, and `git diff --check` passed. `QA-M0-WP4-R2` subsequently reported PASS
  with 0 blockers on HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` and the uncommitted
  worktree. This closes only WP4 package QA; it does not approve taxonomy or Gate 0.
- M0-WP5 repaired build readback: 3,178/3,178 adjacency edges, 1,031/1,031 cross-split edges prioritized
  first, 589/589 sequence rows linked to WP3, and 128 readable pair-atlas pages. Six visually
  inspected pairs have complete reviewer/time/confidence/rationale/evidence fields; all 3,172
  remaining edges and all 589 sequences fail closed as `PENDING`. The 137-artifact manifest
  schema-v2 verifier enforces its exact 11-source/control allowlist, exact 137 non-manifest
  artifacts, declared counts/bytes, decision boundary and all 3,216 raw image/label hashes. The
  WP5-specific suite passed 26 tests, adding removal, duplicate, extra-valid-file, forged-count,
  forged-bytes, missing first/middle/last page, path/root and type-negative cases. Two clean builds
  reproduced manifest SHA-256 `f8d620a3cbb3b500153f6685b94a9936a8f83eb6f5399ce0a2e8be77982d4b80`
  with 137/137 artifact hashes identical. This is a reviewer queue and partial adjudication only;
  it does not resolve D-02 or Gate 0.
- `QA-M0-WP5-R1` subsequently reported PASS with `0 blockers` on HEAD
  `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` plus the current uncommitted tree. This closes
  package QA only: 3,172 edges remain `PENDING` (including 1,026 cross-split), all 589 sequences
  remain `PENDING`, provisional components are not final group truth, D-02 remains `PENDING`,
  Gate 0 remains `BLOCKED`, and `training_authorized=false`. No split mutation or training ran.
- Repository gate after the WP5 manifest repair: Ruff passed on `src tests scripts`; all 129 collected tests passed
  with the existing Starlette deprecation warning; `uv lock --check` resolved 168 packages;
  `git diff --check` passed; Graft is in sync.

Readback on 2026-10-11:

- M0-WP6-R2 promote/verify produced status `WP6_AWAITING_QA_READ_ONLY_PREFLIGHT`; verifier returned
  `valid=true`, zero errors, 20 exact source records and 3 non-manifest artifacts. The WP6 suite
  passed 29 tests. In addition to prior negatives, the isolated-root regression now performs the
  complete QA bypass attempt: replace all 300 values with 999 ms, recompute statistics/fingerprint,
  call `build_benchmark_attestation`, regenerate report, refresh every manifest artifact hash/size,
  and confirm rejection by `trusted attestation source anchor mismatch`. Deletion, substitution,
  old attestation and unpinned-candidate promotion are also rejected.
- Independent milestone `QA-M0-WP6-R2` subsequently returned PASS with `0 blockers` on HEAD
  `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` plus the current uncommitted tree. QA observed
  29/29 targeted and 158/158 full tests passing; Ruff, lock, diff and Graft also passed. The PASS
  closes only the local read-only WP6 package and does not change any Gate 0 decision.
- E0 model, GTSRB train/valid/test, E0 manifest, four evaluation artifacts, decision status and
  inactive acceptance template still match their pinned SHA-256 values. The preflight did not
  train, calibrate, select a threshold, mutate a split, promote a model or change a decision.
- M0-WP7 Batch A build/verify selected exactly 100 pending cross-split WP5 pairs in canonical
  order and rendered 20 pages with five large side-by-side source pairs per page. All 20 final
  pages were visually read back after build with decision text and bbox/context visible. Outcome
  counts are 98 `SAME_CAPTURE_CANDIDATE` and 2 `NOT_RELATED`; confidence counts are 99 `HIGH`
  and 1 `MEDIUM`. The exact 9-source/25-artifact manifest verifies `valid=true` with SHA-256
  `73ed4095a1f59b72f010fd87b63c4a7f0b16bcf8e0c667ec77576ec827e5d7f2`; verifier tests reject
  roster/order/count/bytes/path/symlink and coherently re-hashed selection/annotation/layout/note
  tampering. WP7-specific tests passed 20/20; the full repository gate passed 178/178 tests plus
  Ruff and `uv lock --check` (168 packages). Graft is in sync at 30 files/464 nodes/1,299 edges.
  Independent milestone `QA-M0-WP7` subsequently returned PASS with `0 blockers`: 100/100 blind
  capture-outcome agreement, 97 physical-sign candidates plus 3 physical-sign `NOT_RELATED`, and
  20/20 atlas pages reviewed. This closes only the double-reviewed provisional Batch-A evidence;
  it does not modify WP5 or authorize final/transitive grouping truth, relabeling, split,
  threshold selection or training.
- M0-WP12-R1 build/verify readback: exact selection `edge_000315`…`edge_001033`, 250 pairs,
  500 endpoints, 1,553 boxes, stem 0248 absent, 50 pages, exact 12-source/56-artifact roster and
  manifest SHA-256 `8e576954bc3de456704aecdb67e8625d8621ca017fb08e3b866635db6afcc0f0`.
  The expanded WP12 suite passes 55/55 tests, including exact atlas roster, isolated index/JPEG/
  layout regeneration, bounds/geometry, pixel/index tamper and coherent `edge_000539` rollback.
  Full repository validation passes 391/391 tests plus Ruff, lock and diff; the existing Starlette
  deprecation warning remains nonblocking. Graft was rebuilt/check-clean at 40 files, 755 nodes and
  2,082 edges; optional deep meaning remains unbuilt. PM post-repair visual readback covered all
  50/50 atlas pages with complete rows, overlays, decision text and no observed clipping. This is
  Independent QA subsequently passed the package with 0 blockers after rejecting all 18/18 attack
  classes. This remains provisional evidence, not D-02/group/split/training approval.
- M0-WP13 build/verify readback: exact selection `edge_001041`…`edge_001882`, 250 pairs,
  500 endpoints, 1,079 boxes, stem 0248 absent, 50 readable post-annotation pages, exact
  16-source/56-artifact roster and manifest SHA-256
  `5db80e215f318a6b782d813b4560c20e35e4f3e51ef0423d7298f4818ea3db65`. The 60 targeted tests
  and 450/450 full-suite tests pass, including clean-room regeneration and coherent source-note
  rollback rejection. Independent QA then passed WP13 with 0 blockers after rejecting 18/18 CLI
  attacks, independently reading 50/50 pages and 250/250 panels, and reproducing 56/56 artifacts
  byte-identically. This QA PASS does not alter D-02/Gate 0 authorization.
- M0-WP14 build/verify readback before independent QA: exact selection
  `edge_001894`…`edge_002664`, WP5 order 606…855, 250 pairs, 500 endpoints, 1,413 boxes,
  365 unique stems, stem 0248 absent, 50/50 readable post-annotation pages, exact
  20-source/56-artifact roster and manifest SHA-256
  `ea4667c2ea18bc6fff23ce23beffe5b27372e494160fa9d6ffbc86c3cb3f2dc5`. The 65 targeted tests
  pass, including 18 attack classes, exact exception rosters, coherent rollback,
  count-preserving swap rejection and clean-room 56/56 byte determinism. Full repository
  validation passes 516/516 tests plus Ruff, lock and diff; Graft is check-clean at 44 files,
  845 nodes and 2,298 edges. Status remains `WP14_AWAITING_QA_BATCH_D_PM_PROVISIONAL_REVIEW`;
  D-02 and Gate 0 remain blocked.
- M0-WP15 build/verify readback before independent QA: exact final cross-split selection
  `edge_002665`…`edge_003178`, WP5 order 856…1,031, 176 pairs, 352 endpoints, 992 boxes,
  stem 0248 absent, 36/36 readable post-annotation pages with exact 35×5 + 1×1 pagination,
  exact 24-source/42-artifact roster and manifest SHA-256
  `032aee9da985c5dcb772ddd1c73fa9e4e6794e1beb5107fdb49b0168948a241d`. The 69 targeted
  tests and 585/585 full-suite tests pass, including 18 attack classes, coherent rollback,
  count-preserving exception swap rejection and clean-room determinism; Ruff, lock and diff pass.
  All historical WP5 and WP7…WP14 CLI verifiers remain `valid=true`; Graft is check-clean at
  46 files, 892 nodes and 2,415 edges. Status is
  `WP15_AWAITING_QA_BATCH_E_PM_PROVISIONAL_REVIEW`; D-02 and Gate 0 remain blocked.
- Independent `QA-M0-WP15` closure: PASS with 0 blockers and 0 functional/package findings. QA
  independently verified 704 raw image/label bindings, 24 sources/42 artifacts, 37 atlas files,
  exact 35×5 + 1×1 pagination, 36/36 pages and 176/176 panels; rejected 18/18 attacks plus coherent
  rollback and count-preserving exception swap; and rebuilt 42/42 artifacts plus the manifest
  byte-identically. Zero pending cross-split rows remain outside the five overlays. This does not
  approve D-02, group truth, split or training.
- M0-WP16-R1 build/verify and independent-QA closure: exact first 100 quarantine-eligible
  canonical sequence IDs `proxy_sequence_0001`…`proxy_sequence_0101` minus
  `proxy_sequence_0050`, 339 unique members, stem `0248` absent, one explicit whole-sequence
  exclusion row and 489 sequences outside the overlay. PM read all 100 prepared atlas pages/339
  member frames and post-build pages 1/50/100. Exact roster is 19 sources/107 non-manifest
  artifacts; notes SHA-256 is `d673ac00d0345fcf1fc0b46c2e9e3396ba97d3bd17259ce7a4d370756ed38e9d`
  and R1 manifest SHA-256 is `f3e3fb7a13631ef60b9046f745c07cb39ff3df501c18d5e15e79ee2e505964bc`.
  Initial QA passed package content with 0 blockers but found the P3 top-level unknown-key gap. R1
  exact-checks all 31 top-level fields; nested source/artifact records were audited as already exact.
  The 32 targeted tests and 617/617 full-suite tests pass, including 21 attack classes, coherent
  rollback, count-preserving decision-ID swap rejection and clean-room 107/107 artifact byte
  determinism; Ruff, lock and diff pass. Historical WP5/WP7/WP10–WP15 hashes are unchanged and all
  WP5/WP7/WP10–WP16 CLI verifiers return `valid=true`. Pre/post R1 comparison preserves 106/107
  artifact bytes; only the generated report and builder source changed. Graft is check-clean at
  48 files, 943 nodes and 2,564 edges. Independent `QA-M0-WP16-R1` returned PASS with 0 blockers,
  no new severity findings, 21/21 attacks rejected and clean-room 107/107. The hash-pinned package
  retains historical status `WP16_AWAITING_QA_SEQUENCE_BATCH_A_PM_PROVISIONAL_REVIEW`; closure is
  routing-only. D-02 and Gate 0 remain blocked.
- M0-WP17 build/verify readback before independent QA: exact canonical sequence IDs
  `proxy_sequence_0102`…`proxy_sequence_0201`, no gaps and no overlap with WP16. Selection covers
  100 sequences, 344 unique frames and 1,312 bbox occurrences; stem `0248` is absent and the whole
  canonical `proxy_sequence_0050` exclusion remains PENDING/unreviewed. PM read all 100 prepared
  atlas pages/all 344 frames and post-build pages 1/50/100. Decisions are 100
  `CONTINUOUS_CANDIDATE`, 91 `MULTIPLE_SIGNS`, 9 `SAME_PHYSICAL_SIGN_CANDIDATE`, 100 `HIGH`.
  Exact roster is 21 sources/107 non-manifest artifacts/18,636,827 bytes; trusted-notes SHA-256 is
  `cdefee98149db85d4600cf7f69ee004d6f769ecc23bc6c57dce898732c2e4248` and manifest SHA-256 is
  `374ada61066f70f8ff3ba282dba41229ad2c161303146edd83aba583591b144b`. The 28 targeted tests and
  645/645 full-suite tests pass, including 21 attack classes, coherent rollback, same-count swap,
  exact top-level/nested schema and clean-room 107/107 byte determinism; Ruff, lock and diff pass.
  All WP5/WP7/WP10–WP17 CLI verifiers pass; historical package hashes and README are unchanged;
  raw preservation proof remains `unchanged=true`. Graft is check-clean at 50 files, 970 nodes and
  2,631 edges. Status is `WP17_AWAITING_QA_SEQUENCE_BATCH_B_PM_PROVISIONAL_REVIEW`; D-02 and Gate 0
  remain blocked and training is unauthorized. Independent QA subsequently returned PASS with 0
  blockers/no severity findings after 21/21 attack rejection, clean-room 107/107 and full-suite
  645/645. Closure is routing-only and the hash-pinned historical package remains unchanged.
- M0-WP18 build/verify readback before independent QA: exact canonical sequence IDs
  `proxy_sequence_0202`…`proxy_sequence_0301`, no gaps and no overlap with the exact WP16+WP17
  200-sequence prefix. Selection covers 100 sequences, 400 unique frames and 944 bbox occurrences;
  stem `0248` is absent and whole `proxy_sequence_0050` remains PENDING/unreviewed. PM read all
  100 prepared atlas pages/all 400 frames and post-build pages 1/50/100. Decisions are 100
  `CONTINUOUS_CANDIDATE`, 70 `MULTIPLE_SIGNS`, 30 `SAME_PHYSICAL_SIGN_CANDIDATE`, 100 `HIGH`.
  Exact roster is 23 sources/107 non-manifest artifacts/20,715,246 bytes; trusted-notes SHA-256 is
  `69eb2da7c8dadcb5d27aadc46fa90e7941a1798ac4dca790110e4f8484d0d915` and manifest SHA-256 is
  `35bf843db7eb626404c81477efb509b2e4881a2cc7ea81fcee3187fcfab93649`. The 29 targeted tests and
  674/674 full-suite tests pass, including 22 attack classes, predecessor-prefix tamper, coherent
  rollback, same-count swap, exact top-level/nested schema and clean-room 107/107 byte determinism;
  Ruff, lock and diff pass. All WP5/WP7/WP10–WP18 CLI verifiers pass; historical manifests and the
  user-updated README SHA-256 `9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7`
  are unchanged; raw preservation proof remains `unchanged=true`. Graft is check-clean at 52 files,
  997 nodes and 2,698 edges. Status is
  `WP18_AWAITING_QA_SEQUENCE_BATCH_C_PM_PROVISIONAL_REVIEW`; D-02 and Gate 0 remain blocked,
  training is unauthorized. Independent QA subsequently returned PASS with 0 blockers/no severity
  findings after 22/22 attack rejection, clean-room 107/107 and full-suite 674/674. Closure is
  routing-only and the hash-pinned historical package/report remain unchanged.
- M0-WP19 build/verify readback before independent QA: exact canonical sequence IDs
  `proxy_sequence_0302`…`proxy_sequence_0401`, no gaps and no overlap with the exact
  WP16+WP17+WP18 300-sequence prefix. Selection covers 100 sequences, 422 unique frames and 824
  bbox occurrences; stem `0248` is absent and whole `proxy_sequence_0050` remains
  PENDING/unreviewed. PM read all 100 prepared atlas pages/all 422 frames and post-build pages
  1/50/100. Decisions are 100 `CONTINUOUS_CANDIDATE`, 61 `MULTIPLE_SIGNS`, 39
  `SAME_PHYSICAL_SIGN_CANDIDATE`, 100 `HIGH`. Exact roster is 25 sources/107 non-manifest
  artifacts/20,702,974 bytes; trusted-notes SHA-256 is
  `627e0598d077ccb568c252b7980833cd317803398385fce61e467c3e2de483b1`, selection SHA-256 is
  `a63c8125fd570d19af5719bf11800d6b9ea70e3a03596cf195c63753e0c0296f` and manifest SHA-256 is
  `6796c3a16b2af347f0a74a06cde4477b214d97233d0d38848d9077933c7f712f`. The 29 targeted tests
  pass, including 22 attack classes, WP18-prefix tamper, coherent rollback, same-count swap, exact
  schemas and clean-room 107/107 byte determinism; full validation passes 703/703 tests; Ruff,
  lock and diff pass. Graft is check-clean at 54 files, 1,024 nodes and 2,765 edges. All
  WP5/WP7/WP10–WP19 CLI verifiers pass; historical manifests and the user-updated README SHA-256
  `9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7` are unchanged; raw
  preservation proof remains `unchanged=true`. Status is
  `WP19_AWAITING_QA_SEQUENCE_BATCH_D_PM_PROVISIONAL_REVIEW`; D-02 and Gate 0 remain blocked,
  training is unauthorized. Independent QA subsequently returned PASS with 0 findings after
  targeted 29/29 and full-suite 703/703. Closure is routing-only and the hash-pinned historical
  package/report remain unchanged; WP20 is authorized as the next provisional batch only.
- M0-WP20 build/verify readback before independent QA: exact canonical sequence IDs
  `proxy_sequence_0402`…`proxy_sequence_0501`, no gaps and no overlap with the exact
  WP16…WP19 400-sequence prefix. Selection covers 100 sequences, 406 unique frames and 1,287 bbox
  occurrences; stem `0248` is absent and whole `proxy_sequence_0050` remains PENDING/unreviewed.
  PM read all 100 prepared atlas pages/all 406 frames and post-build pages 1/50/100. Decisions are
  100 `CONTINUOUS_CANDIDATE`, 81 `MULTIPLE_SIGNS`, 19 `SAME_PHYSICAL_SIGN_CANDIDATE`, 100
  `HIGH`. Exact roster is 27 sources/107 non-manifest artifacts/20,410,750 bytes; trusted-notes
  SHA-256 is `04a70bfa693c105da29ac263ab8f24a1e030b489b8379078c79e0dd3f21e6f8b`,
  selection SHA-256 is `b99abd53de497e74e42a75396be9f565c391977c4f35f633975cba3081c3bfc3`
  and manifest SHA-256 is `4523c698ff948ee2adaf879195662caec25ac80280cceb0aaaf91ae72fe89a6c`.
  The 29 targeted tests pass with 22 attack classes, WP19-prefix tamper, coherent rollback,
  same-count swap, exact schemas and clean-room 107/107 byte determinism; full validation passes
  732/732 tests; Ruff, lock and diff pass. All WP5/WP7/WP10–WP20 CLI verifiers pass; historical
  manifests and the user-updated README SHA-256
  `9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7` are unchanged; raw
  preservation proof remains `unchanged=true`. Graft is check-clean at 56 files, 1,051 nodes and
  2,832 edges. Status is `WP20_AWAITING_QA_SEQUENCE_BATCH_E_PM_PROVISIONAL_REVIEW`; D-02 and
  Gate 0 remain blocked and training is unauthorized. Independent QA subsequently returned PASS
  with 0 findings and full-suite 732/732; closure is routing-only and the hash-pinned historical
  package/report remain unchanged.
- M0-WP21 build/verify readback before independent QA: exact canonical sequence IDs
  `proxy_sequence_0502`…`proxy_sequence_0589`, no gaps and no overlap with the exact WP16…WP20
  500-sequence prefix. Selection equals the complete residual `eligible[500:]` suffix: 88
  sequences, 363 unique frames and 1,068 bbox occurrences; stem `0248` is absent and whole
  `proxy_sequence_0050` remains PENDING/unreviewed. PM read all 88 prepared atlas pages/all 363
  frames and post-build pages 1/44/88. Decisions are 88 `CONTINUOUS_CANDIDATE`, 60
  `MULTIPLE_SIGNS`, 28 `SAME_PHYSICAL_SIGN_CANDIDATE`, 88 `HIGH`. Exact roster is 29 sources/95
  non-manifest artifacts/17,536,294 bytes; trusted-notes SHA-256 is
  `8acdfdb0041214f933eb4933cbddfd97bc90868361c4b9351975b6dacbb3e8c1`, selection SHA-256 is
  `40c7c7d9c94767b2b6d82bd9d2d134aa74af0afd7f62ce5ed470e55ab9efbc68` and manifest SHA-256 is
  `7ed7e1355ae1dfc88ec81b7f580aad3bf0874b59832708652ad1ba02265d4e4c`. The 29 targeted tests
  pass with 22 attack classes, WP20-prefix tamper, coherent rollback, same-count swap, exact
  schemas and clean-room 95/95 byte determinism; full validation passes 761/761 tests; Ruff, lock
  and diff pass. All WP5/WP7/WP10–WP21 CLI verifiers pass; historical manifests and the
  user-updated README SHA-256
  `9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7` are unchanged; raw
  preservation proof remains `unchanged=true`. Graft is check-clean at 58 files, 1,078 nodes and
  2,899 edges. Status is `WP21_AWAITING_QA_FINAL_ELIGIBLE_SEQUENCE_BATCH_PM_PROVISIONAL_REVIEW`;
  D-02 and Gate 0 remain blocked, split/training are unauthorized, and no follow-on promotion or
  reconciliation work package had started at that readback. Independent QA later returned PASS
  with 0 findings; closure is routing-only and package bytes remain unchanged.
- M0-WP22 build/verify readback before independent QA: exact canonical selection
  `edge_000002`…`edge_000378`, WP5 order 1,032…1,284 with predecessor/quarantine exclusions,
  250 pairs, 500 endpoints, 903 boxes, no cross-split and no stem `0248`. PM read all 50 prepared
  atlas pages/250 panels and post-build pages 1/25/50. Decisions are 240
  `SAME_CAPTURE_CANDIDATE`/`SAME_PHYSICAL_SIGN_CANDIDATE`, 10 `NOT_RELATED`, all `HIGH`.
  Exact roster is 52 sources/56 non-manifest artifacts/54,312,346 bytes; trusted-notes SHA-256 is
  `c49c00bc85bbc0bc1cfc4683d9dbbd6403705a42600a1251e46e7ade949c6a27`, selection SHA-256 is
  `af70edc35a2a925f4e23bd8ce2e481c7fdf6e18f1c904c963561c412ac74d6aa` and manifest SHA-256 is
  `7086371d65d1389c26541a3621745e0eadb9df7bfe62ca3dab34ffbb45e3b487`. The 45 targeted tests
  and 806/806 full-suite tests pass, including 18 attack classes and clean-room 56/56 byte
  determinism; Ruff, lock and diff pass. All WP5/WP7/WP10–WP22 CLI verifiers pass; Graft is
  check-clean at 60 Python files, 1,121 nodes and 2,998 edges. README SHA-256
  `9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7` is unchanged and raw
  preservation remains `unchanged=true`. Status is
  `WP22_AWAITING_QA_REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_REVIEW`; 1,896 residual PENDING edges
  remain outside overlays, all 589 sequences remain PENDING, D-02/Gate 0 remain blocked, and
  split/training are unauthorized. Independent QA later returned PASS with 0 findings; closure is
  routing-only and package bytes remain unchanged.
- M0-WP23 build/verify readback before independent QA: exact canonical selection
  `edge_000379`…`edge_000760`, WP5 order 1,285…1,534 after exact WP22-prefix exclusion, 250 pairs,
  500 endpoints, 1,556 boxes, no cross-split and no stem `0248`. PM read all 50 prepared atlas
  pages/250 panels; decisions are 233 `SAME_CAPTURE_CANDIDATE`/
  `SAME_PHYSICAL_SIGN_CANDIDATE`, 17 `NOT_RELATED`, all `HIGH`. Exact roster is 56 sources/56
  non-manifest artifacts/54,019,044 bytes; trusted-notes SHA-256 is
  `c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8`, selection SHA-256 is
  `e6913b2eeba22c990cef393490f8d8cb2caaa6745b2045e6edf64c3a6f9973a6`, annotations SHA-256 is
  `2720ac892a9f0ebe46dc027a722702031a8519aaa856965d560da99d85e2c7be` and manifest SHA-256 is
  `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd`. The 45 targeted tests and
  851/851 full-suite tests pass, including 18 attack classes and clean-room 56/56 byte determinism;
  Ruff, lock and diff pass. All historical WP5/WP7/WP10–WP23 CLI verifiers pass; Graft is
  check-clean at 62 Python files, 1,164 nodes and 3,097 edges. README SHA-256
  `9005addc5b9952b36fca7f744489270cc7507bfaad0c6a02f305954915de01a7` is unchanged and raw
  preservation remains `unchanged=true`. Status is
  `WP23_AWAITING_QA_REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_REVIEW`; 1,646 residual PENDING edges
  remain outside overlays, all 589 sequences remain PENDING, D-02/Gate 0 remain blocked, and
  split/training are unauthorized. Independent QA subsequently returned FAIL with exactly one High
  finding: `edge_000664` had an incorrect `NOT_RELATED` decision/rationale; technical/integrity
  checks remained PASS. The initial manifest, artifacts and sources remain unchanged.
- M0-WP23-R1 correction readback and independent-QA routing: append-only correction source changes
  only `edge_000664` from `NOT_RELATED` to `SAME_CAPTURE_CANDIDATE` /
  `SAME_PHYSICAL_SIGN_CANDIDATE`, `HIGH`, supported by same-camera/same-scene raw frames, identical
  classes `7 10 17 19 44`, `strong_candidate`, MAE `6.303241`, dHash `6` and histogram
  `0.99600903`. Corrected counts are 234 same/16 `NOT_RELATED`/250 `HIGH`; the other 249 decision
  semantics are unchanged. Official verify is `valid=true` with 62 sources, 56 artifacts and
  54,306,219 bytes. Initial→R1 manifest SHA-256 is
  `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd` →
  `8b1ca3c9953209d5fc86a8b2265228e27adb63cb430d5c5f5f1375d8d6f86783`; the 57-row manifest-plus-
  artifact delta is `docs/review/generated/wp23_r1_artifact_hash_delta.csv`. All 16 historical
  verifiers pass; 28/28 R1 targeted tests (18 attack classes and clean-room 56/56), 879/879 full
  tests, Ruff, lock and diff pass. Visual readback of pages 39/1/25/50 passes. Graft is check-clean
  at 64 Python files, 1,198 nodes and 3,174 edges. Independent delegated QA subsequently returned
  PASS with 0 findings; this is routing-only and the package keeps status
  `WP23_R1_AWAITING_QA_REVIEW` byte-for-byte.
- M0-WP24 package readback and independent-QA routing: exact canonical selection
  `edge_000763`…`edge_001154`, WP5 order 1,535…1,784 after exact QA-passed WP22/WP23-R1 prefix
  removal, 250 pairs, 500 endpoints, 323 unique stems, 1,581 endpoint boxes and 1,044 unique-stem
  boxes. PM read all 50 atlas pages/250 panels; decisions are 243 same/7 `NOT_RELATED`, all
  `HIGH`. Exact roster is 67 sources/56 non-manifest artifacts/50,037,488 bytes. Manifest,
  selection, annotations and notes SHA-256 values are respectively
  `e5f49a4c5840a6e682f2a7d0cc418183ec6f52d7b745b9f397b570d6770ceaea`,
  `19194c430c03fcaa507646ca0065776e1279471e1b2ed240f05506f74f3b5c9d`,
  `82d480a5f0aee86d92236c73a7651b0ed4068385c69a5bdb571ddc071dd10f6f`, and
  `086f1c58acbe1434b5bf295576d24e4279fccb59e01f56ba5f3aafaec4508ab1`. Official verifier is
  `valid=true`; 46/46 targeted tests, 164/164 combined remaining-edge tests and 925/925 full tests
  pass; Ruff, lock and diff pass. Independent delegated QA returned PASS with 0 findings; routing
  records the closure while the immutable package retains `WP24_AWAITING_QA_REVIEW`. 1,396 residual PENDING edges
  remain outside overlays including two quarantine edges. All 589 sequences and canonical WP5
  remain `PENDING`; D-02/Gate 0 remain blocked; split/training remain unauthorized.
- M0-WP25 PM package before independent QA: exact canonical selection `edge_001155`…`edge_001502`,
  WP5 order 1,785…2,034 after exact QA-passed WP22/WP23-R1/WP24 prefix removal, 250 pairs,
  500 endpoints, 307 unique stems, 1,090 endpoint boxes and 671 unique-stem boxes. PM read all 50
  atlas pages/250 panels; decisions are 240 same/10 `NOT_RELATED`, all `HIGH`. Exact roster is 72
  sources/56 non-manifest artifacts/51,739,615 bytes. Manifest, selection, annotations and notes
  SHA-256 values are respectively `1d7b04d6432424297f2e14178dd59936526dec7d6293872fbda0010bb460e5e9`,
  `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`,
  `990d314a462a2279d9600f2b6b5e2b12c1da73dd7425e7ec07a388d883487cc5`, and
  `b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8`. Official verifier is
  `valid=true`; targeted tests pass 46/46 with 18 attack classes, semantic ID-swap and clean-room
  determinism; combined remaining-edge tests pass 210/210 and full validation passes 971/971.
  All 18 historical/current verifiers, Ruff, lock, diff and Graft check pass. Status is
  `WP25_AWAITING_QA_REVIEW`; 1,146 residual PENDING edges remain outside
  overlays including two quarantine edges. All 589 sequences and canonical WP5 remain `PENDING`;
  D-02/Gate 0 remain blocked; split/training remain unauthorized. Independent QA subsequently
  returned FAIL with exactly one P1 and zero P0/P2/P3 at `edge_001358`; technical/integrity checks
  remained PASS and this initial package is immutable.
- M0-WP25-R1 correction handoff: changes only `edge_001358` to same-capture/same-physical-sign,
  `HIGH`; effective tallies are 241 same, 9 `NOT_RELATED`, 250 `HIGH`. Selection remains
  byte-identical at SHA-256 `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`;
  manifest `96a19417256c312c1ec005f13c5abccf85a1718d12ab0c729cb234baebfe9fe8` contains 78 sources,
  56 artifacts and 52,026,143 bytes. Official verify, 29/29 targeted, 239/239 compatibility,
  1,000/1,000 full tests, 19 CLI verifiers, Ruff, lock, diff and Graft check pass. Graft is current
  at 70 Python files, 1,313 nodes and 3,435 edges. Status is `WP25_R1_AWAITING_QA_REVIEW`;
  independent QA subsequently returned PASS with 0 findings after page 029 slot 4/raw 1365→1366,
  one-edge-only delta and immutable-WP25 checks. Closure is routing-only; no split, training or
  final/transitive group truth was authorized.
- M0-WP26 PM package readback: exact canonical selection `edge_001505`…`edge_001850`, WP5 order
  2,035…2,284 after exact QA-passed WP22/WP23-R1/WP24/WP25-R1 prefix removal, 250 pairs, 500
  endpoints, 305 unique stems, 997 endpoint boxes and 600 unique-stem boxes. PM read all 50 atlas
  pages/250 panels; capture decisions are 240 same/10 `NOT_RELATED`, physical-sign decisions are
  239 same/11 `NOT_RELATED`, all `HIGH`. Exact roster is 83 sources/56 non-manifest artifacts/
  48,503,108 bytes. Manifest, selection, annotations and notes SHA-256 values are respectively
  `4e0ddff49a83baac0c41e6be28f376d09f2d887fd0742ac2efd439e46fdf62e7`,
  `70f9a1a77172eac59761d642cce2689c9bb5a5ba07dc87cea426f0814be51582`,
  `be125fcc5b97ad9c0439b09543d00b62edcc1611c0bc750ae6bf7252b6d4ee70`, and
  `47178a56aa80d5da39e146e1319dea6015e4361161b1a1fe45b91e973dcdf64d`. Status is
  `WP26_AWAITING_QA_REVIEW`; its historical readback left 896 residual PENDING edges outside
  overlays including two quarantine edges. All 589 sequences and canonical WP5 remain `PENDING`;
  D-02/Gate 0 remain blocked and split/training remain unauthorized.
  PM validation passes 47/47 targeted, 286/286 compatibility and 1,047/1,047 full-suite tests;
  durable full-suite exit is 0. All 24 CLI verifiers, Ruff, lock and diff pass; Graft is
  check-clean at 72 Python files, 1,354 nodes and 3,528 edges. Independent QA subsequently
  returned PASS with 0 findings. Closure is routing-only; all WP26 package/source hashes remain
  unchanged and the package keeps historical status `WP26_AWAITING_QA_REVIEW`.
- M0-WP27 PM package before independent QA: exact canonical selection
  `edge_001851`…`edge_002213`, WP5 order 2,285…2,534 after exact QA-passed
  WP22/WP23-R1/WP24/WP25-R1/WP26 prefix removal, 250 pairs, 500 endpoints, 306 unique stems,
  1,069 endpoint boxes and 650 unique-stem boxes. PM read all 50 atlas pages/250 panels and all 12
  exceptional annotated pages. Capture decisions are 247 same/3 `NOT_RELATED`; physical-sign
  decisions are 229 same/21 `NOT_RELATED`, all `HIGH`. Exact roster is 88 sources/56
  non-manifest artifacts/49,363,156 bytes. Manifest, selection, annotations and notes SHA-256
  values are respectively `9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`,
  `3f8915b661bc53df3e2a736bb0dce0481ce95c4ed2c2cdce7e144dfe8b8aadbf`,
  `ce35afc20a4b8ee2f1fefb86210ea61838123dd4a7b9e58969a33e57bb4d4de9` and
  `2635a14140fb4d7dd82c2a0118707db1553babfafb322285ac36722d5f6a7ff8`. Official verifier is
  `valid=true`; targeted tests pass 47/47 and applicable WP22…WP27 compatibility passes 332/332
  after explicitly deselecting only immutable WP26's obsolete no-WP27-files assertion. All 26
  executable verifier entrypoints pass. The final-state applicable full suite passes 1,093/1,093
  in durable `screen` with explicit exit code 0; Ruff, lock and diff pass. Graft is rebuilt and
  check-clean at 74 Python files, 1,395 nodes and 3,621 edges. Status is
  `WP27_AWAITING_QA_REVIEW`; 646
  residual PENDING edges remain outside overlays including two quarantine edges. All 589
  sequences and canonical WP5 remain `PENDING`; D-02/Gate 0 remain blocked; split/training remain
  unauthorized and no final/transitive group truth exists. No WP28 work has started.
- Nonblocking P3 backlog: the inherited diagnostic in
  `scripts/build_wp12_cross_split_review_batch.py` still says “WP12 / exact 51-file contract” when
  WP15 enforces 37 files. Do not mutate the hash-pinned WP12–WP15 builders in place; parameterize
  work-package name and expected roster size in a future verifier version.

## Memory maintenance protocol

Update this file only when a fact will matter in a future session: a changed architecture boundary,
accepted decision, milestone state, verified command, blocker, or superseded risk. Do not append a
chat diary. Replace stale statements and point to the detailed evidence file.

At the end of material work:

1. Update the relevant canonical document.
2. Update this compact memory if the durable state changed.
3. Include the date and exact command/evidence for new verification claims.
4. Run the appropriate tests and Graft freshness check.
5. Leave unresolved proposals explicitly marked as proposed.
