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
- **Phase 6 (Cải tiến UI/UX & Sửa lỗi)**: Đang hoàn thành.
  - Cập nhật logic CMS gộp "Bán mới" & "Tái bán" thành "KHM/Tái bán".
  - Tạo file template import dữ liệu tay `data/template_import.xlsx`.
  - Cải tiến giao diện Import: Tách luồng thành 2 bước (Chọn file -> Hiện thông tin -> Bấm Xác nhận nạp), hiển thị vòng xoay Spinner trong lúc nạp và tự động làm sạch ô upload.
  - Nâng cấp bảng Lịch sử: Lấy 50 dòng, bật phân trang, sắp xếp, lọc native, cuộn 4 chiều (max-height: 400px), highlight trạng thái xanh/đỏ.
  - Sửa lỗi bộ lọc BĐX (Bưu điện Huyện/Xã) không hoạt động do KeyError tên cột viết hoa/viết thường giữa SQLite và Pandas.
- **Đường dẫn Workspace hoạt động**:
  - Mã nguồn: `E:\Projects\Dashboard-BCCP`
  - Cơ sở dữ liệu: `E:\OneDrive\z.Database-TTKD-Data\bccp.db`
- **Cloudflare Tunnel (Truy cập từ xa)**:
  - Tên miền: `dashboard.bdna.io.vn` trỏ về `http://localhost:8050`
  - Trạng thái: Đã cài đặt dịch vụ Windows Service cho `cloudflared` tại `C:\Users\Duong\cloudflared\cloudflared.exe` để tự động chạy khi bật máy.

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
1. **[PENDING] TIP-005**: Khởi động lại dashboard, test chức năng nạp file `.xls` CAS ngày 29.05, kiểm tra Spinner và bảng lịch sử phân trang mới.
2. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.

## Issues & Notes
- **Lỗi `File is not a zip file`**: Đã được sửa bằng cách dùng `xlrd` đọc các file `.xls` cũ từ hệ thống CAS. Người dùng cần khởi động lại Dashboard (chạy lại file `run_dashboard.bat`) để code mới này có hiệu lực trên giao diện.
- **Lỗi bộ lọc BĐX (Bưu điện Huyện/Xã)**: Bộ lọc địa lý động bị crash và luôn trả về mặc định do sự không khớp chữ hoa/thường trong tên cột (`ten_BDX` vs `ten_bdx`) giữa SQLite và Pandas. Đã khắc phục bằng cách đồng bộ sang viết thường toàn bộ ở `sidebar_callbacks.py` và `app.py`. Sếp chỉ cần khởi động lại ứng dụng.
- **Lỗi `ModuleNotFoundError: No module named 'pandas'`**: Đã được sửa trong file `run_dashboard.bat` bằng cách sử dụng `py -3.13 app.py` để đảm bảo hệ thống luôn gọi đúng phiên bản Python 3.13 (đã cài đủ thư viện) thay vì gọi phiên bản mặc định của Windows.
- **Bypass Login**: Hiện tại đang bypass authentication trong `app.py` để phát triển tiện lợi hơn. Cần kích hoạt lại khi deploy chính thức.