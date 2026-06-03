# TIP-bccp-006: Trang KHHH Retention (/bccp/retention)

## Header
- **TIP-ID**: TIP-bccp-006
- **Branch**: feat/bccp-upgrade
- **Module**: analytics/retention, pages/retention, callbacks/retention
- **Dependencies**: Không (dùng trực tiếp transactions)
- **Priority**: P0
- **Estimated effort**: Large

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**:
  - `analytics/customer_classifier.py` (tham khảo logic KHHH)
  - `analytics/kpi_metrics.py` (tham khảo cách query)
  - `components/kpi_cards.py` (tái sử dụng)

## Task

### 1. Tạo `analytics/retention_metrics.py`:

**Hàm `get_khhh_list(db_path, nam, thang, cum=None, bdx=None)`:**
- Trả về danh sách CMS là KHHH trong tháng (thang, nam)
- KHHH = CMS có giao dịch trong ÍT NHẤT 1 trong 3 tháng trước (T-3, T-2, T-1)
- Loại vãng lai
- Nếu có bộ lọc cum/bdx → lọc qua dim_buucuc

**Hàm `get_retention_stats(db_path, nam, thang, cum=None, bdx=None)`:**
- Lấy danh sách KHHH tháng trước (T-1): `khhh_prev`
- Lấy CMS phát sinh tháng hiện tại (T): `cms_current`
- Tính:
  - `retained_count`: Số CMS trong khhh_prev mà cũng có trong cms_current
  - `lost_count`: Số CMS trong khhh_prev mà KHÔNG có trong cms_current
  - `retention_rate_sl`: retained_count / len(khhh_prev) × 100
  - `dt_prev`: Tổng DT của khhh_prev trong tháng T-1
  - `dt_retained`: Tổng DT tháng T của những CMS retained
  - `retention_rate_dt`: dt_retained / dt_prev × 100
- Return dict với tất cả chỉ số trên

**Hàm `get_khhh_changes(db_path, nam, thang, cum=None, bdx=None)`:**
- Lấy danh sách KHHH tháng T (không phải T-1)
- Với mỗi CMS KHHH tháng T:
  - DT tháng T
  - DT tháng T-1 (nếu có)
  - Phân loại:
    - **DT tăng**: DT(T) > DT(T-1) > 0
    - **DT giảm**: 0 < DT(T) < DT(T-1)
    - **Mất**: CMS có trong KHHH tháng trước nhưng KHÔNG phát sinh tháng T
- Return: dict {tang: {count, total_dt_change}, giam: {count, total_dt_change}, mat: {count, total_dt_lost}, duy_tri: {count}}

### 2. Tạo `pages/retention.py`:

**Block 1 — KPI Cards (3 thẻ):**
- Tổng KHHH tháng trước (SL mã CMS)
- DT KHHH tháng này (tổng DT tháng T của CMS retained)
- SL Mất (CMS không phát sinh tháng T)

**Block 2 — Chỉ số duy trì (2 cards lớn):**
- Retention Rate SL: X% (Y/Z mã)
- Revenue Retention: X% (Y đ / Z đ)

**Block 3 — Bộ lọc + Bảng biến động:**
- Bộ lọc: Cụm → BĐX (cascade)
- DataTable phân tích biến động:
  - Cột: Loại | Số lượng CMS | Tổng DT thay đổi
  - 4 dòng: 📈 DT tăng | 📉 DT giảm | ❌ Mất | ✅ Duy trì
- Highlight màu theo loại (xanh/đỏ/cam)

### 3. Tạo `callbacks/retention_callbacks.py`:
- Input: sidebar-year, sidebar-month-select, sidebar-cum + dropdown BĐX riêng
- Gọi `get_retention_stats()` và `get_khhh_changes()`
- Callback cascade BĐX

## Specifications
- "KHHH tháng T" = CMS có giao dịch trong 3 tháng (T-3, T-2, T-1)
- "Tháng trước" trong context retention = tháng T-1 (VD: chọn T05 → KHHH T04)
- DT so sánh: DT tháng T vs DT tháng T-1 (của cùng CMS)
- CMS "Mất" = có trong KHHH tháng T-1 nhưng KHÔNG phát sinh giao dịch tháng T

## Acceptance Criteria
```gherkin
Given chọn tháng 5/2026
When callback chạy
Then KHHH = danh sách CMS có giao dịch T02+T03+T04 (3 tháng trước T05)
And Retention rate = % KHHH T04 còn phát sinh T05
And Revenue retention = DT(T05 của KHHH T04) / DT(T04 của KHHH T04)

Given KHHH T04 có 1000 mã, T05 còn 840 phát sinh
Then Retention rate SL = 84%
And SL Mất = 160

Given CMS "X" DT T04 = 5tr, DT T05 = 7tr
Then CMS "X" thuộc nhóm "DT tăng", thay đổi = +2tr

Given chọn Cụm = "Vinh", BĐX = cụ thể
Then tất cả chỉ số chỉ tính cho bưu cục thuộc BĐX đã chọn
```

## Constraints
- Query phải hiệu quả (829K rows) — dùng INDEX nếu cần
- Không thêm dependency mới
