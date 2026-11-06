# D1 two-seed provisional threshold R1 — independent result QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh), by a Codex agent separate from the inference and report author. Scope is the validation R3 result, its raw prediction CSVs and the report. No inference, training, threshold locking or sealed-test access was performed in this review.

Verdict: PASS

## Reviewed byte bindings (SHA-256)

| Artifact | SHA-256 |
| --- | --- |
| `docs/codex_handoff_two_seed_provisional_threshold_2026-11-06.md` | `678cc4037298cebb3b73ed69d35e8a70bf55ebfa0caaebfe6cabc158701296e8` |
| `docs/review/d1_threshold_lock_r1_contract.md` | `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f` |
| `docs/review/d1_two_seed_provisional_threshold_r1_source_independent_qa_record.md` | `8c20950b544b1a7ea8979518510a44a15ad169280f21e041cdf6a1935dabb998` |
| `docs/review/generated/d1_two_seed_provisional_threshold_r1.json` | `d6ce45568709be8bb3f3ea6d9535870f5027fd40f645addeac3a4a990b627e33` |
| `docs/review/d1_two_seed_provisional_threshold_r1_report.md` | `705ee356cf231f77873c62bf86631d3c5510776cdc2672777ce4caf719c7e636` |

The 11 new seed-20261019 CSVs remain local and Git-ignored under `results/experiments/d1_two_seed_provisional_threshold_r1/`. Their independently checked SHA-256 values are:

| Prediction CSV suffix | SHA-256 |
| --- | --- |
| `agnostic_0.80` | `0b746302c749dd7fefb7d6d6a7e9a46bbed1f3ddd4d586ee8eeb53b2dc9ba295` |
| `agnostic_0.85` | `987d2634992685bf53ecf4208727f4d4d472448162e48a7322505dcd719b51b2` |
| `agnostic_0.90` | `027a166d9ea47f34e0498591d6cc8955e967ca1806a7d3c3a982d6aa6e32b0ef` |
| `classaware_0.45` | `811e2935845d4195507653d743c05f43419bd73ca234761cb1ef4b700114705d` |
| `classaware_0.50` | `c843f73a710674fda66763d1dffe08a85d45b43dc703d650ff924fec10721b8f` |
| `classaware_0.55` | `e9e3041c6708fb38dc495d4a30f299fe375413a89e078582d900cb735c6b0f7f` |
| `classaware_0.60` | `d4cc6b1f10a9ac6d97091f5418808a2097744edea2307b5e38b373d441e3db76` |
| `classaware_0.65` | `041950b291e6db6b635c6acf6228af337c5e41790ce1015f664e3ae9af25bc5e` |
| `classaware_0.70` | `eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8` |
| `classaware_0.75` | `7ab3e9a9ef995cfd913a612cc5368af8bad7a40ad66d4e55f38c332218e15048` |
| `classaware_0.80` | `35fc180ea8bd4b6ee8e1afa2521ec4ca58a30cb02063c26869c3a48bc7043213` |

## Independent checks

- Reconstructed the governed validation roster independently from all 376 `data/images/val` files, their `data/labels54/val` YOLO labels, image dimensions and `data/val_groups.json`: 624 GT boxes in nine D-02 groups. Every row in the 22 pilot and S2 CSVs refers to a roster image and has a valid class, score and box. All 22 CSV hashes match the two result JSONs; all 36 `input_sha256` entries match the files currently at their pinned paths.
- Implemented an independent descending-confidence, IoU ≥0.50 greedy matcher over the raw CSVs. At `classaware_0.70`, confidence 0.19, seed 18 has TP 555 / FP 155 / correct-class hits 461, and seed 19 has 512 / 131 / 383. Mean recall is `0.8549679487179487`; mean FP/image is `0.38031914893617025`. At the fixed 0.20 / 0.70 cell the respective counts are 547 / 150 / 457 and 507 / 127 / 379, with mean recall `0.844551282051282` and mean FP/image `0.3683510638297872`. These exactly reproduce the pilot and S2 QA anchors.
- The unrestricted `agnostic_0.80`, confidence 0.19 cell has seed 18 TP 555 / FP 111 / correct-class hits 437, seed 19 512 / 75 / 368, mean recall `0.8549679487179487` and mean FP/image `0.2473404255319149`. Recomputed every one of the 341 cells from raw CSVs and selected the same unrestricted and class-aware reference cells using the frozen eligibility and tie order. Recomputed exact-class mAP50-95 for all 22 seed/configuration pairs with the QA-pinned common scorer; all values match the JSON.
- Independently drew 1,000 intact-group bootstrap samples using seed 20261018, shared each draw across two seeds and both configurations, and subtracted the seed means. FP/image difference CI is `[-0.2005482456140351, -0.08253315250150692]`. Recomputed mAP50-95 CI from the raw CSVs using the QA-pinned Ultralytics matcher and AP integrator: `[-0.13118843598814658, -0.03447974039348694]`. Both match the JSON. The mAP interval lies wholly below zero, so the unrestricted across-class NMS setting fails the frozen change rule.
- Independently selected the best configuration and confidence on each eight-group fit subset; all nine fold choices match the JSON, and all nine held-out group metrics were recomputed from the raw CSVs. Adjacent votes are 9/9 for `agnostic_0.80`, but the mAP CI failure requires fallback to `classaware_0.70`, confidence 0.19. The report's three comparison rows, statement that seed 19 alone misses recall 0.85, and failure of the 0.30 FP/image marker at the provisional setting match the JSON.
- JSON status is `PROVISIONAL_TWO_SEED_NOT_A_LOCK`, with `split=val`, `thresholds_locked=false` and `sealed_test_accessed=false`. The report identifies this as a two-of-three-seed validation diagnostic, not a D-05 threshold lock or a sealed-test authorization.

## Limit

This PASS establishes reproducibility and internal consistency for the pinned R3 validation result. It does not establish improvement in new driving scenes, safety, or a final threshold. The frozen three-seed contract, independent QA for seed 20261020, and separately approved R3 lock successor remain prerequisites for a final lock. Any change to the JSON, report or CSV bytes above requires delta QA.
