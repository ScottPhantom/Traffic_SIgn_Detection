# D1 train-label-completeness review R1 — addendum 2 (M-D1 and Low findings of the delta QA)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Status: `FROZEN_AWAITING_DELTA_QA`
Author: Claude Code (Opus 5.5), coordinating session.
Boundary: document only. No packet, label edit, inference, training, threshold or D-05 change.
Flags: `sealed_test_accessed=false`, `training_authorized=false`, `labels_modified=false`, `inference_run=false`.

This addendum is append-only. It does not edit the contract, addendum 1 or either QA record. Where it
conflicts with addendum 1, this addendum wins. The only rows it replaces are named in §2.

## 1. Pins

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_train_label_completeness_review_r1_contract.md` | `93375fdf720a094a9db80f6471370d3dc48ed736ef9cc02317a35d3c14f4237f` |
| `docs/review/d1_train_label_completeness_review_r1_contract_independent_qa_record.md` | `7bb3bf89350474cc5f01413415ee122c7984880baa196dbcf2ddb169b9c6bfbc` |
| `docs/review/d1_train_label_completeness_review_r1_addendum_1.md` | `85434212e6fe989b99903534443278f987c55f0110843e73c109f090e81a5275` |
| Addendum 1 delta QA record (written to the worktree `tmp/`, to be placed in `docs/review/` byte for byte as `d1_train_label_completeness_review_r1_addendum_1_independent_qa_record.md`) | `bbcbbca0898df9cde0f61ec3f621c22effe693aad3c761ba156bf82f008cc375` |

The delta QA verdict was `PASS giới hạn` with 0 Critical, 0 High, 1 Medium (M-D1) and 7 Low findings.
The QA wrote that the package becomes ready for Owner approval of the human hours once M-D1 is adopted.

## 2. What this addendum replaces

| Addendum 1 location | Replaced by |
| --- | --- |
| §5.2 R-M3.5, the `n < 20` bullet and the `n ≥ 20` condition | §3 (R-A2.1) |
| §9 AC-3 summary line | §3 (R-A2.1) |
| §4.2 R-M2.3, the definition of `n_adj` | §4 L-D2 |
| §7 L-3, the precedence table (row 0 added before row 1) | §4 L-D3 |
| §3.5, the words "even positions" / "odd positions" | §4 L-D4 |
| §6.2 R-M4.1, the eligibility wording for `q_audit_result` | §4 L-D5 |
| §8, the onboarding line and totals | §5 |

Everything else in the contract and addendum 1 stands unchanged: scope, train-only roster, census,
lists and hashes, crossover, gate bounds, merge rule, privacy, cost inputs other than onboarding,
the QA order, and the A1 block.

## 3. M-D1 — AC-3 applies at every n ≥ 1 (binding) [P]

**R-A2.1 AC-3 (replaces R-M3.5 of addendum 1).** Let `n = |B_ref|` and let `U(k, n)` be the Wilson 95 %
upper limit of S = k/n (z = 1.959964), computed unrounded.

- `n = 0`: AC-3 is `NOT_EVALUABLE`. The report states n = 0, and the Owner record must state it too.
- `n ≥ 1` and `U(k, n) < 0.70`: AC-3 is **triggered**. A1 stays blocked until the Owner records either
  (i) a blind re-review by A and B of every overlay-reviewed frame in the waves completed so far (W1,
  plus W2 if W2 was reviewed), or (ii) acceptance of overlay mode on AC-4 alone, with S, its interval
  and n written into that record.
- Otherwise AC-3 is reported and does not gate.
- **Low-power disclosure.** When `1 ≤ n < 20`, the report and the Owner record must state that AC-3 has
  low power at this n. They must also give the effective trigger from the table below.

**Why this fixes M-D1.** For every n ≥ 1 the new trigger fires at least as often as the superseded rule
(upper limit < 0.5), and at strictly more k for every n ≥ 2. So it is no longer looser than the contract
at small n. Only n = 0 is exempt, because no S exists there.

**Effective triggers [V]** (`scratchpad/add2/wilson_small_n.py`, pure Python, run with `python3 -I`):

| n | AC-3 fires when k ≤ (new, U < 0.70) | U at that k | U at k + 1 | Superseded rule fired when k ≤ (U < 0.5) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | never (U(0,1) = 0.793451) | — | — | never |
| 2 | 0 | 0.657620 | 0.905469 | never |
| 3 | 0 | 0.561497 | 0.792340 | never |
| 4 | 1 | 0.699358 | 0.849961 | 0 |
| 5 | 1 | 0.624465 | 0.769276 | 0 |
| 6 | 1 | 0.563503 | 0.700007 | 0 |
| 7 | 2 | 0.641066 | 0.749542 | 0 |
| 8 | 3 | 0.694258 | 0.784784 | 1 |
| 9 | 3 | 0.645798 | 0.733349 | 1 |
| 10 | 4 | 0.687326 | 0.763407 | 1 |
| 11 | 4 | 0.646199 | 0.719908 | 2 |
| 12 | 5 | 0.680489 | 0.746218 | 2 |
| 13 | 5 | 0.644771 | 0.708562 | 2 |
| 14 | 6 | 0.674094 | 0.732008 | 3 |
| 15 | 7 | 0.698830 | 0.751905 | 3 |
| 16 | 7 | 0.668214 | 0.720004 | 4 |
| 17 | 8 | 0.690368 | 0.738349 | 4 |
| 18 | 8 | 0.662836 | 0.709690 | 4 |
| 19 | 9 | 0.682922 | 0.726702 | 5 |
| 20 | 9 | 0.657915 | 0.700702 | 5 |
| 40 | 22 | 0.692947 | 0.714906 | 13 |
| 60 | 35 | 0.699357 | 0.714305 | 22 |

Notes:
- The n = 20/40/60 rows equal addendum 1 §5.2 (9/20, 22/40, 35/60), and the superseded column equals
  the QA's values (n = 10 → k ≤ 1, n = 15 → k ≤ 3, n = 19 → k ≤ 5, n = 40 → 13).
- At n = 6, k = 2 gives U = 0.700007, which does **not** trigger. Unrounded comparison is binding, as
  in addendum 1 L-8.
- At n = 1 no outcome can trigger. The low-power disclosure then carries the information.

## 4. Low findings L-D1 … L-D7 (binding unless marked)

| ID | Resolution |
| --- | --- |
| **L-D1** truncation symptoms | Addendum 1 stays unedited. Its gate result is the one recorded in the delta QA record: `uv run ruff check src tests` passed, and `uv lock --check` resolved 201 packages, exit 0. Addendum 1 §12's "11 cited files" should read 10, as §1 lists. This addendum's own gate is in §7. |
| **L-D2** `n_adj` | `n_adj` is the number of **distinct objects** on the adjudicated overlay. Labels, added boxes and mask regions that overlap at IoU ≥ 0.1 are merged into one object before counting, so a duplicate label or a `label_issue` mask over its own label counts once. The packet builder computes `n_adj` with this rule and prints it on the overlay page. The verifier recomputes it from the overlay CSV and rejects a mismatch. Q's blind point-per-object method is **not** adopted (proposal kept for a successor). |
| **L-D3** precedence row 0 | New first row of the L-3 table: **(0)** the object matches an existing label at IoU ≥ 0.5 with the same derived key and the box is acceptable → covered. Nothing is recorded, and the existing rows (1)–(5) follow unchanged. **Flag for D-2:** a distinct small sign with ≥ 50 % of its area inside a larger label box (stacked or supplementary plates) falls under row (1). It becomes `label_issue` plus mask, not an added box. That is safe for A1 because the region is masked, but it under-counts additions, and the report must give how many row-(1) cases had a different key. |
| **L-D4** index base | X1 = `C150[0::2]` and X2 = `C150[1::2]`, **0-based** positions in key order. The hashes in addendum 1 §3.5 are unchanged and remain normative. |
| **L-D5** audit enumeration | `q_audit_result ∈ {CLEAN, MISS_CONFIRMED_REPAIRED, MISS_REJECTED, NOT_AUDITED}`. Eligibility under R-M4.1, given the other R-M4.1 conditions hold: `CLEAN` → may be eligible. `MISS_CONFIRMED_REPAIRED` → may be eligible after C's re-check of the repair. `MISS_REJECTED` → may be eligible only if C's rejection carries a reason code `NOT_A_SIGN` or `ALREADY_COVERED`; any other or blank reason → ineligible. `NOT_AUDITED` → never eligible. The verifier enforces all four. The scope of the AC-3 re-review is stated in R-A2.1 (i). |
| **L-D6** calibration timing | No rule change. Disclosed for the Owner: the W0 overlay pilot comes before the blind calibration, and blind passes finish before the first overlay page of W1. C150 excludes W0, so no memory effect on the calibration frames is possible. |
| **L-D7** Q onboarding | Q gets 2 h of onboarding under the L-3 taxonomy, timed in W0 together with the 18 s per-frame estimate. The cost table is updated in §5. |

## 5. Cost (replaces addendum 1 §8 totals) [V arithmetic, inputs U]

The only change is the onboarding line, which now covers four people (A, B, C and Q, 2 h each).
It rises from 6.0 h to 8.0 h in every column.

| Total across four reviewers | Low | Central | High |
| --- | ---: | ---: | ---: |
| Addendum 1 | 34.6 h | 55.3 h | 98.2 h |
| **This addendum** | **36.6 h** | **57.3 h** | **100.2 h** |

Central per-role load: A ≈ 16.9 h, B ≈ 16.9 h, C ≈ 11.9 h, Q ≈ 11.6 h. Without the AC-2 re-brief
reserve the high total is 93.5 h. All per-frame inputs remain unmeasured until W0.

## 6. Owner decisions after this addendum

These are unchanged from addendum 1 §11, plus one note.

- D-1 … D-8.
- D-A1: keep the R10 six keys. The delta QA view is that they fit the background-FP purpose.
- D-A2: accept the census gate (16/5/4 allowed misses in the three largest groups at the same 5 %
  bound). The delta QA view is that it is statistically sound and should be stated in the Owner
  record.
- D-2 now also covers the L-D3 stacked-plate flag and the L-D5 `MISS_REJECTED` reason codes.

A1 stays `A1_BLOCKED_PENDING_TRAIN_LABEL_COMPLETENESS_AND_HUMAN_REVIEW`. Nothing here authorizes a
packet build, label edits, inference or training.

## 7. Commands run and data access

| Command | Result |
| --- | --- |
| `python3 -I scratchpad/add2/wilson_small_n.py` | the table in §3. The n = 20/40/60 and superseded values match addendum 1 and the delta QA. |
| `shasum -a 256` on the four pinned files | equal to §1 |

The commands were run from this session's scratchpad
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/add2/`.

No image, label file, CSV row or model was read for this addendum. The sealed test was not accessed.

## 8. Classification of claims

- **Verified current behavior / artifact [V]:** the trigger table in §3; the pins in §1; the cost
  arithmetic in §5.
- **Proposal [P]:** R-A2.1 and every L-D resolution, until the delta QA and the Owner accept them.
- **Unknown [U]:** every per-frame time input; Q's sensitivity (U-10); train frame sizes (U-4).

`sealed_test_accessed=false` · `training_authorized=false` · `labels_modified=false` · `inference_run=false`
