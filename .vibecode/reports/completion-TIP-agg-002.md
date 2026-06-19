# Completion Report: TIP-agg-002 — Tạo bảng `agg_daily` & viết hàm ETL `rebuild_daily`

---

## 1. Kết Quả Thực Hiện
*   Cập nhật `etl/aggregator.py` thành công:
    *   Bổ sung câu lệnh tạo bảng `agg_daily` có khóa chính là `(ngay, ma_buu_cuc, nhom_dich_vu, bk_e)` và index tối ưu `idx_agg_daily_date_bc` vào hàm `create_summary_tables(conn)`.
    *   Viết hàm `rebuild_daily(conn, nam)`:
        *   Tự động dọn dẹp dữ liệu cũ của năm yêu cầu.
        *   Quét và phát hiện các mã dịch vụ thiếu mapping thuộc nhóm chính (`Truyền thống`, `TMĐT`, `Quốc tế`, `Chuyển phát HCC`), in cảnh báo rõ ràng ra log hệ thống và gán nhãn mặc định `'Khác'`.
        *   Các nhóm khác tự động gán là `'Không phân loại'` và không in cảnh báo để tránh nhiễu thông tin.
        *   Gộp doanh thu, sản lượng và đếm số khách hàng phát sinh (`COUNT(DISTINCT cms)`) theo Ngày + Bưu cục + Nhóm dịch vụ + BK/E từ bảng thô `transactions` và UPSERT cộng dồn từ 4 bảng dịch vụ phụ.

---

## 2. Kết Quả Xác Minh (Verification)
*   Bảng và chỉ mục được tạo lập đúng cấu trúc trong CSDL SQLite.
*   Log chạy tiến trình hiển thị rõ ràng cảnh báo thiếu mapping dịch vụ năm 2025:
    *   Mã `CTN021`, `CTN023`, `ETN046`, `ETN052` (nhóm Truyền thống) bị thiếu mapping.
*   Hàm chạy mượt mà, tổng số dòng gộp được ghi nhận thành công:
    *   Năm 2025: BCCP: `328,737` dòng.
    *   Năm 2026: BCCP: `141,500` dòng; 4 bảng phụ: `56,461` dòng.
