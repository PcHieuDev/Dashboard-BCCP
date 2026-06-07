# TIP-pages-002: Trang Tổng quan DV (BCCP, HCC, TCBC, PPBL)

## HEADER
- TIP-ID: TIP-pages-002
- Branch: feat/pages-redesign
- Project: Dashboard BCCP v2.0
- Module: Pages / Callbacks
- Depends on: TIP-pages-001
- Priority: P0
- Estimated effort: 60 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign
- Key files to reference:
  - `dash_app/pages/kpi_page.py` → trang BCCP hiện tại (sẽ đổi thành Tổng quan DV)
  - `dash_app/callbacks/kpi_callbacks.py` → callbacks hiện tại
  - `dash_app/pages/service_overview.py` → template chung cho HCC/TCBC/PPBL
  - `dash_app/callbacks/service_callbacks.py` → callbacks service
  - Bảng `dim_dichvu` → nhom_chinh, nhom_dich_vu để lấy nhóm con

## TASK
Đổi 4 trang dịch vụ (/bccp, /hcc, /tcbc, /ppbl) sang cấu trúc "Tổng quan dịch vụ" giống trang Tổng quan chung nhưng hiển thị nhóm con.

## SPECIFICATIONS

### Cấu trúc giống TIP-pages-001 nhưng:
- KPI cards: thay vì 4 nhóm DV chính → hiển thị **nhóm con** trong nhóm DV đó
  - `/bccp` → cards cho "Truyền thống", "TMĐT", "Quốc tế", etc. (query từ dim_dichvu WHERE nhom_chinh = 'BCCP')
  - `/hcc` → cards cho nhóm con HCC
  - `/tcbc`, `/ppbl` → tương tự
- Top 10: tính cho nhóm DV chính đó (ví dụ /bccp → chỉ tính DT BCCP)
- Biểu đồ 12 kỳ: stacked theo nhóm con
- 2 bảng chi tiết: cột DT theo nhóm con thay vì 4 nhóm DV chính

### Sửa `dash_app/pages/kpi_page.py`
- Đổi thành layout "Tổng quan DV BCCP" với cấu trúc trên
- Dùng prefix ID `bccp-overview-`

### Sửa `dash_app/callbacks/kpi_callbacks.py`
- Đổi logic query: lọc theo nhom_chinh = 'BCCP', group by nhom_dich_vu
- Đọc từ summary tables

### Sửa `dash_app/pages/service_overview.py`
- Hàm `create_service_page_layout(service_key)` nhận key ("HCC", "TCBC", "PPBL")
- Layout giống kpi_page nhưng nhóm DV chính thay đổi theo service_key
- Prefix ID: `{service_key.lower()}-overview-`

### Sửa `dash_app/callbacks/service_callbacks.py`
- Hàm `register_service_callbacks(app)` xử lý cho cả 3 trang HCC/TCBC/PPBL
- Pattern Matching Callbacks hoặc 3 bộ callbacks riêng

### Query nhóm con
```sql
SELECT DISTINCT nhom_dich_vu FROM dim_dichvu 
WHERE nhom_chinh = ? AND nhom_dich_vu IS NOT NULL
ORDER BY nhom_dich_vu
```

## ACCEPTANCE CRITERIA
- Given: User truy cập /bccp
- When: Trang load
- Then: KPI cards hiện nhóm con BCCP (Truyền thống, TMĐT, Quốc tế...), Top 10 tính cho BCCP, biểu đồ stacked nhóm con

- Given: User truy cập /hcc
- When: Trang load
- Then: Cấu trúc giống /bccp nhưng cho HCC (có thể hiện "—" nếu chưa có dữ liệu)

## CONSTRAINTS
- Trang /hcc, /tcbc, /ppbl có thể chưa có dữ liệu (transactions_hcc = 0 dòng) → hiện empty state
- KHÔNG tạo callback mới nếu có thể tái sử dụng từ kpi_callbacks
- GIỮ NGUYÊN route paths (/bccp, /hcc, /tcbc, /ppbl)
