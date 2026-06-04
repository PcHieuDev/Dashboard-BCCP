# Context — UI Fixes Phase 9

**Ngày tạo**: 2026-06-04
**Branch**: feat/ui-fixes
**Worktree**: E:\Projects\worktrees\Dashboard-BCCP\feat-ui-fixes

## Mục tiêu
Sửa 3 vấn đề được phát hiện sau Phase 8:
- Bug #1: Thêm nút "Lọc" + fix default giá trị bộ lọc khi đổi chu kỳ
- Bug #2: Sidebar menu BCCP luôn tô đậm (mismatch IDs sau Phase 8)
- Bug #3: Biểu đồ Cơ cấu doanh thu BCCP hiển thị cả HCC/TCBC/PPBL

## Tech Stack
- Python 3.13 | Dash | Plotly | SQLite | Flask-Login
- DB: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- Config: `config/settings.py` → DB_PATH

## Cấu trúc quan trọng
```
dash_app/
├── app.py                          ← Entry point, routing
├── components/sidebar.py           ← Layout sidebar + menu accordion
├── callbacks/
│   ├── sidebar_callbacks.py        ← set active menu + cascade filters
│   ├── kpi_callbacks.py            ← KPI cards + 3 charts (update_kpi_cards)
│   ├── customer_callbacks.py
│   ├── global_callbacks.py
│   ├── alerts_callbacks.py
│   ├── new_customer_callbacks.py
│   ├── retention_callbacks.py
│   └── service_callbacks.py
└── pages/...
analytics/
├── kpi_metrics.py                  ← Tính KPI BCCP
└── revenue.py (hoặc kpi_metrics)   ← Query data cho donut chart
```

## IDs Bộ lọc Sidebar
| ID | Kiểu | Ghi chú |
|---|---|---|
| sidebar-year | Dropdown | Năm |
| sidebar-period | Dropdown | Ngày/Tuần/Tháng |
| sidebar-date-range | DatePickerRange | ẩn/hiện |
| sidebar-week-select | Dropdown | ẩn/hiện |
| sidebar-month-select | Dropdown | ẩn/hiện |
| sidebar-compare-mode | Checklist | So sánh |
| sidebar-cum | Dropdown | Cụm |
| sidebar-bdx | Dropdown | BĐX cascade |
| sidebar-buu-cuc | Dropdown | Bưu cục cascade |
| sidebar-nhom-dv | dcc.Store | Store ẩn |
| sidebar-loai-kh | dcc.Store | Store ẩn |
| sidebar-hop-dong | dcc.Store | Store ẩn |

## IDs Nav Links hiện có trong sidebar.py
- nav-global-overview (/)
- nav-bccp-kpi (/bccp)
- nav-bccp-customer (/bccp/customer)
- nav-bccp-new-customer (/bccp/new-customer)  ← MỚI (Phase 8)
- nav-bccp-retention (/bccp/retention)          ← MỚI (Phase 8)
- nav-bccp-alerts (/bccp/alerts)
- nav-hcc-overview (/hcc)
- nav-hcc-revenue (/hcc/revenue)
- nav-tcbc-overview (/tcbc)
- nav-ppbl-overview (/ppbl)

## Bug Pattern
- sidebar_callbacks.py CHƯA được cập nhật sau Phase 8
- Vẫn còn Output cho nav-bccp-revenue, nav-bccp-charts (đã xóa)
- Thiếu Output cho nav-bccp-new-customer, nav-bccp-retention
