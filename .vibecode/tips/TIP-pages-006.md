# TIP-pages-006: Cập nhật routing app.py + dọn dẹp

## HEADER
- TIP-ID: TIP-pages-006
- Branch: feat/pages-redesign
- Project: Dashboard BCCP v2.0
- Module: Integration
- Depends on: TIP-pages-001, TIP-pages-002, TIP-pages-003, TIP-pages-004, TIP-pages-005
- Priority: P0
- Estimated effort: 30 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign
- Key files to reference:
  - `dash_app/app.py` → routing hiện tại (đã được sửa bởi feat/topbar-auth)

## TASK
Cập nhật routing và imports trong app.py sau khi tất cả trang đã được tái cấu trúc.

## SPECIFICATIONS

### 1. Cập nhật imports trong app.py

**Thêm:**
```python
from pages.service_detail import create_service_detail_layout
from callbacks.service_detail_callbacks import register_service_detail_callbacks
```

**Bỏ:**
```python
# from pages.alerts import create_alerts_page_layout  ← đã xóa
# from callbacks.alerts_callbacks import register_alerts_callbacks  ← đã xóa
```

### 2. Cập nhật routing trong `render_page()`

**Thêm route:**
```python
elif pathname == "/bccp/service-detail":
    return create_service_detail_layout(), "📊 Bưu chính chuyển phát - Chi tiết SPDV"
```

**Bỏ routes:**
```python
# elif pathname == "/bccp/alerts":  ← bỏ
# elif pathname == "/hcc/revenue":  ← gộp vào /hcc
```

### 3. Cập nhật callback registration

**Thêm:**
```python
register_service_detail_callbacks(app)
```

**Bỏ:**
```python
# register_alerts_callbacks(app)  ← bỏ
```

### 4. Cập nhật `sync_url_to_tabs_navigation()`
- Thêm case `/bccp/service-detail`
- Bỏ case `/bccp/alerts`

### 5. Dọn dẹp
- Kiểm tra không có import thừa
- Kiểm tra không có callback reference tới component đã xóa
- Kiểm tra tất cả routes hoạt động
- Cân nhắc bỏ `tabs-navigation` hidden input nếu không còn callback nào dùng

## ACCEPTANCE CRITERIA
- Given: App khởi chạy sau khi merge cả 3 nhánh
- When: Truy cập lần lượt tất cả routes
- Then:
  - `/` → Tổng quan chung (layout mới)
  - `/bccp` → Tổng quan DV BCCP
  - `/bccp/new-customer` → KH mới/tái bán (layout mới)
  - `/bccp/retention` → KH hiện hữu (layout mới)
  - `/bccp/customer` → Chi tiết KH (giữ nguyên)
  - `/bccp/service-detail` → Chi tiết SPDV (mới)
  - `/hcc`, `/tcbc`, `/ppbl` → Tổng quan DV tương ứng
  - `/import` → Import (giữ nguyên)
  - `/bccp/alerts` → 404 (đã xóa)
  - Không có lỗi callback Missing Input/Output
  - Không có import thừa gây warning

## CONSTRAINTS
- TIP này chỉ sửa app.py — KHÔNG sửa page hay callback nào khác
- Chạy app để verify, nếu lỗi → log BLOCKED
