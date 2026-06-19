# TIP-agg-003: Tích hợp Rebuild số liệu cho bảng `agg_daily`

---

## 1. Yêu cầu & Mục tiêu
*   Cập nhật `scripts/rebuild_summaries.py`:
    *   Import hàm `rebuild_daily` từ module `etl.aggregator`.
    *   Tích hợp bước rebuild bảng tổng hợp theo ngày `agg_daily` vào hàm `main()` (Ví dụ: Thêm Bước 2.5 ngay sau khi rebuild tổng hợp tháng hoặc tuần).
    *   Đảm bảo tiến trình tự động lặp qua tất cả các năm cần rebuild (2025 và 2026) để tính toán đầy đủ dữ liệu lịch sử cho bảng `agg_daily`.

---

## 2. Tiêu chí nghiệm thu (Acceptance Criteria)
1.  Chạy script `python scripts/rebuild_summaries.py` hoàn tất thành công mà không gặp bất kỳ lỗi ngoại lệ nào.
2.  Bảng `agg_daily` được nạp đầy đủ dữ liệu lịch sử của năm 2025 và năm 2026.
