# TIP-cb-001: Sửa crash KPI Top CMS SQL params + duplicate callback service

## HEADER
- TIP-ID: TIP-cb-001
- Branch: fix/critical-callbacks
- Project: Dashboard-BCCP
- Module: kpi_callbacks.py, service_callbacks.py
- Depends on: None
- Priority: P0
- Estimated effort: 20 phút

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\fix-critical-callbacks
- Bug refs: H-05 (Top CMS SQL params thiếu), H-08 (duplicate callback name)

## TASK

### kpi_callbacks.py - H-05
Tìm đoạn query Top CMS (~dòng 694-711). Query dùng where_str xuất hiện 2 lần trong SQL, nhưng params chỉ truyền 1 lần. Sửa bằng cách nhân đôi params:
- Nếu params_cur là list: dùng params_cur * 2
- Nếu là tuple: dùng params_cur + params_cur
Đọc code để xác định kiểu trước khi sửa.

### service_callbacks.py - H-08
Tìm vòng lặp make_callbacks(pfx) hoặc for prefix in [...]. Các hàm inner như update_service_table_a, update_service_table_b được define với tên cố định → Dash sẽ báo duplicate.
Sửa bằng cách đặt tên hàm unique với pfx. Đọc kỹ cấu trúc trước khi sửa.

## ACCEPTANCE CRITERIA
Given: User filter địa lý trên KPI
When: Query Top CMS chạy
Then: Không ProgrammingError

Given: App khởi động
When: service_callbacks đăng ký
Then: Không DuplicateCallbackError

## CONSTRAINTS
- KHÔNG thay đổi logic SQL
- KHÔNG thay đổi số outputs
