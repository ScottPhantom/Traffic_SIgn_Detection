# D1 corrected-validation evaluator R6 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-and-adversarial QA session`  
Boundary: `NO_REAL_MODEL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

R6 correctly removes R5's mutable staging-source pathname and verifies the final reserved inode,
bytes and link count through a retained run-directory descriptor. It nevertheless returns a
lexical path whose ancestor binding is checked only before the permission-based publication event.
A same-user concurrent actor can replace the run-directory binding immediately after the second
relation check. All later inode, link-count and hash checks then pass inside the detached retained
directory, while the returned lexical path resolves through the replacement directory.

A deterministic temporary-directory reproduction using the real R4 directory-chain and relation
validators made `_safe_write_report()` return success while its returned path contained
`OWNER\n` with mode `0644`; the verified report was instead made readable with mode `0400` in the
detached original directory. R6 is therefore **NO-GO** for real corrected-validation inference.
Preserve R1-R6 and their QA records; repair this issue only in an append-only successor and submit
that successor's exact bytes to fresh independent QA.

`sealed_test_accessed=false` throughout this review.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r6.py` | `fe7280b194f9f39da4db917717df7e3234fa083610c3dbd6e87f41f5cae389de` |
| `detector/tests/test_corrected_val_r6.py` | `768ca31abc71f6f630c42fcfd9b37019f479089cd3768a75c687351b8dd31414` |
| `docs/review/d1_corrected_val_r6_qa_remediation_report.md` | `ee745b0ea8b801452ed00619a766e15271f0c9aa93973d311fbea3aa768eb136` |
| `docs/review/d1_corrected_val_r5_independent_qa_record.md` | `0544ebcaf84675a17ba23f71fddbac560e432ad66059926b6e035a93caa38660` |

All four hashes matched the requested pins before and after the review. No reviewed
implementation, test, remediation or predecessor-QA file was modified. This append-only record is
the only QA-authored repository artifact.

## Review performed

- Read `PROJECT_MEMORY.md`, the R6 remediation record and the pinned R5 independent QA record.
- Used a freshness-aware Graft query to trace `_safe_write_report()` and its inherited directory
  authority, then confirmed `graft check .` reported the wiring graph in sync.
- Traced R6's final-name reservation, exact serialization, descriptor/path identity, link-count,
  hash, relation, publication, failure-quarantine and descriptor-close paths.
- Ran `ruff` on the exact R6 source and test: PASS.
- Ran the exact R6 suite: **12/12 PASS**.
- Ran the R4/R5 publication regressions excluding their duplicate authority checks: **17/17
  PASS**.
- Ran the real R4 integration suite, including directory-chain and sealed guards: **11/11 PASS**.
- Ran `uv lock --check` in `detector/`: PASS.
- Ran one adversarial reproduction only in an automatically removed temporary directory under
  `detector/`; it used no model weights, image inference or sealed-test data.

Green mechanical tests do not establish that the lexical `Path` returned by R6 still names the
inode published through the retained directory descriptor.

## Verified retained properties

- The CLI remains validation-only: only `check` and `evaluate` exist, and R6 contains no test
  export or final-evaluation command.
- The final report name is reserved directly with `O_CREAT | O_EXCL | O_NOFOLLOW` and mode `000`.
- R6 serializes deterministic JSON with one trailing newline, writes and hashes through the
  retained descriptor, and checks that the descriptor and the name under `root_fd` are the same
  regular single-link inode.
- Pre-existing regular-file, symlink and hardlink collisions are preserved by the exclusive
  reservation.
- Content mutation, injected hardlinks and final-name replacement are detected. On pre-publication
  failure, the owned descriptor is forced back to mode `000` without deleting a pathname.
- Directory relations are validated before reservation and a second time before publication.
- `fchmod(report_fd, 0400)` is the publication event. A descriptor-close error after successful
  publication does not reverse success.
- The authority check reported `val_frames=376`, `corrected_frames=39`, `test_included=false` and
  `sealed_test_accessed=false`.

These properties close R5's source-candidate race but do not close the ancestor-binding race below.

## Finding

### QA-D1-CORR-VAL-R6-001 — High — success can return a path that is not bound to the published descriptor

`_safe_write_report()` receives `root_fd`, retained ancestor descriptors and relation tuples at
lines 110-113 of `detector/m1/corrected_val_r6.py`. The inherited `_open_directory_chain()` records
each parent-name-child relation at lines 179-198 of
`scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py`; `_validate_relations()` checks those
bindings at lines 222-231.

R6 performs the second relation validation at line 133, then checks the final name only relative to
the retained `root_fd` at line 134. It subsequently publishes through `report_fd` at lines 136-139,
checks the name again only relative to that same retained `root_fd` at lines 140-142, marks success
and returns `run_dir / REPORT_NAME` at lines 143-144. There is no relation validation after the
publication event and no proof that the returned lexical path still traverses the retained
ancestor descriptors.

The independent reproduction wrapped the real R4 `_validate_relations()` implementation. On its
second call it first let the real validator succeed, then moved the original run directory and
created a replacement directory plus an Owner file at the same lexical report path before control
returned to R6. Observed result:

```text
validate_calls=2
returned_content="OWNER\n"
returned_mode=0644
detached_verified_report_mode=0400
_safe_write_report returned successfully
```

The retained `root_fd` correctly kept R6's descriptor operations attached to the original
directory, so `_require_owned_final()` and the exact-byte hash both passed. That strength is also
the reason they did not notice that the lexical `run_dir` binding had changed. The function then
returned a path resolving to the Owner-controlled replacement instead of the verified report.

The existing relation-failure tests cover a validator that fails on its first or second call. They
do not change an ancestor binding immediately after a successful second check. The exact suite's
12/12 PASS therefore does not exercise this interval.

Impact: a corrected-validation command can report success while the path delivered to the caller
names different bytes, permissions and inode identity from the generated evidence. Downstream
review or gate logic can consequently consume attacker-controlled content or fail to locate the
actual report. Because this report is intended to support model-evaluation decisions, the loss of
publication/path identity is a High-severity blocker.

Required append-only repair:

- Define one authority for both publication and downstream consumption. Do not return a lexical
  path as proof of the object published only through a retained directory descriptor.
- If a path must remain the API, establish a trusted/stable namespace boundary and rebind the
  published descriptor to the path under that authority; finite point-in-time ancestor checks
  alone do not make a same-user-mutable pathname durable.
- Add an adversarial test that swaps the run-directory relation immediately after the last
  successful pre-publication relation validation and require fail-closed behavior or a
  descriptor-bound result.
- Preserve R6's collision non-overwrite, mode-`000` quarantine, exact-byte/hash, single-link,
  validation-only and post-success-close properties.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R6 and this immutable FAIL record | **YES** |
| Implement an append-only successor | **YES** |
| Run R6 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train or retrain | **NO-GO** |
| Access, export or upload sealed test | **NO-GO** |
| Treat 12/12 exact tests as QA PASS | **NO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run corrected validation on the existing registered pilot. Such a PASS would still not authorize
training, sealed-test access, final evaluation, model acceptance, deployment or publication.
