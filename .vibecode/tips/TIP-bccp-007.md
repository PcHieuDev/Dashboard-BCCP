# TIP-bccp-007: Sidebar + Routing Cleanup

## Header
- **TIP-ID**: TIP-bccp-007
- **Branch**: feat/bccp-upgrade
- **Module**: components/sidebar, app
- **Dependencies**: TIP-bccp-003, TIP-bccp-004, TIP-bccp-005, TIP-bccp-006
- **Priority**: P1
- **Estimated effort**: Medium

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**:
  - `dash_app/app.py` (routing chính)
  - `dash_app/components/sidebar.py` (menu + filters)

## Task

### 1. Sửa `components/sidebar.py`:

**Menu BCCP mới** (trong AccordionItem "📦 Bưu chính chuyển phát"):
```python
dbc.AccordionItem([
    dcc.Link("📈 KPI & Biểu đồ", href="/bccp", id="nav-bccp-kpi", className="sidebar-menu-item"),
    dcc.Link("🔍 Chi tiết khách hàng", href="/bccp/customer", id="nav-bccp-customer", className="sidebar-menu-item"),
    dcc.Link("🆕 Khách hàng mới", href="/bccp/new-customer", id="nav-bccp-new-customer", className="sidebar-menu-item"),
    dcc.Link("🔄 KH hiện hữu", href="/bccp/retention", id="nav-bccp-retention", className="sidebar-menu-item"),
    dcc.Link("🚨 Cảnh báo doanh thu", href="/bccp/alerts", id="nav-bccp-alerts", className="sidebar-menu-item"),
], title="📦 Bưu chính chuyển phát", item_id="menu-bccp"),
```

**Xóa:**
- Link `/bccp/revenue` (nav-bccp-revenue)
- Link `/bccp/charts` (nav-bccp-charts)
- Block `bccp-extra-filters` (nếu TIP-004 chưa xóa)

### 2. Sửa `app.py`:

**Thêm routes mới** trong hàm `render_page()`:
- `/bccp/new-customer` → `from pages.new_customer import create_new_customer_layout`
- `/bccp/retention` → `from pages.retention import create_retention_layout`

**Xóa routes cũ:**
- `/bccp/revenue`
- `/bccp/charts`

**Register callbacks mới:**
- `from callbacks.new_customer_callbacks import register_new_customer_callbacks`
- `from callbacks.retention_callbacks import register_retention_callbacks`
- Gọi `register_*_callbacks(app)` trong phần đăng ký

**Xóa register callbacks cũ:**
- `register_charts_callbacks` (nếu còn)
- `register_revenue_callbacks` (nếu còn)

### 3. Dọn dẹp file:
Xóa các file đã được gộp (nếu TIP-003 và TIP-004 chưa xóa):
- `dash_app/pages/charts.py`
- `dash_app/pages/revenue_detail.py`
- `dash_app/callbacks/charts_callbacks.py`
- `dash_app/callbacks/revenue_callbacks.py`

### 4. Kiểm tra toàn bộ:
- Chạy `python dash_app/app.py` (hoặc `run_dashboard.bat`)
- Kiểm tra tất cả routes hoạt động
- Kiểm tra sidebar menu hiển thị đúng 5 mục
- Kiểm tra không còn lỗi import

## Acceptance Criteria
```gherkin
Given khởi động Dashboard
When truy cập http://127.0.0.1:8050
Then Dashboard chạy không lỗi

Given kiểm tra Sidebar menu BCCP
Then thấy 5 mục: KPI & Biểu đồ, Chi tiết KH, KH mới, KHHH, Cảnh báo
And KHÔNG thấy "Doanh thu chi tiết" và "Biểu đồ trực quan"

Given truy cập /bccp/new-customer
Then trang KH mới hiển thị đúng

Given truy cập /bccp/retention
Then trang KHHH hiển thị đúng

Given truy cập /bccp/revenue (URL cũ)
Then hiển thị 404 hoặc redirect về /bccp

Given truy cập /bccp/charts (URL cũ)
Then hiển thị 404 hoặc redirect về /bccp
```

## Constraints
- Đây là TIP cuối cùng — phải đảm bảo toàn bộ Dashboard hoạt động ổn định
- Test toàn bộ navigation trước khi commit
