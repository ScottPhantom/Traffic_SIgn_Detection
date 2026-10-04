# Google Drive import inventory

Nguồn: `https://drive.google.com/drive/folders/1dlqyygcSmkuZOHhVEjsCU8iMtKWpOFUF`

Ngày nhập local: 2026-10-02 (Asia/Ho_Chi_Minh).

## Artifact chính

| Local path | Drive ID | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `models/VGG16_model.h5` | `18lQG_A4TkDgI27Qh9OLlTT-uVL8xrIlo` | 17,593,732 | `745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565` |
| `data/processed/train.p` | `1JA7NRznLTAzqmKszX2TZapu_oXbCBJAq` | 107,146,452 | `5c319e00df7f45a18761e65dfd47341779c310798a71ea3f371659cc4a63da44` |
| `data/processed/valid.p` | `1yZzkPTqvyEtAFF4h197io8SwLuZ8z5uc` | 13,578,712 | `7d92b991f95cf3bfcc6e35b88bad506b89e562992c1eb6c1034462a9604b6948` |
| `data/processed/test.p` | `1-nYkigBk9sqVkCOi9CjCd3BrS87UZ9PA` | 38,888,118 | `60b6450ffdb227042eb32f28d15fe77f98ad24dd550cc85eb445b8c0e502e470` |
| `data/raw/traffic-signs-data.zip` | `15jJ5_RlD5_YTLLFQuw7EPq8iEzJ19OFH` | 123,524,425 | `0ee14ebdd48b07d73ab9f717c902a233f360eb52c8bf68b554747089809f9c75` |
| `data/raw/archive.zip` | `13PwbTzkkk4RiGGJLdG6q5pp5beCx3AYo` | 641,568,792 | `32d8d84a4862f3a5c4b3a231f15e6a35dd6a671903339a0c41306ae0105a8e05` |
| `notebooks/CPV.ipynb` | `1aejraKseGAkTzHIcNNeM_TLdJLaUkF4l` | 116,708 | `f22949d058d9c8d8a43107c37aa4b3a32c5ff11e5b857158fe93fac786780088` |
| `notebooks/CPV301_EDA.ipynb` | `1ZPULBsTysSaZmUPMMnxRXmAEsRchLdRS` | 1,159,067 | `5cd028b9462eadc04e2e15937a2aeb8aa289228747168591cb0f98552b4c837b` |
| `artifacts/DB_logger.db` | `1NvBfuJ9_aFtF815D5F42Ctk3lFAW0xsO` | 20,480 | `07b89e632aa220dec0b67e3cf398101f4a6d7e88918ee0e0269b23a22e90e300` |

Hai ZIP đã vượt kiểm tra `unzip -tq`. Ba file pickle có checksum trùng manifest EDA hiện có.

## Tài liệu và kết quả

- `docs/CPV301_Project_Planning_Group_01.docx`: export từ Google Docs ID `1pALkQ7B7w2pC7DaSaztFhIyn5COjMY5KYxPIsxFL8fA`.
- `docs/Traffic_Sign_Categories.pptx`: export từ Google Slides ID `13FG3wKWyNipAQN3StTkIXqimSyXIWUVbquRnXLkDjCk`.
- `docs/papers/`: ba PDF nguyên bản từ Drive.
- `results/eda/20260915_131027_811744/`: manifest, findings, CSV và 10 PNG từ Drive.

Trạng thái readback ngày 2026-10-03: ba nhóm tài liệu DOCX/PPTX/PDF ở trên không còn trong
checkout Desktop vì người dùng đã chủ động xóa. Đây là trạng thái mong muốn; không cần restore hay
điều tra thêm. Các ID ở trên chỉ giữ provenance của lần import ban đầu, không phải xác nhận rằng
file hiện đang tồn tại dưới `docs/`.

Các thư mục Drive `model/ml_model` và `model/base_CNN_model_dir` trống tại thời điểm đọc. Nội dung lớp học `16. Split and Merge`, `Bài tập trên lớp` và `.ipynb_checkpoints` không được nhập vào project sản phẩm.
