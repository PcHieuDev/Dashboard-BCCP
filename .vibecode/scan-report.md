# Scan Report: Cải tiến UX Topbar & Manual Load

## Tổng quan
Dựa vào các yêu cầu trong `context.md` và các TIP (`TIP-ux-001`, `TIP-ux-002`, `TIP-ux-003`), đợt thi công này tập trung vào hai thay đổi lớn về trải nghiệm người dùng (UX) và kiến trúc luồng dữ liệu (Data flow) của Dashboard:

1. **Giao diện (UI)**: Chuyển các bộ lọc toàn cục (Thời gian, Không gian) từ Sidebar ngang sang một Topbar nằm trên nội dung chính. Sidebar sẽ gọn gàng hơn, chỉ còn chứa phần điều hướng (Navigation Menu) và thông tin cá nhân.
2. **Luồng dữ liệu (Manual Load)**: Xóa bỏ việc tự động truy vấn cơ sở dữ liệu khi mở trang, chuyển tab hoặc khi người dùng thay đổi 1 bộ lọc. Tất cả sẽ được chuyển sang chế độ "Thủ công" (Manual Load) - dữ liệu chỉ được tải khi người dùng nhấn nút "Lọc dữ liệu".

## Phân tích hiện trạng
- **`app.py`**: Hiện đang load `create_sidebar_layout` và phần content chính (gồm tiêu đề và `page-content`). Chưa có vị trí cho Topbar.
- **`components/sidebar.py`**: Chứa toàn bộ logic render cả Navigation Menu và các dropdown bộ lọc (Năm, Chu kỳ, Cụm, v.v.), cũng như nút `btn-apply-filter`. Phần filter này (từ dòng 94 trở đi) cần được bóc tách ra.
- **Callbacks (`kpi_callbacks.py`, `retention_callbacks.py`, `customer_callbacks.py`...)**: Hầu hết đang dùng `Input` cho các thay đổi bộ lọc hoặc thay đổi tab (`tabs-navigation`). Cần phải chuyển những `Input` này thành `State`, và thêm `prevent_initial_call=True`.

## Kế hoạch thi công (Blueprint)

### Batch 1: TIP-ux-001 - Tái cấu trúc Layout (Topbar)
1. Tạo file mới `dash_app/components/topbar.py` để chứa hàm `create_topbar_layout(filter_opts)`.
2. Di chuyển phần code render các bộ lọc (Thời gian, Không gian) và nút `btn-apply-filter` từ `dash_app/components/sidebar.py` sang `dash_app/components/topbar.py`.
3. Sắp xếp lại Topbar theo chiều ngang, đặt nút "Lọc dữ liệu" ở góc phải.
4. Chỉnh sửa `dash_app/app.py` để import và chèn `create_topbar_layout` vào giữa phần tiêu đề và `page-content`.

### Batch 2: TIP-ux-002 & TIP-ux-003 - Triển khai Manual Load
1. Cập nhật `kpi_callbacks.py`, `retention_callbacks.py`, `new_customer_callbacks.py`:
   - Thêm `prevent_initial_call=True`.
   - Đổi `Input("tabs-navigation", "value")` thành `State("tabs-navigation", "value")`.
   - Chỉ giữ `Input("btn-apply-filter", "n_clicks")` làm trigger duy nhất.
2. Cập nhật `customer_callbacks.py`, `hcc_revenue_callbacks.py`, `alerts_callbacks.py`:
   - Đổi các filter con (inline filters) thành `State`.
   - Thêm `prevent_initial_call=True`.

## Nguy cơ tiềm ẩn
- Thay đổi `Input` thành `State` có thể làm hỏng logic load mặc định nếu không thiết lập cẩn thận. Việc chặn initial call (`prevent_initial_call=True`) đồng nghĩa khi vừa mở web lên, dashboard sẽ không có số liệu cho đến khi bấm "Lọc". Cần thiết kế để layout vẫn render đầy đủ mà không bị crash vì thiếu data.
- Việc căn chỉnh CSS cho Topbar cần chú ý để không làm phá vỡ layout responsive.

Tôi sẽ dừng ở đây để Sếp xem xét Scan Report này trước khi tôi bắt đầu thi công Batch 1 (TIP-ux-001).
