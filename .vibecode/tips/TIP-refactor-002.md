# TIP-refactor-002: Thiết lập môi trường Pytest và test mẫu

## HEADER
- TIP-ID: TIP-refactor-002
- Branch: feat/refactor-code-quality
- Project: Dashboard BCCP
- Module: Testing
- Depends on: TIP-refactor-001
- Priority: P1
- Estimated effort: 25 minutes

## CONTEXT
- Cần tạo môi trường kiểm thử cơ bản để sau này phát triển các bộ test sâu hơn.

## TASK
1. Cập nhật `requirements.txt`: Thêm `pytest` và `pytest-cov`.
2. Tạo thư mục `tests/` ở thư mục gốc.
3. Tạo file `tests/conftest.py` chứa các fixtures cơ bản (chưa cần code quá sâu, chỉ cần khởi tạo file).
4. Tạo file `tests/unit/test_analytics.py`: Viết 1-2 bài test mẫu đơn giản (ví dụ: test một hàm tính toán hoặc hàm tiện ích nào đó trong project).
5. Tạo file `tests/integration/test_etl.py`: Viết 1 bài test giả lập gọi hàm khởi tạo DB SQLite ảo.
6. Tạo file `chay_kiem_thu.bat` ở thư mục gốc chứa dòng lệnh chạy `pytest tests/ -v`. File cần được lưu đúng mã hóa tiếng Việt hoặc không dấu (để chạy trên cmd).

## ACCEPTANCE CRITERIA
Given: Môi trường có cài đặt `pytest`.
When: Sếp chạy file `chay_kiem_thu.bat`.
Then: Terminal hiển thị kết quả chạy test mẫu (Passed) màu xanh, không báo lỗi thiếu thư viện hay lỗi module không tìm thấy.
