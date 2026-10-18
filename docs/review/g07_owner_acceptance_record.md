# G0.7 owner acceptance — WP36-R1 is the official DATASET01 split

Status: `OWNER_ACCEPTED_G07_SPLIT`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)
Split package: M0-WP36-R1 (`scripts/build_wp36_r1_group_split.py`, report
`docs/review/wp36_r1_group_split_report.md`)
Independent QA: `docs/review/wp36_r1_independent_qa_record.md` — PASS, 0 P0/P1/P2, 1 P3

The owner accepted WP36-R1 as the official G0.7 train/val/test split of DATASET01.

## Accepted bytes

| File | SHA-256 |
| --- | --- |
| `docs/review/generated/wp36_r1_split_manifest.json` | `064259941895d35054e87a550bf69199c4cae8ffeb4c83b4d7cdf608673438d9` |
| `docs/review/generated/wp36_r1_split_candidate.json` | `869947559c5eda978a64418a662092a4cd86eec17a0c6a12bb9f827aff3f984e` |
| `docs/review/generated/wp36_r1_split_frames.csv` | `8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a` |
| `scripts/build_wp36_r1_group_split.py` | `147710f410314bcbb79d7869758eb5e631cb708f1bba8bc3627dd909c2d0f292` |

Split list hashes (SHA-256 of the sorted stems joined by `\n`, no trailing newline):

- train `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`
- val `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`
- **test (sealed)** `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`

The usable frames are train 1,912, val 376 and test 903 (59.9 / 11.8 / 28.3 %), in 29, 9 and 16
D-02 groups. The 24 quarantined negatives are excluded, and 0544 is the only background frame (in
train).

## Conditions

- **Test seal.** Test frames are used only in an explicit, logged final-evaluation run. They are
  never used for training, model selection, threshold tuning or error analysis that feeds back
  into training. Changing any split list requires a new, append-only split version and a new
  owner decision.
- **Loader guard.** Before every run, the M1 loader checks each list against the
  `split_list_sha256` values above and against `use` in `wp36_r1_split_frames.csv`. The full
  `build_wp36_r1_group_split.py verify` / `check-candidate` runs in CI, as QA P3-1 recommends.
- **Classes without validation** must not drive model selection or tuning: 9, 11, 17, 18, 19, 20,
  22, 25, 28, 30, 40, 45 and 50.
- **Train-only classes** (D-04 part 1, `TRAIN_ONLY_UNVERIFIED` and class 38) have no sealed test.
  They stay "unverified" under the D-04 behaviour gate.
- **WP35 enriched images** are train-only.

## Gate status

G0.7 is **PASS**. Gate 0 is still not open: G0.9 (dataset card) and D-05 (thresholds, latency and
seed count, set on the val split) remain open, and training is not authorized by this record.
