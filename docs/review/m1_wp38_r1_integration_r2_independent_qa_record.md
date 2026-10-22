# M1-WP38-R1 downstream integration R2 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `INDEPENDENT_QA_FAIL`

Reviewer: `Codex independent QA session (read-only source/artifact review)`

Reviewed checkout: committed base `85a8025e1ae1e78d4c84adb2cd6009003e8c93a1` plus the exact
uncommitted R2 bytes pinned below and unrelated user/PM worktree changes.

Boundary: `READ_ONLY_NO_SOURCE_FIX_NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL / NO-GO — 0 Critical, 0 High, 1 Medium and 1 Low findings.**

R2 closes the R1 High writable-path race: after the output root is opened, root-path, child-path,
symlink-leaf and hardlink-leaf attacks cannot redirect writes into an attacker-controlled victim.
The current materialisation is also semantically exact, train/validation-only and sealed-test
closed. However, the completion marker verifier accepts markers whose declared write counts are
missing or false, contrary to the marker's role as mandatory completion evidence. A separate
exception path leaks a child directory descriptor when tree creation fails part-way through.
These defects require an append-only successor and fresh QA.

No official archive, corrected-validation evaluation, new training, Drive write, commit/push or
sealed-test access is authorized by this record.

## Findings

### M-1-R2 — Completion marker schema accepts absent or false write evidence

Severity: **Medium**

Affected source: `scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py`, principally
`verify_materialised()`.

`materialise()` writes `EXPORT_COMPLETE.json` last with a `written` object containing the exact
`train`, `val` and `train_wp35` counts. The verifier requires a single-link regular marker and
checks `package`, `status`, `test_included` and `sealed_test_accessed`, but it never validates the
`written` object or rejects unrecognized/missing fields.

Independent reproduction used a complete copy of the real R2 materialisation and adjusted only
its `data.yaml` root so that the full downstream semantic verifier still examined the copied
tree. Each of the following marker mutations returned `valid=true`, `errors=[]`:

- `written={"train":0,"val":0,"train_wp35":0}`;
- deletion of `written` entirely;
- insertion of an unrecognized `qa_unrecognized=true` field.

Missing marker, partial JSON, symlink marker and hardlinked marker cases do fail closed. A partial
data tree also remains rejected by the downstream semantic verifier. Therefore this issue does
not make missing images or labels valid; it makes the mandatory completion evidence internally
untrustworthy and prevents exact provenance/readback of what the completed writer claims it
wrote.

Required remediation:

1. Preserve R2 and this verdict append-only; implement a new successor.
2. Define the marker's exact schema and require exact key equality.
3. Require `written == {"train": 1912, "val": 376, "train_wp35": 1800}` with integer values,
   then independently match these counts to the verified output roster.
4. Add attacks for missing, extra, wrong-type, negative and false count fields while retaining the
   existing absent/partial/symlink/hardlink cases.

### L-1-R2 — Partial child-directory creation leaks an open descriptor

Severity: **Low**

Affected source: `scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py`, `_safe_tree_fd()`.

The function creates child descriptors inside a dictionary literal. If a later `_mkdir_open()`
raises, the exception handler closes only `images` and `labels`; descriptors already returned for
earlier split directories are no longer reachable by the caller and remain open. An injected
failure on the fourth create produced:

```text
raised=RuntimeError:QA_INJECTED_CHILD_CREATE_FAILURE
images=CLOSED labels=CLOSED train=OPEN_LEAK
```

QA closed the leaked descriptor after observation. In the CLI process this is normally reclaimed
at process exit, so no victim mutation or data-integrity failure was observed. It is nevertheless
incorrect resource ownership for a callable implementation and can accumulate descriptors in a
long-lived process or repeated failure loop.

Required remediation: accumulate every successfully opened descriptor in an owned collection and
close that collection in reverse order on every exception; add injected-failure coverage at each
directory-create/open boundary and assert no leaked or double-closed descriptors.

## Closure of R1 H-1-R1

**PASS / closed for the writable materialisation path.** Independent attacks confirmed:

- after opening the output, renaming the root and replacing its pathname with `output -> victim`
  left the victim sentinel unchanged; new directories, a regular label and a symlink were created
  only in the detached original inode, and `_require_root_identity()` rejected the replacement;
- replacing the old root pathname with a new regular directory also left that replacement
  unchanged while descriptor-relative writes stayed in the detached original;
- after opening `labels/train`, renaming that directory and replacing its pathname with a victim
  symlink could not redirect a write; the byte landed in the detached child inode;
- existing symlink and hardlinked output leaves were rejected by exclusive/no-follow creation and
  their victims remained byte-identical;
- parent/root identity is checked at open, all descendant writes use retained `dir_fd` handles,
  and a late root identity mismatch fails closed;
- an interrupted output without the last marker is rejected and never reused because export
  requires a nonexistent destination.

No descriptor-relative attack mutated a victim. R2 also performs no recursive cleanup through a
potentially replaced pathname, eliminating the cleanup escape that accompanied R1 H-1-R1.

## Dataset Graph authority M-1 reconfirmation

**PASS / remains closed.** The authenticated wrapper is byte-identical to the R1-reviewed source.
Current authorities reproduce 3,215 governed rows with `1912/376/903/24` split/quarantine counts,
plus raw stem `0248` displayed separately as quarantined (25 quarantined raw frames in total), 54
groups, zero cross-split groups, exactly 39 corrected frames, and sealed-test stem-list hash
`afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.

Targeted tests reject forged WP38 stem evidence, WP36 split movement, duplicate WP36 rows and a
wrong D02 group. R1's independent coherent-repin matrix already exercised forged WP38 split,
duplicate/missing/extra/schema-invalid WP36 rows and wrong group/split after refreshing temporary
hash pins; all eight semantic attacks were rejected. Because the wrapper and its pinned authority
bytes are unchanged and current authentication/tests reproduce, that closure carries into R2.

The live authority contract reports `sealed_test_accessed=false`; QA did not enumerate or open any
sealed-test image/label content.

## Materialised candidate and sealed boundary

- `verify-export` returned `valid=true` for
  `data/processed/m1_yolo_wp38_r1_integration_r2/` with its unmodified marker.
- Train: 3,712 image symlinks and 3,712 regular labels = 1,912 governed real images plus 1,800
  WP35 pairs.
- Validation: 376 image symlinks and 376 regular labels.
- Corrected validation roster is exactly stems `1319..1357` (39), every corrected link targets the
  governed WP38-R1 derivative, and corrected/train overlap is zero.
- R1 and R2 materialised train and validation image/label snapshots are byte/link-target identical;
  the R2 integration does not alter train membership or content.
- `images/test` and `labels/test` are absent.
- R2 exposes only `manifest`, `verify`, `export` and `verify-export`; there is no `export-test` or
  `--final-eval` path.
- `results/experiments/sealed_test_access_log.jsonl` remained absent before and after QA.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Exact requested R2 source hashes | PASS, 4/4 exact plus remediation report readback |
| R2 integration verifier | PASS, `valid=true` |
| R2 + graph targeted tests | PASS, **11/11** |
| Materialised export verifier with authentic marker | PASS, `valid=true` |
| Exact corrected/train/validation/no-test roster replay | PASS |
| Root pathname swap to victim symlink/new directory | PASS, anchored writes and victim unchanged |
| Open child-directory pathname replacement | PASS, anchored write and victim unchanged |
| Symlink/hardlink leaf attacks | PASS, rejected without victim mutation |
| Missing/partial/symlink/hardlink completion marker | PASS, rejected |
| False/missing/extra marker fields | **FAIL — accepted as valid** |
| Injected partial tree-create failure | **FAIL — one child descriptor leaked** |
| Dataset Graph authority/current payload | PASS, 54 groups, 0 leakage groups, 39 corrected |
| Repository verifier matrix | PASS, **57/57** |
| Ruff, full `src tests` scope | PASS |
| Root `uv lock --check` | PASS, 168 packages |
| `git diff --check` | PASS |
| Graft | PASS, graph synchronized at 3,396/3,396 wiring nodes |
| Sealed-test access log | ABSENT before and after QA |

Graft was used before source audit. `graft ask` provided the initial flow map and reported about
20,851 tokens saved (approximately USD 0.01); the final `graft check .` remained synchronized.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py` | `a26f1ee3a778086cef35fcd56df7df508dbdaee58d23ba34decba49de264ae4c` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r2_manifest.json` | `7538697ba4fcdf59d86f62b7ce867ee0c609042a1d25922d2ff959607bc6f9de` |
| `tests/test_m1_wp38_r1_integration_r2.py` | `77064cae59d61b3ce80735a6d9f04c7bd95cb8b3b76f06a525e452cc38087748` |
| `src/cpv301_autodrive/dataset01_view_r1.py` | `6763c8d7fd22004773bbac84067f39d0b85c88df5c049759de9250bf433431dc` |
| `tests/test_dataset01_view_r1.py` | `b8f32ae5bf6dce31c37af64ce4552bc32d0022106022a793757da1020964bff4` |
| `docs/review/m1_wp38_r1_integration_r2_qa_remediation_report.md` | `8d76404bfb35c06b98bdde5558f98be5cb7bc7c099ddd9a5bd03b18ed9450654` |
| R1 independent QA `FAIL` record | `245ceb491886a79c121595f65b751f85fbc3a18f4d26461f0afeedc14cfc0b8d` |

## Governance disposition

| Gate | QA disposition |
| --- | --- |
| Exact 39-stem validation substitution | **PASS** |
| Train/WP36 membership preservation | **PASS** |
| Sealed-test hash and closed boundary | **PASS** |
| Materialised train/val-only export | **PASS** |
| Dataset Graph authority M-1 | **PASS / remains closed** |
| R1 writable-path TOCTOU H-1-R1 | **PASS / closed in R2** |
| Completion marker authority | **FAIL — M-1-R2** |
| Descriptor lifecycle | **FAIL — L-1-R2** |
| R2 integration acceptance | **FAIL / NO-GO** |
| Official archive/Drive upload | **NO-GO** |
| Corrected-validation evaluation | **NO-GO pending successor + fresh QA** |
| New 100-epoch training | **NO-GO** |
| Sealed-test access | **NO-GO / not accessed** |

Final disposition: preserve the initial, R1 and R2 bytes plus their independent FAIL records.
Create an append-only successor with strict completion-marker validation and exception-safe
descriptor ownership, then route its exact bytes and materialised output to fresh independent QA.
Only a QA PASS permits clean-commit/archive work and a separate Owner-authorized
corrected-validation evaluation; it still does not authorize new training or sealed-test access.
