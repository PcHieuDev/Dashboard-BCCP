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
- **Hoàn thành & Hủy bỏ (Rollback) nhánh `feat-ux-filters` (06/06/2026 - 07/06/2026)**:
  - Nhánh `feat-ux-filters` ban đầu đã hoàn thành việc tái cấu trúc Topbar (2 hàng), chuyển đổi Manual Load (nút Áp dụng lọc), thêm trang Thống kê Sản phẩm Dịch vụ (SP-DV), và cơ chế chặn lọc >31 ngày đối với trang Khách hàng.
  - Nhánh đã được nghiệm thu đạt **PASS** và gộp (merge) thành công vào nhánh chính `main` (Commit: `6cdb38b`).
  - Sau khi bàn giao, theo yêu cầu của Sếp, hệ thống đã thực hiện **rollback hoàn toàn** bản cập nhật này (Commit revert: `677f029`). Giao diện và logic code của `main` hiện tại đã quay về trạng thái ổn định của **Phase 11**.
- **Sửa lỗi mã hóa tập tin thực thi Batch `.bat` (07/06/2026)**:
  - Khắc phục lỗi Command Prompt không nhận diện được lệnh (`'n'`, `'RE'`, `'cho.'`) do tệp `bat_duong_ham.bat` và `dung_duong_ham.bat` bị mã hóa UTF-16.
  - Đã viết lại và đồng bộ các file script chạy đường hầm này dưới định dạng chuẩn hóa UTF-8 (không BOM)/ASCII, chạy ổn định khi phân quyền UAC của Windows.
- **Sửa lỗi Import CSV Mapping (04/06/2026)**:
  - Khắc phục lỗi `❌ Tệp CSV thiếu cột bắt buộc 'nhom_chinh' làm cột đầu tiên!` do Sếp lưu file CSV từ Excel trên Windows dùng dấu phân tách `;`.
  - Hỗ trợ cả dấu phân tách `;` và `,` khi đọc file CSV trong `import_callbacks.py` và `sync_mappings.py`.
  - Cải tiến logic upload CSV: tự động gộp (merge) danh mục cũ và danh mục mới thay vì ghi đè, bảo toàn dữ liệu khi chỉ thêm dòng mới.
- **Phase 11 (Tối ưu giao diện & Performance - 04/06/2026)**:
  - Sửa logic Top 10 CMS tránh trùng doanh thu (dùng subquery), xóa Area Chart, sửa lỗi logic Tuần 53.
  - Gom 2 card bộ lọc ở Customer Detail thành 1 card Bộ lọc Nâng cao.
  - Tối ưu tải trang Retention cực nhanh bằng cách sửa logic KHHH (chỉ dựa vào tháng T trở đi + Khách hàng mới tháng T).
- **Đường dẫn Workspace hoạt động**:
  - Mã nguồn: `E:\Projects\Dashboard-BCCP`
  - Cơ sở dữ liệu: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- **Cloudflare Tunnel (Truy cập từ xa)**:
  - Tên miền: `dashboard.bdna.io.vn` trỏ về `http://127.0.0.1:8050`.
  - Trạng thái: Dịch vụ Windows Service `cloudflared` đang được điều phối chạy qua script nâng quyền UAC của Sếp.

## Key Decisions & Architecture
- **Mã nguồn tách biệt khỏi OneDrive**: Tránh xung đột đồng bộ OneDrive khi chạy cơ sở dữ liệu và code. Code chính nằm tại `E:\Projects\Dashboard-BCCP`.
- **Phân tách Tài liệu Bàn giao**: 
  - `GEMINI.md` đóng vai trò là tài liệu tóm tắt ngắn gọn nhất để Agent/Nhân sự mới nắm bắt nhanh mục tiêu, techstack và đường dẫn workspace.
  - `project_state.md` lưu trữ toàn bộ chi tiết kỹ thuật chuyên sâu và lịch sử phát triển của dự án.
- **Luồng Import mới**:
  1. Người dùng chọn file -> file được đọc và hiển thị thông tin ở `selected-file-info`, hiện nút Xác nhận.
  2. Người dùng bấm Xác nhận -> Spinner quay, file được ghi tạm, gọi `import_any_excel_file` để tự động phân tích và import (cho cả `.xls` và `.xlsx`).
  3. Kết quả trả về `dbc.Alert` tại `upload-status-message`, đồng thời reset `upload-data` contents để ẩn nút và xóa file info.
- **Cơ chế Gộp danh mục Dịch vụ tự động**: Khi tải lên file CSV để đồng bộ sản phẩm dịch vụ mới, hệ thống sẽ tự động ghép với danh mục hiện tại và khử trùng theo mã dịch vụ (`ma_spdv`) để đảm bảo không bị ghi đè mất các dịch vụ khác. File CSV mapping trên đĩa sẽ được lưu lại dưới dạng chuẩn hóa dấu phẩy `,` và mã hóa `utf-8-sig`.

### Cấu trúc thư mục hiện tại (Sau khi Revert):
```
E:\Projects\Dashboard-BCCP\
├── config/         (settings.py, holidays.py, week_calendar.py) ← DÙNG CHUNG
├── data/           (mapping_spdv.csv, mapping-BC-BDX-Cum.csv)  ← DÙNG CHUNG
├── database/       (bccp.db)                                   ← DÙNG CHUNG
├── etl/            (importer.py, aggregator.py)                ← DÙNG CHUNG
├── analytics/      (revenue.py, customer_classifier.py)        ← DÙNG CHUNG
├── scripts/        (generate_tokens.py, migrate_add_year.py, sync_mappings.py)
├── dash_app/       ← APP CHÍNH (Dash ổn định của Phase 11)
│   ├── app.py              (Khởi chạy & định tuyến tab)
│   ├── assets/style.css    (CSS style)
│   ├── components/         (sidebar.py, kpi_cards.py, data_table.py)
│   ├── callbacks/          (sidebar_callbacks.py, kpi_callbacks.py, customer_callbacks.py, global_callbacks.py, hcc_revenue_callbacks.py, import_callbacks.py, new_customer_callbacks.py, retention_callbacks.py, alerts_callbacks.py, utils.py, export_helpers.py)
│   ├── pages/              (kpi_page.py, customer_detail.py, global_overview.py, hcc_revenue.py, import_data.py, new_customer.py, retention.py, service_overview.py, alerts.py)
│   ├── db/                 (connection.py, auth.py)
│   └── requirements.txt
├── run_dashboard.bat
├── bat_duong_ham.bat       ← Bật Cloudflare Tunnel
├── dung_duong_ham.bat      ← Tắt Cloudflare Tunnel
└── project_state.md
```

### Database Schema:
- `transactions` — ~307K dòng (5 tháng 2026, ~60K/tháng), cột chính: cms, buu_cuc, san_pham_dv, ngay_chap_nhan, cuoc_tt_tong, nam_du_lieu
- `dim_spdv` — Ánh xạ mã SPDV → nhom_dich_vu
- `dim_buucuc` — Ánh xạ mã bưu cục → ten_bdx, ten_cum (18 Cụm)
- `import_log` — Lịch sử import

### Logic phân loại KH (theo tháng, không cộng dồn):
- **Vãng lai**: CMS null / bắt đầu bằng `VANGLAI_`
- **KHM/Tái bán**: Không có phát sinh giao dịch nào trong 3 tháng liền trước.
- **Hiện hữu**: Có phát sinh giao dịch trong 3 tháng liền trước.

## Pending Tasks
1. **[PENDING] Bổ sung dữ liệu**: Chờ Sếp nạp thêm dữ liệu 2 ngày cuối tháng 5 (30.05 - 31.05) và dữ liệu tháng 6 còn thiếu (từ 03/06 trở đi).
2. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.

## Issues & Notes
- **Lỗi không hiển thị Alert khi nạp thành công**: Đã sửa triệt để bằng cách đổi `dismissible` thành `dismissable` trong DBC Alert.
- **Bypass Login**: Hiện tại đang bypass authentication trong `app.py` để phát triển tiện lợi hơn. Cần kích hoạt lại khi deploy chính thức.
- **Lỗi CSV dấu phân tách ';'**: Đã khắc phục triệt để bằng việc hỗ trợ cả `,` và `;` ở tất cả các module đọc CSV mapping.
