# Context: Bối cảnh dự án phục vụ Builder

Tài liệu cung cấp bối cảnh kỹ thuật, quy tắc code và các quyết định nghiệp vụ của Sếp cho Builder thực thi.

---

## 1. Tổng Quan Dự Án
Dự án Dashboard doanh thu BCCP cần bổ sung bảng tổng hợp theo ngày `agg_daily` vào Database SQLite chung `dashboard.db` để phục vụ cho các dự án tích hợp sau này (như chatbot). Không thay đổi giao diện Dash App (UI) hiện tại.

---

## 2. Các Quyết Định Nghiệp Vụ Của Sếp (RRI)
1.  **Cột phân loại `BK/E`**: 
    *   Mảng BCCP và HCC được map theo file CSV `001-mapping-spdv-new.csv` (lưu ý: copy file này đè lên `data/mapping-spdv.csv` của dự án).
    *   Không còn giá trị `'Đại lý'` (chỉ có `BK`, `EMS`, `Đại lý QT`, `Khác`, `Không phân loại`).
    *   Các dịch vụ phụ (TCBC, PPBL, PHBC) không có trong file mapping CSV -> Mặc định gán là `'Không phân loại'`.
    *   Các dịch vụ thuộc mảng chính (Truyền thống, TMĐT, Quốc tế, Chuyển phát HCC) nhưng không có trong mapping CSV -> Gán là `'Khác'`.
2.  **Logic cảnh báo (Log Warning)**:
    *   Chỉ in cảnh báo `[WARNING]` ra log hệ thống nếu dịch vụ chưa được map thuộc một trong bốn nhóm: **Truyền thống**, **TMĐT**, **Quốc tế**, **Chuyển phát HCC**.
    *   Các nhóm khác tự động gán là `'Không phân loại'` và **không cảnh báo**.
3.  **Số khách hàng phát sinh (`so_kh_phat_sinh`)**:
    *   Đếm số lượng khách hàng phát sinh doanh thu trong ngày bằng logic `COUNT(DISTINCT cms)`. 
    *   Khách hàng hợp lệ là khách hàng có `cms` không NULL, không rỗng `""`, không bắt đầu bằng `'VANGLAI_'` và giá trị không phải là `'none'` (không phân biệt hoa thường).

---

## 3. Kiến Trúc Cơ Sở Dữ Liệu
*   **Bảng `dim_dichvu`**: Bổ sung cột `bk_e` (TEXT).
*   **Bảng `agg_daily`**:
    *   Khóa chính: `PRIMARY KEY (ngay, ma_buu_cuc, nhom_dich_vu, bk_e)`.
    *   Cột: `ngay`, `nam`, `thang`, `ma_buu_cuc`, `nhom_dich_vu`, `bk_e`, `tong_doanh_thu`, `tong_san_luong`, `so_kh_phat_sinh`.
    *   Chỉ mục: `idx_agg_daily_date_bc` trên cột `(ngay, ma_buu_cuc)`.

---

## 4. Kỷ Luật Code (Karpathy Principles)
*   **Think & Simplify**: Viết code rõ ràng, có ghi chú tiếng Việt dễ hiểu.
*   **Surgical Edits**: Sửa đúng chỗ, không làm ảnh hưởng đến các hàm tổng hợp tháng/tuần đang chạy ổn định.
*   **Database Connection**: Đóng kết nối (`conn.close()`) ngay sau khi sử dụng để tránh lỗi `database is locked`.
