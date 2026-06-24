# TIP-app-001: Bảo mật route test-login + sửa thứ tự khai báo logger + chuẩn hóa logger level

## HEADER
- TIP-ID: TIP-app-001
- Branch: fix/critical-app
- Project: Dashboard-BCCP
- Module: dash_app/app.py
- Depends on: None
- Priority: P0
- Estimated effort: 15 phút

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\fix-critical-app
- Key files: dash_app/app.py
- Bug refs: C-05 (logger dùng trước khai báo), C-06 (route test-login), C-07 (logger.error cho thành công)

## TASK
1. C-06: Xóa hoàn toàn route /test-login/<username> (dòng ~113-123 trong app.py)
2. C-05: Di chuyển block khởi tạo logger lên trước hàm log_user_action (~dòng 90)
3. C-07: Đổi logger.error() → logger.info() cho thông báo đăng nhập/đăng xuất thành công

## SPECIFICATIONS
- Không thay đổi bất kỳ logic nào khác trong app.py
- Không thêm import mới ngoài việc di chuyển block logger

## ACCEPTANCE CRITERIA
Given: App đang chạy
When: User đăng nhập → đăng xuất
Then: Log chỉ có INFO, không có ERROR giả; route /test-login/ không tồn tại; không NameError khi logger được gọi sớm

## CONSTRAINTS
- KHÔNG sửa bất kỳ callback nào
- KHÔNG thay đổi cấu hình Flask/Dash
