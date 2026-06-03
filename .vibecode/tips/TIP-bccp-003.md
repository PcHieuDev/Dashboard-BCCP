# TIP-bccp-003: Gộp Charts vào trang /bccp

## Header
- **TIP-ID**: TIP-bccp-003
- **Branch**: feat/bccp-upgrade
- **Module**: pages/kpi, callbacks/kpi
- **Dependencies**: Không
- **Priority**: P1
- **Estimated effort**: Medium

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**:
  - `dash_app/pages/kpi_page.py` (layout KPI — SẼ SỬA)
  - `dash_app/pages/charts.py` (layout charts — SẼ XÓA)
  - `dash_app/callbacks/kpi_callbacks.py` (callback KPI — SẼ SỬA)
  - `dash_app/callbacks/charts_callbacks.py` (callback charts — SẼ XÓA)

## Task

### 1. Sửa `pages/kpi_page.py`:
- Giữ nguyên 5 KPI cards ở trên
- Thêm bên dưới 3 biểu đồ (copy layout từ `charts.py`):
  - Row 1: Donut cơ cấu DV (col-4) + Line xu hướng theo ngày (col-8)
  - Row 2: Bar ngang so sánh Cụm (col-12)
- Giữ nguyên các component IDs từ charts.py (hoặc đổi tên phù hợp, miễn không conflict)

### 2. Sửa `callbacks/kpi_callbacks.py`:
- Gộp logic tạo 3 biểu đồ từ `charts_callbacks.py` vào callback chính
- Thêm 3 Output mới cho 3 biểu đồ
- Đảm bảo cùng nhận Input từ sidebar filters

### 3. Xóa file:
- `dash_app/pages/charts.py`
- `dash_app/callbacks/charts_callbacks.py`

### 4. LƯU Ý:
- CHƯA sửa `app.py` routing và `sidebar.py` menu ở TIP này — sẽ làm ở TIP-007
- Nếu cần, tạm comment route cũ trong app.py để tránh lỗi import

## Acceptance Criteria
```gherkin
Given trang /bccp đang hiển thị
When người dùng truy cập
Then thấy 5 KPI cards + 3 biểu đồ (Donut, Line, Bar) trên cùng 1 trang

Given thay đổi bộ lọc tháng/năm/cụm trên sidebar
When callback chạy
Then cả KPI cards và 3 biểu đồ đều cập nhật đúng dữ liệu
```

## Constraints
- Giữ nguyên style/theme hiện tại của biểu đồ
- Không thêm dependency mới
