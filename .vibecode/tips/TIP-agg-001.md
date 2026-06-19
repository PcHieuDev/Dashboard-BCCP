# TIP-agg-001: Đồng bộ cột `BK/E` vào bảng danh mục `dim_dichvu`

---

## 1. Yêu cầu & Mục tiêu
*   Sao chép nội dung file mapping mới từ `data/001-mapping-spdv-new.csv` sang file mapping chính `data/mapping-spdv.csv` của dự án để đảm bảo đồng bộ.
*   Cập nhật mã nguồn `scripts/sync_mappings.py` để tự động kiểm tra xem bảng `dim_dichvu` đã có cột `bk_e` chưa, nếu chưa có thì chạy lệnh SQL `ALTER TABLE dim_dichvu ADD COLUMN bk_e TEXT`.
*   Cập nhật hàm `sync_spdv` trong `scripts/sync_mappings.py` để đọc cột `bk/e` từ file CSV (giao diện cột mới) và chèn dữ liệu cột này vào `dim_dichvu`. Nếu giá trị trống thì mặc định là `'Khác'`.

---

## 2. Tiêu chí nghiệm thu (Acceptance Criteria)
1.  Đọc được cột `bk/e` từ file CSV mapping (không phân biệt chữ hoa/thường).
2.  Bảng `dim_dichvu` trong SQLite `dashboard.db` được cập nhật thêm cột `bk_e` và chứa dữ liệu phân loại chính xác (`BK`, `EMS`, `Đại lý QT`, `Khác`, `Không phân loại`).
3.  Chạy script `python scripts/sync_mappings.py` thành công không gặp lỗi.
