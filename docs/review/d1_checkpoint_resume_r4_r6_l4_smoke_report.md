# D1 checkpoint/resume R4-R6 live L4 smoke report

Date: 2026-10-21  
Executor: Codex PM session  
Disposition: **PM PASS; independent artifact QA PASS with 0 findings**  
Pilot 100 epoch authorization: **GO for the D1 single-seed pilot only**

## Scope

This report records the live two-runtime Colab smoke required before the D1 100-epoch pilot. It
does not evaluate model quality and does not authorize access to the sealed test split.

The run used the QA-passed implementation commit
`47c86d17430808ceeee6e1a1a553cf6fef88e5ed`, exposed by the pinned notebook commit
`f674946a15f7035a656404df05ee1bf23e6323e4` on branch `DEV/Rroject_Pineline`.

## Colab and data binding

- Account: `tainguyentan0908@gmail.com`.
- Accelerator shown by Colab for both legs: NVIDIA L4.
- Notebook: `detector/colab/d1_train_checkpoint_r6.ipynb`.
- Run label: `checkpoint_smoke_seed_20261018_r4_r6`.
- Bundle SHA-256: `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`.
- Export contains train/val only; `bundle_binding.test_included=false`.
- Train stem SHA-256: `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`.
- Val stem SHA-256: `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.
- Run binding SHA-256: `e7f8938dd2db4a22d86cadb5cc8c01b0a2f322bf87e709940eb75fd1addc5b2f`.
- Checkpoint binding SHA-256: `41e4940f238105692f1a6ab274ec541285a2a1a131c0b212f478acdbfc3c9bbd`.

## Leg 1: fresh runtime

The notebook was run with `MODE="fresh"` and `--stop-after-epoch 1` on a newly allocated L4
runtime.

- Started: `2026-10-21T01:48:22+00:00`.
- Finished: `2026-10-21T01:52:04+00:00`.
- Runtime identity digest:
  `f9479825d3652e42e08acf64189ff664fd032841413baeaf0550e26bd6007520`.
- Terminal status: `PAUSED_FOR_RESUME`.
- Completed epoch: 1.
- Recovery pointer: `epoch-0001`.
- Epoch-1 manifest SHA-256:
  `b6934b9b46f7bef6cdf2942d1d0209d4be19e369aaa77d61015f0ad73b8dbaf4`.
- Both `weights/last.pt` and `weights/best.pt` were present on Drive at 76,222,627 bytes and
  matched the checkpoint manifest.
- `sealed_test_accessed=false`.

After the Drive evidence was read back, Colab's **Disconnect and delete runtime** action was
confirmed. The UI returned to a disconnected state before the resume leg was started.

## Leg 2: distinct resume runtime

Only the notebook mode was changed from `fresh` to `resume`; the notebook was then run from the
top on a newly allocated L4 runtime.

- Started: `2026-10-21T01:55:44+00:00`.
- Finished: `2026-10-21T01:59:41+00:00`.
- Runtime identity digest:
  `6da5cabaf95dcc10e408d006badaecd3a14e128c5f9bf30a1e7d7fe85e8bdb5c`.
- The digest differs from the fresh leg and both attempts preserve the same run/checkpoint
  bindings.
- The resume command included `--resume` and did not include `--stop-after-epoch`.
- `training_outcome.resumed=true`.
- Terminal status: `SUCCEEDED`.
- Completed epoch: 2.
- Recovery pointer: `epoch-0002`.
- Epoch-2 manifest SHA-256:
  `1165a7290991444071c2a588ab3a8628850757a8192a2f69d1229f33a18e79df`.
- The notebook's final verifier returned `D1_R4_LIVE_STATE_VERIFIED` and
  `D1_RUNTIME_EVIDENCE_VERIFIED` with `attempt_count=2` and
  `distinct_runtime_digests=true`.
- `sealed_test_accessed=false`.

## Durable artifacts read back from Drive

Drive run directory:

`CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/checkpoint_smoke_seed_20261018_r4_r6`

Observed artifact SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| Result archive | `3c640d756bcdce9984ae20d96b57eca4ff936482b7f6eb6817abb92cc47291a4` |
| Archive manifest | `d1e33d2c8c44660437a447b81654ab95acd79dbd9dcdc184ff45be837db464db` |
| `colab_execution.json` | `17dd4a5fcd657875ef8cfca605fd1baf433f68950e76f23c932e2e46bcb642cd` |
| `execution_attempts.jsonl` | `d49dad2349a94e9e50a9fd096330748c8c843b219d01e5fda268c5dc54301965` |
| `DB_logger.db` | `83e3b722b489f67a1edb0c362d30f40712cb76ddb6b0f80b7d2e4ef801f96110` |
| `colab_train.log` | `20e6c800fd86ae941828ba16ddd90d86cd3497c6bcaab2a9d29083bc17b9104a` |

The result manifest declares `terminal_outcome="SUCCEEDED"`,
`sealed_test_accessed=false`, and archive SHA-256
`3c640d756bcdce9984ae20d96b57eca4ff936482b7f6eb6817abb92cc47291a4`.
The archive contains final `best.pt`, `last.pt`, `results.csv`, `args.yaml`, `run_contract.json`,
`colab_execution.json`, `colab_train.log`, and `DB_logger.db`.

SQLite readback found table `logs` with 2,475 rows spanning
`2026-10-21 01:48:24` through `2026-10-21 01:59:41`. It contains the fresh
`PAUSED_FOR_RESUME` outcome, the resume start with `--resume`, `resumed=true`, and the final
`SUCCEEDED` packaging event.

## PM verification

The local R4-R6 verifier was executed read-only against the synced Drive run directory and
returned:

```json
{
  "status": "D1_R4_LIVE_STATE_VERIFIED",
  "runtime_evidence": {
    "status": "D1_RUNTIME_EVIDENCE_VERIFIED",
    "attempt_count": 2,
    "distinct_runtime_digests": true,
    "run_binding_sha256": "e7f8938dd2db4a22d86cadb5cc8c01b0a2f322bf87e709940eb75fd1addc5b2f",
    "checkpoint_binding_sha256": "41e4940f238105692f1a6ab274ec541285a2a1a131c0b212f478acdbfc3c9bbd",
    "sealed_test_accessed": false
  }
}
```

## Independent QA closure

The independent artifact-QA session verified the Drive artifacts, chronology, two distinct runtime
identities, epoch-1 to epoch-2 continuity, archive/manifest hashes, SQLite/text logs, and sealed-test
status, and recorded PASS with 0 findings in
`docs/review/d1_checkpoint_resume_r4_r6_l4_artifact_independent_qa_record.md`. The D1 single-seed
100-epoch pilot is therefore **GO**. Sealed-test access and final evaluation remain **NO-GO**.
