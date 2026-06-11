# TIP-refactor-001: Triển khai hệ thống Logging tập trung

## HEADER
- TIP-ID: TIP-refactor-001
- Branch: feat/refactor-code-quality
- Project: Dashboard BCCP
- Module: Config / All
- Depends on: None
- Priority: P0
- Estimated effort: 20 minutes

## CONTEXT
- Working directory: `E:\Projects\worktrees\Dashboard-BCCP\feat-refactor-code-quality`
- Key files to reference: Toàn bộ các file `.py` có lệnh `print()`.

## TASK
1. Tạo thư mục `logs` ở thư mục gốc (nếu chưa có).
2. Tạo file `config/logger.py` chứa hàm cấu hình `get_logger(name)` sử dụng module `logging` mặc định của Python.
   - Ghi ra console: Dùng định dạng `[%(levelname)s] %(message)s`
   - Ghi ra file: File `logs/dashboard.log`, dùng `RotatingFileHandler` tối đa 5 file, mỗi file 10MB, định dạng `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
3. Quét toàn bộ mã nguồn (.py) để thay thế các lệnh `print(...)` thành `logger.info(...)` hoặc `logger.error(...)` (đối với các dòng báo lỗi). Các file trọng tâm: `app.py`, thư mục `etl/`, thư mục `scripts/`.
4. Không thay thế các dòng `print` trong file `run_dashboard.bat`.

## ACCEPTANCE CRITERIA
Given: App đang chạy và import file.
When: Có lỗi xảy ra hoặc ứng dụng in thông báo.
Then: Nội dung thông báo không chỉ xuất hiện trên màn hình console mà còn được lưu lại vào `logs/dashboard.log` với timestamp chính xác.
Then: Chạy lệnh tìm kiếm `print(` trong các thư mục `dash_app`, `etl`, `analytics`, `scripts` sẽ không còn kết quả nào (trừ những chỗ thực sự bất khả kháng).
