# TIP-fix-db-etl: Nâng cấp Cơ sở dữ liệu và Logic ETL Phân bổ
Generated: 2026-06-07
Branch: feat-db-etl
Priority: High

---

## 1. MỤC TIÊU (OBJECTIVE)
Nâng cấp cấu trúc các bảng giao dịch dịch vụ con và cập nhật logic aggregate để hỗ trợ lưu nhóm dịch vụ con và phân bổ doanh thu/sản lượng theo ngày thô.

---

## 2. YÊU CẦU CHI TIẾT (SPECIFICATIONS)

### 2.1 Cấu trúc Cơ sở dữ liệu (Database Migration)
*   Thêm các cột sau vào 3 bảng: `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl`:
    *   `tu_ngay` (INTEGER DEFAULT 1)
    *   `tu_thang` (INTEGER DEFAULT 1)
    *   `tu_nam` (INTEGER)
    *   `den_ngay` (INTEGER DEFAULT 30)
    *   `den_thang` (INTEGER DEFAULT 12)
    *   `den_nam` (INTEGER)
*   *Lưu ý:* Thực hiện kiểm tra sự tồn tại của cột bằng SQLite PRAGMA trước khi ALTER TABLE để tránh lỗi crash nếu chạy nhiều lần.

### 2.2 Đọc file import (etl/importer.py)
*   Trong hàm `import_service_excel`:
    *   Đọc các giá trị thời gian thô từ dòng Excel (cột 6: tu_ngay, cột 7: tu_thang, cột 8: tu_nam, cột 9: den_ngay, cột 10: den_thang, cột 11: den_nam).
    *   Cập nhật câu lệnh SQL INSERT để ghi đầy đủ 6 cột ngày này.

### 2.3 Logic Aggregate Phân rã Nhóm con & Phân bổ Trung bình ngày (etl/aggregator.py)
*   **Hàm `rebuild_monthly`:**
    *   BCCP: Query SELECT `COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu` thay vì `d.nhom_chinh`.
    *   HCC/TCBC/PPBL: Query SELECT `t.ten_dich_vu as nhom_dich_vu` thay vì hằng số `'HCC'`, `'TCBC'`, `'PPBL'`.
*   **Hàm `rebuild_weekly`:**
    *   Phần BCCP: SELECT `COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu`.
    *   Phần dịch vụ con (HCC/TCBC/PPBL):
        *   Đọc tất cả giao dịch trong `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl` của năm đó.
        *   Với mỗi giao dịch, parse `ngay_bat_dau = date(tu_nam, tu_thang, tu_ngay)` và `ngay_ket_thuc = date(den_nam, den_thang, den_ngay)`.
        *   Tính số ngày `N = (ngay_ket_thuc - ngay_bat_dau).days + 1`.
        *   Doanh thu 1 ngày: `dt_ngay = doanh_thu / N`, sản lượng 1 ngày: `sl_ngay = san_luong / N`.
        *   Duyệt qua các tuần `[w_start, w_end]` trong năm. Tính số ngày giao thoa `ngay_giao` giữa tuần và khoảng ngày giao dịch.
        *   Cộng dồn doanh thu tuần = `dt_ngay * ngay_giao` và sản lượng tuần = `sl_ngay * ngay_giao` vào `agg_weekly`.

---

## 3. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)
1.  Chạy script db migration không lỗi, 3 bảng transactions con được bổ sung đầy đủ 6 cột ngày.
2.  Import file Excel mẫu dịch vụ khác (`data/mau-file-import/mau_import_dich_vu_khac.xlsx`) thành công, các cột ngày được ghi nhận chính xác trong database.
3.  Chạy `rebuild_monthly` và `rebuild_weekly` thành công. Bảng `agg_monthly` và `agg_weekly` chứa thông tin nhóm dịch vụ con thay vì nhóm chính.
4.  Tổng doanh thu/sản lượng trong bảng aggregate trùng khớp hoàn toàn với tổng doanh thu/sản lượng trong bảng thô.
