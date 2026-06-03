# TIP-bccp-004: Gộp Revenue + Bộ lọc DV vào /bccp/customer

## Header
- **TIP-ID**: TIP-bccp-004
- **Branch**: feat/bccp-upgrade
- **Module**: pages/customer, callbacks/customer
- **Dependencies**: Không
- **Priority**: P1
- **Estimated effort**: Large

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**:
  - `dash_app/pages/customer_detail.py` (layout — SẼ SỬA)
  - `dash_app/pages/revenue_detail.py` (layout revenue — SẼ XÓA)
  - `dash_app/callbacks/customer_callbacks.py` (SẼ SỬA)
  - `dash_app/callbacks/revenue_callbacks.py` (SẼ XÓA)
  - `dash_app/components/sidebar.py` (SẼ SỬA — bỏ bộ lọc DV BCCP)

## Task

### 1. Sửa `pages/customer_detail.py`:
Tái cấu trúc layout thành 3 phần:

**Phần A — Bộ lọc DV BCCP (INLINE, đặt ở đầu trang):**
- 4 dropdown/checklist trong 1 Row:
  - Nhóm dịch vụ (Dropdown multi)
  - Loại khách hàng (Checklist: Hiện hữu, KHM/Tái bán, Vãng lai)
  - Trạng thái hợp đồng (Checklist: Có HĐ, Không HĐ)
- Các component IDs mới (tránh conflict với sidebar cũ): `customer-filter-nhom-dv`, `customer-filter-loai-kh`, `customer-filter-hop-dong`

**Phần B — Bảng doanh thu xoay chiều (TỪ revenue_detail.py):**
- 2 Dropdown Group By (chính + phụ) + Nút Xuất Excel
- DataTable doanh thu pivot
- Copy logic từ `revenue_callbacks.py`

**Phần C — Pivot CMS chi tiết (ĐÃ CÓ):**
- Giữ nguyên bảng pivot CMS hiện tại
- Nút Xuất Excel

### 2. Sửa `callbacks/customer_callbacks.py`:
- Gộp logic từ `revenue_callbacks.py` vào
- Callback bộ lọc DV inline → ảnh hưởng cả bảng revenue và pivot CMS
- Export Excel cho cả 2 bảng theo bộ lọc đã chọn

### 3. Sửa `components/sidebar.py`:
- Xóa hoàn toàn block `bccp-extra-filters` (id=`bccp-extra-filters`, lines 219-263)
- Xóa các div chứa `sidebar-nhom-dv`, `sidebar-loai-kh`, `sidebar-hop-dong`

### 4. Xóa file:
- `dash_app/pages/revenue_detail.py`
- `dash_app/callbacks/revenue_callbacks.py`

### 5. LƯU Ý:
- CHƯA sửa routing trong `app.py` — làm ở TIP-007
- Cần giữ callback IDs cũ của sidebar (`sidebar-nhom-dv` etc.) nếu có callback khác đang dùng, hoặc xóa hết nếu không còn ai dùng

## Acceptance Criteria
```gherkin
Given trang /bccp/customer đang hiển thị
When người dùng truy cập
Then thấy bộ lọc DV inline + bảng revenue xoay chiều + bảng CMS pivot

Given chọn Nhóm DV = "TMĐT" trong bộ lọc inline
When callback chạy
Then cả bảng revenue và bảng CMS đều chỉ hiển thị dữ liệu TMĐT

Given nhấn "Xuất Excel"
When export chạy
Then file Excel chứa dữ liệu đã lọc

Given kiểm tra Sidebar
Then KHÔNG còn block "Bộ lọc dịch vụ BCCP"
```

## Constraints
- Giữ nguyên style DataTable hiện tại
- Bộ lọc DV inline không ảnh hưởng các trang khác
