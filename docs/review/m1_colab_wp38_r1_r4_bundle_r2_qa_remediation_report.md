# M1 Colab WP38-R1 R4 bundle R2 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `NO_ARCHIVE_BUILT_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_TRAINING_NO_SEALED_TEST`

## Scope

Bundle R1 and its independent QA `FAIL` record remain immutable. R2 addresses only finding
M-1-R1: the public archive-manifest reader was not fully type-strict even though full semantic
archive verification still rejected the reported mutations.

## Type-strict remediation

Schema 3 requires exact types and values for every authority field:

- `counts` is an exact six-key object; every value is a non-Boolean integer equal to the governed
  count.
- `repo_git_commit` is exactly 40 lowercase hexadecimal characters.
- Every authority and file SHA-256 is exactly 64 lowercase hexadecimal characters.
- `kind` is a string in the closed vocabulary `raw_image`, `wp38_r1_image`, `wp38_r1_label`,
  `wp35_image`, `wp35_label`.
- `source_split` is a string in `train|val`; `size` and `file_count` are non-Boolean integers;
  `file_count` is exactly 5,927.
- Policy flags are exact booleans; package/status/split fields are exact typed values.

R2 also binds the immutable R1 source and its independent QA FAIL record in the manifest metadata.
All earlier roster, path/member, deterministic archive, no-overwrite, partial cleanup and
clean-checkout controls are inherited unchanged.

## Current evidence

- QA-reported mutations `counts=True`, numeric commit, numeric/uppercase SHA and numeric/Boolean/
  unknown/whitespace `kind`: rejected.
- Boolean, float, string, negative or wrong governed counts: rejected.
- Typed synthetic manifest: accepted.
- Targeted R2 tests: 16/16 PASS.
- Contract verifier: `valid=true`, exactly 5,927 train/validation files.
- No official archive built; no Drive write; sealed-test access log absent.

## Exact QA inputs

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_colab_bundle_wp38_r1_r2.py` | `4528310078a4b1f0bb0450ab0ce830d09cec6213e720eb596b871eb8a2c8d71f` |
| `tests/test_m1_colab_bundle_wp38_r1_r2.py` | `7eee624ca1b78543cbc0cdfe20a0aae83e176a76fa56db2c0145eab75fafd2d1` |
| Bundle R1 independent QA FAIL record | `35bd63cbd5906834ec1674312096286b3343bf18f056f3051a7e9e28875f3fb6` |

## QA gate

Independent QA must replay the full R1 mutation matrix plus schema/type confusion, exact roster and
R4 authority bindings. A PASS changes source state only to `READY_FOR_OWNER_COMMIT_DECISION`; it
does not authorize commit, archive build, upload, training, evaluation or sealed-test access.
