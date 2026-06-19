# TIP-agg-002: Tạo bảng `agg_daily` & viết hàm ETL `rebuild_daily`

---

## 1. Yêu cầu & Mục tiêu
*   Cập nhật `etl/aggregator.py`:
    *   Hàm `create_summary_tables(conn)`: Thêm câu lệnh khởi tạo bảng `agg_daily` và tạo index `idx_agg_daily_date_bc` trên cột `(ngay, ma_buu_cuc)`.
    *   Viết hàm `rebuild_daily(conn, nam: int)`:
        1. Xóa dữ liệu cũ của năm đó: `DELETE FROM agg_daily WHERE nam = ?`.
        2. Quét kiểm tra mapping: Tìm các mã dịch vụ trong bảng `transactions` phát sinh trong năm đó nhưng không khớp với `dim_dichvu` hoặc cột `bk_e` bị NULL.
           * Nếu nhóm dịch vụ (`nhom_dich_vu` hoặc `nhom_chinh` nếu map) là một trong bốn nhóm: **Truyền thống**, **TMĐT**, **Quốc tế**, **Chuyển phát HCC**, hãy ghi cảnh báo dạng `[WARNING]` ra log hệ thống và gán giá trị mặc định là `'Khác'`.
           * Các nhóm khác tự động gán là `'Không phân loại'` và không in cảnh báo.
        3. Tổng hợp dữ liệu từ `transactions`:
           * Thực hiện `LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu`.
           * Đếm khách hàng phát sinh: `COUNT(DISTINCT CASE WHEN cms hợp lệ THEN cms END)` (CMS hợp lệ: không null/rỗng/vãng lai/none).
           * Gộp theo `ngay_chap_nhan`, `ma_buu_cuc`, `nhom_dich_vu` con, và cột `bk_e` (sử dụng logic fallback phân loại đã định nghĩa ở trên).
        4. Tổng hợp dữ liệu từ 4 bảng dịch vụ phụ:
           * Gộp bằng cách quét các bản ghi trong năm chỉ định, `LEFT JOIN dim_dichvu` qua `ten_dich_vu = ma_dich_vu OR ten_dich_vu = ten_dich_vu`.
           * Áp dụng SQLite `UPSERT` để chèn hoặc cộng dồn doanh thu và sản lượng vào bảng `agg_daily` dựa trên khóa chính `(ngay, ma_buu_cuc, nhom_dich_vu, bk_e)`.
           * Lưu ý: các bảng phụ này không có `cms` hợp lệ nên `so_kh_phat_sinh` được gán mặc định bằng `0`.

---

## 2. Tiêu chí nghiệm thu (Acceptance Criteria)
1.  Bảng `agg_daily` và chỉ mục được tạo thành công trong Database SQLite.
2.  Hàm `rebuild_daily` chạy không lỗi, thực hiện gộp chính xác số liệu Ngày + Bưu cục + Nhóm dịch vụ con + BK/E từ cả bảng thô và các bảng phụ.
3.  In ra cảnh báo chi tiết các mã dịch vụ bị thiếu mapping thuộc mảng dịch vụ chính.
