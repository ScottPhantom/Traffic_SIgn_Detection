# G0.7 owner decision, revision 1 — search ranking applied literally

Status: `OWNER_APPROVED_SPLIT_RULES_R1`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)
Amends: `docs/review/g07_owner_decision_record.md`, which is unchanged and pinned by WP36.
Trigger: WP36 independent QA, finding P2-1 (`docs/review/wp36_independent_qa_record.md`).

WP36 ranked the ±3-point ratio band above criterion 3, "at least 2 test groups for
`TRAIN_VAL_TEST` classes". QA showed that this ordering changes the split. The owner chose the
order in the G0.7 record, applied literally:

1. hard rules;
2. per-class requirements;
3. at least 2 test groups for `TRAIN_VAL_TEST` classes where possible;
4. ratio, including the ±3-point band, which is a target and not a hard rule;
5. box balance.

## Consequences accepted by the owner

- The test split may be about 28–29 % of usable frames, above the 15 ± 3 % target, in exchange
  for more classes with two independent test groups.
- Classes 22 and 25 cannot both meet their requirement (both depend on group D02-C0032). The owner
  accepts that 22 loses its validation group, provided 25 gets its test group. Class 22 is then
  not used for tuning, like the other no-validation classes.
- The ratio terms use usable frames: the 24 quarantined negatives are excluded (QA P3-1).

All other rules of the G0.7 record are unchanged. The split is approved only after WP36-R1 passes
independent QA and the owner accepts it. Training is not authorized.
