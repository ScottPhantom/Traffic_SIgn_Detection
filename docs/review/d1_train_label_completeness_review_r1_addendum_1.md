# D1 train-label-completeness review R1 — addendum 1 (fixes QA findings M1–M4)

Status: `FROZEN_AWAITING_DELTA_QA`
Boundary: `DESIGN_ADDENDUM_ONLY_NO_PACKET_NO_LABEL_EDIT_NO_DATA_MOVE_NO_TRAINING_NO_INFERENCE_NO_SEALED_TEST`
Flags (this addendum and every artifact it later specifies): `sealed_test_accessed=false`,
`training_authorized=false`, `labels_modified=false`, `inference_run=false`
Author: Claude Code session `d1-train-label-completeness-r1-addendum-1`, branch `yolo11n-dual-track-r1`,
HEAD `7a95591`, 2026-11-05 (Asia/Ho_Chi_Minh). Documentation only; no existing file was edited.
This file is append-only from the moment of its delta QA: any later change is a new addendum, never an edit.

Claim tags (as in the contract): **[V]** verified in this session by a command listed in §12;
**[P]** proposal (nothing here is implemented); **[U]** unknown.

## 0. Purpose and precedence

The independent QA of the contract returned PASS giới hạn with four Medium and eight Low findings and
required an append-only addendum before the Owner may ratify the contract or approve human hours.
This addendum fixes M1–M4 with binding resolutions, answers L-1…L-8, restates every number that M1
changes, and updates the cost estimate. It authorizes nothing. A1 stays
`A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`.

**Precedence rule [P].** Where this addendum and the contract disagree, this addendum governs for the
sections in the table below. Every contract text not listed there stands unchanged.

| Contract text | Superseded or amended by | What changes |
| --- | --- | --- |
| §1.2 (class-presence stratum, "six class ids") and §3.2 (786, per-group table, text) | §3 (M1) | six ids are derived keys; 938/974; table restated |
| §3.3 waves W1/W2, "stop after W1" | §3.5, §3.6 (M1) | W1 = 938, W2 = 974; W1-stop rule restated |
| §3.3 audit sample (1,230 frames) | §4 (M2) | census audit of all 1,912 frames; 1,230 kept only for Option S |
| §3.3 calibration set, §4.2 step 2 | §5 (M3) | crossover; lists fixed and hashed |
| §3.4 P-1 exclusions | §6 (M4) | exclusions removed under the census |
| §3.5 R_res, §5.1 AC-1, AC-2, AC-3, AC-4, AC-5 | §4, §5, §6, §7 | wording and numeric tables below |
| §4.3 vocabulary, §4.2 step 4 merge rule, §4.5 privacy | §7 (L-2, L-3, L-4) | precedence table, merge rule, wording |
| §7 cost, §9 register | §8, §10 | recomputed |

## 1. Pins and start-of-task record

SHA-256 values taken 2026-11-05 on the working tree. Both inputs are untracked files.

| Input | SHA-256 | Match |
| --- | --- | --- |
| `docs/review/d1_train_label_completeness_review_r1_contract.md` | `93375fdf720a094a9db80f6471370d3dc48ed736ef9cc02317a35d3c14f4237f` | equals brief **[V]** |
| `docs/review/d1_train_label_completeness_review_r1_contract_independent_qa_record.md` | `7bb3bf89350474cc5f01413415ee122c7984880baa196dbcf2ddb169b9c6bfbc` | equals brief **[V]** |

Files this addendum cites that the contract did not pin, or re-pins because the fix depends on them:

| Evidence | SHA-256 | Use |
| --- | --- | --- |
| `docs/review/generated/d1_ea_r1_predictions.csv` (new pin) | `cb3cb05f0cadc7d2c3e077120d5b1311648247f74a9648e287da1c4be915f1dd` | M1: id-space evidence, class-level columns only |
| `detector/m1/yolo54_improvement_r3.py` (contract pin, rehashed) | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` | M1: `FOCUS_KEYS` (line 143) and `TRAIN_STEM_LIST_SHA256` |
| `docs/review/generated/m1_yolo_classes.csv` (rehashed) | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` | M1: key ↔ yolo_id map |
| `docs/review/generated/wp33_derived_boxes.csv` (rehashed; train stems only) | `4b9307003ce8fd3c1d50763a5950d3d57cf6b2ee6df3aeef74621707067501c0` | M1 recount |
| `docs/review/generated/wp36_r1_split_frames.csv` (rehashed; `split=train` rows only) | `8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a` | roster, groups |
| `docs/review/generated/m1_yolo_export_manifest.json` (rehashed) | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` | roster hash |
| `docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md` (rehashed) | `9ec8dd0d9e2866ef098ca3afada624ea5562837531f9b077981c45940ed0f78f` | M1: the six-class table, lines 45–53 |
| `docs/review/generated/wp35_enrichment_lineage.csv` (rehashed) | `e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed` | L-1 recount |
| `scripts/build_wp35_rare_class_enrichment.py` (rehashed) | `be194e3d397d8294b693aa0b9638daedb5af3ff42b055b187d1de3bc9c05559f` | L-1: `augment()` line 201, RNG line 202 |
| `scripts/build_m1_yolo_dataset.py` (rehashed) | `3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93` | L-8: `split_lists()` line 91 |

Every one of these equals the value printed in the contract or the QA record where one exists
**[V]**. The recount scripts live in this session's scratchpad, not in the repository; their SHA-256 values are
in §12 and copies are in the shared notes folder for the delta QA.

Start of task **[V]** (`graft check .`): `graph check: OK — the wiring graph is in sync with the code`
(deep layer not built; 6,446 nodes pending the optional meaning tier).

`git log --oneline -3`:

```text
7a95591 feat(d1): fusion R1 YOLO54+CompactCNN relabel ablation — NO_GO, result QA'd
17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn
399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS
```

`git status --short | head -60` (first 60 lines; more entries exist; every one is an Owner or
other-session change, preserved as-is; `git status` is quoted from the start of the session):

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
?? detector/colab/run_d1_colab_a2_r1.py
?? detector/colab/run_d1_colab_a3_r1.py
?? detector/colab/run_d1_colab_a3_r2.py
?? detector/colab/train_compact_improvement_r1.py
?? detector/colab/train_compact_improvement_r2.py
?? detector/colab/verify_cascade_b0_completion_r1.py
?? detector/colab/verify_cascade_b0_completion_r2.py
?? detector/colab/verify_cascade_b0_completion_r3.py
?? detector/colab/verify_cascade_b0_completion_r4.py
?? detector/m1/a2_repeat_list_r1.py
?? detector/m1/dynamic_threshold_conflict_eval_r6.py
?? detector/m1/dynamic_threshold_eval_r1.py
?? detector/m1/dynamic_threshold_eval_r3.py
?? detector/m1/dynamic_threshold_overlap_audit_r5.py
?? detector/m1/dynamic_threshold_r1.py
?? detector/m1/dynamic_threshold_r2.py
?? detector/m1/dynamic_threshold_r2_r1.py
?? detector/m1/resumable_train_a2_r1.py
?? detector/m1/resumable_train_a3_r1.py
?? detector/m1/sahi_eval_r1.py
?? detector/m1/val_reeval_r1.py
?? detector/m1/val_reeval_r2.py
?? detector/tests/test_a2_repeat_list_r1.py
```

## 2. What does NOT change

Everything here is the contract's text and stays in force exactly as written.

- **Scope: train only.** Reviewed population is the 1,912 roster frames; the 17 quarantined train
  stems and stem `0248` stay outside. Validation and the sealed test are never selection inputs.
- **Sealed test.** `afa03d4b…` is cited from the export manifest only. No path with a `test`
  component is opened, listed or hashed by any artifact this addendum specifies.
- **Flags.** `sealed_test_accessed=false`, `training_authorized=false`, `labels_modified=false`,
  `inference_run=false` in every manifest and report. No existing label is changed.
- **QA order (contract §6.5), normative:** independent QA of the contract → delta QA of this addendum
  → Owner approval → packet build → human review → independent QA of the package. The delta QA is
  inserted before the Owner step; it does not replace any step.
- **A1 stays blocked.** Nothing here makes any frame negative-eligible. No D-05 gate, threshold,
  model, split or label is touched.
- **Roster, groups, roles A/B/C/Q, WP35 decision (§1.3), vocabulary of frame status, canonical-JSON and
  fail-closed manifest rules (§6.2), code placement (§6.4).** Unchanged, except where §7 amends a rule.
- **Bounds.** 5% per group (N_g ≥ 59), 2% for the small-group pool (404 frames), 2% pooled, AC-6, the
  27 untrained boxes. Their numeric values do not change; M2 changes only what they are measured on.

## 3. M1 — the target-class stratum is 938 frames, not 786

### 3.1 QA finding (quoted from the QA record, lines 54–60)

> **M1 — The target-class stratum uses the wrong class-id space; the [V] claim "786" is wrong.** The
> contract reads the R10 ids 10/12/23/30/39/46 as YOLO ids […] and asks QA to confirm (U-8). Evidence
> shows they are **WP33 derived keys**. […] The correct target set is keys {10 P.130, 12 R.415a,
> 23 P.111a+P.111b, 30 S.505a-xe tải, 39 P.127-60, 46 P.131a} (YOLO ids 10/12/25/32/40/48). That gives
> **938 target-class frames, 974 other** **[V]**. […] **[P] Correction:** restate §3.2/§3.3/§9 with
> derived keys and 938/974, and resolve U-8. Alternatively adopt the D-3 train-only stratification,
> which removes the val dependency altogether.

### 3.2 Resolution (binding) [P]

**R-M1.1 Definition.** The six class numbers in the R10 packet table (lines 45–53) are **derived keys**
(the WP33 `derived_key` namespace), not `yolo_id`. The target stratum is
`T = {"10", "12", "23", "30", "39", "46"}` as `derived_key` strings. A frame is in the **target-class
stratum (T-frame)** iff it is a roster frame with at least one WP33 row on it that has
`train_eligible == "True"` and `derived_key ∈ T`. A frame without such a row is an **other frame**.

**R-M1.2 Translation table (the only permitted path from key to yolo_id is `m1_yolo_classes.csv`).**

| derived key | code (derived_code) | yolo_id | R10 background FP |
| --- | --- | ---: | ---: |
| 10 | P.130 | 10 | 53 |
| 12 | R.415a | 12 | 44 |
| 23 | P.111a+P.111b | **25** | 35 |
| 30 | S.505a (xe tải) | **32** | 19 |
| 39 | P.127 (60 km/h) | **40** | 12 |
| 46 | P.131a | **48** | 13 |

Total 176/214 = 82.2% **[V]** (R10 packet lines 45–53; counts equal the rows in
`d1_ea_r1_predictions.csv`, §3.3). Translation traps that the builder and verifier must test, because
the class map reuses codes: key 30 is yolo_id 32, but **yolo_id 30 is key 28** (also S.505a); key 39 is
yolo_id 40, but **yolo_id 39 is key 38** (also P.127); yolo_id 23 is key 21 (W.203b). In the R3 module
`FOCUS_KEYS` the same trap appears: key 32 (P.123b) is yolo_id 33 and key 41 (P.127) is yolo_id 42
**[V]** (`yolo54_improvement_r3.py:143`, class map rows 33 and 42).

**R-M1.3 Namespace rule for every later artifact.** A class value is written with its namespace:
`derived_key` or `yolo_id`. A bare number is rejected by the verifier. Any list of classes copied from an
R10, R3 or Review 2 table is a `derived_key` list unless that table says otherwise, and is translated
through the pinned class map with an assertion on the result.

**R-M1.4 U-8 is closed** by §3.3. D-3 keeps its default (class-level stratum from the R10 table), now
stated in keys. D-3's disclosure stands: only six class-level numbers from a QA-passed validation
document enter this design; they change wave order and stratum labels only, never roster membership,
gates or labels. The train-only alternative remains available and costs nothing in this design.

**R-M1.5 `FOCUS_KEYS` is a different set and is not the stratum.** The brief for this addendum pointed
at `yolo54_improvement_r3.FOCUS_KEYS`. That tuple is `("7","32","41","46")`: the four classes of the R3
class-wise A0b search (three supported critical classes plus key 46). It overlaps the R10 six-class set
only in key 46. It was chosen for false-negative work, not for background false positives, so using it
would replace the stratum's purpose and not repair its id space. This addendum therefore keeps the six
R10 keys, uses the module only as the authoritative example of the key/yolo_id trap, and reports the
`FOCUS_KEYS` counts in §3.4 so the Owner can choose otherwise (decision D-A1, §11).

### 3.3 Evidence that the six numbers are keys [V]

Recomputed independently of the QA record; class-level columns only, no pixels, boxes or stems used for selection.

- `d1_ea_r1_predictions.csv`: 697 rows = 483 `PAIRED` + 214 `BACKGROUND`. The `BACKGROUND` rows
  by `pred_class` are 10: 53, 12: 44, 23: 35, 30: 19, 46: 13, 39: 12 — identical to the R10 table, so the
  table was printed in the namespace of this column.
- That column is in key space: for the 483 `PAIRED` rows `gt_class` is among the WP33 `derived_key`
  values of the same stem on 483/483, and among the stem's `yolo_id` values on 272/483. On the 211 rows
  where the two namespaces disagree, `derived_key` explains 211/211 and `yolo_id` explains 0/211. (The QA
  record counted 176/176 by stem; the unit differs, the conclusion is the same.)

### 3.4 Recount from the pinned train files [V]

Roster: `wp36_r1_split_frames.csv` `split=train` and `use != QUARANTINED` → **1,912** frames,
`"\n".join(sorted(stems))` SHA-256 `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`
(equals the export manifest and `TRAIN_STEM_LIST_SHA256`); 29 groups. WP33 rows on roster stems: 5,442 =
5,415 eligible + 27 not. No non-eligible row carries a key in `T`.

| Namespace and set | Frames |
| --- | ---: |
| **T-frames: eligible rows with `derived_key ∈ {10,12,23,30,39,46}`** | **938** |
| Other frames | **974** |
| Cross-check: train label files, any line with `yolo_id ∈ {10,12,25,32,40,48}`; frame set equals the T-frame set | 938 |
| Contract's reading (ids as yolo_id → keys {10,12,21,28,38,44}) — reproduces its 786 and its table | 786 |
| `FOCUS_KEYS` {7,32,41,46} frames | 506 |
| `FOCUS_KEYS` ∩ T-frames | 308 |
| `FOCUS_KEYS` ∪ T-frames | 1,136 |

Frames by key (eligible rows): key 10: 596, 12: 150, 23: 264, 30: 93, 39: 164, 46: 220 (a frame can hold
several keys, so the six do not add to 938). The label-file check reads
`data/processed/m1_yolo/labels/train/*.txt` for the 1,912 roster stems; the aggregate label hash was
not recomputed **[U]** (the contract's builder must pin it, §6.2).

**Restated per-group table (replaces the contract's §3.2 table).** `T` = T-frames, `contract` = its old
count. Stratum cells are (T, N_g − T).

| Group | N_g | T | contract | | Group | N_g | T | contract |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| D02-C0051 | 505 | **244** | 208 | | D02-C0053 | 25 | 0 | 0 |
| D02-C0038 | 218 | **206** | 163 | | D02-C0007 | 21 | 0 | 0 |
| D02-C0027 | 190 | 137 | 137 | | D02-C0010 | 21 | 0 | 0 |
| D02-C0002 | 119 | 0 | 0 | | D02-C0039 | 18 | 0 | 0 |
| D02-C0049 | 115 | 65 | 65 | | D02-C0008 | 17 | 15 | 15 |
| D02-C0014 | 87 | 0 | 0 | | D02-C0023 | 17 | 0 | 0 |
| D02-C0040 | 75 | **75** | 0 | | D02-C0033 | 16 | 0 | 0 |
| D02-C0022 | 68 | **68** | 63 | | D02-C0037 | 13 | 0 | 0 |
| D02-C0025 | 66 | 0 | 0 | | D02-C0004 | 12 | 0 | 0 |
| D02-C0036 | 65 | **44** | 40 | | D02-C0021 | 11 | **0** | 11 |
| D02-C0019 | 45 | 37 | 37 | | D02-C0016 | 10 | 0 | 0 |
| D02-C0015 | 44 | 44 | 44 | | D02-C0047 | 10 | 0 | 0 |
| D02-C0026 | 38 | 0 | 0 | | D02-C0029 | 3 | 3 | 3 |
| D02-C0013 | 29 | 0 | 0 | | D02-C0043 | 28 | 0 | 0 |
| D02-C0054 | 26 | 0 | 0 | | | | | |

Sum of T: 938 (contract column: 786). Six cells change, exactly the six the QA record named. T-frames occur in
11 groups (C0051, C0038, C0027, C0049, C0040, C0022, C0036, C0019, C0015, C0008, C0029; the contract had C0021
in place of C0040). Nothing in the group sizes, the 404-frame small-group pool or the group gates depends on `T`.

### 3.5 Restated lists, seed and key [V]

Key and seed unchanged: `key(stem) = SHA-256(f"20261105|d1_train_label_completeness_r1|{stem}")` as hex,
smallest lexicographically first. List hash convention: SHA-256 of `"\n".join(stems in the listed order)`,
no trailing newline. The lists below are recomputed values; the packet builder must reproduce them
byte-for-byte or fail closed.

| List | Rule | Size | SHA-256 |
| --- | --- | ---: | --- |
| W0 | 40 lowest keys overall | 40 | `89aa32f4d341bdc9962aeb810b4fc883b8014e10015dbae491daa8f97a549ad6` |
| W1 | all T-frames (includes W0 members), key order | **938** | `db6729d71e3453c991a2fc1283044504891177b7f36b9bccdf8eae811ad55ef1` |
| W2 | all other frames (includes W0 members), key order | **974** | `4d91956c233eea6047cc8dc1b202bee03afd07bf7a68e707a06b9994b506ecea` |
| Calibration C150 | §5.2 | 150 | `9770d3fd7ac0b7a7e932a14e685153ac87613de956a654d1fb075a9f0fa602d2` |
| X1 | even positions of C150 in key order | 75 | `dcf33e8a6d2bf10ff06106389a957dbabce38b62c8cc66954028b3e36e3bea50` |
| X2 | odd positions of C150 in key order | 75 | `a5aaddada14cec3eccdf34aadaa3fb6fa1e28f074d6c892e0f1a5d62cb302596` |

W0 ∩ W1 = **25** of 40 (the contract's reading gives 20); W0 members are re-reviewed in their wave. C150
contains 72 T-frames (X1 35, X2 37) and spans 28 of 29 groups (C0029 gets 0). Wave semantics are unchanged:
W1 is reviewed before W2, and the first 400 frames reviewed in wave order feed the AC-2 stop.

### 3.6 Stop after W1 (restated) [P]

If the Owner stops after W1 (decision D-8), A1 is limited to W1 frames that completed review and audit in a group
that passes, with `n_g` = that group's W1 frames and the same 5% rule, `UB(x_g, n_g) ≤ 0.05` on unrounded values.
A group needs `n_g ≥ 59` to be able to pass at all (`UB(0,59) = 0.0495`, `UB(0,58) = 0.0503`). Under W1-only that is:

| Group | W1 frames n_g | max confirmed misses x_g to pass |
| --- | ---: | ---: |
| D02-C0051 | 244 | 6 |
| D02-C0038 | 206 | 4 |
| D02-C0027 | 137 | 2 |
| D02-C0040 | 75 | 0 |
| D02-C0022 | 68 | 0 |
| D02-C0049 | 65 | 0 |

The other five T-groups (C0036 44, C0019 37, C0015 44, C0008 15, C0029 3 W1 frames) cannot pass and contribute no
negatives after a W1-only stop; there is no pooled gate below 59 frames and no extrapolation to unreviewed frames.
The pooled bound AC-5 is evaluated on the reviewed frames only, with the same 2% limit.

## 4. M2 — the gate bounds only auditor-detectable misses

### 4.1 QA finding (quoted, line 56)

> **M2 — The gate bounds only *auditor-detectable* residual misses.** R_res counts misses that one auditor Q finds
> and C confirms. Q's sensitivity is never measured. §4.2 step 5 audits "on the adjudicated result", which
> implies overlay mode, so Q likely shares the anchoring that AC-3 worries about. AC-4/AC-5 are therefore
> lower-bound statements on the true residual rate, while the contract presents them as the rate bound. For
> the 5 sampled groups, the audit list is also computable by anyone holding the seed and key text […].
> **[P] Correction:** (a) name the estimand "auditor-detectable residual"; (b) Q draws blind first, then compares
> with the adjudicated overlay, or Q's sensitivity is measured on the calibration set; (c) preferably audit
> all 1,912 frames: +682 frames × 12 s ≈ **+2.3 h**. […]

### 4.2 Resolution (binding) [P]

The QA's three corrections are all adopted, with (b) implemented as a plain-image-first commit, because a full
blind drawing by Q on 1,912 frames would cost about 40 h at the calibration rate and the Owner has not asked for it.

**R-M2.1 Estimand name.** `R_res` is renamed **`R_res_aud`, the auditor-detectable residual rate**: the fraction
of frames in which Q, working under R-M2.3, finds a real in-scope sign that A, B and C left neither labelled nor
masked, and C confirms it. Every AC-4/AC-5 sentence, the report and the group-gate JSON use this name. No document
may call `R_res_aud` "the" residual missing rate; it is a lower bound on the true residual rate, because
Q's own sensitivity is unmeasured **[U]** (U-10, §10).

**R-M2.2 Census audit.** Q audits **all 1,912 roster frames**, not a hash sample. The §3.3 audit rule `n_g = min(N_g, 93)`
and the 1,230-frame list are superseded. For every group, `n_g = N_g`. The 1,230-frame list survives only inside
Option S (§6.4). The audit order is the wave order; Q is never told a frame's group, wave or any A/B/C identity.
Because every frame is audited, no list of audited frames exists that A, B or C could anticipate; the
predictability issue disappears and the audit CSV is not shipped to A, B or C.

**R-M2.3 Q works plain-image-first.** For each frame Q first sees only the plain image (no outline, no mark) and
records `q_blind_count`: an integer, the number of distinct real traffic-sign-like objects Q can see that an
annotator would label, mask or class as out of scope. Only then does Q see the adjudicated overlay (labels,
added boxes, mask regions) with its own count `n_adj`. Rule:

- `q_blind_count > n_adj` → Q must locate the extra object(s) and record `MISS_FOUND(box)`; C confirms or
  rejects.
- `q_blind_count ≤ n_adj` → `CLEAN`, unless Q also sees a miss on the overlay, which is recorded the same way.

The audit template gains `q_blind_count` (required integer ≥ 0, entered before the overlay page is opened; the page
order is the control) and keeps `CLEAN`/`MISS_FOUND`. The verifier rejects a blank or negative `q_blind_count` and
any `CLEAN` row with `q_blind_count > n_adj`. That the count really came first is a procedural control
that tooling cannot prove **[U]**; the packet builder generates the plain and overlay pages as separate files so
the order is inspectable.

**R-M2.4 What the gate means and its numeric consequence.** The counting rule is unchanged: only C-confirmed misses
enter `x_g`, and a repaired miss still counts. `UB(x, n)` is the exact one-sided 95% Clopper–Pearson upper
bound on unrounded values, compared with `≤`. Under a census it is a process bound on how often A/B/C leave a
detectable miss, treating frames as exchangeable **[U: within-group correlation]**; it is no longer a sampling
bound. With `n_g = N_g` the pre-registered maximum x_g for a group to pass (`UB(x_g, N_g) ≤ 0.05`) is:

| Group | N_g | max x_g | UB at max x_g | UB at max + 1 | max under the old n_g (93 or N_g) |
| --- | ---: | ---: | ---: | ---: | ---: |
| D02-C0051 | 505 | 16 | 0.047725 | 0.050068 | 1 |
| D02-C0038 | 218 | 5 | 0.047617 | 0.053597 | 1 |
| D02-C0027 | 190 | 4 | 0.047526 | 0.054532 | 1 |
| D02-C0002 | 119 | 1 | 0.039243 | 0.051959 | 1 |
| D02-C0049 | 115 | 1 | 0.040586 | 0.053732 | 1 |
| D02-C0014 | 87 | 0 | 0.033848 | 0.053368 | 0 |
| D02-C0040 | 75 | 0 | 0.039156 | 0.061695 | 0 |
| D02-C0022 | 68 | 0 | 0.043099 | 0.067871 | 0 |
| D02-C0025 | 66 | 0 | 0.044375 | 0.069870 | 0 |
| D02-C0036 | 65 | 0 | 0.045042 | 0.070914 | 0 |

Small-group pool: unchanged (19 groups, 404 frames, already a census): `UB(x_pool, 404) ≤ 0.02`, i.e. x_pool ≤ 3
(`UB(3,404) = 0.019080`, `UB(4,404) = 0.022513`), and no single small group above 1. **[V]** (all values by bisection, pure Python).

**Disclosed trade-off for QA and the Owner.** For the three largest groups the allowed count rises (1 → 16, 5, 4)
because the bound is now taken over all frames; the allowed *rate* is the same 5% upper bound. The old design
left up to 5% of a group's frames unaudited and unrepaired; the census audits and repairs all of them, so the
frames that remain wrong are those both the reviewers and Q missed, roughly `(1 − S_Q)` of the `x_g/N_g` found
**[U: S_Q unmeasured]**. The pooled AC-5 bound (2%) also caps the sum: `UB(27,1912) = 0.0194`, `UB(28,1912) = 0.0200`
(Clopper–Pearson cross-check **[V]**; the bootstrap in §3.5 of the contract is the normative AC-5 estimator). If QA
prefers the old absolute counts, the alternative is to keep the gate on the hash sample and hide that list from
A/B/C; this addendum does not take it (decision D-A2, §11).

**R-M2.5 Q sensitivity.** Not measured, therefore not claimed. A planted-omission probe (remove one existing label
from the overlay Q sees on a hash-chosen 5% of frames) was considered and **not adopted**: it only measures
vigilance on signs that were once labelled, so it overstates sensitivity on signs that three reviewers missed,
and it adds a verifier path. Q's miss rate is carried as U-10. When the Owner needs a number, the route is a
second independent auditor Q2 on a hash sample of the frames Q marked `CLEAN`, specified in its own record.

## 5. M3 — memory contamination and the AC-3 trigger

### 5.1 QA finding (quoted, line 58)

> **M3 — The blind calibration is contaminated by memory, and the AC-3 trigger does not match its rationale.** The
> same A and B draw the 150 frames blind and later review the same frames in overlay mode. Recall of their own
> blind pass inflates S. Separately, the stated purpose is to detect sensitivity "well under 0.7". AC-3, however,
> fires only when the 95% upper limit is < 0.5: with about 40 blind additions that needs S ≤ 13/40 = 0.325 (Wilson)
> **[V]**; a sensitivity of about 0.5–0.6 passes silently. **[P] Correction:** use a crossover […] and align the
> AC-3 threshold with the rationale or state the 0.325 effective trigger explicitly.

### 5.2 Resolution (binding) [P]: crossover with fixed lists

**R-M3.1 Calibration set.** `C150`: for each group, quota `q_g = largest-remainder rounding of 150 · N_g / 1,912`
(ties by `group_id`; the quotas sum to 150), taking the `q_g` lowest-key frames of that group among roster frames
not in W0; C150 is the union, ordered by key. The contract's "proportional to group size" is this rule. List
hash in §3.5; quotas by group (C0051 40, C0038 17, C0027 15, C0002 9, C0049 9, C0014 7, C0040 6, C0022 5, C0025 5,
C0036 5, C0019 4, C0015 4, C0026 3, six groups of 2, nine groups of 1, C0029 0) **[V]**.

**R-M3.2 Crossover.** `X1` and `X2` as in §3.5. **A draws X1 blind and does not see X1 in overlay mode. B draws
X2 blind and does not see X2 in overlay mode.** A reviews X2 in overlay mode; B reviews X1 in overlay mode; both
overlay-review every other roster frame. No annotator ever sees one frame in both modes, so there is nothing to
remember. Both blind passes are complete before either annotator opens the first overlay page of W1 (habit
washout), and the blind mode shows no outline, label or mark. C adjudicates a calibration frame like any other:
one blind row and one overlay row take the place of the A/B pair, with the same merge rules and C sees them
anonymized and order-randomized.

**R-M3.3 Blind additions.** A blind box is an *existing-label re-find* if the L-3 precedence (§7) matches it to an
existing label at IoU ≥ 0.5 with the same key; otherwise it is a *candidate addition*. C confirms or rejects every
candidate addition; the confirmed ones are the **blind reference set** `B_ref`.

**R-M3.4 Estimator.** `S = |{b ∈ B_ref : the other annotator's overlay pass also added a box with the same key at
IoU ≥ 0.5}| / |B_ref|`, pooled over both directions (A-blind vs B-overlay on X1; B-blind vs A-overlay on X2) with
a Wilson 95% interval, and each direction reported separately. Reference limits to state in the report: B_ref is what
one blind reviewer finds, so it excludes signs a blind reviewer also misses, and S therefore measures overlay
sensitivity *relative to a single blind pass*, not to the truth **[U]**. Calibration frames are **excluded from the
AC-2 agreement statistic** (the two rows are in different modes) and reported in their own table; their `A`/`B` rows
count for AC-1 coverage (every roster frame has two annotator rows and at least one `OVERLAY` row).

**R-M3.5 AC-3 (replaces the contract's AC-3).** Let `n = |B_ref|`.

- `n < 20`: AC-3 is `NOT_EVALUABLE`; S, its interval and `n` are reported; AC-3 does not block (the gate is
  AC-4, with Q working under R-M2.3 and independent of overlay anchoring).
- `n ≥ 20` and the Wilson 95% **upper** limit of S is **< 0.70**: AC-3 is triggered. A1 stays blocked until the
  Owner records either (i) blind re-review of W1 by A and B, or (ii) acceptance of overlay mode on AC-4 alone with S
  stated in the record.
- Otherwise AC-3 is reported and does not gate.

The rationale ("detect S well under 0.7") and the trigger now agree: the upper limit is below 0.7 only if the data
show S below 0.7. Effective triggers **[V]** (Wilson): n = 20 → at most 9 of 20 (S ≤ 0.45); n = 40 → at most 22 of
40 (S ≤ 0.55); n = 60 → at most 35 of 60 (S ≤ 0.583). For the record, the superseded rule (upper limit < 0.5) fired
only at 13/40 (S ≤ 0.325) with n = 40, as the QA computed. The calibration remains a diagnostic: it can fail
the package only through this one trigger.

## 6. M4 — P-1 exclusion versus the audit

### 6.1 QA finding (quoted, line 60)

> **M4 — The P-1 exclusion rule contradicts the deterministic audit and would leave high-risk frames unaudited yet
> eligible.** §3.4 excludes P-1 frames […] from the rate estimate, calibration and **audit sample**. §3.3 defines
> the audit as lowest keys among *all* frames, "excluding none". Under the census those frames are still reviewed
> and can become negative-eligible in a passing group without ever entering the gate. […] **[P] Correction:**
> under the census, P-1 changes order only, and P-1 frames stay in the hash-defined calibration and audit lists.
> Under Option S, P-1 frames are an additional purposive set reported separately; the hash sample is unchanged and
> P-1 frames outside it are eligible only if reviewed.

### 6.2 Resolution (binding) [P]

**R-M4.1 Invariant (replaces every weaker eligibility wording, binds the verifier).** A frame is
`negative_eligible` only if **all** hold: final status `REVIEWED_COMPLETE` after A/B/C; **audited by Q** with result
`CLEAN`, or `MISS_FOUND` that C confirmed and that was then repaired in the derived overlay and re-checked by C; and its group passes
the gate. No frame is eligible without a Q audit. `frame_eligibility_r1.csv` gains `q_audit_result`; the verifier
fails closed if `negative_eligible=true` with a blank or `NOT_AUDITED` `q_audit_result`.

**R-M4.2 Census (recommended).** The P-1 clause of §3.4 about exclusion from the rate estimate, calibration and
audit is **struck**. Under the census, P-1 may reorder the review queue only, as §3.4 already says for annotators; a P-1 frame
stays in W1/W2, in the C150 list if the hash puts it there, in the audit and in every gate statistic. Reordering
a complete census cannot bias a census-wide rate, so no exclusion is needed. P-1 still requires its own explicit Owner
authorization to run inference (D-7); nothing here authorizes it.

**R-M4.3 Option S (kept for comparison, restated).** Reviewed and audited frames are the 1,230 hash-list frames of
the contract's §3.3 (n_g = min(N_g, 93), lowest keys), the calibration lists above unchanged. P-1 frames outside that
list are a **purposive additional set**: reviewed by A/B/C and audited by Q under the same protocol, reported
in their own stratum (counts, `x`, rate), never added to `x_g`, the pooled estimate, C150 or AC-2, and the hash list is not
altered. A P-1 frame is `negative_eligible` only if reviewed, audited, `REVIEWED_COMPLETE` and in a passing group
(R-M4.1). Option S frames outside both lists are never eligible. Under Option S the 1,230-frame audit list must be
withheld from A/B/C (the predictability argument of M2 applies to it).

## 7. Low findings (L-1 … L-8)

| ID | Resolution | Status |
| --- | --- | --- |
| **L-1** WP35 facts and mechanics | (a) The contract's "180 sources × 10 transforms" is an average; per-source use varies (QA: 5 to 50). **Binding:** the WP35 inheritance transform is obtained by replaying `augment(context, key, index)` of `scripts/build_wp35_rare_class_enrichment.py` (line 201) with its seeded RNG `random.Random(f"{SEED}:{key}:{index}")` (line 202), importing the builder unedited; the rounded `angle_deg`/`crop_scale`/`crop_x/y` in `wp35_enrichment_lineage.csv` are never used to rebuild geometry. A rotated mask is its axis-aligned hull (conservative). (b) **Recount [V]:** the pool-failure exposure is **7** of the 10 WP35 source groups (C0010, C0013, C0015, C0016, C0019, C0021, C0053), carrying 1,050 of 1,800 images (58%) and 111 of 180 source frames; the QA record said 6 of 10. A small-group pool failure therefore removes most WP35 inheritance. | Adopted; QA's "6" corrected to 7 |
| **L-2** agreement and merge rule | **Binding:** A/B agree on a box when the keys are equal and IoU ≥ 0.5 (greedy one-to-one). An agreed box enters the overlay with coordinates equal to the **mean of the two boxes' corners**, rounded to 0.1 px; no C review is needed for it, and it is inside Q's census. Any status difference, unmatched box, key difference, `UNCERTAIN`, or IoU < 0.5 on a pair goes to C. Deviation recorded: Review 2's `verify_pair` flags any non-identical box set; this package accepts agreement at IoU ≥ 0.5 because the unit here is "is the sign covered", not box regression. | Adopted |
| **L-3** taxonomy precedence | **Binding** order for each real object, first matching row wins: (1) it overlaps an existing label at **IoU ≥ 0.1, or ≥ 50% of its area inside an existing label box**: not an addition; record `label_issue` (`BAD_BOX`/`DUPLICATE` same key, `WRONG_CLASS` different key) and add a mask region at the true extent (the D1-VLA-R1 `NO_LABEL_NEARBY_IOU_LT_0_1` boundary); (2) class decidable and in the 54-class map: added class box (derived key); (3) legible, outside the 54 classes: `OUT_OF_SCOPE`; (4) a sign certainly present, class undecidable, longer side > 17.5 px: `UNREADABLE`; (5) otherwise sign-like and not ruled out: `IGNORE_REGION`. Truncated sign (class decidable): clipped class box **and** mask; the mask only blocks negatives, the box stays ground truth. `IGNORE_REGION` for "too truncated or occluded to label" at any size is a deliberate extension of VRL R2/R3 (≤ 17.5 px only); it is safe because VRL's builder rule applied to the val derived-label artifact and this one is separate, and it is flagged for D-2. **Resolution:** the 17.5 px threshold is defined for a 960 × 540 frame; for a frame of width W the threshold is `17.5 · W/960` px. Train frame dimensions are unverified **[U]** (U-4); the builder lists every frame whose size is not 960 × 540, and the Owner or QA decides on them before review. | Adopted; U-4 stays open |
| **L-4** privacy wording | **Binding replacement of the contract's "no upload to any external API":** no frame or page is uploaded to a hosted annotation service, Colab, Drive or any external API *by the review team*. AI sessions are not reviewers (D-1). **Default for D-5:** AI QA sessions do **not** view DATASET01 train pixels for this package; they verify lineage, hashes, CSVs, counts and recomputed gates only. Viewing pixels transmits them to a model API and needs an explicit Owner record. | Adopted; D-5 default now "no" |
| **L-5** AC-2 terminal rule | **Binding:** at most **one** re-brief cycle. If raw frame-status agreement is < 0.85 in the first 400 reviewed frames (calibration frames excluded, §5.2), stop, re-brief, re-review those 400; if raw agreement on the re-review is still < 0.85 the package stops as `PACKAGE_STOPPED_AGREEMENT`, A1 stays blocked, and the Owner decides in a new record; no second re-brief. Hours reserve in §8. | Adopted |
| **L-6** cost presentation | Per-role loads, a calibration range and a re-centred additions line are in §8. The additions centre moves from 300 to 500 (validation prior 104/376 ≈ 0.28 per frame ≈ 530 over 1,912 frames, itself a lower bound and not a train measurement **[U]**). | Adopted |
| **L-7** clustering | Census removes the five sampled groups' anti-conservative bound (§4.2). **Binding additions:** report for each group the point rate `x_g/N_g`, the number of distinct contiguous-stem runs among its confirmed misses, and state in the report that frames inside a provisional D-02 group are near-duplicates and `UB` treats them as exchangeable. D-02 groups come from provisional AI visual review (`d02_owner_decision_record.md`), so they are review units, not certified capture units. No other correction is made. | Adopted, bound remains an independence-assuming bound |
| **L-8** test rows; numeric rule | **Binding:** the builder reads only rows with `split == "train"`, never calls `build_m1_yolo_dataset.split_lists()` (it recomputes and compares the test list hash), and never recomputes or compares the test `stem_list_sha256`; the roster hash check uses the train list only. Hashing a file that physically contains test rows is a byte hash, not use of the sealed split's content. `UB(1,93) = 0.049994` is not rounded in any comparison; tables use unrounded values and rounded display only. | Adopted |

## 8. Cost estimate (human hours), updated

All per-frame inputs are **[U]** until the W0 pilot measures them; ranges are assumptions, not data. Changes
against the contract's §7: M2 (census audit with a plain-first count), M3 (each calibration frame has one blind
and one overlay reviewer, so the blind work halves and overlay reviews fall by 150), L-5 (re-brief reserve), L-6
(additions, calibration range, per-role split).

| Item | Assumption | Low | Central | High |
| --- | --- | ---: | ---: | ---: |
| Overlay pass, A **and** B | 12 / 18 / 30 s × 3,674 frame-reviews (2 × 1,912 − 150 calibration frames) | 12.2 | 18.4 | 30.6 |
| Adding boxes, A **and** B | 200 / 500 / 900 additions × 30 s, two people | 3.3 | 8.3 | 15.0 |
| Blind calibration (one blind reviewer per frame) | 150 frames × 60 / 76 / 120 s | 2.5 | 3.2 | 5.0 |
| C reconciliation of blind candidate additions | assumption | 0.5 | 1.0 | 2.0 |
| Adjudication, C | 10% / 17.5% / 25% of frames × 60 / 90 / 120 s | 3.2 | 8.4 | 15.9 |
| Census audit, Q (plain-first count + overlay) | 1,912 frames × 12 / 18 / 30 s | 6.4 | 9.6 | 15.9 |
| C confirmation of Q findings | assumption | 0.5 | 0.5 | 1.0 |
| Onboarding, W0 pilot, guideline note (A, B, C) | 2 h each | 6.0 | 6.0 | 6.0 |
| AC-2 re-brief reserve (A and B re-review 400 frames at 30 s; contingency, not expected) | | 0 | 0 | 6.7 |
| **Total across four reviewers** | | **≈ 35 h** | **≈ 55 h** | **≈ 98 h** |

Previous contract totals: 35 / 49 / 75 h. The central total rises by about 6 h (+5.9): the census audit line goes from 4.6 h
to 10.1 h (+5.5 h, with its confirmations), the additions line from 5.0 h to 8.3 h (+3.3 h) and C's reconciliation adds 1.0 h;
the crossover saves 3.2 h of blind work and 0.75 h of overlay. Without the reserve the high total is 91.5 h; the QA's overlay-only
census (12 s, +2.3 h) is the low column. **Central per-role load [V arithmetic]:** A ≈ 16.9 h, B ≈ 16.9 h, C ≈ 11.9 h, Q ≈ 9.6 h
(sum 55.3 h); the contract's "≈ 12 h per person" understated A and B. Stopping after W1 (938 frames, 49% of the roster)
reduces the per-frame lines roughly in that proportion; that is not recomputed here. Engineering hours for builder, verifier, tests and any
tool, independent QA effort and Owner calendar remain **[U]**.

## 9. Updated acceptance criteria (summary of amended wording) [P]

All bounds stay pre-registered; changing any after review starts voids the package.

- **AC-1.** Every roster frame has two annotator rows (mode `OVERLAY` or, on C150 frames, one `BLIND` and one
  `OVERLAY`), a Q audit row with `q_blind_count`, and a final status; C resolves 100% of disagreements and
  `UNCERTAIN`; the 1,912-frame roster hash, manifests and pins verify; flags false.
- **AC-2.** As in the contract, calibration frames excluded, with the L-5 terminal rule.
- **AC-3.** As in §5.2 (`n ≥ 20` and Wilson upper < 0.70, otherwise report only).
- **AC-4.** Group gate on `R_res_aud`: `UB(x_g, N_g) ≤ 0.05` for the ten groups with N_g ≥ 59 (maximum x_g in §4.2);
  small-group pool `UB(x_pool,404) ≤ 0.02` (x_pool ≤ 3, none above 1 per group).
- **AC-5.** Pooled `R_res_aud` (census value `Σ x_g / 1,912`) with the contract's bootstrap upper limit ≤ 0.02.
- **AC-6.** Unchanged (27 untrained train boxes, `OUT_OF_SCOPE`, `UNREADABLE`, `IGNORE_REGION`, defect masks as masks).
- **Eligibility.** R-M4.1 invariant; the contract's §5.2 and §5.3 otherwise stand. A package QA FAIL or any of
  AC-1/AC-2 stop/AC-5/AC-6 failing keeps A1 blocked.

## 10. Claim register after this addendum

| Claim | Class | Source |
| --- | --- | --- |
| R10's six numbers (10/12/23/30/39/46) are derived keys; yolo_ids 10/12/25/32/40/48 | V | §3.3, `d1_ea_r1_predictions.csv`, class map |
| Train T-frames = 938, other = 974; per-group table of §3.4 | V (recount; label-file cross-check equal) | §3.4 |
| The contract's 786 is the count for the yolo_id reading; it was wrong for the stated purpose | V | §3.4 |
| W0 ∩ W1 = 25; W0/W1/W2/C150/X1/X2 hashes | V (recomputed lists) | §3.5 |
| `FOCUS_KEYS` = {7,32,41,46}, 506 frames, 308 shared with T | V | §3.4 |
| Max-x tables (ten groups, pool, W1-stop), Clopper–Pearson values | V (bisection) | §3.6, §4.2 |
| Wilson trigger table for AC-3 | V | §5.2 |
| WP35: 7 of 10 source groups are in the small-group pool, 1,050 / 1,800 images | V | L-1 |
| Cost 35 / 55 / 98 h | P (assumptions) | §8 |
| Census audit, plain-first Q, crossover, AC-3 rule, eligibility invariant | P | §4–§6 |
| Train missing-label rate; Q sensitivity `S_Q` (U-10); within-group correlation; train frame sizes (U-4); label-hash aggregate | **U** | — |
| Train labels are incomplete, and by how much | **U** | never audited |

New unknown U-10: Q's sensitivity (the true residual rate cannot be bounded from `R_res_aud` alone). Contract unknowns U-1…U-9
stand; U-8 is closed by §3.3.

## 11. Open decisions after this addendum

- **D-1** unchanged (AI sessions never count as reviewers by default).
- **D-2** now also ratifies the L-3 precedence table and the `IGNORE_REGION` extension.
- **D-3** informed by M1: default keeps the R10 six keys (class level only); train-only stratification remains available.
- **D-4** census vs Option S (Option S restated in §6.3); keep the calibration (crossover, ≈ 3 h).
- **D-5** default changed to "no pixels to AI QA"; an Owner record is needed to change it.
- **D-6, D-7, D-8** unchanged (packet-lineage QA; P-1 inference authorization; who decides after W1).
- **D-A1 (new).** Stratum set: the R10 six keys (this addendum) or `FOCUS_KEYS` (506 frames) or their union (1,136 frames).
- **D-A2 (new).** Gate on the full census (this addendum; allowed misses 16/5/4 in the three largest groups) or on a hidden hash sample (at most 1 miss in each of the five sampled groups).

## 12. Commands run and data-access disclosure

Read-only; scripts run with `python3 -I`, kept in the session scratchpad, copies placed in the shared notes folder.

| Step | Result |
| --- | --- |
| `graft check .`; `git status --short \| head -60`; `git log --oneline -3` | §1; HEAD `7a95591` |
| `shasum -a 256` of the contract, QA record and 11 cited files | §1 |
| `graft grep "FOCUS_KEYS"` | `("7","32","41","46")` at `yolo54_improvement_r3.py:143`; a different set in `sahi_eval_r1.py` and `("7","32","41")` in the A2/A3 modules, none used as the stratum |
| `recount_addendum1.py` (SHA-256 `cb7ae1f40f680aa988d846ad1cdb24fcce0a1ec70853e2e87cd9318c76ebda91`) | roster, 938/974, group table, FOCUS counts, label-file cross-check, W0/W1/W2/C150/X1/X2, WP35 pool recount |
| `extra_addendum1.py` (SHA-256 `50ba28297e718197967088916fa530ca7e860e58029d828afa1d3dd37fdb8948`) | Wilson triggers, pooled and W1-stop Clopper–Pearson limits, hours |
| `u8_addendum1.py` (SHA-256 `495ebd150f2c80b57567a9c4c5982de7653da19b99045e32b4f286e3f69f8c91`) | §3.3 id-space evidence |
| `uv run ruff check src tests && uv lock --check` | recorded in the hand-over below |

**Data-access disclosure.** (1) Train only for every count in §3.4–§3.6. (2) §3.3 read the class-level columns
(`pred_class`, `gt_class`, `disposition`) of the QA-passed validation export, plus the `derived_key` of the same stems in the
WP33 table, solely to confirm the id space the contract asked QA to confirm (U-8); nothing was selected, ordered or stratified
from it, and no validation pixel, box coordinate or stem list was used. (3) Parsing the pinned CSVs necessarily tokenizes test rows; they were dropped at
read (`split == "train"` and stem filters), not counted and not used; no path with a `test` component was opened;
`split_lists()` was not called. (4) No image of any split was opened; no model was loaded. (5) Disclosed incidental
read: `grep` lines of `detector/m1/a2_repeat_list_r1.py` appeared while resolving `FOCUS_KEYS` usages; it was not edited, not
cited as evidence here, and no other `a2` file was touched.

## 13. Hand-off to the delta QA

Status `FROZEN_AWAITING_DELTA_QA`. The delta QA reviews this file only. Suggested checks: (a) rehash §1 pins;
(b) recount §3.4 from the pinned train rows, including the label-file cross-check and the key/yolo_id table; (c) recompute W0,
W1, W2, C150, X1, X2 and their hashes; (d) recompute the max-x tables and the Wilson triggers; (e) confirm each of M1–M4
is closed and L-1…L-8 answered; (f) confirm §2 changes nothing it should not; (g) decide D-A1 and D-A2 as input to the Owner.
Then, in the contract's order: Owner approval (with D-1…D-8, D-A1, D-A2) → packet build → human review → independent QA of the
package. No packet, label, inference, training, D-05 or threshold change is authorized by this addendum. A1 stays
`A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`.

`sealed_test_accessed=false` · `training_authorized=false` · `labels_modified=false` · `inference_run=false`
