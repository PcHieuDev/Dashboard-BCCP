# TIP-topbar-002: Tạo topbar_callbacks.py (cascade, phân quyền)

## HEADER
- TIP-ID: TIP-topbar-002
- Branch: feat/topbar-auth
- Project: Dashboard BCCP v2.0
- Module: Callbacks
- Depends on: TIP-topbar-001
- Priority: P0
- Estimated effort: 45 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-topbar-auth
- Key files to reference:
  - `dash_app/callbacks/sidebar_callbacks.py` → callbacks cascade hiện có (sẽ chuyển logic sang topbar)
  - `dash_app/db/auth.py` → User model với `assigned_cum`
  - `config/week_calendar.py` → `get_week_list(year)`
  - `config/settings.py` → DB_PATH

## TASK
Tạo file callbacks mới xử lý logic Topbar: cascade bộ lọc, phân quyền, ẩn/hiện.

## SPECIFICATIONS

### File mới: `dash_app/callbacks/topbar_callbacks.py`

Hàm `register_topbar_callbacks(app)` đăng ký các callback sau:

#### Callback 1: Ẩn/hiện container Tuần/Tháng
- Input: `sidebar-period.value`
- Output: `week-container.style`, `month-container.style`
- Logic: 
  - "Tuần" → hiện week-container, ẩn month-container
  - "Tháng" → ẩn week-container, hiện month-container

#### Callback 2: Cập nhật options Tuần khi đổi Năm
- Input: `sidebar-year.value`
- Output: `sidebar-week-select.options`, `sidebar-week-select.value`
- Logic: Gọi `get_week_list(year)`, tạo options, default = tuần hiện tại hoặc tuần cuối

#### Callback 3: Cascade Cụm → Xã/phường + Bưu cục
- Input: `sidebar-cum.value`
- Output: `sidebar-bdx.options`, `sidebar-bdx.value`, `sidebar-buu-cuc.options`, `sidebar-buu-cuc.value`
- Logic:
  - Nếu Cụm = None/"Tất cả" → hiện tất cả Xã/Bưu cục
  - Nếu Cụm = giá trị cụ thể → query `dim_buucuc WHERE ten_cum = ?` → chỉ hiện Xã/Bưu cục thuộc cụm đó
  - Reset Xã và Bưu cục về None (Tất cả)

#### Callback 4: Cascade Xã/phường → Bưu cục
- Input: `sidebar-bdx.value`
- State: `sidebar-cum.value`
- Output: `sidebar-buu-cuc.options`, `sidebar-buu-cuc.value`
- Logic:
  - Nếu Xã = None/"Tất cả" → hiện tất cả Bưu cục trong Cụm (hoặc tất cả nếu Cụm cũng Tất cả)
  - Nếu Xã = giá trị cụ thể → query `dim_buucuc WHERE ten_bdx = ?` → chỉ hiện Bưu cục thuộc xã đó

#### Callback 5: Phân quyền tài khoản khi load
- Trigger: Khởi tạo (app load)
- Logic:
  - Đọc `current_user.assigned_cum` từ Flask-Login
  - Nếu `assigned_cum` có giá trị (không None, không rỗng):
    - Set `sidebar-cum.value = assigned_cum`
    - Set `sidebar-cum.disabled = True`
    - Set `sidebar-cum.options` chỉ chứa 1 option là cụm được gán
    - Trigger cascade để Xã/Bưu cục chỉ hiện đơn vị trực thuộc
  - Nếu `assigned_cum` rỗng/None → để nguyên (admin xem toàn tỉnh)

### Cách kiểm tra phân quyền
```python
from flask_login import current_user
from flask import has_request_context

def get_user_cum():
    if has_request_context() and current_user.is_authenticated:
        cum = getattr(current_user, 'assigned_cum', None)
        if cum and cum.strip():
            return cum.strip()
    return None
```

## ACCEPTANCE CRITERIA
- Given: User đăng nhập là admin (assigned_cum = None)
- When: Chọn Cụm "Tân Kỳ" → Áp dụng
- Then: Xã/phường chỉ hiện các xã thuộc Tân Kỳ, Bưu cục tương tự

- Given: User đăng nhập có assigned_cum = "Tân Kỳ"
- When: Trang load
- Then: Dropdown Cụm bị disabled, value = "Tân Kỳ", không thể thay đổi

- Given: Chu kỳ = "Tuần"
- When: Render
- Then: Hiện dropdown Tuần, ẩn dropdown Tháng

## CONSTRAINTS
- KHÔNG sửa sidebar_callbacks.py ở TIP này
- KHÔNG sửa app.py ở TIP này
- Dùng `sqlite3.connect(str(DB_PATH))` cho query dim_buucuc
- Đóng connection bằng `finally: conn.close()`
