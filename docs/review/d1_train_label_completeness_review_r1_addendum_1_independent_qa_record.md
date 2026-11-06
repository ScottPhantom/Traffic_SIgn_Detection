# D1 train-label-completeness review R1 — addendum 1 — independent delta QA record

Status: `DELTA_QA_PASS_GIOI_HAN__0_CRITICAL_0_HIGH_1_MEDIUM_7_LOW__ONE_SENTENCE_FIX_BEFORE_OWNER_APPROVAL`
Boundary: `DOCUMENT_REVIEW_ONLY_NO_PACKET_NO_LABEL_EDIT_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST`
Flags: `sealed_test_accessed=false`, `training_authorized=false`, `labels_modified=false`, `inference_run=false`
Date: 2026-11-05 (Asia/Ho_Chi_Minh). Main checkout branch `yolo11n-dual-track-r1`, HEAD `7a95591` (as stated in the brief; git was not run in the main checkout).
Reviewer: independent QA agent spawned by the coordinating Claude session (did not author).
Reviewed file: `docs/review/d1_train_label_completeness_review_r1_addendum_1.md`, SHA-256
`85434212e6fe989b99903534443278f987c55f0110843e73c109f090e81a5275`. It equals the brief, and I rechecked it unchanged at the end of the review. No repository file was edited.

Verdict: PASS giới hạn — 0 Critical, 0 High, 1 Medium, 7 Low. M1–M4 and L-1…L-8 from the contract QA are closed. Every number I could recompute matches: 938/974, the per-group table, the W0/W1/W2/C150/X1/X2 hashes, the max-x tables, the Wilson triggers, the WP35 recount and the cost. Scope, flags, QA order and the sealed-test boundary are unchanged. One finding is new. The AC-3 `n < 20 → NOT_EVALUABLE` branch removes small-n triggers that the superseded rule had, and the addendum does not disclose this (M-D1). That loosens AC-3 beyond what M3 required.

**Ready for Owner approval of the human hours?** Not as-is. It becomes ready once M-D1 is adopted, preferably in a short append-only addendum 2 or verbatim in the Owner approval record. M-D1 is a one-sentence rule change. It does not alter any count, list, hash or hour figure, so only a one-line delta check is needed. The Low items can be carried into the builder specification or the Owner record and do not block approval. Nothing here unblocks A1. A1 stays `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`.

## D1–D7 summary

| Check | Result | Basis |
| --- | --- | --- |
| D1 Pins | PASS | Addendum hash equals the brief. Contract `93375fdf…` and QA record `7bb3bf89…` are equal. All 10 cited files in addendum §1 rehash equal. The 9 re-pins equal contract §2, and the new pin `d1_ea_r1_predictions.csv` is `cb3cb05f…`. The cited lines are correct: `FOCUS_KEYS` at `yolo54_improvement_r3.py:143`, `TRAIN_STEM_LIST_SHA256` at :130, `augment()` at WP35 builder :201 and its RNG at :202, `split_lists()` at `build_m1_yolo_dataset.py:91`, and the R10 table at :45–53. The author's three scratch scripts were found in session `2b616079…` and hash equal to §12; I did not run them. **[V]** |
| D2 M1 | PASS | My own recount from the train rows only gives: roster 1,912; hash `6ac76750…`; 29 groups; WP33 rows 5,442 = 5,415 eligible + 27 not; 0 non-eligible rows in T. T-frames (eligible `derived_key ∈ {10,12,23,30,39,46}`) = **938**, other = **974**. The label-file cross-check (yolo_id ∈ {10,12,25,32,40,48} in `labels/train/<stem>.txt`) gives 938 with an identical frame set. The contract's reading (keys {10,12,21,28,38,44}) gives 786. Per-key frames are 596/150/264/93/164/220. The six changed group cells, the 11 T-groups, W0∩W1 = 25 (20 under the old reading), C150 with 72 T-frames (X1 35, X2 37), 28/29 groups, C0029 = 0 and all quotas match. All six list hashes match byte for byte. `FOCUS_KEYS` gives 506 frames, intersection 308, union 1,136. The class map confirms key 32 = yolo 33 and key 41 = yolo 42, as well as key 30 = yolo 32 / yolo 30 = key 28, key 39 = yolo 40 / yolo 39 = key 38, and yolo 23 = key 21. The §3.3 id-space evidence reproduces: 697 = 483 PAIRED + 214 BACKGROUND; BACKGROUND counts 53/44/35/19/13/12; key space 483/483 vs yolo 272/483; on the 211 rows where the two disagree, keys explain 211 and yolo explains 0. Keeping the R10 six keys rather than `FOCUS_KEYS` is reasoned and offered to the Owner as D-A1. **[V]** |
| D3 M2, M3, M4 | PASS with M-D1, L-D2 | **M2:** (a) the estimand is renamed `R_res_aud` and declared a lower bound, with U-10. (c) The audit is a census of all 1,912 frames, which removes predictability and the sampled-group clustering problem. (b) is met in reduced form: Q gives a plain-image count before seeing the overlay rather than a full blind drawing, and Q's sensitivity is explicitly not measured. This is acceptable because the over-claim, which was the substance of M2, is removed; the count rule has a gap (L-D2). The census max-x table is recomputed exactly. **M3:** the crossover is exactly as the QA required: A is blind on X1 and overlays X2, B the reverse, and no annotator sees a frame in both modes. The AC-3 threshold is aligned (Wilson upper < 0.70), and the triggers 9/20, 22/40, 35/60 and the old 13/40 are verified. The new `n < 20` exemption is a regression (M-D1). **M4:** the eligibility invariant R-M4.1 requires a Q audit for every eligible frame and the verifier fails closed. The P-1 exclusion is struck under the census. Under Option S, P-1 frames form a purposive stratum that must be reviewed **and** audited, which is stricter than the QA asked. No high-risk frame can be eligible without an audit. **[V] text / [P] design** |
| D4 Low items | PASS | Each of L-1…L-8 is adopted with a binding rule. L-1 also corrects the QA record: 7 of 10 WP35 source groups are in the small-group pool, not 6 (1,050/1,800 images, 111/180 sources; per-source use 5–50) **[V]**. L-4 tightens D-5 to "no pixels to AI QA". L-3's precedence table has a drafting gap (L-D3). |
| D5 No silent changes | PASS with M-D1 | Unchanged: train only, the 17 quarantined stems and `0248` excluded, `afa03d4b…` cited from the manifest only, four flags, QA order with the delta QA inserted before the Owner step, A1 blocked, and the 5%/2%/2% bounds. L-8 strengthens the test-row handling. The census raises the allowed miss counts (16/5/4) at the same 5% bound; this is disclosed and left to the Owner as D-A2. The calibration timing moves from "before any overlay" to "before W1 overlay" (L-D6); this resolves a contract inconsistency and is listed under the superseded §4.2 step 2. The single undisclosed loosening is M-D1. |
| D6 Cost and claims | PASS | Recomputed: low 34.6, central 55.3, high 98.2 h (91.5 without the reserve). Per role A = B 16.9, C 11.9, Q 9.6 h. The central delta of +5.9 h against 49.4 decomposes as stated. Claims carry [V]/[P]/[U] tags, the register is updated (786 reclassified, U-8 closed, U-10 added), and the decisions D-1…D-8, D-A1 and D-A2 are listed. Q onboarding is not costed (L-D7). **[V]** |
| D7 Completeness and gate | PASS with L-D1 | 606 lines, §0–§13 present, no section cut mid-sentence. The file ends with the flags line and a final newline. One dangling promise is a symptom of the cut-off: §12 says the gate is "recorded in the hand-over below", but §13 does not contain it. I ran the gate myself: `uv run ruff check src tests` → `All checks passed!`; `uv lock --check` → `Resolved 201 packages in 4ms`; exit 0. **[V]** |

## Findings

### Medium (fix before the Owner approves the hours)

**M-D1 — The AC-3 `n < 20` branch removes small-n triggers that the superseded rule had, and this is not disclosed.** R-M3.5 makes AC-3 `NOT_EVALUABLE` and non-blocking whenever `|B_ref| < 20`. The superseded rule (Wilson upper < 0.5) had no floor and fired at small n. Under it, n = 10 fired at k ≤ 1, n = 15 at k ≤ 3 and n = 19 at k ≤ 5. The new rule fires at none of these **[V]** (`dqa_add1_ac3small.py`). The addendum compares the two rules only at n = 40, which makes the new rule look uniformly stricter. Small n is realistic: B_ref now comes from one blind reviewer per frame on 150 frames, and the train additions rate is unknown (U-1). In that regime neither the overlay sensitivity S nor Q's sensitivity would be measured. That is the anchoring risk M2 and M3 address. This loosens AC-3 beyond what M3 required and fails the "as required or better" test of D3 and D5. **[P] Correction (one sentence):** for `1 ≤ n < 20`, apply the same Wilson rule (upper < 0.70 triggers), because Wilson is valid at small n; at a minimum, keep the superseded `upper < 0.5` as a floor. Only `n = 0` is `NOT_EVALUABLE`. State the effective small-n triggers in the record.

### Low (carry into the builder specification or the Owner record; non-blocking)

- **L-D1 Truncation symptoms.** §12 promises the gate result "in the hand-over below", and §13 does not give it. §12 also says "11 cited files", while §1 lists 10. Because the addendum is append-only, it should not be edited. This record supplies the gate result (above).
- **L-D2 `n_adj` counts artefacts, not objects.** The overlay count `n_adj` (labels + added boxes + mask regions) counts a duplicate label twice. A defective existing label also counts twice, since L-3 adds a mask at its true extent. A frame with one such artefact and one missed sign then passes `q_blind_count ≤ n_adj` as `CLEAN`, and detection falls back on overlay vigilance. It is also unstated whether the builder prints `n_adj`, which the verifier rule needs. **[P]** Define `n_adj` as the number of distinct objects, merging artefacts at IoU ≥ 0.1, and have the builder print it on the overlay page. A better option is for Q to place one blind point per object, which the verifier can match by location.
- **L-D3 L-3 precedence row (1) has no "already correct" exit.** Read literally, a correctly labelled sign (IoU ≥ 0.5 with an existing label of the same key) matches row (1) and gets a `label_issue`. **[P]** Add a row 0: a match to an existing label at IoU ≥ 0.5 with the same key and an acceptable box means covered, nothing recorded. Also flag for D-2 that a distinct small sign ≥ 50% inside a larger label box (stacked or supplementary plates) becomes a `label_issue` + mask instead of an added box. That is safe for A1 because it is masked, but it under-counts additions.
- **L-D4 X1/X2 index base.** "Even positions" is 0-based (`C150[0::2]`); a 1-based reading swaps X1 and X2. The hashes pin the intended lists **[V]**. **[P]** Write "0-based index" in the builder specification. The largest-remainder tie-break never operates here (boundary remainders 0.452 vs 0.412) **[V]**.
- **L-D5 Enumerations.** Read literally, R-M4.1 makes a frame whose `MISS_FOUND` C *rejected* ineligible. That is conservative, but probably unintended. AC-3 option (i) "blind re-review of W1" leaves W2's treatment open. **[P]** Enumerate `q_audit_result ∈ {CLEAN, MISS_CONFIRMED_REPAIRED, MISS_REJECTED, NOT_AUDITED}` and state the eligibility of each value. Name the scope of the AC-3 re-review.
- **L-D6 Calibration timing.** The contract said "before they see any overlay on any frame"; the addendum says "before the first overlay page of W1", so the W0 overlay pilot comes first. This resolves the contract's own W0-first inconsistency and is covered by the precedence row for §4.2 step 2. The Owner should know about it; no memory effect is possible, because C150 excludes W0.
- **L-D7 Q load.** Q now makes a plain-first count under the L-3 taxonomy, but the 2 h onboarding line covers only A, B and C. The 18 s central estimate covers two pages per frame and is unmeasured **[U]**. **[P]** Add about 2 h of onboarding for Q and time it in W0.

## Commands run and results

All commands were read-only. Scripts are in the scratchpad (`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/`) and were run with `python3 -I`.

| Command | Result |
| --- | --- |
| `shasum -a 256` addendum, contract, QA record | `85434212…`, `93375fdf…`, `7bb3bf89…`: equal to the brief |
| `shasum -a 256` of the 10 files in addendum §1 | all equal to addendum §1 and contract §2 |
| `grep -n` / `sed -n` on `yolo54_improvement_r3.py`, WP35 builder, M1 builder, R10 packet, class map | lines as cited (D1) |
| `dqa_add1_recount.py` (`1886a553…`) | roster/hash/groups, 938/974/786, label-file cross-check 938 with an equal set, per-group table, `FOCUS_KEYS` 506/308/1,136, W0/W1/W2/C150/X1/X2 hashes, quotas, WP35 pool 7/1,050/111, Clopper–Pearson max-x for the ten groups, pool, pooled and W1-stop, Wilson triggers: all equal to the addendum |
| `dqa_add1_u8.py` (`cd3428f0…`) | 697/483/214; BACKGROUND 53/44/35/19/13/12; 483/483 vs 272/483; 211/211 vs 0/211 |
| `dqa_add1_ac3small.py` (`8bd0f81d…`) | small-n trigger comparison (M-D1); hours 34.64/55.30/98.15, A = B 16.94, C 11.86, Q 9.56, delta +5.90 |
| `find /private/tmp/claude-501 -name "*addendum1.py"`, `shasum`, `grep -i test` | the author's scripts hash equal to §12; no test path is opened |
| `uv run ruff check src tests` | `All checks passed!` (`uv run` refreshed the editable install in `.venv`; no tracked file changed) |
| `uv lock --check` | `Resolved 201 packages in 4ms`, exit 0 |

**Data-access disclosure.** (1) All counts come from train rows only. Test rows inside `wp36_r1_split_frames.csv` and `wp33_derived_boxes.csv` were tokenized while parsing and dropped by the `split == "train"`/roster filters; they were not counted or used. (2) The train label files were read as text (class ids only) for the 1,912 roster stems. (3) To verify addendum §3.3, I read the class-level columns (`disposition`, `pred_class`, `gt_class`) of the QA-passed validation export, plus the eligible WP33 `derived_key` of those stems. This is the same scope as the contract QA. Nothing was selected or ordered from them. (4) No image of any split was opened, no model was loaded, no path with a `test` component was opened, and `split_lists()` was not called.

## SHA-256 summary

| File | SHA-256 |
| --- | --- |
| Reviewed addendum 1 | `85434212e6fe989b99903534443278f987c55f0110843e73c109f090e81a5275` |
| Contract | `93375fdf720a094a9db80f6471370d3dc48ed736ef9cc02317a35d3c14f4237f` |
| Contract QA record | `7bb3bf89350474cc5f01413415ee122c7984880baa196dbcf2ddb169b9c6bfbc` |
| `d1_ea_r1_predictions.csv` (new pin) | `cb3cb05f0cadc7d2c3e077120d5b1311648247f74a9648e287da1c4be915f1dd` |
| Recomputed train `stem_list_sha256` | `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372` |
| W0 / W1 / W2 | `89aa32f4…a549ad6` / `db6729d7…ad55ef1` / `4d91956c…506ecea` (equal to addendum §3.5) |
| C150 / X1 / X2 | `9770d3fd…a602d2` / `dcf33e8a…3bea50` / `a5aaddad…302596` (equal to addendum §3.5) |
| This record | reported in the hand-over; embedding it here would change it |

## Required corrections (proposals)

1. **[P] M-D1 (blocking for Owner approval):** in an addendum 2, or verbatim in the Owner approval record, replace the `n < 20` branch of R-M3.5 with "for `1 ≤ n`, Wilson upper < 0.70 triggers; `n = 0` is `NOT_EVALUABLE`" (at a minimum, keep `upper < 0.5` as a small-n floor), and state the effective triggers.
2. **[P] L-D2…L-D5, L-D7 (non-blocking):** write them into the builder and verifier specification: `n_adj` as distinct objects printed by the builder, or Q blind points; L-3 row 0; 0-based X1/X2; the `q_audit_result` enumeration and the scope of the AC-3 re-review; Q onboarding about 2 h.
3. **[P] Owner inputs:** decide D-A1 (QA view: the R10 six keys are fit for the stated background-FP purpose) and D-A2 (QA view: the census gate is statistically sound at the same 5% bound and repairs every detected miss; the higher absolute counts should be stated in the Owner record). Also decide D-1…D-8, with L-D6 noted.

No packet, label, inference, training, D-05 or threshold change is authorized by this record. The sealed test (`afa03d4b…`) was not accessed.

This record was written outside the repository, in the worktree `tmp/` folder, and will be placed unchanged into `docs/review/`.

`sealed_test_accessed=false` · `training_authorized=false` · `labels_modified=false` · `inference_run=false`
