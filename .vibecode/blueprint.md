# BLUEPRINT: Dashboard Doanh thu BCCP (feat-ux-filters)
## Vibe Coding 8-Step v6.0

### PROJECT INFO
| Field | Value |
|-------|-------|
| Project | Dashboard Doanh thu BCCP |
| Nature | Data Visualization + Dashboard Interaction + Medium Scale |
| Date | 2026-06-05 |

### GOALS
**Primary Goal:** Refactoring diện rộng để Tách Topbar, chuyển cơ chế sang Manual Load (State) chống giật lag, tinh gọn lại bộ lọc Ngày và bổ sung Trang phân tích SPDV.
**Target Audience:** Ban Giám đốc, Các bộ phận kinh doanh BCCP (20+ users).
**Key Message:** Nhanh gọn, Tối ưu, và Lọc chủ động.

### ARCHITECTURE
Mô hình "User-Driven Load": Chuyển từ "Reactive Callback" sang "Stateful Trigger". Toàn bộ Data Layer (`utils.py`, `revenue.py`) chuyển sang giao thức nhận `start_date` và `end_date` (liên tục) thay cho vector (Năm, Chu kỳ, Tuần, Tháng). Bổ sung module Trang SPDV hoàn toàn độc lập nhưng tái sử dụng bộ lọc từ Topbar.

### DESIGN SYSTEM (nếu UI project)
#### Layout Pattern (Topbar)
```text
┌────────────────────────────────────────────────────────┐
│ [Từ ngày - Đến ngày]         [So sánh]                 │
├────────────────────────────────────────────────────────┤
│ [Đơn vị: Cụm/BC/Huyện]       [Nút Áp dụng bộ lọc 🔍]    │
└────────────────────────────────────────────────────────┘
```
#### Colors
Primary: (Kế thừa Dash Bootstrap) | Secondary: (Kế thừa) | Accent: (Kế thừa)

### TECH STACK
Python 3.13, Dash, SQLite, pandas, plotly.

### FILE STRUCTURE
```text
dash_app/
├── components/
│   ├── topbar.py (Thiết kế lại theo 2 hàng ngang)
│   └── sidebar.py (Thêm Link SPDV)
├── callbacks/
│   ├── utils.py (Đổi logic start_date/end_date)
│   ├── [7 file callbacks cũ] (Đổi từ Input sang State)
│   ├── service_analysis_callbacks.py [NEW]
│   └── global_callbacks.py (Chặn ngày)
├── pages/
│   └── service_analysis.py [NEW]
analytics/
└── revenue.py (Bỏ chu_ky, nam)
config/
└── week_calendar.py (Đổi logic delta days)
```

### RRI REQUIREMENTS MATRIX
| Blueprint Section | Requirements | Source (RRI Q#) |
|-------------------|-------------|-----------------|
| UI Components     | REQ-001 (Topbar 2 hàng), REQ-003 (Chặn ngày) | RRI Q#1, Q#3, Feedback |
| Interaction       | REQ-002 (Manual Load toàn bộ trang)   | RRI Q#2      |
| Data Utilities    | REQ-004 (Delta days), REQ-005 (Kế hoạch)| RRI Q#3      |
| New Features      | REQ-006 (Trang SPDV)                  | Phụ lục      |

### TASK DECOMPOSITION PREVIEW
Estimated Tasks: 6
├── TIP-001: Data Core Refactoring (`utils.py`, `revenue.py`, `week_calendar.py`)
├── TIP-002: Topbar UI Redesign (2 hàng) & Limit Date Callback
├── TIP-003: Manual Load Migration - Khối Báo cáo Tổng quan (KPI, Service)
├── TIP-004: Manual Load Migration - Khối Chi tiết Khách hàng (Customer, New, Retention)
├── TIP-005: Manual Load Migration - Khối HCC & Cảnh báo
└── TIP-006: Trang Thống kê Sản phẩm Dịch vụ (UI & Logic)
Estimated Effort: 150 min

### CHECKPOINT
- [x] Architecture matches expectations
- [x] Design phù hợp (Layout Topbar 2 hàng)
- [x] Requirements đầy đủ (từ RRI)
- [x] Task decomposition hợp lý
- [x] Không thiếu gì quan trọng

Reply "APPROVED" để tiếp tục.
