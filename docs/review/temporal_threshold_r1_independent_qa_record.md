# Temporal Dynamic Threshold R1 — independent QA, 2026-11-04

Verdict: **PASS for a reproducible, offline, validation-only diagnostic.** The numbers in
`docs/review/temporal_threshold_r1_report.md` §2–§4 replay exactly and match an independent
recount. **This is not a D-05 acceptance and not a go for app or video activation.** One
provenance defect: the §1a timestamp is wrong (see C6). It does not change any result.

Scope: the author session's package as handed over. The QA session did not edit the files under
review, `review2_*.py`, `app_pages/07_demo.py` or `views.py`. It did not open the sealed test,
change D-05, enable anything in the app, commit, stash or switch branches. Every claim below is
**VERIFIED** (rerun or read back in this checkout on 2026-11-04) unless marked otherwise.

## Reviewed artifacts (SHA-256 recomputed, all match the hand-over brief and report §6)

| File | SHA-256 |
| --- | --- |
| `src/cpv301_autodrive/temporal_threshold.py` | `a519066abc6106ae0e729d09d846847997a1d9b584efc769c88d4b03308e9fdc` |
| `scripts/evaluate_temporal_threshold_r1.py` | `b6f17073c7a27cb38154affc516971241f43245fafd39b57499d43b70dd9881d` |
| `tests/test_temporal_threshold_r1.py` | `655254766cd4c6bb69a8f6470531817c26061fc4f48d1581d9d8611b0394b2c9` |
| `docs/review/generated/temporal_threshold_r1_val.json` | `05527c98e3a6ea47e337639d57e370620973ca2843bbd525b5be00e846b037f3` |
| `docs/review/generated/temporal_threshold_r1_mini.json` | `1c619fd59e6c8d18a2f3becf39e5f105908ec0eb1a6af15a7c0f2715c4d8eae3` |
| `data/processed/temporal_threshold_r1_mini/…_conf0001_step2.csv` (ignored) | `67b714a7763a46afb5fa21467dcd8d6f930809b09527d5b66877104cbb9327c0` |
| `data/processed/temporal_threshold_r1_mini/…_conf0001_step2.manifest.json` (ignored) | `8145ef272917893d65b50ab9a1bec6ca7c0f14d0a59cab82d05265c8f0d80b8a` |
| `docs/review/temporal_threshold_r1_report.md` (at QA time; not in the brief) | `38178eec2061f8250bf067d117481c6f1f11a7b501102c04f3544883e4522f6f` |

Pinned inputs: the val prediction CSV `87884c53…c893` was hashed directly and has 1999 rows, the
same number the loader returns. The split, checkpoint and class map are hash-checked by
`dynamic_threshold_r2_r1.verify_pins` on every load. The Mini labels `b90710ee…`, the Mini clip
`1fab7593…` (via the manifest) and the pinned conf-0.20 upload `343e00c3…` all match.

## Checks

| # | Check | Result |
| --- | --- | --- |
| C1 | Hashes, `sealed_test_accessed=false` and `app_activation=false` in both JSONs | **PASS** |
| C2 | Module matches pre-registration §1/§1a | **PASS** |
| C3 | Replay of both evaluations matches the canonical JSON | **PASS** |
| C4 | Independent recount of the key numbers | **PASS** |
| C5 | §2 sequence audit | **PASS** |
| C6 | Pre-registration integrity | **PASS with limitation; §1a timestamp defect** |
| C7 | Gates: ruff, pytest, lock, graft | **PASS** |
| C8 | Report text agrees with the JSON | **PASS** |

### C1 — hashes, flags, untouched files

- All eight hashes above were recomputed with `shasum -a 256` and all match.
- Both JSONs have `sealed_test_accessed: false` and `app_activation: false`. The Mini manifest
  has `training: false` and `sealed_test_accessed: false`.
- `temporal_threshold` is imported only by `scripts/evaluate_temporal_threshold_r1.py` and
  `tests/test_temporal_threshold_r1.py`. No app page or runtime module imports it. This confirms
  in code that there is no app activation.
- `07_demo.py` and `views.py` already showed `M` in git before this package. `07_demo.py` was
  last modified at 13:34:18, before the module was created (13:38:32). `review2_front_demo_r1.py`
  changed at 13:46:41, after the package was handed over. That change is probably the concurrent
  Review 2 UI session; it is not part of this package. `review2_temporal_r1.py` (the linker
  dependency) was last modified 2026-11-01. QA can't attribute edits by session, but nothing in
  the package depends on or changes those files.

### C2 — module against §1/§1a

Read line by line against §1 and against the linker it delegates to
(`review2_temporal_r1.track_prediction_rows`):

- `PRIMARY = TemporalParams(enter=0.35, keep=0.15, window=5, max_miss=2, link_iou=0.30,
  predict_motion=True)`. The linker is called with `max_missing_samples = max_miss − 1 = 1` and
  `sample_step=1`.
- Candidates with `s < keep` get `below_keep_floor` and are never linked or emitted. Invalid
  boxes get `invalid_box`; non-finite values and scores outside [0, 1] also count as invalid,
  which is stricter than §1.
- `accumulated_score = sigmoid(logit(keep) + Σ(logit(s) − logit(keep)))` over the observed
  frames with index `> t − 5` (t−4…t). Frames without an observation add 0. With one observation
  this returns `s` itself, so a candidate seen in only one frame with `s < enter` can never
  confirm.
- `TENTATIVE → CONFIRMED` happens at `S_t ≥ enter`, online. Earlier frames are not back-filled.
  A confirmed track emits when it has a linked candidate with `s ≥ keep`. Because every linked
  candidate already has `s ≥ keep`, every evidence term is ≥ 0, so `S_t ≥ keep` always holds once
  linked.
- Close rule: each frame without a link adds a miss, and the 2nd consecutive miss closes the
  track. The linker keeps a track while `sample − last ≤ max_missing_samples + 1 = 2`, so the
  two agree. Linker IDs are never reused (`next_id` only increases). That makes the §1 "reused
  ID opens a new track" branch unreachable but harmless.
- Rows the linker marks `same_frame_duplicate` are dropped with `same_frame_duplicate_in_track`.
  The label is `argmax` of the cumulative per-class score sum from the track's start, with ties
  going to the smaller `yolo_id` (`min(key=(-mass, c))`). Label switches are counted between
  consecutive emitted frames. Output boxes carry the track label and `S_t`; raw candidates are
  not modified.
- In the evaluation script, the FP-budget search uses the §1a rule: the lowest threshold on
  0.05…0.95 with FP/image ≤ temporal, plus the reverse direction. GT-track label switches use the
  same linker settings on GT boxes with class-agnostic `_greedy_pairs` at IoU 0.5, as §1 says.
  The bootstrap uses 1000 rounds, seed 20261018, resampling D-02 groups.

### C3 — replay

`evaluate_val()` and `evaluate_mini()` were called in memory, without the CLI (which refuses to
overwrite), and written to the QA scratch directory. After removing `source_sha256` and
`postprocess_ms_total_local`, both outputs equal the canonical JSONs exactly. `source_sha256` was
also identical, so the source has not changed since the artifacts were generated.

### C4 — independent recount

`recount.py` (evidence below) shares only the pinned data loader `load_frames`. It has its own
IoU function, its own greedy score-ordered matcher, its own segmentation, and its own
re-implementation of the R1 linker rules (R12 settings, same-code duplicate grouping at
IoU ≥ 0.9, motion prediction, greedy assignment by IoU and then label tie-break). It also
re-implements the temporal rule, the FP-budget search, lost/recovered counting, GT-track
switches, the §2 audit and the Mini scorer. Results:

| Quantity | Report / JSON | Independent |
| --- | --- | --- |
| Baseline 0.20 localized / FP / correct-class (/624) | 547 / 150 / 457 | 547 / 150 / 457 |
| Temporal localized / correct-class / FP | 519 / 442 / 125 | 519 / 442 / 125 |
| Lowest fixed threshold within FP budget | 0.29: 507 / 425 / 122 FP | 0.29: 507 / 425 / 122 FP |
| Highest fixed threshold reaching temporal recall | 0.26: 519 / 433 / 130 FP | 0.26: 519 / 433 / 130 FP |
| Lost localized / correct-class | 38 / 33 | 38 / 33 (same per-class split) |
| Recovered localized / correct-class | 10 / 18 | 10 / 18 |
| Per class 7 / 10 / 12 (support, base, temporal) | 111,66,63 / 48,48,48 / 65,60,58 | same; 32/41/46 support 0 |
| GT-track switches, baseline | 34 on 77 tracks (23 with a switch) | 34 / 77 / 23 |
| GT-track switches, temporal | 12 on 73 tracks (10 with a switch) | 12 / 73 / 10 |
| Run stats: tracks, confirmed, emitted, below floor, invalid, tentative | 340, 266, 644, 1237, 18, 100 | same |
| Segments, primary / reviewed-only variant | 13 / 176 | 13 / 176 |
| Bootstrap CI: detection recall / correct-class recall / FP per image | [−0.101, +0.002] / [−0.061, +0.012] / [−0.137, −0.020] | [−0.1012, 0.0023] / [−0.0609, 0.0119] / [−0.1374, −0.0196] |
| Mini P.130 TP/FP/FN, base → temporal | 12/0/5 → 15/1/2 | 12/0/5 → 15/1/2 |
| Mini W.205c TP/FP/FN, base and temporal | 0/0/16 both | 0/0/16 both |
| Mini other codes on target boxes, base → temporal | P.131a 7→3, W.207 6→1, W.224 13→19 (26→23) | same |
| Mini rows / sampled / decoded / evaluable frames | 246 / 103 / 206 / 74 | same |

The bootstrap was recomputed from QA's own per-frame counts. With a different seed (1), the
detection-recall CI is [−0.0995, 0.0017], so the conclusion is the same: only the FP/image CI
excludes 0.

### C5 — §2 sequence audit

Recomputed independently from the loader order, the WP16–WP21 annotation JSONs and
`grouping_proxy_edges.csv`:

- 376 frames, 9 groups. Each group is one contiguous block, and stems strictly increase in loader
  order.
- 363 same-group adjacent pairs have stem step 1: 200 inside a reviewed `CONTINUOUS_CANDIDATE`
  run, 137 `uncertain`, 26 `adjacency_only`.
- Four gaps: C0001 `0059→0062`, and C0020 `0711→0720`, `0729→0741`, `0750→0836`. The split CSV
  confirms the explanations: 0060/0061 are `val/QUARANTINED`; the C0020 gaps contain train frames
  of C0019 (8), C0021 (11) and C0022 (68) plus C0023 (17). The report names only C0019/C0021/C0022
  for the last gap. That is a minor omission and does not affect any number.
- 607 GT transitions: 197 with same-class IoU ≥ 0.5, 336 with IoU ≥ 0.3, 28 with no same-class
  box in the next frame, and median IoU 0.370.

### C6 — pre-registration integrity (limitation)

There is no cryptographic timestamp or commit; §1/§1a are plain append-only text. Filesystem
birth times (local time, +07:00) are consistent with §1 being written first:

- report created 13:37:42, matching the "13:37" stated in §1;
- module 13:38:32, test 13:39:02, script 13:41:36;
- Mini CSV/manifest 13:42:28, JSONs 13:43:11 (regenerated after `ruff format`, as the report
  says);
- the report was last modified at 13:44:27.

**Defect:** §1a is labelled "2026-11-04T13:5x+07:00", but the report was last written at
13:44:27, and the system clock read 13:49:41 when QA checked it. The stated time cannot be
correct. QA therefore can't establish from file metadata whether §1a was written before or after
the first temporal result.

Mitigation, verified: the erratum is **outcome-neutral**.

- Under the original 0.20…0.95 grid, the lowest threshold within the FP budget is still 0.29 and
  the recall-matching threshold is still 0.26.
- The literal §1 rule ("highest threshold within budget") gives 0.95, which is degenerate. That
  supports the author's explanation that §1 had a wording error.
- No temporal parameter differs between §1 and the code.

Recommendation (PROPOSAL): append a correction note to the report fixing the §1a time label. Do
not edit §1a in place.

### C7 — gates

- `uv run ruff check src tests scripts`: All checks passed.
- `uv run pytest -q tests/test_temporal_threshold_r1.py tests/test_review2_temporal_overlay_r2.py`:
  17 passed.
- `uv lock --check`: Resolved 201 packages, consistent.
- `graft check .`: wiring graph in sync.

### C8 — report text against the JSON

The tables in §3.2–§3.6 and §4 were read against the canonical JSON and agree: recall and
precision to 4 decimals, the CIs, every sensitivity row, the reviewed-segmentation variant
(502/424/119), and the Mini event sequences. These include the 16/16 W.224 under temporal and
the P.130↔P.131a flips going from 6 to 4.

## Advisory findings (not blocking a diagnostic PASS)

1. **Test gaps.** There are no unit tests for `same_frame_duplicate` handling, for frames
   leaving the N-frame window, or for the label tie-break. The behaviour was checked here by
   reading the code and by the matching recount; tests would protect it against regressions.
2. **Silent fallback in Mini reproduction.** If the pinned conf-0.20 upload file has a different
   hash, the script leaves `pinned` empty instead of raising an error. The file matches today
   (`343e00c3…`, 54 rows, 0 mismatches), but a future rerun could report a mismatch for the wrong
   reason.
3. **Two matching rules in the Mini results.** P.130 frame-level TP is 15 (R2 scorer), while the
   event-level `correct_code_frames` is 14, which uses the best-scoring overlapping row per GT
   box. Both are correct under their own rules. The report quotes only the frame-level number.
4. **Mini sequence boundaries.** The Mini clip is run as one sequence with no scene-break input.
   §1 does not specify scene breaks for evaluation B. Whether the clip has a cut is **UNKNOWN**
   to this QA.
5. **Limitations the author already lists, confirmed:** 1 seed; val already seen by DT R1–R6;
   only 9 bootstrap groups; sequences only partly continuous (200/363 reviewed pairs); classes
   32/41/46 have zero val support; Mini has 2 GT events and is DEMO_ONLY. On this val the
   temporal rule trades −28 localized / −15 correct-class GT for −25 FP compared with 0.20. Its
   advantage at the same FP budget (+9 to +17 correct-class GT) has no CI of its own.

## Decision boundary

- PASS covers reproducibility and the correctness of the reported diagnostic numbers only.
- D-05 is unchanged.
- No app, video or default-threshold change is authorized by this record.
- The report's §5 PROPOSAL (an experimental, off-by-default display toggle) still needs a separate
  Owner decision.

## Evidence

QA scripts and outputs are outside the repo, in the shared session notes folder
`side-session-notes/local_0f8736ca-…/temporal_dt_r1_qa_evidence/`:

| File | SHA-256 |
| --- | --- |
| `recount.py` | `a8cf044acc757c0a3d28c8bf6a8e9bea8e35af43924553d6f456a24046777dfb` |
| `extra.py` (bootstrap, §1a neutrality) | `6af54157495655414bb8d99e542d9dc9992aff36c798f64fa1f8c768f9254544` |
| `replay.py` | `31a403f9fa1761c80c45861b2aef93cc4d75bf2bfbebd553e40926bd065d0074` |
| `recount_out.json` | `85f1e04d9973bbfe56221ce446b836f1705ca988567b536f786ce748c3aed767` |
| `replay_val.json` | `62b5b330c609ae2f34bc15a3f60eef39a4901a64ede49565ff233c0ae4063f39` |
| `replay_mini.json` | `e3633dd190f3ecdf9d47e48a2a42d4435fcd1d8322ec29cdcf51d78dce597fab` |

Rerun commands, from the checkout root:

```bash
uv run python <evidence>/replay.py <outdir>
uv run python <evidence>/recount.py
uv run python <evidence>/extra.py <evidence>
```
