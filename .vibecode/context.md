# Context — Phase 10: PRD Alignment

**Ngày tạo**: 2026-06-04
**Branch**: feat/phase10-prd
**Worktree**: E:\Projects\worktrees\Dashboard-BCCP\feat-phase10-prd
**DB**: E:\OneDrive\z.Database-TTKD-Data\dashboard.db

## Mục tiêu
Nâng cấp toàn diện 5 trang Dashboard theo PRD. 12 TIPs chia 3 batch.

## Quyết định của Sếp
- **Donut /bccp**: Giữ CẢ 2 (DV + KH), thu nhỏ lại hoặc dùng biểu đồ tròn (không donut)
- **Line chart**: Đổi sang **tuần BCCP** (T6→T5 hàng tuần)
- **Heatmap**: Mặc định so **tháng trước**, có tùy chọn so cùng kỳ YoY
- **Area Chart**: Theo **tháng** (4-6 tháng gần nhất)
- **Churn Alert**: Tất cả KHHH, không phát sinh trong **7 ngày**
- **Batch**: Hoàn thiện tất cả

## Tech Stack
- Python 3.13 | Dash | Plotly | SQLite | Flask-Login
- DB: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- Config: `config/settings.py` → DB_PATH

## Cấu trúc quan trọng
```
dash_app/
├── app.py                          ← Routing
├── components/
│   ├── sidebar.py                  ← Sidebar + btn-apply-filter
│   └── kpi_cards.py                ← Template cards
├── callbacks/
│   ├── sidebar_callbacks.py        ← Cascade + period toggle
│   ├── kpi_callbacks.py            ← /bccp: 5 cards + 3 charts (23 outputs)
│   ├── customer_callbacks.py       ← /bccp/customer
│   ├── new_customer_callbacks.py   ← /bccp/new-customer
│   ├── retention_callbacks.py      ← /bccp/retention
│   ├── global_callbacks.py         ← / (trang chủ): 4 KPI + donut + 2 tables
│   ├── alerts_callbacks.py
│   ├── service_callbacks.py        ← HCC/TCBC/PPBL (không đụng)
│   └── export_helpers.py           ← generate_excel_report, generate_customer_excel
└── pages/
    ├── global_overview.py          ← Layout trang chủ
    ├── kpi_page.py                 ← Layout /bccp
    ├── new_customer.py             ← Layout /bccp/new-customer
    ├── retention.py                ← Layout /bccp/retention
    └── customer_detail.py          ← Layout /bccp/customer

analytics/
├── global_metrics.py               ← get_total_revenue_by_service, get_revenue_by_cum
├── revenue.py                      ← query_revenue (core engine), 673 dòng
├── customer_classifier.py          ← classify: Vãng lai / KHM / KHHH
├── new_customer_calculator.py      ← calculate_new_customers
└── retention_metrics.py            ← get_retention_stats, get_khhh_changes
```

## Tuần BCCP
- Tuần tính từ **Thứ 6 tuần trước** đến **Thứ 5 tuần này**
- Tuần 1 = 01/01 → ngày Thứ 5 đầu tiên (hoặc 08/01)
- Cần viết helper `get_bccp_week_boundaries(date)` → (start, end, week_number)

## Bộ lọc Sidebar (đã có nút Lọc)
| ID | Kiểu | Ghi chú |
|---|---|---|
| sidebar-year | Dropdown | Năm |
| sidebar-period | Dropdown | Ngày/Tuần/Tháng |
| sidebar-month-select | Dropdown | Tháng |
| sidebar-cum | Dropdown | Cụm |
| sidebar-bdx | Dropdown | BĐX |
| sidebar-buu-cuc | Dropdown | Bưu cục |
| btn-apply-filter | Button | Trigger duy nhất |

## Callbacks Pattern (Phase 9)
```python
@app.callback(
    [Output(...)],
    [Input("btn-apply-filter", "n_clicks"),  # Trigger
     Input("tabs-navigation", "value")],      # Tab guard
    [State("sidebar-year", "value"),          # Bộ lọc → State
     State("sidebar-month-select", "value"),
     ...]
)
```

## Hàm analytics có thể tái sử dụng
- `get_total_revenue_by_service(db, year, month, cum)` → dict{BCCP,HCC,TCBC,PPBL}
- `get_revenue_by_cum(db, year, month)` → DataFrame(Cụm, BCCP, HCC, TCBC, PPBL)
- `query_revenue(db, ...)` → DataFrame (core BCCP query engine)
- `get_retention_stats(db, year, month, cum)` → dict retention
- `get_khhh_changes(db, year, month, cum)` → DataFrame biến động
- `calculate_new_customers(db, year, month)` → insert vào new_customers table
- `classify_customers()` → Vãng lai/KHM/KHHH

## Thứ tự thi công
1. TIP-10-001 + 002 (Trang chủ: Stacked Bar + Heatmap)
2. TIP-10-003 + 004 (/bccp: KPI nâng cấp + Charts đổi)
3. TIP-10-005 + 006 + 007 (/bccp: Customer Health + Area + Top CMS)
4. TIP-10-008 (/bccp/new-customer: Leaderboard + Top KHM + Bar DV)
5. TIP-10-009 + 010 + 011 (/bccp/retention: Gauge + Waterfall + Churn)
6. TIP-10-012 (/bccp/customer: Dropdown mã DV)
