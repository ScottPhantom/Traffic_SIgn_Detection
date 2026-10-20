# D1 checkpoint/resume R3 code pin record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)

Status: `R3_QA_PASS_CODE_PINNED_READY_FOR_L4_RERUN`

The independently reviewed R3 implementation was committed as
`b9ce31f7278e41f51f6bd7430c2f97f653321618`. The successor notebook pins that exact immutable
commit and uses the append-only Drive run label `checkpoint_smoke_seed_20261018_r2`.

The implementation commit contains the archive-order, single-read gzip extraction repair, its
regression test, the aborted R2 smoke incident record, and the R3 independent QA PASS record.

This pin authorizes only the two-runtime L4 recovery drill:

1. `fresh`: finish epoch 1, verify Drive generation `epoch-0001`, then stop;
2. delete/disconnect the ephemeral runtime;
3. reconnect a new L4 runtime, set only `MODE = "resume"`, and finish epoch 2;
4. verify the final result package and the persisted execution/checkpoint evidence.

The 100-epoch pilot and sealed-test access remain `NO-GO`.
