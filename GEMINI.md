# GEMINI.md - Project State & Agent Handover

## Project Goal
Dashboard doanh thu bưu chính chuyển phát (BCCP) hỗ trợ bộ lọc đa chiều, phân loại khách hàng tự động, import dữ liệu từ Excel vào SQLite. Phục vụ **20+ người dùng** từ nhiều phòng ban, dự kiến deploy lên **server nội bộ**.

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đã chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite (đang lưu trữ đồng bộ trên OneDrive) -> PostgreSQL khi deploy server
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl, xlrd>=2.0.1 (đọc file .xls)
- **Encoding**: UTF-8 toàn bộ

## Current State
- **Phase 5 (Chuyển đổi sang Dash)**: Đã hoàn thành và nghiệm thu.
  - Phase 5A (Migrate tính năng): Xong.
  - Phase 5B (Export Excel/PDF, phân quyền, cảnh báo): Xong.
  - Phase 5D (Chi tiết Khách hàng CMS): Xong.
- **Phase 6 (Cải tiến UI/UX & Sửa lỗi)**: Đã hoàn thành toàn bộ 5 TIPs.
  - Cập nhật logic CMS gộp "Bán mới" & "Tái bán" thành "KHM/Tái bán".
  - Tạo file template import dữ liệu tay `data/template_import.xlsx`.
  - Cải tiến giao diện Import: Tách luồng thành 2 bước (Chọn file -> Hiện thông tin -> Bấm Xác nhận nạp), hiển thị vòng xoay Spinner trong lúc nạp và tự động làm sạch ô upload.
  - Nâng cấp bảng Lịch sử: Lấy 50 dòng, bật phân trang, sắp xếp, lọc native, cuộn 4 chiều (max-height: 400px), highlight trạng thái xanh/đỏ.
  - Sửa lỗi crash JS phía client khiến giao diện không hiển thị Alert khi nạp thành công (do cú pháp `||` không hợp lệ trong `style_data_conditional` của DataTable).
- **Đường dẫn Workspace hoạt động**:
  - Mã nguồn: `E:\Projects\Dashboard-BCCP`
  - Cơ sở dữ liệu: `E:\OneDrive\z.Database-TTKD-Data\bccp.db`

## Key Decisions & Architecture
- **Mã nguồn tách biệt khỏi OneDrive**: Tránh xung đột đồng bộ OneDrive khi chạy cơ sở dữ liệu và code. Code chính nằm tại `E:\Projects\Dashboard-BCCP`.
- **Luồng Import mới**:
  1. Người dùng chọn file -> file được đọc và hiển thị thông tin ở `selected-file-info`, hiện nút Xác nhận.
  2. Người dùng bấm Xác nhận -> Spinner quay, file được ghi tạm, gọi `import_any_excel_file` để tự động phân tích và import (cho cả `.xls` và `.xlsx`).
  3. Kết quả trả về `dbc.Alert` tại `upload-status-message`, đồng thời reset `upload-data` contents để ẩn nút và xóa file info.
- **Cấu trúc Thư mục**:
  - `dash_app/pages/import_data.py` (Layout trang import)
  - `dash_app/callbacks/import_callbacks.py` (Callback xử lý upload & bảng lịch sử)
  - `etl/importer.py` (Logic xử lý nạp file Excel & phân loại file RAW/Template)
  - `scripts/sync_mappings.py` (Script đồng bộ danh mục sản phẩm/bưu cục từ CSV vào DB)

## Pending Tasks
1. **[PENDING] Nghiệm thu thực tế**: Sếp chạy lại dashboard và verify chức năng import mới.
2. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.

## Issues & Notes
- **Lỗi `File is not a zip file`**: Đã được sửa bằng cách dùng `xlrd` đọc các file `.xls` cũ từ hệ thống CAS. Người dùng cần khởi động lại Dashboard (chạy lại file `run_dashboard.bat`) để code mới này có hiệu lực trên giao diện.
- **Lỗi không hiển thị Alert khi nạp thành công**: Đã sửa triệt để bằng cách dịch trạng thái thô sang tiếng Việt (`SUCCESS_RAW` -> `"Thành công"`) và chuyển điều kiện highlight màu trong DataTable thành các luật đơn riêng biệt để tránh crash JS client.
- **Bypass Login**: Hiện tại đang bypass authentication trong `app.py` để phát triển tiện lợi hơn. Cần kích hoạt lại khi deploy chính thức.