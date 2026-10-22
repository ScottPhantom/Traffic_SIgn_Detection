# M1-WP38-R1 downstream integration R3 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_FAIL`

Reviewer: `Codex independent QA session (read-only source/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted R3 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_FIX_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL / NO-GO — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

R3 closes both findings reported against R2: completion-marker values and types are now strict,
and every descendant descriptor opened before an injected partial-tree failure is closed while
the original exception is preserved. The current materialisation is semantically exact,
train/validation-only and sealed-test closed.

However, verification still performs pathname checks followed by pathname reads without retaining
no-follow descriptors or binding the checked inode to the read bytes. Independent races replaced
the marker, root and parent after their checks and were accepted. An active parent replacement
during `materialise()` caused the writer to populate its detached original tree but return
`verified=true` for a different, pre-existing tree at the public output pathname. This violates
the artifact identity/new-output boundary and is a High blocker.

No official archive, corrected-validation evaluation, new training, Drive write, commit/push or
sealed-test access is authorized by this record.

## Finding

### H-1-R3 — Verification and final materialisation result are not bound to opened path identities

Severity: **High**

Affected source: `scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py`, principally
`verify_materialised()` and the inherited `materialise()` final-verification path.

#### Marker `lstat()` / `read_text()` race

The verifier first calls `marker_path.lstat()`, validates a single-link regular file, then calls
`marker_path.read_text()`. These operations are not bound to the same inode. Independent full
semantic replays swapped the marker in that exact window while retaining byte-identical valid
content:

| Attack after `lstat()` | Post-swap state | Result |
| --- | --- | --- |
| `os.replace()` with another single-link regular file | inode changed | `valid=true`, no errors |
| replace with symlink to external valid marker | final marker is symlink | `valid=true`, no errors |
| replace with hardlink to external valid marker | final marker has link count 2 | `valid=true`, no errors |

Thus the verifier can report success even though the object finally present violates the exact
regular/single-link property it claims to have checked.

#### Root and parent replacement after safety check

After `require_safe_existing_directory(out)` returned, QA atomically replaced either the complete
output root or its parent with a separate regular directory tree containing the same valid export.
Both full semantic replays returned `valid=true`; observed root inode before and after differed in
both cases. No descriptor pins the checked root/parent identity through marker and dataset reads.

#### Active writer parent swap returns the wrong tree as its product

QA also attacked the real R3 `materialise()` flow after `_open_new_root()` had opened the output
parent/root but before descendant creation:

1. The public parent was renamed, detaching the newly opened empty output tree.
2. A separate parent containing a pre-existing semantically valid R3 export was renamed into the
   public pathname.
3. Descriptor-relative writes correctly populated only the detached original tree.
4. The inherited root identity check passed relative to the retained old `parent_fd`.
5. Final path-based verification examined the replacement public tree and returned success.

Observed evidence:

- `materialise_verified=true`;
- reported `out` was the public replacement pathname;
- public output inode exactly matched the replacement inode captured before the swap;
- a completion marker existed in both the detached newly written tree and the replacement tree;
- the replacement-parent victim sentinel remained byte-identical, proving descriptor-relative
  writes did not mutate it;
- `sealed_test_accessed=false`.

The R2/R3 descriptor writer still prevents redirected victim writes, but `verified=true` is now
attached to a different object from the tree that the writer created. An attacker can therefore
substitute an already-valid but independently controlled/stale output and defeat exact artifact
identity and the new-output-only claim.

Required remediation:

1. Preserve R3 and this verdict append-only; implement a new successor.
2. Open the output parent, root and marker with no-follow descriptor-relative operations.
3. Read marker bytes from the exact opened marker descriptor, verify `fstat()` is a single-link
   regular file before and after reading, and reject identity/link changes.
4. Keep parent/root descriptors through the complete semantic replay. Read directories/files
   relative to those retained descriptors or bind every consumed inode to a descriptor-based
   inventory; do not fall back to the public pathname after the writer closes descriptors.
5. Before returning, verify that the public parent/root path still resolves to the same retained
   device/inode chain opened by the writer.
6. Add deterministic regular/symlink/hardlink marker swaps, root swaps, parent swaps and the active
   writer-parent replacement attack. Every attack must fail closed, preserve the original error,
   and never return `verified=true` for a different inode.

## Closure of R2 findings

### M-1-R2 strict completion-marker schema

**PASS / closed for static content attacks.** Both direct validation and full materialised replay
rejected all 13 required mutations:

- missing or extra top-level field;
- missing or extra `written` key;
- zero, negative, Boolean, float and string counts;
- wrong package or status;
- `test_included=true` or `sealed_test_accessed=true`.

The authentic marker requires exact keys and exact integer values
`train=1912`, `train_wp35=1800`, `val=376`. Authentic full semantic verification returns
`valid=true`. The remaining race is H-1-R3 above, not a static-schema bypass.

### L-1-R2 descriptor cleanup

**PASS / closed.** QA injected failure before each of the six descendant directory opens. For all
positions 1 through 6:

- every descriptor returned by an earlier successful open was closed;
- `/dev/fd` returned to its pre-call set;
- the root descriptor remained caller-owned;
- the exact injected `RuntimeError` and message were re-raised without masking;
- QA observed no double-close.

## Writable-path regression excluding the new parent-identity finding

R3 inherits the exact R2 descriptor-relative write defense. Independent regression confirmed:

- root pathname replacement with `output -> victim` left the victim unchanged, wrote only into
  the detached original inode and was rejected by the retained root identity check;
- replacing an opened child split directory with a victim symlink left the victim unchanged and
  wrote only into the detached child inode;
- existing symlink and hardlinked label leaves were rejected by exclusive/no-follow creation and
  their targets remained byte-identical.

These tests confirm no redirected mutation. They do not close H-1-R3 because parent replacement
can still make final verification/reporting refer to a different public tree.

## Dataset Graph and materialised candidate

- Current graph authorities authenticate 3,215 governed rows, 54 groups, zero cross-split groups,
  and exactly 39 corrected frames.
- Split counts remain 1,912 train, 376 validation, 903 sealed test and 24 governed quarantine rows,
  plus raw stem `0248` shown separately as quarantined (25 raw quarantined frames total).
- Sealed-test stem-list SHA-256 remains
  `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.
- Materialised train contains 3,712 image symlinks and 3,712 regular labels: 1,912 real plus 1,800
  WP35 train-only pairs.
- Materialised validation contains 376 image symlinks and 376 regular labels.
- Corrected validation is exactly stems `1319..1357` (39), every link targets the governed
  WP38-R1 derivative, and corrected/train overlap is zero.
- `images/test` and `labels/test` are absent.
- Commands remain only `manifest`, `verify`, `export`, `verify-export`; there is no `export-test`
  or `--final-eval` path.
- `results/experiments/sealed_test_access_log.jsonl` remained absent before and after QA.

QA did not enumerate or open sealed-test image/label content.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Exact requested R3 hashes | PASS, 3/3 plus remediation/R2 FAIL record readback |
| R3 integration verifier | PASS, `valid=true` |
| R3 + graph targeted tests | PASS, **15/15** |
| Authentic materialised full semantic replay | PASS, `valid=true` |
| Static marker mutation matrix | PASS, **13/13 rejected** in full-output replay |
| Descriptor failure positions | PASS, **6/6**, no leak or masking |
| Root/child redirected-write attacks | PASS, victim unchanged |
| Symlink/hardlink output-leaf attacks | PASS, rejected and victim unchanged |
| Marker regular/symlink/hardlink race | **FAIL — 3/3 accepted** |
| Verifier root/parent regular-directory race | **FAIL — 2/2 accepted** |
| Active writer parent replacement | **FAIL — returned verified replacement tree** |
| Exact train/validation/correction/no-test roster | PASS |
| Dataset Graph authority | PASS, 54 groups, 0 leakage groups, 39 corrected |
| Repository verifier matrix | PASS, **58/58** |
| Ruff, full `src tests` scope | PASS |
| Root `uv lock --check` | PASS, 168 packages |
| `git diff --check` | PASS |
| Graft | PASS, synchronized at 3,422/3,422 wiring nodes |
| Sealed-test access log | ABSENT before and after QA |

Graft was used before source audit. `graft ask` supplied the R3 flow map and reported about 17,819
tokens saved (approximately USD 0.01); final `graft check .` remained synchronized.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py` | `729277d443fffd4fa21d3a793f7f5b0b18744bf703cf9ecf9088a0c6bcfb5226` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r3_manifest.json` | `734b082d49e607de97e61a8a7db7203993fe7645b552be8c99e5cc2aed31be9e` |
| `tests/test_m1_wp38_r1_integration_r3.py` | `ca813cad25cf8a79726b3d37edd80c9a479e708b0500620baab89d478ce8085b` |
| `docs/review/m1_wp38_r1_integration_r3_qa_remediation_report.md` | `1ddfc4aabb721c462d2e867b5cc2283cb415fef0b311ee8b62890c1f4d29fd2a` |
| R2 independent QA `FAIL` record | `b37c7bf34e6160b496dd28cd56993e7a786689ac7733968513aac09c0464f7eb` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Static completion-marker authority M-1-R2 | **PASS / closed** |
| Descriptor lifecycle L-1-R2 | **PASS / closed** |
| Exact 39-stem validation substitution | **PASS** |
| Train/WP36 membership preservation | **PASS** |
| Dataset Graph authority | **PASS** |
| Sealed-test hash and closed boundary | **PASS** |
| Descriptor-relative redirected-write defense | **PASS** |
| Marker/root/parent identity across check/use | **FAIL — H-1-R3** |
| R3 integration acceptance | **FAIL / NO-GO** |
| Official archive/Drive upload | **NO-GO** |
| Corrected-validation evaluation | **NO-GO pending successor + fresh QA** |
| New 100-epoch training | **NO-GO** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: preserve the initial, R1, R2 and R3 bytes plus their independent FAIL records.
Create an append-only successor that binds marker reads and the complete semantic replay to retained
no-follow parent/root/file descriptors, then route its exact bytes and materialised output to fresh
independent QA. Only a QA PASS permits clean-commit/archive work and a separate Owner-authorized
corrected-validation evaluation; it still does not authorize new training or sealed-test access.
