# Verify Report: Nghiệm thu tính năng bảng `agg_daily` có cột `BK/E`

Tài liệu ghi nhận kết quả nghiệm thu (QA Verification) cho toàn bộ tính năng.

---

## 1. Kết quả kiểm tra đối chiếu số liệu (Nghiệm thu thực tế)

Chạy script đối chiếu [verify_sums.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-agg-daily-v2/scripts/verify_sums.py) trên SQLite database thu được kết quả khớp 100%:

```
--- 3. BẢNG TỔNG HỢP NGÀY (agg_daily) vs BẢNG THÔ NĂM 2026 ---
Tổng Thô 2026 (BCCP + Phụ): Doanh thu = 66,632,245,325.00, Sản lượng = 2,328,092
Tổng Ngày 2026 (agg_daily):  Doanh thu = 66,632,245,325.00, Sản lượng = 2,328,092
-> Chênh lệch Doanh thu = 0.000000 VNĐ
-> Chênh lệch Sản lượng = 0
```
=> **Đạt yêu cầu**: Dữ liệu gộp từ bảng thô `transactions` và 4 bảng phụ được bảo toàn hoàn hảo, không lệch lệch 1 đồng doanh thu hay 1 đơn vị sản lượng nào.

---

## 2. Kiểm tra tính năng tự động (ETL & Mapping)

1.  **Đồng bộ Mapping**:
    *   Chạy `sync_mappings.py` thành công. Bảng `dim_dichvu` được tạo thêm cột `bk_e` và nạp thành công 82 dòng dịch vụ BCCP/HCC cùng cột `BK/E` tương ứng.
2.  **Cảnh báo thiếu Mapping**:
    *   Tiến trình tự động in cảnh báo chính xác cho các dịch vụ thuộc 4 nhóm chính bị thiếu mapping trong năm 2025:
        *   `CTN021`, `CTN023`, `ETN046`, `ETN052`.
    *   Các dịch vụ khác (thuộc TCBC, PPBL, PHBC...) tự động chuyển vào nhãn `'Không phân loại'` và không in cảnh báo, tránh nhiễu log.
3.  **Tự động cập nhật khi Import**:
    *   Hàm `_auto_aggregate_after_import` trong `etl/importer.py` đã được tích hợp bước gọi `rebuild_daily(conn, nam)`.
    *   **Kết quả**: Khi Sếp import file Excel mới, bảng `agg_daily` sẽ tự động cập nhật ngay lập tức mà không cần phải chạy lại toàn bộ quy trình `rebuild_summaries.py`.

---

## 3. Kết luận
*   Tính năng hoạt động **ổn định, chính xác 100%**.
*   Đáp ứng hoàn toàn các tiêu chí nghiệm thu đề ra trong [contract.md](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-agg-daily-v2/.vibecode/contract.md).
*   Khuyến nghị: Sếp cho phép merge nhánh `feat/agg-daily-v2` vào `main`.
