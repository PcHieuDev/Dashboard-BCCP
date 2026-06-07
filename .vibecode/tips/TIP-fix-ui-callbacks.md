# TIP-fix-ui-callbacks: Chỉnh sửa Giao diện, Callbacks và Hiển thị
Generated: 2026-06-07
Branch: feat-ui-analytics
Priority: High
Dependencies: TIP-fix-db-etl

---

## 1. MỤC TIÊU (OBJECTIVE)
Sửa đổi giao diện, callbacks và logic hiển thị để xử lý các lỗi hiển thị sidebar, trùng lặp bưu cục xã, đồng bộ bộ lọc địa lý các trang con, và tái cấu trúc trang `/customer` và `/service-detail`.

---

## 2. YÊU CẦU CHI TIẾT (SPECIFICATIONS)

### 2.1 Hiển thị Tổng quan chung (global_metrics.py & global_callbacks.py)
*   Cập nhật các truy vấn SQL từ `agg_monthly` / `agg_weekly` để `LEFT JOIN` với `dim_dichvu` quy đổi về `nhom_chinh` (`'BCCP'`, `'HCC'`, `'TCBC'`, `'PPBL'`) trước khi GROUP BY/SELECT.
*   **Sửa lỗi trùng lặp xã ở bảng chi tiết xã:**
    *   Truy vấn doanh thu theo bưu cục rồi join với `dim_buucuc` lấy `ma_bdx`, `ten_bdx`, `ten_cum`.
    *   Sử dụng Pandas `groupby(['ten_cum', 'ten_bdx', 'ma_bdx'], as_index=False).sum()` để gộp các bưu cục cùng xã lại.
    *   Bảng hiển thị chỉ hiển thị cột `Cụm` và `Xã / Bưu cục` (chứa Tên Xã từ `ten_bdx`), không hiển thị mã xã/mã bưu cục.

### 2.2 Sidebar & Điều hướng (sidebar_callbacks.py & style.css)
*   **Topbar bộ lọc:** Sửa callback `update_sidebar_state` để luôn hiển thị Topbar (`{"display": "block"}`) trên toàn bộ các trang (kể cả `/hcc`, `/tcbc`, `/ppbl`).
*   **Đóng accordion tự động:** Khi `pathname` không bắt đầu bằng `/bccp`, gán `active_accordion = None` gửi về `sidebar-accordion` để tự động thu gọn accordion "Bưu chính chuyển phát".
*   **Highlight:**
    *   Sửa CSS hoạt động của liên kết con: `.sidebar-menu-item.active.active-bccp` hiển thị màu xanh đặc trưng rõ ràng.
    *   Sửa CSS của accordion button: khi accordion đóng, button không có màu nền xám nhạt (`.sidebar-accordion .accordion-button.collapsed`).

### 2.3 Các trang con và bộ lọc địa lý (service_callbacks.py & service_overview.py)
*   Cập nhật callback `update_service_dashboard`, `update_service_table_a`, `update_service_table_b` trong `service_callbacks.py` để nhận thêm 3 `State` bộ lọc địa lý: `sidebar-cum`, `sidebar-bdx`, `sidebar-buu-cuc`.
*   Lọc DataFrame kết quả theo các giá trị bộ lọc địa lý này.
*   **Sắp xếp thứ tự dịch vụ BCCP:** Nếu `service_key == "BCCP"`, sắp xếp danh sách `sub_services` theo đúng thứ tự: **Truyền thống, TMĐT, Quốc tế, Phát hành báo chí**.
*   **Sửa lỗi trùng lặp xã:** Xử lý dồn dòng theo xã (`ten_bdx`) tương tự như ở trang Tổng quan chung.

### 2.4 Trang Chi tiết khách hàng (/bccp/customer)
*   **pages/customer_detail.py:**
    *   Bỏ bảng xoay chiều ở trên cùng các dropdown `revenue-g1`, `revenue-g2`, `revenue-compare-opt`.
    *   Đưa dropdown "Nhóm dịch vụ" lên hàng bộ lọc nâng cao. Loại bỏ nút Lọc riêng biệt.
*   **callbacks/customer_callbacks.py:**
    *   Bảng chi tiết khách hàng CMS cố định các cột: `Cụm`, `Xã / Phường`, `Bưu cục chấp nhận`, `Mã CMS`, `Sản lượng`, `Doanh thu không VAT`.
    *   Bộ lọc hoạt động tự động khi bấm nút "Áp dụng" trên Topbar hoặc thay đổi bộ lọc inline.

### 2.5 Trang Chi tiết sản phẩm dịch vụ (/bccp/service-detail)
*   **pages/service_detail.py & callbacks/service_detail_callbacks.py:**
    *   Bổ sung 2 biểu đồ cột xếp chồng lần lượt từ trên xuống: Doanh thu theo mã SPDV và Sản lượng theo mã SPDV.
    *   Bảng thống kê doanh thu theo mã SPDV đưa xuống dưới cùng và thêm cột sản lượng.
    *   Lược bỏ biểu đồ cơ cấu tỷ trọng doanh thu theo nhóm dịch vụ.

---

## 3. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)
1.  Bảng chi tiết xã ở trang chủ và các trang con chỉ hiển thị một dòng duy nhất cho mỗi xã, không bị lặp tên xã.
2.  Lọc địa lý trên Topbar hoạt động và cập nhật số liệu chính xác cho tất cả các trang con.
3.  Khi chuyển sang trang không phải BCCP, accordion "Bưu chính chuyển phát" tự động đóng lại, tiêu đề không bị sáng xám. Link con đang chọn được highlight xanh rõ ràng.
4.  Trang `/bccp/customer` hiển thị đúng bảng duy nhất với đầy đủ các cột yêu cầu, không có nút Lọc riêng.
5.  Trang `/bccp/service-detail` hiển thị đúng 2 biểu đồ xếp dọc và bảng thống kê đặt dưới cùng có cột sản lượng.
6.  Thứ tự dịch vụ BCCP hiển thị đúng: Truyền thống, TMĐT, Quốc tế, Phát hành báo chí.
