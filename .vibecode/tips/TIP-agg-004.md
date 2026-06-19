# TIP-agg-004: Cập nhật đối chiếu số liệu bảng `agg_daily`

---

## 1. Yêu cầu & Mục tiêu
*   Cập nhật `scripts/verify_sums.py`:
    *   Bổ sung phần đối chiếu tổng doanh thu và sản lượng giữa bảng tổng hợp ngày `agg_daily` với bảng thô `transactions` và các bảng phụ cho năm 2026.
    *   Thực hiện so sánh tổng chênh lệch doanh thu và sản lượng để kiểm tra tính nhất quán. In kết quả đối chiếu ra console của Windows/Log.

---

## 2. Tiêu chí nghiệm thu (Acceptance Criteria)
1.  Chạy `python scripts/verify_sums.py` thành công.
2.  Kết quả đối chiếu cho thấy tổng doanh thu và sản lượng của bảng `agg_daily` khớp hoàn toàn (chênh lệch bằng `0`) với bảng thô đối với năm 2026.
