# Completion Report: TIP-11-001

## 1. Kết quả thực hiện
- **Status**: DONE
- **Files modified**:
  - `dash_app/callbacks/kpi_callbacks.py`
  - `dash_app/callbacks/utils.py`
  - `dash_app/pages/kpi_page.py`

## 2. Chi tiết thay đổi
- Chuyển logic lấy Top 10 CMS thành câu query `SELECT cms, SUM(cuoc_tt_tong)` trực tiếp từ bảng `transactions` để tránh lỗi nhân bản doanh thu khi JOIN với `dim_buucuc` (khi một bưu cục có nhiều record trong dim_buucuc). Logic JOIN chỉ được dùng riêng biệt bằng subquery hoặc IN để filter.
- Xóa `chart-customer-area` khỏi giao diện, mở rộng container bảng Top CMS ra `lg=12`.
- Cập nhật hàm `get_bccp_week_number` trả về 1 nếu tính ra tuần 53.

## 3. Checklist Acceptance Criteria
- [x] Top 10 CMS hiển thị doanh thu hợp lý.
- [x] Bảng Top CMS chiếm full width hoặc bố cục đẹp.
- [x] Không còn Area chart trên UI.
- [x] Biểu đồ line chart theo tuần không xuất hiện "Tuần 53".
