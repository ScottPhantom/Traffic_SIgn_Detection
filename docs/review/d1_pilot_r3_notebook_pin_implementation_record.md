# D1 Pilot R3 recovery notebook pin implementation record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: `IMPLEMENTED_LOCALLY_PIN_QA_PENDING_NO_LIVE_RESUME`

The resume-only notebook `detector/colab/d1_train_pilot_r3.ipynb` is generated from immutable Pilot
R2 notebook SHA-256 `721c5c0f35eb58719bcc6b5a71ce24cce136388bb8060bc2393aec7a5da4b1ae`.

It deliberately separates two identities:

- the clean training checkout remains pinned to checkpoint-bound commit
  `939f6bbce9f5c955b13ebcc84addd5083d242355`;
- the QA-passed recovery sidecar is fetched from implementation commit
  `e20a69541e3a6327739238fc71691109ce8f51d0` and must match SHA-256
  `8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c` before it is written or
  executed outside the training checkout.

The notebook fixes `MODE="resume"`, requires the existing Drive recovery pointer, contains no fresh
branch or stop-after-epoch argument, and retains the exact Pilot R2 seed/model/training configuration.
Its terminal cell requires `SUCCEEDED`, epoch 100, `epoch-0100`, exactly one result archive,
retry-aware live evidence and `sealed_test_accessed=false`.

The first notebook-pin QA found a High replacement window between download verification and later
execution/import. Repair R1 now writes the sidecar with exclusive `O_NOFOLLOW` creation, rejects
symlink/non-regular files, reads through an `O_NOFOLLOW` descriptor and re-hashes the bytes at every
use. Training executes those already-verified bytes through Python stdin; final verification
compiles/imports those already-verified bytes in memory. Neither path re-opens an unchecked script.
Regression coverage replaces the runner after an earlier successful verification and confirms the
replacement is rejected before its marker code can execute; a symlinked runner is also rejected.

No live Colab resume, Drive mutation, sealed-test access, final evaluation or model acceptance is
claimed. Independent notebook-pin QA is required before execution.
