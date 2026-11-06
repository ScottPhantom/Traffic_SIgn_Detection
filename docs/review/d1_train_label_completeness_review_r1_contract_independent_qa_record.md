# D1 train-label-completeness review R1 contract — independent QA record

Status: `INDEPENDENT_QA_PASS_GIOI_HAN__4_MEDIUM_8_LOW__ADDENDUM_REQUIRED_BEFORE_OWNER_APPROVAL`
Boundary: `DOCUMENT_REVIEW_ONLY_NO_PACKET_NO_LABEL_EDIT_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST`
Flags: `sealed_test_accessed=false`, `training_authorized=false`, `labels_modified=false`,
`inference_run=false`
Reviewer: an independent Claude Code QA session that did not write the contract. Branch
`yolo11n-dual-track-r1`, HEAD `7a95591`, 2026-11-05 (Asia/Ho_Chi_Minh).
Reviewed file: `docs/review/d1_train_label_completeness_review_r1_contract.md` (untracked), SHA-256
`93375fdf720a094a9db80f6471370d3dc48ed736ef9cc02317a35d3c14f4237f`. The hash matches the brief and
was rechecked unchanged at the end of the review. The contract was not edited. This record is the
only file created.

Verdict: PASS giới hạn — 0 Critical, 0 High, 4 Medium, 8 Low. The design meets the hard requirements: train only, sealed test never read, flags, QA → Owner → build → review → QA order, a deterministic seed and lists, a pass/fail for every group, and no negatives from unreviewed frames. All 31 pins match. Every roster count except one reproduces. M1 is that exception: the target-class stratum uses the wrong class-id space, so the correct count is 938 frames, not 786. M1–M4 must be resolved in an append-only addendum before the Owner ratifies the contract or a packet is built. Nothing here unblocks A1.

## Claim tags

**[V]** verified by this QA with a command below; **[P]** proposal (this record's corrections);
**[U]** unknown.

## L1–L9 summary

| Check | Result | Basis (detail in the sections below) |
| --- | --- | --- |
| L1 Evidence | PASS | 31/31 pins rehash equal **[V]**; tracked state agrees (25 clean, 4 untracked Review 2 scripts, `PROJECT_MEMORY.md` modified, still `5571f6a1…`). Every cited file:line says what the contract claims (§A). |
| L2 Counts | PASS with M1 | Train roster 1,912, `stem_list_sha256` `6ac76750…` recomputed, 29 groups, sizes, 404-frame small-group pool, 5,442/5,415/27 boxes, 27 frames with untrained boxes, 3 empty frames, WP35 1,800/12×150/180 sources/10 groups, 1,230 audit and 765/465 splits: all reproduce **[V]**. Target-class frames: 786 reproduces only under the YOLO-id reading, which is wrong (M1); the correct count is **938**. |
| L3 Scope and leakage | PASS | Train is the only reviewed population. Val and the sealed test are never selection inputs; the test hash `afa03d4b…` is cited from the export manifest only. D-3 (class-level ids from the R10 val table) affects wave order only, not membership, gates or labels. It is consistent with the R10 Track A, so it is acceptable if disclosed and ratified. The WP35 decision is justified by lineage (with L-1). |
| L4 Sampling design | PASS with M2, M4, L-7, L-8 | Seed `20261105` and the SHA-256 key are fixed; W0, the calibration allocation (largest remainder, sum 150) and the audit list are computable **[V]**. All eight Clopper–Pearson values are exact, and 59/93 are the true minima **[V]**. Gaps: the gate measures only misses the auditor can see (M2); within-group clustering is unhandled for the 5 sampled groups (L-7); the P-1 exclusion rule conflicts with the audit list (M4). P-1 is clearly a proposal needing separate inference authorization, with `inference_run=false` **[V]**. |
| L5 Review protocol | PASS with M3, L-2, L-3, L-4 | A/B/C/Q separation, AI sessions excluded by default (D-1), C blind to identity. The blind-calibration design is contaminated (M3). Agreement and merge rule (L-2), taxonomy precedence and the IGNORE_REGION extension beyond VRL (L-3), privacy vs "no external API" (L-4). |
| L6 Acceptance and A1 effect | PASS with L-5 | Bounds pre-registered and frozen by Owner approval. Every group has a rule: 10 groups with N_g ≥ 59 are under AC-4; 19 groups / 404 frames are in the pool **[V]**. §5.2 and §5.3 exclude unreviewed, unresolved and failing-group frames, and WP35 enters only by inheritance. The AC-2 stop has no terminal rule (L-5). |
| L7 Outputs, flags, order | PASS | Three required flags plus `inference_run=false`. Canonical JSON with `O_CREAT|O_EXCL|O_NOFOLLOW` matches R3 §7 **[V]**; byte-identical rebuild; exact allowlists; no pixels committed (`data/processed/*` ignored at `.gitignore:16` **[V]**). Order QA → Owner → build → review → QA (§6.5) plus optional lineage QA (D-6). |
| L8 Cost and unknowns | PASS with L-6 | 34.5 / 49.4 / 74.7 h recomputed from the stated assumptions **[V]**. Claims are tagged; the §9 register has one misclassified [V] (786, M1). Unknowns U-1…U-9 are reasonable; add Q sensitivity and audit mode (M2) and the provisional nature of D-02 groups (L-7). |
| L9 Gate | PASS | `uv run ruff check src tests` → `All checks passed!`; `uv lock --check` → `Resolved 201 packages`, exit 0 **[V]**. |

## A. L1 — evidence citations checked

- R3 contract §6 (`d1_yolo54_improvement_r3_contract.md:215-223`): it states `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`, that "the train split may contain unlabelled real signs", and that A1 "can only follow a QA-passed human train-label-completeness review package. R3 defines none." §7 has canonical JSON and `O_CREAT | O_EXCL | O_NOFOLLOW`. **Matches.**
- R10 packet lines 45–53: six predicted classes 10/12/23/30/46/39 = 53/44/35/19/13/12 FP, totalling 176/214 = 82.2%. Lines 76–100: D1-EA-R1 package requirements and Track A "Mine hard negatives only from the training split…", prioritizing 10/12/23/30/46/39. **Matches.**
- Next-direction proposal line 17, the "Hard-negative từ train" row: it cites R10 :45-53/:76-100, keeps R10 214 and R3 150 apart, and says "Đầu tiên QA độ đầy đủ nhãn train và tiêu chí negative" ("first, QA train-label completeness and the negative criterion"). **Matches.**
- D1-VLA-R1 report: strata 10 / 138 / 66; decisions 7 / 4 / 9 / 2 / 116; 112 unique; 104 HIGH/MEDIUM proposals. **Matches** (116+9+4+7+2 = 138; 138+66+10 = 214).
- D1-VRL R1: 26 re-fitted boxes + 78 ignore regions; the QA record says FAIL on H1, 0 C / 1 H / 0 M / 5 L. R2: 64 added (38/23/3) + 40 ignore; QA PASS with 1 Medium. R3: 64 + 40, 214 → 150 (0.399/img) → 110, "circular by construction"; QA PASS 0/0/0/4 Low; owner record `OWNER_ACCEPTED_AS_DERIVED_VALIDATION_LABELS__NOT_YET_EVALUATION_AUTHORITY`. "R3 added 64 boxes from reviewing pilot FPs" is correct: the VLA audited the pilot's R10 background FPs at conf 0.20. **Matches.**
- 15.7% arithmetic: 104/(560+104) = 0.1566. It is correctly framed as a lower bound for validation groups only.
- M1 export manifest: train `frames` 1912, `boxes` 5415, `frames_with_untrained_boxes` 27, `empty_label_frames` 3, `stem_list_sha256` `6ac767509def…`. The test `stem_list_sha256` is `afa03d4b6deb…`; only the manifest field was read. `build_m1_yolo_dataset.py::derive` builds all split labels from one `wp33_derived_boxes.csv`, using `train_eligible == "True"` rows. **Matches.**
- Review 2 scripts: `FRAME_COLUMNS`/`BOX_COLUMNS`, required `UNCERTAIN` reason, `OUT_OF_SCOPE` needs a note, `IMAGE_SIZE = (1920, 1536)` hard-coded, `NOTES_COLUMNS` (`…decision, reason, source_considered`), ignore CSV `(…, x1, y1, x2, y2, reason)`. **Matches** (keyed by `source_video_frame`, so the contract's `frame_stem` is a stated rename).
- `val_relabel_r3.py` `SMALL_PX = 17.5`; the VRL R3 report says "A re-evaluation must keep the IoU-0.5 matching rule". **Matches.** That is an evaluation rule, though, not an A/B agreement rule (L-2).
- WP35 builder `plan_geometry`: rotation plus crop without padding; the "never cut a sign" refusal applies to **all** WP33 boxes of the frame, including UNKNOWN/EXCLUDED, not only train-eligible ones. The contract's "labelled" is therefore accurate in the WP33 sense. Manifest `WP35_REAL_FRAME_AUGMENTATION_AWAITING_QA`, `training_only=true`. **Matches.**
- WP7/WP12 precedent: `wp12_cross_split_review_batch_b_report.md:6,18` records a "PM/Codex provisional visual reviewer". **Matches.**
- The snapshot was authored at HEAD `17db663`. Commit `7a95591` (fusion R1) since then did not alter any pinned file; all 31 hashes are equal.

## B. Findings

### Medium (must be fixed by an addendum before Owner approval)

**M1 — The target-class stratum uses the wrong class-id space; the [V] claim "786" is wrong.** The contract reads the R10 ids 10/12/23/30/39/46 as YOLO ids (P.130, R.415a, W.203b, S.505a-xe tải và xe công, P.127-50, W.233) and asks QA to confirm (U-8). Evidence shows they are **WP33 derived keys**. In `d1_ea_r1_predictions.csv` (the R10 D1-EA export), `gt_class` agrees with the WP33 derived keys on 334/334 val stems with GT, and with the YOLO ids on 158/334. On the 176 stems where the two spaces differ, the score is 176/176 for derived keys and 0/176 for YOLO ids **[V]**. The R10 confusions also read naturally only in key space: 32 P.123b↔7 P.123a, 41↔39/40 (all P.127), 46 P.131a↔10 P.130. The correct target set is keys {10 P.130, 12 R.415a, 23 P.111a+P.111b, 30 S.505a-xe tải, 39 P.127-60, 46 P.131a} (YOLO ids 10/12/25/32/40/48). That gives **938 target-class frames, 974 other** **[V]**. Per-group counts that change: C0051 208→244, C0038 163→206, C0040 0→75, C0022 63→68, C0036 40→44, C0021 11→0. The rest are unchanged. Corrected W0∩W1 = 25 of 40. Effect: W1/W2 membership, the §3.2 table, the §9 register line and the "stop after W1" scope. No gate, coverage or sealed-test consequence. **[P] Correction:** restate §3.2/§3.3/§9 with derived keys and 938/974, and resolve U-8. Alternatively adopt the D-3 train-only stratification, which removes the val dependency altogether.

**M2 — The gate bounds only *auditor-detectable* residual misses.** R_res counts misses that one auditor Q finds and C confirms. Q's sensitivity is never measured. §4.2 step 5 audits "on the adjudicated result", which implies overlay mode, so Q likely shares the anchoring that AC-3 worries about. AC-4/AC-5 are therefore lower-bound statements on the true residual rate, while the contract presents them as the rate bound. For the 5 sampled groups, the audit list is also computable by anyone holding the seed and key text, so A/B/C could know which frames will be audited. **[P] Correction:** (a) name the estimand "auditor-detectable residual"; (b) Q draws blind first, then compares with the adjudicated overlay, or Q's sensitivity is measured on the calibration set; (c) preferably audit all 1,912 frames: +682 frames × 12 s ≈ **+2.3 h**. This removes sampling, the predictability issue and most of L-7. Otherwise keep the audit list out of the A/B/C packet.

**M3 — The blind calibration is contaminated by memory, and the AC-3 trigger does not match its rationale.** The same A and B draw the 150 frames blind and later review the same frames in overlay mode. Recall of their own blind pass inflates S. Separately, the stated purpose is to detect sensitivity "well under 0.7". AC-3, however, fires only when the 95% upper limit is < 0.5: with about 40 blind additions that needs S ≤ 13/40 = 0.325 (Wilson) **[V]**. A sensitivity of about 0.5–0.6 passes silently. **[P] Correction:** use a crossover (A blind on half X1 and overlay on X2; B the reverse; S compares the blind consensus of one with the overlay of the other), and align the AC-3 threshold with the rationale or state the 0.325 effective trigger explicitly.

**M4 — The P-1 exclusion rule contradicts the deterministic audit and would leave high-risk frames unaudited yet eligible.** §3.4 excludes P-1 frames (pilot fires with no label) from the rate estimate, calibration and **audit sample**. §3.3 defines the audit as lowest keys among *all* frames, "excluding none". Under the census those frames are still reviewed and can become negative-eligible in a passing group without ever entering the gate. That is exactly the enriched-miss population. Under the census, reordering creates no selection bias, so no exclusion is needed. **[P] Correction:** under the census, P-1 changes order only, and P-1 frames stay in the hash-defined calibration and audit lists. Under Option S, P-1 frames are an additional purposive set reported separately; the hash sample is unchanged and P-1 frames outside it are eligible only if reviewed.

### Low

- **L-1 WP35 facts and mechanics.** "180 sources × 10 transforms" is an average: per-source use ranges from 5 to 50 images **[V]**. The non-duplication argument gets stronger, not weaker. The lineage CSV rounds `angle_deg` (2 dp), `crop_scale` (3 dp) and `crop_x/y` (1 dp), so the "builder's own transform" must be obtained by replaying `augment()`'s seeded RNG (`random.Random(f"{SEED}:{key}:{index}")`), not by rebuilding from the CSV. A rotated mask maps to its axis-aligned hull, which is conservative and acceptable. 6 of the 10 WP35 source groups are in the small-group pool, so a pool failure removes most WP35 inheritance. This is worth stating to the Owner.
- **L-2 Agreement and merge rule.** Review 2's `verify_pair` flags any non-identical box set (exact equality). The contract instead accepts A/B agreement at IoU ≥ 0.5 with the same key, citing VRL's evaluation-matching rule, and does not say which coordinates enter the overlay when A and B agree without C. **[P]** Specify the rule (for example, C confirms all additions, or the box is the coordinate mean or the union) and record the deviation from Review 2.
- **L-3 Taxonomy precedence.** `IGNORE_REGION` is extended to "too truncated/occluded to label" objects of any size, while VRL R2/R3 allow ignore only for locators ≤ 17.5 px, and the builder refuses others. The "TRUNCATED" rule makes a sign both a class box and a mask. A badly boxed existing sign (IoU < 0.5) qualifies both as `BAD_BOX`+mask and as an addition. **[P]** Add one precedence table. Also record the frame resolution the 17.5 px threshold applies to: D1-EA val frames are 960×540, while Review 2 hard-codes 1920×1536 (U-4).
- **L-4 Privacy wording.** "No upload … to any external API" conflicts with AI QA sessions viewing DATASET01 pixels, which transmits them to a model API. D-5 must be decided explicitly before the build, and the no-upload sentence should carve out or forbid that use.
- **L-5 AC-2 has no terminal rule.** After a stop, re-brief and re-review, it is unstated what happens if agreement is still < 0.85. **[P]** Allow at most one re-brief cycle, then `A1 stays blocked` pending an Owner decision. The re-review hours are not in §7.
- **L-6 Cost presentation.** Recomputed totals are exact. However, "≈ 12 h per person" hides an uneven load: on the central line A and B carry about 17 h each, C about 11 h and Q about 4–5 h. The calibration figure of 76 s/frame has no stated source and no range. The central 300 additions are below the validation prior: 104/376 ≈ 0.28 per frame, or about 530 over 1,912 frames, and that prior is itself a lower bound. The adding-boxes line should centre at about 500+.
- **L-7 Clustering.** Clopper–Pearson and the within-group frame bootstrap assume independent frames. The "inflate rather than hide" argument holds only for census-audited groups; for the 5 sampled groups the bound is anti-conservative. D-02 groups are "provisional AI visual review" (`d02_owner_decision_record.md:26`), so the strata themselves are not certified capture units. **[P]** Use a census audit (M2c), or resample contiguous stem runs within a group.
- **L-8 Test rows in pinned CSVs; numeric rule.** `wp36_r1_split_frames.csv` and `wp33_derived_boxes.csv` physically contain test rows, and `build_m1_yolo_dataset.split_lists()` hashes the test list as a G0.7 guard. **[P]** The builder must filter to `split=train` and must not call `split_lists()`, or the record must state that hashing the sealed stem list is not test access. `UB(1,93) = 0.049994`, which passes by 6×10⁻⁶. The rule should say the comparison uses the unrounded value; the printed "0.0500" passes under ≤ either way.

## C. Recount detail (L2) **[V]**

From `wp36_r1_split_frames.csv`, `split=train` rows only: 1,929 rows (TRAIN 1,911, BACKGROUND 1 = `0544`/D02-C0014, QUARANTINED 17 in C0038 8 / C0051 8 / C0002 1). `0248` is absent. Roster = non-quarantined = 1,912; its `"\n".join(sorted)` SHA-256 is `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`, equal to the export manifest. That resolves the contract's "[U: not recomputed]".

WP33 boxes on roster stems: 5,442 = 5,415 eligible + 27 not. The 27 are 26 `UNKNOWN`/`UNKNOWN_EVAL_ONLY` ("class 31 routed to UNKNOWN") and 1 `16:UNREADABLE`/`EXCLUDED`, one box per frame across 27 frames. Frames with no eligible label: `0544`, `1297`, `1298` (the last two are UNKNOWN only). 54 classes have boxes.

Groups: 29. Sizes 505, 218, 190, 119, 115, 87, 75, 68, 66, 65 (10 groups > 60, all ≥ 59, totalling 1,508), plus 19 groups of 3–45 totalling 404. Audit: Σmin(N_g, 93) = 1,230 = 765 (24 groups ≤ 93) + 465 (C0051/C0038/C0027/C0002/C0049). Per-group target counts under the contract's YOLO-id reading reproduce its table exactly (786). The corrected key-space counts are in M1.

WP35 lineage: 1,800 rows, 12 keys × 150, 180 distinct sources, all `use=TRAIN` and all in the roster, 10 groups exactly as listed; `source_group_id` agrees with WP36 on every row.

Clopper–Pearson one-sided 95% upper bounds (exact, bisection on the binomial CDF): UB(0,59) 0.049508, UB(0,58) 0.050339, UB(0,93) 0.031699, UB(1,93) 0.049994, UB(1,92) 0.050526, UB(2,93) 0.066150, UB(0,87) 0.033848, UB(1,87) 0.053368, UB(3,404) 0.019080, UB(4,404) 0.022513. The smallest n with UB(1,n) ≤ 0.05 is 93; with UB(0,n) ≤ 0.05 it is 59.

Hours (recomputed): overlay 12.75 / 19.12 / 31.87; additions 1.67 / 5.00 / 10.00; calibration 6.33; adjudication 3.19 / 8.36 / 15.93; audit 4.1 + 0.5; onboarding 6. Totals **34.5 / 49.4 / 74.7 h**.

## D. Commands run and results

Start of task (HEAD `7a95591`, as expected):

```text
$ graft check .
graph check: OK — the wiring graph is in sync with the code. (deep layer not built; 6317 nodes pending the optional meaning tier)
$ git log --oneline -3
7a95591 feat(d1): fusion R1 YOLO54+CompactCNN relabel ablation — NO_GO, result QA'd
17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn
399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS
$ shasum -a 256 docs/review/d1_train_label_completeness_review_r1_contract.md
93375fdf720a094a9db80f6471370d3dc48ed736ef9cc02317a35d3c14f4237f
```

`git status --short | head -60` at the start (Owner and other-session changes, preserved; more entries exist beyond line 60):

```text
 M PROJECT_MEMORY.md
 M docs/product_roadmap.md
 M docs/review/cam_hanh_trinh_display_rename_r1_2026-11-04.md
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
```

Review commands (read-only; scripts kept in the session scratchpad, run with `python3 -I`):

| Command | Result |
| --- | --- |
| Rehash of the 31 §2 pins plus `git status --porcelain` per path | 31/31 equal; states as claimed |
| `sed`/`awk`/`grep` on R3 §6–§7, R10 :40–102, next-direction :17, VLA, VRL R1–R3 reports, QA and owner records, M1 manifest, Review 2 scripts, `val_relabel_r3.py`, WP35 builder, `.gitignore`, `d02_owner_decision_record.md` | citations as in §A |
| `graft grep "stem_list_sha256"`, `graft skeleton scripts/build_m1_yolo_dataset.py`, `graft skeleton scripts/build_wp35_rare_class_enrichment.py` | located `list_sha256`/`split_lists`/`derive`/`render` and `plan_geometry`/`augment` |
| `recount.py` (train rows of WP36 and WP33, classes CSV, WP35 lineage) | §C figures |
| U-8 check: `d1_ea_r1_predictions.csv` `gt_class` vs WP33 derived keys of the same val stems | 334/334 key-space vs 158/334 YOLO-id; discriminating stems 176/176 vs 0/176 |
| Clopper–Pearson, Wilson, hour arithmetic (pure Python) | §C values; AC-3 effective trigger S ≤ 0.325 at 40 additions |
| `git check-ignore -v data/processed/d1_train_label_review_r1/x docs/review/assets/x` | `.gitignore:16` and `.gitignore:41` |
| `uv run ruff check src tests` | `All checks passed!` (exit 0) |
| `uv lock --check` | `Resolved 201 packages in 4ms` (exit 0) |

Data-access disclosure: this QA read validation **class metadata** (the `gt_class` column of the QA-passed D1-EA export, and WP33 rows of those val stems) only to resolve the contract's own open point U-8. It was not used to select, order or stratify anything, and no val pixels were viewed. Test rows inside the two pinned CSVs were filtered out and not used. No path with a `test` component was opened. No image of any split was opened.

## E. SHA-256 summary

| File | SHA-256 |
| --- | --- |
| Reviewed contract | `93375fdf720a094a9db80f6471370d3dc48ed736ef9cc02317a35d3c14f4237f` |
| 31 contract pins (§2 of the contract) | all equal to the values printed there, rechecked 2026-11-05 at HEAD `7a95591` |
| `docs/review/generated/d1_ea_r1_predictions.csv` (read for U-8 only) | not pinned by the contract; addendum M1 should pin it if it cites it |
| Recomputed train `stem_list_sha256` | `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372` |
| This record | reported in the hand-over; self-embedding would change it |

## F. Hand-off

1. An append-only addendum to the contract fixes M1–M4. The Low items are recommended. Then comes a short delta QA of the addendum only.
2. Owner approval, per §6.5, follows only after that, together with D-1…D-8 (D-3 now informed by M1; D-5 by L-4).
3. No packet, label, inference, training, D-05 or threshold change is authorized by this record.
   A1 stays `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`.

`sealed_test_accessed=false` · `training_authorized=false` · `labels_modified=false` · `inference_run=false`
