# D1 train-label-completeness review R1 — design contract

Status: `PROPOSAL_AWAITING_INDEPENDENT_QA`
Boundary: `DESIGN_CONTRACT_ONLY_NO_LABEL_EDIT_NO_DATA_MOVE_NO_TRAINING_NO_INFERENCE_NO_SEALED_TEST`
Flags (this contract and every artifact it later specifies): `sealed_test_accessed=false`,
`training_authorized=false`, `labels_modified=false`
Author: Claude Code session `d1-train-label-completeness-r1`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`, 2026-11-05 (Asia/Ho_Chi_Minh). Documentation only; no existing file was edited.

Claim tags used throughout: **[V]** verified artifact or current behavior (with a pointer),
**[P]** proposal (nothing here is implemented), **[U]** unknown.

## 0. Purpose in one paragraph

Hard-negative mining (Track A1) turns "a pilot prediction that matches no ground truth" into
"background". That is only safe on frames where every real sign has been labelled or deliberately
masked. This contract fixes the human review package that establishes, per frame and per D-02
capture group, whether that is true on the **train** split. It decides who reviews what, how, with
what output format, which pre-registered bounds count as "complete enough", and what each outcome
does to A1. It authorizes nothing: no review is run, no packet is built, no label changes, and A1
stays `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`.

## 1. Question and scope

**Question.** On the 1,912 raw train frames and the 1,800 WP35 train-only images exported for
YOLO training, what fraction of real, in-scope traffic signs is missing from the training labels,
and on which frames/groups is the residual missing-label rate low enough that an unmatched
prediction may be treated as a negative candidate?

### 1.1 Why the question is live (evidence)

- **[V]** R3 contract §6 states that the train split may contain unlabelled real signs and that A1
  can only follow a QA-passed human train-label-completeness review package; R3 defines none.
- **[V]** The same label table feeds every split: `scripts/build_m1_yolo_dataset.py::derive` builds
  train, val and test labels from one `wp33_derived_boxes.csv` (`train_eligible == "True"` rows).
  Train labels therefore share their origin with the validation labels that were proven incomplete.
- **[V]** Validation evidence that unlabelled real signs exist in this data family
  (D1-VLA-R1 → D1-VRL R1–R3, all independently QA-reviewed):
  - Of 214 R10 background false positives, 138 had no label nearby (IoU < 0.1); visual review
    found 116 in-taxonomy unlabelled signs (112 unique), 9 out-of-taxonomy unlabelled signs, 4 out-of-taxonomy
    signs already labelled `UNKNOWN`, 7 non-signs and 2 unclear.
  - 104 HIGH/MEDIUM proposals became, in D1-VRL-R1, 26 re-fitted boxes + 78 ignore regions
    (QA FAIL on geometry premise, H1) and, in D1-VRL-R2/R3, **64 added ground-truth boxes + 40
    ignore regions** (R3: QA PASS, 0 Critical/High/Medium, 4 Low; owner-accepted as derived
    validation labels). With the 64 boxes alone, FP falls 214 → 150 (0.399 per image); the extra
    40 → 110 is circular by construction (ignore regions built from the same predictions).
  - Arithmetic from those artifacts: 104 added/masked unlabelled signs against 560 original
    validation GT boxes, i.e. at least 104/(560+104) = 15.7% of the audited sign population was
    missing. This is a **lower bound** (only model-detected signs were audited, D1-VLA-R1 limits) and it
    describes validation groups, not train.
- **[U]** The train missing-label rate. Train labels were never audited. Validation-based numbers
  are a prior for motivation only and enter no acceptance threshold.
- **[V]** A second, separate mechanism is already recorded in the train export manifest: 27 train
  frames carry boxes that are real signs but are **deliberately unlabelled** because the WP33 table
  marks them `UNKNOWN` (26) or `16:UNREADABLE` (1), `train_eligible=False`
  (`m1_yolo_export_manifest.json`: `splits.train.frames_with_untrained_boxes = 27`; recount from
  `wp33_derived_boxes.csv` over the 1,912 train frames: 5,442 boxes, 5,415 eligible, 27 not).
  A prediction on such a sign matches no train label yet is not background. Any A1 rule must mask
  these 27 regions regardless of what this review finds.

### 1.2 Split scope

- **Train only [P].** Reviewed population: the 1,912 raw frames of the WP36-R1 train split that the
  M1 export uses. **[V]** `wp36_r1_split_frames.csv` has 1,929 `split=train` rows: `use=TRAIN` 1,911,
  `BACKGROUND` 1 (stem `0544`, group `D02-C0014`), `QUARANTINED` 17. 1,911 + 1 = 1,912 equals the
  export manifest's train frame count, so the 17 quarantined train stems are outside the export (stem `0248`, owner-quarantined under
  G0.4, has no row in this CSV at all). They stay excluded, are not reviewed and are not given a group. The packet
  builder must re-verify the roster against the export manifest's train `stem_list_sha256`
  `6ac76750…` **[U: not recomputed in this session]**.
- **Validation and the sealed test are never read for selection [P].** No val stem, val box, val
  prediction or val-derived list chooses which train frame is reviewed, in which order, or into which
  stratum. The validation records above are cited as *evidence for the design*, read from their
  QA-passed documents, not as selection input. One disclosed exception requires QA judgement: the
  class-presence stratum in §3.2 names six class ids that come from the R10 val error table
  (class level only, no pixels, boxes or stems). Alternative if QA rejects it: stratify on train
  box-count terciles instead. See open decision D-3.
- **Sealed test.** `afa03d4b…` is the test stem-list hash in the export manifest. This package never
  opens, lists or hashes any path with a `test` component. `sealed_test_accessed=false`.

### 1.3 WP35 derived images: decision

**[V]** Facts: `wp35_enrichment_lineage.csv` has 1,800 rows = 12 derived keys × 150 images, generated
from **180 distinct train raw frames** (all `use=TRAIN`) in 10 capture groups
(`D02-C0010/13/14/15/16/19/21/22/49/53`) by rotation, crop-without-padding, photometric change
and JPEG; labels are the source boxes mapped through the same transform, and the builder refuses any
crop that cuts a *labelled* box (`build_wp35_rare_class_enrichment.py`, "never cut a sign").
Its manifest status is `WP35_REAL_FRAME_AUGMENTATION_AWAITING_QA` and `training_only=true`.

**Decision [P]: WP35 images are not reviewed as images and not part of the rate estimate.** Reasons:
1. The unit of evidence is the real sign in a real frame; 1,800 images are 180 sources × 10
   transforms, so reviewing them would count the same sign ten times.
2. Every WP35 pixel and label is a deterministic function of a raw train frame plus a lineage row.
   If the raw frame is reviewed, the WP35 image inherits the review.
3. The builder only guards against cutting *labelled* signs; an unlabelled sign cut by the crop is
   invisible to it. That is a WP35-specific missing-label hazard, handled by masking, below.

**Inheritance rule [P].** A WP35 image is *negative-eligible* only if (a) its source raw frame has
final status `REVIEWED_COMPLETE` in a passing group (§5), and (b) every reviewed region of the
source frame (added boxes, `OUT_OF_SCOPE`, `UNREADABLE`, `IGNORE_REGION`, existing `UNKNOWN`
boxes) is mapped into the WP35 image with the **builder's own transform function** (not a
re-implementation), and any region touched by the crop border is masked, not left as background.
Otherwise the image is `NOT_ELIGIBLE`. The 180 sources are inside the census (§3), so no extra
review is required.

## 2. Evidence binding

SHA-256 of every file read for this contract, taken 2026-11-05 on the working tree (HEAD `17db663`).
Tracked state: `clean` = tracked and unmodified, `untracked` = Owner's uncommitted file,
`modified` = tracked with uncommitted Owner edits.

| Evidence | SHA-256 | State |
| --- | --- | --- |
| `docs/review/d1_yolo54_improvement_r3_contract.md` (§6 A1 blocked) | `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f` | clean |
| `docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md` (lines 45–53, 76–100) | `9ec8dd0d9e2866ef098ca3afada624ea5562837531f9b077981c45940ed0f78f` | clean |
| `docs/review/next_direction_proposal_2026-11-04.md` (hard-negative row, line 17) | `dc2a08ad0ce171254ab5ff292cad5052ebfeb57c6ced867583c79f1c1b477d68` | clean |
| `docs/review/d1_vla_r1_report.md` | `93ee9566e7b237e7bc61ab7e858a2b17db76cebf0865ae178a7017022b8d0e9f` | clean |
| `docs/review/d1_vla_r1_independent_qa_record.md` | `5e856b77dace347774246e4f11a38379f3b068182e65bf35e92dac56c030948c` | clean |
| `docs/review/d1_vrl_r1_report.md` | `9c6fe2f7a3b08d91b614437d6f0a3c1bdc47ed3dea98abf59d071b585f4c24a1` | clean |
| `docs/review/d1_vrl_r1_independent_qa_record.md` (FAIL) | `e168b6bf2cb5b3322ff3f3ffb7701bf65433952610baeafe42aeca1e435fab0c` | clean |
| `docs/review/d1_vrl_r2_report.md` | `73016ba46525069e1d43b15d0e148d476ce91c0d592106a0658aad180fe1b346` | clean |
| `docs/review/d1_vrl_r2_independent_qa_record.md` (PASS, 1 Medium) | `0758405680147ba9b153758076b0803245373947ece90953f22ca3025369514d` | clean |
| `docs/review/d1_vrl_r3_report.md` | `a66e1baeb8e889cc9cd770ef2c1e3b9e90d9683b85ad8b0dde7b6942bf141123` | clean |
| `docs/review/d1_vrl_r3_independent_qa_record.md` (PASS, 4 Low) | `33ef3935ccdb24741e036183389478c5623d3c18ffe8c5f3322d465e782caa98` | clean |
| `docs/review/d1_vrl_r3_owner_acceptance_record.md` | `4d9482856771960240cdf727834e9283fb9ba072f88992c6204dcbb6405d7480` | clean |
| `docs/review/d1_vrl_r3_box_review_notes.csv` | `b653abb393fa278a4737cf3e08160e1c312d5b1b11d96cba029da8f3e4f4a385` | clean |
| `docs/review/generated/d1_vrl_r3_manifest.json` | `87dd0fd9ecea85745f613a788ef70ae830d396fc9e747f233db0c6fc536b8e07` | clean |
| `docs/review/generated/m1_yolo_export_manifest.json` | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` | clean |
| `docs/review/generated/wp35_enrichment_manifest.json` | `e9d42ec569a55cc118f6f8c08ad93dc3f0fee4ea7f73d79f905b958af41abd95` | clean |
| `docs/review/generated/wp35_enrichment_lineage.csv` | `e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed` | clean |
| `docs/review/generated/wp36_r1_split_frames.csv` (read for `split=train` rows only) | `8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a` | clean |
| `docs/review/generated/wp33_derived_boxes.csv` (read for the 1,912 train stems only) | `4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0` | clean |
| `docs/review/generated/m1_yolo_classes.csv` (54 classes) | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` | clean |
| `docs/review/d02_owner_decision_record.md` (54 capture groups = `group_id`) | `2b071cbff4a15c3b1c96b418ad9c8c56a12ec9bbf8ce7155c16baed41a412e85` | clean |
| `scripts/build_m1_yolo_dataset.py` (export and train lists) | `3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93` | clean |
| `scripts/build_wp35_rare_class_enrichment.py` | `be194e3d397d8294b693aa0b9638daedb5af3ff42b055b187d1de3bc9c05559f` | clean |
| `detector/m1/val_relabel_r3.py` (derived-label, ignore-region rules) | `34b89e320775abb8bf6186558ce03666c221331969c978836b01342e2e0d72ec` | clean |
| `detector/m1/yolo54_improvement_r3.py` (pin/manifest pattern) | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` | clean |
| `scripts/build_review2_annotation_packet_r1.py` | `19a4593cb12367b59da852c72c2512b352b84ca6a045e0d3fed42e2b0271c0ef` | untracked |
| `scripts/verify_review2_annotations_r1.py` | `fdcb473dade1c622fba2b031b6e956c91445728e1c88da32ed748b5ebf2c37ad` | untracked |
| `scripts/verify_review2_adjudication_r1.py` | `d3a5d9fb580aef0ba7d4c726462ae27de87d2fc150c6e0e642b07324489b1796` | untracked |
| `scripts/verify_review2_ignore_r2.py` | `6e2059528d4a4a97abfcb770d5dcef258778c0da6bd15de1aed8cc91c41cedcf` | untracked |
| `PROJECT_MEMORY.md` (working-tree snapshot, will drift) | `5571f6a1532a5f9a0bd99160531b094d4947599b6f8f5f4b0fb9420c162eeab8` | modified |
| `AGENTS.md` | `d2bd8b861a4ddb68914e26f1cc291781422bea1f3629b1b2782f5e6ecf46eb92` | clean |

Notes:
- The four Review 2 scripts are **uncommitted Owner files**. They are pattern references only; the
  successor modules in §6 copy the pattern and import nothing from them (§6.4).
- The R10 packet's 214 FP (R10 labels) and the 150 FP / 0.3989 per image of R3 validation (VRL-R3
  labels, `d1_vrl_r3_report.md`) are different cohorts. They are not added or mixed
  (`next_direction_proposal_2026-11-04.md` says the same).
- Whole-file pins for evidence read only in part (R10 packet, split frames, WP33 boxes) bind the
  entire file, so a later edit to any line invalidates the pin.

## 3. Sampling design

### 3.1 Recommendation: census of the 1,912 raw frames, prioritized in waves

**[P] Review every raw train frame (census), in the deterministic wave order of §3.3.** Why not a
sample only:
1. *Eligibility is per frame.* A negative candidate is only safe on a frame that was fully
   reviewed. A sample certifies the sampled frames and, at most, estimates a rate for the rest.
2. *A per-group bound needs most of the data anyway.* Showing a 5% one-sided 95% bound on a group
   takes ≥ 59 frames with zero misses (≥ 93 with one). Applied to the 29 train groups
   (§3.2 table) that is 404 + 826 = 1,230 frames, **64% of the train roster**, so a census adds
   only about 36% more review on top of what a sampled design already needs.
3. *Cheap mode.* Overlay review (§4.2) is a scan-and-confirm task, not annotation from scratch.

Sample-only variant (**Option S**, kept for Owner comparison): review the 1,230 frames above
(whole groups ≤ 93 frames, 93 random frames from each of the five larger groups). Outcome: a rate
estimate with CI and group eligibility, but no certified frames outside the sample.

### 3.2 Roster, groups and strata

**[V]** Recounted from `wp36_r1_split_frames.csv` (train rows) and `wp33_derived_boxes.csv`:
1,912 frames in 29 D-02 capture groups; sizes 505, 218, 190, 119, 115, 87, 75, 68, 66, 65 for the ten
groups with more than 60 frames, and 19 groups of 3–45 frames totalling 404. Three train frames have
no eligible label (`0544`, plus two whose only boxes are untrained). 786 frames contain at least one
labelled box of YOLO class 10, 12, 23, 30, 39 or 46 (the six ids in the R10 background-FP table;
ids as printed there, mapped through `m1_yolo_classes.csv` — QA must confirm the id→code mapping
because the class map reuses a code under two ids, e.g. P.127 as 39 and 41, S.505a as 30 and 32).

| Group | Frames | Target-class frames | Group | Frames | Target-class frames |
| --- | ---: | ---: | --- | ---: | ---: |
| D02-C0051 | 505 | 208 | D02-C0019 | 45 | 37 |
| D02-C0038 | 218 | 163 | D02-C0015 | 44 | 44 |
| D02-C0027 | 190 | 137 | D02-C0026 | 38 | 0 |
| D02-C0002 | 119 | 0 | D02-C0013 | 29 | 0 |
| D02-C0049 | 115 | 65 | D02-C0043 | 28 | 0 |
| D02-C0014 | 87 | 0 | D02-C0054 | 26 | 0 |
| D02-C0040 | 75 | 0 | D02-C0053 | 25 | 0 |
| D02-C0022 | 68 | 63 | D02-C0007 / C0010 | 21 / 21 | 0 / 0 |
| D02-C0025 | 66 | 0 | D02-C0039 | 18 | 0 |
| D02-C0036 | 65 | 40 | D02-C0023 / C0008 | 17 / 17 | 0 / 15 |
| D02-C0033 | 16 | 0 | D02-C0037 / C0004 | 13 / 12 | 0 / 0 |
| D02-C0021 | 11 | 11 | D02-C0047 / C0016 / C0029 | 10 / 10 / 3 | 0 / 0 / 3 |

**Strata (fixed before any review) [P]:** stratum = `group_id` × `target_class_frame ∈ {yes, no}`.
Groups of fewer than 59 frames form the pre-registered **small-group pool** (19 groups, 404 frames)
for acceptance (§5.2). The strata are built from train data only.

### 3.3 Order, seed and deterministic selection

- **Seed [P]: `20261105`.** No random-number library is used. Each frame gets
  `key = SHA-256(f"{seed}|d1_train_label_completeness_r1|{stem}")` as a hex string; "lowest key"
  means lexicographically smallest.
- **Waves [P]:** `W0` pilot = the 40 lowest-key frames overall (guideline freeze and timing only;
  re-reviewed under the frozen guideline). `W1` = target-class frames (786), `W2` = all other
  frames (1,126), each ordered by key. If the Owner stops after W1, A1 is limited to frames that
  completed review and passed their group gate (§5.3).
- **Blind calibration set [P]:** 150 frames, allocated proportionally to group size with
  largest-remainder rounding (ties by `group_id`), lowest keys within each group, drawn from W1 ∪ W2
  excluding W0.
- **QA audit sample [P]:** per group `n_g = min(N_g, 93)` frames, lowest keys among all frames of
  the group *after* adjudication, excluding none (the calibration set may overlap). Total
  1,230 frames: 765 in the 24 groups with N_g ≤ 93 (census audit) and 93 in each of the five groups
  C0051, C0038, C0027, C0002, C0049 (465).

### 3.4 Pilot predictions on train: proposal P-1 (not part of the baseline)

- Whether pilot predictions on the train split may be used to prioritize review is **proposed
  only**. It needs a separate explicit Owner authorization to run pilot `best.pt`
  (`5d5815a9…`, pinned in R3) on train frames; this contract authorizes no inference and has none
  to cite. `inference_run=false` throughout.
- If authorized, P-1 may only **reorder** the review queue (frames with a pilot detection that
  matches no existing label first). Annotators A and B stay model-blind: no prediction is drawn.
  Predictions create no label; the CSV carrying them is not an input to any label file.
- P-1 frames are **excluded** from the rate estimate, the calibration set and the QA audit sample,
  because selecting on "pilot fired where no label exists" enriches for missing labels and would bias
  every rate upward.
- **[U / hypothesis]** The pilot was trained on these labels, so on train it may under-detect the
  very signs that are unlabelled (it may have learned them as background). A quiet frame under the pilot is therefore never
  evidence of completeness. P-1 shortens the review of FP-prone frames; it does not replace review of the rest.
- Under the census recommendation P-1 mainly changes order; its main value arises only if the Owner chooses Option S.

### 3.5 Estimands, sample-size rationale and CI

- **R_pre** (descriptive): fraction of roster frames with ≥ 1 adjudicated *unlabelled in-scope sign*
  (frame level) and unlabelled in-scope boxes / (existing eligible + unlabelled in-scope boxes)
  (box level). Under a census this is an observed finite-population value, with no sampling error;
  its uncertainty is reviewer error, addressed by R_res and the calibration set. A 95% Wilson interval
  per group is still reported for comparability with validation-style statements.
- **R_res** (gating): residual frame-level missing rate *after* A/B/C, measured by an
  independent audit of the §3.3 audit sample. Estimator and CI:
  - per group: exact one-sided 95% Clopper–Pearson upper bound `UB(x_g, n_g)` on confirmed misses;
  - pooled: stratified estimator `Σ N_g·x_g/n_g / ΣN_g` with a percentile bootstrap 95% CI
    (B = 10,000 replicates, seed `20261105`, frames resampled within group);
  - exact values used in the rules: `UB(0,59)=0.0495`, `UB(0,93)=0.0317`, `UB(1,93)=0.0500`,
    `UB(2,93)=0.0662`, `UB(0,87)=0.0338`, `UB(1,87)=0.0534`, `UB(3,404)=0.0191`, `UB(4,404)=0.0225`.
- **Sample-size rationale [P]:** `n_g = 93` is the smallest n that lets a group pass the 5% bound with
  one confirmed miss; 59 is the zero-miss minimum; the 404-frame small-group pool supports a 2%
  bound with up to three misses. A 150-frame calibration set is large enough to detect gross
  anchoring (overlay sensitivity well under 0.7), not to estimate it precisely: with roughly 40
  blind-found additions the 95% interval is about ±15 points **[U: additions per frame unknown]**.
- **Dependence caveat [U]:** frames inside a capture group are near-duplicates; omissions of the same
  physical sign are likely correlated across frames. Clopper–Pearson treats frames as independent and
  therefore *understates* uncertainty. Mitigation: the audit is a census for 24 of 29 groups, and
  confirmed misses are counted per frame, so correlated misses inflate x_g rather than hide.

## 4. Review protocol

### 4.1 Roles [P]

- **A and B**: two independent human annotators, no communication, separate working copies.
- **C**: human adjudicator, not A or B, resolves every disagreement and every `UNCERTAIN`.
- **Q (audit)**: independent QA reviewer who performs the §3.3 audit; not A, B or C.
- "Human" means Owner-designated persons. AI sessions build tooling and do QA of artifacts but do
  not act as A, B or C. **[V]** Earlier packages (WP7, WP12) recorded PM/Codex provisional visual
  reviews; this contract does not extend that precedent unless the Owner says so (open decision D-1).
- The A/B/C structure follows **[V]** the Review 2 annotation packet (annotators A and B, adjudicator
  C, `verify_pair` disagreement queue, `adjudication_notes.csv`).

### 4.2 Passes

1. **W0 pilot** (A, B, C on 40 frames): freeze this guideline, measure seconds per frame,
   disagreement rate, additions per frame. Results are written into a guideline-freeze note; any
   change after that note forces re-review of W1/W2 frames reviewed under the old text.
2. **Calibration pass** (A and B, 150 frames, **blind**, before they see any overlay on any frame):
   draw every in-scope sign from scratch. Purpose: estimate overlay-mode sensitivity
   `S = (blind-consensus additions also found in overlay mode)/(blind-consensus additions)`.
   Report only; it is a gate only in the failure case of §5.2, AC-3. This pass is the most droppable
   cost item (§7).
3. **Overlay pass** (A and B, all 1,912 frames, wave order): each annotator sees the frame with the
   existing YOLO train labels drawn as thin outlines plus class code, and a plain-image toggle.
   Their task is limited to completeness: add every real in-scope sign that has no label, mask
   what cannot be labelled, flag label defects, and set a frame status.
4. **Adjudication** (C): resolves frames where A and B differ in status or box set (greedy one-to-one
   matching at IoU ≥ 0.5 with equal class key; the IoU-0.5 rule is **[V]** the one VRL-R3 preserves), plus all `UNCERTAIN`. C sees anonymized,
   order-randomized A/B marks and writes a reason in `adjudication_notes.csv`.
5. **QA audit** (Q): audits the §3.3 sample on the adjudicated result, blind to A/B/C identity,
   records `CLEAN` or `MISS_FOUND(box)` per frame. C confirms or rejects each Q finding; only
   C-confirmed misses count as `x_g`.

### 4.3 Frame status and box categories (output vocabulary) [P]

Frame status per annotator: `COMPLETE_NO_ADDITION`, `COMPLETE_WITH_ADDITIONS`, `UNCERTAIN` (reason
required, mirroring Review 2's required reason). Final status after C: `REVIEWED_COMPLETE`
(everything real is labelled or masked) or `REVIEWED_INCOMPLETE_UNRESOLVED` (cannot be completed;
never negative-eligible).

Box `category` column (class key from `m1_yolo_classes.csv` in `derived_key`, else the sentinel):

| Category | Meaning | Becomes, for mining |
| --- | --- | --- |
| `<54-class key>` | real, legible sign of a class in the 54-class map, **not** covered by an existing label (IoU < 0.5 with every label of the same class) | derived added box; a later A1 must treat it as GT, never negative |
| `OUT_OF_SCOPE` | real, legible traffic sign outside the 54 classes; note names the QCVN code if known | mask |
| `UNREADABLE` | a sign is present but its class cannot be decided from the frame | mask |
| `IGNORE_REGION` | sign-like object whose longer side is ≤ 17.5 px or that is too truncated/occluded to label; no class box is added | mask |

- **[V]** Basis: Review 2's verifier accepts class keys or `OUT_OF_SCOPE` with a required note;
  D1-VRL-R2/R3 use ignore regions only for locators ≤ 17.5 px on the longer side, expanded by 25% per
  side, with an unmatched prediction ≥ 50% inside not counted as an FP; WP33 already carries
  `UNKNOWN` and `16:UNREADABLE` boxes as non-trainable real signs.
  **[P]** This contract reuses those thresholds as defaults; D-02 below lets QA challenge them.
- Multiple faces on one pole are boxed individually (**[V]** the VRL pole discs were individual boxes).
- Not recorded at all (they remain background, and are the best hard negatives): billboards, shop
  boards, license plates, vehicle backs, signs facing away from the camera, objects that are
  clearly not traffic signs. A sign-like object the annotator cannot rule out is `IGNORE_REGION`, never silently background.
- **Label defects.** A column `label_issue ∈ {NONE, WRONG_CLASS, BAD_BOX, DUPLICATE}` plus a mask region
  at the true sign extent when an existing box overlaps it with IoU < 0.5. **No existing label is changed**
  (`labels_modified=false`); defects are reported for a separate repair decision.
- Truncated at the frame edge: box clipped to the image, `notes="TRUNCATED"`, and the region is
  masked in the eligibility file regardless of class.
- Class disagreement between A and B at IoU ≥ 0.5 goes to C; C may answer `UNREADABLE`.
- Every proposed box must have `0 ≤ x1 < x2 ≤ width` and `0 ≤ y1 < y2 ≤ height` for **that frame**.
  **[V]** the Review 2 verifier hard-codes `IMAGE_SIZE = (1920, 1536)`, so it cannot be reused unchanged;
  per-frame dimensions come from the frames manifest **[U: train frame sizes not inspected in this session]**.

### 4.4 Tool and formats (compatible with existing packets) [P]

- **Packet layout** copies the Review 2 packet **[V]**: `frames_manifest.csv`, `frame_review_template.csv`
  (`annotator_id, frame_stem, status, notes`), `box_review_template.csv`
  (`annotator_id, frame_stem, derived_key, x1, y1, x2, y2, notes`), `class_map_54.csv` (copy of the pinned
  map), `gallery.html`, `manifest.json` with `support_files_sha256`; adjudication adds
  `adjudicator_C_frame_review.csv`, `adjudicator_C_box_review.csv`, `adjudication_notes.csv`
  (`frame_stem, decision, reason, source_considered`) and, like `verify_review2_ignore_r2`, an
  ignore-regions CSV (`frame_stem, x1, y1, x2, y2, reason`).
  New columns: `group_id`, `wave`, `existing_label_sha256`, `label_issue`.
- **Pixel coordinates**, as Review 2 does; normalized YOLO coordinates are derived by the
  builder, never typed.
- **Box entry.** Baseline: CSV editing plus generated zoom pages with a tick grid (the **[V]**
  D1-VRL R2/R3 hand-drawn-box method: eye estimates recorded, snap only within 1 px). Optional, not
  assumed: a single-file offline HTML canvas tool that exports the CSV; no network and no external
  scripts. **[U]** how Review 2 annotators actually entered boxes, and the build and QA cost of any new tool.
- Packets are built by **new successor modules** (§6.4). No existing file is edited.

### 4.5 Privacy and third-party imagery [P]

- **[V]** DATASET01 licence is unresolved (WP3: repository metadata CC-BY-SA 3.0, card prose 4.0,
  uploader authority and image ownership `UNKNOWN`). Packets are therefore internal review material,
  never redistributed.
- Output root is under `data/processed/` (**[V]** git-ignored, `.gitignore:16`); page images are never committed.
  What may be committed: the manifest, CSVs of stems, keys and coordinates, and this document's
  descendants. No pixels.
- No upload of packet pages or frames to Colab, Drive, a hosted annotation service or any external
  API. Reviewers work on local copies. Independent QA sessions that view pages follow the practice
  already used for D1-VRL QA (pages under git-ignored `docs/review/assets/`); Owner decides
  whether that is acceptable for this packet (D-5).
- Annotators add a `privacy_flag` for any frame with a recognizable face or readable licence plate,
  without transcribing it. Flagged frames never appear in a shared page, report image, demo or
  slide. **[U]** whether DATASET01 frames contain identifiable persons or plates at all; none was inspected here.
- Review notes carry enumerated values and coordinates only; free text must not transcribe plates,
  names or private text. If a page is ever exported for a presentation, a privacy ledger like
  `review2_mini_upload_masked_r10_native_frame_privacy_ledger_2026-11-01.md` is required first.

## 5. Acceptance criteria and effect on A1

All bounds below are **proposals**, pre-registered here and frozen by Owner approval of this contract.
Changing a bound after any review starts voids the package. They change no D-05 gate or any threshold.

### 5.1 Criteria

- **AC-1 Coverage and integrity.** Every roster frame has A and B rows and a final status; C resolves 100%
  of status/box disagreements and `UNCERTAIN`; manifests and pins verify; no stem outside the
  1,912; no `0248`/quarantined stem; flags false; roster equals the export manifest's train list.
- **AC-2 Reviewer agreement (report, with a stop).** Report raw frame-status agreement, Cohen's κ
  (and prevalence, because κ is unstable at low prevalence) and box-level F1 between A and B at IoU ≥ 0.5.
  If raw agreement < 0.85 in the first 400 reviewed frames, stop, re-brief and re-review those frames.
- **AC-3 Overlay sensitivity (diagnostic, one failure mode).** Report `S` with a 95% interval from the
  calibration set. If the interval's **upper** limit is < 0.5, overlay mode is not fit for purpose:
  the Owner chooses between blind re-review and an A1 restricted to the audited sample.
  Otherwise `S` informs but does not gate (R_res does).
- **AC-4 Residual-miss bound per group (the gate).** Group g (N_g ≥ 59) passes iff
  `UB(x_g, n_g) ≤ 0.05` using only C-confirmed misses in the audit sample. The **small-group pool**
  (19 groups, 404 frames, census audit) passes iff `UB(x_pool, 404) ≤ 0.02`, i.e. at most 3
  confirmed misses, and no single small group has more than 1. A failing pool excludes all its
  groups. Misses found are repaired in the derived overlay and re-checked by C; a repaired miss does not erase
  its contribution to `x_g`.
- **AC-5 Pooled residual bound.** Stratified pooled R_res has bootstrap 95% upper limit ≤ 0.02.
- **AC-6 Mask completeness for mining.** The 27 existing untrained train boxes (26 `UNKNOWN`, 1
  `16:UNREADABLE`) and every `OUT_OF_SCOPE`, `UNREADABLE`, `IGNORE_REGION` and defect-mask region are
  present in the eligibility file as mask regions.

### 5.2 Effect on A1

| Outcome | Effect on A1 |
| --- | --- |
| Package QA FAIL, or AC-1/AC-2(stop)/AC-5/AC-6 fails | **A1 stays blocked.** Nothing is negative-eligible. |
| AC-3 failure mode triggered | A1 stays blocked until the Owner picks blind re-review or an audited-sample-only A1 in a new record. |
| AC-1…AC-6 pass for all groups | A1 may *proceed to its own contract* (§5.3). Not authorized by this package. |
| Some groups fail AC-4 | A1 is **limited to passing groups' frames with final status `REVIEWED_COMPLETE`**; failing groups contribute no negatives (their positive training data are unchanged). |
| Review stopped early (waves incomplete) | A1 limited to completed frames in passing groups; no extrapolation to unreviewed frames. |

### 5.3 What "negative candidate" may mean afterwards [P]

Even after a pass, a prediction on a reviewed frame is a *negative candidate* only if all hold:
1. frame is `REVIEWED_COMPLETE` and its group passes; WP35 images only via the §1.3 inheritance rule;
2. IoU < 0.1 with every existing label, added box and mask region (the **[V]** D1-VLA-R1
   `NO_LABEL_NEARBY_IOU_LT_0_1` stratum; the other two strata, 66 overlapping at IoU ≥ 0.5 and 10 inside a
   labelled box, are duplicate or box-extent issues and are not candidates), and ≥ 50% of its area is not inside any mask region
   (the VRL ignore-region rule);
3. A1's own contract, independent QA and explicit Owner authorization exist.

Review-derived added boxes are a **derived overlay**, like the D1-VRL directories. They are not training labels. Using them as
positive labels is a separate label-repair decision, not an A1 step and not made here.

## 6. Outputs, manifest, determinism, flags and QA order

### 6.1 Outputs (to be produced only after the §6.5 approvals) [P]

Under `data/processed/d1_train_label_review_r1/` (git-ignored): `roster.csv`, `frames/`,
`frames_manifest.csv`, `frame_review_template.csv`, `box_review_template.csv`, `class_map_54.csv`,
`gallery.html`, wave and calibration/audit lists, annotator A/B files, `adjudicator_C_*.csv`,
`adjudication_notes.csv`, `qa_audit.csv`, `train_completeness_overlay_r1.csv` (added boxes and mask
regions, pixel and normalized), `frame_eligibility_r1.csv`
(`frame_stem, group_id, final_status, group_gate, negative_eligible, wp35_inheritable`) and
`group_gate_r1.json`.
Committed (no pixels): the manifest `docs/review/generated/d1_train_label_completeness_review_r1_manifest.json`
and CSVs of coordinates, plus a report and QA record in `docs/review/`.

### 6.2 Manifest and determinism [P]

- Canonical JSON (sorted keys, compact separators, finite numbers), written once with
  `O_CREAT | O_EXCL | O_NOFOLLOW`, after every pin is re-verified, as in **[V]** R3 contract §7.
- The manifest pins: every evidence file in §2, the builder/verifier modules and tests, the seed
  `20261105`, the key function text, wave/calibration/audit lists, the source `stem_list_sha256`,
  per-frame image and label SHA-256, `schema_version`, and the flags. It never pins a QA record.
- Rebuilding from the same inputs must be byte-identical; any pin drift, symlink, path escape or
  unknown stem fails closed. Rosters (frames, boxes, regions) are exact allowlists; counts are
  derived, not trusted.
- Flags in manifest and report: `sealed_test_accessed=false`, `training_authorized=false`,
  `labels_modified=false`, plus `inference_run=false` (P-1 would require its own record).
  Source labels under `data/processed/m1_yolo/labels/train/` are byte-unchanged before and after
  (hash recorded). No file is moved or deleted.

### 6.3 Verifier [P]

The verifier fails closed on: missing/extra frame rows, status outside the vocabulary, an
`UNCERTAIN` without a reason, `COMPLETE_WITH_ADDITIONS` without boxes or `COMPLETE_NO_ADDITION`
with boxes, `OUT_OF_SCOPE` without a note, a duplicate box, an
out-of-frame box, a key not in the 54 classes, a C row not covering the queue, a QA finding not
resolved by C, an audit sample that differs from the deterministic list, a group gate not
recomputable from the audit CSV, or any pin mismatch. This mirrors **[V]** `verify_pass`,
`verify_pair`, `verify_adjudication`.

### 6.4 Code placement [P]

New files only: `scripts/build_d1_train_label_completeness_packet_r1.py`,
`scripts/verify_d1_train_label_completeness_r1.py`, tests under `tests/` or `detector/tests/`. They
copy the Review 2 patterns but import nothing from the uncommitted Review 2 scripts. Graft before change:
`graft callers` on any shared helper, then rebuild and check Graft. Default code gate:
`uv run ruff check src tests && uv run pytest -q && uv lock --check`.

### 6.5 QA order (normative) [P]

1. **Independent QA of this contract** (includes the open decisions in §8).
2. **Owner approval** (ratifies bounds, roles, waves, Option C vs S, P-1 yes/no).
3. **Build the packet** (builder + verifier + tests; byte-identical rebuild).
4. **Human review** (W0 → calibration → overlay → adjudication → QA audit).
5. **Independent QA of the package** (lineage, completeness, recomputed gates, flags).

Recommended refinement **[P]**: a short *packet-lineage QA* between steps 3 and 4, because a defective packet wastes
the dominant cost (human hours). The Owner decides (D-6).

## 7. Cost estimate (human hours) and unknowns

All per-frame inputs are **[U]** until the W0 pilot measures them; ranges are assumptions, not data.

| Item | Assumption | Low | Central | High |
| --- | --- | ---: | ---: | ---: |
| Overlay pass, A **and** B | 12 / 18 / 30 s per frame × 1,912 frames, two people | 12.7 | 19.1 | 31.8 |
| Adding boxes, A **and** B | 100 / 300 / 600 additions × 30 s, two people | 1.7 | 5.0 | 10.0 |
| Blind calibration, A **and** B | 150 frames × ~76 s, two people | 6.3 | 6.3 | 6.3 |
| Adjudication, C | 10% / 17.5% / 25% of frames × 60 / 90 / 120 s | 3.2 | 8.4 | 16.0 |
| QA audit, Q | 1,230 frames × 12 s (plus confirmations by C ≈ 0.5 h) | 4.6 | 4.6 | 4.6 |
| Onboarding, W0 pilot, guideline note (A, B, C) | 2 h each | 6.0 | 6.0 | 6.0 |
| **Total across four reviewers** | | **≈ 35 h** | **≈ 49 h** | **≈ 75 h** |

- About 12 h per person on the central line, roughly 2–3 working days each, in parallel for A/B.
- Biggest swing: adjudication rate. Most droppable: calibration (−6.3 h, at the cost of an unmeasured
  anchoring risk). **Option S** (1,230 frames) costs ≈ 60–65% of the overlay lines.
- Builder, verifier, tests and (optional) tool: engineering hours are not included and **[U]**; the
  optional box-drawing tool is the largest of those unknowns. Independent QA effort for steps 1 and 5 is separate.
- Owner calendar: **[U]** annotator identities and availability.

### 7.1 Unknowns carried forward

- U-1 Train missing-label rate and additions per frame; validation figures are only a motivating prior.
- U-2 Within-group correlation of omissions (design effect); bounds assume independence.
- U-3 Whether overlay mode anchors reviewers (calibration measures it only roughly).
- U-4 Train frame dimensions, decode success, and roster/stem-list-hash agreement; the builder must verify.
- U-5 How Review 2 annotators entered boxes; whether any tool is reusable.
- U-6 Presence of identifiable persons/plates in DATASET01 frames; licence authority.
- U-7 Whether the pilot under-detects unlabelled train signs (hypothesis in §3.4).
- U-8 YOLO-id → code mapping for the six target ids (duplicate codes in the class map).
- U-9 Whether any later model (N54, Cascade, fusion) should share this package: out of scope here.

## 8. Open decisions for QA and Owner

- **D-1** Who are A, B, C, Q; may AI sessions ever count as reviewers (default: no).
- **D-2** Ratify the ≤ 17.5 px ignore rule, 25% expansion, ≥ 50% inside, IoU 0.5 and IoU 0.1 as defaults.
- **D-3** Class-presence stratum from the R10 val class table (default) or train-only stratification.
- **D-4** Census (recommended) vs Option S (1,230 frames); keep or drop the calibration pass.
- **D-5** Handling of pixel viewing by AI QA sessions for DATASET01 frames.
- **D-6** Insert a packet-lineage QA before human review.
- **D-7** P-1 pilot-on-train prioritization: authorize inference separately, or never.
- **D-8** Who decides after W1 whether to continue to W2.

## 9. Claim register (summary)

| Claim | Class | Source |
| --- | --- | --- |
| A1 blocked until a QA-passed human train-label-completeness package exists | V | R3 contract §6 |
| 214 R10 background FP; six classes = 176 (82.2%) | V | R10 packet lines 45–53 |
| 64 boxes + 40 ignore regions added in D1-VRL-R3; FP 214 → 150 → 110 | V | VRL R3 report |
| Validation labels were incomplete (≥ 15.7% of audited signs) | V (arithmetic) | VLA/VRL reports, 104 / (560 + 104) |
| Train labels incomplete, and by how much | **U** | never audited |
| 27 train frames hold real but deliberately unlabelled boxes | V | export manifest; WP33 recount |
| WP35: 1,800 images from 180 train frames in 10 groups | V | lineage CSV |
| Train = 1,912 frames in 29 groups; 786 target-class frames | V (recount) | split frames, WP33 boxes |
| Census is the recommended design; waves, seed, bounds, roles, formats | P | this contract |
| Pilot-on-train prioritization | P (needs separate authorization) | §3.4 |
| Hours 35 / 49 / 75 | P (assumptions) | §7 |
| Packet builder, verifier, tool | P (nothing built) | §6 |

## Appendix A — Start-of-task record (2026-11-05)

`graft check .` → `graph check: OK — the wiring graph is in sync with the code` (deep layer not
built; 6,159 nodes pending the optional meaning tier).

`git log --oneline -3`:

```text
17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn
399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS
5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met
```

`git status --short | head -60` (first 60 lines; more entries exist beyond line 60; every one is an
Owner or other-session change preserved as-is):

```text
 M PROJECT_MEMORY.md
 M docs/product_roadmap.md
 M docs/review_index.md
 M scripts/run_parallel_checks.py
 M src/cpv301_autodrive/app_pages/07_demo.py
 M src/cpv301_autodrive/dataset01_view.py
 M src/cpv301_autodrive/dataset01_view_r1.py
 M src/cpv301_autodrive/presentation.py
 M src/cpv301_autodrive/views.py
 M tests/test_e0_compute_readiness.py
 M tests/test_web_app.py
 M tests/test_wp35_rare_class_enrichment.py
?? detector/colab/audit_classifier_data_r1.py
?? detector/colab/build_cascade_b0_bundle_r1.py
?? detector/colab/cascade_b0_r1.ipynb
?? detector/colab/d1_train_a3_r1.ipynb
?? detector/colab/d1_train_a3_r2.ipynb
?? detector/colab/diagnose_cascade_classifier_r1.py
?? detector/colab/evaluate_cascade_b0_r1.py
?? detector/colab/evaluate_cascade_b0_r2.py
?? detector/colab/evaluate_compact_improvement_r1.py
?? detector/colab/evaluate_compact_improvement_r2.py
?? detector/colab/evaluate_d1_a3_r2_common_r1.py
?? detector/colab/evaluate_vgg16_54_r1.py
?? detector/colab/evaluate_vgg16_54_r2.py
?? detector/colab/evaluate_vgg16_54_r3.py
?? detector/colab/evaluate_vgg16_54_r4.py
?? detector/colab/evaluate_yolo11n_n1_r1.py
?? detector/colab/latency_cascade_b0_r1.py
?? detector/colab/latency_cascade_b0_r2.py
?? detector/colab/latency_cascade_b0_r3.py
?? detector/colab/package_d1_a3_r2_result_r1.py
?? detector/colab/render_cascade_b0_report_r1.py
?? detector/colab/render_cascade_b0_report_r2.py
?? detector/colab/render_cascade_b0_report_r3.py
?? detector/colab/render_cascade_b0_report_r4.py
?? detector/colab/run_d1_colab_a3_r1.py
?? detector/colab/run_d1_colab_a3_r2.py
?? detector/colab/train_compact_improvement_r1.py
?? detector/colab/train_compact_improvement_r2.py
?? detector/colab/verify_cascade_b0_completion_r1.py
?? detector/colab/verify_cascade_b0_completion_r2.py
?? detector/colab/verify_cascade_b0_completion_r3.py
?? detector/colab/verify_cascade_b0_completion_r4.py
?? detector/m1/dynamic_threshold_conflict_eval_r6.py
?? detector/m1/dynamic_threshold_eval_r1.py
?? detector/m1/dynamic_threshold_eval_r3.py
?? detector/m1/dynamic_threshold_overlap_audit_r5.py
?? detector/m1/dynamic_threshold_r1.py
?? detector/m1/dynamic_threshold_r2.py
?? detector/m1/dynamic_threshold_r2_r1.py
?? detector/m1/resumable_train_a3_r1.py
?? detector/m1/sahi_eval_r1.py
?? detector/m1/val_reeval_r1.py
?? detector/m1/val_reeval_r2.py
?? detector/tests/test_cascade_b0_completion_verifier_r1.py
?? detector/tests/test_cascade_b0_completion_verifier_r2.py
?? detector/tests/test_cascade_b0_completion_verifier_r3.py
?? detector/tests/test_cascade_b0_completion_verifier_r4.py
?? detector/tests/test_cascade_b0_eval_readiness.py
```

## Appendix B — Graft locations of reusable patterns

- M1 export and train list: `scripts/build_m1_yolo_dataset.py` (`derive`, `split_lists`, `label_text`,
  `MANIFEST_PATH`); consumers `detector/m1/yolo54_improvement_r3.py` (`EXPORT_MANIFEST`),
  `scripts/build_m1_colab_bundle.py`, `scripts/build_d1_cascade_detector_dataset.py`.
- WP35 lineage and transform: `scripts/build_wp35_rare_class_enrichment.py` (`MIN_TARGET_PX`, crop
  planner, "never cut a sign").
- Packet flow: `scripts/build_review2_annotation_packet_r1.py::build_packet`; verifiers
  `verify_review2_annotations_r1.py` (`verify_packet`, `verify_pass`, `verify_pair`),
  `verify_review2_adjudication_r1.py::verify_adjudication`, `verify_review2_ignore_r2.py::verify_ignore_r2`.
- Derived labels, ignore regions: `detector/m1/val_relabel_r3.py`.
- Pin/manifest/determinism: `detector/m1/yolo54_improvement_r3.py`.

## Appendix C — Hand-off conditions

This contract is not in force until independent QA passes it and the Owner approves it. It does not
unblock A1, authorize training, inference or labelling, or change D-05. `PROJECT_MEMORY.md` and
`docs/review_index.md` are untouched by this session; routing entries are for a separate task.
