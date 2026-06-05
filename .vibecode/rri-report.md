# RRI REPORT: Dashboard Doanh thu BCCP (Nhánh feat-ux-filters)
Generated: 2026-06-05
Complexity: Medium
Questions Asked: 3 (Smart-Asked) + 25 (Auto-Answered từ project_state.md) across 5 personas

## REQUIREMENTS MATRIX
| REQ-ID  | Requirement          | Source    | Priority | Persona    |
|---------|----------------------|-----------|----------|------------|
| REQ-001 | Tinh gọn Topbar, chỉ giữ Lọc Từ ngày - Đến ngày | RRI Q#1  | P0       | End User   |
| REQ-002 | Manual Load: Không tự auto-load, phải bấm nút | RRI Q#2  | P0       | End User   |
| REQ-003 | Chặn chọn ngày quá 1 tháng ở Khách hàng Mới/HH | RRI Q#3  | P1       | Business   |
| REQ-004 | So sánh Cùng kỳ/Kỳ trước bằng delta days | RRI Q#3  | P0       | Business   |
| REQ-005 | Tính KPI Kế hoạch theo Tháng tương ứng | RRI Q#3  | P1       | Business   |
| REQ-006 | Bổ sung trang Thống kê Sản phẩm Dịch vụ (Gói cước)| Phụ lục  | P0       | Operator   |

## AUTO-ANSWERED (from Scan & project_state.md)
- **AUTH**: Đã có `Flask-Login` (tạm tắt trong dev), phân quyền theo Cụm → Reuse.
- **DB**: SQLite hiện tại, thiết kế DB-agnostic để lên PostgreSQL → Reuse cấu trúc query.
- **BUSINESS RULES**: Vãng lai CMS null, Khách hàng KHM/Tái bán tính theo 3 tháng → Reuse logic `analytics/revenue.py`.
- **ARCHITECTURE**: Dash modularized (components, callbacks, pages) → Reuse cấu trúc file.

## DECISIONS LOG
| Decision | Options Considered | Chosen | Rationale |
|----------|--------------------|--------|-----------|
| [D-001]  | Tách Topbar (Chỉ Ngày vs Cả Ngày & Không gian) | Cả Ngày & Không gian | Gom toàn bộ bộ lọc toàn cục lên Topbar để Sidebar chỉ dành cho điều hướng. |
| [D-002]  | Tinh gọn bộ lọc Ngày | Giữ DateRange (Từ ngày-Đến ngày) | Trực quan nhất, bỏ các dropdown rườm rà (Năm/Tháng/Tuần) dễ gây lỗi chéo. |
| [D-003]  | Logic So sánh | Tính theo tham số (Tháng/Năm) vs Delta days | Dùng Delta days (khoảng thời gian tương ứng) để linh hoạt mọi DateRange. |

## OPEN QUESTIONS
- Không còn câu hỏi mở. Tất cả REQ-IDs đã được mapping.
