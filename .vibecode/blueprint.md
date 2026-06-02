# BLUEPRINT: Dashboard-BCCP (Phase 6)
## Vibe Coding 8-Step v6.0

### PROJECT INFO
| Field   | Value                                                    |
|---------|----------------------------------------------------------|
| Project | Dashboard Điều Hành Doanh Thu — Phase 6 Bug Fix & UI     |
| Nature  | Web UI (Dash) + CRUD Lifecycle + Team Scale (~20 users)  |
| Date    | 2026-06-02                                               |

### GOALS
**Primary Goal:** Sửa lỗi dữ liệu sai nhóm (HCC bị kẹt BCCP), nâng cấp trang chủ, thêm báo cáo HCC, dọn dẹp PDF.
**Target Audience:** 20+ nhân viên phòng BCCP, TTKD, BGĐ Bưu điện tỉnh Nghệ An.
**Key Message:** Dữ liệu chính xác theo 4 nhóm dịch vụ, giao diện trực quan hơn, vận hành dễ dàng hơn.

### ARCHITECTURE

**6 Dimensions Analysis (VISION):**

| Dimension    | Phân tích                                                          |
|--------------|--------------------------------------------------------------------|
| Interface    | Web UI (Dash + Bootstrap), truy cập qua browser, Cloudflare Tunnel |
| Data flow    | Excel upload → ETL → SQLite → Analytics → Dash UI                 |
| User model   | Multi-user, phân quyền theo Cụm/BĐX, hiện bypass auth             |
| Lifecycle    | CRUD: Import data → View reports → Export Excel                    |
| Scale        | Team (~20 users), single server, ~300K transactions                |
| State        | Persistent DB (SQLite), lru_cache in-memory, dcc.Store client-side |

**Building blocks:**
```
├── Entry points
│   ├── dash_app/app.py → 10 trang + 1 Flask route
│   └── scripts/sync_mappings.py → CLI đồng bộ danh mục
├── Core modules
│   ├── analytics/global_metrics.py → Tính YTD, Cụm, 4 nhóm DV
│   ├── analytics/revenue.py → Query engine GROUP BY động
│   └── analytics/customer_classifier.py → Phân loại KH
├── Data layer
│   ├── dashboard.db → transactions, dim_dichvu, dim_buucuc, plans
│   ├── dash_app/db/connection.py → DatabaseManager + cached query
│   └── data/mapping-spdv.csv → Danh mục dịch vụ (CSV nguồn)
├── Integration points
│   ├── etl/importer.py → Import Excel (Template/RAW CAS/HCC/TCBC/PPBL)
│   └── Cloudflare Tunnel → dashboard.bdna.io.vn
└── Cross-cutting
    ├── dash_app/db/auth.py → Flask-Login (bypass)
    ├── dash_app/callbacks/utils.py → Format tiền, cache, resolve filters
    └── dash_app/callbacks/export_helpers.py → Xuất Excel (+ PDF sắp xóa)
```

**User Flows:**
```
Operator (Import data):
├── Entry → Mở /import, chọn loại DV, upload Excel
├── Core loop → Xác nhận nạp → Kiểm tra lịch sử → Upload CSV danh mục → Đồng bộ
├── Edge cases → File lỗi → Alert đỏ, file trùng → cảnh báo
└── Exit → Đóng tab

End User (Xem báo cáo):
├── Entry → Mở /, thấy tổng quan 4 nhóm DV + bảng YTD theo Cụm
├── Core loop → Chọn nhóm DV → Xem KPI/Revenue/Charts → Lọc → Xuất Excel
├── Edge cases → Dữ liệu trống → "Không tìm thấy dữ liệu", % rỗng → "-"
└── Exit → Đóng tab
```

**Design Direction (UI):**

| Element       | Decision              | Rationale                                    |
|---------------|-----------------------|----------------------------------------------|
| Font pairing  | Inter (heading+body)  | Đang dùng, clean và professional             |
| Primary color | #1E293B (Slate dark)  | Đang dùng, phù hợp dashboard nghiệp vụ      |
| Density       | Compact               | Nhiều số liệu trên 1 màn hình               |
| Motion        | Subtle (Spinner only) | Dashboard số liệu, không cần animation phức  |
| YTD Colors    | 4 nấc: <60% #DC2626, 60-80% #F97316, 80-100% #EAB308, >100% #22C55E | Phân biệt rõ mức hoàn thành |

### TECH STACK
Reuse toàn bộ stack hiện tại (từ Scan):
- Python 3.13 + Dash >=2.15.0 + DBC >=1.5.0
- SQLite (dashboard.db) + Pandas >=2.0.0
- **Loại bỏ**: reportlab, pdfkit (xóa khỏi requirements)

### FILE STRUCTURE
```
Thay đổi so với hiện tại:

[MODIFY] data/mapping-spdv.csv              ← Thêm cột nhom_chinh
[MODIFY] scripts/sync_mappings.py           ← Target dim_dichvu, thêm backup
[MODIFY] analytics/global_metrics.py        ← Fix ten_cum, thêm cache
[MODIFY] dash_app/components/data_table.py  ← Fix "0%" → "-"
[MODIFY] dash_app/pages/global_overview.py  ← Bar chart → DataTable 4 màu
[MODIFY] dash_app/pages/revenue_detail.py   ← Xóa nút PDF
[MODIFY] dash_app/pages/import_data.py      ← Thêm Upload CSV + nút Sync
[MODIFY] dash_app/app.py                    ← Route /bccp, thêm /hcc/revenue
[MODIFY] dash_app/components/sidebar.py     ← Link /bccp, thêm menu HCC revenue
[MODIFY] dash_app/callbacks/revenue_callbacks.py  ← Xóa logic PDF
[MODIFY] dash_app/callbacks/export_helpers.py     ← Xóa hàm PDF + imports
[MODIFY] dash_app/callbacks/import_callbacks.py   ← Thêm callback CSV sync
[MODIFY] dash_app/callbacks/global_callbacks.py   ← Render DataTable YTD mới
[MODIFY] dash_app/requirements.txt          ← Xóa reportlab, pdfkit
[NEW]    dash_app/pages/hcc_revenue.py      ← Layout báo cáo HCC
[NEW]    dash_app/callbacks/hcc_revenue_callbacks.py ← Callbacks cho HCC revenue
```

### RRI REQUIREMENTS MATRIX
| Blueprint Section       | Requirements       | Source (RRI Q#)     |
|-------------------------|--------------------|---------------------|
| Database & ETL          | REQ-016, REQ-017   | Q-11, Q-13, Q-14   |
| Backend Analytics       | REQ-018            | Scan GAP-1, Q-10   |
| Frontend Global         | REQ-019            | Q-01, Q-09          |
| Frontend BCCP/HCC       | REQ-020, REQ-021   | Q-02, Q-05, Q-08   |

### TASK DECOMPOSITION PREVIEW
Estimated Tasks: 5
├── TIP-001: ETL — CSV cấu trúc mới + sync_mappings.py + backup
├── TIP-002: Backend — Fix ten_cum + cache + format "-"
├── TIP-003: Frontend — Trang chủ DataTable YTD 4 màu
├── TIP-004: Frontend — HCC Revenue page + Routing /bccp + Xóa PDF
└── TIP-005: Frontend — Import UI (Upload CSV + nút Đồng bộ)
Estimated Effort: ~120 min

### CHECKPOINT
- [x] Architecture matches expectations (reuse stack, chỉ thêm module)
- [x] Design phù hợp (giữ nguyên design system, chỉ thêm bảng màu YTD)
- [x] Requirements đầy đủ (6 REQ-IDs, 15 RRI questions)
- [x] Task decomposition hợp lý (5 TIPs, dependency rõ ràng)
- [x] Không thiếu gì quan trọng

Reply "APPROVED" để tiếp tục.
