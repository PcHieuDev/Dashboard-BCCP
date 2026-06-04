# Completion Report: TIP-11-004

## 1. Kết quả thực hiện
- **Status**: DONE
- **Files modified**:
  - `analytics/retention_metrics.py`

## 2. Chi tiết thay đổi
- Định nghĩa lại `get_khhh_list(T)`: Thay vì quét 3 tháng trước, KHHH của tháng T chỉ đơn giản bằng tập khách hàng có giao dịch trong tháng T trừ đi tập khách hàng mới của tháng T. Rất nhanh vì chỉ cần đọc dữ liệu tháng T.
- Tính số lượng Mất, Tăng, Giảm: Giữ nguyên logic đối chiếu giữa `KHHH(T)` và `KHHH(T-1)`. Do cả 2 hàm đều chạy định nghĩa mới nên tốc độ cải thiện đáng kể. Khách hàng "Mất" là khách hàng thuộc `KHHH(T-1)` nhưng doanh thu ở `T` bằng 0.
- Cảnh báo rời mạng `get_churn_alerts`: Bỏ các subquery quét 3 tháng phức tạp, chỉ lấy tập `KHHH(T-1)` và so sánh doanh thu của họ ở tháng `T` so với `T-1`. Nếu giảm > 20% hoặc không có giao dịch > 7 ngày thì vào bảng cảnh báo.

## 3. Checklist Acceptance Criteria
- [x] Sửa định nghĩa get_khhh_list (trừ đi khách hàng mới của tháng T).
- [x] Trang `/bccp/retention` tải nhanh, không cần join/lọc 3-4 tháng dữ liệu.
- [x] Bảng Cảnh báo hiển thị dựa trên so sánh T và T-1.
