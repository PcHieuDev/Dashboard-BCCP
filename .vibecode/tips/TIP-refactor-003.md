# TIP-refactor-003: Cấu hình Flake8 và file chạy hàng loạt

## HEADER
- TIP-ID: TIP-refactor-003
- Branch: feat/refactor-code-quality
- Project: Dashboard BCCP
- Module: Linting
- Depends on: TIP-refactor-002
- Priority: P2
- Estimated effort: 15 minutes

## CONTEXT
- Chúng ta muốn phát hiện lỗi cú pháp mà không gây xáo trộn code cũ.

## TASK
1. Tạo file `.flake8` ở thư mục gốc với các cấu hình bỏ qua các lỗi định dạng không quan trọng (ví dụ: `E501` - dòng quá dài, `E402` - module level import not at top). Tập trung bật các lỗi cú pháp nghiêm trọng (F-series).
2. Sửa lỗi cú pháp nghiêm trọng (nếu `flake8` cảnh báo về biến chưa được định nghĩa, hoặc import thừa) ở các file lõi.
3. Tạo file `kiem_tra_code.bat` chứa lệnh `flake8 .` để Sếp tự chạy kiểm tra.

## ACCEPTANCE CRITERIA
Given: Developer đã cài đặt `flake8`.
When: Developer chạy lệnh `kiem_tra_code.bat`.
Then: Flake8 quét thành công mà không văng ra hàng tá lỗi định dạng vặt, chỉ báo cáo các lỗi thực sự đáng chú ý (nếu có).
