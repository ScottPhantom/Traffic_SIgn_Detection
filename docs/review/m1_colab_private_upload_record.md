# M1 Colab private train/val upload record

Status: `UPLOAD_VERIFIED_SMOKE_NOT_RUN`
Recorded at: `2026-10-19T00:48:33+07:00`

## Authorized scope

The Owner authorized a private Google Drive upload of only the M1 train and validation exports in
`docs/review/m1_colab_training_owner_decision_record.md`. The sealed test was not authorized for
upload and remains protected by D-05.

## Uploaded package

- Repository commit bound inside the archive:
  `1842a1b77e6448a54fec486937f4c0f0e6ff19f5`.
- Archive: `m1_colab_train_val.tar.gz`, `766226824` bytes, SHA-256
  `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191`.
- Sidecar: `m1_colab_train_val.tar.gz.manifest.json`, `1499866` bytes, SHA-256
  `2c43d5fdff3de32af3fa3b9621f7f73cf1646c2f51801c5844ae89e8f4ae8d3b`.
- Manifest status: `TRAIN_VAL_ONLY_READY`; `5888` payload files; regular files only.
- Allowed splits: exact list `["train", "val"]`; `test_included=false`.
- Raw counts: `1912` train images and `376` validation images.
- WP35 train-only counts: `1800` images and `1800` labels.
- Train stem-list SHA-256:
  `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`.
- Validation stem-list SHA-256:
  `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.
- Sealed-test stem-list commitment only:
  `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.
  The sealed-test files are absent from the archive.

## External readback

The upload was read back in the Owner's private Google Drive account at:

`My Drive/CPV391/M1_D1_Colab`

Google Drive displayed both expected filenames, reported the archive as `730.7 MB` and the
sidecar as `1.4 MB`, and displayed `Only you can see the information` for the selected object.
The Drive storage total changed consistently with the archive upload. This is external UI
readback; the cryptographic sizes and hashes above come from the local source files.

## Post-upload verification

After the active branch advanced beyond the bundle checkpoint, verification against the new HEAD
failed closed with `bundle manifest binding differs: repo_git_commit`, as designed. The archive
was then verified from a temporary detached worktree at its exact bound commit
`1842a1b77e6448a54fec486937f4c0f0e6ff19f5`. That verification returned `status=VERIFIED`,
`file_count=5888`, the archive SHA-256 above, the exact train/validation stem hashes above and
`test_included=false`. No manifest field or archive byte was rewritten to follow the newer branch.

## Execution boundary

The immutable notebook was opened from the bound commit under the same Google account and showed
an L4 runtime option with `SMOKE=True`, one epoch and the expected Drive bundle path. No notebook
cell has been executed. Therefore:

- no Colab runtime has been connected;
- no dependency has been installed in Colab;
- no pretrained weight has been downloaded inside Colab;
- no GPU/CUDA identity has been observed;
- no training, checkpoint, metric, latency result or result archive exists;
- the sealed test has not been exported, uploaded, opened or evaluated.

The next authorized project step remains the one-epoch Colab smoke. Its execution and any newly
acquired software installation require action-time confirmation in the computer-use session.
