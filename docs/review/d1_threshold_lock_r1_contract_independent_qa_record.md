# D1 three-seed threshold lock R1 — independent contract QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh), by a Codex agent separate from the contract author. Scope is the frozen preparation contract only. No inference, training, S2 run-state inspection, or sealed-test access occurred.

Verdict: PASS

## Reviewed artifact and authority

- Contract: `docs/review/d1_threshold_lock_r1_contract.md`, SHA-256 `726932dbcd32842658477c9d36f4dc7c240d412d92119e76e5b3536a4d278f0f` at review time.
- The frozen text agrees with Owner-approved D-05 Q1/Q2/Q4: three seeds 20261018/20261019/20261020, selection on validation, 95% group-bootstrap uncertainty, and no sealed-test access before an approved lock. It explicitly says seed 20261020 is **not** authorized to train by this record.
- Pins for the D-05 decision, both pilot NMS reports, `m1.contract` and `m1.cli` were recomputed and match every SHA-256 cited in the contract. The NMS reports support the stated limited results: across-class IoU 0.80 failed the mAP CI condition, and per-class IoU 0.45 failed the FP CI condition in the separate paired test.

## Contract checks

- The confidence union (coarse 0.05–0.95 step 0.05 and fine 0.15–0.30 step 0.01), eight per-class IoUs and three diagnostic across-class IoUs are specified before any S2 validation score is used. Selection uses three-seed mean recall/FP, the D-05 recall ≥0.85 gate, and deterministic tie breaks; each seed and standard deviation remain reportable. The selected cell's per-seed recall gate is reported without silently changing the primary rule.
- The change-away-from-0.70 rule prespecifies shared group draws across all three seeds, 1,000 paired bootstrap rounds with seed 20261018, and ≥7/9 leave-one-group-out votes in the same NMS mode. A failed condition falls back to per-class 0.70; no eligible point means no lock.
- **R3 binding is explicitly resolved by a successor path, not assumed equivalent.** `m1.cli cmd_lock_thresholds` reads its own val export reports and selects per-seed confidence. `bind_threshold_lock` checks exact schema-1 keys and report hashes but does not verify R3 roster identity, shared three-seed confidence, or aggregate selection. The contract requires a new independently QA'd R3 writer/verifier and compatible final reader; a sidecar proof must be bound by that reader or a versioned schema used. This is a **future implementation gate**, not an implemented feature.
- Future `LOCKED_ON_VAL`, independent QA and Owner approval are required after all three result-QA passes and separately authorized NMS inferences. The current document does not create a lock, request test access, change D-05, or provide a runnable final-evaluation command. `sealed_test_accessed=false`.

## Limits and handoff

This PASS verifies completeness and internal consistency of the *pre-result selection contract*. It does not prove any S2 validation result exists or is absent outside the checked repository paths, and it does not validate future successor code, report hashes, R3 proof, threshold lock, or sealed-test evaluation. Those remain separate gates. `graft check .` was in sync at review time.
