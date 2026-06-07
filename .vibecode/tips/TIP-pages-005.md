# TIP-pages-005: Trang Chi tiết SPDV (mới) + bỏ Alerts

## HEADER
- TIP-ID: TIP-pages-005
- Branch: feat/pages-redesign
- Project: Dashboard BCCP v2.0
- Module: Pages / Callbacks
- Depends on: None
- Priority: P1
- Estimated effort: 45 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign
- Key files to reference:
  - `dash_app/pages/alerts.py` → sẽ xóa
  - `dash_app/callbacks/alerts_callbacks.py` → sẽ xóa
  - Bảng `dim_dichvu` → ma_dich_vu, ten_dich_vu, nhom_dich_vu (WHERE nhom_chinh = 'BCCP')
  - Bảng `transactions` → san_pham_dv, cuoc_tt_tong

## TASK
1. Tạo trang mới "Chi tiết sản phẩm dịch vụ" tại route `/bccp/service-detail`
2. Xóa trang Cảnh báo doanh thu

## SPECIFICATIONS

### Trang Chi tiết SPDV

#### Layout:
1. **Bảng tổng hợp DT theo mã SPDV**
   - Cột: Mã DV | Tên DV | Nhóm DV | DT kỳ hiện tại | DT kỳ trước | % Thay đổi
   - Dữ liệu: query transactions (hoặc summary) GROUP BY san_pham_dv, JOIN dim_dichvu
   - Sort: DT kỳ hiện tại giảm dần
   - Lọc theo bộ lọc Topbar (thời gian + địa lý)

2. **Biểu đồ phân rã doanh thu theo nhóm DV**
   - Pie chart hoặc horizontal bar chart (plotly)
   - Hiển thị tỷ trọng % mỗi nhóm DV trong tổng DT BCCP

### File mới
- `dash_app/pages/service_detail.py` → hàm `create_service_detail_layout()`
- `dash_app/callbacks/service_detail_callbacks.py` → hàm `register_service_detail_callbacks(app)`

### Prefix ID: `spdv-`

### Xóa files
- `dash_app/pages/alerts.py`
- `dash_app/callbacks/alerts_callbacks.py`

## ACCEPTANCE CRITERIA
- Given: User truy cập /bccp/service-detail
- When: Trang load
- Then: Bảng hiện danh sách SPDV với doanh thu, biểu đồ phân rã hiển thị đúng

- Given: alerts.py và alerts_callbacks.py
- When: Kiểm tra filesystem
- Then: 2 file đã bị xóa

## CONSTRAINTS
- Trang SPDV chỉ hiện dữ liệu BCCP (nhom_chinh = 'BCCP')
- KHÔNG tạo trang SPDV cho HCC/TCBC/PPBL (chưa có yêu cầu)
- KHÔNG sửa app.py ở TIP này (sẽ cập nhật routing ở TIP-pages-006)
