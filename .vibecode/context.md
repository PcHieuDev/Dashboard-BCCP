# PROJECT CONTEXT: Dashboard BCCP v2.0
Generated: 2026-06-07 | For: Builder

## 1. Project Overview
Dashboard doanh thu bưu chính chuyển phát (BCCP) phục vụ 20+ người dùng nội bộ bưu điện tỉnh. Hệ thống hiển thị KPI, biểu đồ và bảng dữ liệu doanh thu theo nhiều chiều (thời gian, địa lý, dịch vụ, khách hàng). Dữ liệu được import từ Excel vào SQLite. Truy cập qua Cloudflare Tunnel tại `dashboard.bdna.io.vn`.

Nâng cấp v2.0 tập trung: chuyển bộ lọc lên Topbar, tạo bảng trung gian tối ưu tốc độ, cập nhật định nghĩa nghiệp vụ (KH mới, Churn), tái cấu trúc giao diện.

## 2. Tech Stack & Conventions
- **Language**: Python 3.13
- **Framework**: Dash + dash-bootstrap-components
- **Database**: SQLite (`E:/OneDrive/z.Database-TTKD-Data/dashboard.db`)
- **Auth**: Flask-Login (`dash_app/db/auth.py`) — User có `role`, `assigned_cum`
- **Styling**: Vanilla CSS (`dash_app/assets/style.css`)
- **Naming**: snake_case cho Python, kebab-case cho CSS classes
- **File organization**: Pages trong `dash_app/pages/`, callbacks tương ứng trong `dash_app/callbacks/`, analytics trong `analytics/`
- **Encoding**: UTF-8 toàn bộ. Trên Windows cần `sys.stdout.reconfigure(encoding='utf-8')` khi print tiếng Việt.

## 3. Architecture (summary)
```
dash_app/app.py (entry point, routing, layout chính)
  → components/topbar.py [MỚI] (bộ lọc toàn cục)
  → components/sidebar.py (menu điều hướng)
  → pages/*.py (layout từng trang)
  → callbacks/*.py (logic xử lý sự kiện)
     → analytics/*.py (tính toán nghiệp vụ)
        → SQLite DB (summary tables + raw transactions)

config/settings.py → DB_PATH, COLUMN_NAMES, SERVICE_TABLES
config/week_calendar.py → lịch tuần (Thứ 6→Thứ 5), hàm so sánh kỳ
etl/importer.py → import Excel vào DB
```

Key entry points:
- `dash_app/app.py` — Khởi chạy Dash server, routing URL → page layout
- `etl/importer.py` — Import dữ liệu Excel
- `scripts/rebuild_summaries.py` [MỚI] — Rebuild tất cả summary tables

## 4. Key Decisions (from RRI)
| Decision | Chosen | Rationale |
|----------|--------|-----------|
| Phân bổ kế hoạch tuần | Số ngày lịch (calendar days) | Đơn giản, không phụ thuộc lịch nghỉ |
| Top 10 ranking | Tỷ lệ % tăng trưởng/hoàn thành | Công bằng giữa xã quy mô khác nhau |
| Phân quyền tài khoản cụm | Khóa Cụm, cho chọn Xã/Bưu cục con | Bảo mật + linh hoạt |
| Retention khi lọc Tuần | So sánh tuần-tuần | Theo dõi biến động nhanh |
| KH mới khi lọc Tuần | Giữ logic tháng, hiển thị tuần | Định nghĩa KH mới theo tháng |

## 5. Patterns to Follow
- **Callback pattern**: Mỗi trang có `register_xxx_callbacks(app)` trong file riêng, đăng ký ở `app.py`
- **DB access**: `sqlite3.connect(str(DB_PATH))` trong mỗi hàm, đóng bằng `finally: conn.close()`
- **Filter flow**: Topbar state lưu trong `dcc.Store` → nút "Áp dụng" → trigger callback qua `Input("btn-apply-filter", "n_clicks")` + `State(...)` các filter
- **Revenue formatting**: Dùng `format_revenue()` từ `callbacks/utils.py`
- **Export Excel**: Dùng pattern trong `callbacks/export_helpers.py`

> For full details → read `.vibecode/blueprint.md`
