# PROJECT CONTEXT: Dashboard-BCCP (Phase 7)
Generated: 2026-06-02 | For: Builder (Thợ thi công)

## 1. Project Overview
Dashboard Điều Hành Doanh Thu Bưu chính — phục vụ ~20 nhân viên phòng TTKD/BGĐ Bưu điện tỉnh Nghệ An.

**Phase 7 (hiện tại)** — 5 TIPs: TIP-006 → TIP-007 → TIP-009 → (TIP-008 + TIP-010 song song)

### Vấn đề cần giải quyết:
1. **Routing lỗi**: vào `/hcc` bị đẩy về `/bccp` → Fix `sync_url_to_tabs_navigation` mặc định trả về `"tab-kpi"` thay vì `None`
2. **Sidebar filter**: Nhóm DV/Loại KH/HĐ hiện ở mọi trang → ẩn khi không ở `/bccp*`
3. **PHBC**: Thêm Phát hành báo chí vào BCCP (bảng `transactions_phbc` + import UI + KPI card)

## 2. Tech Stack & Conventions
- Language: Python 3.13 (dùng `py -3.13` trên Windows)
- Framework: Dash >=2.15.0 + dash-bootstrap-components >=1.5.0
- Database: SQLite (`E:\OneDrive\z.Database-TTKD-Data\dashboard.db`)
- Auth: Flask-Login (hiện BYPASS — `if False:`)
- Styling: Vanilla CSS (`dash_app/assets/style.css`)
- Naming conventions: snake_case toàn bộ, tên cột DB viết **thường** (`ten_cum`, `ten_bdx`)
- File organization: pages/ cho layout, callbacks/ cho logic, components/ cho reusable UI

## 3. Architecture
```
Excel upload → etl/importer.py → dashboard.db (SQLite)
                                       │
CSV upload → scripts/sync_mappings.py → dim_dichvu (bảng danh mục)
                                       │
analytics/global_metrics.py ◄──────────┤  (4 nhóm DV)
analytics/revenue.py ◄─────────────────┘  (BCCP chi tiết)
                │
        dash_app/app.py → 11+ trang Dash UI
```

### Key entry points:
- `dash_app/app.py`: Routing, layout, khởi tạo callbacks. **QUAN TRỌNG**: Callback `sync_url_to_tabs_navigation` (L224-245) — đây là nguyên nhân routing lỗi.
- `dash_app/callbacks/kpi_callbacks.py`: L73 check `tab_val != "tab-kpi"` — cần thêm `or tab_val is None`
- `dash_app/components/sidebar.py`: Layout sidebar — cần thêm container `bccp-extra-filters`
- `dash_app/callbacks/sidebar_callbacks.py`: Callback `update_sidebar_state` — cần thêm Output để ẩn/hiện bccp-extra-filters

### Database tables hiện có:
- `transactions` — Dữ liệu BCCP gốc (~307K dòng)
- `transactions_hcc` — Dữ liệu HCC (cấu trúc gọn: id, thang, nam, ma_buu_cuc, doanh_thu)
- `transactions_tcbc` — Dữ liệu TCBC
- `transactions_ppbl` — Dữ liệu PPBL
- `transactions_phbc` — **[CHƯA TỒN TẠI]** — TIP-009 sẽ tạo
- `dim_dichvu` — Danh mục dịch vụ mới (nhom_chinh: BCCP/HCC/TCBC/PPBL, 97 dòng)
- `dim_spdv` — Legacy, analytics/revenue.py vẫn JOIN
- `dim_buucuc` — Danh mục bưu cục (636 dòng, cột: `ten_cum`, `ten_bdx`, `ten_buu_cuc`)
- `plans` — Kế hoạch doanh thu
- `import_log` — Lịch sử import

## 4. Key Decisions (Phase 7)
| Decision | Chosen | Rationale |
|----------|--------|-----------|
| D-018 | `tabs-navigation` trả về `None` cho URL ngoài BCCP | Không cần refactor callback cũ |
| D-019 | CSS show/hide `bccp-extra-filters` theo pathname | Pattern đã có sẵn trong sidebar_callbacks |
| D-020 | Xóa hoàn toàn `sidebar-spdv` | Sếp confirm bỏ bộ lọc SPDV chi tiết |
| D-021 | Xóa HCC card khỏi /bccp, thay bằng PHBC | HCC thuộc HCC, không thuộc BCCP |
| D-022 | Bảng `transactions_phbc` cấu trúc giống `transactions_hcc` | Đồng nhất |
| D-023 | PHBC chỉ cần 1 KPI card trong /bccp, không sub-page | Sếp confirm |

## 5. Dependency Map TIPs Phase 7
```
TIP-006 (Fix routing) — CHẠY ĐẦU TIÊN, độc lập
    ↓
TIP-007 (Sidebar filter) — sau TIP-006
    ↓
TIP-009 (DB + ETL PHBC) — độc lập, chạy sau TIP-006
    ↓
TIP-008 (KPI card PHBC) — sau TIP-009
TIP-010 (Import UI PHBC) — sau TIP-009, song song với TIP-008
```

## 6. Patterns to Follow
- **Guard pattern** trong callbacks BCCP: `if tab_val != "tab-kpi" or tab_val is None: return [dash.no_update] * N`
- **Show/hide pattern**: Xem `sidebar_callbacks.py` hàm `update_sidebar_state` — đã dùng pattern `{"display": "block"/"none"}` cho `filter_style`
- **Safe DB query**: Dùng `try/except` khi query bảng có thể chưa tồn tại (ví dụ `transactions_phbc`)
- **Cache pattern**: `functools.lru_cache` hoặc dict-based cache (xem `hcc_revenue_callbacks.py`)
- **DataTable pattern**: Xem `dash_app/components/data_table.py` — `render_revenue_datatable()`
- **Subprocess pattern**: `subprocess.run([sys.executable, "scripts/..."], cwd=project_root, timeout=30)`

> Chi tiết đầy đủ → đọc `.vibecode/blueprint.md` và từng TIP file.
