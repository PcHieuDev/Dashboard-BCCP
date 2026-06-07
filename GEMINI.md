# GEMINI.md - Project State & Agent Handover (Concise Summary)

> [!IMPORTANT]
> Đây là bản tóm tắt ngắn gọn của dự án. Để nắm bắt toàn bộ nội dung chi tiết về lịch sử phát triển, cấu trúc thư mục, sơ đồ dữ liệu (schema), logic phân loại và các tác vụ đang chờ xử lý, vui lòng đọc tài liệu chi tiết tại [project_state.md](file:///E:/Projects/Dashboard-BCCP/project_state.md).

## Project Goal
Dashboard doanh thu bưu chính chuyển phát (BCCP) hỗ trợ bộ lọc đa chiều, phân loại khách hàng tự động, import dữ liệu từ Excel vào SQLite. Phục vụ **20+ người dùng** từ nhiều phòng ban, dự kiến deploy lên **server nội bộ**.

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đã chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite (đang lưu trữ đồng bộ trên OneDrive) -> PostgreSQL khi deploy server
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl, xlrd>=2.0.1 (đọc file .xls)
- **Encoding**: UTF-8 toàn bộ

# toàn bộ các nhánh worktrees của dự án đều phải tạo trong thư mục E:\Projects\worktrees\Dashboard-BCCP

> [!CAUTION]
> **KHÔNG được tự ý xóa worktree (mục làm việc tạm thời) hoặc xóa nhánh local** khi chưa có yêu cầu rõ ràng từ Sếp.  
> Các worktree và nhánh local cần được giữ lại để Sếp kiểm tra công việc dễ dàng hơn.  
> Chỉ thực hiện xóa khi Sếp nói rõ "xóa worktree" hoặc "xóa nhánh" hoặc tương tự.

## Active Workspace & Links
- **Mã nguồn chính**: [Dashboard-BCCP](file:///E:/Projects/Dashboard-BCCP)
- **Cơ sở dữ liệu**: [dashboard.db](file:///E:/OneDrive/z.Database-TTKD-Data/dashboard.db)
- **Trang thái hiện tại**: Đã hoàn thành Phase 11 (Tối ưu giao diện & Performance) và rollback nhánh `feat-ux-filters`. Xem chi tiết toàn bộ lịch sử và trạng thái dự án tại [project_state.md](file:///E:/Projects/Dashboard-BCCP/project_state.md).
- **Cloudflare Tunnel (Truy cập từ xa)**: Tên miền `dashboard.bdna.io.vn` trỏ về `http://127.0.0.1:8050`. Windows Service `cloudflared` đang hoạt động ổn định.
