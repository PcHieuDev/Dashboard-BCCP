# TIP-bccp-002: ETL Trigger — Auto-calc new_customers khi import BCCP

## Header
- **TIP-ID**: TIP-bccp-002
- **Branch**: feat/bccp-upgrade
- **Module**: callbacks/import
- **Dependencies**: TIP-bccp-001
- **Priority**: P0
- **Estimated effort**: Small

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**: `dash_app/callbacks/import_callbacks.py`, `etl/importer.py`
- **Tham khảo**: `analytics/new_customer_calculator.py` (từ TIP-001)

## Task
Sửa luồng import BCCP để tự động cập nhật bảng `new_customers` sau mỗi lần import thành công.

### 1. Sửa `callbacks/import_callbacks.py`:
- Tìm vị trí sau khi `import_any_excel_file()` hoặc `import_raw_excel_file()` trả về thành công
- Import và gọi `calculate_new_customers(DB_PATH, nam, thang)` với năm/tháng từ file vừa import
- Bọc trong try-except để không ảnh hưởng luồng import chính nếu calc bị lỗi
- Thêm thông báo vào Alert: "Đã cập nhật danh sách KH bán mới"

### 2. Xác định năm/tháng:
- Lấy từ kết quả trả về của hàm import (đã có `thang_du_lieu` trong import_log)
- Parse `thang_du_lieu` (format "T05") → thang=5
- `nam_du_lieu` có trong dữ liệu import

## Specifications
- Chỉ trigger khi import file **BCCP** (RAW hoặc Template), KHÔNG trigger cho HCC/TCBC/PPBL/PHBC
- Nếu `calculate_new_customers` gặp lỗi → log ra console, KHÔNG fail toàn bộ import
- Thông báo Alert vẫn hiện "Thành công" nhưng thêm dòng phụ về KH bán mới

## Acceptance Criteria
```gherkin
Given người dùng upload file BCCP RAW tháng 3/2026
When file import thành công
Then bảng new_customers được cập nhật cho thang=3, nam=2026
And Alert hiển thị "Thành công" kèm thông tin KH bán mới

Given người dùng upload lại file BCCP tháng 3/2026 (re-import)
When file import thành công
Then new_customers tháng 3 được xóa cũ và tính lại

Given người dùng upload file HCC
When file import thành công
Then bảng new_customers KHÔNG bị ảnh hưởng
```

## Constraints
- Không thay đổi logic import hiện tại
- Trigger chỉ là "add-on" sau import thành công
