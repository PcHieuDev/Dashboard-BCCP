# BLUEPRINT: Dashboard BCCP (Nâng cấp Code)
## Vibe Coding 8-Step v6.0

### PROJECT INFO
| Field | Value |
|-------|-------|
| Project | Dashboard BCCP - Giai đoạn Nâng cấp Code Quality |
| Nature | Tooling, Logging, Testing |
| Date | 2026-06-11 |

### GOALS
**Primary Goal:** Thay thế `print()` bằng hệ thống `logging` chuẩn, thiết lập nền tảng kiểm thử tự động (`pytest`), và cấu hình kiểm soát lỗi chính tả code (`flake8`).
**Target Audience:** Lập trình viên / Đội ngũ bảo trì hệ thống.

### ARCHITECTURE
1. **Logging**: 
   - Module `config/logger.py` cấu hình `RotatingFileHandler` (lưu file `logs/dashboard.log`, giới hạn 5 file x 10MB) và hiển thị log ra console có format.
   - Trích xuất toàn bộ lệnh `print` hiện tại ở các file lõi và thay bằng `logger.info`, `logger.error`.
2. **Testing**: 
   - Thư mục `tests/` với `conftest.py` (fixtures cấu hình DB test).
   - Tách riêng `tests/unit/` (kiểm tra logic) và `tests/integration/` (kiểm tra luồng nhập liệu).
3. **Linting**:
   - Khởi tạo `.flake8` để áp chuẩn PEP8 một cách mềm dẻo (bỏ qua cảnh báo dòng dài, chỉ tập trung bắt lỗi cú pháp nguy hiểm).

### TECH STACK
- Python 3.13 (Hiện có)
- `logging` (Thư viện tích hợp sẵn của Python)
- `pytest`, `pytest-cov` (Mới)
- `flake8` (Mới)

### FILE STRUCTURE
```
├── config/logger.py              [NEW]
├── logs/dashboard.log            [NEW]
├── tests/                        [NEW]
│   ├── conftest.py               [NEW]
│   ├── integration/test_etl.py   [NEW]
│   └── unit/test_analytics.py    [NEW]
├── .flake8                       [NEW]
├── chay_kiem_thu.bat             [NEW]
└── kiem_tra_code.bat             [NEW]
```

### RRI REQUIREMENTS MATRIX
| Blueprint Section | Requirements | Source |
|-------------------|-------------|-----------------|
| Khởi tạo Logging  | REQ-001     | RRI Q#1         |
| Thiết lập Pytest  | REQ-002     | RRI Q#2         |
| Thiết lập Flake8  | REQ-003     | RRI Q#3         |

### TASK DECOMPOSITION PREVIEW
Estimated Tasks: 3
├── TIP-refactor-001: Triển khai hệ thống Logging tập trung
├── TIP-refactor-002: Thiết lập môi trường Pytest và test mẫu
└── TIP-refactor-003: Cấu hình Flake8 và file chạy hàng loạt
Estimated Effort: 60 min

### CHECKPOINT
- [x] Kiến trúc đáp ứng đúng tầm nhìn đề ra.
- [x] Đã phủ kín các yêu cầu từ RRI.
- [x] Kế hoạch chia task hợp lý.

Reply "APPROVED" to proceed.
