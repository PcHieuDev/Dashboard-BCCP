## COMPLETION REPORT — TIP-bccp-001

**STATUS:** DONE
**TIMESTAMP:** 2026-06-04T01:05:00+07:00

**FILES CHANGED:**
- Created: [new_customer_calculator.py](file:///E:/Projects/worktrees/Dashboard-BCCP/feat-bccp-upgrade/analytics/new_customer_calculator.py) — Module tính toán KH bán mới theo tháng và nạp lịch sử.
- Modified: None

**TEST RESULTS:**
- Acceptance criteria tested: 4/4 passed
- Details:
  - Given dữ liệu transactions từ T05/2025: Chạy nạp lịch sử tạo ra dữ liệu chính xác từ T10/2025 đến T06/2026.
  - Given CMS bán mới (không giao dịch trong 3 tháng trước): Được lọc ra và chèn vào bảng `new_customers`.
  - Given CMS đã giao dịch trong lookback: Bị loại bỏ chính xác khỏi danh sách KH mới.
  - Given chạy lại cho tháng cũ: Dữ liệu cũ bị xóa hoàn toàn trước khi nạp lại, không bị duplicate.

**ISSUES DISCOVERED:**
- None

**DEVIATIONS FROM SPEC:**
- None

**SUGGESTIONS:**
- Dữ liệu `plans_new_customer` sử dụng cột `ma_xa` khớp trực tiếp với `ma_bdx` của `dim_buucuc` (đều có độ dài 4 chữ số), điều này giúp việc join so sánh KPI ở các bước sau rất thuận lợi.

**KARPATHY CHECK:**
- Assumptions surfaced: Yes — Xác nhận cấu trúc `ma_bdx` (4 chữ số) khớp với `ma_xa` của kế hoạch bán mới.
- Simplicity test passed: Yes — Dùng Window Function (`ROW_NUMBER() OVER`) trong SQLite để xử lý tập hợp thay vì loop từng dòng, giúp tối ưu hóa thời gian thực thi (nạp toàn bộ lịch sử 9 tháng chỉ mất vài giây).
- Surgical changes only: Yes — Chỉ viết file mới, không động chạm sang các file khác của hệ thống.
- Success criteria verified: Yes
