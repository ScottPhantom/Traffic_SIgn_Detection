# Prompt bàn giao cho Claude — D1 YOLO11s pilot R3 đến khi hoàn tất 100 epoch

> Dán toàn bộ nội dung từ mục **PROMPT BẮT ĐẦU** đến **PROMPT KẾT THÚC** vào
> Claude Code/Claude CLI đang mở tại repository này. Đây là lệnh thực thi của Owner,
> không phải báo cáo để Claude chỉ tóm tắt.

---

## PROMPT BẮT ĐẦU

Bạn là kỹ sư/PM kế nhiệm đang tiếp tục một run huấn luyện thật, không phải bắt đầu một
thí nghiệm mới. Hãy làm việc liên tục đến khi pilot D1 YOLO11s R3 hoàn tất 100 epoch,
toàn bộ bằng chứng hoàn tất được xác minh, và gói công việc đã sẵn sàng chuyển cho một
QA độc lập. Không tự cấp trạng thái PASS hoặc GO thay cho QA.

### 1. Phạm vi và nguồn sự thật

- Repository có thẩm quyền:
  `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`
- Branch hiện hành: `DEV/Rroject_Pineline`.
- Owner là người duy nhất có quyền thay đổi phạm vi, mở test niêm phong, đổi gate D-05,
  tải/upload dữ liệu ngoài phạm vi đã duyệt, hoặc xuất bản kết quả.
- Trước khi làm bất kỳ việc gì, đọc toàn bộ:
  1. `AGENTS.md`;
  2. `PROJECT_MEMORY.md`;
  3. các tài liệu canonical mà `PROJECT_MEMORY.md` định tuyến đến cho D1/Colab;
  4. các hồ sơ R3 được liệt kê ở mục 4 bên dưới.
- Dùng Graft trước khi đọc hoặc sửa source:

  ```bash
  cd /Users/nguyentantai/Desktop/app/Traffic_Sign_Detector
  graft check .
  graft ask "How does the D1 Colab R3 runner checkpoint, resume, log attempts, and verify terminal artifacts?" --source .
  ```

- Nếu `graft check .` báo `STALE`, dùng các truy vấn Graft freshness-aware trong khi
  điều tra và chạy `graft build . && graft check .` trước khi bàn giao thay đổi source.
- Repo và artifact thực tế luôn thắng prompt này nếu có sai khác. Phải nêu rõ sai khác,
  không âm thầm chọn một bên.

### 2. Trạng thái đã quan sát tại thời điểm bàn giao

Đây là snapshot có thời điểm, không phải bằng chứng tự động cho trạng thái ở thời điểm
bạn đọc prompt:

- Ngày: `2026-10-21`, múi giờ `Asia/Ho_Chi_Minh`.
- Notebook đang dùng:
  `detector/colab/d1_train_pilot_r3.ipynb` tại commit pin
  `904ba8083cfc6cdf7e5aa0fc3c01319efc519d99`.
- URL notebook đã mở:
  `https://colab.research.google.com/github/ScottPhantom/Traffic_SIgn_Detection/blob/904ba8083cfc6cdf7e5aa0fc3c01319efc519d99/detector/colab/d1_train_pilot_r3.ipynb`
- Notebook đang chạy cell train trên GPU NVIDIA L4, `MODE="resume"`.
- Log terminal live được quan sát khoảng `15:32:38 2026-10-21 +07:00` đang ở
  epoch `26/100`, vẫn tăng batch bình thường, chưa thấy terminal failure.
- Bằng chứng Drive đọc qua connector ở cùng giai đoạn chỉ mới nhìn thấy checkpoint bền
  vững `epoch-0016`, `status="STARTED"`, `error=null`,
  `sealed_test_accessed=false`.
- Vì vậy **không được đồng nhất epoch đang hiển thị trong terminal với checkpoint có thể
  phục hồi**. Ngay khi nhận việc, hãy đọc lại file thật trên Drive/mounted Drive, kiểm tra
  manifest và hash để xác định epoch bền vững mới nhất.
- Tên run cố định: `pilot_seed_20261018_r2`.
- Thư mục Drive logic:
  `M1_D1_Colab/runs/pilot_seed_20261018_r2`.
- `colab_execution.json` ở lần đọc cuối ghi:
  `status="STARTED"`, `mode="resume"`,
  `started_at="2026-10-21T08:05:38Z"`, `error=null`,
  `sealed_test_accessed=false`.
- `recovery/latest.json` ở lần đọc cuối trỏ đến `epoch-0016` với binding digest
  `fc81808ed503921b37e0e30fa748b779173461898b3098413059ab85de5532b6`.

Connector Drive hoặc trang GitHub có thể cache. Chỉ gọi một trạng thái là “hiện tại” khi
bạn đã đọc lại file/artifact thật hoặc quan sát notebook runtime trực tiếp. Nếu chỉ có
snapshot cũ, ghi rõ đó là snapshot cũ.

### 3. Cấu hình pilot phải giữ nguyên

Không thay đổi các giá trị sau trong khi tiếp tục run:

```text
model: YOLO11s pretrained
task: detector 54 lớp
seed: 20261018
epochs: 100
imgsz: 1280
batch: 4
patience: 0
device: 0
tag: pilot_100e_seed_20261018_r2
run_label: pilot_seed_20261018_r2
```

Đây là detector YOLO11s 54 lớp, không phải model crop GTSRB 43 lớp có tên file
`VGG16_model.h5`. Không mô tả pilot này là đã được xác nhận cho giao thông Việt Nam,
OOD, UNKNOWN, hoặc an toàn xe thật. Mọi hành vi xe chỉ là mô phỏng.

### 4. Các pin và hồ sơ đã được QA độc lập

Giữ nguyên và xác minh lại các pin quan trọng:

```text
training checkout commit:
  939f6bbce9f5c955b13ebcc84addd5083d242355

R3 sidecar implementation commit:
  e20a69541e3a6327739238fc71691109ce8f51d0

R3 notebook pin commit:
  904ba8083cfc6cdf7e5aa0fc3c01319efc519d99

R3 runner SHA-256:
  8c9b23472091f6c677d635a54e4f4e8b896e1fcf204d627ba56eb208db00c49c

R3 notebook SHA-256:
  67d8d24a3f432b17085069d7d7545a3673bdd3fa6771be094f698c6e99e8ee81

builder SHA-256:
  cfd9d0517ead578d1eb6092be73718bb10fbe77fdfa46802f1b559a5c40378ce

notebook tests SHA-256:
  8bf195327cb07f0efd9c97a4383458f1adddec54297f4e636ca0ec93f8055d1c

dataset bundle SHA-256:
  7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641
dataset bundle size:
  766226800 bytes

sidecar manifest SHA-256:
  7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2
sidecar manifest size:
  1499866 bytes

pretrained model SHA-256:
  85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5
```

Đọc các hồ sơ sau trước khi can thiệp:

- `docs/review/d1_pilot_r3_retry_recovery_implementation_record.md`
- `docs/review/d1_pilot_r3_retry_recovery_source_independent_qa_record.md`
- `docs/review/d1_pilot_r3_notebook_pin_implementation_record.md`
- `docs/review/d1_pilot_r3_notebook_pin_independent_qa_record.md`
- `docs/review/d1_checkpoint_resume_r4_r6_l4_artifact_independent_qa_record.md`

Các source/notebook R3 đã được QA độc lập PASS với 0 finding trong phạm vi review của
chúng. PASS source không có nghĩa pilot 100 epoch đã hoàn tất hoặc model đã đạt gate.

### 5. Việc phải làm ngay

1. Không restart notebook đang chạy khỏe và không chạy `fresh`.
2. Kiểm tra trực tiếp:
   - notebook còn kết nối L4 và cell train có tiếp tục tạo output;
   - `colab_execution.json`;
   - `recovery/latest.json`;
   - checkpoint manifest;
   - SQLite log và text log;
   - danh sách attempt append-only;
   - `sealed_test_accessed=false`.
3. Xác minh checkpoint mới nhất bằng manifest và SHA-256 của đủ năm file recovery mà
   runner yêu cầu. Không chỉ kiểm tra tên thư mục hoặc sự tồn tại của `last.pt`.
4. Theo dõi tối đa mỗi 10 phút. Khi trạng thái vẫn `STARTED`, epoch/checkpoint tăng,
   runtime khỏe và không cần Owner thao tác thì không phát thông báo dài hoặc gây nhiễu
   notebook.
5. Chỉ báo Owner khi có một trong các thay đổi có ý nghĩa:
   - checkpoint quan trọng mới;
   - runtime mất kết nối hoặc GPU đổi;
   - terminal failure;
   - cần Owner đăng nhập/xác nhận Drive;
   - run hoàn tất;
   - phát hiện `sealed_test_accessed` không còn là `false`.

### 6. Quy trình phục hồi bắt buộc nếu runtime bị ngắt

Nếu runtime ngắt đột ngột nhưng không có terminal failure:

1. Không xóa hoặc ghi đè lịch sử attempt, log, checkpoint hay thư mục run.
2. Đọc lại `recovery/latest.json`, manifest và đủ năm file checkpoint.
3. Rehash tất cả file và xác minh đúng run/checkpoint binding.
4. Chỉ khi checkpoint hợp lệ mới mở một runtime L4 mới.
5. Dùng đúng notebook R3 đã pin và `MODE="resume"`.
6. Bảo đảm checkout train vẫn là commit
   `939f6bbce9f5c955b13ebcc84addd5083d242355` và clean trước khi import/train.
7. Xác minh epoch kế tiếp bắt đầu sau checkpoint, không train lại từ epoch 1.
8. Giữ toàn bộ attempt cũ. Thiết kế R3 cho phép một attempt `fresh` đã PAUSED, không
   hoặc nhiều attempt `resume` FAILED, và attempt cuối SUCCEEDED.

Nếu có terminal failure thật, ghi lại failure append-only và chẩn đoán nguyên nhân trước
khi resume. Không biến một attempt FAILED thành SUCCEEDED bằng cách sửa tay log/trạng thái.

### 7. Điều kiện hoàn tất 100 epoch

Chỉ công bố run hoàn tất khi tất cả điều kiện sau đều có bằng chứng đọc lại:

- checkpoint bền vững cuối là `epoch-0100`;
- `colab_execution.json` có `status="SUCCEEDED"`;
- `training_outcome.status` là `COMPLETED` hoặc `COMPLETED_FROM_FINAL_CHECKPOINT`;
- `training_outcome.completed_epoch == 100`;
- có đúng một result archive `*_result.tar.gz` cho run;
- có result manifest và mọi hash/size khớp file thật;
- archive có đúng các thành viên bắt buộc:
  1. `best.pt`;
  2. `last.pt`;
  3. `results.csv`;
  4. `args.yaml`;
  5. `run_contract.json`;
  6. `colab_execution.json`;
  7. `colab_train.log`;
  8. `DB_logger.db`;
- SQLite log mở được, có run/epoch/attempt phù hợp và không mâu thuẫn text log;
- text log kết thúc hợp lệ, không che giấu traceback/failure;
- retry-aware runtime evidence hợp lệ;
- có ít nhất hai runtime digest khác nhau trong lịch sử recovery đã được bảo toàn;
- `sealed_test_accessed=false` ở execution state, run contract, manifest và báo cáo;
- test niêm phong chưa được export, đọc, đánh giá hoặc dùng để chọn threshold/model.

Chạy cell xác minh cuối của notebook R3 nếu runtime vẫn còn. Nếu phải xác minh ngoài
notebook, dùng cùng logic/schema của runner R3, không tự tạo một verifier giản lược.

### 8. Báo cáo PM sau khi hoàn tất

Tạo hồ sơ append-only mới:

`docs/review/d1_pilot_r3_100e_completion_report.md`

Báo cáo tối thiểu phải có:

- thời gian bắt đầu/kết thúc và múi giờ;
- cấu hình train thực tế;
- commit/SHA/binding digest;
- bảng toàn bộ attempt với mode, runtime digest, epoch bắt đầu/kết thúc, trạng thái và lỗi;
- checkpoint phục hồi cuối và bằng chứng hash;
- result archive, manifest, size và SHA-256;
- kiểm tra đủ tám thành viên archive;
- kết quả đối chiếu SQLite log với text log và `results.csv`;
- bằng chứng `epoch-0100`, `status=SUCCEEDED`;
- bằng chứng `sealed_test_accessed=false`;
- danh sách điều gì đã đo thật, điều gì chỉ là ước tính, điều gì chưa kiểm chứng;
- mọi sự cố, cách khôi phục và phần còn thiếu;
- trạng thái cuối phải là `READY_FOR_INDEPENDENT_QA`, không phải `QA PASS`, `GO`,
  `M4 ACCEPTED` hay “model đạt chuẩn”.

Nếu cần sửa source/notebook để xử lý lỗi mới, không sửa file bị pin tại chỗ. Tạo gói
revision mới, ghi rõ blast radius, lý do và hash; sau đó chờ QA source riêng trước khi dùng
revision đó cho training.

### 9. Đánh giá val và latency sau khi artifact hoàn tất

Không mở test niêm phong. Sau khi result archive đã hoàn tất và Owner đã cho phép tải
artifact về local nếu cần, chạy đánh giá **val** và latency trên M1 Pro theo CLI hiện có:

```bash
cd /Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/detector
uv run python -m m1.cli evaluate \
  --weights <verified-run>/weights/best.pt \
  --split val \
  --bootstrap

uv run python -m m1.cli latency \
  --weights <verified-run>/weights/best.pt
```

Viết `docs/review/d1_pilot_report.md` với:

- mAP50, mAP50-95, AP-small;
- recall detection bỏ qua lớp và FP/ảnh tại threshold chỉ chọn từ val;
- recall từng lớp kèm support;
- kết quả tách theo độ phân giải;
- mẫu lỗi bỏ sót, sai khung và sai lớp;
- latency p95 đo trên M1 Pro;
- lớp không có val/test phải được ghi đúng là chưa kiểm chứng, không được suy diễn PASS.

Nếu Owner chưa cho phép download artifact từ Drive, hãy hoàn thành báo cáo training và
QA handoff trước, ghi evaluation local là `BLOCKED_PENDING_OWNER_DOWNLOAD_APPROVAL`, rồi
hỏi Owner một câu ngắn, rõ target file cần tải. Không tự tải.

### 10. Quality gate của repo

Sau mọi thay đổi source hoặc tài liệu material, chạy và lưu exit code/output thật:

```bash
cd /Users/nguyentantai/Desktop/app/Traffic_Sign_Detector
uv run ruff check src tests
uv lock --check
uv run python scripts/run_parallel_checks.py verifiers

cd detector
uv run ruff check m1 tests
uv run pytest

cd ..
graft build .
graft check .
git diff --check
git status --short
```

Baseline gần nhất được biết là bộ verifier `52/52` và detector tests `93 passed`, nhưng
hãy báo số thực bạn vừa chạy; không copy số baseline nếu chưa chạy lại. Không sửa các
test cũ hoặc file pin chỉ để làm gate xanh.

### 11. Bàn giao cho QA độc lập

Sau khi PM report hoàn chỉnh:

1. Chuyển đúng source pin, report, result manifest, archive metadata, checkpoint manifest,
   `colab_execution.json`, `run_contract.json`, SQLite log, text log và `results.csv` cho
   một QA ở session/agent độc lập.
2. QA phải làm read-only và tự kiểm tra hash/schema/chronology/binding, không chỉ đọc kết
   luận của PM.
3. QA phải xác minh:
   - epoch 100 thực sự hoàn tất;
   - resume không quay về epoch 1;
   - attempt history append-only;
   - archive đủ và hash đúng;
   - SQLite/text/result nhất quán;
   - hai runtime digest khác nhau;
   - `sealed_test_accessed=false`;
   - test niêm phong chưa bị mở.
4. Nếu QA FAIL, quay lại sửa đúng finding và tạo revision record; không tự bỏ qua.
5. Chỉ sau QA PASS mới có thể báo Owner rằng pilot 100 epoch đã được nghiệm thu về mặt
   artifact. QA PASS này vẫn không tự động chứng minh model đạt D-05 và không cho phép mở
   test niêm phong.

Nếu bạn không có cơ chế tạo QA/session độc lập, dừng ở
`READY_FOR_INDEPENDENT_QA` và đưa cho Owner một prompt QA riêng; không tự đóng cả vai PM
lẫn QA trong cùng phiên.

### 12. Các giới hạn tuyệt đối

- Không chạy `export-test`.
- Không dùng `--final-eval`.
- Không đọc hoặc phân tích test niêm phong.
- Không chọn model/threshold từ test.
- Không đổi gate D-05.
- Không lật ngang ảnh.
- Không xóa raw data, checkpoint, log hay attempt cũ.
- Không upload thêm dữ liệu, download artifact mới, commit hoặc push nếu chưa có xác nhận
  Owner ngay trước hành động external/material đó.
- Không sửa `README.md`, root `pyproject.toml`, root `uv.lock`,
  `src/cpv301_autodrive/dataset_graph.py`, `docs/dataset01_card.md` hoặc file đã pin tại chỗ.
- Không mô tả “cell đang chạy”, “epoch hiện trên terminal”, hay “file tồn tại” là bằng
  chứng hoàn tất khi chưa đọc lại terminal state, hash, manifest và logs.
- Không tuyên bố an toàn, production-ready, Việt Nam-ready hoặc model đạt gate khi chưa có
  bằng chứng đúng phạm vi.

### 13. Định dạng báo cáo cho Owner

Mỗi cập nhật có ý nghĩa phải ngắn và theo đúng bốn mục:

1. **Đã xác minh:** bằng chứng hiện tại, thời điểm và nguồn.
2. **Đang diễn ra:** epoch live và checkpoint bền vững phải ghi riêng.
3. **Rủi ro/chưa kiểm chứng:** nêu rõ điều chưa biết hoặc snapshot có thể stale.
4. **Hành động tiếp theo:** việc bạn sẽ làm hoặc đúng một thao tác cần Owner thực hiện.

Khi hoàn tất, báo thêm danh sách file thay đổi, lệnh kiểm tra và kết quả thật. Đừng commit
hoặc push báo cáo cho đến khi Owner xác nhận hành động đó.

Hãy bắt đầu bằng việc đọc repo/Graft và xác minh lại trạng thái run thật hiện tại. Nếu run
đang khỏe, tiếp tục theo dõi; không khởi động lại chỉ để tạo cảm giác đã “nhận việc”.

## PROMPT KẾT THÚC
