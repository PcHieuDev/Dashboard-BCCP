# TIP-topbar-003: Tích hợp topbar vào app.py, thu gọn sidebar

## HEADER
- TIP-ID: TIP-topbar-003
- Branch: feat/topbar-auth
- Project: Dashboard BCCP v2.0
- Module: Integration
- Depends on: TIP-topbar-001, TIP-topbar-002
- Priority: P0
- Estimated effort: 60 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-topbar-auth
- Key files to reference:
  - `dash_app/app.py` → layout chính, serve_layout(), routing, đăng ký callbacks
  - `dash_app/components/sidebar.py` → layout sidebar hiện tại (sẽ cắt bỏ bộ lọc)
  - `dash_app/callbacks/sidebar_callbacks.py` → callbacks bộ lọc cũ (sẽ bỏ phần filter)
  - `dash_app/assets/style.css` → CSS sidebar hiện tại

## TASK
Tích hợp Topbar vào layout chính, tái cấu trúc Sidebar thành menu-only, dọn dẹp callbacks cũ.

## SPECIFICATIONS

### 1. Sửa `dash_app/app.py`

**Import thêm:**
```python
from components.topbar import create_topbar_layout
from callbacks.topbar_callbacks import register_topbar_callbacks
```

**Sửa serve_layout()** — phần layout Dashboard (sau khi đăng nhập):
```python
# Layout hiện tại:
# html.Div([
#     dcc.Location(...),
#     create_sidebar_layout(FILTER_OPTS),  ← sidebar có bộ lọc
#     html.Div([header, page-content], className="content")
# ])

# Layout MỚI:
# html.Div([
#     dcc.Location(...),
#     create_sidebar_layout(),              ← sidebar chỉ menu
#     html.Div([
#         create_topbar_layout(FILTER_OPTS), ← topbar chứa bộ lọc
#         header,
#         page-content
#     ], className="content")
# ])
```

**Đăng ký callbacks:**
```python
register_topbar_callbacks(app)  # Thêm dòng này
```

### 2. Sửa `dash_app/components/sidebar.py`

**Hàm `create_sidebar_layout()`** — BỎ tham số filter_opts (không cần nữa):

Chỉ giữ:
1. **Profile box** (hiện tên user, nút đăng xuất)
2. **Menu điều hướng** — cấu trúc mới:

```
📊 Tổng quan chung                           → /
───────────────────────────────────────
📦 Bưu chính chuyển phát (Accordion)
   ├─ 📈 Tổng quan dịch vụ                   → /bccp
   ├─ 🆕 Khách hàng mới/tái bán              → /bccp/new-customer
   ├─ 🔄 KH hiện hữu                         → /bccp/retention
   ├─ 🔍 Chi tiết khách hàng                  → /bccp/customer
   └─ 📋 Chi tiết sản phẩm dịch vụ           → /bccp/service-detail
───────────────────────────────────────
🏢 Hành chính công
   └─ 📈 Tổng quan dịch vụ                   → /hcc
───────────────────────────────────────
💰 Tài chính Bưu chính
   └─ 📈 Tổng quan dịch vụ                   → /tcbc
───────────────────────────────────────
🛍️ Phân phối bán lẻ
   └─ 📈 Tổng quan dịch vụ                   → /ppbl
```

**BỎ hoàn toàn:**
- Section bộ lọc Thời gian (Năm, Chu kỳ, Ngày/Tuần/Tháng)
- Section bộ lọc Địa lý (Cụm, BĐX, Bưu cục)
- Section So sánh (Radio items kỳ trước/cùng kỳ/KH)
- Nút "🔍 Áp dụng bộ lọc" 
- Section "🚨 Cảnh báo doanh thu"
- Section "📊 Báo cáo doanh thu HCC"

### 3. Sửa `dash_app/callbacks/sidebar_callbacks.py`

BỎ các callbacks:
- Ẩn/hiện container ngày/tuần/tháng (đã chuyển sang topbar_callbacks)
- Cascade Cụm → BĐX → Bưu cục (đã chuyển sang topbar_callbacks)
- Load giá trị mặc định cho bộ lọc (đã chuyển sang topbar_callbacks)

GIỮ LẠI:
- Callback highlight active menu item theo URL
- Callback đăng xuất (btn-logout)
- Bất kỳ callback nào liên quan đến toggle sidebar/accordion

### 4. Sửa `dash_app/assets/style.css`

- Thu gọn `.sidebar` width từ ~280px xuống ~220px
- Thêm styles cho `.topbar-container` (đã định nghĩa ở TIP-topbar-001)
- Cập nhật `.content` margin-left tương ứng với sidebar mới

## ACCEPTANCE CRITERIA
- Given: App khởi chạy, user đăng nhập
- When: Trang load
- Then:
  - Topbar hiển thị ở trên content area với đầy đủ bộ lọc
  - Sidebar chỉ có profile box + menu điều hướng (không có bộ lọc)
  - Sidebar hẹp hơn, content area rộng hơn
  - Menu đúng cấu trúc mới (không có Cảnh báo, không có Dịch vụ cha)
  - Tất cả routes hoạt động (click menu → đúng trang)
  - Không có lỗi callback (Missing Input/Output)
  - Nút Áp dụng trên Topbar hoạt động (trigger các callback trang)

## CONSTRAINTS
- GIỮ NGUYÊN ID `btn-apply-filter` — tất cả page callbacks đang dùng ID này
- GIỮ NGUYÊN dcc.Store `sidebar-compare-mode` ở dạng ẩn nếu callbacks trang cũ còn dùng (sẽ chuyển inline ở nhánh pages-redesign)
- KHÔNG sửa logic callback của các trang (global, kpi, new_customer, retention...)
- Kiểm tra kỹ không có callback nào reference tới component đã bị xóa khỏi sidebar
