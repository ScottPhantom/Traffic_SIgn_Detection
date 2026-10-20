# Hướng dẫn smoke checkpoint/resume D1 R1 trên Colab

Trạng thái: `AWAITING_INDEPENDENT_QA_AND_PINNED_CODE_COMMIT`

Phạm vi: chỉ `train`/`val`; không xuất, đọc hoặc đánh giá test niêm phong.

## Mục đích

Notebook kế nhiệm không bắt đầu pilot 100 epoch. Nó thực hiện recovery drill hai chặng:

1. chặng `fresh` hoàn thành đúng epoch 1/2, ghi snapshot đã hash lên Drive rồi chủ động pause;
2. Owner ngắt runtime, kết nối một runtime L4 mới và chạy chặng `resume`; runner khôi phục
   optimizer/scheduler/scaler từ `last.pt`, chạy epoch 2/2 và tạo result package chuẩn.

Chỉ khi hai chặng, standalone verifier và QA độc lập đều PASS mới được đề xuất chạy pilot 100
epoch bằng một state directory mới.

## Trước khi mở Colab

- QA độc lập phải PASS package local.
- Commit chứa runner phải được Owner cho phép commit/push lên branch hiện tại.
- Thay `CODE_COMMIT = 'PENDING_AFTER_QA'` trong
  `detector/colab/d1_train_checkpoint_r1.ipynb` bằng SHA-1 40 ký tự của commit đã review và push.
- Commit/push notebook đã pin đó, rồi mở đúng notebook từ branch.
- Không dùng lại `RUN_LABEL` nếu recovery drill đã tạo state trước đó.

Placeholder hiện tại cố ý làm notebook fail closed; không được bỏ assert hoặc chuyển sang branch
floating.

## Chặng 1 — fresh, đúng một epoch

1. Chọn L4 và đăng nhập đúng tài khoản giữ bundle trong
   `MyDrive/CPV301/Traffic_Sign_Detector/M1_D1_Colab`.
2. Giữ `MODE = 'fresh'`, `EPOCHS=2`, `BATCH=4` và `--stop-after-epoch 1` như notebook.
3. Run all, cho phép mount Drive.
4. Chỉ chấp nhận khi cell cuối xác nhận:
   - `colab_execution.json.status == PAUSED_FOR_RESUME`;
   - `recovery/latest.json.generation == epoch-0001`;
   - không có result archive sớm;
   - `sealed_test_accessed == false`.
5. Không sửa file trong state directory. Ngắt/xóa runtime Colab để chứng minh ổ `/content` cũ
   không còn.

## Chặng 2 — runtime mới, resume

1. Kết nối một runtime L4 mới.
2. Đổi duy nhất `MODE = 'resume'`; giữ nguyên code commit, run label, seed, epochs, image size,
   batch và mọi tham số khác.
3. Run all. Notebook phải clone sạch cùng `CODE_COMMIT`, hash lại bundle, tái tạo train/val và
   kiểm tra toàn bộ checkpoint trước khi restore.
4. Chỉ chấp nhận khi:
   - `colab_execution.json.status == SUCCEEDED`;
   - `training_outcome.resumed == true`;
   - completed epoch là 2;
   - có đúng một `*_result.tar.gz` và sidecar;
   - SQLite/text log chứa cả hai attempt và terminal success;
   - `sealed_test_accessed == false`.

## Đọc lại và QA sau Colab

Tải archive và manifest về local, sau đó chạy:

```bash
cd detector
uv run python colab/verify_d1_result.py \
  --archive /duong/dan/D1_*_result.tar.gz \
  --manifest /duong/dan/D1_*_result.tar.gz.manifest.json
```

Verifier phải trả `status=D1_COLAB_RESULT_PACKAGE`, `terminal_outcome=SUCCEEDED` và
`sealed_test_accessed=false`. Sau đó QA độc lập phải kiểm thêm `execution_attempts.jsonl`,
`latest.json`, manifest snapshot, hash năm recovery artifact, hai epoch trong `results.csv` và
trạng thái optimizer có trong checkpoint resume.

## Khi nào tuyệt đối không resume

- thay seed, batch, epochs, image size, workers, fraction hoặc patience;
- thay code commit, detector lock, pretrained weight, export manifest hoặc stem hash;
- `latest.json`, manifest hay bất kỳ artifact nào sai hash;
- checkpoint path có symlink;
- state không dừng ở `PAUSED_FOR_RESUME`;
- run đã `SUCCEEDED` hoặc đã tạo result package.

Trong các trường hợp trên, giữ nguyên evidence và dừng. Không sửa `latest.json`, không hạ guard,
không mở test niêm phong.
