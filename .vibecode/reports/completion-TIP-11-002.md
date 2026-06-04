# Completion Report: TIP-11-002

## 1. Kết quả thực hiện
- **Status**: DONE
- **Files modified**:
  - `dash_app/pages/customer_detail.py`
  - `dash_app/callbacks/customer_callbacks.py`

## 2. Chi tiết thay đổi
- Chuyển `Dropdown` Nhóm theo (group_by) và bộ lọc dịch vụ BCCP Inline vào cùng một khối "⚙️ Bộ lọc Nâng cao".
- Xóa nút Xuất Excel doanh thu thừa, chỉ để lại nút Xuất Excel CMS. Cập nhật lại callback xóa bỏ đoạn code xử lý xuất Excel tương ứng.
- Cập nhật bảng `customer-detail-datatable` (CMS) để chỉ hiển thị các cột: Mã CMS, Tên KH, Nhóm DV chính, Sản lượng, Cước không VAT. 
- Hàm tính toán tự động tìm ra "Nhóm DV chính" dựa vào nhóm dịch vụ mang lại doanh thu Cước không VAT lớn nhất cho khách hàng. Tương tự cho phần Xuất Excel.

## 3. Checklist Acceptance Criteria
- [x] Trang `/bccp/customer` có bộ lọc gọn gàng.
- [x] Nút xuất file không bị lặp.
- [x] Bảng CMS chỉ có các cột: Mã CMS, Tên KH, Nhóm DV chính, Sản lượng, Cước không VAT.
