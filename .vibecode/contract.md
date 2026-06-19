# Contract: Cam kết Phạm vi và Sản phẩm bàn giao

Tài liệu xác nhận phạm vi công việc và kết quả nghiệm thu cho tính năng thêm bảng `agg_daily` có cột `BK/E`.

---

## 1. Kết quả bàn giao mong muốn (Deliverables)

*   [ ] **Bảng Cơ sở dữ liệu**:
    *   Bảng `dim_dichvu` trong `dashboard.db` được bổ sung thêm cột `bk_e` và nạp thành công dữ liệu từ file mapping mới.
    *   Bảng `agg_daily` được tạo lập thành công trong CSDL `dashboard.db` cùng chỉ mục `idx_agg_daily_date_bc`.
*   [ ] **Mã nguồn đồng bộ Mapping**:
    *   [sync_mappings.py](file:///E:/Projects/Dashboard-BCCP/scripts/sync_mappings.py) hỗ trợ đọc cột `BK/E` từ file CSV mới và import vào DB.
*   [ ] **Mã nguồn ETL**:
    *   [etl/aggregator.py](file:///E:/Projects/Dashboard-BCCP/etl/aggregator.py) có hàm khởi tạo bảng ngày và hàm `rebuild_daily(conn, nam)` tính toán chính xác số liệu Ngày + Bưu cục + Nhóm dịch vụ + BK/E từ bảng thô và 4 bảng phụ.
    *   [etl/importer.py](file:///E:/Projects/Dashboard-BCCP/etl/importer.py) tự động kích hoạt `rebuild_daily` khi nạp file Excel mới.
    *   [scripts/rebuild_summaries.py](file:///E:/Projects/Dashboard-BCCP/scripts/rebuild_summaries.py) tích hợp bước chạy rebuild bảng ngày cho năm 2025 và 2026.
*   [ ] **Mã nguồn Kiểm tra chất lượng**:
    *   [scripts/verify_sums.py](file:///E:/Projects/Dashboard-BCCP/scripts/verify_sums.py) bổ sung kiểm tra chênh lệch số liệu bảng `agg_daily` so với bảng thô.

---

## 2. Tiêu chí nghiệm thu (Acceptance Criteria)

1.  Chạy `python scripts/sync_mappings.py` thành công không lỗi, bảng `dim_dichvu` có dữ liệu cột `bk_e`.
2.  Chạy `python scripts/rebuild_summaries.py` hoàn thành toàn bộ (gồm cả bước build `agg_daily` mới) cho năm 2025 và 2026.
3.  Chạy `python scripts/verify_sums.py` và kết quả chênh lệch Doanh thu / Sản lượng giữa bảng ngày `agg_daily` và bảng thô bằng `0` (hoặc khớp hoàn toàn).
4.  Cảnh báo log hiển thị rõ ràng nếu có dịch vụ bị thiếu mapping trong quá trình rebuild.

---

## 3. Ràng buộc & Loại trừ (Exclusions)
*   **Không chỉnh sửa** bất kỳ tệp tin nào thuộc dự án Chatbot (`Chatbot-hoidap-database`).
*   **Không chỉnh sửa** giao diện Dashboard chính (Dash App UI) trong đợt triển khai này.
