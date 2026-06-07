# BLUEPRINT: Dashboard BCCP v2.0
## Vibe Coding 8-Step v6.0

### PROJECT INFO
| Field | Value |
|-------|-------|
| Project | Dashboard Doanh thu BCCP — Nâng cấp Tổng thể |
| Nature | Web UI (Dashboard) + Analytics + Team scale (20+ users) |
| Date | 2026-06-07 |

### GOALS
**Primary Goal:** Nâng cấp dashboard hiện có để tối ưu bộ lọc (Topbar), cải thiện tốc độ (summary tables), thay đổi định nghĩa nghiệp vụ (KH mới, Churn) và tái cấu trúc giao diện các trang.

**Target Audience:** 20+ nhân viên bưu điện tỉnh, từ cấp tỉnh đến cấp cụm, không chuyên IT.

**Key Message:** Dashboard nhanh hơn, gọn hơn, đúng logic nghiệp vụ hơn.

---

### ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────┐
│                         BROWSER                              │
│  ┌──────────────── TOPBAR (Global Filters) ───────────────┐  │
│  │ [Năm][Chu kỳ][Tuần/Tháng] [Cụm][Xã/phường][Bưu cục]  │  │
│  │ [🔍 Áp dụng]   ← phân quyền: khóa cứng Cụm nếu user  │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌─────────┬─────────────────────────────────────────────┐   │
│  │SIDEBAR  │           CONTENT AREA                      │   │
│  │(Menu    │  [So sánh inline: ☐Kỳ trước ☐CK ☑KH]      │   │
│  │ only)   │  [KPI Cards + Biểu đồ + Bảng dữ liệu]     │   │
│  └─────────┴─────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│                    Dash Callbacks Layer                       │
│  topbar_callbacks.py → global_callbacks.py → kpi_callbacks   │
│  → new_customer_callbacks → retention_callbacks → ...        │
└──────────────────┬───────────────────────────────────────────┘
                   │ Đọc từ Summary Tables (nhanh)
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                    SQLite Database                            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐       │
│  │transactions  │  │agg_monthly   │  │plans          │       │
│  │(~1M raw)     │→ │agg_weekly    │  │plans_weekly   │       │
│  │              │  │agg_*_customer│  │               │       │
│  └─────────────┘  └──────────────┘  └───────────────┘       │
│  ┌─────────────┐  ┌──────────────┐                           │
│  │dim_buucuc   │  │new_customers │                           │
│  │dim_dichvu   │  │(+cột ngày)   │                           │
│  └─────────────┘  └──────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

---

### DESIGN SYSTEM
#### Colors
- Primary: `#2563EB` (Blue — Trust)
- Secondary: `#64748B` (Slate — Neutral)
- Accent: `#10B981` (Emerald — Growth positive), `#EF4444` (Red — Negative)
- Topbar BG: `#F8FAFC`, Border: `#E2E8F0`

#### Typography
- Headings + Body: Inter (giữ nguyên)

---

### TECH STACK
- **Giữ nguyên**: Python 3.13, Dash, dash-bootstrap-components, SQLite, Flask-Login, pandas, plotly, openpyxl, xlrd
- **Bổ sung**: Không có thư viện mới — chỉ thêm modules Python nội bộ

---

### FILE STRUCTURE (Chi tiết thay đổi)

#### Nhánh 1: `feat/db-summary` — Database & ETL

| Hành động | File | Mô tả |
|-----------|------|-------|
| [NEW] | `etl/aggregator.py` | Script tạo/refresh `agg_monthly`, `agg_monthly_customer`, cập nhật `agg_weekly` cho 2025 |
| [NEW] | `scripts/rebuild_summaries.py` | Entry point chạy rebuild tất cả summary tables |
| [MODIFY] | `config/week_calendar.py` | Thêm hàm `allocate_weekly_plan()` phân bổ KH tháng → tuần theo ngày lịch |
| [MODIFY] | `etl/importer.py` | Thêm trigger gọi aggregator sau mỗi lần import thành công |
| [MODIFY] | `analytics/new_customer_calculator.py` | Thêm cột `ngay_phat_sinh`, thêm điều kiện `cuoc_tt_tong > 0` |
| [MODIFY] | `analytics/customer_classifier.py` | Thêm điều kiện DT > 0 cho KHM/Tái bán |

#### Nhánh 2: `feat/topbar-auth` — Topbar Filters & Phân quyền

| Hành động | File | Mô tả |
|-----------|------|-------|
| [NEW] | `dash_app/components/topbar.py` | Component Topbar filters (Năm, Chu kỳ, Tuần/Tháng, Cụm, Xã/phường, Bưu cục, nút Áp dụng) |
| [NEW] | `dash_app/callbacks/topbar_callbacks.py` | Callbacks: cascade Cụm→Xã→BC, phân quyền `assigned_cum`, ẩn/hiện tuần/tháng |
| [MODIFY] | `dash_app/components/sidebar.py` | Bỏ toàn bộ bộ lọc, chỉ giữ menu điều hướng + profile box. Cập nhật cấu trúc menu mới |
| [MODIFY] | `dash_app/callbacks/sidebar_callbacks.py` | Bỏ callbacks bộ lọc cũ, chỉ giữ highlight active menu |
| [MODIFY] | `dash_app/app.py` | Tích hợp Topbar vào layout chính, cập nhật routing, đăng ký topbar callbacks |
| [MODIFY] | `dash_app/assets/style.css` | Thêm styles Topbar, thu gọn sidebar width |

#### Nhánh 3: `feat/pages-redesign` — Tái cấu trúc Pages & Callbacks

| Hành động | File | Mô tả |
|-----------|------|-------|
| [MODIFY] | `dash_app/pages/global_overview.py` | Layout mới: KPI 3 chỉ tiêu, Top 10 xã, biểu đồ 12 kỳ, 2 bảng YTD theo xã |
| [MODIFY] | `dash_app/callbacks/global_callbacks.py` | Logic mới: đọc summary, Top 10, 12 kỳ liên tiếp, 2 bảng kỳ/lũy kế, inline compare |
| [MODIFY] | `dash_app/pages/kpi_page.py` | Đổi thành "Tổng quan DV BCCP" — cấu trúc giống global nhưng cho nhóm con BCCP |
| [MODIFY] | `dash_app/callbacks/kpi_callbacks.py` | Logic mới cho Tổng quan DV BCCP |
| [MODIFY] | `dash_app/pages/service_overview.py` | Template chung cho HCC/TCBC/PPBL — cấu trúc giống global |
| [MODIFY] | `dash_app/callbacks/service_callbacks.py` | Logic chung cho các Tổng quan DV |
| [MODIFY] | `dash_app/pages/new_customer.py` | Layout mới: 3 chỉ số, bỏ KH/phân rã DV, Top KH 4 tháng |
| [MODIFY] | `dash_app/callbacks/new_customer_callbacks.py` | Logic 3 chỉ số, hỗ trợ tuần/tháng, bỏ kế hoạch |
| [MODIFY] | `dash_app/pages/retention.py` | Layout mới: 4 card biến động + 3 bảng chi tiết xuất Excel |
| [MODIFY] | `dash_app/callbacks/retention_callbacks.py` | Logic Churn 3 tháng, Duy trì dương, biến động tuần-tuần, 3 bảng |
| [MODIFY] | `dash_app/analytics/retention_metrics.py` | Cập nhật định nghĩa Churn, Duy trì, thêm hàm biến động tuần |
| [MODIFY] | `dash_app/analytics/global_metrics.py` | Đọc từ summary tables thay vì raw |
| [NEW] | `dash_app/pages/service_detail.py` | Trang Chi tiết sản phẩm dịch vụ |
| [NEW] | `dash_app/callbacks/service_detail_callbacks.py` | Callbacks cho trang SPDV |
| [DELETE] | `dash_app/pages/alerts.py` | Bỏ trang Cảnh báo doanh thu |
| [DELETE] | `dash_app/callbacks/alerts_callbacks.py` | Bỏ callbacks Cảnh báo |

---

### RRI REQUIREMENTS MATRIX → BLUEPRINT MAPPING

| Blueprint Section | Requirements | Mô tả |
|-------------------|-------------|-------|
| Nhánh 1: DB & ETL | REQ-001, REQ-002, REQ-003, REQ-004, REQ-018 | Bỏ lọc ngày, cùng kỳ YoY, KH tuần, summary tables, cột ngày KH mới |
| Nhánh 2: Topbar & Auth | REQ-005, REQ-006, REQ-007, REQ-008, REQ-009 | Topbar filters, inline compare, nút Áp dụng, cascade, phân quyền |
| Nhánh 3: Global Overview | REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015 | KPI 3 chỉ tiêu, Top 10, 12 kỳ, bỏ heatmap, 2 bảng YTD |
| Nhánh 3: Service Overview | REQ-016 | Tổng quan DV cho BCCP/HCC/TCBC/PPBL |
| Nhánh 3: BCCP Menu | REQ-017 | Đổi cấu trúc sidebar, bỏ alerts, thêm SPDV |
| Nhánh 3: New Customer | REQ-018→REQ-022, REQ-028 | Định nghĩa mới, 3 chỉ số, Top 4T, bỏ KH, lọc địa lý |
| Nhánh 3: Retention | REQ-023→REQ-027, REQ-028 | Churn 3 tháng, Duy trì dương, 3 bảng, tuần-tuần, lọc địa lý |

---

### TASK DECOMPOSITION PREVIEW

```
[feat/db-summary] — 4 TIPs
├── TIP-db-001: Tạo aggregator.py + bảng agg_monthly, agg_monthly_customer
├── TIP-db-002: Cập nhật agg_weekly cho 2025 + plans_weekly
├── TIP-db-003: Cập nhật new_customer_calculator (cột ngày, DT>0)
└── TIP-db-004: Tích hợp aggregator vào importer + script rebuild

[feat/topbar-auth] — 3 TIPs
├── TIP-topbar-001: Tạo topbar.py component + CSS
├── TIP-topbar-002: Tạo topbar_callbacks.py (cascade, phân quyền, ẩn/hiện)
└── TIP-topbar-003: Tích hợp topbar vào app.py, thu gọn sidebar

[feat/pages-redesign] — 6 TIPs
├── TIP-pages-001: Trang Tổng quan chung (layout + callbacks mới)
├── TIP-pages-002: Trang Tổng quan DV (BCCP, HCC, TCBC, PPBL)
├── TIP-pages-003: Trang KH mới (layout + callbacks + logic 3 chỉ số)
├── TIP-pages-004: Trang Retention (layout + callbacks + Churn + 3 bảng)
├── TIP-pages-005: Trang Chi tiết SPDV (mới) + bỏ Alerts
└── TIP-pages-006: Cập nhật routing app.py + sidebar menu + dọn dẹp

Tổng: 13 TIPs
```

---

### BRANCH PLAN

| # | Branch | Module | TIPs | Worktree Path | Dependencies |
|---|--------|--------|------|---------------|-------------|
| 1 | `feat/db-summary` | Database & ETL | TIP-db-001→004 | `E:\Projects\worktrees\Dashboard-BCCP\feat-db-summary` | None |
| 2 | `feat/topbar-auth` | Topbar & Auth | TIP-topbar-001→003 | `E:\Projects\worktrees\Dashboard-BCCP\feat-topbar-auth` | None |
| 3 | `feat/pages-redesign` | Pages & Callbacks | TIP-pages-001→006 | `E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign` | feat/db-summary + feat/topbar-auth |

#### Merge Order
```
feat/db-summary → feat/topbar-auth → feat/pages-redesign
```

#### Conflict Prevention
- **feat/db-summary**: chỉ sửa `etl/`, `analytics/`, `config/week_calendar.py`, `scripts/` — KHÔNG chạm `dash_app/`
- **feat/topbar-auth**: chỉ sửa `dash_app/components/`, `dash_app/callbacks/sidebar_callbacks.py`, `dash_app/callbacks/topbar_callbacks.py` (MỚI), `dash_app/app.py`, `dash_app/assets/style.css`
- **feat/pages-redesign**: chỉ sửa `dash_app/pages/`, `dash_app/callbacks/*_callbacks.py` (trừ sidebar & topbar), `analytics/retention_metrics.py`, `analytics/global_metrics.py`

> [!WARNING]
> **Xung đột tiềm ẩn**: `app.py` bị sửa ở cả nhánh 2 (tích hợp topbar) và nhánh 3 (routing). Giải pháp: Nhánh 2 merge trước, nhánh 3 rebase lên main đã merge nhánh 2 trước khi build.
>
> `analytics/retention_metrics.py` và `analytics/global_metrics.py` bị sửa ở cả nhánh 1 (đọc summary) và nhánh 3 (logic biến động). Giải pháp: Nhánh 1 chỉ thêm hàm helper mới, không sửa hàm cũ. Nhánh 3 sửa hàm cũ. Merge nhánh 1 trước.

---

### CONTRACT

#### DELIVERABLES
| # | Item | Details | Requirements |
|---|------|---------|-------------|
| 1 | Bảng trung gian + ETL | `agg_monthly`, `agg_monthly_customer`, `plans_weekly`, cập nhật `agg_weekly` 2025, cột ngày KH mới | REQ-001→004, REQ-018 |
| 2 | Topbar filters + Phân quyền | Component Topbar, cascade, phân quyền khóa cứng Cụm, nút Áp dụng | REQ-005→009 |
| 3 | Trang Tổng quan chung v2 | KPI 3 chỉ tiêu, Top 10 xã, 12 kỳ, 2 bảng YTD theo xã | REQ-010→015 |
| 4 | Trang Tổng quan DV (4 trang) | BCCP/HCC/TCBC/PPBL theo cấu trúc chung | REQ-016 |
| 5 | Sidebar menu mới | Cấu trúc lại, bỏ alerts, thêm SPDV | REQ-017 |
| 6 | Trang KH mới v2 | 3 chỉ số, bỏ KH, Top 4 tháng, hỗ trợ tuần | REQ-018→022, REQ-028 |
| 7 | Trang Retention v2 | Churn 3 tháng, Duy trì dương, 3 bảng xuất Excel, biến động tuần | REQ-023→027, REQ-028 |
| 8 | Trang SPDV | Chi tiết sản phẩm dịch vụ (khôi phục từ feat-ux-filters) | REQ-017 |

#### NOT INCLUDED
- Chuyển đổi sang PostgreSQL (pending task riêng)
- Kích hoạt lại authentication bắt buộc (chờ deploy chính thức)
- Import dữ liệu HCC/TCBC/PPBL (các bảng `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl` hiện 0 dòng — chờ Sếp nạp dữ liệu)
- Responsive mobile layout (Topbar sẽ responsive cơ bản nhưng không thiết kế riêng cho mobile)

---

### CHECKPOINT

- [ ] Kiến trúc đúng với mong đợi (Topbar + sidebar thu gọn + summary tables)
- [ ] Giao diện phù hợp (wireframe các trang chính)
- [ ] Yêu cầu đầy đủ (28 REQ-IDs đã được ánh xạ)
- [ ] Phân rã tác vụ hợp lý (13 TIPs trên 3 nhánh)
- [ ] Không thiếu sót gì quan trọng

> **Sếp trả lời "APPROVED" + "CONFIRM" để tôi tiến hành tạo TIPs chi tiết và worktrees.**
