# D1 corrected-validation evaluator R3 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-QA session`  
Boundary: `READ_ONLY_NO_REAL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

R3 closes R2's transient input-swap problem by making both Ultralytics consumers read an
exclusive private snapshot copied from verified open descriptors. It also closes the early
descriptor leak, preserves the validation-only/R4/registered-weight/CCW90/metric contracts, and
passes its nominal report-failure tests. However, its cleanup helper still separates the inode
check from pathname unlink. A replacement installed between those two syscalls is deleted even
though the evaluator did not create it. Therefore the claimed exact-inode rollback and no-external-
deletion property is false, and R3 is not authorized for a real validation run.

Preserve R1, R2, R3 and their QA records. Implement an append-only successor and submit its exact
bytes to fresh independent QA.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r3.py` | `7d356ed0bead2dedefcbe008ba2718d0a0d4ff65f26d94b35af162face993a34` |
| `detector/tests/test_corrected_val_r3.py` | `fc4e02733a52e5634c7cc86300b9d69c8d9ee6968b5d16f767564cb82efcd02d` |
| `docs/review/d1_corrected_val_r3_qa_remediation_report.md` | `1005695f43809c36c90beefb5d6c9f62b626ab3fd1ad213d26f50f054285c820` |
| R2 independent QA FAIL record | `19ca3e92d9631d3ab45c195d16321c107c3462482143a39ef8ba36608614e28f` |
| pinned R4 integration exporter | `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426` |
| R4 integration independent QA PASS record | `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591` |
| pinned R4 integration manifest | `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

All requested hashes matched at final readback. No reviewed implementation or test source was
modified. This append-only record is the only QA-authored repository artifact.

## Verified properties

### Private snapshot and use-time binding

- The registered pilot weight binding passed for seed `20261018`, run
  `D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2`, weight SHA-256
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`, run-contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`, attestation SHA-256
  `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc` and registry SHA-256
  `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`.
- R3 copies the checkpoint, 376 validation images, 376 labels and generated validation-only YAML
  from verified descriptors into a private temporary tree. Both `YOLO.val()` and the bounded
  one-image-at-a-time frame loader consume only paths inside that tree. Report publication now
  occurs only after the snapshot context has exited.
- Independent mocks replaced and restored the public checkpoint, image link, label, corrected-data
  root and corrected-data parent at open/copy boundaries. The snapshot either contained the
  original `GOOD` descriptor bytes or construction failed on the expected hash; no mocked consumer
  received replacement `EVIL` bytes.
- A forced EVIL descriptor at the source-open boundary and destination mutation at the final hash
  boundary were rejected. Owned failed-copy destinations were removed. Snapshot source and
  destination descriptor lifetimes returned to the baseline count.

### Authority, validation boundary and metrics

- The real R4 authority/dependency tests passed **11/11**. The contract remains 376 validation
  frames with exactly 39 corrected frames, train/validation-only materialisation,
  `test_included=false` and `sealed_test_accessed=false`.
- Parser choices are exactly `check` and `evaluate`; there is no train/test/final-eval route.
- The governed UNKNOWN boxes on corrected stems `1319..1328` are transformed in normalized
  coordinates before pixel conversion: `x'=y`, `y'=1-x`, `w'=h`, `h'=w`. Independent numeric
  replay mapped `[0.25, 0.40, 0.10, 0.20]` to `[0.40, 0.75, 0.20, 0.10]`, then to pixel XYXY
  `[3.0, 14.0, 5.0, 16.0]` for a 10x20 image.
- Metric construction remains delegated to the pinned predecessor flow: mAP50, mAP50-95,
  AP-small, per-class AP50, validation threshold selection, resolution breakdown, UNKNOWN false
  recognition, confusion matrix, error samples, group bootstrap and gate report.
- No model inference/evaluation or training was run. The sealed-test access log was absent before
  and after QA.

### Nominal report behavior

- Pre-existing final and partial names were exercised as regular files, symlinks and hardlinks;
  they were preserved without external overwrite.
- Fresh failures were injected at write, fsync, link, first unlink, stat and both relation checks.
  In the non-racing cases, exact directory rosters and file-descriptor counts returned to their
  baselines. Nominal success produced exactly one regular, single-link final report and no partial.
- These checks do not negate the replacement race below.

## Finding

### QA-D1-CORR-VAL-R3-001 — High — cleanup inode check and unlink are still racy

`_unlink_owned()` at lines 327–333 first calls `os.stat(name, dir_fd=root_fd,
follow_symlinks=False)`, compares that result with the invocation-owned inode, and then performs a
separate `os.unlink(name, dir_fd=root_fd)`. The directory descriptor prevents parent redirection,
but it does not make those two pathname operations atomic.

Independent reproduction injected a relation failure after publication so rollback ran. When the
helper had already observed the evaluator-owned final inode but before its unlink, a concurrent
actor removed that link and renamed its unique file containing `OWNER-BYTES` into `REPORT_NAME`.
The evaluator then applied its stale authorization decision to the new directory entry and
unlinked it. Observed evidence was:

```text
attack_fired True owner_exists False report_exists False roster []
UNLINK_REPLACEMENT_RACE_REPRODUCED
```

Thus an unsuccessful invocation can delete a path it did not create. This is the exact final-
replacement race requested by the R2 FAIL record and contradicts R3's remediation claim that only
the exact final inode created by the invocation is removed.

Required append-only repair:

- redesign cleanup so it never authorizes a later pathname unlink from an earlier inode check;
- avoid deleting a published name after an error if exact conditional unlink cannot be guaranteed,
  or use a publication protocol whose failure states cannot masquerade as a completed report and
  whose cleanup does not touch replaceable public names;
- retain the deterministic replacement-between-check-and-unlink attack for both final and partial
  cleanup, plus owner-byte preservation and descriptor-equality assertions.

## Mechanical evidence

```text
graft check .
graft ask "On exact current corrected_val_r3, trace private snapshot lifecycle ..." --source .
cd detector && uv run ruff check m1/corrected_val_r3.py tests/test_corrected_val_r3.py
cd detector && uv run pytest -q tests/test_corrected_val_r3.py
cd detector && uv run ruff check m1 tests && uv run pytest -q && uv lock --check
uv lock --check
uv run pytest -q tests/test_m1_wp38_r1_integration_r4.py
```

Observed results:

- exact R3 tests: **8/8 PASS**;
- full detector suite: **127/127 PASS**;
- R4 integration dependency tests: **11/11 PASS**;
- detector Ruff, root/detector locks and `git diff --check`: **PASS**;
- Graft wiring graph: **OK / synchronized** after freshness-aware query;
- exact source hashes unchanged and sealed-test access log absent.

The green nominal tests do not exercise the confirmed check/unlink replacement race.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R3 and this FAIL record | **YES** |
| Implement append-only evaluator R4 | **YES** |
| Run R3 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train/retrain | **NO-GO** |
| Access/export/upload sealed test | **NO-GO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run validation on the existing registered `best.pt`. Such a PASS would still not authorize
training, upload, sealed-test access, final evaluation, model acceptance or deployment.
