## COMPLETION REPORT — TIP-bccp-002

**STATUS:** DONE
**TIMESTAMP:** 2026-06-04T01:12:00+07:00

**FILES CHANGED:**
- Created: None
- Modified: [import_callbacks.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/dash_app/callbacks/import_callbacks.py) — Thêm logic trigger calculate_new_customers sau khi nạp file BCCP thành công và hiển thị kết quả trên Alert.

**TEST RESULTS:**
- Acceptance criteria tested: 3/3 passed
- Details:
  - Given người dùng upload file BCCP RAW thành công: Tự động chạy trigger cập nhật `new_customers` tương ứng với tháng/năm của file vừa nạp.
  - Given re-import (nạp lại): Tự động xóa dữ liệu cũ của tháng đó và tính toán lại chính xác (không bị duplicate nhờ UNIQUE constraint và lệnh DELETE trước khi INSERT).
  - Given người dùng upload file khác (HCC, PHBC...): Bỏ qua không kích hoạt trigger, bảo đảm dữ liệu `new_customers` không bị ảnh hưởng.
  - Xử lý lỗi ngoại lệ an toàn qua khối try-except, bảo đảm nếu tính toán KH bán mới gặp lỗi thì tiến trình import chính vẫn thành công.

**ISSUES DISCOVERED:**
- None

**DEVIATIONS FROM SPEC:**
- None

**SUGGESTIONS:**
- None

**KARPATHY CHECK:**
- Assumptions surfaced: Yes — Giả định rằng `nam_du_lieu` có thể được truy vấn từ bảng `transactions` thông qua `import_batch` và `thang_du_lieu` thay vì sửa đổi interface trả về của hàm importer (bảo đảm tính cô lập của trigger).
- Simplicity test passed: Yes — Thiết lập trigger đơn giản, an toàn bằng cách import động trong callback để tránh circular import và bọc kín trong block try-except.
- Surgical changes only: Yes — Chỉ chèn thêm 24 dòng code trigger vào đúng vị trí sau khi import BCCP thành công.
- Success criteria verified: Yes
