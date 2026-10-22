# M1 Colab WP38-R1 R4 bundle R2 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_PASS`

Reviewer: `Codex independent QA session (read-only source/contract review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted bundle R2 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_OFFICIAL_ARCHIVE_NO_NETWORK_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

R2 closes bundle R1 finding M-1-R1. The public manifest validator and archive-reader boundary now
enforce exact container and primitive types, exact key sets, lowercase hexadecimal commit/digest
formats, governed counts, the closed file-kind vocabulary and non-Boolean integer sizes/counts.
An independent matrix of 231 malformed-schema mutations was rejected in full, while a valid typed
synthetic manifest and the genuine 5,927-file manifest both passed.

The genuine roster remains exact, train/validation-only and bound to the accepted integration R4
exporter, manifest and independent QA PASS record. Inherited archive traversal/link/duplicate,
determinism, no-overwrite, partial-cleanup and dirty-checkout controls also passed replay.

This PASS changes the source state only to `READY_FOR_OWNER_COMMIT_DECISION`. It does not authorize
commit, archive creation, Drive upload or any other external write. It does not authorize model
training, evaluation or sealed-test access.

No official archive was built. QA used only in-memory manifests and tiny local fixtures outside the
repository. No reviewed source or existing artifact was modified; no network access occurred.

## Closure of M-1-R1

Bundle R1 and its independent QA FAIL record remain immutable. R2 adds an append-only schema-3
successor with these independently reproduced controls:

1. The top-level manifest must be an exact `dict` with the exact required key set.
2. `schema_version` and `file_count` must be non-Boolean integers with exact values 3 and 5,927.
3. Package/status fields must be exact strings; allowed splits must be the exact list
   `["train", "val"]`; policy flags must be exact booleans with governed values.
4. `repo_git_commit` must be exactly 40 lowercase hexadecimal characters.
5. All twelve authority SHA fields and every file SHA must be exactly 64 lowercase hexadecimal
   characters.
6. `counts` must be an exact six-key dictionary. Every value must be a non-Boolean integer equal
   to the governed count.
7. Every file record must be an exact five-key dictionary. Paths must be safe strings,
   `source_split` must be exactly `train|val`, `kind` must belong to the five-value closed
   vocabulary, and `size` must be a nonnegative non-Boolean integer.
8. Duplicate normalized paths remain forbidden.
9. The R2 manifest binds both the immutable R1 source hash and its independent QA FAIL-record hash.

## Independent type-strict replay

QA first accepted a valid typed synthetic 5,927-record manifest, then changed one condition at a
time and restored it after each rejection. **231/231 mutations were rejected.** Coverage included:

- missing and extra top-level keys;
- Boolean, float, string and negative substitutions for `schema_version` and `file_count`;
- non-string, wrong-value and whitespace variants for package/status;
- tuple, string, missing, extra and test-bearing split declarations;
- numeric/string/null and wrong Boolean values for all three policy flags;
- non-string commit values, uppercase hex, invalid alphabet, whitespace and lengths 0/39/41;
- for every one of the twelve authority SHA fields: non-string, Boolean, null, uppercase hex,
  invalid alphabet, whitespace and lengths 0/63/65;
- non-dictionary counts plus missing/extra nested keys;
- for every governed count: Boolean, float, string, negative and wrong integer values;
- non-list file rosters and list-length/file-count disagreement;
- missing and extra file-record keys;
- non-string, traversal, absolute, backslash and dot-component paths;
- non-string, uppercase, invalid-alphabet, whitespace and wrong-length file hashes;
- non-string, test, empty and whitespace split values;
- non-string, Boolean, unknown, empty and whitespace file kinds;
- Boolean, float, string, negative and null sizes;
- duplicate normalized file paths.

This directly replays all four R1 failures (`counts=True`, numeric commit, numeric authority SHA and
numeric kind) and expands the test to every authority field and nested numeric/string boundary.

## Genuine roster and authority replay

QA built the genuine manifest only in memory and validated all 5,927 current source records. Every
source was a regular nonsymlink file with the exact governed hash and recorded size.

- exact unique records: **5,927/5,927**;
- raw train images: **1,912**;
- raw validation images: **337**;
- corrected WP38-R1 validation images: **39**;
- corrected WP38-R1 validation labels: **39**;
- WP35 train images: **1,800**;
- WP35 train labels: **1,800**;
- corrected stems: exact `1319..1357`;
- source splits: exact set `{train, val}`;
- test payload paths: **0**;
- integration R4 exporter, manifest and QA PASS-record bindings: exact;
- bundle R1 source and QA FAIL-record bindings: exact;
- contract result: `valid=true`, `test_included=false`, `sealed_test_accessed=false`,
  `training_authorized=false`.

The sealed-test stem-list digest remains governance metadata only. QA did not enumerate or open
sealed-test image or label content, and the sealed-test access log remained absent.

## Inherited archive and output replay

All archive construction used tiny local fixtures rather than the official roster.

| Attack/control | Result |
| --- | --- |
| `../` traversal member | rejected |
| absolute-path member | rejected |
| backslash member path | rejected |
| duplicate tar member | rejected |
| symlink tar member | rejected |
| hardlink tar member | rejected |
| duplicate JSON key | rejected |
| archive path that is itself a symlink | rejected |
| Existing archive, sidecar, partial or sidecar-partial as regular files | **4/4 rejected** |
| Existing archive, sidecar, partial or sidecar-partial as symlinks | **4/4 rejected** |
| Injected payload-write failure | archive, sidecar and both partials absent afterward |
| Two equivalent tiny builds | byte-identical gzip/tar output |
| Tiny archive member contract | regular-only, mode 0644, mtime/uid/gid 0, empty owner names |
| Authoritative dirty checkout | rejected before archive or sidecar creation |

The CLI exposes only `contract`, `build` and `verify`; it contains no test-export or final-evaluation
path.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Exact requested R2 source/test/R1-QA hashes | PASS, **3/3** |
| Targeted R2 tests | PASS, **16/16** |
| Contract verifier | PASS, `valid=true`, **5,927 files** |
| Independent type-strict mutation matrix | PASS fail-closed, **231/231 rejected** |
| Valid synthetic schema control | PASS |
| Genuine in-memory manifest and source replay | PASS, **5,927/5,927** |
| Exact roster/count/split/authority binding replay | PASS |
| Unsafe archive/member attacks | PASS fail-closed, **8/8 rejected** |
| No-overwrite attacks | PASS fail-closed, **8/8 rejected** |
| Deterministic regular-file archive fixture | PASS |
| Partial-output cleanup fixture | PASS |
| Dirty-checkout pre-write gate | PASS |
| Repository verifier matrix | PASS, **61/61** |
| Ruff for exact R2 exporter and tests | PASS |
| Root lock | PASS, resolves **168 packages** |
| `git diff --check` | PASS |
| Graft | PASS, wiring graph synchronized |
| Sealed-test access log | absent before and after QA |

Graft was used before source review. The freshness-aware scoped query reported approximately
33,736 tokens saved (about USD 0.02).

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_colab_bundle_wp38_r1_r2.py` | `4528310078a4b1f0bb0450ab0ce830d09cec6213e720eb596b871eb8a2c8d71f` |
| `tests/test_m1_colab_bundle_wp38_r1_r2.py` | `7eee624ca1b78543cbc0cdfe20a0aae83e176a76fa56db2c0145eab75fafd2d1` |
| Bundle R1 independent QA FAIL record | `35bd63cbd5906834ec1674312096286b3343bf18f056f3051a7e9e28875f3fb6` |
| `docs/review/m1_colab_wp38_r1_r4_bundle_r2_qa_remediation_report.md` | `1fcfca728ef741cec60838d017b323056c600ca18235b419182f4cae3f0b031e` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| R1 type-strict finding M-1-R1 | **PASS / closed** |
| Exact 5,927-file roster and source bytes | **PASS** |
| R4 and R1 predecessor authority bindings | **PASS** |
| Train/validation-only and no-test payload | **PASS** |
| Archive traversal/link/duplicate defenses | **PASS** |
| Deterministic archive/no-overwrite/cleanup controls | **PASS** |
| Clean-checkout gate | **PASS** |
| Bundle R2 independent QA | **PASS** |
| Source state | **READY_FOR_OWNER_COMMIT_DECISION** |
| Commit, official archive build or upload | **NOT AUTHORIZED BY THIS RECORD** |
| New model training or evaluation | **NOT AUTHORIZED** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: bundle R2 is ready for the Owner to decide whether to authorize a clean commit.
Only after that separate decision may a clean-checkout archive build and any private upload be
considered. This QA PASS itself authorizes none of those actions.
