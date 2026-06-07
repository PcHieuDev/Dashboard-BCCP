# Project State - Dashboard Doanh thu BCCP

## Project Goal
Dashboard doanh thu bưu chính chuyển phát (BCCP) hỗ trợ bộ lọc đa chiều, phân loại khách hàng tự động, import dữ liệu từ Excel vào SQLite. Phục vụ **20+ người dùng** từ nhiều phòng ban, dự kiến deploy lên **server nội bộ**.

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đã chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite (đang lưu trữ đồng bộ trên OneDrive) -> PostgreSQL khi deploy server
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl, xlrd>=2.0.1 (đọc file .xls)
- **Encoding**: UTF-8 toàn bộ

## Current State
- **Tái cấu trúc bộ lọc & Phân quyền Cụm (07/06/2026)**:
  - Loại bỏ hoàn toàn bộ lọc ngày (DatePickerRange), tích hợp bộ lọc Tuần/Tháng ngang (Topbar) cho trang Tổng quan và BCCP.
  - Phân quyền Cụm: Khóa cứng dropdown Cụm đối với tài khoản được gán Cụm cụ thể, nhưng cho phép chọn sâu hơn ở BĐX và mã Bưu cục.
  - Sidebar được thu gọn từ 320px về 220px, chỉ chứa thông tin tài khoản và menu Accordion điều hướng.
- **Tối ưu hiệu năng bằng Summary Tables (07/06/2026)**:
  - Xây dựng các bảng tổng hợp trung gian: `agg_monthly`, `agg_monthly_customer` (theo bưu cục/khách hàng) và `plans_weekly` (phân bổ kế hoạch tuần theo số ngày trong tháng).
  - Tự động cập nhật bảng summary tương ứng ngay sau khi import file Excel mới (cả RAW CAS và Template).
  - Cập nhật logic Khách hàng mới (`new_customers`): Chỉ tính các giao dịch có doanh thu dương `cuoc_tt_tong > 0` và thêm cột `ngay_phat_sinh` (ngày giao dịch đầu tiên trong tháng).
  - Chạy thành công tác vụ rebuild dữ liệu lịch sử từ T10/2025 đến T06/2026.
- **Đường dẫn Workspace hoạt động**:
  - Mã nguồn: `E:\Projects\Dashboard-BCCP`
  - Cơ sở dữ liệu: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- **Cloudflare Tunnel (Truy cập từ xa)**:
  - Tên miền: `dashboard.bdna.io.vn` trỏ về `http://127.0.0.1:8050`
  - Trạng thái: Windows Service `cloudflared` đang hoạt động ổn định.

## Key Decisions & Architecture
- **Mã nguồn tách biệt khỏi OneDrive**: Tránh xung đột đồng bộ OneDrive khi chạy cơ sở dữ liệu và code. Code chính nằm tại `E:\Projects\Dashboard-BCCP`.
- **Cơ chế Summary Tables**: Để tối ưu hiệu năng cho tập dữ liệu ~1 triệu dòng, các trang Tổng quan và BCCP sẽ đọc dữ liệu từ các bảng tổng hợp trước thay vì quét toàn bộ bảng transactions.
- **Phân bổ kế hoạch tuần**: Kế hoạch tuần được phân bổ theo tỷ lệ số ngày của tuần nằm trong tháng tương ứng (tính trên tổng số ngày của tháng đó).

### Cấu trúc thư mục hiện tại:
```
E:\Projects\Dashboard-BCCP\
├── config/         (settings.py, holidays.py, week_calendar.py) ← DÙNG CHUNG
├── data/           (mapping_spdv.csv, mapping-BC-BDX-Cum.csv)  ← DÙNG CHUNG
├── database/       (bccp.db)                                   ← DÙNG CHUNG
├── etl/            (importer.py, aggregator.py)                ← DÙNG CHUNG
├── analytics/      (revenue.py, customer_classifier.py, new_customer_calculator.py) ← DÙNG CHUNG
├── scripts/        (generate_tokens.py, migrate_add_year.py, sync_mappings.py, rebuild_summaries.py)
├── dash_app/       ← APP CHÍNH (Dash modularized)
│   ├── app.py              (Khởi chạy & định tuyến tab)
│   ├── assets/style.css    (CSS style)
│   ├── components/         (sidebar.py, topbar.py, kpi_cards.py)
│   ├── callbacks/          (sidebar_callbacks.py, topbar_callbacks.py, kpi_callbacks.py, customer_callbacks.py, import_callbacks.py)
│   ├── pages/              (kpi_page.py, customer_detail.py, global_overview.py, hcc_revenue.py, import_data.py, new_customer.py, retention.py)
│   └── db/                 (connection.py, auth.py)
├── run_dashboard.bat
└── project_state.md
```

### Database Schema:
- `transactions` — ~1 triệu dòng (dữ liệu 2025 và 2026), cột chính: cms, buu_cuc, san_pham_dv, ngay_chap_nhan, cuoc_tt_tong, nam_du_lieu
- `agg_monthly` — Tổng hợp doanh thu, sản lượng, số KH phát sinh theo tháng, bưu cục, nhóm dịch vụ.
- `agg_monthly_customer` — Tổng hợp doanh thu, sản lượng, số giao dịch theo tháng, bưu cục, khách hàng (CMS), nhóm dịch vụ.
- `plans_weekly` — Kế hoạch tuần phân bổ từ kế hoạch tháng.
- `new_customers` — Khách hàng mới theo tháng, có thêm cột `ngay_phat_sinh` và chỉ ghi nhận khách hàng có doanh thu dương.
- `dim_spdv` / `dim_dichvu` — Ánh xạ mã SPDV → nhóm dịch vụ.
- `dim_buucuc` — Ánh xạ mã bưu cục → ten_bdx, ten_cum (18 Cụm).

### Logic phân loại KH (theo tháng, không cộng dồn):
- **Vãng lai**: CMS null / bắt đầu bằng `VANGLAI_` / 'none'
- **KHM/Tái bán**: Không có phát sinh giao dịch nào có doanh thu dương trong 3 tháng liền trước.
- **Hiện hữu**: Có phát sinh giao dịch có doanh thu dương trong 3 tháng liền trước.

## Pending Tasks
1. **[IN PROGRESS] Phase 3: Redesign các trang hiển thị (nhánh 3)**: Chuyển đổi các trang `kpi_page.py`, `new_customer.py`, `retention.py`, `customer_detail.py` sang đọc dữ liệu từ các bảng summary mới và điều chỉnh layout theo Topbar/Sidebar mới.
2. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.

## Issues & Notes
- **RBAC & Authentication**: Chức năng phân quyền đã hoạt động ổn định trên Topbar. Hỗ trợ test login nhanh qua route `/test-login/<username>`.
- **Database Lock**: Do SQLite sử dụng khóa độc quyền khi viết, trong quá trình chạy script `rebuild_summaries.py` (khoảng 7 phút), database sẽ tạm thời khóa tất cả các truy cập đọc/ghi khác.

