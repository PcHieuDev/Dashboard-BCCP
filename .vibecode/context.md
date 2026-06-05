# PROJECT CONTEXT: Dashboard Doanh thu BCCP
Generated: 2026-06-05 | For: Builder (Thợ thi công)

## 1. Project Overview
Dự án Dashboard Doanh thu BCCP phục vụ BĐVN. Đợt nâng cấp này tập trung vào cấu trúc lại Topbar thành 2 hàng bộ lọc, đổi cơ chế từ tự động load biểu đồ sang "Manual Load" (ấn nút mới load) để giảm tải, đồng thời làm 1 trang mới là Thống kê SP-DV.

## 2. Tech Stack & Conventions
- Language: Python 3.13
- Framework: Dash + Dash Bootstrap Components
- Database: SQLite
- Data processing: pandas

## 3. Architecture (tóm tắt)
- Data Layer: Các truy vấn SQLite nằm ở `analytics/revenue.py`, được gói qua cache layer ở `dash_app/callbacks/utils.py`. Data Layer nhận tham số `start_date`, `end_date`.
- UI Layer: Layout chính định nghĩa bởi `app.py` và `components/topbar.py`.
- Controllers: Nằm trong folder `dash_app/callbacks/`. Toàn bộ sẽ phải listen `btn-apply-filter` bằng `Input` và đọc các bộ lọc bằng `State`.

## 4. Key Decisions (từ RRI)
| Decision | Chosen | Rationale |
|----------|--------|-----------|
| D-001  | Topbar 2 hàng | Rõ ràng phân tách thời gian vs không gian. |
| D-002  | Manual Load | Không load lung tung khi đổi 1 filter nhỏ. |
| D-003  | So sánh Delta Days | Khoảng lùi ngày tỷ lệ thuận với số ngày chọn. |
| D-004  | Chặn ngày | Max 31 ngày ở các trang chi tiết KH để tránh treo DB. |

> Chi tiết đầy đủ → đọc `.vibecode/blueprint.md`
