# SCAN REPORT: Dashboard-BCCP (Phase 6 — Focused Scan)
Generated: 2026-06-02

```
TECH_STACK:
  Language: Python 3.13
  Framework: Dash >=2.15.0 + dash-bootstrap-components >=1.5.0
  Styling: Vanilla CSS (dash_app/assets/style.css — 10,740 B)
  Database: SQLite (dashboard.db — qua sqlite3 stdlib)
  Auth: Flask-Login >=0.6.0 (hiện đang BYPASS — `if False:`)
  State: dcc.Store (service-type-store), lru_cache (utils.py, connection.py)
  Other: Pandas >=2.0.0, Plotly >=5.18.0, openpyxl, xlrd >=2.0.1, reportlab (PDF — sắp xóa), pdfkit

EXISTING_MODULES:
  - config/settings.py: Cấu hình DB path, data path, column names, multi-service groups
  - config/holidays.py: Quản lý ngày lễ VN (cố định + âm lịch 2025-2027)
  - config/week_calendar.py: Lịch tuần (T6→T5), tính kỳ trước/cùng kỳ
  - analytics/global_metrics.py: Tính doanh thu 4 dịch vụ, lũy kế YTD, tỷ lệ HT, phân rã Cụm
  - analytics/revenue.py: Core Query Engine — GROUP BY động, so sánh kỳ, pivot KH
  - analytics/customer_classifier.py: Phân loại KH: KHM/Tái bán, Hiện hữu, Vãng lai
  - etl/importer.py: Import Excel (Template/RAW CAS/HCC/TCBC/PPBL), auto-detect format
  - scripts/sync_mappings.py: Đồng bộ CSV → dim_dichvu + dim_spdv + dim_buucuc
  - scripts/migrate_dim_dichvu.py: Migration dim_spdv → dim_dichvu, seed HCC/TCBC/PPBL
  - dash_app/app.py: Entry point — routing 10 trang + Flask auth routes

PATTERNS_DETECTED:
  - Auth (Flask-Login): 6 files sử dụng — hiện BYPASS
  - Caching (lru_cache): utils.py (2 hàm), connection.py (1 hàm), revenue.py (dict cache)
  - State (dcc.Store): service_overview.py lưu loại DV, sidebar dùng tabs-navigation ẩn
  - Export (Excel+PDF): export_helpers.py — 687 dòng, format VND header 2 tầng

REUSABLE_COMPONENTS:
  - sidebar.py: dash_app/components/sidebar.py — Sidebar Accordion 4 nhóm DV + 8 bộ lọc + profile
  - kpi_cards.py: dash_app/components/kpi_cards.py — Grid 7 thẻ KPI với sparkline + delta
  - data_table.py: dash_app/components/data_table.py — DataTable render + GROUP_BY_LABEL_MAP

GAPS_DETECTED:
  - [GAP-1] Lỗi KeyError ten_Cum: analytics/global_metrics.py dùng "ten_Cum" nhưng SQLite trả "ten_cum"
  - [GAP-2] dim_dichvu sai nhóm: HCC bị gán cứng nhom_chinh='BCCP' từ migration cũ
  - [GAP-3] mapping-spdv.csv thiếu cột nhom_chinh: Không phân biệt được 4 nhóm DV
  - [GAP-4] Trang chủ YTD: Biểu đồ Bar chưa đúng yêu cầu (cần Bảng số liệu)
  - [GAP-5] Route /bccp/kpi: Cần rút gọn thành /bccp
  - [GAP-6] Thiếu /hcc/revenue: Trang HCC không có báo cáo doanh thu chi tiết
  - [GAP-7] 2 bảng song song: dim_spdv (legacy) + dim_dichvu (mới) — revenue.py vẫn JOIN dim_spdv
  - [GAP-8] PDF dependencies: reportlab + pdfkit trong requirements nhưng sắp bỏ

CODE_HEALTH:
  Type Safety: None (no type hints)
  Linting: Not configured
  Tests: 0 files — Không có thư mục tests/ hay file test_*.py
  Debug Artifacts: ~60+ print() trong dash_app/ + 2 debug scripts (check_hcc_db.py, debug_cum.py)
  TODO/FIXME: 0 found

ESTIMATED_SIZE:
  Files: 31 .py files
  Lines of Code: ~5,200
  Components/Modules: 3 reusable components, 8 page layouts, 11 callback modules
  API Routes/Endpoints: 10 pages + 1 Flask route

COMPLEXITY_ASSESSMENT: Medium
  Signals: Có DB + auth, multi-page (10 trang), team scale (~20 users), multiple service groups
  Nhưng scope thay đổi lần này: Focused (bug fixes + thêm 1 trang + refactor CSV) → RRI áp dụng mức Small (15-20 câu)
```
