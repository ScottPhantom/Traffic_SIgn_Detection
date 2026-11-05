# D1-A2-R1 source independent QA record (second independent reviewer)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: independent QA agent spawned by the coordinating Claude session (did not author)
Boundary: read-only source QA. No repository file was edited. No git write operation, training,
Colab, upload or inference happened. D-05 and every threshold are unchanged. The sealed test
(`afa03d4b…`) was not opened. `sealed_test_accessed=false`. `training_authorized=false`.

Verdict: PASS giới hạn — the A2 source and run contract are correct against R3 §5; no source defect blocks an L4 smoke, but three pre-smoke conditions (C1–C3) must be met because two operator paths can waste the run or burn the single permitted Drive state folder.

**May an L4 smoke proceed once the Owner authorizes it?** Yes, provided that:

- the reviewed package is committed with byte-identical SHA-256s (contract §7 gate 2);
- a separate Owner authorization record exists (contract §6);
- conditions **C1**, **C2** and **C3** (§6 below) are met.

This record authorizes nothing. The resume to epoch 100 additionally needs the smoke QA.

**Where this record was written.** The session could not write to the main checkout. The record was
therefore written to
`/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/.claude/worktrees/centercam-yolo54-r1/tmp/d1_a2_r1_source_independent_qa_record.md`.
It is to be placed unchanged under `docs/review/` later.

**Prior record notice.** `docs/review/d1_a2_r1_source_independent_qa_record.md` already exists in
the main checkout (SHA-256 `382884233b441079723665595c653e6fdaafd426d90c7959cbbaf8698cd53ec2`,
modified 2026-11-05 20:02). It is an earlier QA record by another reviewer. To keep this review
independent, I read only its header and verdict line, and did not use its findings. Placing this
record must not overwrite that file. A distinct name is proposed, for example
`d1_a2_r1_source_independent_qa_record_r2.md`.

## 1. Q1–Q6 summary

| Check | Result | Evidence (detail in §3–§5) |
| --- | --- | --- |
| Q1 data delta | **PASS** | My own script, not importing the author's modules, reproduced roster `0ce6afdc…69aa3`. It gave 3,712 / 1,912 / 1,800 train images, 975 = 339 + 636 repeated and 4,687 entries. Boxes: DK7 83+145, DK32 86+52, DK41 171+439, matching R3 §5. The DK→yolo map is 7→7, 32→33, 41→42. WP35 counts were cross-checked against the derived-key source labels. The list hash `90d735d6…` equals the written list byte for byte. No val/test stems; every line is under `images/train/`. The trap variant (yolo ids 7/32/41) would give 388 images, roster `079d88a7…`, so it is clearly distinguishable. |
| Q2 single change | **PASS** | The A2 `train_args` key set equals the pilot `run_contract.json` (16 keys), and only `data` differs. Every passed key equals the pilot `args.yaml` except run identity. Epochs 100, patience 0 (pilot), seed 20261018, fliplr 0.0, batch 4, imgsz 1280, workers 4, fraction 1.0, deterministic, pretrained `85a76fe8…`. `optimizer` is not passed (`auto`). In Ultralytics 8.4.172 this resolves to AdamW with lr0 0.000172, since ceil(4687/64)×100 = 7,400 ≤ 10,000. The pilot `args.yaml` `optimizer: AdamW` is the resolved value (`trainer.py:1181` writes it back). |
| Q3 guards | **PASS (with C1/C2)** | The roster/list are built or verified before `base.execute`. The list, roster, rule id, entry count and authorization SHA enter the recovery binding (`experiment` becomes `D1-A2-R1`) and `run_contract.json`. Authorization is refused before data is touched (trainer) and before any state is written (launcher). `sealed_test_accessed=false` and `training_authorized=false` hold in the manifest, plan and run contract. Path, `test`-component, symlink, hardlink, image-link-escape and byte-hash refusals exist. The list, manifest and result archive are write-once; runtime files are write-or-byte-match. Gaps: a dirty checkout (C1) and a launcher/trainer guard mismatch on the authorization file name (C2). |
| Q4 resume and smoke | **PASS** | Follows A3-R2: fresh with `--stop-after-epoch` limited to {None, 1}; resume forbids a stop boundary. The launcher captures `BASE_PARSER = r1.parser` once, so the A3-R1 recursion is avoided (the test drives the real r6→r5→r2→r1 entry). Checkpoint binding = base binding + A2 fields. The Drive suffix is `M1_D1_Colab/runs/d1_a2_seed_20261018_r1` and the checkpoint dir is `<state>/recovery`. On resume, Ultralytics `check_resume` takes `data` from the current `train_args`, which is the re-materialised runtime YAML (`trainer.py:1033`). |
| Q5 run contract | **PASS (one clarification needed, P4)** | §3 is verbatim from the R3 §5 cell and from `run_specs` (`yolo54_improvement_r3.py:827`), and states the DK/yolo map. §4 gives the common evaluator (`5d8e49bf…`, bundle `8e6ffe77…`, 376/624) plus the paired CI (`7edb3824…`, 1,000 rounds, seed 20261018). §7 order: source QA → commit → Owner auth → L4 smoke → smoke QA → resume → result QA. §8 D-A2-1 is accurate: the 339 variant gives roster `2485b4bd…`, list `c953d458…` and 4,051 entries, all reproduced by me. §2.2, §8 and §9 arithmetic checks out (1,172 vs 928 iterations; 14,786.4 s pilot). Claims are classified, and the shim's real-Colab behavior is marked unknown. The §7 gate 2/3 wording needs a clarification (P4, see C1). |
| Q6 tests and gates | **PASS (one transient flake noted)** | 80 tests: first invocation 1 failure (transient, §4), then 80/80 on two full reruns and the failing test alone. Ruff on the 6 new files passes, and so does `ruff format --check`. Root ruff and both `uv lock --check` pass. `graft check .` OK. Detector-wide ruff has 44 findings, all in 17 `colab/*.ipynb` notebooks and none in the new files. Coverage gaps in §5. |

## 2. SHA-256 verification

### 2.1 Reviewed files (all match the brief)

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_a2_r1_run_contract.md` | `1ce153656f2c6c7a7700bdbf57f4d9c1205184ef07bf18a0fd912056e2f396e1` |
| `detector/m1/a2_repeat_list_r1.py` | `28fc4cedb438859f2edd6215a97eb00cb36f385344e19731155e1da971712619` |
| `detector/m1/resumable_train_a2_r1.py` | `c3823eefb9777912fc76302a642427a64869c9097274fc4d5841966c07d42ace` |
| `detector/colab/run_d1_colab_a2_r1.py` | `a6bb6e684701b5a95bd03b71bac777693ec08f1ccb853c98edb2cefdcec2d6de` |
| `detector/tests/test_a2_repeat_list_r1.py` | `1213bfd854dc979bbde6401df51a666194ae224e2b22fbf16c91c88f64a1e248` |
| `detector/tests/test_resumable_train_a2_r1.py` | `baee841bb99d4581cecf9601622fd86dd52f7947f6b4ddba65da3e434a4970dd` |
| `detector/tests/test_run_d1_colab_a2_r1.py` | `6a5745e1eed306d8968dbfe584710916fde871f9fb2bfedaabeb458c22eb0997` |

### 2.2 Locally built A2 artifacts named by the run contract (Git-ignored)

| File | SHA-256 | Note |
| --- | --- | --- |
| `data/processed/d1_a2_r1/a2_train_list.txt` | `90d735d67bde2bf736b5fc8570110561f0184747f3fb25c8f42a3a599d0fdec2` | 4,687 lines. Equals my independent recomputation byte for byte. |
| `data/processed/d1_a2_r1/a2_train_list_manifest.json` | `12f09435a923cfe9e11c6c62f63d1c9906e9840d75ed2908df755bc30b110cbd` | `r3_roster_cross_check=MATCH`, `image_bytes_verified=true`, test/validation/sealed flags false. |
| `data/processed/d1_a2_r1/runtime/` | absent | Consistent with contract §11 ("No runtime YAML was written locally"). |

The local `labels/train.cache` is dated 2026-10-18, so the §11 claim that "No label cache was
written" is consistent.

### 2.3 Binding spec and authorities

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_yolo54_improvement_r3_contract.md` | `3382de28faa960f3c0be3acc28a1ca2d7d17192bfe371f8affca347c6886162f` (match; also the blob at `7a95591`) |
| `docs/review/d1_yolo54_improvement_r3_addendum_a3_executed_2026-11-05.md` | `a1ab05c185f5befa4ab28607662a71a3e6fb80fe28e81368c64a5c1366c74642` (match) |
| `docs/review/generated/d1_yolo54_improvement_r3_analysis.json` | `214aaf404c28cc19edcbbd4216e174e569e6bd44c7ef39d134728361aa44c97b` (holds roster `0ce6afdc…69aa3`) |
| `detector/m1/yolo54_improvement_r3.py` | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` (tracked at `7a95591` with this hash; `FOCUS_KEYS=("7","32","41","46")`, `A2_REPEAT_KEYS=("7","32","41")`, factor 2) |
| Pilot `args.yaml` | `a457c6d51547477348c19a06ec4cf3c8794508169b2e0e1a43edc6260b7d16f0` |
| Pilot `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| `docs/review/generated/m1_yolo_export_manifest.json` | `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71` |
| `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` |
| `docs/review/generated/wp35_enrichment_lineage.csv` | `e802fc264feff5168c28b531801af04051a36accc3c893ad5ab2e72975d38fed` |
| `docs/review/generated/wp36_r1_split_frames.csv` | `8e197d9c7103ac5dc6b7ffc8a3d1aeb30bb6034048d470e4887dd868df95823a` |
| `results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv` | `d45aa7f398a040c44cbc040f4ec005d7e5a8ef50586e905315f76c792ca29022` |

### 2.4 Precedent and reused predecessors (all match contract §5 where pinned there)

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_a3_r1_run_contract.md` | `ed6754f333998848dc4dd344c0119c1aec7f9a323a06c47246ebb0cf8cd71c33` |
| `docs/review/d1_a3_r2_run_contract.md` | `2cf710279878e850b3991bb80a920bafd1f00941c3f3ebe8803b5fbd4115a47e` |
| `detector/colab/run_d1_colab_a3_r2.py` | `9149d69f5301ba5b09f3d8d4d62958c2dddaa62f8edf0919e71a6cd9d73f877d` |
| `detector/m1/resumable_train_a3_r1.py` | `c1eea926fcf72fa194f68f592812a280fb055d9ee9b28435abebc65d0220c87f` |
| `docs/review/d1_a3_r1_source_independent_qa_record.md` | `433d9b3973f6e24a263f1a425adceae2b0c3d8242eef99ee1afa4a128c55cacb` (hashed, not re-reviewed) |
| `docs/review/d1_a3_r2_source_independent_qa_record.md` | `724a3cb1cdaf0f58e962c136605b7726ed8f7ad3ce0b7687bebbaa9191d8ea5f` (hashed, not re-reviewed) |
| `docs/review/d1_a3_r2_packaging_repair_r1_record.md` | `aefa4afeb6c6ec42683cb77bb86f4580d8757119ea7901432620803d3ae0c842` |
| `detector/m1/resumable_train.py` | `0a963d4bc246613402283531b6280836606ac1f5b35b5d215b3959a1354aa6e7` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/m1/contract.py` | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` |
| `detector/m1/cli.py` | `3e0c13b3c47fb396429a0d06e16c6e6d98ca063d10d68d81a4c87af42b4cf967` |
| `detector/colab/run_d1_colab_checkpoint_r6.py` | `71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35` |
| `detector/colab/run_d1_colab_checkpoint_r5.py` | `c1ebfe7e311aa4fb1ccad6738dc392b538083214fe89f79767408caef98acc48` |
| `detector/colab/run_d1_colab_checkpoint_r2.py` | `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112` |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| `detector/colab/run_d1_colab.py` | `6a508eebcb83915201569bc74913a3dd546b288caf2331a9b3e4bd7a567500bc` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` (Ultralytics 8.4.172 installed) |
| `detector/colab/evaluate_d1_a3_r2_common_r1.py` | `5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6` (untracked at `7a95591`, as contract §10 says) |
| `detector/m1/a3_pilot_paired_ci_r1.py` | `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4` (tracked at `7a95591`) |

Provenance note: the A3 run contracts, A3 trainer and A3-R2 launcher are not tracked at
`7a95591`. A2 does not import them; they are precedent only.

### 2.5 QA scratch scripts (outside the repo, not to be committed)

| File | SHA-256 |
| --- | --- |
| `/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/qa_a2_roster.py` | `d3f45d262364d1da9f4b0aef99d43479cec2adc349dc1b8d68cefa280adf90b6` |
| `/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/test_qa_a2_integration.py` | `59c15cd683ff47b1c0a072778d1da83d1048aa7d359a3783c6f53228cb413fad` |

## 3. Detailed findings

### 3.1 Q1 — independent roster recomputation

`qa_a2_roster.py` uses only the standard library and does not import `m1.*`. It checks the
export-manifest, class-map, lineage and split-frame pins and the manifest train binding
(`6ac76750…` / `d907fb9f…`, recomputed from the raw labels). It then reads
`data/processed/m1_yolo/labels/train` and checks the image roster against the labels. The repeat
targets are taken through the class map (`{'7': 7, '32': 33, '41': 42}`).

Result: train 3,712 (raw 1,912, WP35 1,800), repeated 975 (339 raw, 636 WP35), entries 4,687, and
these boxes:

| Derived key | yolo_id | Raw boxes | WP35 boxes | R3 §5 |
| --- | --- | --- | --- | --- |
| 7 | 7 | 83 | 145 | 83 + 145 |
| 32 | 33 | 86 | 52 | 86 + 52 |
| 41 | 42 | 171 | 439 | 171 + 439 |

Further results:

- **Roster.** `0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3`, the same as the
  value in the R3 analysis JSON.
- **List.** `90d735d6…fdec2`. The written list equals the recomputed list byte for byte.
- **WP35 cross-check.** For every WP35 image, the derived-key source label
  (`data/processed/wp35_enrichment/labels`) gives the same per-class counts and the same repeated
  set as the exported yolo-id labels.
- **Split safety.** Every raw stem is a WP36-R1 `train` frame, and every WP35 source stem is
  `train`. List stems ∩ non-train split stems = ∅. Lines outside `images/train/` = 0. Only the
  split-frame CSV metadata was read; no val or test image or label was opened.
- **Read-only verify.** `uv run python -m m1.a2_repeat_list_r1 verify` returned
  `A2_TRAIN_LIST_VERIFIED`, with the same hashes and counts and `r3_roster_cross_check=MATCH`.

### 3.2 Q2 — single change

- `resumable_train_a2_r1.train_arguments` = `base.train_arguments(...)` with `data` replaced by the
  runtime YAML.
- The pilot `run_contract.json` `train_args` has exactly the 16 keys that `base.train_arguments`
  produces, including `fliplr` from `FORBIDDEN_OVERRIDES`. It has no `optimizer` key.
- The runtime YAML is the pilot export `data.yaml` with only `train: images/train` rewritten. Its
  `path:` must equal the resolved export root, no `test:` line is allowed, and `val: images/val` is
  kept.
- **Patience 0 semantics.** `EarlyStopping.patience = patience or inf` (`utils/torch_utils.py:1122`).
- **Duplicate preservation in 8.4.172 (source reading).** `get_img_files` keeps duplicate list lines
  and resolves no paths. `cache_labels` appends a label per image to a list. `get_labels` sets
  `im_files` from that list. `img2label_paths` maps to the export `labels/train`. A corrupt or
  missing label would drop an entry and trip the `on_train_start` multiset guard (refusal, not a
  silent change).

### 3.3 Q3 — guards (code reading plus tests)

**Authorization.**

- **Trainer.** It requires a path and SHA. The path must be relative, its parent exactly
  `docs/review`, its suffix `.md`, and it must not be the run contract. The SHA must be lowercase
  64-hex and match the bytes. The record must contain the exact line on a line by itself, and must
  contain `D1-A2-R1`, the full list SHA and the full roster SHA. The file is read through
  `r3.guard`.
- **Launcher.** It applies the same checks with its own symlink walk, before `r6.main`, so no state
  is written on refusal (tested).

**Binding.**

- The recovery binding adds `experiment=D1-A2-R1`, `owner_authorization_sha256`, `a2_rule_id`,
  `a2_train_list_sha256`, `a2_repeated_roster_sha256` and `a2_train_list_entries`. Tests show a
  different authorization or a changed list refuses resume.
- The launcher run binding adds the authorization SHA, the checkout, the state path, the bundle and
  the list/roster hashes.

**Write-once.**

- The list and manifest use `O_CREAT|O_EXCL|O_NOFOLLOW`. Partial output is refused, and the output
  chain may contain no symlink.
- Runtime files are write-or-byte-match.
- The result archive uses `x:gz` and refuses to overwrite.
- `run_contract.json` is rewritten at finalisation. This is inherited base behavior, as in the
  pilot.

### 3.4 Q4 — resume, smoke, chain entry, packaging shim

- **Chain entry.** `run_d1_colab_a2_r1.main` validates, then patches `r1.parser`,
  `r1.build_train_command`, `r2.run_binding`, `r1.base.write_json` and
  `r1.base.load_detector_contract`. It calls `r6.main` and restores everything in `finally`.
  `r2.main` resolves `run_binding`, and `r1._package_successor` resolves
  `base.load_detector_contract`, by attribute or global lookup at call time, so the patches take
  effect.
- **A3 packaging lesson applied.** `A2ContractShim.inspect_run_weights` validates the exact A2 key
  set (base 10 + 5). It forwards every other attribute, and the attributes it uses all exist in
  `m1/contract.py` (`canonical_sha256`, `strict_json`, `sha256_file`, `GATES`,
  `PRETRAINED_WEIGHTS_SHA256`, `DETECTOR_LOCK_SHA256`, `check_contract`,
  `validate_environment_record`, `RESULTS_DIR`).
- **QA integration probe** (`test_qa_a2_integration.py`, scratch). It ran the A2 trainer fresh
  (stop at 1) and then resume, with a fake YOLO and a synthetic export. The `run_contract.json` it
  actually wrote was passed to `inspect_a2_run_weights` with the **real**
  `validate_environment_record`.
  - Clean checkout (`git_dirty_files=0`): **accepted**, and the attestation was produced.
  - Dirty checkout (`git_dirty_files=1`): **refused** with "must bind a clean Git checkout". This
    happens at packaging, i.e. after all 100 epochs. 2/2 passed. This shows the trainer↔packager
    schema agreement the A3-R2 run lacked. It also shows the late-failure path behind C1.

### 3.5 Q5 — run contract accuracy

- Every number in §2.1, §2.2, §8 and §9 that I could recompute agreed:
  - 1,172 / 928 iterations per epoch (×1.263);
  - auto optimizer 7,400 and 6,400;
  - 339-variant roster, list and 4,051 entries;
  - pilot `results.csv` epoch 100 `time` = 14,786.4 s.
- §3 is verbatim. R3 §4 gives validation support of 111 / 29 / 26.
- §8 describes D-A2-1 accurately. It agrees with R3 §5 ("must be decided before A2 is frozen for
  running") and with addendum §3 ("still open"). The source freezes 975 for QA. An authorization
  naming the 975 hashes is the Owner's choice. Choosing 339 supersedes this package and this QA.
- Claims are classified (§12) without material overreach. The shim's real-Colab behavior and Colab's
  Ultralytics version are correctly marked unknown.
- **Imprecision 1 (§7 gates 2/3).** "The launcher's `--expected-checkout` is that commit" (the
  package commit). The authorization record is created afterwards (gate 3) and must be present in
  the Colab checkout. If it is dropped in as an untracked file, the checkout is dirty (see C1).
- **Imprecision 2 (§2.2).** The contract does not name the alternative to AdamW. In 8.4.172, `auto`
  above 10,000 iterations would be MuSGD, not SGD. This is not reached (7,400), so it is
  informational only.

## 4. Commands and results

All commands ran on the main checkout (`/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`) in
read-only fashion.

| Command | Result |
| --- | --- |
| `shasum -a 256 <7 reviewed files + authorities>` | all match (§2) |
| `python3 -I …/scratchpad/qa_a2_roster.py <repo>` | roster/list/counts/boxes as §3.1; `written_list_equals_recomputed=true` |
| `cd detector && uv run python -m m1.a2_repeat_list_r1 verify` | `A2_TRAIN_LIST_VERIFIED`, `MATCH` (read-only; no file written) |
| `cd detector && uv run pytest -q tests/test_a2_repeat_list_r1.py tests/test_resumable_train_a2_r1.py tests/test_run_d1_colab_a2_r1.py` (1st) | **1 failure**: `test_real_export_reproduces_r3_roster`, `RuntimeError: refused non-regular or hardlinked file: results/data_audit/…/image_inventory.csv` (I did not capture the pass count) |
| same, isolated `-k real_export` | 1 passed |
| same, full (2nd and 3rd) | 80/80 passed, exit 0 |
| `stat -f %l …/image_inventory.csv` | 1 link, regular file. The flake was not reproducible; most likely a transient external hardlink or clone of the file during the first run. Cause unknown. |
| `uv run pytest -q -p no:cacheprovider …/scratchpad/test_qa_a2_integration.py` | 2 passed (clean accepted; dirty refused at packaging) |
| `cd detector && uv run ruff check <6 new files>` | All checks passed |
| `cd detector && uv run ruff format --check <6 new files>` | 6 files already formatted |
| `cd detector && uv run ruff check .` | 44 errors, all in 17 `colab/*.ipynb` notebooks; **none** in the new files |
| `cd detector && uv lock --check` | pass (66 packages) |
| `uv run ruff check src tests` (root) | All checks passed. `uv run` re-installed the editable root package into `.venv`; no tracked file changed. |
| `uv lock --check` (root) | pass (201 packages) |
| `graft check .` | `graph check: OK — the wiring graph is in sync with the code` (deep layer not built) |
| `git ls-tree -r 7a95591 …` / `git show 7a95591:<file> \| shasum` (from the QA worktree, read-only object reads) | R3 module, R3 contract, addendum, analysis JSON, class map, inventory and paired-CI module are tracked at `7a95591`; the A3 trainer/launcher/contracts and the common evaluator are not |

## 5. Coverage gaps (assessment)

1. **The dirty-checkout path is untested and unguarded early.** The shim tests stub
   `validate_environment_record` to a no-op. Neither the launcher nor the trainer refuses a dirty
   checkout before training. My probe confirms the refusal only happens at packaging (C1).
2. **No repository test passes the trainer-written `run_contract.json` through the shim.** The
   shim tests use a hand-built record. My probe closes this for the clean case. A permanent test is
   proposed (P3).
3. **Real Ultralytics duplicate handling is untested.** Tests use FakeYOLO, so only my source
   reading of 8.4.172 covers it. The L4 smoke must show `Using 4687 train` in `colab_train.log`
   (C3).
4. **`materialize_runtime` has not run on a real export.** No local runtime YAML exists. A
   `path:` mismatch on Colab would refuse before training, but it would burn the state folder (see
   C2 rationale).
5. **The launcher accepts a fresh run without a stop boundary.** `stop_after_epoch=None` is
   allowed (inherited from A3-R2). Such a run trains 100 epochs, and then
   `validate_runtime_evidence` requires exactly a fresh-pause plus a resume attempt, so it could not
   be packaged (P1).
6. **The authorization-name guard differs between launcher and trainer.** The launcher test itself
   uses `…_owner_authorization_test.md`. The launcher accepts that name, but the trainer's
   `r3.guard` refuses any component containing `test`, as in "latest" or "attestation". The trainer
   also refuses hardlinked files (C2).

## 6. Required fixes and conditions (proposals; none applied by this QA)

**Pre-smoke conditions (required before the L4 smoke):**

- **C1 — committed authorization and a clean checkout.**
  - Commit the Owner authorization record.
  - Pass as `--expected-checkout` the commit that contains both the byte-identical reviewed package
    and that record.
  - Before launch, confirm `git status --porcelain` is empty in the Colab checkout.
  - Reason: `contract.environment()` counts untracked files. The A2 packaging shim
    (`require_clean=True`) would refuse an untracked record only after 100 epochs, the same failure
    class as the A3-R2 packaging failure. The smoke alone would not reveal this.
- **C2 — authorization file name and type.**
  - The record must be a regular, single-link, non-symlinked file directly under `docs/review/`.
  - Its name must not contain the substring `test`, case-insensitive (this excludes, for example,
    "latest" and "attestation").
  - Reason: the launcher accepts such names but the trainer refuses them after the launcher has
    written state. A failed fresh attempt makes the only permitted state folder
    (`d1_a2_seed_20261018_r1`) unusable for a new fresh start ("fresh R4 state already contains
    attempts"). That would force an append-only successor with a new suffix.
- **C3 — smoke QA checklist additions.** In the mirrored `epoch-0001` `run_contract.json`, check:
  - `environment.git_dirty_files == 0`;
  - `environment.git_commit` = `--expected-checkout`;
  - `train_args` = pilot + `data` only;
  - the `a2_data` list and roster hashes;
  - `owner_authorization` = the record path and SHA.

  In `colab_train.log`, check `Using 4687 train`. In the checkpoint manifest binding, check the A2
  fields.

**Proposals (non-blocking, for any later append-only successor or addendum):**

- **P1.** The launcher should require `--stop-after-epoch 1` for `mode=fresh`, refusing `None`, so
  that an unpackageable fresh-to-100 run cannot start.
- **P2.** The launcher should apply the trainer's exact `r3.guard` rules (test-component and
  hardlink refusals) to the authorization path. Both should refuse a dirty checkout before writing
  state.
- **P3.** Add a permanent test that passes the trainer-produced `run_contract.json` through
  `inspect_a2_run_weights` with the real `validate_environment_record`, for both clean and dirty
  cases (as in the scratch probe).
- **P4.** Add a run-contract addendum clarifying §7 gates 2/3: `--expected-checkout` is the commit
  containing the package **and** the authorization record. Optionally, name MuSGD as the
  >10,000-iteration `auto` branch in 8.4.172.
- **P5.** Place this record under a name that does not overwrite the existing
  `d1_a2_r1_source_independent_qa_record.md` (`3828842…`).

## 7. Flags

- `sealed_test_accessed=false`. Only the token `afa03d4b` in run names was read, never the sealed
  split.
- `training_authorized=false`.
- No repository file was edited. No git write was made. No Colab, upload, inference, D-05 or
  threshold change happened.
