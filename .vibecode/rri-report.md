# RRI REPORT: Dashboard BCCP — Sửa lỗi & Tối ưu giao diện (5 yêu cầu)
Generated: 2026-06-07
Role: Contractor (Chủ thầu)
User (Boss): Sếp

---

## 1. KẾT QUẢ PHỎNG VẤN & QUYẾT ĐỊNH THIẾT KẾ (DECISIONS LOG)

### Quyết định 1: Bộ lọc & Đồng bộ dữ liệu các trang dịch vụ con (BCCP, HCC, TCBC, PPBL)
*   **Vấn đề:** Các trang dịch vụ con không hoạt động khi lọc địa lý (Cụm, Xã, Bưu cục) và bị ẩn Topbar bộ lọc.
    *   Mặc dù dữ liệu các dịch vụ HCC, TCBC, PPBL được nạp gộp từ file Excel, do định dạng file import có các cột khoảng ngày (Từ ngày/Tháng/Năm đến Đến ngày/Tháng/Năm) nên hệ thống vẫn để bộ lọc hoạt động bình thường cho cả Tuần và Tháng. Khi aggregate dữ liệu, hệ thống sẽ tự động chia trung bình ngày để phân bổ đều doanh thu/sản lượng vào các tuần/tháng tương ứng.
    *   Cập nhật các callback cập nhật dashboard và bảng chi tiết xã trong `service_callbacks.py` để nhận thêm 3 `State` địa lý: `sidebar-cum`, `sidebar-bdx`, `sidebar-buu-cuc` và áp dụng lọc vào SQL query.
    *   Trang HCC sẽ load đúng dữ liệu từ bảng `transactions_hcc` (dịch vụ chuyển phát HCC). Các trang TCBC, PPBL sẽ load từ `transactions_tcbc`, `transactions_ppbl`.

### Quyết định 2: Giao diện bảng Bưu cục Xã (Yêu cầu 2)
*   **Vấn đề:** Mỗi xã xuất hiện nhiều lần do gom nhóm theo mã bưu cục chấp nhận.
*   **Giải pháp thống nhất:** 
    *   Gom nhóm dữ liệu theo Mã xã (`ma_bdx`) và Tên xã (`ten_bdx`) để cộng dồn doanh thu của tất cả bưu cục thuộc cùng một xã thành một dòng duy nhất.
    *   Trên bảng hiển thị, cột "Xã / Bưu cục" sẽ chỉ hiển thị "Tên Xã" (ví dụ: "Bưu điện xã Anh Sơn"), loại bỏ hiển thị mã bưu cục/mã xã để giao diện sạch sẽ, gọn gàng theo mong muốn của Sếp.

### Quyết định 3: Tái cấu trúc trang Chi tiết Khách hàng (`/bccp/customer`) (Yêu cầu 4)
*   **Vấn đề:** Giao diện bộ lọc nâng cao rườm rà, có nút Lọc không cần thiết, bảng hiển thị chưa đúng định dạng.
*   **Giải pháp thống nhất:**
    *   Loại bỏ hoàn toàn tính năng "xoay chiều tự do" (bỏ bảng xoay chiều ở trên cùng các dropdown `Chiều phân tích chính/phụ`).
    *   Chỉ hiển thị một bảng kết quả duy nhất ở dưới hiển thị chi tiết theo từng khách hàng (Mã CMS). Bảng này sẽ có các cột cố định: `Tên cụm`, `Tên xã`, `Bưu cục chấp nhận`, `Mã CMS`, `Sản lượng`, `Doanh thu (không VAT)`.
    *   Gộp bộ lọc "Nhóm dịch vụ" vào trong phần bộ lọc nâng cao inline (đưa lên hàng đầu cùng với các bộ lọc Loại khách hàng, Trạng thái hợp đồng).
    *   Không sử dụng nút "Lọc" riêng biệt tại phần bộ lọc nâng cao; dữ liệu sẽ tự động cập nhật khi người dùng nhấn nút "Áp dụng" trên Topbar hoặc thay đổi các bộ lọc inline.

### Quyết định 4: Sửa lỗi Sidebar điều hướng (Yêu cầu 1 & 4)
*   **Giải pháp thống nhất:**
    *   Cập nhật callback điều hướng để khi `pathname` không bắt đầu bằng `/bccp` (như khi ở `/` hoặc `/hcc`), thuộc tính `active_item` của Accordion sẽ được set thành `None` (hoặc rỗng) để đóng accordion "Bưu chính chuyển phát" lại.
    *   Tối ưu CSS của accordion button để khi đóng, tiêu đề "Bưu chính chuyển phát" không bị bôi nền xám (chỉ sáng khi chính nó hoặc trang con bên trong đang hoạt động).
    *   Đảm bảo link con đang chọn (ví dụ: "Chi tiết khách hàng" khi ở `/bccp/customer`) được highlight nổi bật bằng màu xanh đặc trưng của BCCP.

    *   Thêm 2 biểu đồ cột xếp chồng lần lượt từ trên xuống (không đặt nằm ngang hàng vì có nhiều mã sản phẩm sẽ làm biểu đồ quá nhỏ): Doanh thu theo mã SPDV và Sản lượng theo mã SPDV.
    *   Bảng thống kê doanh thu theo mã SPDV được đưa xuống dưới cùng của trang và bổ sung thêm cột "Sản lượng".
    *   Gỡ bỏ biểu đồ "Cơ cấu tỷ trọng doanh thu theo nhóm dịch vụ".

---

## 2. MA TRẬN YÊU CẦU & MÃ HÓA (REQUIREMENTS MATRIX)

| Mã REQ | Mô tả yêu cầu | File ảnh hưởng trực tiếp | Mức độ ưu tiên |
| :--- | :--- | :--- | :--- |
| **REQ-UX-001** | Sidebar đóng/mở đúng accordion theo trang, highlight đúng link con đang active, không bôi xám accordion button khi đóng. | `sidebar.py`, `sidebar_callbacks.py`, `style.css` | P0 (Cao nhất) |
| **REQ-DATA-001** | Gom nhóm bảng Bưu cục Xã theo xã (`ma_bdx`), cộng dồn doanh thu, chỉ hiển thị Tên Xã ở cột Xã. | `global_metrics.py`, `service_callbacks.py` | P0 (Cao nhất) |
| **REQ-SVC-001** | Sửa lỗi các trang dịch vụ con: hiện bộ lọc Topbar, hỗ trợ lọc theo địa lý (Cụm, Xã, Bưu cục), khóa chu kỳ Tháng khi xem HCC/TCBC/PPBL. | `sidebar_callbacks.py`, `service_callbacks.py`, `service_overview.py` | P0 (Cao nhất) |
| **REQ-CUST-001** | Tái cấu trúc `/bccp/customer`: Bỏ bảng xoay chiều, cố định các cột bảng CMS dưới, gộp bộ lọc Nhóm dịch vụ, bỏ nút Lọc riêng. | `customer_detail.py`, `customer_callbacks.py` | P0 (Cao nhất) |
| **REQ-DET-001** | Tái cấu trúc `/bccp/service-detail`: Thêm 2 biểu đồ doanh thu & sản lượng theo mã SPDV, hạ bảng thống kê thêm cột sản lượng, bỏ biểu đồ cơ cấu tỷ trọng. | `service_detail.py`, `service_detail_callbacks.py` | P0 (Cao nhất) |
