# D1 Pilot R2 code-pin record

Date: 2026-10-21  
Status: `PINNED_AFTER_INDEPENDENT_SOURCE_QA_PASS`

Independent source QA PASSed Pilot R2 with 0 findings in
`docs/review/d1_pilot_r2_source_independent_qa_record.md` (SHA-256
`b1bf79412382a966f3ac5e96f09011664bbcd14e58cf18751c4bbadb0c0ac00a`). The immutable
implementation commit is:

`939f6bbce9f5c955b13ebcc84addd5083d242355`

The deterministic builder and generated `detector/colab/d1_train_pilot_r2.ipynb` now pin that exact
commit. No runner, training configuration or authorization boundary changed in the pin step.

This pin makes the notebook eligible for mechanical re-verification and push. It does not itself
prove a live Pilot R2 run. Sealed-test access and final evaluation remain forbidden.
