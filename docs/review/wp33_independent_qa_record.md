# M0-WP33 independent QA record

Status: `QA_PASS_WP33_DERIVED_LABELS_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP33 or the D-03 owner records)`
Reviewed at: `2026-10-18T00:30:00+07:00`
Boundary: `QA_OF_D03_DERIVED_LABEL_SET_ONLY_NOT_GATE0_APPROVAL_NO_CLASS_INDICES_NO_SPLIT_NO_TRAINING`

This append-only record reports independent QA of M0-WP33, the D-03 derived label set. It
modifies no package, builder, test, owner record, raw label, `PROJECT_MEMORY.md` or roadmap file.
WP33 keeps its `WP33_DERIVED_LABELS_AWAITING_QA` status string.

## Verdict

- **WP33: PASS.** 0 P0, 0 P1, 0 P2, 4 P3.
- **Class 23:** none of the 465 boxes is a different sign. **No decision disagreements.**
- **Height values:** I agree with every value in `wp33_height_value_decisions.csv` (101 of 101
  boxes) and with the four exclusions. The P3 findings concern only confidence labels and wording.

## Package bytes reviewed

- Builder `720a085fed1d10af…`, test `3ad9d5c2e2265a84…`, report `63bcf4ff3aba7070…`.
- Boxes `4b9307003ce8fd3c…`, taxonomy `199ddd322aa05d48…`, manifest `ea59ff9889002d1b…`.
- Height decisions `329ff96518e1a0b8…` (equal to the builder pin).

## Checks performed

1. **Class 23, all 10 atlas pages and all 465 crops read directly.**
   - Every legible crop shows the same combined design: a motorcycle or moped and a motorised
     three-wheeler in one red circle with a slash. It appears in two layouts:
     - motorcycle upper right and three-wheeler lower left (for example 0799–1059 and 1238–1426);
     - three-wheeler upper right and motorcycle lower left (for example 2068–2421, 2883–2899 and
       3054–3070).
   - No box is a plain P.111a, P.111b, P.104, P.106 or any other sign. The QCVN page 84 reference
     (`qcvn_page_084_p111.png`) confirms that no single QCVN variant matches the combined design,
     which supports the owner's revision to `P.111a+P.111b`.
   - **Caveat (not a finding):** some runs are too blurred to make out the pictograms:
     - 0751–0782;
     - 1012–1028;
     - 1226–1237;
     - 1383–1408;
     - 2305–2331;
     - 2338–2366;
     - 3015–3036.

     In every one of these runs, the same pole and post appear in focus in neighbouring frames
     of the same run, so the combined-design reading holds by sequence continuity.
2. **Height values, all 73 class-16 crops, all 27 class-43 crops and 0776:7 read directly.**

   Raw context crops were also checked for 2088:2, 2278:2, 2279:2, 0776:7, 0814:4 and 0797:3.
   - **P.117 values:**

     | Stems | Value | Count |
     | --- | --- | --- |
     | 0551–0593 | 2,0 m | 43 |
     | 0595–0603 | 2,5 m | 9 |
     | 0797–0814 | 2,2 m | 18 |

     0551–0568 are blurry but continuous with the legible 0569–0593, so MEDIUM is correct for
     them.
   - **W.239b values:**

     | Stems | Value | Count |
     | --- | --- | --- |
     | 0571–0592 | 2,5 m | 22 |
     | 0751–0757 | 2,7 m | 5 |

     0571–0582 are correctly MEDIUM.
   - **The four exclusions are agreed:**
     - 2088:2 is cut off at the image edge.
     - 2278:2 and 2279:2 are a blurred red circle half-hidden behind a blue board; it is not even
       certain that they are P.117.
     - 0776:7 is a height-limit disc beside a cls23 sign. Its digits are unreadable, and raw
       class 18 is wrong for it.
   - **Other boxes:** I found no other class-16 or class-43 box that is unreadable or shows a
     different value. The confidence labels are covered in P3-1.
3. **Independent re-derivation (QA-only script; does not import the builder).**

   The script reads the raw labels, the inventory, owner tables parts 1 and 2 and the height
   decisions.
   - Raw label hashes: all 3,216 label files re-hashed against the inventory, with 0 mismatches.
   - Coverage: there are 8,334 raw boxes, and every one appears exactly once in the derived table
     (no duplicate `stem:line`). The non-empty line count equals `box_count` for every stem.
   - Exact match: all 8,334 rows match my derivation field by field (raw class, geometry, derived
     key, code, Vietnamese name, train eligibility and role). There are 0 mismatches.
   - Roles: 8,290 CLASS, 38 UNKNOWN_EVAL_ONLY (class 31), 4 EXCLUDED (heights) and 2 QUARANTINED
     (stem 0248).
   - All 101 height decisions are used, and every one matches its box's raw class.
   - The taxonomy's train and excluded counts equal the box table for all 56 keys. That is 54
     trainable keys, plus `16:UNREADABLE` and `UNKNOWN`.
4. **Names and codes against the owner tables.**
   - Every derived code and Vietnamese name equals `approved_code` / `approved_name_vi` in part 1
     or part 2.
   - Classes 3 (`R.302a Phải đi vòng sang bên phải`) and 24 (`P.129 Kiểm tra`) keep their current
     names, as the owner chose.
   - Class 23 uses the revised name from the part-2 revision.
   - Height keys use `P.117*v` and `W.239b*v` with comma decimals in the names.
5. **Verifier and tests.**
   - `uv run python scripts/build_wp33_derived_labels.py verify` returns `valid=true` with
     4 artifacts.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp33_derived_labels.py` reports 7 passed.
6. **Tampering attacks.** These ran on a staged copy that used a staged copy of the raw labels.
   The baseline and restored runs were both `valid=true`. All seven failed closed:
   - F1: change height decision 0797:3 from 2.2 to 2.0. Rejected because the pinned source
     changed.
   - F2: the same change, then run `build`. Still rejected by the same pin.
   - F3: set one class-23 box to `train_eligible=False`. Rejected because the artifact differs.
   - F4: change class 31 from ROUTE_TO_UNKNOWN in owner part 2. Rejected because the pinned
     source changed.
   - F5: edit one byte in raw label `0797.txt`. Rejected with `raw label hash mismatch`.
   - F6: edit one taxonomy row. Rejected.
   - F7: flip a `false` to `true` in the manifest. Rejected.
7. **Boundary.** The report says raw labels are read only and hash-checked, and that the package
   does not:
   - assign training class indices;
   - generate a split;
   - authorize training.

   It also states that D-04 and D-05 remain pending and Gate 0 remains BLOCKED. This is consistent
   with the owner records.

## Findings (all P3, non-blocking)

### P3-1: some confidence labels are higher than the evidence

These values are correct, but four boxes are marked `HIGH, value read directly` although the
digits are only partly visible or blurred:

- `0814:4`: P.117, cut off at the image edge, only "2,2" partly visible.
- `0797:3` and `0798:3`: very blurred, so 2,2 is legible only with the following frames.
- `0592:1`: W.239b, left half cut off, only "5m" visible.

`MEDIUM, value read by sequence continuity` would be more accurate. This changes no class.

### P3-2: 0776:7 could be recovered by continuity (optional)

The raw context of 0776:7 shows a P.117 disc beside the cls23 sign on the same gantry as the 2,2 m
sequence 0797–0814. It has the same layout, and the same green-striped helmet appears ahead. A
MEDIUM 2,2 m reading by continuity is plausible. Excluding the box, as the owner decided, is the
conservative choice, and I do not ask for a change.

### P3-3: the builder silently skips malformed label lines

`derive` uses `continue` on lines without 5 fields. Today there is no impact: all 8,334 lines are
well formed, and the box count equals the inventory `box_count`. Still, a malformed line in a
future copy would be dropped silently instead of failing closed.

### P3-4: review atlases are not covered by the manifest; stale atlas title

`docs/review/assets/wp33/` is not part of the verified artifacts, so the atlas pages could change
without `verify` noticing. The class-23 page titles still read "P.111 -> a/b/c/d", which is the
superseded split plan.

## Governance

- D-03 derived labels are provisional QA-passed evidence.
- D-02, D-04 and D-05 remain pending, and Gate 0 remains BLOCKED.
- No class indices, split or training are authorized. Raw labels, the staging copy and the iCloud
  original are untouched.
- This record modifies no WP33 file, owner record, builder, test, `PROJECT_MEMORY.md` or roadmap
  file.
