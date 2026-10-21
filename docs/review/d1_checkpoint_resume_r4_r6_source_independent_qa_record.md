# D1 checkpoint/resume R4-R6 source independent QA record

Status: `INDEPENDENT_QA_PASS`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**PASS for source release, commit/push, notebook pinning and a new two-runtime/two-epoch L4
smoke. The 100-epoch pilot remains NO-GO until the live smoke receives a separate independent
artifact QA PASS.**

R4-R6 closes the sole R4-R5 blocker. The terminal execution object now requires
`type(schema_version) is int` and the exact value `2` before delegating to the inherited semantic
validator. Independent execution confirmed that integer `2` passes while JSON float `2.0`, boolean
`true`, string `"2"` and `null` fail closed through the direct validator, the actual archived
`colab_execution.json` path and the actual live JSON/JSONL comparison path.

No Critical, High, Medium or Low finding remains in the frozen R4-R6 scope. This review did not run
Colab, train a model, upload data, access the sealed test, commit or push.

## Frozen inputs and inheritance

All four handed-off hashes matched before review:

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r6.py` | `71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35` |
| `detector/colab/d1_train_checkpoint_r6.ipynb` | `837f40148acb6884a829652c941648c8902557226d51c49af258bd7a2ed55e1d` |
| `tests/test_d1_checkpoint_runtime_evidence_r4_r6.py` | `8e20e757cf88d53976c25148e641daefcf7156a4285822bfaca0bb3f9bd3409e` |
| `docs/review/d1_checkpoint_resume_r4_r6_implementation_record.md` | `2af9aad4d6c73710a95b86f1c9d104491ef2dcc17f2c5a23878c9c9de6d8348b` |

The append-only inherited runner chain also retained the hashes accepted by the preceding records:

| Inherited artifact | SHA-256 |
| --- | --- |
| `run_d1_colab_checkpoint_r5.py` | `c1ebfe7e311aa4fb1ccad6738dc392b538083214fe89f79767408caef98acc48` |
| `run_d1_colab_checkpoint_r4.py` | `25431f08a10b016a21b19a5c5c98c1d7419eee180bb7aeaf772b674f9b1cb27f` |
| `run_d1_colab_checkpoint_r3.py` | `1c2999cbaf4248b5df649a3a0e63e5b2c5d1d7ae697ae858ef06df19707dbe0c` |
| `run_d1_colab_checkpoint_r2.py` | `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |

## Independent attack results

### Exact execution schema type: PASS

- Direct validation accepted exact integer `2`.
- Direct validation rejected `2.0`, `true`, `"2"` and `null`.
- A separately built canonical eight-file tar archive with a valid integer execution schema passed
  the real R6 archive verifier.
- Four otherwise identical archives carrying `2.0`, `true`, `"2"` or `null` were rejected by the
  real archive decoder/verifier.
- A live directory using the real strict execution reader, JSONL attempt reader, archive verifier
  and archive/live equality check passed with integer `2`; the same live path rejected each of the
  four invalid representations. Only checkpoint filesystem I/O was stubbed in that isolated live
  fixture; runtime-evidence parsing and comparison were not stubbed.

### Direct, archive, live and packaging installation: PASS

`validate_runtime_evidence` performs the exact-type check before the pinned R4-R2 semantic
validator. R6 temporarily installs this validator around all public paths and restores the prior
binding in `finally`:

- direct calls use the R6 validator;
- archive calls wrap the inherited archive verifier;
- live calls wrap the R5 live verifier, whose nested R4-R2 calls resolve the installed validator;
- `main` wraps the entire inherited execution, including the final package verification invoked by
  the R4-R2 runner.

Although the inherited compatibility reader converts schema v2 to the historical schema v1 for
the base package source checks, final packaging invokes the installed R4 archive verifier against
the archived bytes. Therefore a malformed `2.0`, `true`, `"2"` or `null` execution schema cannot
produce a successful governed package result.

### Adjacent type-confusion and bypass review: PASS

An independent 128-case mutation matrix exercised wrong JSON-compatible scalar/container types in
the terminal execution and both attempts. It covered status, mode, sealed-test flag, error,
timestamps, runtime identity, run/checkpoint hashes and embedded attempts. Every mutation was
rejected. In particular:

- `sealed_test_accessed` requires the singleton `False`, so `0`, `1`, `null`, `"false"` and
  containers cannot substitute for it;
- both attempts require an exact key set; runtime identity requires exactly `schema` and `digest`;
- hashes require lowercase 64-character strings;
- mode/status pairs, null error, timezone-aware non-overlapping chronology, two ordered attempts,
  distinct runtime digests and equal run/checkpoint bindings remain mandatory;
- execution identity and its embedded attempts must exactly equal the successful resume evidence;
- archived and live evidence must match exactly;
- duplicate JSON keys and non-finite values remain rejected by the inherited strict parsers.

The inherited checkpoint path protections remain intact: type-strict checkpoint schema and sizes,
generation validation before path construction, ancestor-symlink rejection, pinned-store replay,
manifest and artifact rehashing, and durable preflight failure evidence.

## Notebook boundary

The R6 notebook is unexecuted, defaults to `MODE = "fresh"`, uses the isolated run label
`checkpoint_smoke_seed_20261018_r4_r6`, calls only the R6 runner and remains blocked at
`CODE_COMMIT = "PENDING_AFTER_QA"`. It contains neither `export-test` nor `--final-eval` and does
not authorize the sealed test or the 100-epoch pilot.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 plus all R4 through R4-R6 targeted root tests | PASS, **58/58** |
| Independent adjacent-type mutation matrix | PASS, **128/128 rejected** |
| Independent real archive schema matrix | PASS, integer `2`; **4/4 invalid forms rejected** |
| Independent real live schema matrix | PASS, integer `2`; **4/4 invalid forms rejected** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff | PASS |
| Detector Ruff | PASS |
| Root lock | PASS, **168 packages** |
| Detector lock | PASS, **66 packages** |
| Repository verifier matrix | PASS, **52/52** in 101.4 s wall time |
| `git diff --check` | PASS before this append-only QA record |
| Graft freshness-aware source trace | PASS; active direct/archive/live/main flow located |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| R4-R5 strict execution schema repair | **PASS** |
| R4-R6 source release, commit/push and notebook pin | **GO** |
| New isolated two-runtime/two-epoch L4 smoke | **GO** |
| Sealed-test access | **NO-GO / not authorized** |
| 100-epoch pilot | **NO-GO pending independent live-smoke artifact QA PASS** |

After commit/push, replace only the notebook's `CODE_COMMIT` placeholder with the exact clean
release commit, then run the isolated fresh leg and resume leg on two distinct newly allocated L4
runtimes. Preserve both attempt digests, epoch-0001 and epoch-0002 checkpoints, result archive,
manifest, SQLite log and text log for the next independent QA session.
