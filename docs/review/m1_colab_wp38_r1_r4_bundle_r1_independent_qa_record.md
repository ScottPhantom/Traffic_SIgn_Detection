# M1 Colab WP38-R1 R4 bundle R1 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_FAIL`

Reviewer: `Codex independent QA session (read-only source/contract review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted bundle R1 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_OFFICIAL_ARCHIVE_NO_NETWORK_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST`

## Verdict

**FAIL / NO-GO — 0 Critical, 0 High, 1 Medium and 0 Low findings.**

The source contract reproduces the exact 5,927-file train/validation-only roster, binds the
accepted integration R4 exporter/manifest/QA record, hashes all current regular source files and
inherits effective archive traversal/link/duplicate/no-overwrite/partial-cleanup defenses.

However, the public `_validate_manifest()` / `read_archive_manifest()` boundary is not fully
type-strict. It accepts invalid types for the counts object, Git commit, authority hashes and file
kind while presenting the result as a validated schema. The later full `verify_archive()` semantic
replay rejects these particular mutations by comparing them with exact expected metadata and
records, so QA did not demonstrate acceptance of a forged official bundle. Nevertheless, explicit
type-strict schema validation is a required gate and the parsing API does not meet it.

Bundle R1 must not advance to `READY_FOR_OWNER_COMMIT_DECISION`. Preserve this record and the R1
bytes append-only and implement a successor. No official archive was built from the dirty checkout.
No reviewed source was modified; no upload, commit, push, training, evaluation, network action or
sealed-test access occurred.

## Medium finding

### M-1-R1 — validated-manifest API accepts invalid metadata and record-field types

Severity: **Medium**.

Affected source: `scripts/build_m1_colab_bundle_wp38_r1_r1.py`, `_validate_manifest()` and the
`read_archive_manifest()` API that returns after calling it.

The validator strictly rejects the top-level key-set, policy values, Boolean-as-integer attacks on
`schema_version`, `file_count` and per-record `size`, unsafe paths, duplicate paths and invalid
split values. It does not validate the types or formats of several other declared schema fields.

Independent mutation of a genuine in-memory 5,927-file manifest produced:

| Mutation | `_validate_manifest()` result |
| --- | --- |
| `schema_version=True` | rejected |
| `file_count=True` | rejected |
| first record `size=True` | rejected |
| missing top-level key | rejected |
| extra top-level key | rejected |
| `allowed_splits=("train", "val")` | rejected |
| `counts=True` | **accepted** |
| `repo_git_commit=123` | **accepted** |
| `integration_manifest_sha256=123` | **accepted** |
| first record `kind=123` | **accepted** |

The same accepted mutations were rejected by `verify_archive()` when QA supplied exact expected
metadata/record authorities, confirming that the second semantic layer remains fail-closed. That
does not repair the schema boundary: `read_archive_manifest()` is a callable parser that returns
the accepted malformed object as validated, and future callers may legitimately rely on the
declared types before invoking full semantic replay.

Impact: the bundle cannot claim a type-strict manifest contract, and malformed metadata can cross
the parsing/shape-validation boundary. Current full verification prevents promotion of the tested
forgeries, so severity is Medium rather than High.

Required remediation:

1. Preserve R1 and this FAIL record; create an append-only R2 successor.
2. Require `repo_git_commit` to be the governed lowercase hexadecimal commit format.
3. Require every SHA-256 authority field to be a string of exactly 64 lowercase hexadecimal
   characters.
4. Require `counts` to have the exact governed key set and exact non-Boolean integer values.
5. Require each file-record `kind` to be a string in the exact governed kind vocabulary; retain
   exact semantic record comparison in `verify_archive()`.
6. Add direct `_validate_manifest()` and archive-parser mutation tests for all fields, including
   Boolean-as-integer, number/string/container substitutions, missing/extra nested keys and invalid
   digest alphabets.

## Independently verified roster and bindings

QA built the manifest only in memory; it did not invoke an official archive build. Every one of the
5,927 current sources was checked as a regular nonsymlink file with exact expected hash and size.

- exact unique file records: **5,927/5,927**;
- raw train images: **1,912**;
- raw validation images: **337**;
- corrected WP38-R1 validation images: **39**;
- corrected WP38-R1 validation labels: **39**;
- WP35 train images: **1,800**;
- WP35 train labels: **1,800**;
- corrected stems: exact `1319..1357`;
- source splits: exact set `{train, val}`;
- test image/label payload paths: **0**;
- R4 integration exporter hash: exact pin;
- R4 integration manifest hash: exact pin;
- R4 independent QA PASS-record hash: exact pin;
- `test_included=false`, `sealed_test_accessed=false`, `training_authorized=false` in the contract
  verifier result.

The sealed-test stem-list hash is retained only as governance metadata. QA did not enumerate or
open sealed-test image or label content.

## Archive and output attack evidence

All archive construction in QA used tiny local fixtures outside the repository. No official
5,927-file archive was produced.

| Attack/control | Result |
| --- | --- |
| `../` traversal member | rejected |
| absolute-path member | rejected |
| backslash path | rejected |
| duplicate tar member | rejected |
| symlink tar member | rejected |
| hardlink tar member | rejected |
| duplicate JSON key in embedded manifest | rejected |
| archive path that is itself a symlink | rejected |
| Existing archive/sidecar/partial/sidecar-partial, regular-file forms | **4/4 rejected** |
| Existing archive/sidecar/partial/sidecar-partial, symlink forms | **4/4 rejected** |
| Injected payload-write failure | partial archive and sidecar artifacts fully removed |
| Two equivalent tiny local builds | byte-identical gzip/tar archives |
| Tiny archive member types/metadata | regular-only, mode 0644, mtime/uid/gid 0, empty owner names |
| Dirty authoritative checkout | rejected before archive or sidecar creation |

The fixture builder was isolated from the official roster and used only to exercise inherited
archive mechanics. The clean-checkout guard remained active and was independently exercised
against the authoritative dirty checkout.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Exact requested source/test/R4-QA hashes | PASS, **3/3** |
| Contract verifier | PASS mechanically, `valid=true`, **5,927 files** |
| Targeted bundle R1 tests | PASS, **5/5** |
| Full in-memory source hash/regular-file replay | PASS, **5,927/5,927** |
| Exact roster/count/split/R4 binding replay | PASS |
| Type-strict direct manifest mutation matrix | **FAIL, 4 malformed types accepted** |
| Full semantic verifier on those four mutations | PASS fail-closed, **4/4 rejected** |
| Archive unsafe-member attacks | PASS fail-closed, **8/8 rejected** |
| No-overwrite attacks | PASS fail-closed, **8/8 rejected** |
| Deterministic regular-file archive fixture | PASS |
| Partial-output cleanup fixture | PASS |
| Ruff for exact exporter and targeted test | PASS |
| Root lock | PASS, resolves **168 packages** |
| `git diff --check` | PASS |
| Sealed-test access log | absent before and after QA |

Graft was used before source review. The freshness-aware scoped query reported approximately
28,398 tokens saved (about USD 0.02).

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_colab_bundle_wp38_r1_r1.py` | `64cfa2d3f52db838f38e113d08c71c25418ce885e89b95322d9880263b7969d9` |
| `tests/test_m1_colab_bundle_wp38_r1_r1.py` | `575ca94c3555880c51b253a1a5a0244d2ca5a8b7a110c2f73afa26123b2d3e92` |
| Integration R4 independent QA PASS record | `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591` |
| `docs/review/m1_colab_wp38_r1_r4_bundle_r1_implementation_record.md` | `7b15055083fe83bf5fc10876baaffc2d2ec16957993cbca1c9e0291b9ec62577` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Exact 5,927-file roster and source bytes | **PASS** |
| R4 exporter/manifest/QA authority binding | **PASS** |
| Train/validation-only and no-test payload | **PASS** |
| Archive traversal/link/duplicate defenses | **PASS** |
| Deterministic regular-file archive mechanics | **PASS** |
| No-overwrite and partial cleanup | **PASS** |
| Clean-checkout gate | **PASS** |
| Type-strict schema boundary | **FAIL — M-1-R1** |
| Bundle R1 independent QA | **FAIL / NO-GO** |
| `READY_FOR_OWNER_COMMIT_DECISION` | **NOT REACHED** |
| Official archive build or external write | **NOT AUTHORIZED** |
| New model training or evaluation | **NOT AUTHORIZED** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: preserve bundle R1 and this QA record as immutable failure evidence. Implement
the type-strict manifest remediation as an append-only successor and route its exact bytes to a
fresh independent QA session before asking the Owner for a commit or archive/upload decision.
