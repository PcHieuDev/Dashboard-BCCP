# TIP-fix-001: Sửa Sidebar Active Menu (Bug #2)

## Header
- **TIP-ID**: TIP-fix-001
- **Branch**: feat/ui-fixes
- **Module**: callbacks/sidebar
- **Dependencies**: Không
- **Priority**: P0 (crash ngầm, ảnh hưởng toàn UX)
- **Estimated effort**: Small

## Bối cảnh & Root Cause
Sau Phase 8, `pages/charts.py` và `pages/revenue_detail.py` đã bị xóa, thêm 2 trang mới.
`sidebar_callbacks.py` chưa cập nhật → Output trỏ vào IDs không tồn tại, thiếu IDs mới.

### IDs lỗi hiện tại trong Output list:
```python
# CÒN TRONG CALLBACK nhưng KHÔNG CÒN trong sidebar.py:
Output("nav-bccp-revenue", "className"),
Output("nav-bccp-charts", "className"),
Output("nav-tcbc-revenue", "className"),   # Kiểm tra thêm
Output("nav-ppbl-revenue", "className"),   # Kiểm tra thêm

# CÓ TRONG sidebar.py nhưng THIẾU trong callback:
Output("nav-bccp-new-customer", "className"),
Output("nav-bccp-retention", "className"),
```

## Thay đổi cần thực hiện

### File: `dash_app/callbacks/sidebar_callbacks.py`

**Bước 1 — Cập nhật Output list:**

Thay thế toàn bộ Output list của `update_sidebar_state` thành:
```python
[Output("sidebar-filters-container", "style"),
 Output("sidebar-accordion", "active_item"),
 Output("nav-global-overview", "className"),
 Output("nav-bccp-kpi", "className"),
 Output("nav-bccp-customer", "className"),
 Output("nav-bccp-new-customer", "className"),   # MỚI (Phase 8)
 Output("nav-bccp-retention", "className"),       # MỚI (Phase 8)
 Output("nav-bccp-alerts", "className"),
 Output("nav-hcc-overview", "className"),
 Output("nav-hcc-revenue", "className"),
 Output("nav-tcbc-overview", "className"),
 Output("nav-ppbl-overview", "className"),
 Output("bccp-extra-filters", "style")]           # Giữ nếu còn
```

**Bước 2 — Cập nhật dict `classes` và logic if/elif:**

Xóa các key cũ không còn:
- `classes["bccp-rev"]` (map với nav-bccp-revenue)
- `classes["bccp-chart"]` (map với nav-bccp-charts)
- `classes["tcbc-rev"]`, `classes["ppbl-rev"]` (nếu không còn IDs tương ứng)

Thêm key mới:
```python
# Trong branch elif pathname.startswith('/bccp'):
classes["bccp-new-cust"] = f"sidebar-menu-item active active-bccp" if pathname == "/bccp/new-customer" else "sidebar-menu-item"
classes["bccp-ret"] = f"sidebar-menu-item active active-bccp" if pathname == "/bccp/retention" else "sidebar-menu-item"
```

**Bước 3 — Cập nhật return statement** cho đúng thứ tự Output:
```python
return [
    filters_style,
    active_accordion,
    classes["global"],
    classes["bccp-kpi"],
    classes["bccp-cust"],
    classes["bccp-new-cust"],   # MỚI
    classes["bccp-ret"],         # MỚI
    classes["bccp-alert"],
    classes["hcc-over"],
    classes["hcc-rev"],
    classes["tcbc-over"],
    classes["ppbl-over"],
    bccp_extra_style,
]
```

> ⚠️ Thợ phải đọc file thực tế `sidebar_callbacks.py` để biết tên key dict, thứ tự return chính xác trước khi sửa!

## Acceptance Criteria
```gherkin
Given người dùng đang ở /hcc
Then accordion BCCP KHÔNG mở rộng/tô đậm
And accordion HCC được mở rộng + active-hcc

Given người dùng đang ở /bccp/new-customer
Then nav link "Khách hàng mới" highlight active-bccp
And accordion BCCP mở rộng

Given người dùng đang ở /bccp/retention
Then nav link "KH hiện hữu" highlight active-bccp

Given người dùng đang ở /
Then accordion nào cũng không active
And nav-global-overview highlight active
```
