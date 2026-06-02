# CONTRACT: Dashboard-BCCP (Phase 6)

## DELIVERABLES
| # | Item                              | Details                                                    | Requirements          |
|---|-----------------------------------|------------------------------------------------------------|-----------------------|
| 1 | Sync Engine mới                   | CSV có nhom_chinh, sync vào dim_dichvu, auto backup        | REQ-016, REQ-017      |
| 2 | Fix Global Metrics                | Fix ten_cum, cache 5p, format "-" cho chia 0               | REQ-018               |
| 3 | DataTable YTD Trang chủ           | Bảng 4 cột, conditional color 4 nấc                       | REQ-019               |
| 4 | Routing & PDF Cleanup             | /bccp/kpi → /bccp, xóa toàn bộ PDF (UI + logic + deps)    | REQ-020               |
| 5 | HCC Revenue Page                  | /hcc/revenue với bộ lọc + bảng chi tiết clone BCCP         | REQ-021               |
| 6 | Import UI nâng cấp                | Upload CSV danh mục + nút Đồng bộ trên web                 | REQ-016               |

## TECH STACK
- Python 3.13, Dash >=2.15.0, Pandas >=2.0.0, SQLite
- **Loại bỏ**: reportlab, pdfkit

## TASK GRAPH SUMMARY
5 TIPs, estimated 120 minutes
```
TIP-001: ETL CSV + Sync ──────────────────────┐
    │                                          │
    ▼                                          │
TIP-002: Backend Fix + Cache ─────┐            │
    │                              │           │
    ▼                              ▼           ▼
TIP-003: Global UI        TIP-004: HCC+Route   TIP-005: Import UI
```

## NOT INCLUDED
- Không gộp bảng transactions TCBC/PPBL vào transactions chung
- Không fake data cho PHBC (User tự nhập qua CSV sau)
- Không thay đổi logic auth (vẫn giữ bypass)
- Không thêm test suite (scope ngoài phase này)
- Không refactor print() → logging (scope ngoài)

## CONFIRM
Reply "CONFIRM" để nhận Task Graph.
