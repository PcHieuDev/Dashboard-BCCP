# TIP-pages-003: Trang KH mới (layout + callbacks + logic 3 chỉ số)

## HEADER
- TIP-ID: TIP-pages-003
- Branch: feat/pages-redesign
- Project: Dashboard BCCP v2.0
- Module: Pages / Callbacks
- Depends on: feat/db-summary (TIP-db-003 — cột ngày, DT>0)
- Priority: P0
- Estimated effort: 60 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign
- Key files to reference:
  - `dash_app/pages/new_customer.py` → layout hiện tại
  - `dash_app/callbacks/new_customer_callbacks.py` → callbacks hiện tại
  - `analytics/new_customer_calculator.py` → bảng new_customers (đã sửa ở TIP-db-003)
  - Bảng `new_customers`: schema (cms, thang, nam, buu_cuc, ma_bdx, ten_cum, nhom_dv, tong_doanh_thu, ngay_phat_sinh)

## TASK
Tái cấu trúc trang Khách hàng mới/tái bán theo yêu cầu mới.

## SPECIFICATIONS

### Label toàn trang: "Khách hàng mới/tái bán"

### Section 1: 3 Chỉ số KPI (3 cards ngang)

**Khi lọc THÁNG (ví dụ T05/2026):**
1. **Số KH mới/tái bán trong kỳ** = COUNT từ new_customers WHERE thang = 5 AND nam = 2026 (+ lọc địa lý)
2. **Tổng KH mới/tái bán 4 tháng gần nhất** = COUNT từ new_customers WHERE (thang, nam) IN {T02, T03, T04, T05}/2026 (+ lọc địa lý)
3. **Tổng DT bán mới trong kỳ của KH 4 tháng** = SUM doanh thu trong T05/2026 của các CMS thuộc new_customers 4 tháng gần nhất

**Khi lọc TUẦN (ví dụ Tuần 20, 15/5-21/5):**
1. **Số KH mới trong tuần** = COUNT DISTINCT cms FROM transactions WHERE ngay_chap_nhan BETWEEN '2026-05-15' AND '2026-05-21' AND cms IN (new_customers 4 tháng gần nhất) (+ DT > 0 + lọc địa lý)
2. **Tổng KH mới/tái bán 4 tháng gần nhất** = giữ nguyên (logic tháng)
3. **Tổng DT bán mới trong tuần** = SUM cuoc_tt_tong FROM transactions WHERE ngay_chap_nhan BETWEEN tuần AND cms IN (new_customers 4 tháng)

### Section 2: Bảng danh sách KH mới/tái bán
- Bỏ cột STT
- Cột: Tên cụm | Phường/xã | Bưu cục | CMS | Ngày phát sinh | Nhóm DV | Doanh thu
- Dữ liệu: từ bảng new_customers, lọc theo kỳ và địa lý
- Khi lọc Tháng: hiện KH mới của tháng đó
- Khi lọc Tuần: hiện KH mới 4 tháng gần nhất có phát sinh DT trong tuần đó
- Chuẩn hiển thị: 4 tháng gần nhất (gộp cả 4 tháng trong bảng)
- Sort: Doanh thu giảm dần

### BỎ
- Biểu đồ phân rã dịch vụ
- Phần Kế hoạch (toàn trang)
- Bảng/biểu đồ trend KH mới

### Lọc địa lý
- Đọc từ Topbar: sidebar-cum, sidebar-bdx, sidebar-buu-cuc
- Join new_customers với dim_buucuc để lọc

## ACCEPTANCE CRITERIA
- Given: new_customers có dữ liệu T02-T05/2026
- When: Lọc Tháng T05/2026
- Then: 3 chỉ số hiển thị đúng, bảng Top KH có cột đúng, sort DT giảm dần

- Given: Lọc Tuần 20 (15/5-21/5)
- When: Trang render
- Then: Chỉ số (1) = số CMS mới có DT trong tuần 20, chỉ số (2) giữ 4 tháng, chỉ số (3) = DT trong tuần 20

## CONSTRAINTS
- KHÔNG thêm biểu đồ mới
- KHÔNG hiển thị Kế hoạch KH mới
- Đọc từ bảng new_customers (đã được TIP-db-003 cập nhật), KHÔNG query trực tiếp transactions để tìm KH mới
- Query transactions chỉ để tính DT phát sinh trong tuần cho KH đã xác định
