# CONTRACT — Hợp đồng cam kết thực hiện
Generated: 2026-06-07
Role: Contractor (Chủ thầu)
User (Boss): Sếp

---

## 1. PHẠM VI CÔNG VIỆC (SCOPE OF WORK)

Nhận bàn giao và cam kết hoàn thành 5 hạng mục sửa lỗi & nâng cấp trải nghiệm giao diện trên hệ thống Dashboard doanh thu BCCP:
1.  **Sidebar & Accordion:** Sửa lỗi chuyển trang accordion tự đóng/mở và highlight rõ ràng liên kết con đang xem, không bôi xám accordion header khi đóng.
2.  **Bảng bưu cục xã:** Gom nhóm dữ liệu theo mã xã 4 số và tên xã để cộng dồn doanh thu, chỉ hiển thị cột "Tên Xã" (không bị lặp lại xã).
3.  **Trang con dịch vụ con:** Sửa lỗi các trang chủ dịch vụ con (/bccp, /hcc, /tcbc, /ppbl) không load dữ liệu. Tích hợp bộ lọc địa lý và thời gian trên Topbar, phân bổ doanh thu trung bình ngày cho các dịch vụ nạp gộp để lọc tuần/tháng chính xác.
4.  **Tái cấu trúc `/bccp/customer`:** Bỏ bảng xoay chiều, cố định bảng CMS ở dưới hiển thị các cột yêu cầu, gộp bộ lọc nhóm dịch vụ, bỏ nút Lọc riêng biệt.
5.  **Tái cấu trúc `/bccp/service-detail`:** Bổ sung 2 biểu đồ cột xếp chồng lần lượt, đưa bảng thống kê xuống dưới cùng thêm cột sản lượng, bỏ biểu đồ cơ cấu tỷ trọng.

---

## 2. KẾT QUẢ BÀN GIAO (DELIVERABLES)

*   **Mã nguồn hoàn chỉnh:** Các file Python (`importer.py`, `aggregator.py`, `global_metrics.py`, `service_callbacks.py`, `customer_detail.py`, `customer_callbacks.py`, `service_detail.py`, `service_detail_callbacks.py`, `sidebar_callbacks.py`, `global_callbacks.py`) được chỉnh sửa sạch sẽ, không có code thừa.
*   **CSS tối ưu:** File `style.css` được cập nhật định dạng sidebar accordion trực quan.
*   **Cơ sở dữ liệu nâng cấp:** Các bảng giao dịch dịch vụ con được bổ sung các cột khoảng ngày.
*   **Báo cáo kiểm thử:** Chạy thử nghiệm thành công toàn bộ dashboard không phát sinh exception, số liệu gộp xã chính xác.

---

## 3. LOẠI TRỪ (EXCLUSIONS)

*   Không thay đổi hoặc thiết kế lại cấu trúc bảng phân quyền người dùng (RBAC) ngoài phạm vi sidebar.
*   Không can thiệp vào các dịch vụ khác ngoài 4 dịch vụ chính (BCCP, HCC, TCBC, PPBL).
*   Không sử dụng Tailwind CSS hay bất kỳ thư viện CSS ngoài nào khác.
