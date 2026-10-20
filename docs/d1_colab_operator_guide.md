# Hướng dẫn tự vận hành training D1 trên Google Colab

Trạng thái tài liệu: `OPERATOR_GUIDE_TRAIN_VAL_ONLY`

Cập nhật: 2026-10-19 (`Asia/Ho_Chi_Minh`)

## 1. Phạm vi và nguyên tắc an toàn

Hướng dẫn này dành cho Owner tự chạy baseline chính **YOLO 54 lớp** trên Google Colab. Notebook
chỉ dùng dữ liệu `train` và `val`; nó không có lệnh xuất, đọc hoặc đánh giá test niêm phong.

Không thực hiện các thao tác sau trong giai đoạn smoke/pilot:

- không thêm `export-test`, `--final-eval` hoặc đường dẫn test;
- không dùng test để chọn model, confidence threshold hoặc NMS threshold;
- không sửa script để bỏ qua kiểm tra hash, commit, CUDA hoặc split;
- không bật horizontal flip; package đã khóa `fliplr=0`;
- không đổi taxonomy 54 lớp hoặc thay trọng số pretrained bằng file khác;
- không xóa log/run cũ để tái sử dụng cùng `RUN_LABEL`.

Nếu một assert hoặc verifier dừng notebook, hãy coi đó là lỗi cần điều tra. Không comment assert
để ép training tiếp tục.

## 2. Cơ chế lưu log

Notebook có ba lớp log và đều được đặt trong Google Drive tại:

```text
My Drive/CPV391/M1_D1_Colab/runs/<RUN_LABEL>/
```

Các file chính:

| File | Vai trò |
| --- | --- |
| `colab_train.log` | Log văn bản, gồm từng command và toàn bộ stdout/stderr của subprocess |
| `DB_logger.db` | Cơ sở dữ liệu SQLite được ghi liên tục trong lúc workflow chạy |
| `colab_execution.json` | Trạng thái máy đọc được: `STARTED`, `SUCCEEDED` hoặc `FAILED`, các bước đã hoàn thành và lỗi cuối |
| `*_result.tar.gz` | Gói kết quả chỉ được tạo sau khi workflow kết thúc thành công |
| `*_result.tar.gz.manifest.json` | Roster, kích thước và SHA-256 của gói kết quả |

SQLite dùng bảng `logs` tương thích với notebook VGG16 đã lưu trước đó:

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    level TEXT,
    logger TEXT,
    message TEXT
);
```

Mỗi dòng output của lệnh con được ghi vào console, `colab_train.log` và `DB_logger.db`. Vì thư mục
state nằm trên Drive, hai log này vẫn còn nếu tab trình duyệt bị đóng. Tuy nhiên checkpoint model
đang train nằm trong runtime tạm của Colab cho đến khi workflow thành công và đóng gói; runtime bị
ngắt giữa chừng không có nghĩa là có thể resume.

## 3. Chuẩn bị trước khi chạy

### 3.1. Tài khoản và dữ liệu Drive

Đăng nhập đúng Google account đã giữ bundle riêng tư. Kiểm tra thư mục:

```text
My Drive/CPV391/M1_D1_Colab/
```

Phải có sidecar và một trong hai dạng vận chuyển được notebook hỗ trợ:

```text
m1_colab_train_val_backend_r1.tar.gz.manifest.json
```

- một archive đầy đủ `m1_colab_train_val_backend_r1.tar.gz`; hoặc
- tám phần `m1_colab_train_val_backend_r1.tar.gz.part-00` đến `part-07`.

Đường chia phần là phương án vận hành hiện tại vì upload archive 730,7 MiB trực tiếp đã thất bại
trên Drive sau nhiều lần resumable retry. Bảy phần đầu có `99614720` bytes; `part-07` có
`68923760` bytes. Hash chính xác được pin trong notebook và
`tmp/m1_colab_train_val_backend_r1.tar.gz.parts.json` tại máy chuẩn bị.

Thông tin gói đã được QA:

- archive size: `766226800` bytes;
- archive SHA-256: `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641`;
- sidecar size: `1499866` bytes;
- sidecar SHA-256: `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2`;
- embedded repository commit: `ffc2b448f06c45dae597de5b565cab64c0377573`;
- chỉ có `train` và `val`, tổng cộng `5888` payload files;
- `test_included=false`.

Không đổi tên, nối hoặc giải nén thủ công các file trên Drive. Notebook tự hash từng phần, nối vào
runtime tạm `/content`, rồi kiểm lại size và SHA-256 của archive hoàn chỉnh trước khi đọc manifest.

### 3.2. Hash lại chính bản đang mount trên Drive

Upload record chỉ chứng minh source bytes ở máy local và trạng thái UI lúc upload. Trước khi
notebook đọc manifest bên trong archive, notebook phải hash lại **chính sidecar và archive hoặc
tám phần đang mount từ Drive**.

1. Chạy riêng cell đầu tiên để mount Drive.
2. Chạy cell preflight có sẵn ngay sau cell mount. Không rút gọn hoặc bỏ qua danh sách
   `PART_SPECS`; đó là contract size/hash của cả tám phần.

Chỉ tiếp tục khi cell in `mounted_bundle_preflight: PASS`. Nếu dùng các phần, output phải có
`bundle_source: verified_drive_parts`. Giữ cell preflight này để mỗi lần **Chạy tất cả** đều hash
từng input, nối đúng thứ tự và hash archive hoàn chỉnh trước cell đọc manifest/checkout code. Nếu
hash hoặc kích thước khác, dừng ngay; không sửa expected hash theo file vừa đọc.

### 3.3. Mở notebook đúng phiên bản

Mở notebook đã bind với bundle:

```text
https://colab.research.google.com/github/ScottPhantom/Traffic_SIgn_Detection/blob/DEV/Rroject_Pineline/detector/colab/d1_train.ipynb?authuser=3
```

Có thể nhấn **Sao chép vào Drive** để giữ một bản vận hành riêng. Không thay code của các cell kiểm
tra commit, bundle và result package.

### 3.4. Chọn GPU

Trong Colab:

1. Chọn **Thời gian chạy → Thay đổi loại thời gian chạy**.
2. Chọn GPU **L4** nếu tài khoản cung cấp L4.
3. Lưu cấu hình.
4. Nút góc phải phải hiển thị loại GPU dự kiến; khi bắt đầu chạy, Colab sẽ kết nối runtime.

Notebook và runner sẽ tự kiểm tra CUDA/GPU/driver. Không coi việc giao diện hiện chữ “L4” là bằng
chứng training đã chạy; bằng chứng cuối nằm trong `colab_execution.json` và result archive.

## 4. Chạy smoke một epoch

Smoke là lần chạy bắt buộc trước pilot 100 epoch.

Trong cell cấu hình, giữ nguyên:

```python
RUN_LABEL = 'smoke_seed_20261018_backend_r1'
SMOKE = True
SEED = 20261018
EPOCHS = 1 if SMOKE else 100
IMGSZ = 1280
BATCH = 8
DEVICE = '0'
```

Run `smoke_seed_20261018` đã thất bại và là evidence bất biến; tuyệt đối không dùng lại. Notebook
kế nhiệm đã dùng label mới:

```python
RUN_LABEL = 'smoke_seed_20261018_backend_r1'
```

Không tái sử dụng thư mục state cũ.

Sau đó:

1. Xác nhận cell hash preflight nằm sau cell mount và trước mọi cell đọc bundle.
2. Chọn **Thời gian chạy → Chạy tất cả**.
3. Cho phép Colab mount Google Drive khi được hỏi.
4. Xác nhận cell preflight in `Mounted Drive bundle and sidecar hashes: PASS`.
5. Theo dõi output của cell gọi `run_d1_colab.py`.
6. Không đóng tab hoặc ngắt runtime trong lúc training.
7. Chờ cell cuối đọc lại `colab_execution.json` và result archive.

Workflow sẽ tự động:

1. đọc manifest bên trong bundle và checkout đúng commit `ffc2b448f06c45dae597de5b565cab64c0377573`;
2. xác minh bundle chỉ có train/val và stem hashes đúng;
3. tái tạo dataset YOLO train/val;
4. chạy `uv sync --frozen` trong môi trường detector;
5. tải đúng trọng số Ultralytics đã được Owner duyệt nếu local runtime chưa có;
6. xác minh SHA-256 của `yolo11s.pt` là
   `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`;
7. chạy `m1.cli check`;
8. train một epoch với `fliplr=0` và telemetry bị tắt;
9. đóng gói đúng tám artifact kết quả và tạo sidecar manifest.

## 5. Xác nhận smoke thành công

Chỉ công nhận thành công khi cell cuối chạy xong và đồng thời thỏa các điều kiện:

```python
execution['status'] == 'SUCCEEDED'
execution['sealed_test_accessed'] is False
```

`steps_completed` phải theo đúng thứ tự:

```text
bundle_verified_and_extracted
train_val_export_regenerated
detector_lock_synchronized
approved_pretrained_weight_verified
m1_cli_check_passed
training_completed
```

Thư mục run trên Drive phải có:

```text
colab_train.log
DB_logger.db
colab_execution.json
<D1_RUN_NAME>_result.tar.gz
<D1_RUN_NAME>_result.tar.gz.manifest.json
```

Không công nhận thành công chỉ vì progress bar đã đạt 100% hoặc cell training không còn quay.

### 5.1. Đọc nhanh SQLite sau khi run kết thúc

Có thể thêm một cell kiểm tra tạm thời sau cell cuối:

```python
import sqlite3

database = STATE_DIR / 'DB_logger.db'
with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
    assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    rows = connection.execute(
        '''
        SELECT id, timestamp, level, logger, message
        FROM logs
        ORDER BY id DESC
        LIMIT 50
        '''
    ).fetchall()

for row in reversed(rows):
    print(row)
```

Đọc 100 dòng cuối của text log:

```python
lines = (STATE_DIR / 'colab_train.log').read_text(encoding='utf-8').splitlines()
print('\n'.join(lines[-100:]))
```

## 6. Xử lý khi notebook thất bại

Đầu tiên đọc:

```python
import json

execution_path = STATE_DIR / 'colab_execution.json'
print(json.dumps(json.loads(execution_path.read_text()), indent=2, ensure_ascii=False))
```

Sau đó kiểm tra `error`, `steps_completed`, 100 dòng cuối `colab_train.log` và các dòng cuối trong
SQLite.

| Hiện tượng | Cách xử lý |
| --- | --- |
| `Missing approved train/val bundle` | Kiểm tra mount Drive, account và đường dẫn `CPV391/M1_D1_Colab` |
| `state directory must be empty` | Dùng `RUN_LABEL` mới; không xóa run cũ |
| CUDA/GPU identity không hợp lệ | Chọn lại runtime GPU L4, reconnect, dùng label mới và chạy lại từ đầu |
| Bundle/hash mismatch | Dừng; không tải gói khác và không bỏ kiểm tra hash |
| `yolo11s.pt` hash mismatch | Dừng; xóa runtime Colab, dùng runtime mới để runner tải lại file chính thức |
| Matplotlib báo `module://matplotlib_inline.backend_inline` không hợp lệ | Không phải OOM. Giữ run thất bại; chỉ dùng successor runner đã QA với `MPLBACKEND=Agg`, bundle mới và `RUN_LABEL` mới |
| CUDA out of memory | Dùng run label mới và giảm `BATCH` từ `8` xuống `4`; giữ `IMGSZ=1280`. Đây là cấu hình candidate mới: phải QA smoke và giữ cùng batch cho pilot/ba seed nếu được duyệt |
| `status=STARTED` nhưng runtime đã mất | Coi run là thất bại do ngắt đột ngột; dùng label mới, không resume thư mục cũ |
| `status=FAILED` | Giữ nguyên toàn bộ folder để review; sửa nguyên nhân rồi chạy label mới |

Không chạy lại chỉ riêng cell training trên state directory cũ. Workflow yêu cầu thư mục mới để
không trộn log và artifact của hai lần chạy.

## 7. Chạy pilot 100 epoch sau khi smoke được review

Chỉ chuyển sang pilot sau khi gói smoke đã được tải về, verifier chấp nhận và QA xác nhận.

Trong bản notebook mới, đổi:

```python
RUN_LABEL = 'pilot_seed_20261018'
SMOKE = False
SEED = 20261018
```

Giữ nguyên cấu hình đã vượt smoke và được QA chấp nhận:

```python
IMGSZ = 1280
DEVICE = '0'
```

`BATCH` phải bằng batch của smoke đã được duyệt:

- mặc định là `8` nếu smoke batch 8 thành công;
- là `4` nếu smoke batch 8 bị OOM, smoke recovery batch 4 đã PASS và QA/Owner chấp nhận cấu hình
  đó.

Không dùng batch 4 để chữa OOM smoke rồi âm thầm quay lại batch 8 ở pilot hoặc ba seed. Mọi seed
cuối phải dùng cùng cấu hình đã khóa trên validation.

Với `SMOKE=False`, notebook đặt `EPOCHS=100`. Chạy lại toàn bộ notebook từ đầu. Đây là **pilot một
seed**, chưa phải ứng viên cuối ba seed.

Sau pilot:

1. giữ nguyên archive và manifest trên Drive;
2. tải cả hai file về máy local;
3. chạy standalone verifier;
4. chỉ sau verifier PASS, giải nén và đặt nguyên thư mục pilot `D1_*` dưới
   `<repo>/results/experiments/`;
5. từ `detector/`, chạy `uv run python -m m1.cli register-runs --weights
   ../results/experiments/<PILOT_RUN>/weights/best.pt`;
6. gửi `docs/review/generated/d1_run_registry.json` cho QA độc lập, rồi git-track và commit file
   không đổi; xác nhận registry sạch;
7. chỉ sau registry gate mới chạy `uv run python -m m1.cli evaluate --weights
   ../results/experiments/<PILOT_RUN>/weights/best.pt --split val --bootstrap`;
8. viết báo cáo pilot từ `<repo>/results/experiments/<PILOT_RUN>/eval_val.json`;
9. chỉ sau review mới quyết định có train ba seed cuối hay đề xuất hiệu chỉnh gate một lần;
10. không sửa hoặc ghi đè D-05 hiện tại; mọi gate hiệu chỉnh phải được ghi trong một
   **append-only successor decision record** mới và được Owner phê duyệt rõ ràng trước khi mở
   sealed test.

Registry pilot đã commit không được xóa hoặc sửa tay. Khi ba final run sẵn sàng, lệnh
`register-runs` ở Mục 9 sẽ đọc registry sạch hiện có và thêm các attestation final vào successor
registry, sau đó registry mới lại phải qua QA và commit không đổi trước final validation evaluate.

## 8. Xác minh result archive trên máy local

Đặt archive và manifest trong một thư mục local, sau đó chạy từ repo:

```bash
cd detector
uv run python colab/verify_d1_result.py \
  --archive /duong/dan/<D1_RUN_NAME>_result.tar.gz \
  --manifest /duong/dan/<D1_RUN_NAME>_result.tar.gz.manifest.json
```

Verifier phải trả JSON có:

```text
status = D1_COLAB_RESULT_PACKAGE
terminal_outcome = SUCCEEDED
sealed_test_accessed = false
```

Không giải nén và tự chọn riêng `best.pt` trước khi verifier PASS.

## 9. Các seed cuối và giới hạn test niêm phong

Ba seed được D-05 phê duyệt là:

```text
20261018
20261019
20261020
```

Không chạy ba seed cuối ngay sau smoke. Trình tự đúng là:

```text
smoke 1 epoch
→ QA smoke
→ pilot 1 seed / 100 epoch
→ pilot validation report
→ nếu cần: tạo append-only successor decision record và chờ Owner phê duyệt
→ khóa cấu hình train cuối (chưa khóa threshold)
→ train đủ ba seed với cùng cấu hình
→ verify từng result package và đặt ba run dưới <repo>/results/experiments/
→ register cả ba best.pt vào run registry
→ QA, git-track và commit run registry không đổi trong worktree sạch
→ evaluate cả ba weights trên validation
→ tạo đúng một threshold lock từ đúng ba validation report
→ QA và commit threshold lock không đổi trong repo
→ chỉ sau đó mới xem xét đánh giá test niêm phong một lần
```

“Khóa cấu hình train” ở bước trước ba seed chỉ gồm model, dữ liệu, hyperparameter và seed set. Nó
không phải threshold lock. Confidence/NMS cuối chỉ có thể được khóa sau khi đã có đủ ba validation
report của ba seed khác nhau `20261018`, `20261019`, `20261020`.

Sau khi mỗi result archive vượt standalone verifier, giải nén archive đã verify và đặt nguyên thư
mục run `D1_*` của nó dưới `<repo>/results/experiments/`. Không chỉ chép riêng `best.pt` vì CLI
còn kiểm `last.pt`, `run_contract.json` và các binding của run. Giả sử ba run local lần lượt là
`D1_seed_20261018`, `D1_seed_20261019`, `D1_seed_20261020`, chạy từ thư mục `detector/`:

```bash
uv run python -m m1.cli register-runs \
  --weights \
    ../results/experiments/D1_seed_20261018/weights/best.pt \
    ../results/experiments/D1_seed_20261019/weights/best.pt \
    ../results/experiments/D1_seed_20261020/weights/best.pt
```

Lệnh tạo `../docs/review/generated/d1_run_registry.json` nhưng cố ý báo
`ready_for_evaluation=false`. Chưa chạy evaluate. Trước hết phải:

1. gửi registry cho QA độc lập, đối chiếu ba seed, run contract và SHA-256 của weights;
2. `git add ../docs/review/generated/d1_run_registry.json` và commit file registry không đổi;
3. xác nhận `git status --short -- ../docs/review/generated/d1_run_registry.json` không có output.

Chỉ sau đó mới evaluate validation cho từng run; mỗi lệnh tự ghi `eval_val.json` trong đúng thư mục
run:

```bash
uv run python -m m1.cli evaluate \
  --weights ../results/experiments/D1_seed_20261018/weights/best.pt \
  --split val --bootstrap
uv run python -m m1.cli evaluate \
  --weights ../results/experiments/D1_seed_20261019/weights/best.pt \
  --split val --bootstrap
uv run python -m m1.cli evaluate \
  --weights ../results/experiments/D1_seed_20261020/weights/best.pt \
  --split val --bootstrap
```

Nếu tên run thực tế khác ví dụ, thay cả tên trong command bằng đúng tên thư mục đã được result
manifest xác minh. `register-runs` và `evaluate` sẽ từ chối weights không nằm dưới
`<repo>/results/experiments/`, thiếu artifact, sai seed hoặc registry chưa được git-track, commit
và sạch.

Sau khi cả ba `eval_val.json` đã được review, tạo threshold lock đúng một lần từ thư mục
`detector/`:

```bash
uv run python -m m1.cli lock-thresholds \
  --reports \
    ../results/experiments/D1_seed_20261018/eval_val.json \
    ../results/experiments/D1_seed_20261019/eval_val.json \
    ../results/experiments/D1_seed_20261020/eval_val.json \
  --out ../docs/review/generated/d1_threshold_lock.json
```

CLI sẽ từ chối nếu không có đúng ba report, sai bộ seed hoặc ba report không trỏ tới ba weights
khác nhau. Threshold lock phải được QA độc lập kiểm tra, thêm vào git và commit trong worktree sạch,
không thay đổi, trước bất kỳ lệnh `export-test` hoặc `evaluate --split test --final-eval` nào. Không
tạo threshold lock tạm từ riêng pilot và không chạy `lock-thresholds` lần thứ hai sau khi đã xem
test.

Test niêm phong không nằm trong bundle Drive và không được dùng trong Colab training.

## 10. Baseline detector một lớp và classifier

Notebook detector một lớp nằm tại:

```text
detector/colab/d1_cascade_train.ipynb
```

Nó dùng cùng bundle train/val nhưng ghi vào:

```text
My Drive/CPV391/M1_D1_Colab/cascade_runs/<RUN_ID>/
```

Chỉ chạy notebook này sau khi baseline YOLO 54 lớp smoke đã được review. Trình tự cũng là smoke một
epoch trước, dùng run ID mới cho mỗi lần chạy. Package R2 đã QA PASS nhưng cascade gate addendum
vẫn chưa được Owner duyệt, vì vậy kết quả cascade chỉ được dùng trên validation.

Classifier 54 lớp hiện có hai implementation candidate:

```text
compact_cnn
vgg16_scratch
```

Chưa có architecture được Owner chọn và chưa có notebook classifier Colab đã QA. Không tự viết
cell training classifier hoặc dùng model VGG16 43 lớp cũ thay cho classifier WP33 54 lớp.

## 11. Checklist ngắn cho Owner

Trước khi chạy:

- [ ] Đúng Google account và Drive folder riêng tư.
- [ ] Archive và sidecar đúng tên.
- [ ] Bản archive/sidecar đang mount đã được hash lại và cell preflight in `PASS`.
- [ ] Notebook đúng commit bind với bundle.
- [ ] Runtime GPU L4.
- [ ] `SMOKE=True` và `EPOCHS=1`.
- [ ] `RUN_LABEL` chưa từng dùng.
- [ ] `SEED=20261018`, `IMGSZ=1280`, batch là cấu hình smoke candidate (`8` mặc định).

Sau khi chạy:

- [ ] Cell cuối báo `SUCCEEDED`.
- [ ] `sealed_test_accessed=false`.
- [ ] SQLite `PRAGMA integrity_check` trả `ok`.
- [ ] Có text log, SQLite log, execution JSON, result archive và manifest.
- [ ] Không xóa run folder dù run thành công hay thất bại.
- [ ] Không chuyển sang pilot trước khi smoke package được verifier/QA duyệt.
