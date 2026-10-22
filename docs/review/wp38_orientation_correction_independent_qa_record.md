# M0-WP38 orientation-correction independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_FAIL`

Reviewer: `Codex independent QA session (read-only implementation/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the current
uncommitted WP38 package and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_OR_ARTIFACT_FIX_NO_TRAINING_NO_SEALED_TEST_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

The current shipped artifact bytes independently reproduce the intended 39-frame counter-clockwise
orientation correction, but the verifier does not anchor the source JPEG bytes or materialized
validation-label bytes to an independent predecessor trust root. A coherently rebuilt package from
a modified source image or modified source label still returns `valid=true`. This violates the
declared exact-source/raw-immutability contract and is a release blocker.

WP38 must remain `WP38_AWAITING_INDEPENDENT_QA`. This verdict does not authorize use of the
derived images or labels by evaluation/export, does not change the WP36-R1 split, does not
authorize training and does not authorize sealed-test access.

No repository implementation or existing artifact was modified during QA. No model training,
upload, commit, push or sealed-test access occurred.

## High finding

### H-1 — source-image and source-label hashes are self-recorded, not independently pinned

Severity: **High**.

`render()` reads each current raw JPEG and materialized `m1_yolo/labels/val` file, records their
current hashes in lineage, derives a new source-binding digest and then constructs the expected
manifest from those same current bytes. `verify()` calls `render()` again and compares package
outputs with that freshly generated expectation. None of the six `PINNED_SOURCES` contains or is
used as an exact per-stem image-byte/hash authority, and the pinned WP33 table is not replayed to
derive the exact expected materialized validation-label bytes.

Consequently, before/after equality in `build()` proves only that raw bytes did not change during
that invocation. It does not prove that the invocation started from the governed raw bytes.

Independent clean-room attacks, using all six exact pinned predecessor files and the exact current
builder, reproduced both acceptance failures:

1. One decoded pixel in source JPEG stem `1319` was changed and the image was saved as a valid
   540x960 JPEG. `build()` and its post-build `verify()` returned `valid=true`:
   `TAMPERED_RAW_IMAGE_ACCEPTED=true stem=1319`.
2. The normalized `x` coordinate in source label stem `1329` was changed by `0.001`, retaining a
   valid in-bounds class-14 box and the same total box/class counts. `build()` and its post-build
   `verify()` returned `valid=true`:
   `TAMPERED_SOURCE_LABEL_ACCEPTED=true stem=1329`.

Both attacks changed the resulting lineage/source-binding and derived artifacts coherently, so the
package's self-consistency checks could not distinguish them from the governed inputs.

Impact: an altered raw frame or label can be promoted as an exact WP38 correction while
`raw_mutated=false`, exact-source lineage and predecessor binding appear valid. The current artifact
happens to match the independently checked inventory and labels, but the verifier cannot preserve
that fact after release.

Required remediation:

1. Add an independently pinned per-image authority, such as the canonical WP1 image inventory and
   its governing manifest/attestation, and compare every stem `1319..1357` current JPEG SHA-256,
   relative path and dimensions against that authority before deriving any output.
2. Derive the exact expected validation-label bytes for all 39 stems from the pinned WP33 table
   and governed export rules, or bind them to an equivalent independently pinned per-file label
   roster. Compare current label bytes/hashes against that expectation before rotation. For this
   group the rule must preserve ten empty UNKNOWN-eval labels (`1319..1328`) and the exact 29
   class-12/class-14 boxes on `1329..1357`.
3. Reject symlink ancestors for the canonical raw and materialized-label source paths and reject a
   non-canonical `--raw-root`; final-component symlink/hardlink checks alone are not an independent
   source-root binding.
4. Add regression attacks matching the two reproductions above. They must fail before any derived
   artifact is written and must not allow a coherent manifest/lineage refresh to restore validity.
5. Produce an append-only R1 package and submit it to a new independent QA session. Do not edit or
   overwrite this initial QA-FAIL record.

## Independently reproduced current-artifact evidence

The finding is a verifier/trust-root defect, not an allegation that the currently generated pixels
or boxes are wrong. Independent readback of the present artifact produced:

- exact stems `1319..1357`: **39/39**;
- group/split: exact `D02-C0034`, validation only, **39/39**;
- source dimensions 540x960 and derived dimensions 960x540: **39/39**;
- decoded derived pixels equal `source.transpose(ROTATE_90)`: **39/39**;
- normalized box transform `x'=y`, `y'=1-x`, `w'=h`, `h'=w`: **29/29**;
- derived boxes/classes: **29**, exact class-ID set `{12, 14}`;
- source-image SHA-256 equals both lineage and the canonical image inventory: **39/39**;
- derived image/label SHA-256 equals lineage: **78/78**;
- manifest artifact roster: exact **87** entries = 39 PNG + 39 label + 8 preview + 1 lineage;
- every listed artifact size/hash and actual roster: exact match;
- builder hash in the manifest equals current builder SHA-256;
- raw image aggregate before/after the read-only replay: unchanged.

## Visual QA

All eight preview pages were inspected at original detail, covering every panel exactly once:

- pages 01–07: five panels each;
- page 08: four panels;
- total: **39/39 panels**.

Every scene is upright after `CCW_90`. All visible class-14 truck-restriction boxes on stems
`1329..1331` and class-12 lane/vehicle-sign boxes on stems `1332..1357` align with the intended
signs. Stems `1319..1328` correctly display no derived boxes because their WP33 rows are routed to
UNKNOWN evaluation rather than the 54-class detector labels.

## Mechanical evidence

| Check | Result |
| --- | --- |
| WP38 targeted tests | PASS, **7/7** |
| Official WP38 verifier | PASS mechanically, `valid=true`, 39 frames, 29 boxes |
| Independent pixel/geometry/hash replay | PASS for current bytes, **39/39** |
| Visual review | PASS for current previews, **8/8 pages, 39/39 panels** |
| Raw/current inventory comparison | PASS, **39/39** |
| Artifact roster/hashes | PASS, **87/87** |
| Changed-source image attack | **FAIL-CLOSED GATE FAILED**; tampered source accepted |
| Changed-source label attack | **FAIL-CLOSED GATE FAILED**; tampered source accepted |
| Ruff for WP38/registration sources | PASS |
| Root lock | PASS, resolves **168 packages** |
| `git diff --check` | PASS |
| Graft | PASS, wiring graph synchronized |
| Sealed-test access log | absent before/after QA |

The repository-wide verifier matrix and unrelated full test suite were not run after the confirmed
High blocker, following the required stop-on-failure boundary. Their outcome could not repair the
source trust defect.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `scripts/build_wp38_orientation_correction.py` | `c3b2726241b53be23a9e1b233d38b5dad3994d2f6fc073beabef82f6bd89c23e` |
| `tests/test_wp38_orientation_correction.py` | `9bade3517487250065ccf1604f943acf3b96a05e0f1a8b10ea1316d0261cabe5` |
| `scripts/run_parallel_checks.py` | `810b4c02cb20c4bb8fce2473b7e37278bb22e553b5b50fd5f6235b4272a86768` |
| `docs/review/generated/wp38_orientation_correction_manifest.json` | `a59fd9f59236e990be722e09063a52065e1ed0a0dcb0d7f03fa4baf52d82313e` |
| `docs/review/generated/wp38_orientation_correction_lineage.csv` | `1d7340d5c222925751a45c30d58b4a2ebc04715457d048842036be5414c6e659` |
| `docs/review/wp38_orientation_correction_implementation_record.md` | `feace96da3143909dbbbcfa4dc88c00b87a619fb75bdf2eda0f90b6de3bad018` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| Current artifact pixel/box correctness | **PASS for current bytes** |
| Current preview orientation/alignment | **PASS** |
| Exact source/provenance fail-closed verification | **FAIL (H-1)** |
| WP38 independent QA | **FAIL** |
| Use in evaluation/export | **NO-GO** |
| Split change or training authorization | **NO-GO / unchanged false** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: preserve the current initial WP38 package and this QA record as immutable
failure evidence. Implement the remediation only as an append-only R1 successor and route it to a
new independent QA session.
