# TIP-bccp-005: Trang Khách hàng mới (/bccp/new-customer)

## Header
- **TIP-ID**: TIP-bccp-005
- **Branch**: feat/bccp-upgrade
- **Module**: pages/new_customer, callbacks/new_customer
- **Dependencies**: TIP-bccp-001 (bảng new_customers phải có)
- **Priority**: P0
- **Estimated effort**: Large

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**:
  - `analytics/new_customer_calculator.py` (từ TIP-001 — query data)
  - `components/kpi_cards.py` (tái sử dụng component KPI)
  - `callbacks/utils.py` (format_revenue)
  - `data/mapping-BC-BDX-Cum.csv` (mapping xã)

## Task

### 1. Tạo `pages/new_customer.py`:
Layout gồm:

**Block 1 — KPI Cards (3 thẻ):**
- Tổng SL KH mới (count CMS trong new_customers)
- Tổng DT bán mới (sum tong_doanh_thu)
- % Đạt KH bán mới (thực tế / plans_new_customer × 100)

**Block 2 — Chi tiết theo Nhóm DV (2 cards):**
- Truyền thống: SL | DT | KH | % Đạt
- TMĐT: SL | DT | KH | % Đạt

**Block 3 — Bộ lọc + Bảng BĐX:**
- Dropdown Cụm (cascade từ sidebar-cum hoặc riêng)
- Dropdown BĐX (lọc theo Cụm đã chọn)
- DataTable:
  - Cột: BĐX | SL KH mới TT | DT TT | KH TT | SL KH mới TMĐT | DT TMĐT | KH TMĐT | Tổng SL | Tổng DT | Tổng KH | % Đạt
  - Dòng cuối: TỔNG CỘNG
  - Phân trang, sort native
- Nút Xuất Excel

### 2. Tạo `callbacks/new_customer_callbacks.py`:

**Callback chính:**
- Input: `sidebar-year`, `sidebar-month-select`, `sidebar-cum` + bộ lọc BĐX riêng
- Query `new_customers` WHERE nam, thang, (ten_cum nếu có)
- Query `plans_new_customer` WHERE nam, thang → JOIN mapping ma_xa = ma_bdx → ten_cum, ten_bdx
- Tính KPI: SL, DT, % đạt KH
- Tính bảng BĐX: GROUP BY ma_bdx, JOIN plans_new_customer

**Callback cascade BĐX:**
- Khi chọn Cụm → lọc danh sách BĐX tương ứng

**Callback Export Excel:**
- Xuất DataTable theo bộ lọc hiện tại

### 3. Mapping quan trọng:
```
new_customers.ma_bdx = plans_new_customer.ma_xa
→ Dùng để so sánh DT thực tế bán mới vs KH bán mới
```

## Specifications
- KH bán mới trong `plans_new_customer` là KH **tháng** (đã phân kỳ từ KH năm)
- Nếu không có KH cho 1 xã → hiển thị "-" (không có KH)
- Bộ lọc Cụm "Tất cả" → hiện tất cả BĐX

## Acceptance Criteria
```gherkin
Given trang /bccp/new-customer hiển thị, chọn T05/2026
When callback chạy
Then KPI cards hiện đúng SL, DT, % đạt KH tháng 5

Given chọn Cụm = "Vinh"
When callback cascade chạy
Then dropdown BĐX chỉ hiện các BĐX thuộc Cụm Vinh
And bảng chỉ hiện dữ liệu Cụm Vinh

Given nhấn "Xuất Excel"
Then file Excel chứa bảng BĐX đã lọc

Given không có KH bán mới cho 1 BĐX
Then cột KH và % Đạt hiện "-"
```

## Constraints
- Tái sử dụng `make_kpi_card_layout()` nếu phù hợp
- Style DataTable theo chuẩn dự án (xem global_callbacks.py)
