# Project State — Dashboard Doanh thu BCCP

## Project Goal
Dashboard doanh thu bưu chính chuyển phát (BCCP) với bộ lọc đa chiều, phân loại khách hàng tự động, và import dữ liệu từ Excel vào SQLite. Phục vụ **20+ người dùng** từ nhiều phòng ban. Sẽ deploy lên **server nội bộ**.

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đang chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite hiện tại → PostgreSQL khi deploy server (database-agnostic)
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl
- **Encoding**: UTF-8 toàn bộ

## Current State — Phase 6 ĐANG TRIỂN KHAI

### Quyết định chiến lược (RRI Interview 2026-05-31):
- **CHUYỂN HOÀN TOÀN sang Dash**, bỏ Streamlit
- Code Streamlit cũ → backup tại `E:\OneDrive\DB-loi\streamlit_v2_backup\` (KHÔNG xóa)
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
- **Phase 1**: Xây dựng dashboard Streamlit cơ bản ✅
- **Phase 3**: So sánh cùng kỳ năm trước (YoY) ✅
- **Phase 4**: Tối ưu hiệu năng + tạo Dash prototype (KPI page) ✅
- **Phase 5A**: Di chuyển toàn bộ tính năng sang cấu trúc Dash modularized ✅
- **Phase 5D**: Bổ sung chức năng "Chi tiết Khách hàng (CMS)" xoay chiều ✅ (2026-05-31, 4/4 TIPs PASS)

### Phase 5 — Chuyển đổi Streamlit → Dash (ĐÃ ĐÓNG):
- **Phase 5A** (Migrate tính năng): 9 TIPs — `[x]` ĐÃ NGHIỆM THU ✅ (2026-05-31, 6/6 hạng mục PASS)
- **Phase 5B** (Tính năng mới: Export, Phân quyền, Cảnh báo): 3 TIPs — `[x]` ĐÃ NGHIỆM THU ✅ (2026-05-31, 6/6 hạng mục PASS)
- **Phase 5D** (Tính năng mới: Chi tiết Khách hàng CMS): 4 TIPs — `[x]` ĐÃ NGHIỆM THU ✅ (2026-05-31, 4/4 hạng mục PASS)
- **Phase 5C** (Deploy server + PostgreSQL): TẠM DỪNG

### Phase 6 — Cải tiến & Tính năng mới:
- Tiếp nhận các yêu cầu mới từ người dùng.
- Phân loại khách hàng đã gộp "Bán mới" & "Tái bán" thành "KHM/Tái bán" (điều kiện: không giao dịch trong 3 tháng liền trước).

### Active Workspace:
- **Project chính**: `E:\OneDrive\z.Database-TTKD\`
- **Dash App**: `E:\OneDrive\z.Database-TTKD\dash_app\`
- **Streamlit backup (v1)**: `E:\OneDrive\DB-loi\streamlit_backup\`
- **Streamlit backup (v2 - Phase 3)**: `E:\OneDrive\DB-loi\streamlit_v2_backup\` (ĐÃ TẠO)
- **Project cũ nhất**: `E:\OneDrive\DB-loi\z.Database-TTKD-v1\`

## Key Decisions & Architecture

### Cấu trúc thư mục hiện tại:
```
E:\OneDrive\z.Database-TTKD\
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
1. **[DONE] Phase 5A**: Migrate Streamlit → Dash (9 TIPs) ✅
2. **[DONE] Phase 5B**: Export Excel/PDF, Phân quyền, Cảnh báo (TIP-10 → TIP-12) ✅
3. **[DONE] Phase 5D**: Bổ sung chức năng "Chi tiết Khách hàng (CMS)" xoay chiều (4 TIPs) ✅
4. **[PAUSED] Phase 5C**: Deploy server nội bộ + PostgreSQL (Tạm dừng)
5. **[DONE] Cập nhật logic CMS**: Gộp "Bán mới" & "Tái bán" thành "KHM/Tái bán".
6. **[IN PROGRESS] Phase 6**: Chờ yêu cầu tính năng mới từ người dùng.

## Issues & Notes
- **Lưu ý Thư viện mới**: Đã cài đặt và cập nhật vào `requirements.txt` các thư viện `openpyxl` (xuất Excel), `reportlab`/`pdfkit` (xuất PDF), `Flask-Login` (phân quyền), `xlrd>=2.0.1` (đọc file .xls cũ từ CAS).
- **[FIX QUAN TRỌNG - 2026-05-31] Bug duplicate VANGLAI khi import RAW**:
  - **Nguyên nhân**: SQLite coi `NULL ≠ NULL` trong UNIQUE constraint, khiến các dòng vãng lai (ma_hop_dong=NULL) không bị nhận diện trùng lặp.
  - **Fix 1 (code)**: Sửa `importer.py` → `import_raw_excel_file`: convert `ma_hop_dong = ""` → `None` trước khi INSERT.
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
- **[ĐỒNG BỘ DANH MỤC - 2026-06-01]**: Đã tạo script [sync_mappings.py](file:///e:/OneDrive/z.Database-TTKD/scripts/sync_mappings.py) để đồng bộ sản phẩm dịch vụ và bưu cục từ 2 file CSV trong thư mục `data/` vào bảng `dim_spdv` và `dim_buucuc` trong cơ sở dữ liệu SQLite sau khi Sếp chỉnh sửa.



