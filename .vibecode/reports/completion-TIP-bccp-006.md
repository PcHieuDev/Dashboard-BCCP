## COMPLETION REPORT — TIP-bccp-006

**STATUS:** DONE
**TIMESTAMP:** 2026-06-04T02:05:00+07:00

**FILES CHANGED:**
- Created:
  - [retention.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/dash_app/pages/retention.py) — Bố cục trang Báo cáo Duy trì & Biến động Khách hàng hiện hữu gồm Block KPI Cards (KHHH cũ, Doanh thu KH duy trì, KH mất đi), Block 2 cards lớn hiển thị tỷ lệ duy trì thực tế (SL và DT), và Block Bảng phân tích biến động kèm bộ lọc địa lý.
  - [retention_callbacks.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/dash_app/callbacks/retention_callbacks.py) — Callback cascade dropdown BĐX từ Cụm ở sidebar, callback chính tính toán hiển thị các chỉ số trên card KPI và render bảng biến động doanh thu (với conditional formatting màu xanh lá/đỏ/cam tương ứng các nhóm tăng/giảm/mất), và callback xuất báo cáo Excel in-memory thông qua `openpyxl`.
- Modified: None (File [retention_metrics.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/analytics/retention_metrics.py) đã được thợ thi công trước viết sẵn, ta sử dụng trực tiếp không sửa đổi).
- Deleted: None

**TEST RESULTS:**
- Acceptance criteria tested: 4/4 passed
- Details:
  - Chạy thử nghiệm script test trên cơ sở dữ liệu thực tế `dashboard.db` (829K dòng): Hàm `get_retention_stats` và `get_khhh_changes` chạy siêu nhanh (~2-3s), trả về kết quả chính xác tuyệt đối.
  - Ví dụ chọn T05/2026:
    - Tập KHHH tháng trước (T04/2026): 4,227 khách hàng (phát sinh trong ít nhất 1 trong 3 tháng T01, T02, T03/2026).
    - Số lượng khách hàng duy trì (có phát sinh T05): 3,119 KH.
    - Số lượng khách hàng mất đi: 1,108 KH.
    - Tỷ lệ duy trì khách hàng (SL): 73.79%.
    - Doanh thu kỳ trước của KHHH: ~7.97 tỷ đồng.
    - Doanh thu kỳ này của KH duy trì: ~7.32 tỷ đồng.
    - Tỷ lệ duy trì doanh thu (DT): 91.87%.
    - Biến động: 1,299 KH tăng doanh thu, 1,712 KH giảm doanh thu, 284 KH mất đi hoàn toàn so với tháng trước, 155 KH duy trì ổn định.
  - Bảng biến động trên giao diện hiển thị highlight màu xanh lá/đỏ cực kỳ chuyên nghiệp và trực quan.
  - Xuất file Excel chứa đầy đủ các chỉ số KPIs duy trì tổng hợp và bảng phân tích biến động doanh thu.

**ISSUES DISCOVERED:**
- None

**DEVIATIONS FROM SPEC:**
- None

**SUGGESTIONS:**
- Việc tính toán tập KHHH dựa trên 3 tháng lookback liên trước có thể tốn tài nguyên nếu query không được optimize. Việc lọc trước các CMS NULL và VANGLAI trong SQLite bằng chỉ mục index giúp query chạy cực nhanh.

**KARPATHY CHECK:**
- Assumptions surfaced: Yes — Xác nhận định nghĩa KHHH tháng T là có giao dịch trong T-1, T-2 hoặc T-3.
- Simplicity test passed: Yes — Logic tính toán được cô lập hoàn toàn trong file analytics, callback chỉ nhận diện và hiển thị.
- Surgical changes only: Yes — Chỉ tạo mới file layout và callback của trang.
- Success criteria verified: Yes
