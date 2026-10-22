# M1-WP38-R1 downstream integration R4 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_PASS`

Reviewer: `Codex independent QA session (read-only source/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted R4 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_FIX_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_NETWORK_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

R4 closes R3 finding H-1-R3. Marker, output-root and output-parent identity changes are rejected
after descriptor-bound verification begins. The final materialisation result is accepted only when
the public root has the exact device/inode captured from the root created by that invocation.
Retained marker/root/parent/tree descriptors are closed on success and every injected failure
path exercised by this review.

The materialised candidate independently verifies as an exact train/validation-only bundle:
3,712 train image/label pairs, 376 validation image/label pairs and exactly 39 corrected validation
stems `1319..1357`. No test directory or test payload is present. The sealed-test access log is
absent and every R4 result/marker reviewed declares `sealed_test_accessed=false`.

No reviewed source, manifest, predecessor or existing artifact was modified. QA used only local
fixtures. No model training, evaluation, network access, upload, commit, push or sealed-test access
occurred.

## Closure of H-1-R3

The R3 package and its independent QA FAIL record remain immutable. R4 closes the exact identity
gap through the following independently reproduced properties:

1. Every component of the absolute output path is opened with no-follow directory flags and kept
   in a retained descriptor chain.
2. The completion marker is opened relative to the retained root. Its bytes are read from that
   exact descriptor, and its single-link regular-file inode is revalidated before and after the
   semantic replay.
3. `images`, `labels`, `train` and `val` are opened descriptor-relatively. Their exact rosters,
   image symlink targets, governed source hashes, regular label bytes and `data.yaml` are replayed
   without reopening the public output root by pathname.
4. Every parent/name/child directory relationship is revalidated before success is returned.
5. Materialisation captures the created root's `(st_dev, st_ino)` and passes that identity into
   final verification. A different public root is rejected before its contents can be accepted.
6. All retained descriptors are closed in reverse order, and the marker descriptor is closed
   separately in the `finally` path.

## Independent identity attacks

The following attacks were run through the real R4 verifier using physical, local temporary
paths. Each attack changed object identity while preserving otherwise acceptable bytes where
applicable. Every attack returned `valid=false`, and `/dev/fd` matched its exact pre-attack set
after return.

| Attack | Result |
| --- | --- |
| Replace marker with a new same-byte regular file during replay | **REJECTED; descriptors clean** |
| Replace marker with a symlink to a same-byte external marker | **REJECTED; descriptors clean** |
| Replace marker with a hardlink to a same-byte external marker | **REJECTED; descriptors clean** |
| Replace the complete public output root during replay | **REJECTED; descriptors clean** |
| Replace the public output parent during replay | **REJECTED; descriptors clean** |
| Give final verification an identity different from the created root | **REJECTED** |
| Replace the public root after a real local materialisation but before final verify | **REJECTED; created inode pin observed; descriptors clean** |

For the active materialiser attack, QA observed that the captured expected identity exactly equaled
the root inode created and populated by the invocation. The replacement public root had a distinct
identity. Materialisation raised instead of returning `verified=true`; it did not attach success
to the replacement tree.

The R4 test module additionally injected failure while opening the absolute directory chain and
confirmed all already-opened descriptors were closed without masking the injected exception.

## Independent roster and boundary replay

Descriptor-bound verification of the current candidate returned `valid=true`. Independent direct
enumeration, limited to the materialised train/validation output, established:

- output-root roster: exactly `images`, `labels`, `data.yaml`, and `EXPORT_COMPLETE.json`;
- train: **3,712** image symlinks and **3,712** regular nonsymlink labels;
- validation: **376** image symlinks and **376** regular nonsymlink labels;
- corrected validation links: exactly **39**, stems `1319..1357`;
- corrected images are validation-only and target the governed
  `wp38_r1_orientation_corrected` derivative;
- `images/test` and `labels/test`: absent;
- completion marker: exact R4 schema, including `train=1912`, `train_wp35=1800`, `val=376`,
  `test_included=false`, and `sealed_test_accessed=false`;
- available CLI actions: only `manifest`, `verify`, `export`, and `verify-export`; no
  `export-test` or `--final-eval` path;
- sealed-test access log: absent before and after QA.

QA did not enumerate or open sealed-test image or label content.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Exact requested review hashes | PASS, **3/3** |
| R4 manifest verification | PASS, `valid=true` |
| R4 test module | PASS, **11/11** |
| Independent marker identity attacks | PASS, **3/3 rejected** |
| Independent root/parent identity attacks | PASS, **2/2 rejected** |
| Active materialiser replacement attack | PASS, replacement rejected |
| Descriptor cleanup across independent attacks | PASS, exact `/dev/fd` equality |
| Current materialised descriptor replay | PASS, `valid=true` |
| Exact train/validation/correction/no-test roster | PASS |
| Ruff for the exact exporter and test | PASS |
| Root lock | PASS, resolves **168 packages** |
| `git diff --check` | PASS |
| Graft | PASS, wiring graph synchronized |
| Sealed-test access log | absent before and after QA |

Graft was used before source review. The scoped flow query reported approximately 21,862 tokens
saved (about USD 0.01).

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py` | `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json` | `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` |
| `tests/test_m1_wp38_r1_integration_r4.py` | `98edd4001d288053de9c405728daf71871472c6f0fdd4871b4731146fc1979cf` |
| `docs/review/m1_wp38_r1_integration_r4_qa_remediation_report.md` | `9710049de987bc0e191ab6075221fac9b2ed7ebc20c99bc0794e0e749f38abd9` |
| R3 independent QA FAIL record | `2e5820573e8efcac03b176fdf79717ef74604c81700e98ac5d046b2b8825fc17` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Marker/root/parent identity binding | **PASS** |
| Materialiser-created root identity binding | **PASS** |
| Descriptor lifecycle | **PASS** |
| Exact train/validation/corrected roster | **PASS** |
| No-test and sealed-test boundary | **PASS** |
| R4 integration acceptance | **PASS** |
| Bundle/corrected-validation preparation | **GATE OPEN, subject to normal owner workflow** |
| Corrected-validation evaluation | **NOT AUTHORIZED BY THIS RECORD** |
| New model training | **NOT AUTHORIZED** |
| Upload, commit or push | **NOT AUTHORIZED BY THIS QA RECORD** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: R4 passes independent QA for preparation of the governed train/validation bundle
and corrected-validation data path. This record does not authorize training. Evaluation, upload,
commit/push and any sealed-test action remain separate owner-governed steps.
