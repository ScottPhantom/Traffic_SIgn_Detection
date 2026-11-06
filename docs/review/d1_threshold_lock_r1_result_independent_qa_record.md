# D1 two-seed R3 validation lock — independent result QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh) by a Codex agent separate from the input-binding author and lock writer. Scope: existing R3 validation predictions and the versioned R3 lock/proof output. No model inference, training, threshold activation or sealed-test access occurred.

Verdict: PASS — the versioned two-seed validation lock and proof reproduce the QA-pinned provisional result and the independent CSV recomputation; the setting remains awaiting Owner approval.

## Byte bindings (SHA-256)

| Artifact | SHA-256 |
| --- | --- |
| `docs/review/generated/d1_threshold_lock_r1.json` | `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d` |
| `docs/review/generated/d1_threshold_lock_r1_r3_proof.json` | `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77` |
| `docs/review/generated/d1_two_seed_provisional_threshold_r1.json` | `d6ce45568709be8bb3f3ea6d9535870f5027fd40f645addeac3a4a990b627e33` |
| `docs/review/d1_two_seed_lock_r1_inference_binding_authorization_2026-11-06.md` | `40e9f8806feab30a803fec633b7907e03a4d8b0ee785c5edc860ebd902f2615a` |
| `docs/review/d1_two_seed_lock_r1_inference_binding_independent_qa_record.md` | `318bc488eab770d6ddd3991c25a006d1266dca62651d18cbb5fc6ff5410bb401` |
| Seed 20261018 temporary R3 report (under `tmp/d1_two_seed_lock_r1_inputs/`) | `926a850f491756fdc72c8f937e2f3433fca058bbe9969501b24a37929fc3ad31` |
| Seed 20261019 temporary R3 report (under `tmp/d1_two_seed_lock_r1_inputs/`) | `c468357d6ed67aac7e90460f9d40b553db32c2df765078f89ceef7c326bfded1` |

Both report hashes match the proof's `report_sha256` entries and the candidate `val_report` bindings. The candidate weights, contracts and attestations match their bound seed reports. Each report contains 11 configurations, 31 confidence points per configuration, `split=val`, and `sealed_test_accessed=false`. All 22 input CSV hashes were independently checked against the two QA-passed generated JSONs before scoring. The validation roster has 376 images, 624 ground-truth boxes and nine D-02 groups.

## Independent operating-point recomputation

I parsed the raw CSV predictions, reconstructed each frame's validation boxes, and used a separate score-ordered greedy IoU ≥0.50 matcher for class-agnostic TP/FP and exact-class hits. The three required cells are:

| NMS / confidence | Seed 18 TP / FP / exact-class | Seed 19 TP / FP / exact-class | Two-seed mean recall / FP per image |
| --- | ---: | ---: | ---: |
| Class-aware 0.70 / 0.19 (selected) | 555 / 155 / 461 | 512 / 131 / 383 | 0.8549679487179487 / 0.38031914893617025 |
| Class-aware 0.70 / 0.20 (control) | 547 / 150 / 457 | 507 / 127 / 379 | 0.844551282051282 / 0.3683510638297872 |
| Across-class 0.80 / 0.19 (control) | 555 / 111 / 437 | 512 / 75 / 368 | 0.8549679487179487 / 0.2473404255319149 |

All counts and means match the proof and the earlier independent provisional-result QA. The selected setting is confidence 0.19, class-aware NMS IoU 0.70. Seed 18 recall is 555/624 = 0.8894230769230769 and seed 19 recall is 512/624 = 0.8205128205128205; the mean clears 0.85, but seed 19 alone does not. Mean FP/image 0.38031914893617025 remains above the 0.30 D-05 marker.

## Change test and cross-validation

With an independently written 1,000-draw group-resampling loop (seed 20261018, intact D-02 groups, the same draw for both seeds/settings), I recalculated FP/image from per-frame counts and mAP50–95 with the QA-pinned Ultralytics AP scorer. The across-class 0.80 minus class-aware 0.70 difference at confidence 0.19 is FP/image -0.13297872340425534, 95% CI `[-0.2005482456140351, -0.08253315250150692]`; mAP50–95 difference -0.060001508410162274, 95% CI `[-0.13118843598814658, -0.03447974039348694]`. Both intervals match the proof and provisional QA JSON. The mAP interval is wholly below zero; therefore the across-class configuration fails the frozen NMS change rule despite fewer FP.

I recomputed all nine leave-one-group-out selections from raw CSV frames and the fixed 31-point grid, fitting on eight groups and checking each held-out group's TP/FP/GT/image counts. Every configuration, confidence and held-out count matches the proof; the nine fit subsets select across-class 0.80 with confidence 0.17, 0.22, 0.19, 0.18, 0.19, 0.20, 0.19, 0.20 and 0.19 respectively. Adjacent votes are 9/9. The proof's fold list is byte-equivalent as JSON to the earlier provisional-result fold list.

## Record boundary

The lock JSON has exactly two candidates with distinct pinned weights and the same confidence/NMS setting. Its `status=LOCKED_ON_VAL`, `sealed_test_seen=false`; the proof has `sealed_test_accessed=false`. These fields describe a versioned validation record, not an effective production or final-evaluation authorization. The independent writer verifier completed successfully and the checks above reproduced its material values. The record must remain `AWAITING_OWNER_APPROVAL` for use: a separate Owner approval record is required by the R3 reader. This QA does not establish out-of-sample performance, safety, or stability across future seeds or driving scenes. `sealed_test_accessed=false`.
