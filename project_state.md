# Project State - Dashboard Doanh thu BCCP

## Project Goal
Dashboard doanh thu bưu chính chuyển phát (BCCP) với bộ lọc đa chiều, phân loại khách hàng tự động, và import dữ liệu từ Excel vào SQLite. Phục vụ **20+ người dùng** từ nhiều phòng ban. Sẽ deploy lên **server nội bộ**.

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đang chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite hiện tại -> PostgreSQL khi deploy server (database-agnostic)
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl, xlrd>=2.0.1
- **Encoding**: UTF-8 toàn bộ

## Current State
- **Sửa lỗi Import CSV Mapping (04/06/2026)**:
  - Khắc phục lỗi `Tệp CSV thiếu cột bắt buộc 'nhom_chinh' làm cột đầu tiên!` do Sếp lưu file CSV từ Excel trên Windows dùng dấu phân tách `;`.
  - Hỗ trợ cả dấu phân tách `;` và `,` khi đọc file CSV trong `import_callbacks.py` và `sync_mappings.py`.
  - Cải tiến logic upload CSV: tự động gộp (merge) danh mục cũ và danh mục mới thay vì ghi đè, bảo toàn dữ liệu khi chỉ thêm dòng mới.
  - Đồng bộ trực tiếp thành công dịch vụ mới `CTN052` của Sếp từ file `template_them_san_pham_dich_vu.csv` vào DB.
- **Phase 11 (Tối ưu giao diện & Performance - 04/06/2026)**: Hoàn thành 4 TIPs.
  - **TIP-11-001**: Sửa logic Top 10 CMS tránh trùng doanh thu (dùng subquery), xóa Area Chart, sửa lỗi logic Tuần 53.
  - **TIP-11-002**: Gom 2 card bộ lọc ở Customer Detail thành 1 card Bộ lọc Nâng cao, tối ưu hiển thị Datatable (cắt cột Nhóm DV chính).
  - **TIP-11-003**: Xóa Dropdown lọc BĐX dư thừa ở New Customer, bổ sung Native Filter & Sort cho TẤT CẢ các bảng.
  - **TIP-11-004**: Tối ưu tải trang Retention cực nhanh bằng cách sửa logic KHHH (chỉ dựa vào tháng T trở đi + Khách hàng mới tháng T) thay vì quét ngược 3 tháng.
- **Phase 10 (Nâng cấp Dashboard)**: Đã nghiệm thu và merge 8/12 TIPs vào nhánh `main`:
  - `[x]` TIP-10-001: Stacked Bar Chart theo tháng (Trang chủ)
  - `[x]` TIP-10-002: Heatmap Cụm x DV tăng trưởng % (Trang chủ)
  - `[x]` TIP-10-003: KPI nâng cấp + 2 Pie Charts (DV + KH) (/bccp)
  - `[x]` TIP-10-004: Customer Health Gauge & KPIs (/bccp)
  - `[x]` TIP-10-005: Area Chart cơ cấu KH + Top 10 CMS (/bccp)
  - `[x]` TIP-10-006: Leaderboard Cụm + Top KHM + Bar DV (/bccp/new-customer)
  - `[x]` TIP-10-007: Gauge SL/DT + Waterfall Biến động KHHH + Churn Alerts & Export (/bccp/retention)
  - `[x]` TIP-10-008: Dropdown SPDV cụ thể cascade và lọc (/bccp/customer)
- **Mã nguồn**: E:\Projects\Dashboard-BCCP (nhánh `main`)
- **Cơ sở dữ liệu**: E:\OneDrive\z.Database-TTKD-Data\dashboard.db
- **Trạng thái**: Chờ thi công tiếp Batch 2 (TIP-10-009 đến TIP-10-012).

### Quyết định chiến lược (RRI Interview 2026-05-31):
- **CHUYỂN HOÀN TOÀN sang Dash**, bỏ Streamlit
- Code Streamlit cũ -> backup tại `E:\OneDrive\DB-loi\streamlit_v2_backup\` (KHÔNG xóa)
- Module dùng chung (`analytics/`, `config/`, `etl/`, `database/`) giữ nguyên
- Thiết kế database-agnostic từ đầu để dễ chuyển PostgreSQL sau

### Stress Test Results (7 kịch bản):
| Metric | Kết quả |
|---|---|
| Dữ liệu chính xác | **7/7 kịch bản KHỚP 100%** |
| Tốc độ <3s | 4/7 kịch bản |
| Tốc độ 3-5s | 3/7 kịch bản (cold start) |
| Tốc độ >5s | 0/7 kịch bản |

### Các Phase đã hoàn thành:
- **Phase 1**: Xây dựng dashboard Streamlit cơ bản
- **Phase 3**: So sánh cùng kỳ năm trước (YoY)
- **Phase 4**: Tối ưu hiệu năng + tạo Dash prototype (KPI page)
- **Phase 5A**: Di chuyển toàn bộ tính năng sang cấu trúc Dash modularized
- **Phase 5D**: Bổ sung chức năng "Chi tiết Khách hàng (CMS)" xoay chiều (2026-05-31, 4/4 TIPs PASS)

### Phase 5 - Chuyển đổi Streamlit -> Dash (ĐÃ ĐÓNG):
- **Phase 5A** (Migrate tính năng): 9 TIPs - `[x]` ĐÃ NGHIỆM THU (2026-05-31, 6/6 hạng mục PASS)
- **Phase 5B** (Tính năng mới: Export, Phân quyền, Cảnh báo): 3 TIPs - `[x]` ĐÃ NGHIỆM THU (2026-05-31, 6/6 hạng mục PASS)
- **Phase 5D** (Tính năng mới: Chi tiết Khách hàng CMS): 4 TIPs - `[x]` ĐÃ NGHIỆM THU (2026-05-31, 4/4 hạng mục PASS)
- **Phase 5C** (Deploy server + PostgreSQL): TẠM DỪNG

### Phase 6 - Cải tiến & Tính năng mới:
- Tiếp nhận các yêu cầu mới từ người dùng.
- Phân loại khách hàng đã gộp "Bán mới" & "Tái bán" thành "KHM/Tái bán" (điều kiện: không giao dịch trong 3 tháng liền trước).

### Active Workspace:
- **Project chính**: `E:\Projects\Dashboard-BCCP\` (Đã di chuyển ra khỏi OneDrive để quản lý bằng Git)
- **Dash App**: `E:\Projects\Dashboard-BCCP\dash_app\`
- **Database (OneDrive Sync)**: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- **Streamlit backup (v1)**: `E:\OneDrive\DB-loi\streamlit_backup\`
- **Streamlit backup (v2 - Phase 3)**: `E:\OneDrive\DB-loi\streamlit_v2_backup\`
- **Project cũ nhất**: `E:\OneDrive\DB-loi\z.Database-TTKD-v1\`

## Key Decisions & Architecture

### Cấu trúc thư mục hiện tại:
```
E:\Projects\Dashboard-BCCP\
├── config/         (settings.py, holidays.py, week_calendar.py) ← DÙNG CHUNG
├── data/           (mapping_spdv.csv, mapping-BC-BDX-Cum.csv)  ← DÙNG CHUNG
├── database/       (bccp.db)                                   ← DÙNG CHUNG
├── etl/            (importer.py, aggregator.py)                ← DÙNG CHUNG
├── analytics/      (revenue.py, customer_classifier.py)        ← DÙNG CHUNG
├── scripts/        (generate_tokens.py, migrate_add_year.py, sync_mappings.py)
├── dash_app/       ← ĐÂY LÀ APP CHÍNH (đã được modularized hoàn toàn)
│   ├── app.py              (Khởi chạy & định tuyến tab)
│   ├── assets/style.css    (CSS style)
│   ├── components/         (sidebar.py, kpi_cards.py, data_table.py)
│   ├── callbacks/          (sidebar_callbacks.py, kpi_callbacks.py, revenue_callbacks.py, customer_callbacks.py, import_callbacks.py, charts_callbacks.py, alerts_callbacks.py, utils.py, export_helpers.py)
│   ├── pages/              (kpi_page.py, revenue_detail.py, customer_detail.py, import_data.py, charts.py, alerts.py)
│   ├── db/                 (connection.py, auth.py)
│   └── requirements.txt
├── dong_bo_len_github.bat  ← Đẩy tất cả các nhánh lên GitHub
├── tai_toan_bo_ve_may.bat  ← Tải và cập nhật tất cả các nhánh từ GitHub về máy
├── run_dashboard.bat
└── project_state.md
```

### Database Schema:
- `transactions` — ~307K dòng (5 tháng 2026, ~60K/tháng), cột chính: cms, buu_cuc, san_pham_dv, ngay_chap_nhan, cuoc_tt_tong, nam_du_lieu
- `dim_spdv` — Ánh xạ mã SPDV → nhom_dich_vu (Truyền thống, TMĐT, Quốc tế, Hành chính công)
- `dim_buucuc` — Ánh xạ mã bưu cục → ten_bdx, ten_cum (18 Cụm)
- `import_log` — Lịch sử import

### Logic phân loại KH (theo tháng, không cộng dồn):
- **Vãng lai**: CMS null / bắt đầu bằng `VANGLAI_`
- **KHM/Tái bán**: Không có phát sinh giao dịch nào trong 3 tháng liền trước.
- **Hiện hữu**: Có phát sinh giao dịch trong 3 tháng liền trước.

### Tuần BCCP: T6→T5, tuần 1 = 01/01 → 08/01

### So sánh YoY:
- `compare_mode`: `prev_period` | `yoy` | `both`
- KPI cards hỗ trợ `value_yoy` + `compare_label_yoy`
- Data table hỗ trợ 12 cột `_yoy` + `_yoy_pct_change`

## Pending Tasks
1. **[PENDING] Bổ sung dữ liệu**: Chờ Sếp nạp thêm dữ liệu 2 ngày cuối tháng 5 (30.05 - 31.05) và dữ liệu tháng 6 còn thiếu (từ 03/06 trở đi).
2. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.
3. **[PENDING] Nghiệm thu thực tế Phase 8**: Sếp chạy Dashboard và kiểm tra các trang mới:
   - `/bccp` - KPI + 3 biểu đồ
   - `/bccp/customer` - bộ lọc DV inline + bảng revenue
   - `/bccp/new-customer` - KH mới theo xa/cụm + so KH
   - `/bccp/retention` - KHHH retention rate + biến động
4. **[PENDING] Nghiệm thu thực tế nhánh feat/ui-fixes**: Sếp kiểm tra các lỗi giao diện và tối ưu bộ lọc:
   - Sidebar Active Menu (Bug #2) đồng bộ trạng thái khi bấm chuyển đổi.
   - Lọc bỏ Hành chính công khỏi biểu đồ cơ cấu BCCP (Bug #3).
   - Bộ lọc sidebar không tự trigger mà bắt đầu áp dụng khi bấm nút "Áp dụng bộ lọc".
   - Giá trị mặc định chu kỳ thời gian không bị mất khi chọn chu kỳ hoặc thay đổi năm.

## Issues & Notes
- **Lỗi không hiển thị Alert khi nạp thành công**: Đã sửa triệt để bằng cách đổi `dismissible` thành `dismissable` trong DBC Alert.
- **Lịch sử KHM**: Bảng `new_customers` đã được khởi tạo và chạy tính toán đầy đủ cho toàn bộ các tháng lịch sử.
- **Bypass Login**: Hiện tại đang bypass authentication trong `app.py` để phát triển tiện lợi hơn. Cần kích hoạt lại khi deploy chính thức.
- **Lỗi CSV dấu phân tách ';'**: Đã khắc phục triệt để bằng việc hỗ trợ cả `,` và `;` ở tất cả các module đọc CSV mapping.
- **[SỬA LỖI QA REPORT - 2026-06-02]**: Khắc phục triệt để 3 lỗi trong báo cáo nghiệm thu QA:
  - **ISSUE-002 (HIGH)**: Khai báo hàm `get_prev_month_year` cục bộ trong `service_callbacks.py` để tránh lỗi `NameError`.
  - **ISSUE-001 (MINOR)**: Gộp và tinh giản UX menu con của 3 dịch vụ mới trong `sidebar.py` (chỉ hiển thị mục "Tổng quan & Chi tiết", ẩn mục trùng link để tránh lỗi callback).
  - **ISSUE-003 (MINOR)**: Đổi các câu query nạp bộ lọc trong `app.py` sang bảng chuẩn hóa `dim_dichvu` thay thế hoàn toàn cho `dim_spdv` cũ.
- **[SỬA LỖI REGRESSION TÍCH HỢP - 2026-06-02]**: Khắc phục lỗi `TypeError: unhashable type: 'list'` khi chuyển bộ lọc so sánh ở Sidebar từ Radio (chọn một) sang Checklist (chọn nhiều). Đã thêm chuẩn hóa dữ liệu `compare_mode` từ list về string tương thích ngược trong `utils.py` và `kpi_callbacks.py`, giúp trang KPI BCCP cũ tiếp tục hoạt động chính xác 100% khi lọc và truy vấn cache.
- **[TẠM TẮT ĐĂNG NHẬP - 2026-06-01]**: Đã bypass hàm kiểm tra `current_user.is_authenticated` trong `dash_app/app.py` để tạm thời truy cập trực tiếp vào Dashboard không cần đăng nhập.
- **Lưu ý Thư viện mới**: Đã cài đặt và cập nhật vào `requirements.txt` các thư viện `openpyxl` (xuất Excel), `reportlab`/`pdfkit` (xuất PDF), `Flask-Login` (phân quyền), `xlrd>=2.0.1` (đọc file .xls cũ từ CAS).
- **[FIX QUAN TRỌNG - 2026-05-31] Bug duplicate VANGLAI khi import RAW**:
  - **Nguyên nhân**: SQLite coi `NULL ≠ NULL` trong UNIQUE constraint, khiến các dòng vãng lai (ma_hop_dong=NULL) không bị nhận diện trùng lặp.
  - **Fix 1 (code)**: Sửa `importer.py` -> `import_raw_excel_file`: convert `ma_hop_dong = ""` -> `None` trước khi INSERT.
  - **Fix 2 (DB)**: Dọn sạch **18,204 dòng trùng lặp** đã tồn tại trong DB (giữ id nhỏ nhất).
  - **Fix 3 (DB schema)**: Thêm Partial UNIQUE Index `idx_unique_no_contract` trên `(buu_cuc, san_pham_dv, ngay_chap_nhan, cms, san_luong, cuoc_tt_tong) WHERE ma_hop_dong IS NULL`.
- **Vấn đề đã giải quyết**:
  - Đã refactor `app.py` monolithic thành cấu trúc modularized chuẩn hóa.
  - Khắc phục triệt để lỗi dropdown tuần `ValueError` do unpacking tuple.
  - Sửa đổi import Streamlit an toàn bằng try-except trong `revenue.py`.
  - Khắc phục `FutureWarning` của pandas bằng cách dùng `StringIO`.
  - Cấu hình output UTF-8 tiếng Việt hoàn chỉnh cho Windows console.
- Cột `so_kh` trong kết quả aggregate là `COUNT DISTINCT cms` — bao gồm vãng lai.
- File `process_directory.py` (nén dữ liệu gốc): `E:\OneDrive\TTKD - Công việc hàng ngày\...\process_directory.py`.
- **[CẤU HÌNH GIT - 2026-06-01]**: Khởi tạo Git repository cục bộ tại workspace chính `E:\OneDrive\z.Database-TTKD\`, thiết lập `.gitignore` loại trừ các file database, excel và log, cấu hình user identity cục bộ, đổi tên branch mặc định sang `main`, và thực hiện commit đầu tiên nhằm sửa lỗi đồng bộ hóa/checkout worktree của hệ thống Agent.
- **[CẬP NHẬT TEMPLATE IMPORT & SỬA LỖI UI - 2026-06-01]**: Tạo file Excel mẫu phục vụ điền dữ liệu thủ công tại [template_import.xlsx](file:///e:/OneDrive/z.Database-TTKD/data/template_import.xlsx) với các cột quan trọng bôi màu xanh (STT, CMS, Ma_HD, Buu_Cuc, San_Pham, Ngay_CN, San_Luong, Cuoc_TT_Tong). Sửa lỗi nghiêm trọng trong callback nạp dữ liệu tại [import_callbacks.py](file:///e:/OneDrive/z.Database-TTKD/dash_app/callbacks/import_callbacks.py#L112-L132) do truyền sai tham số và gán sai kiểu trả về (dict sang tuple), giúp tính năng import trên Dashboard chạy ổn định.
- **[ĐỒNG BỘ DANH MỤC - 2026-06-01]**: Đã tạo script [sync_mappings.py](file:///E:/Projects/Dashboard-BCCP/scripts/sync_mappings.py) để đồng bộ sản phẩm dịch vụ và bưu cục từ 2 file CSV trong thư mục `data/` vào bảng `dim_spdv` và `dim_buucuc` trong cơ sở dữ liệu SQLite sau khi Sếp chỉnh sửa.
- **[SỬA LỖI ĐỌC FILE .XLS & LỊCH SỬ IMPORT - 2026-06-01]**: Cấu hình bộ điều phối `import_any_excel_file` trong [importer.py](file:///E:/Projects/Dashboard-BCCP/etl/importer.py) giúp tự động nhận diện file RAW (từ CAS) và file mẫu điền tay (Template) cho cả định dạng .xls và .xlsx. Sửa lỗi lệch cột SQLite của lịch sử import trong [import_callbacks.py](file:///E:/Projects/Dashboard-BCCP/dash_app/callbacks/import_callbacks.py#L32-L75).
