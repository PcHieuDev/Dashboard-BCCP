# TIP-pages-001: Trang Tổng quan chung (layout + callbacks mới)

## HEADER
- TIP-ID: TIP-pages-001
- Branch: feat/pages-redesign
- Project: Dashboard BCCP v2.0
- Module: Pages / Callbacks
- Depends on: feat/db-summary (summary tables), feat/topbar-auth (topbar)
- Priority: P0
- Estimated effort: 90 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign
- Key files to reference:
  - `dash_app/pages/global_overview.py` → layout hiện tại (sẽ viết lại)
  - `dash_app/callbacks/global_callbacks.py` → callbacks hiện tại (sẽ viết lại)
  - `analytics/global_metrics.py` → hàm tính toán (sẽ sửa đọc từ summary)
  - `dash_app/callbacks/utils.py` → `format_revenue()`
  - `config/week_calendar.py` → `get_week_list()`, `get_prev_period()`, `get_same_period_prev_year()`
  - `config/settings.py` → SERVICE_GROUPS, SERVICE_COLORS, SERVICE_TABLES

## TASK
Tái cấu trúc hoàn toàn trang Tổng quan chung theo wireframe mới.

## SPECIFICATIONS

### Layout mới (từ trên xuống dưới):

#### Section 1: KPI Cards — 4 nhóm dịch vụ
- 4 cards ngang: BCCP, HCC, TCBC, PPBL
- Mỗi card hiển thị:
  - Tên nhóm DV + Tổng doanh thu kỳ hiện tại
  - ▲/▼ % vs Kỳ trước (so với kỳ liền trước: tuần trước hoặc tháng trước)
  - ▲/▼ % vs Cùng kỳ (cùng tuần/tháng năm trước)
  - 🎯 % vs Kế hoạch (doanh thu / kế hoạch × 100)
- LUÔN hiển thị cả 3 chỉ tiêu — không cần bộ lọc so sánh

#### Section 2: Top 10 Bưu điện xã/phường
- 3 bảng ngang (dbc.Row, 3 dbc.Col):
  - Bảng 1: Top 10 vs Kỳ trước (% tăng trưởng)
  - Bảng 2: Top 10 vs Cùng kỳ (% tăng trưởng)
  - Bảng 3: Top 10 vs Kế hoạch (% hoàn thành)
- Mỗi bảng cột: Tên cụm | Tên xã | Chỉ số %
- Chỉ xét xã có doanh thu dương ở cả kỳ hiện tại và kỳ so sánh (tránh chia 0)
- Sắp xếp giảm dần theo %

#### Section 3: Biểu đồ doanh thu theo kỳ
- Biểu đồ cột stacked (plotly): 12 kỳ liên tiếp đến kỳ hiện tại
  - Nếu lọc Tháng → 12 tháng gần nhất
  - Nếu lọc Tuần → 12 tuần gần nhất
- Mỗi cột chia theo nhóm DV (BCCP, HCC, TCBC, PPBL) với SERVICE_COLORS
- Trục X: label kỳ (T01/2026 hoặc Tuần 12)

#### Section 4: 2 Bảng doanh thu chi tiết
- **Bảng A: Kỳ hiện tại** — chi tiết theo XÃ (không theo Cụm)
  - Inline filter: dbc.Checklist ["Kỳ trước", "Cùng kỳ", "Kế hoạch"], mặc định check "Kế hoạch"
  - Cột: Tên cụm | Tên xã | DT BCCP | DT HCC | DT TCBC | DT PPBL | Tổng DT | % So sánh (theo filter đã chọn)
  - Sort mặc định: Tên cụm ASC, Tên xã ASC
- **Bảng B: Lũy kế** — cùng cấu trúc nhưng tính lũy kế từ đầu năm đến kỳ hiện tại
  - Inline filter riêng (độc lập với Bảng A)

### Sửa `analytics/global_metrics.py`
- Thêm hàm đọc dữ liệu từ `agg_monthly` / `agg_weekly` thay vì raw transactions
- Hàm `get_top10_by_comparison(conn, period_type, period_value, year, compare_type)` → DataFrame top 10 xã
- Hàm `get_12_periods_revenue(conn, period_type, current_period, current_year)` → DataFrame 12 kỳ
- Hàm `get_period_detail_by_xa(conn, period_type, period_value, year)` → DataFrame chi tiết theo xã
- Hàm `get_ytd_detail_by_xa(conn, period_type, period_value, year)` → DataFrame lũy kế

### Bỏ
- Bản đồ nhiệt (heatmap)
- Bảng chi tiết doanh thu theo Cụm

## ACCEPTANCE CRITERIA
- Given: DB có summary tables, user đăng nhập
- When: Truy cập trang / (Tổng quan chung), chọn Tháng 5/2026
- Then:
  - 4 KPI cards hiện doanh thu + 3 chỉ tiêu so sánh
  - 3 bảng Top 10 hiện dữ liệu xã, sắp xếp đúng
  - Biểu đồ 12 tháng hiện stacked bar
  - 2 bảng chi tiết theo xã hoạt động, inline filter chuyển đổi được
- When: Chuyển Chu kỳ sang Tuần, chọn Tuần 20
- Then: Tất cả section tự cập nhật theo tuần

## CONSTRAINTS
- Dùng prefix ID `global-` cho tất cả component mới
- BỎ hoàn toàn dependency vào `sidebar-compare-mode` — dùng inline checklist riêng
- Đọc từ summary tables — KHÔNG query trực tiếp bảng transactions
- Fallback: nếu summary chưa có dữ liệu → hiện "—" và thông báo nhẹ
