# Bàn giao Codex: chương trình chấm test cuối (successor) và chuẩn bị chốt contract đánh giá cuối — 2026-11-06

Owner nói trong chat ngày 06/11, nguyên văn: "Bắt đầu bàn giao công việc". Câu này đáp lại danh sách bước,
trong đó có bước "Chốt contract đánh giá cuối, viết chương trình chấm test mới, cho QA, rồi anh duyệt mở
test".

- Người viết: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`, HEAD
  `6ba906d` lúc viết.

Việc này **chạy song song** với bộ khóa R3: không ghi chung file nào. Phần chốt contract (mục 3) phải chờ.

## 0. Ranh giới (bất biến) — quan trọng nhất

- **TUYỆT ĐỐI KHÔNG MỞ TEST.**
  - Không mở, liệt kê, đếm, đọc, hash hay chấm bất kỳ file nào của sealed test `afa03d4b…`.
  - Không gọi `export-test`, `m1.cli evaluate --split test`, hay bất kỳ lệnh nào chạm tới test.
  - Mọi test chỉ được dùng **dữ liệu tổng hợp**, tức ảnh và nhãn giả tạo trong thư mục tạm của test.
  - Mọi output ghi `sealed_test_accessed=false`.
- **Không train, không suy luận trên weight thật.**
- **Không sửa file đã pin hoặc đã QA:** `contract.py`, `cli.py`, `metrics.py`, các evaluator, contract,
  phụ lục. Chỉ tạo file mới.
- **Git:** chỉ `git add` từng đường dẫn cụ thể. Không `git add -A`, stash, reset, clean. Giữ nguyên file dirty
  của Owner. **Không push** nếu Owner chưa cho phép trong chat.
- QA độc lập do phiên hoặc agent **khác** với phiên viết code, và có đúng một dòng `Verdict:`.

## 1. Đọc trước

- `docs/review/d1_final_evaluation_r1_contract_draft.md`, cùng phụ lục 1 (2 seed) và record QA bản nháp.
- `docs/review/d05_owner_decision_record.md`, `docs/review/d05_proposal.md`.
- `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`: Q1 đã đổi thành 2 seed. Các mốc Q2 giữ nguyên.
- `docs/review/d1_threshold_lock_r1_contract.md` và phụ lục 1.
- `docs/codex_handoff_r3_threshold_lock_successor_2026-11-06.md`: reader của bộ khóa R3 là đầu vào của chương
  trình chấm này.
- Cơ chế có sẵn: `contract.log_test_access` (`detector/m1/contract.py:578`) và luồng `--final-eval --reason`
  trong `detector/m1/cli.py`.

## 2. Viết chương trình chấm test cuối (code, test, QA nguồn)

File mới:
- `detector/m1/d1_final_evaluation_r1.py`
- `detector/tests/test_d1_final_evaluation_r1.py`
- `docs/review/d1_final_evaluation_r1_implementation_record.md`
- `docs/review/d1_final_evaluation_r1_source_independent_qa_record.md`

### 2.1 Thứ tự kiểm trước khi chạm vào test (fail closed)

Mọi bước dưới đây phải chạy và PASS **trước** khi đọc bất kỳ byte nào của test:
1. **Record khóa và sidecar R3:** đọc qua reader của bộ khóa R3, và verifier phải PASS. Record phải có đúng 2
   candidate (seed 20261018, 20261019), một bộ `(confidence, nms_iou, agnostic_nms)` chung,
   `status: LOCKED_ON_VAL`, `sealed_test_seen=false`.
2. **Record Owner duyệt record khóa:** có tồn tại, khớp hash của record khóa.
3. **Record Owner duyệt mở test:** có tồn tại, có nêu lý do, khớp hash của contract đánh giá cuối đã chốt.
4. **Quyết định về mốc D-05 (Q4):**
   - có record Owner nói rõ dùng hay không dùng lần hiệu chỉnh duy nhất;
   - nếu dùng thì đọc mốc mới từ record đó;
   - nếu không có record thì từ chối chạy.
5. **Quyết định về nhãn test:** có record Owner chọn (a) chấm với nhãn hiện có, hoặc (b) rà nhãn test mù đã được
   duyệt riêng. Không có record thì từ chối chạy.
6. **Hash của 2 weight** khớp record khóa. Hash của code chấm và các module dùng lại khớp contract đã chốt.
7. **Nhật ký truy cập:** ghi qua `contract.log_test_access`, hoặc một cơ chế append-only tương đương đã QA. Nếu
   nhật ký đã có một lần mở test thành công cho gói này thì **từ chối** (chỉ được mở một lần).

### 2.2 Chấm điểm (chỉ khi mọi kiểm ở 2.1 PASS)

- Mỗi weight chạy suy luận một lần trên test. Dùng đúng bộ ngưỡng đã khóa, cùng tiền xử lý và imgsz 1280 như
  validation.
- **Mốc D-05 Q2:**
  - mAP50 trên các lớp có box test, mAP50-95;
  - recall bỏ qua lớp ở ngưỡng đã khóa;
  - FP/ảnh;
  - recall lớp quan trọng (Q3) có ≥ 20 box, và recall các lớp khác có ≥ 20 box, theo đúng quy tắc
    "lớp không đạt thì bỏ khỏi hành vi mô phỏng, không làm trượt gate".
- **Chỉ báo cáo** AP-small, phân tích theo độ phân giải, và lớp có dưới 20 box.
- **Thống kê:**
  - lấy **trung bình 2 seed**;
  - báo cáo từng seed và hiệu giữa hai seed;
  - CI 95 % bằng bootstrap theo nhóm D-02, ghi rõ CI này **giữ cố định 2 weight** và không phản ánh dao động
    giữa các seed.
- **Latency Q5** cho 2 weight: M1 Pro MPS, batch 1, 50 lần khởi động, 300 lần đo, gồm cả tiền xử lý,
  suy luận và NMS. Mốc p95 ≤ 100 ms. Bước đo này **không** cần ảnh test, dùng ảnh validation.
- **Output:** một JSON kết quả và một báo cáo, gồm phán quyết từng mốc, các hash, nhật ký truy cập và
  `sealed_test_accessed=true` **chỉ** trong lần chạy thật.

### 2.3 Test bắt buộc (chỉ dữ liệu tổng hợp)

- **Từ chối** khi thiếu hoặc sai bất kỳ điều kiện nào ở 2.1:
  - thiếu record khóa hoặc verifier không PASS;
  - record có 3 candidate, hoặc ngưỡng khác nhau giữa các candidate;
  - thiếu record Owner duyệt khóa, thiếu record duyệt mở test, thiếu quyết định Q4, thiếu quyết định nhãn
    test;
  - hash weight lệch;
  - nhật ký đã có một lần mở test.
- **Chứng minh không đọc test trước khi các kiểm PASS:** ví dụ, một "test giả" mà mọi lệnh đọc đều bị chặn,
  và kiểm rằng không lần đọc nào xảy ra khi một điều kiện bị thiếu.
- **Phép chấm đúng trên dữ liệu tổng hợp:** trung bình 2 seed, quy tắc lớp ≥ 20 box, tính mAP trên các lớp có
  box.

## 3. Chốt contract đánh giá cuối (chỉ khi đủ điều kiện)

**Chỉ viết bản chính thức** `docs/review/d1_final_evaluation_r1_contract.md` khi đã có đủ:
- record khóa đã qua QA **và** đã được Owner duyệt;
- quyết định Q4 của Owner;
- quyết định nhãn test của Owner;
- chương trình chấm ở mục 2 đã qua QA nguồn.

Contract chính thức pin hash của:
- 2 weight;
- record khóa và sidecar;
- các record quyết định;
- code chấm;
- lệnh chạy chính xác.

Sau đó làm QA contract độc lập. **Không** tạo record duyệt mở test: việc đó là của Owner.

Nếu chưa đủ điều kiện thì chỉ làm mục 2, rồi báo Owner còn chờ những gì.

## 4. Điều kiện DỪNG

- Bất kỳ bước nào cần chạm vào test.
- Cần sửa file đã pin hoặc đã QA.
- QA nguồn không PASS sau hai vòng sửa.
- Đặc tả mơ hồ tới mức phải tự quyết một quy tắc chấm: ghi lại và hỏi Owner, không tự quyết.
