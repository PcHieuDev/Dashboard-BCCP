## COMPLETION REPORT — TIP-bccp-005

**STATUS:** DONE
**TIMESTAMP:** 2026-06-04T02:00:00+07:00

**FILES CHANGED:**
- Created:
  - [new_customer.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/dash_app/pages/new_customer.py) — Bố cục trang Báo cáo Khách hàng mới gồm 3 Block: KPI Cards tổng hợp (SL KH mới, Doanh thu, % Đạt), Chi tiết theo Nhóm DV (Truyền thống, TMĐT) và Bảng BĐX kèm bộ lọc BĐX & nút xuất Excel.
  - [new_customer_callbacks.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/dash_app/callbacks/new_customer_callbacks.py) — Callback cascade bộ lọc Cụm ->Dropdown BĐX, callback chính truy vấn dữ liệu từ bảng `new_customers` và `plans_new_customer`, xử lý tính toán KPIs, hiển thị DataTable (với phân trang, sort native và dòng tổng cộng) và callback xuất báo cáo Excel in-memory thông qua `openpyxl`.
- Modified: None
- Deleted: None

**TEST RESULTS:**
- Acceptance criteria tested: 4/4 passed
- Details:
  - Khi truy cập `/bccp/new-customer`, KPI cards hiển thị chính xác số lượng KH mới, doanh thu phát triển mới và tỷ lệ hoàn thành kế hoạch so với bảng dữ liệu plans.
  - Bộ lọc Cụm ở sidebar tương tác cascade mượt mà: chọn cụm "Vinh" thì dropdown BĐX trên trang chỉ hiển thị các bưu điện huyện/xã tương ứng của cụm Vinh và bảng dữ liệu tự động lọc theo.
  - Nút "Xuất Excel" tạo ra file Excel chuẩn format của dự án (màu sắc header, border mảnh, font chữ, tự động co giãn chiều rộng cột, định dạng hiển thị tiền tệ, số lượng và phần trăm).
  - Với các BĐX không có kế hoạch bán mới được khai báo trong DB, cột kế hoạch và tỷ lệ đạt được hiển thị dấu "-" chính xác như đặc tả.

**ISSUES DISCOVERED:**
- None

**DEVIATIONS FROM SPEC:**
- None

**SUGGESTIONS:**
- Việc gộp logic tính toán KPIs tổng hợp và KPIs chi tiết dịch vụ vào cùng một callback chính giúp tăng hiệu năng phản hồi, tránh truy vấn database SQLite nhiều lần.

**KARPATHY CHECK:**
- Assumptions surfaced: Yes — Xác nhận định dạng dữ liệu trong bảng `plans_new_customer` khớp nối qua cột `ma_xa` với `ma_bdx` của `new_customers`.
- Simplicity test passed: Yes — Thiết kế code rõ ràng, tách biệt giữa hàm xử lý dữ liệu (Pandas) và callback Dash.
- Surgical changes only: Yes — Chỉ tạo mới file layout và callback của trang.
- Success criteria verified: Yes
