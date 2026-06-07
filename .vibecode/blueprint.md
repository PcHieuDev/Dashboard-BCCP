# BLUEPRINT — Chi tiết thiết kế kỹ thuật (Sửa 5 lỗi/yêu cầu)
Generated: 2026-06-07
Role: Contractor (Chủ thầu)
Status: DRAFT → Chờ Sếp phê duyệt (APPROVED)

---

## 1. THIẾT KẾ CƠ SỞ DỮ LIỆU & LUỒNG ETL

### 1.1 ALTER TABLE (Cập nhật bảng giao dịch dịch vụ con)
Bổ sung các trường thời gian vào các bảng `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl` để lưu khoảng ngày thô:
*   `tu_ngay` (INTEGER DEFAULT 1)
*   `tu_thang` (INTEGER DEFAULT 1)
*   `tu_nam` (INTEGER)
*   `den_ngay` (INTEGER DEFAULT 30)
*   `den_thang` (INTEGER DEFAULT 12)
*   `den_nam` (INTEGER)

### 1.2 Nhập dữ liệu (etl/importer.py)
*   Hàm `import_service_excel`:
    *   Đọc các giá trị thời gian thô từ Excel tại các cột:
        *   Cột 6: `tu_ngay` (index 5)
        *   Cột 7: `tu_thang` (index 6)
        *   Cột 8: `tu_nam` (index 7)
        *   Cột 9: `den_ngay` (index 8)
        *   Cột 10: `den_thang` (index 9)
        *   Cột 11: `den_nam` (index 10)
    *   Chèn các trường này vào SQL INSERT tương ứng của 3 bảng `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl`.

### 1.3 Tổng hợp dữ liệu (etl/aggregator.py)
*   **Hàm `rebuild_monthly`:**
    *   Query dữ liệu BCCP: SELECT `COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu` thay vì `d.nhom_chinh`.
    *   Query dữ liệu HCC/TCBC/PPBL: SELECT `t.ten_dich_vu as nhom_dich_vu` thay vì các hằng số `'HCC'`, `'TCBC'`, `'PPBL'`.
*   **Hàm `rebuild_weekly`:**
    *   Phần BCCP: SELECT `COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu`.
    *   Phần HCC/TCBC/PPBL:
        *   Duyệt qua từng tuần `[w_start, w_end]` trong năm.
        *   Đọc dữ liệu thô từ 3 bảng giao dịch con.
        *   Tính doanh thu trung bình ngày: `dt_ngay = doanh_thu / ((den_ngay - tu_ngay).days + 1)`.
        *   Tính số ngày giao thoa của giao dịch với tuần hiện tại:
            `ngay_giao = max(0, (min(w_end, ngay_ket_thuc) - max(w_start, ngay_bat_dau)).days + 1)`.
        *   Cộng dồn doanh thu tuần = `dt_ngay * ngay_giao` vào `agg_weekly`.

---

## 2. LOGIC TRUY VẤN VÀ GỘP DÒNG THEO XÃ (GROUP BY XÃ)

### 2.1 Quy đổi nhóm dịch vụ con về nhóm chính
Mọi câu SQL query từ `agg_monthly` và `agg_weekly` ở trang Tổng quan chung sẽ được cập nhật để quy đổi ngược về nhóm chính:
```sql
SELECT COALESCE(d.nhom_chinh, 'Khác') as nhom_dich_vu, SUM(a.tong_doanh_thu) 
FROM agg_monthly a
LEFT JOIN (SELECT DISTINCT nhom_dich_vu, nhom_chinh FROM dim_dichvu) d ON a.nhom_dich_vu = d.nhom_dich_vu
WHERE a.nam = ? AND a.thang = ?
GROUP BY COALESCE(d.nhom_chinh, 'Khác')
```

### 2.2 Gom nhóm theo mã xã 4 số (Bỏ trùng lặp xã)
Trong `analytics/global_metrics.py` (hàm `get_period_detail_by_xa` và `get_ytd_detail_by_xa`) và `dash_app/callbacks/service_callbacks.py` (bảng chi tiết xã):
*   Thực hiện truy vấn SQL gom nhóm theo bưu cục rồi join với `dim_buucuc` để lấy `ma_bdx`, `ten_bdx`, `ten_cum`.
*   Sử dụng Pandas để thực hiện `groupby` dồn dòng:
    ```python
    df_grouped = df.groupby(['ten_cum', 'ten_bdx', 'ma_bdx'], as_index=False)[num_cols].sum()
    ```
*   Bảng hiển thị chỉ hiển thị cột `Cụm`, và cột `Xã / Bưu cục` (lấy giá trị `ten_bdx` là Tên Xã, ví dụ: "Bưu điện xã Anh Sơn"), loại bỏ cột hiển thị mã bưu cục/mã xã để giao diện sạch sẽ.

---

## 3. THIẾT KẾ CHI TIẾT CÁC FILE GIAO DIỆN (DASH PAGES)

### 3.1 Trang Chi tiết khách hàng (/bccp/customer)
*   **Bộ lọc nâng cao:**
    *   Bỏ 2 dropdown chiều phân tích `revenue-g1` và `revenue-g2`.
    *   Đưa bộ lọc "Nhóm dịch vụ" lên chung hàng với các bộ lọc Loại khách hàng, Trạng thái hợp đồng.
    *   Loại bỏ nút "Lọc" riêng biệt. Bộ lọc hoạt động tự động khi nhấn nút "Áp dụng" trên Topbar hoặc khi thay đổi bộ lọc inline.
*   **Bảng hiển thị:**
    *   Bỏ bảng xoay chiều ở trên.
    *   Chỉ hiển thị một bảng duy nhất bên dưới với các cột cố định: `Cụm`, `Xã / Phường`, `Bưu cục chấp nhận`, `Mã CMS`, `Sản lượng`, `Doanh thu không VAT`.

### 3.2 Trang Chi tiết sản phẩm dịch vụ (/bccp/service-detail)
*   **Biểu đồ:**
    *   Thêm 2 biểu đồ cột xếp chồng lần lượt theo chiều dọc (Doanh thu theo mã SPDV ở trên, Sản lượng theo mã SPDV ở dưới).
    *   Bỏ biểu đồ cơ cấu tỷ trọng doanh thu theo nhóm dịch vụ.
*   **Bảng thống kê:**
    *   Hạ bảng thống kê doanh thu theo mã SPDV xuống dưới cùng của trang.
    *   Bổ sung thêm cột `Sản lượng` bên cạnh cột `Doanh thu`.

### 3.3 Sidebar & Điều hướng
*   **Đóng/mở tự động:**
    *   Trong `sidebar_callbacks.py`, khi `pathname` không bắt đầu bằng `/bccp`, gán `active_accordion = None` gửi về `sidebar-accordion` để tự động thu gọn accordion "Bưu chính chuyển phát".
*   **Highlight:**
    *   Sửa CSS để khi accordion đóng, button không có màu nền xám.
    *   Làm sáng nổi bật liên kết con đang chọn với class `.sidebar-menu-item.active.active-bccp`.
