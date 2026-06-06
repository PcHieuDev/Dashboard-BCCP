---
id: TIP-ux-001
title: Tách Sidebar và tạo Topbar Component
status: planned
---

## Acceptance Criteria
1. File `dash_app/components/sidebar.py` chỉ còn chứa Profile Box và Menu Accordion.
2. File `dash_app/components/topbar.py` được tạo mới, chứa toàn bộ dropdown (Year, Month, Period, Compare, Cum, Buu_cuc, v.v.).
3. Nút `btn-apply-filter` (Lọc dữ liệu) màu xanh nằm ở cuối cùng bên phải của Topbar.
4. Topbar không được fixed/sticky (cuộn theo trang bình thường).
5. File `dash_app/app.py` được cập nhật để include Topbar nằm ngang phía trên `page-content`.
6. Code chạy thành công không văng lỗi syntax.
