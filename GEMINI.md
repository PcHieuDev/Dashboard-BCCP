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
- **Sửa lỗi Import CSV Mapping (04/06/2026)**:
  - Khắc phục lỗi `❌ Tệp CSV thiếu cột bắt buộc 'nhom_chinh' làm cột đầu tiên!` do Sếp lưu file CSV từ Excel trên Windows dùng dấu phân tách `;`.
  - Hỗ trợ cả dấu phân tách `;` và `,` khi đọc file CSV trong `import_callbacks.py` và `sync_mappings.py`.
  - Cải tiến logic upload CSV: tự động gộp (merge) danh mục cũ và danh mục mới thay vì ghi đè, bảo toàn dữ liệu khi chỉ thêm dòng mới.
  - Đồng bộ trực tiếp thành công dịch vụ mới `CTN052` của Sếp từ file `template_them_san_pham_dich_vu.csv` vào DB.
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
  - Sửa lỗi lệch múi giờ trong bảng Lịch sử import (sử dụng alias `created_at_local` và `datetime(created_at, 'localtime')` trong SQLite).
  - Khởi tạo và tính toán thành công dữ liệu lịch sử khách hàng mới (`new_customers`) từ tháng 10/2025 đến tháng 6/2026.
  - Phát hiện dữ liệu tháng 5/2026 bị thiếu dữ liệu hai ngày cuối tháng (30/05 và 31/05) do tệp nguồn chỉ chạy đến 29/05.
- **Đường dẫn Workspace hoạt động**:
  - Mã nguồn: `E:\Projects\Dashboard-BCCP`
  - Cơ sở dữ liệu: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`

## Key Decisions & Architecture
- **Mã nguồn tách biệt khỏi OneDrive**: Tránh xung đột đồng bộ OneDrive khi chạy cơ sở dữ liệu và code. Code chính nằm tại `E:\Projects\Dashboard-BCCP`.
- **Luồng Import mới**:
  1. Người dùng chọn file -> file được đọc và hiển thị thông tin ở `selected-file-info`, hiện nút Xác nhận.
  2. Người dùng bấm Xác nhận -> Spinner quay, file được ghi tạm, gọi `import_any_excel_file` để tự động phân tích và import (cho cả `.xls` và `.xlsx`).
  3. Kết quả trả về `dbc.Alert` tại `upload-status-message`, đồng thời reset `upload-data` contents để ẩn nút và xóa file info.
- **Cơ chế Gộp danh mục Dịch vụ tự động**: Khi tải lên file CSV để đồng bộ sản phẩm dịch vụ mới, hệ thống sẽ tự động ghép với danh mục hiện tại và khử trùng theo mã dịch vụ (`ma_spdv`) để đảm bảo không bị ghi đè mất các dịch vụ khác. File CSV mapping trên đĩa sẽ được lưu lại dưới dạng chuẩn hóa dấu phẩy `,` và mã hóa `utf-8-sig`.

## Pending Tasks
1. **[PENDING] Bổ sung dữ liệu**: Chờ Sếp nạp thêm dữ liệu 2 ngày cuối tháng 5 (30.05 - 31.05) và dữ liệu tháng 6 còn thiếu (từ 03/06 trở đi).
2. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.

## Issues & Notes
- **Lỗi không hiển thị Alert khi nạp thành công**: Đã sửa triệt để bằng cách đổi `dismissible` thành `dismissable` trong DBC Alert.
- **Lịch sử KHM**: Bảng `new_customers` đã được khởi tạo và chạy tính toán đầy đủ cho toàn bộ các tháng lịch sử.
- **Bypass Login**: Hiện tại đang bypass authentication trong `app.py` để phát triển tiện lợi hơn. Cần kích hoạt lại khi deploy chính thức.
- **Lỗi CSV dấu phân tách ';'**: Đã khắc phục triệt để bằng việc hỗ trợ cả `,` và `;` ở tất cả các module đọc CSV mapping.