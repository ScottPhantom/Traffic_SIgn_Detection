# VGG16-54 R1 long-run R6 launch repair record

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Status: `IMPLEMENTED_PENDING_INDEPENDENT_LAUNCH_QA`

R5 failed closed before emitting an `ATTEMPT` or starting GPU model work because the R4 smoke had
already restored its checkpoint into the default ephemeral runtime directory
`/content/vgg16_54_work/D1_VGG16_54_R1`. The checkpoint store correctly refuses to overwrite an
existing resume destination.

R6 changes only the local ephemeral work root to `/content/vgg16_54_long_r6_work`. It does not
delete, rename or reuse the R4 local restore and does not alter any Drive checkpoint, log, proof,
configuration, runtime identity or model source. The governed runner must create the new work root,
verify and restore the latest Drive checkpoint there, and continue from epoch 2 on the same
QA-reviewed runtime digest
`648af06dd95af878657f2f041dd78a18cdf3137c27858176454204065a3e1ff5`.

The exact successor command is frozen in
`docs/review/generated/vgg16_54_r1_long_r6_launch_contract.json`. It retains `mode=resume`, omits
`--stop-after`, pins the same two-runtime smoke proof and has no test, final-evaluation or sealed-test
route. Independent launch QA must PASS before execution.
