# D1 corrected-validation evaluator R4 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-QA session`  
Boundary: `READ_ONLY_NO_REAL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 1 Medium and 0 Low findings.**

R4 successfully makes macOS `renameatx_np(..., RENAME_EXCL)` the final report-publication mutation.
Pre-existing, immediately inserted and concurrently competing final names are never overwritten or
deleted. The R3 private-snapshot protections also remain effective. However, pre-publication
partial cleanup retains the same non-atomic `stat` then `unlink` authorization pattern that failed
R3, and the first descriptor close after successful publication is unguarded. Independent attacks
deleted an Owner replacement at the partial name and produced a raised failure after a valid final
report had already been atomically published.

R4 remains **NO-GO** for real corrected-validation inference. Preserve R1–R4 and their QA records;
implement an append-only successor and submit its exact bytes to fresh independent QA.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r4.py` | `5d3f69b8fa6e150acfc9fbf7d9ca1b9aa8e0af1c43538c175125e3dbe3a88e18` |
| `detector/tests/test_corrected_val_r4.py` | `50614fe194e4218f537f096ed1ad69dad530e143cf94ab107f044c5974c99e4a` |
| `docs/review/d1_corrected_val_r4_qa_remediation_report.md` | `645727f18d03a94f25410d7527e24e60a9542de79fd6b9aed4cba40cf6774bc3` |
| R3 independent QA FAIL record | `d8624a2beaf998d051e55952acab1407895e43a6980f61527089633e038e7b93` |
| pinned R4 integration exporter | `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426` |
| R4 integration independent QA PASS record | `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591` |
| pinned R4 integration manifest | `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

All requested hashes matched before review. Final readback below reconfirms the candidate hashes.
No reviewed implementation or test source was modified. This append-only record is the only
QA-authored repository artifact.

## Verified properties

### Atomic final publication

- Nominal publication produced exactly one regular final report and no partial. No unlink was
  invoked after successful `RENAME_EXCL`.
- Pre-existing final regular files, symlinks and hardlinks were rejected with `EEXIST`; Owner bytes
  and directory entries were preserved.
- Independent interposition installed each of regular, symlink and hardlink destinations
  immediately before the atomic rename. All were preserved, the evaluator partial was removed and
  publication failed without a success claim.
- Two publishers were synchronized at the rename syscall. Exactly one atomically succeeded, the
  other received `EEXIST`, and the directory contained exactly one final report and no partial.
- Ordinary pre-publication failures injected at write, fsync, partial hash, partial stat, relation
  validation and rename cleaned the invocation-owned partial and restored descriptor counts.

These properties close R3's final-name replacement race, but they do not close the partial cleanup
race or post-publication false-failure path below.

### Private snapshot, authority and metrics

- Retained checkpoint descriptors defeated public checkpoint replacement. Image, label,
  corrected-data root and parent swap-back attacks either copied the original bytes into the
  private snapshot or failed on governed hashes. Forced EVIL source-open and destination-hash
  mutations were rejected before a consumer could run.
- Both model consumers remain confined to the private 754-entry snapshot. The snapshot is destroyed
  before report publication.
- The real R4 dependency suite passed **11/11**: 376 validation frames, 39 corrected frames,
  train/validation-only materialisation, `test_included=false` and
  `sealed_test_accessed=false`.
- Parser choices remain exactly `check` and `evaluate`; there is no train/test/final-eval route.
- The governed corrected-stem UNKNOWN transform remains `x'=y`, `y'=1-x`, `w'=h`, `h'=w`
  before pixel conversion. Numeric replay mapped `[0.25, 0.40, 0.10, 0.20]` to
  `[0.40, 0.75, 0.20, 0.10]`, then `[3.0, 14.0, 5.0, 16.0]` for a 10x20 image.
- The registered pilot remains bound to seed `20261018`, weight SHA-256
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`, run-contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`, attestation SHA-256
  `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc` and registry SHA-256
  `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`.
- Metric construction and bounded one-image-at-a-time prediction remain inherited from the pinned
  R3/R2/R1 flow. No real model inference/evaluation or training was run. The sealed-test access log
  was absent before and after QA.

## Findings

### QA-D1-CORR-VAL-R4-001 — High — random partial cleanup can delete an Owner replacement

`_cleanup_random_partial()` at lines 361–369 checks the partial's inode with `os.stat()` and then
performs a separate pathname `os.unlink()`. Random naming reduces accidental collision probability,
but does not make those two operations atomic or prevent a same-user concurrent actor from
observing/replacing the entry after creation.

Independent reproduction injected a relation failure before publication. After cleanup had
authorized the evaluator inode but before unlink, the attacker removed that link and moved its
unique `OWNER` file into the random partial name. The evaluator then deleted the replacement:

```text
PARTIAL_RACE True False []
```

`True False` means the race fired and the unique Owner path no longer existed. This violates the
R3 QA requirement to retain the replacement-between-check-and-unlink attack for both final and
partial cleanup and contradicts the no-external-deletion boundary.

Required append-only repair: never make a later pathname unlink decision from an earlier inode
observation. If conditional unlink cannot be guaranteed, leave a non-authoritative random partial
for explicit recovery rather than risk deleting a replacement, and record the cleanup failure.

### QA-D1-CORR-VAL-R4-002 — Medium — unguarded close can report failure after publication

After `_rename_exclusive()` succeeds, lines 414–416 mark publication complete and return, but the
`finally` block executes `os.close(temp_fd)` unguarded at lines 420–422. An injected close error
after actually closing that descriptor propagated from `_safe_write_report()`, skipped retained-
descriptor cleanup and left the valid final report present:

```text
POST_PUBLISH_CLOSE_FAILURE True True ['eval_val_wp38_r1_r4_r4.json']
```

Thus the atomic report can exist while the evaluator reports failure, contradicting the remediation
claim that post-publication descriptor closes are non-authoritative and cannot create a false
failure. The same unguarded close can also interrupt pre-publication cleanup and descriptor closure.

Required append-only repair: handle every descriptor close independently, continue closing the
remaining descriptors, and ensure cleanup errors after atomic publication cannot change the
success result. Retain explicit before/after descriptor-count and injected-close tests for every
failure and success phase.

## Mechanical evidence

```text
graft check .
graft ask "Trace corrected_val_r4 report publication ..." --source .
cd detector && uv run ruff check m1/corrected_val_r4.py tests/test_corrected_val_r4.py
cd detector && uv run pytest -q tests/test_corrected_val_r4.py
cd detector && uv run ruff check m1 tests && uv run pytest -q && uv lock --check
uv lock --check
uv run pytest -q tests/test_m1_wp38_r1_integration_r4.py
```

Observed results:

- exact R4 tests: **9/9 PASS**;
- full detector suite: **136/136 PASS**;
- R4 integration dependency tests: **11/11 PASS**;
- detector Ruff, root/detector locks and `git diff --check`: **PASS**;
- Graft wiring graph: **OK / synchronized** after freshness-aware query;
- exact sealed-test access log absent.

The green nominal tests do not exercise either confirmed adversarial finding.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R4 and this FAIL record | **YES** |
| Implement append-only evaluator R5 | **YES** |
| Run R4 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train/retrain | **NO-GO** |
| Access/export/upload sealed test | **NO-GO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run validation on the existing registered `best.pt`. Such a PASS would still not authorize
training, upload, sealed-test access, final evaluation, model acceptance or deployment.
