# PROJECT CONTEXT: Dashboard BCCP (Refactoring)
Generated: 2026-06-11 | For: Builder

## 1. Project Overview
Dự án Dashboard doanh thu BCCP (Dash). Mục tiêu hiện tại là nâng cấp chất lượng mã nguồn (Code Quality Refactoring) bằng cách thay thế các lệnh in `print()` thô sơ bằng hệ thống `logging` chuẩn, thiết lập môi trường kiểm thử tự động `pytest`, và áp dụng `flake8` để kiểm soát lỗi cú pháp. Không thay đổi giao diện UI hay cấu trúc database.

## 2. Tech Stack & Conventions
- Language: Python 3.13
- Framework: Dash
- Database: SQLite
- Testing: pytest
- Linting: flake8
- Logging: Python's built-in `logging` module

## 3. Architecture (summary)
Hệ thống được chia thành:
- `dash_app/`: Frontend & Callbacks
- `etl/`: Pipeline xử lý dữ liệu Excel -> SQLite
- `analytics/`: Xử lý logic nghiệp vụ và query DB
- Khung Logging mới sẽ nằm ở `config/logger.py` và được import ở khắp nơi.
- Khung Testing mới sẽ nằm ở `tests/` chạy độc lập ngoài thư mục code.

## 4. Key Decisions (from RRI)
| Decision | Chosen | Rationale |
|----------|--------|-----------|
| Thư viện Test | pytest | Chuẩn ngành, dễ thiết lập, xuất report dễ nhìn |
| Thư mục Log | logs/ | Tách biệt khỏi thư mục code, dễ dàng dọn dẹp |
| File cấu hình Lint | .flake8 | Linh hoạt, cấu hình tắt các cảnh báo không cần thiết |

## 5. Patterns to Follow
- Logging: Sử dụng `from config.logger import get_logger`, sau đó `logger = get_logger(__name__)` ở đầu mỗi file. Tránh dùng `print()`.
- Testing: Viết các hàm bắt đầu bằng chữ `test_`, lưu file bắt đầu bằng `test_`. Dùng fixture trong `conftest.py` thay vì lặp lại code setup.
