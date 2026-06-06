TECH_STACK:
  Language: Python 3.13
  Framework: Dash
  Styling: Dash Bootstrap Components, Custom CSS
  Database: SQLite (dự kiến PostgreSQL)
  Auth: Flask-Login
  State: dcc.Store, Callbacks (Dash)
  Other: pandas, plotly

EXISTING_MODULES:
  - analytics: Xử lý logic tính toán doanh thu và khách hàng
  - config: Cấu hình hệ thống, Lịch tuần BCCP
  - dash_app/components: Sidebar, Topbar, KPI Cards, Data Table
  - dash_app/pages: Các trang chức năng (KPI, Retention, New Customer, HCC)
  - dash_app/callbacks: Tương tác và điều hướng dữ liệu (54 điểm gọi Input)

PATTERNS_DETECTED:
  - Cache Pattern: Sử dụng @functools.lru_cache ở tầng Data (utils.py)
  - Callback Pattern: Auto-load (Reactive) khi Dropdown thay đổi
  - Modularized Dash: Chia nhỏ App thành Components và Callbacks

REUSABLE_COMPONENTS:
  - dash_app/components/data_table.py — Bảng dữ liệu chuẩn hóa
  - dash_app/components/kpi_cards.py — Card KPI dùng chung

GAPS_DETECTED:
  - UI Gap: Topbar rườm rà bộ lọc thời gian.
  - Performance Gap: Các biểu đồ liên tục re-render khi người dùng chọn lọc do thiếu cơ chế Manual Load (State).
  - Logic Gap: Hàm query_revenue() phụ thuộc chặt vào "Chu kỳ" và "Năm", khó mở rộng tính toán Delta Days.
  - Feature Gap: Thiếu trang báo cáo phân tích riêng cho các Gói cước (SPDV).

CODE_HEALTH:
  Type Safety: Partial (Python type hints ở một số file)
  Linting: Not Configured
  Tests: None (Chỉ có test script thủ công)
  Debug Artifacts: Clean
  TODO/FIXME: 0 found

ESTIMATED_SIZE:
  Files: ~25 files (Python)
  Lines of Code: ~3500 lines
  Components/Modules: 12
  API Routes/Endpoints: N/A (Dash Pages)

COMPLEXITY_ASSESSMENT: Medium
