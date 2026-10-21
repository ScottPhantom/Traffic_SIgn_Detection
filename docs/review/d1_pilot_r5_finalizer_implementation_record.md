# D1 Pilot R5 packaged-state finalizer implementation record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Status: `R5_AWAITING_INDEPENDENT_SOURCE_QA`

## Scope

Pilot R4 successfully reused the verified `epoch-0100` checkpoint without training another epoch
and created the final result archive, manifest, retry-aware SQLite log and text log. Its final
notebook readback exposed two post-package verification defects:

1. the reconstructed experiment directory remained as the checkout's sole untracked path, so the
   inherited clean-checkout guard rejected the otherwise immutable source checkout; and
2. the inherited R6 wrapper reinstalled its original two-attempt validator while verifying the
   archive, shadowing Pilot R3's retry-aware validator. The real pilot now has six attempts: one
   fresh pause, four failed resumes retained as evidence and one successful final resume.

Independent source QA then demonstrated two additional fail-open cases in the first R5 candidate:

3. a structurally valid retry history with a different number of attempts could pass; and
4. the live SQLite/text-log paths could be symlinks to files outside the reviewed state directory.

R5 is an append-only verification successor. It does not train, package, export test data or run a
final evaluation. It verifies the packaged Drive state and makes no model-quality decision.

## Repair

`detector/colab/run_d1_colab_pilot_r5.py`:

- pins the training checkout to commit `939f6bbce9f5c955b13ebcc84addd5083d242355`;
- pins the R3 and R4 sidecars by SHA-256;
- permits cleanup only when Git reports the exact expected reconstructed run directory as the sole
  untracked path;
- authenticates all seven pinned Drive artifacts, their manifest bindings and both predecessor
  sidecar hashes before exact cleanup; cleanup then precedes the predecessor's mandatory clean-Git
  guard and semantic checkpoint/runtime/log verification;
- requires an exact `git clean -nd -- <run>` result before running the matching `git clean -fd`;
- refuses symlink targets, tracked changes, extra untracked files, a different run identity or a
  different terminal outcome;
- patches the retry-aware validator at the R6 wrapper boundary, where the inherited implementation
  previously shadowed the R3 patch;
- requires the exact observed history of six attempts and four failed resumes, rejecting integer,
  boolean and count substitutions;
- independently compares retry-aware live evidence with the R6 checkpoint/archive verifier;
- requires the execution record, attempt journal, SQLite database, text log, latest pointer,
  result archive and result manifest to be regular non-symlink files with exact size and SHA-256;
- checks that the verified archive manifest binds the byte-identical live execution record and
  SQLite database (the live text log is pinned separately because the failed R4 readback appended
  its traceback after the already-created archive);
- reruns R4 retry-aware SQLite/text-log validation against the 100-row `results.csv`;
- requires one archive, its manifest, `epoch-0100` and `sealed_test_accessed=false`.

## Live artifact readback before source QA

The R4 packaging command completed with return code 0. A local snapshot of the synced Drive state
was verified from a clean detached clone of the training commit:

- status: `D1_PILOT_R5_PACKAGED_STATE_VERIFIED`;
- attempts: `6`;
- failed resumes retained: `4`;
- distinct runtime digests: `true`;
- latest generation: `epoch-0100`;
- archive SHA-256: `6ae2e6a29e1712ff5372764d5cc1eb6bb7ae9c9d06d7a08de8aab3e3c2f6778f`;
- manifest SHA-256: `0ecac47986d946ed83dfbac1e203f60b4e6055e5054ed9c52476db128b7f7796`;
- `sealed_test_accessed=false`.

The amended candidate passed 17 focused tests, including the independent-QA counterexamples, and
the same temporary snapshot reverified successfully after the exact artifact pins were added.

This is PM implementation evidence, not independent QA. Direct SQLite access on the Google Drive
Desktop mount stalled in file-provider I/O, so the successful verification used a byte-for-byte
temporary local snapshot of the required live files. The Drive originals were not modified.

## Authorization boundary

- R5 source release, commit/push and notebook pin: **NO-GO pending independent QA PASS**.
- R5 Colab finalizer execution: **NO-GO pending source release and notebook-pin QA**.
- D1 pilot artifact acceptance: **NO-GO pending independent artifact QA**.
- Sealed-test access, final evaluation, model acceptance and deployment: **NO-GO**.
