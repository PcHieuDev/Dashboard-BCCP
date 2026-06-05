## COMPLETION REPORT — TIP-refactor-004

**STATUS:** DONE
**TIMESTAMP:** 2026-06-05T15:48:00+07:00

**FILES CHANGED:**
- Modified: `dash_app/callbacks/customer_callbacks.py`, `dash_app/callbacks/new_customer_callbacks.py`, `dash_app/callbacks/retention_callbacks.py`
  - Chuyển đổi các callback chính và callback xuất Excel sang nhận `State` `start_date` / `end_date` trực tiếp.
  - Bổ sung logic chặn truy vấn và xuất Excel nếu khoảng ngày lớn hơn 31 ngày tại trang Khách hàng mới và Khách hàng hiện hữu/Duy trì. Trả về `dbc.Alert` thông báo lỗi trực tiếp trên giao diện để bảo vệ hiệu năng hệ thống.

**TEST RESULTS:**
- Acceptance criteria tested: 1/1 passed
- Details: Chặn lọc trên 31 ngày hoạt động hoàn hảo, hiển thị Alert đỏ cảnh báo, không gây lag DB.

**KARPATHY CHECK:**
- Assumptions surfaced: No
- Simplicity test passed: Yes
- Surgical changes only: Yes
- Success criteria verified: Yes
