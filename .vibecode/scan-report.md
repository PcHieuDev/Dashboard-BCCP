# Scan Report: Bổ sung bảng `agg_daily` có cột phân loại `BK/E`

Báo cáo quét codebase và đánh giá tác động kỹ thuật khi thêm bảng tổng hợp ngày `agg_daily` phân rã theo cột phân loại `BK/E`.

---

## 1. Hiện Trạng Hệ Thống Dữ Liệu & Codebase
*   **Database chính**: SQLite `dashboard.db` (~648 MB) nằm ở `E:\z.Database-TTKD-Data\dashboard.db`.
*   **Database rút gọn cho Chatbot Cloud**: `dashboard_lite.db` (~11 MB) được tạo bằng script `shrink_db.py` để loại bỏ bảng `transactions` thô (>600MB) nhằm đẩy lên GitHub.
*   **Các bảng tổng hợp hiện tại**: `agg_monthly` (~21k dòng) và `agg_weekly` (~80k dòng). Cả hai bảng này đều gộp dữ liệu theo nhóm dịch vụ con (`nhom_dich_vu`), chưa phân rã theo nhóm phân loại `BK/E`.
*   **File Mapping Dịch Vụ Mới**: `E:\Projects\Dashboard-BCCP\data\001-mapping-spdv-new.csv` gồm 82 dòng định nghĩa cột `BK/E` (gồm các giá trị: `BK`, `EMS`, `Đại lý QT`, `Đại lý`).

---

## 2. Kết Quả Mô Phỏng & Đánh Giá Mức Độ Phình Dữ Liệu
Chạy thử nghiệm đếm số dòng thực tế trên bảng giao dịch `transactions` của CSDL gốc `dashboard.db` (1,134,268 dòng):

*   **Trường hợp 1: Gộp Ngày + Bưu Cục + Nhóm Dịch Vụ (Không có cột BK/E)**:
    *   Tổng số dòng kết quả: **311,740 dòng**.
    *   Dung lượng dự kiến: **~23.78 MB**.
*   **Trường hợp 2: Gộp Ngày + Bưu Cục + Nhóm Dịch Vụ + BK/E (Theo yêu cầu của Sếp)**:
    *   Tổng số dòng kết quả: **470,237 dòng** (Tăng thêm **158,497 dòng**, tương đương **+50.84%** so với trường hợp 1).
    *   Dung lượng dự kiến của bảng: **~35.88 MB** (Bao gồm cả chỉ mục tìm kiếm `PRIMARY KEY` và `INDEX`).

### 📈 Tác Động Đến Dung Lượng File CSDL:
1.  **CSDL Gốc (`dashboard.db`)**: Tăng từ `648 MB` lên khoảng `684 MB` (+5.5%). Tác động không đáng kể đối với hệ thống chạy offline trên máy của Sếp.
2.  **CSDL Rút Gọn (`dashboard_lite.db`)**: Tăng từ khoảng `11 MB` lên khoảng `47 MB` (đã bao gồm bảng `agg_daily` mới). 
    > [!WARNING]
    > Mức dung lượng 47MB vẫn dưới ngưỡng 50MB (giới hạn cảnh báo của GitHub). Tuy nhiên, khi dữ liệu các tháng tiếp theo của năm 2026 nạp vào, dung lượng file rút gọn sẽ dễ dàng vượt quá 50MB và tiến tới 100MB (ngưỡng từ chối push của GitHub). 
    > **Giải pháp đề xuất**: Khi chạy script `shrink_db.py`, chúng ta sẽ giới hạn chỉ copy dữ liệu `agg_daily` và `agg_weekly` của năm hiện hành (ví dụ năm 2026) hoặc chỉ giữ lại 3 tháng gần nhất để giảm dung lượng file Cloud.

---

## 3. Rà Soát Các Thành Phần Code Cần Thay Đổi (Gaps & Giao Điểm)

### A. Cơ sở dữ liệu và Mappings:
*   Cần bổ sung cột `bk_e` (TEXT) vào bảng danh mục `dim_dichvu` trong SQLite để lưu trữ thông tin mapping từ file `001-mapping-spdv-new.csv`.
*   Cập nhật script đồng bộ mapping `scripts/sync_mappings.py` để:
    *   Đọc file mapping mới `001-mapping-spdv-new.csv`.
    *   Đồng bộ cột `BK/E` vào cột `bk_e` của bảng `dim_dichvu`.

### B. Tiến trình tổng hợp dữ liệu (ETL / Rebuild):
*   **`etl/aggregator.py`**:
    *   Hàm `create_summary_tables(conn)`: Định nghĩa thêm bảng `agg_daily` với cột `bk_e` (TEXT) và khóa chính `PRIMARY KEY (ngay, ma_buu_cuc, nhom_dich_vu, bk_e)`.
    *   Hàm `rebuild_daily(conn, nam)`: Tổng hợp dữ liệu từ `transactions` và 4 bảng phụ (`transactions_hcc`, `transactions_tcbc`, `transactions_ppbl`, `transactions_phbc`) theo cấp ngày, JOIN bảng `dim_dichvu` để lấy `nhom_dich_vu` và `bk_e`, thực hiện UPSERT vào `agg_daily`.
*   **`scripts/rebuild_summaries.py`**:
    *   Tích hợp bước chạy `rebuild_daily` sau khi tổng hợp tháng và tuần.
