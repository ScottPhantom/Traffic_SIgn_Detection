# M0-WP38-R1 orientation-correction independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_PASS`

Reviewer: `Codex independent QA session (read-only implementation/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted WP38-R1 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_OR_ARTIFACT_FIX_NO_TRAINING_NO_EXPORT_NO_EVALUATION_NO_SEALED_TEST_NO_COMMIT_NO_PUSH`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

WP38-R1 closes predecessor H-1. Before any derived output is written, the builder independently
binds all 39 source images to the pinned WP1 inventory and reconstructs all 39 materialized label
files byte-for-byte from the pinned WP33 boxes and taxonomy/class-index rule. The two attacks that
the initial WP38 verifier accepted now fail closed before an output tree is created.

The final package independently reproduces the exact 39-frame counter-clockwise correction,
29 transformed boxes and exact 87-artifact roster. Its previews are upright and the boxes align.
No repository implementation or prior record was modified during QA. No model training, upload,
commit, push, export, evaluation or sealed-test access occurred.

This PASS accepts only the WP38-R1 correction package at its declared evidence boundary. It does
not authorize training or sealed-test access, does not change the WP36-R1 split, and does not by
itself authorize an evaluator/exporter to consume the corrected frames. That requires the
separately governed successor integration described by the manifest's `authorization_note`.

## Closure of predecessor H-1

The initial WP38 QA record remains immutable and remains a FAIL for that predecessor package.
WP38-R1 is an append-only successor with these independently reproduced controls:

1. The raw source must be the canonical repository raw root. Lexically noncanonical roots are
   rejected.
2. Every component of the repository, raw, image, label and pinned-authority paths is checked with
   `lstat()` and may not be a symlink. Each source must be a regular file.
3. The pinned WP1 inventory governs exact relative path, dimensions and SHA-256 for every source
   image stem `1319..1357`.
4. Expected validation-label bytes are regenerated from the pinned WP33 rows and governed taxonomy
   mapping, not trusted from the current materialized label file.
5. Read-only source authorities may have multiple hardlinks because exact pinned bytes, a regular
   file type and symlink-free ancestry define their trust. An independent clean-room replay with
   inventory `st_nlink=2` passed only while the hash remained exact.
6. Writable outputs remain stricter: output files must be regular, nonsymlink paths with
   `st_nlink==1`; output symlink and hardlink attacks are rejected.

## Independent source-authority and transform replay

The current package and its governing sources were recalculated independently of the builder's
reported result:

- exact stem roster `1319..1357`: **39/39**;
- exact group/split: `D02-C0034`, validation only, **39/39**;
- WP1 authority path, byte hash and 540x960 dimensions: **39/39**;
- materialized labels equal independently reconstructed WP33/taxonomy bytes: **39/39**;
- UNKNOWN-only empty labels: exact stems `1319..1328`, **10/10**;
- labeled stems `1329..1357`: exactly **29** boxes with class-ID set `{12, 14}`;
- decoded output pixels equal `source.transpose(ROTATE_90)`: **39/39**;
- output dimensions: 960x540, **39/39**;
- normalized transform `x'=y`, `y'=1-x`, `w'=h`, `h'=w`: **29/29**;
- canonical raw hashes before and after replay: unchanged;
- manifest roster: exact **87** non-self artifacts = 39 PNG + 39 labels + 8 preview pages
  + 1 lineage ledger;
- actual roster, every listed byte size and SHA-256, builder binding and predecessor/source pins:
  exact match.

## Fail-closed attack evidence

All source attacks used clean-room copies and verified that no package root, preview directory,
lineage ledger or manifest had been created after rejection:

| Attack | Independent result |
| --- | --- |
| Replace stem `1319` with a modified but valid 540x960 JPEG | **REJECTED BEFORE OUTPUT** by pinned image authority hash |
| Change stem `1329` normalized label x-coordinate by `+0.001` | **REJECTED BEFORE OUTPUT** by WP33-derived byte authority |
| Supply a noncanonical raw root | **REJECTED** |
| Put a symlink in the canonical-looking raw-root ancestry | **REJECTED** |
| Give the exact pinned inventory a second read-only hardlink | **ACCEPTED AS INTENDED**, with exact hash and symlink-free regular path |
| Modify a generated output | **REJECTED** |
| Remove a generated output | **REJECTED** |
| Add an extra generated output | **REJECTED** |
| Replace output with a symlink or hardlink | **REJECTED** |
| Leave a partial output tree | **REJECTED** |
| Put a symlink in output ancestry | **REJECTED** |

The read-only input-hardlink case is not a weakening of byte authority: changing the content would
change the pinned SHA-256 and fail. It prevents concurrent clean-room readers from invalidating an
otherwise exact authority, while the output namespace remains single-link and fail-closed.

## Visual QA

All eight final R1 preview pages were inspected at original detail:

- pages 01–07: five panels each;
- page 08: four panels;
- total coverage: **8/8 pages, 39/39 panels**.

Every scene is upright after `CCW_90`. The class-14 boxes on stems `1329..1331` and class-12 boxes
on stems `1332..1357` align with their visible traffic signs. Stems `1319..1328` correctly have no
derived detector box because their WP33 rows are routed to UNKNOWN evaluation.

## Mechanical evidence

| Check | Result |
| --- | --- |
| WP38-R1 targeted suite, final bytes | PASS, **7/7** |
| WP38 + WP38-R1 parallel xdist regression | PASS, **14/14** |
| Official WP38-R1 verifier | PASS, `valid=true`, 39 frames, 29 boxes |
| Repository verifier matrix | PASS, **54/54** |
| Independent authority/pixel/geometry/roster replay | PASS |
| Visual review | PASS, **8/8 pages, 39/39 panels** |
| Ruff for builder, test and verifier registration | PASS |
| Root lock | PASS, resolves **168 packages** |
| `git diff --check` | PASS |
| Graft | PASS, wiring graph synchronized |
| Sealed-test access log | absent before and after QA |

A broader unrelated full root test run completed the serialized repo-writing segment at **126/126**
and reached 29% of its parallel segment without a failure before it was intentionally stopped to
keep this review proportional. It is not represented as a completed full-suite PASS. The focused
xdist regression covering both WP38 generations completed separately at 14/14.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `scripts/build_wp38_r1_orientation_correction.py` | `f54ca45ba46269f2ebbf459a856de307cd77403aaefb5503ce58485b086da2e0` |
| `tests/test_wp38_r1_orientation_correction.py` | `15eb8b171d6ceb21d9f519e1bbf801534984792df14932393d118618c15e2265` |
| `scripts/run_parallel_checks.py` | `ed828c11c1c9f5f2bfb2463df922cfe050a3344e5326911963868597d39b836d` |
| `docs/review/generated/wp38_r1_orientation_correction_manifest.json` | `d88f5eae525a4aa6d77cdf3f581b60328a441aec0ff091cd907af20e8405385a` |
| `docs/review/generated/wp38_r1_orientation_correction_lineage.csv` | `459fbb8990713b2d63b112ac4561f8509c2dfa07a295bf711fe1bad98ed7304d` |
| `docs/review/wp38_r1_orientation_correction_qa_remediation_report.md` | `c29cfb5b15d585cd8b9b1254d9e08f918515158c5648e9bbf510e67fa7b7b788` |

The preserved predecessor anchors were also rechecked: initial WP38 builder
`c3b2726241b53be23a9e1b233d38b5dad3994d2f6fc073beabef82f6bd89c23e`, manifest
`a59fd9f59236e990be722e09063a52065e1ed0a0dcb0d7f03fa4baf52d82313e` and lineage
`1d7340d5c222925751a45c30d58b4a2ebc04715457d048842036be5414c6e659` remain unchanged.

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Exact source/provenance fail-closed verification | **PASS** |
| Pixel and box correction | **PASS** |
| Preview orientation and alignment | **PASS** |
| WP38-R1 independent QA | **PASS** |
| WP38 predecessor | **FAIL remains preserved** |
| Split membership | **UNCHANGED: validation only** |
| Training authorization | **NO-GO / `false`** |
| Sealed-test access | **NO-GO / not accessed** |
| Evaluator/exporter consumption | **NOT AUTHORIZED BY THIS RECORD** |

Final disposition: WP38-R1 passes independent QA as the governed orientation-correction evidence
package. Preserve the original WP38 FAIL and all R1 evidence append-only. Any downstream use must
be introduced by a separately reviewed integration that preserves the validation-only boundary and
does not change training or sealed-test authorization.
