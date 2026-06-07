# SCAN REPORT: Dashboard BCCP — Nâng cấp Tổng thể
Generated: 2026-06-07
Type: Existing Codebase → Full Scan

---

## TECH_STACK
- **Language**: Python 3.13
- **Framework**: Dash (Plotly) + dash-bootstrap-components
- **Styling**: Vanilla CSS (`dash_app/assets/style.css`)
- **Database**: SQLite (`E:/OneDrive/z.Database-TTKD-Data/dashboard.db`)
- **Auth**: Flask-Login (`dash_app/db/auth.py`) — model User có thuộc tính `role`, `assigned_cum`
- **State**: Dash `dcc.Store`, `dcc.Location` cho routing
- **Other**: pandas, openpyxl, xlrd>=2.0.1, plotly, sqlite3

## EXISTING_MODULES
- **config/** — Cấu hình hệ thống:
  - `settings.py` (DB_PATH, cấu hình chung)
  - `week_calendar.py` (lịch tuần Thứ 6→Thứ 5, hàm `get_week_list`, `get_prev_period`, `get_same_period_prev_year`)
  - `holidays.py` (ngày lễ VN 2025-2027)
- **data/** — Danh mục ánh xạ:
  - `mapping_spdv.csv` (mã SPDV → nhóm dịch vụ)
  - `mapping-BC-BDX-Cum.csv` (bưu cục → BĐX → Cụm)
- **etl/** — Import & ETL:
  - `importer.py` (35KB — import Excel .xls/.xlsx vào transactions, tự detect format)
- **analytics/** — Logic phân tích nghiệp vụ:
  - `customer_classifier.py` (phân loại KH: Vãng lai, KHM/Tái bán, Hiện hữu — theo tháng)
  - `global_metrics.py` (16KB — doanh thu theo dịch vụ, cơ cấu, YTD, heatmap tăng trưởng)
  - `new_customer_calculator.py` (9.8KB — tính toán & lưu KH mới vào bảng `new_customers`)
  - `retention_metrics.py` (16KB — KHHH, retention stats, biến động tăng/giảm/mất, churn alerts)
  - `revenue.py` (25KB — doanh thu chi tiết BCCP theo nhiều chiều)
- **dash_app/pages/** — Layouts giao diện (10 files):
  - `global_overview.py`, `kpi_page.py`, `service_overview.py`, `customer_detail.py`, `new_customer.py`, `retention.py`, `alerts.py`, `hcc_revenue.py`, `import_data.py`
- **dash_app/callbacks/** — Logic xử lý sự kiện (13 files, tổng ~253KB):
  - `global_callbacks.py` (21KB), `kpi_callbacks.py` (41KB), `new_customer_callbacks.py` (41KB), `retention_callbacks.py` (27KB), `alerts_callbacks.py` (19KB), `customer_callbacks.py` (13KB), `hcc_revenue_callbacks.py` (20KB), `service_callbacks.py` (20KB), `sidebar_callbacks.py` (11KB), `import_callbacks.py` (23KB), `utils.py` (15KB), `export_helpers.py` (20KB)
- **dash_app/components/** — Thành phần giao diện dùng chung:
  - `sidebar.py` (Sidebar + bộ lọc + profile box + accordion menu)
  - `kpi_cards.py`, `data_table.py`
- **dash_app/db/** — Kết nối & xác thực:
  - `connection.py`, `auth.py` (Flask-Login User model)
- **scripts/** — Scripts tiện ích (8 files):
  - `generate_tokens.py`, `init_users_db.py`, `sync_mappings.py`, các migrate scripts

## PATTERNS_DETECTED
- **Routing**: `dcc.Location` + callback `render_page()` trong `app.py` — dispatch layout theo pathname
- **Auth**: Flask-Login + `current_user` — bypass tạm thời ở dev; user có `role` (admin/user/cluster_viewer) và `assigned_cum`
- **DB Connections**: Mỗi hàm callback/analytics mở `sqlite3.connect()` riêng, không dùng connection pool
- **Filter Flow**: Sidebar chứa cả bộ lọc thời gian + địa lý + so sánh → nút "Áp dụng" → trigger callback qua `btn-apply-filter`
- **Callback Pattern**: Mỗi trang đăng ký callbacks riêng qua hàm `register_xxx_callbacks(app)` trong `app.py`
- **Tương thích ngược**: Input ẩn `tabs-navigation` để callback cũ BCCP hoạt động khi chuyển sang URL routing

## REUSABLE_COMPONENTS
- **Sidebar**: `dash_app/components/sidebar.py` — Cần tái cấu trúc lớn (chuyển lên topbar)
- **KPI Cards**: `dash_app/components/kpi_cards.py` — Tái sử dụng được
- **Data Table**: `dash_app/components/data_table.py` — Tái sử dụng được
- **Hàm `format_revenue()`**: `callbacks/utils.py` — Tái sử dụng được
- **Export helpers**: `callbacks/export_helpers.py` — Tái sử dụng cho xuất Excel

## DATABASE SCHEMA (Thực tế — dump từ DB)
| Bảng | Mô tả | Cột chính |
|------|-------|-----------|
| `transactions` | Giao dịch BCCP (~307K dòng) | id, cms, buu_cuc, san_pham_dv, ngay_chap_nhan, san_luong, cuoc_tt_tong, thang_du_lieu, nam_du_lieu |
| `dim_spdv` | Ánh xạ mã SPDV → nhóm_dich_vu | ma_spdv, ten_spdv, nhom_dich_vu |
| `dim_buucuc` | Ánh xạ bưu cục → BĐX → Cụm | ma_bc, ten_buu_cuc, ma_bdx, ten_bdx, ten_cum |
| `dim_holidays` | Ngày lễ | ngay, ten_ngay_le, nam |
| `import_log` | Lịch sử import | batch_id, file_name, thang_du_lieu, so_dong_import |
| `new_customers` | KH mới đã tính toán | cms, thang, nam, buu_cuc, ma_bdx, ten_cum, nhom_dv, tong_doanh_thu |
| `agg_daily_customer` | Tổng hợp ngày theo KH | cms, buu_cuc, ngay, nhom_dich_vu, tong_doanh_thu |
| `agg_weekly` | Tổng hợp tuần theo bưu cục | tuan_so, nam, buu_cuc, nhom_dich_vu, tong_doanh_thu |
| `agg_weekly_customer` | Tổng hợp tuần theo KH | cms, buu_cuc, tuan_bat_dau, nhom_dich_vu, tong_doanh_thu |
| `users` | Tài khoản đăng nhập | id, username, password_hash, role, assigned_cum |
| `access_tokens` | Token truy cập | token, level, value |

| `transactions_hcc` | Giao dịch HCC | ma_buu_cuc, doanh_thu, nam_du_lieu, thang_du_lieu |
| `transactions_tcbc` | Giao dịch TCBC | ma_buu_cuc, doanh_thu, nam_du_lieu, thang_du_lieu |
| `transactions_ppbl` | Giao dịch PPBL | ma_buu_cuc, doanh_thu, nam_du_lieu, thang_du_lieu |
| `transactions_phbc` | Giao dịch PHBC | (cấu trúc tương tự) |
| `plans` | Kế hoạch doanh thu | nhom_dich_vu, ma_buu_cuc, nam, thang, ke_hoach_doanh_thu |
| `plans_new_customer` | Kế hoạch KH mới | (cần xác nhận cấu trúc) |
| `dim_dichvu` | Danh mục dịch vụ chi tiết | ma_dich_vu, ten_dich_vu, nhom_chinh, nhom_dich_vu |

> **Thống kê dung lượng thực tế:**
> - `transactions`: **997,152 dòng**
> - `agg_weekly`: 19,080 dòng
> - `agg_weekly_customer`: 75,576 dòng
> - `agg_daily_customer`: 218,700 dòng
> - `agg_monthly` / `agg_monthly_customer`: **CHƯA TỒN TẠI** → cần tạo mới

## GAPS_DETECTED
1. **Bộ lọc theo Ngày**: Còn tồn tại trong sidebar (`DatePickerRange`) nhưng yêu cầu mới là bỏ hoàn toàn.
2. **Bộ lọc nằm ở Sidebar**: Chiếm diện tích lớn, chưa di chuyển lên Topbar — ảnh hưởng trải nghiệm trên màn hình nhỏ.
3. **Phân quyền Topbar**: `assigned_cum` chỉ khóa dropdown Cụm ở sidebar, chưa triển khai ở topbar.
4. **Định nghĩa KH mới**: Hiện tại `customer_classifier.py` dùng logic "không có giao dịch trong 3 tháng trước" (đúng), nhưng **chưa kiểm tra điều kiện "doanh thu dương"** → cần cập nhật thêm điều kiện `cuoc_tt_tong > 0`.
5. **Định nghĩa Churn**: Hiện `retention_metrics.py` dùng "KHHH tháng T-1 không phát sinh ở tháng T" → Yêu cầu mới: "3 tháng gần nhất có doanh thu, tháng này không có".
6. **Định nghĩa Duy trì (Ổn định)**: Hiện tại chỉ check `dt_curr == dt_prev` → Yêu cầu mới thêm: **doanh thu phải dương**.
7. **Bảng summary tháng**: Chưa có `agg_monthly` hay `agg_monthly_customer` — dữ liệu lịch sử theo tháng chưa được pre-aggregate.
8. **Kế hoạch tuần**: Chưa có logic phân bổ kế hoạch tháng → tuần theo ngày lịch.
9. **Bảng `agg_monthly`**: Chưa tồn tại → cần tạo mới để pre-aggregate dữ liệu lịch sử theo tháng.
10. **Trang chi tiết sản phẩm dịch vụ**: Từng được thiết kế ở nhánh `feat-ux-filters` (đã rollback) → cần khôi phục.
11. **Trang /hcc, /tcbc, /ppbl**: Chỉ có template `service_overview.py` chung → cần tái cấu trúc theo dạng "Tổng quan dịch vụ" giống trang chính.

## CODE_HEALTH
- **Type Safety**: Partial (dùng type hints ở một số hàm, không toàn bộ)
- **Linting**: Configured (utf-8 headers, docstrings)
- **Tests**: 2 files (`verify_phase6.py`, `check_hcc_db.py`) — test coverage thấp
- **Debug Artifacts**: Clean (không thấy console.log/print thừa)
- **TODO/FIXME**: 2 found
  - Bypass auth trong `app.py` (cần kích hoạt lại khi deploy)
  - Chuyển đổi sang PostgreSQL khi deploy server

## ESTIMATED_SIZE
- **Files**: ~35 files (Python) + CSS + CSV
- **Lines of Code**: ~10,000 lines
- **Components/Modules**: 10 page layouts, 13 callback modules, 5 analytics modules
- **Entry Points**: `dash_app/app.py` (Dash server), 9 URL routes

## COMPLEXITY_ASSESSMENT: **Medium** (DB + auth, multi-page, team scale, phân quyền theo vai trò)
