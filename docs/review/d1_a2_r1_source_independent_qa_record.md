# D1-A2-R1 source independent QA record

Status: `QA_PASS_LIMITED_PRE_SMOKE_CONDITIONS`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent side session. The reviewer did not write the reviewed
files.
Boundary: read-only source QA. The reviewer did not edit any reviewed file, train, start Colab,
upload, run inference, change D-05 or any threshold, commit, stash, reset or push. The sealed test
(`afa03d4b…`) was not opened. `sealed_test_accessed=false`. `training_authorized=false`.

Verdict: PASS giới hạn — no source defect blocks an L4 smoke; two pre-smoke process conditions (C1, C2) must be met first.

**May an L4 smoke proceed once the Owner authorizes it?** Yes, on these terms:

- the QA-passed package is committed;
- **C1** and **C2** below are met;
- a separate Owner authorization record exists (contract §6).

Long training (the resume to epoch 100) still needs smoke QA, and it is covered only by the Owner's
authorization. This record authorizes nothing.

## 1. Starting state

| Item | Observed |
| --- | --- |
| Checkout | `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1` |
| `git log --oneline -3` | `7a95591` fusion R1 NO_GO; `17db663` fusion contract; `399bf70` paired A3−pilot CIs |
| `git status --short` | the 13 Owner-modified tracked files (`PROJECT_MEMORY.md`, `docs/product_roadmap.md`, …, `tests/test_wp35_rare_class_enrichment.py`). Many untracked files, including the 7 reviewed files. None was modified by this QA. |
| `graft check .` | `graph check: OK — the wiring graph is in sync with the code` (deep layer not built) |

## 2. SHA-256 verification

### 2.1 Reviewed files (all match the brief)

| File | SHA-256 | Match |
| --- | --- | --- |
| `docs/review/d1_a2_r1_run_contract.md` | `1ce153656f2c6c7a7700bdbf57f4d9c1205184ef07bf18a0fd912056e2f396e1` | yes |
| `detector/m1/a2_repeat_list_r1.py` | `28fc4cedb438859f2edd6215a97eb00cb36f385344e19731155e1da971712619` | yes |
| `detector/m1/resumable_train_a2_r1.py` | `c3823eefb9777912fc76302a642427a64869c9097274fc4d5841966c07d42ace` | yes |
| `detector/colab/run_d1_colab_a2_r1.py` | `a6bb6e684701b5a95bd03b71bac777693ec08f1ccb853c98edb2cefdcec2d6de` | yes |
| `detector/tests/test_a2_repeat_list_r1.py` | `1213bfd854dc979bbde6401df51a666194ae224e2b22fbf16c91c88f64a1e248` | yes |
| `detector/tests/test_resumable_train_a2_r1.py` | `baee841bb99d4581cecf9601622fd86dd52f7947f6b4ddba65da3e434a4970dd` | yes |
| `detector/tests/test_run_d1_colab_a2_r1.py` | `6a5745e1eed306d8968dbfe584710916fde871f9fb2bfedaabeb458c22eb0997` | yes |

### 2.2 Locally built artifacts named by the contract (Git-ignored)

| File | SHA-256 | Note |
| --- | --- | --- |
| `data/processed/d1_a2_r1/a2_train_list.txt` | `90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2` | 4,687 lines; matches contract §2.1 |
| `data/processed/d1_a2_r1/a2_train_list_manifest.json` | `12f09435a923cfe9e11c6c62f63d1c9906e9840d75ed2908df755bc30b110cbd` | matches §2.1 |
| `data/processed/d1_a2_r1/runtime/` | absent | consistent with contract §11 ("no runtime YAML written locally"); running the tests did not create it |

### 2.3 Binding spec and predecessors

| File | SHA-256 | Match |
| --- | --- | --- |
| `docs/review/d1_yolo54_improvement_r3_contract.md` | `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f` | yes |
| R3 addendum `d1_yolo54_improvement_r3_addendum_a3_executed_2026-11-05.md` | `a1ab05c185f5befa4ab28607662a71a3e6fb80fe28e81368c64a5c1366c74642` | yes |
| `docs/review/generated/d1_yolo54_improvement_r3_analysis.json` | `214aaf404c28cc19edcbbd4216e174e569e6bd44c7ef39d134728361aa44c97b` | equals the R3 manifest pin |
| `detector/m1/yolo54_improvement_r3.py` | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` | yes (contract §5) |
| Pilot `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` | yes |
| Pilot `args.yaml` | `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` | yes |
| `m1_yolo_export_manifest.json` / `m1_yolo_classes.csv` | `8a8df5f2…d179d71` / `7cda296a…cb58d242` | yes |
| `wp36_r1_split_frames.csv` / `wp35_enrichment_lineage.csv` | `8e197d9c…df95823a` / `e802fc26…75d38fed` | yes |
| `resumable_train.py` / `checkpoint_store.py` / `contract.py` | `0a963d4b…` / `e1f8f00c…` / `901e7e37…` | yes (contract §5) |
| `run_d1_colab_checkpoint_r6.py` / `_r1.py` / `detector/uv.lock` | `71a9f4a9…` / `e3193ad7…` / `5d56642a…` | yes (contract §5) |
| `d1_a3_r1_run_contract.md` / `d1_a3_r2_run_contract.md` | `ed6754f3…8cd71c33` / `2cf71027…4115a47e` | yes |
| `run_d1_colab_a3_r2.py` / `resumable_train_a3_r1.py` | `9149d69f…` / `c1eea926…` | equal to the A3-R2 source QA pins |
| §4 evaluator `evaluate_d1_a3_r2_common_r1.py` / `a3_pilot_paired_ci_r1.py` | `5d8e49bf…` / `7edb3824…` | yes (contract §4) |

## 3. Q1–Q6 summary

| Check | Result | Basis |
| --- | --- | --- |
| **Q1 data delta** | **PASS** | Own scratchpad script, importing no repo module. Roster `0ce6afdc…69aa3` matches exactly. Counts 3,712 / 1,912 / 1,800, then 975 = 339 + 636, then 4,687. Boxes match R3 §5. List SHA `90d735d6…` matches, and the author's list is line-identical. No val or test entry. |
| **Q2 single change** | **PASS** | Effective `train_args` equal the pilot `run_contract.json` key for key, except `data`. Every non-identity value equals the pilot `args.yaml`. |
| **Q3 guards** | **PASS (advisory A1, A3)** | Roster and list are verified before training. The hashes enter `run_contract.json`, the recovery binding and the launcher run binding. Authorization path and SHA are required. The flags are false. Path, symlink and test refusals are present. Writes are write-once. |
| **Q4 resume/smoke** | **PASS (condition C1, advisory A2)** | Captured predecessor parser, so no R1 recursion. Fresh smoke is limited to `--stop-after-epoch 1`, and resume forbids a stop. The checkpoint binding holds the list and authorization. Drive suffix `d1_a2_seed_20261018_r1` is distinct. |
| **Q5 run contract** | **PASS giới hạn (condition C1, C2)** | Criteria verbatim with the DK→yolo_id mapping. Evaluator plan = common path + paired CI. D-A2-1 accurate. Claims classified. The gate list omits the notebook step and is ambiguous on which commit `--expected-checkout` names. |
| **Q6 tests/gates** | **PASS** | 80/80 focused tests pass. Ruff and format are clean on the 6 new files. Detector-wide ruff: 44 findings, all in `.ipynb` files, 0 from the new files. Root ruff, both lock checks and graft are OK. The root pytest run did not complete in the QA window (§5). It is not relevant to these files. |

## 4. Findings in detail

### Q1 — data delta (independent recompute)

Script: `/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/a240a870-5e8b-4c46-bbbb-a6628947c11e/scratchpad/qa_a2_roster.py`
(run with `python3 -I`; reads the export labels, class map, split frames, lineage and WP35 source
labels directly; no `m1` import).

- Pins re-hashed: export manifest, class map, split frames and lineage are all equal to the pins.
- **DK→yolo_id from the class map:** `{'7': 7, '32': 33, '41': 42}`, so the targets are yolo_id
  {7, 33, 42}.
- Trap check: an identity map ({7, 32, 41}) would repeat **388** images (roster `079d88a7…`). The
  hazard is real, and the source avoids it. `EXPECTED_YOLO_IDS` and the tests for an identity map
  and a synthetic 32/41 export cover it.
- Train export: 3,712 labels = 1,912 raw + 1,800 WP35. The image and label stems agree.
- Raw stems that are not WP36-R1 `train`: 0. WP35 images whose source frame is not train: 0.
- The raw stem-list hash and the label hash both equal the manifest's train binding
  (`6ac76750…` / `d907fb9f…`).
- WP35 exported labels vs their lineage source re-mapped through the class map: 0 mismatches.
- Repeated: **975** (raw **339**, WP35 **636**). Entries **4,687**. Roster
  **`0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3`**.
- Boxes: DK7 83 raw + 145 WP35; DK32 86 + 52; DK41 171 + 439. These are identical to R3 §5 and the
  R3 analysis JSON.
- List, with the format `images/train/<stem>.jpg`, stems sorted, a repeated stem twice in a row and a
  trailing newline: `90d735d6…fdec2`. The author's list equals mine line for line.
- 339 variant: roster `2485b4bd…c422`, list `c953d458…6b95`, 4,051 entries. These equal contract §8.
- No validation or test path can enter the list:
  - the export `images/train` contains only train stems;
  - `refuse_non_train_entry` rejects any `val` component, any component containing `test`, escapes
    and non-`images/train/` prefixes;
  - the runtime YAML refuses a pilot YAML that has a `test:` key.

### Q2 — single change

- Effective args = `base.train_arguments` with only `data` replaced.
- These are the 16 keys of the pilot `run_contract.json` `train_args`: `batch 4`, `data`,
  `deterministic True`, `device "0"`, `epochs 100`, `exist_ok True`, `fliplr 0.0`, `fraction 1.0`,
  `imgsz 1280`, `name`, `patience 0`, `plots False`, `pretrained True`, `project`,
  `seed 20261018` and `workers 4`.
- Pilot `args.yaml`: `patience: 0`, `workers: 4`, `fliplr: 0.0`, `deterministic: true`.
- `optimizer` is not passed, as in the pilot. The pilot `args.yaml` shows `optimizer: AdamW` /
  `lr0: 0.000172` only because Ultralytics 8.4.172 writes the `auto` choice back
  (`engine/trainer.py:1181`).
- `auto` rule, read in the locked 8.4.172 source:
  - `iterations = ceil(4687/64)×100 = 7,400`, which is ≤ 10,000, so AdamW with
    `lr_fit = round(0.01/58, 6) = 0.000172` (unchanged);
  - above 10,000 the rule would choose `MuSGD`. The contract does not claim otherwise.
- Pretrained model: `contract.bind_training_model`, and the shim checks `PRETRAINED_WEIGHTS_SHA256`
  (`85a76fe8…`).
- `run_contract.json` and `train_args` differ from the pilot only by run identity (`name`,
  `project`), which follows from tag `a2_r1`.
- The author's test checks every key against the real pilot files. My integration probe (Q4)
  reconfirmed the produced `train_args` against the launcher's `expected_train_args`, with an empty
  diff.
- Observation, outside scope: the A3 trainer froze `patience 30`, whereas the pilot used `0`. A2
  correctly uses the pilot's `0`, and Ultralytics treats 0 as no early stopping
  (`patience or inf`, `torch_utils.py:1122`).

### Q3 — guards

- **Roster before training.** `execute` checks the frozen arguments, then the authorization, then
  `prepare_a2_data`. That step runs `ensure`, a build-or-verify that recomputes the roster, the list,
  the box counts and the image bytes (`hash_images=True`) and cross-checks R3 `a2_repeat_roster`. It
  then compares the runtime-list size, and only after that does it reach `base.execute`.
  `dataset_guard` (`on_train_start`) compares the Ultralytics `im_files` multiset with the runtime
  list. I verified in the 8.4.172 source that `get_img_files` and `cache_labels` keep duplicates.
- **Hash binding.** The list, roster, rule id, entry count and authorization SHA are in:
  - the recovery binding (`_a2_binding_fields`);
  - `run_contract.json` (`a2_data`, `owner_authorization`);
  - the launcher `run_binding` (with the checkout and bundle);
  - `colab_execution.json`.
- **Authorization.** Both the trainer and the launcher require:
  - a repo-relative `docs/review/*.md` path that is not the contract;
  - a 64-hex SHA that matches the bytes;
  - the exact standalone line `OWNER_AUTHORIZES_TRAINING: D1-A2-R1`;
  - the experiment id and the full list and roster SHAs.

  A 339-hash record cannot pass. The launcher refuses before writing any state (tested).
- **Flags.** `TRAINING_AUTHORIZED = False` in the trainer and the launcher.
  `sealed_test_accessed=False` in the manifest, `run_contract.json` and the outcomes.
- **Path, symlink and test refusals.** `r3.guard` handles inputs. The output chain refuses
  symlinks. Image links must resolve to exactly `<governed root>/<stem>.jpg`. The launcher's
  authorization path walk refuses symlinks.
- **Write-once.** `O_CREAT|O_EXCL|O_NOFOLLOW`. Partial output is refused. A runtime file is written
  once or must be byte-identical.
- Advisories: **A1** and **A3** in §6.

### Q4 — fresh, smoke, resume

- **Recursion pitfall.** `BASE_PARSER = r1.parser` is captured at import, before `r1.parser` is
  patched. `test_real_predecessor_entry_reaches_launch_without_recursion` drives the real
  R6 → R5 → R2 preflight with the patched parser and stubs only `r1.main`. It also checks that every
  patch is restored.
- **Patched module globals.** The launcher patches `r1.parser`, `r1.build_train_command`,
  `r2.run_binding`, `r1.base.write_json` and `r1.base.load_detector_contract`. All are looked up at
  call time:
  - `r2.main` calls `run_binding` and `r1.parser()`;
  - `r1.main` calls `build_train_command` and `_package_successor`;
  - `_package_successor` calls `base.load_detector_contract(...).inspect_run_weights`.

  The only other caller of `load_detector_contract` is `run_d1_colab.py:416`, which also calls only
  `inspect_run_weights`, so the shim covers it.
- **Smoke and resume.** Smoke is `mode=fresh --stop-after-epoch 1`. A different boundary is refused.
  The R1 base gives `PAUSED_FOR_RESUME` without packaging. Resume:
  - forbids a stop;
  - requires exactly one fresh `PAUSED_FOR_RESUME` attempt with a distinct runtime digest and an
    identical run binding (R2);
  - restores `run_contract.json`, `args.yaml` and `results.csv` from the checkpoint;
  - must reach `COMPLETED` or `COMPLETED_FROM_FINAL_CHECKPOINT` at epoch 100, so an early stop is
    rejected.
- **Checkpoint identity.** The A2 fields join the base binding, which already holds the git commit,
  lock, model, export, class map, split and test seal. Tests show that resume refuses a different
  authorization record and a tampered list.
- **Drive.** The suffix `M1_D1_Colab/runs/d1_a2_seed_20261018_r1` is enforced and differs from the
  pilot and A3 folders. A fresh run requires an empty state dir.
- **QA integration probe (new evidence).** The author's packaging-shim tests use a fake contract
  object only. I added scratchpad test
  `/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/a240a870-5e8b-4c46-bbbb-a6628947c11e/scratchpad/test_qa_a2_integration.py`.
  It runs the real A2 trainer (fresh smoke, then resume to 100) with the author's synthetic export
  and fake YOLO, and feeds the produced `run_contract.json` to the launcher schema. The result:
  - key set = `A2_RUN_CONTRACT_KEYS`;
  - `a2_data` keys = `A2_DATA_KEYS`;
  - `train_args` diff vs `expected_train_args` = `{}`;
  - `owner_authorization` and `status TRAINED` are as expected.

  This means the trainer output and the shim schema agree. The real `check_contract`,
  `validate_environment_record` and the clean-tree requirement on a real Colab result remain
  **unknown** until the run. See C1.

### Q5 — run contract

- **Success criteria.** The §3 quote is identical to the R3 §5 A2 "Success on R3" cell. The machine
  text is identical to `runs.A2_repeat_factor_7_32_41.success_criterion` in the R3 analysis JSON.
  The DK7→7, DK32→33 and DK41→42 mapping is stated. Validation support 111 / 29 / 26 matches R3 §4.
  D-05 is not changed.
- **Evaluator plan.** It follows the common path: `evaluate_d1_a3_r2_common_r1.py` with bundle
  `8e6ffe77…`, verified in the source, plus an append-only A2 successor. The paired CI uses an
  `a3_pilot_paired_ci_r1` successor: 1,000 rounds, seed 20261018, D-02 groups, identical draws. The
  degenerate-CI caveat is accurate. It is correctly labelled a proposal.
- **Gate order.**
  1. source QA;
  2. commit (Owner);
  3. Owner authorization;
  4. L4 smoke;
  5. smoke QA;
  6. resume;
  7. result QA, then the evaluator QA.

  This is consistent with the required order; the contract adds the commit step. **Gaps:** C1
  (which commit `--expected-checkout` names) and C2 (no notebook step).
- **D-A2-1.** The description is accurate.
  - R3 §5 leaves 975 vs 339 to the Owner, "before A2 is frozen for running", and the addendum keeps
    it open.
  - The 339 values are recomputed and equal.
  - The arithmetic is right: 1,172 vs 1,013 iterations per epoch, and auto still AdamW
    (7,400 / 6,400).
  - The append-only consequence is stated correctly.
- **Claims.**
  - The pilot time of 14,786 s is verified: `results.csv` epoch 100 `time` = 14786.4.
  - The compute-mismatch caveat is honest.
  - The packaging shim is correctly listed as unknown on a real result.
  - No overreach was found.
  - Minor: §1 gives the R3 analysis JSON without a hash. It is `214aaf40…`, which equals the R3
    manifest pin.

### Q6 — tests and gates

- **Tests.** The 80 tests cover:
  - the real roster reproduction;
  - the DK hazard, both an identity map and a synthetic 32/41 export;
  - each refusal path;
  - the single-change diff against the real pilot files;
  - the authorization gate;
  - fresh → smoke → resume with binding refusals;
  - the dedup guard;
  - the early-stop rejection;
  - the no-recursion entry;
  - the shim accept and reject cases.
- **Coverage gaps (proposals, not blockers):**
  - the shim is never run against the real `contract` module or a real environment record (partly
    closed by the probe above);
  - there is no test of a non-symlink regular-file image in the export with `hash_images=False`
    (not used by the trainer);
  - there is no test that an untracked authorization record makes the run dirty (C1);
  - the authorization tests do not cover a record that names both the 975 and the 339 hashes.
    Accepting such a record is acceptable, because it still names the 975 list.

## 5. Commands run and results

| Command | Result |
| --- | --- |
| `graft check .` | `graph check: OK` |
| `git status --short \| head -60`, `git log --oneline -3` | §1; HEAD `7a95591` |
| `shasum -a 256 <reviewed files, artifacts, spec, predecessors>` | §2, all matching |
| `python3 -I …/scratchpad/qa_a2_roster.py "$PWD"` | Q1 values above |
| `(cd detector && uv run pytest -q tests/test_a2_repeat_list_r1.py tests/test_resumable_train_a2_r1.py tests/test_run_d1_colab_a2_r1.py)` | **80 passed** in 5.68 s |
| `(cd detector && PYTHONPATH=$PWD uv run pytest -q -s --rootdir <scratchpad> <scratchpad>/test_qa_a2_integration.py)` | **1 passed**. The first attempt failed only because my probe did not remove the run dir between legs, as the author's test does. Fixed in the probe. |
| `(cd detector && uv run ruff check <6 new files>)` / `ruff format --check` | `All checks passed!` / `6 files already formatted` |
| `(cd detector && uv run ruff check m1 colab tests)` | 44 findings, **all in `.ipynb`**, 0 in `.py`, none in the new files |
| `(cd detector && uv lock --check)` | `Resolved 66 packages` (OK) |
| `uv run ruff check src tests` (root) | `All checks passed!` |
| `uv lock --check` (root) | `Resolved 201 packages` (OK) |
| `uv run pytest -q` (root) | **Not completed: unknown.** The first attempt ended without a visible summary line because the output was cut by `tail -2`. The second attempt was still running after more than 17 minutes and was stopped by the reviewer. None of the reviewed files lives under root `src/` or `tests/`, so the root suite is not a gate for this package. Root ruff and the root lock check pass. |
| Read-only source reads | Ultralytics 8.4.172 `trainer.py` (auto optimizer, iterations), `base.py` `get_img_files`, `dataset.py` `get_labels`/`cache_labels`, `torch_utils.py` EarlyStopping; `contract.py` `inspect_run_weights`/`environment`; R1/R2/R6 launchers; `run_d1_colab.py` |

Nothing was trained, no Colab or Drive was touched, nothing was uploaded, and no model was loaded or
run. The only files written are this record and the two scratchpad files.

## 6. Conditions and proposals (no reviewed file was edited)

**C1 — required before the smoke (process; affects the result path).**

- The trainer reads the authorization record from the checkout, and so does the launcher.
- `contract.environment()` counts `git status --porcelain` lines, which include untracked files. The
  A2 packaging shim then demands `git_dirty_files == 0` (`require_clean=True`).
- So an authorization record that is present but **uncommitted** in the Colab checkout would let
  training run for about 5 L4-hours and then fail at packaging.
- Contract §7 step 2 says `--expected-checkout` is the package commit, and step 3 creates the record
  afterwards.
- **Proposal:**
  - an append-only contract addendum (or the operator instructions) stating that
    `--expected-checkout` must be a commit containing both the QA-passed package and the committed
    Owner authorization record, with a clean tree;
  - smoke QA must check `environment.git_dirty_files == 0` in the smoke `run_contract.json`;
  - optionally, a launcher successor that refuses at preflight when `git status --porcelain` is
    non-empty or the record is untracked.

**C2 — required before the smoke (process).**

- The package has no Colab notebook or operator cell sequence for A2.
- The A3 precedent ran its launcher from a notebook (`d1_train_a3_r2.ipynb`) and required a separate
  notebook delta QA before the live smoke.
- **Proposal:** an append-only `detector/colab/d1_train_a2_r1.ipynb`, or an equivalent operator
  guide, with the exact fresh-smoke and resume commands (`--owner-authorization`, its SHA,
  `--expected-checkout`, the Drive state dir), followed by independent delta QA. The alternative is
  an Owner decision recording that the CLI is run directly.

**A1 — advisory.** The source does not force the smoke: `mode=fresh` without `--stop-after-epoch`
(a single 100-epoch leg) is accepted, as in A3. The gate is a process gate.

- **Proposal:** the authorization record names the smoke-first sequence, or a successor refuses a
  fresh run without `--stop-after-epoch 1`.

**A2 — advisory.** `inspect_a2_run_weights` does not compare `record.contract.data_yaml` with the
governed `check_contract()["data_yaml"]`. The real `inspect_run_weights` implies this check through
`data == data_yaml`.

- **Proposal:** add the comparison in any later shim successor.

**A3 — advisory.** The runtime YAML and runtime list hashes are in `run_contract.json` and are
checked by the shim, but they are not in the recovery binding. Low risk, because both are
deterministic and write-once.

- **Proposal:** bind them in any later successor.

**A4 — advisory.** Contract §1 lists the R3 analysis JSON without a hash.

- **Proposal:** pin `214aaf404c28cc19edcbbd4216e174e569e6bd44c7ef39d134728361aa44c97b` in any
  addendum.

## 7. Claim classification (this record)

- **Verified artifact:** every SHA in §2; the Q1 roster, counts, boxes and list hashes, recomputed
  independently; the pilot time of 14,786.4 s.
- **Verified current behavior:**
  - the 80 tests;
  - the integration probe (synthetic export, fake YOLO);
  - the Ultralytics 8.4.172 source behaviors cited.
- **Proposal:** C1, C2 and A1–A4; the §4 evaluator successors (unchanged from the contract).
- **Unknown:**
  - the A2 outcome and wall time;
  - the shim on a real Colab result;
  - Colab installing exactly 8.4.172;
  - the D-A2-1 choice;
  - whether the first L4 smoke passes the stricter image-link check on the regenerated Colab export.
    It fails closed.

`sealed_test_accessed=false`
