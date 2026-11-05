# D1 YOLO54 + CompactCNN classifier fusion R1 — Owner authorization record

Status: `OWNER_AUTHORIZED_CONDITIONAL_ON_ADDENDUM_QA_PASS`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Recorded by: Claude Code (Opus 5.5), side session started from the coordinating session.
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`.

This record is append-only. It edits neither the contract nor its QA record. It records an
authorization; it does not execute anything. When it was written, no fusion was implemented or
run, the classifier ran on no crop, and no fusion metric was computed or viewed.

Claim labels: **[VA]** verified artifact (re-read or rehashed in this checkout on 2026-11-05);
**[P]** proposal or binding rule for a future step; **[U]** unknown.

## 1. Pinned documents [VA]

| Document | SHA-256 |
| --- | --- |
| Contract `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` (committed in `17db663`) | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| Contract QA record `docs/review/d1_yolo54_classifier_fusion_r1_contract_independent_qa_record.md` (verdict PASS giới hạn; C1 and C2 required) | `aa3c4e384118a02fa28fb790d056951221334c7ecdefa410e02f381b83d5e902` |

Both hashes were recomputed with `shasum -a 256` in this checkout and match the values in the
handoff.

## 2. The exchange, verbatim

The coordinator wrote to the Owner, in chat:

> Contract này chưa được chạy. Trước khi chạy cần hai bước: một phụ lục sửa C1 và C2 (có QA), và anh duyệt cho chạy.

The Owner replied:

> cho phép

Source: the Owner's chat with the coordinating session on 2026-11-05, as relayed to this session
in its task brief. This session did not see the chat itself. The quoted words are reproduced as
relayed. **[U]** for anything beyond that relay.

## 3. Interpretation told to the Owner

The coordinator told the Owner, in chat, that "cho phép" is read as follows. This record adopts
that reading and nothing broader.

**A. Authorized now.** Writing the addendum that resolves corrections C1–C8 of the QA record
(`docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md`).

**B. Authorized only after an independent QA PASS of that addendum.** Implementing and executing
contract §8 steps 3–5 (as amended by the addendum) **exactly once**, offline. Step 3 is
implementation plus independent source QA of the scorer, step 4 is one execution, and step 5 is
independent result QA. Execution includes:

- the CompactCNN R2 combined classifier on **CPU, float32**, for the accuracy arm (contract §5);
- the recompute of the relabel decisions on **MPS**, to list CPU/MPS differences (contract §5);
- the **§6.4 latency arm**, with live YOLO11s-54 pilot inference and live classifier inference on
  local MPS (Apple M1 Pro).

Every arm uses the R3 **validation** images only (376 frames, roster
`24e2a67d1e176a7e09caf4b1f6daa2bf5240981d00c8e1a535640e6b8066118e`).

**Reading rule added by this record [P]; it was not part of what the Owner was told.** A
PASS giới hạn verdict on the addendum counts as a PASS only if it lists no correction that is
required before execution. If the addendum QA requires a correction, condition B is not met. A
further QA'd addendum is then needed before execution. This mirrors how the contract's own
PASS giới hạn was handled: its required C1 and C2 had to be resolved before execution.

## 4. Not authorized

- Training or fine-tuning any model, YOLO or classifier.
- App integration or enablement of any kind. No output is connected to a vehicle; behaviour output
  stays simulation only.
- Any change to D-05, the conf 0.20 operating point, NMS or any threshold, and writing any
  threshold lock.
- Opening, listing or scoring the sealed test (`afa03d4b…`). The pilot run directory name contains
  the token `afa03d4b` as a provenance label. Reading that run's `best.pt` or validation CSV is not
  sealed-test access.
- Upload to any external service.
- `git push`, and any commit not separately authorized.
- **Any re-run after results have been seen.** This includes another τ, other pairs, another
  checkpoint or a fixed bug. If the single execution ends `INVALID` or cannot complete, a new
  written Owner authorization is required before anything is run again.

## 5. Flags carried into every downstream output

`sealed_test_accessed=false`, `training_authorized=false`, `app_enable_authorized=false`,
`threshold_lock_written=false`, `d05_changed=false`, `push_authorized=false`,
`rerun_after_results_authorized=false`.

## 6. What this record does not establish

- It does not show that the addendum is correct. That is the job of the addendum's independent QA
  **[P]**.
- It does not establish any fusion result, any GO, or any D-05 progress. Under contract §7, even a
  `GO_CANDIDATE_FOR_CONFIRMATION` would only be an in-sample candidate.
