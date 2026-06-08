# RRI REPORT: Dashboard Doanh thu BCCP
Generated: 2026-06-08
Complexity: Medium
Questions Asked: 4 issues analyzed

## REQUIREMENTS MATRIX
| REQ-ID  | Requirement          | Source    | Priority | Persona    |
|---------|----------------------|-----------|----------|------------|
| REQ-001 | Sửa lỗi Sidebar luôn mở "Bưu chính chuyển phát" | User (Issue 1) | P1 | End User |
| REQ-002 | Đồng bộ trạng thái bộ lọc Topbar khi chuyển trang | User (Issue 2) | P1 | End User |
| REQ-003 | Áp dụng bộ lọc Địa lý (Cụm) cho trang Tổng quan | User (Issue 2) | P0 | End User |
| REQ-004 | Sửa lỗi tính toán "Kỳ trước" và "Cùng kỳ" ở trang Tổng quan | User (Issue 3) | P0 | Business |
| REQ-005 | Hiển thị giá trị "Kỳ trước" / "Cùng kỳ" ở thẻ so sánh trang /bccp | User (Issue 4) | P1 | Business |

## AUTO-ANSWERED (từ mã nguồn)
- **Cơ chế tính Kế hoạch (Tổng quan)**: Hệ thống lấy tổng từ bảng `plans` theo tháng/tuần tương ứng, nhưng hiện tại KHÔNG truyền tham số `cum` vào hàm `get_plans_current_period`, dẫn đến không lọc được theo Cụm.
- **Cơ chế tính Kỳ trước/Cùng kỳ (Tổng quan)**: Hoàn toàn chính xác như Sếp đã chỉ ra, cột `nhom_dich_vu` trong `agg_monthly` chứa đúng cấp "Nhóm dịch vụ" (Truyền thống, TMĐT, v.v.). Tuy nhiên, logic code ở trang Tổng quan chung lại dùng thẳng giá trị "Truyền thống", "TMĐT" này để đem đi so khớp với danh sách các "Nhóm chính" (`["BCCP", "HCC", "TCBC", "PPBL"]`). Do "Truyền thống" không khớp với chữ "BCCP" nên kết quả không được cộng dồn vào, dẫn đến giá trị bằng 0.
- **Nguyên nhân /bccp không hiện So sánh**: Hàm render ẩn hoàn toàn khối so sánh nếu doanh thu kỳ trước `val_prev == 0` hoặc do truyền thiếu năm (`nam`) vào hàm `query_revenue` cho kỳ trước.

## DECISIONS LOG
| Decision | Options Considered | Chosen | Rationale |
|----------|--------------------|--------|-----------|
| [D-001] Sửa lỗi SQL trang Tổng quan | 1. Sửa trực tiếp SQL JOIN với dim_dichvu<br>2. Sửa file aggregator.py | 1 | Tránh phải chạy lại ETL quá khứ, giải quyết triệt để tại logic render (global_metrics.py). |
| [D-002] Khắc phục bộ lọc Cụm bị bỏ qua | 1. Bổ sung tham số `cum` vào các lời gọi hàm ở global_callbacks.py | 1 | Nhanh gọn, đúng thiết kế ban đầu. |

## OPEN QUESTIONS
- [OQ-001]: Sếp muốn Sidebar khi chuyển trang thì: (A) Tự động mở menu chứa trang đó và đóng các menu khác, hay (B) Giữ nguyên trạng thái đóng/mở cuối cùng mà Sếp đã thao tác?
- [OQ-002]: Về bộ lọc Topbar bị reset khi chuyển trang, Sếp có muốn thiết lập cơ chế "Lưu trạng thái bộ lọc vào Local Storage" để trình duyệt nhớ luôn cả khi F5 tải lại trang không?
