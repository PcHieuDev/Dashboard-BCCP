# Feature Context: UX Topbar & Manual Load

## Mục tiêu chính
Nâng cấp trải nghiệm người dùng bằng cách dời toàn bộ bộ lọc toàn cục (Thời gian, Cụm, v.v.) từ menu dọc bên trái (Sidebar) sang thanh nằm ngang (Topbar) phía trên nội dung, giúp giải phóng không gian màn hình ngang cho Datatable và Chart.

Đồng thời, chấm dứt tình trạng auto-load của mọi biểu đồ/bảng khi chuyển trang hay thay đổi một Dropdown. Hệ thống giờ chuyển sang **Manual Load 100%**: người dùng bắt buộc phải bấm nút "Lọc dữ liệu" màu xanh (duy nhất 1 nút) thì dữ liệu mới được tải và hiển thị.

## Yêu cầu Kiến trúc
- **Layout**: `app.py` chia thành Sidebar (trái) và main content (phải). Trong main content, chia thành Topbar (trên) và page-content (dưới).
- **Callbacks**: Tất cả trigger cũ (`tabs-navigation`, `customer-filter-...`) phải bị giáng cấp từ `Input` xuống `State`.
- **Trạng thái khởi tạo**: Bổ sung `prevent_initial_call=True` để ngăn query DB khi khởi động/chuyển trang.

## Chú ý quan trọng
- Không di chuyển các bộ lọc con (Inline filters) của trang Customer Detail hay HCC lên Topbar. Chúng vẫn ở vị trí cũ, nhưng bị tắt tính năng auto-trigger (đổi thành State).
- Nút "Lọc dữ liệu" đặt ở tận cùng bên phải của Topbar.
