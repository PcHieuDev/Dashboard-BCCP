# TIP-007 Completion Report
- **Status**: DONE
- **Issues Found**: None
- **Resolution**: 
  - Xóa ID `sidebar-spdv` khỏi file `sidebar.py`.
  - Tách nhóm bộ lọc riêng cho BCCP vào ID `bccp-extra-filters`.
  - Thêm logic vào `sidebar_callbacks.py` để ẩn/hiện nhóm này thông qua CSS `display` khi URL thay đổi (hiện ở `/bccp*`, ẩn ở các nơi khác).
  - Gỡ bỏ hoàn toàn biến `spdv` khỏi Input và đối số của toàn bộ callbacks. Mặc định gán `spdv = None` bên trong hàm.
