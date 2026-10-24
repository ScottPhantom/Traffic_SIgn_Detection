# VGG16-54 R1 — Owner decision record

Status: `OWNER_APPROVED_EXACT_CONFIG_COMMIT_PUSH_UPLOAD_AND_FRESH_SMOKE`

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Boundary: `OWNER_APPROVES_SCOPED_COMMIT_PUSH_PRIVATE_DRIVE_UPLOAD_AND_FRESH_EPOCH1_SMOKE_NO_SEALED_TEST`

## Direct Owner decision captured

The Owner asked why the proposed VGG16 classifier used 30 epochs rather than 100 and directed:
if a 100-epoch schedule can improve the model, use 100 epochs.

This authorizes changing the training ceiling from 30 to 100 epochs. It is implemented as a
maximum rather than a forced terminal epoch:

- maximum epochs: `100`;
- early stopping cannot occur before epoch `30`;
- early-stopping patience: `15` consecutive epochs without a better validation selection score;
- `best.pt` remains selected by supported-class validation macro-F1, with lower validation loss
  as the tie-break.

This decision does **not** claim that epoch 100 must be more accurate than epoch 30. The final
checkpoint selected for comparison may come from any epoch that wins the locked validation rule.

## Exact Owner approval — 2026-10-24

The Owner subsequently approved the full configuration identified by canonical config SHA-256
`b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a`:

- scratch `weights=None`, RGB `32x32`, `54` classes;
- seed `20261018`;
- maximum `100` epochs, no early stop before `30`, patience `15`;
- batch `256`, workers `2`;
- AdamW learning rate `1e-4`, weight decay `1e-4`;
- CUDA AMP enabled;
- no horizontal flip;
- supported-class macro-F1 selection with lower validation loss as tie-break;
- `sealed_test_accessed=false`.

The Owner also authorized a scoped VGG commit, a new branch named `codex/vgg16-54-r1`, push to
GitHub, and upload of the Owner approval, QA proof and notebook to the private project Drive.
Fresh epoch-1 smoke is authorized after immutable commit and notebook QA gates pass.

The exact machine-readable approval is
`docs/review/generated/vgg16_54_r1_owner_approval.json`. It must be hash-pinned in the launch
notebook and verified before any GPU work.

This decision does not authorize sealed-test access. Resume smoke still requires a genuinely
different L4 runtime and independent artifact QA; long training remains blocked until that smoke
QA PASS.

`sealed_test_accessed=false`.
