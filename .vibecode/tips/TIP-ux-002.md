---
id: TIP-ux-002
title: Chuyển sang Manual Load (KPI, Retention, New Customer)
status: planned
---

## Acceptance Criteria
1. Bổ sung `prevent_initial_call=True` vào toàn bộ callbacks của `kpi_callbacks.py`, `retention_callbacks.py`, `new_customer_callbacks.py`.
2. Đổi tất cả các `Input("tabs-navigation", "value")` thành `State("tabs-navigation", "value")` ở các callbacks render biểu đồ.
3. Nút "Lọc dữ liệu" (`btn-apply-filter`) là `Input` duy nhất kích hoạt các callbacks này.
4. Đảm bảo khi mới vào trang (chưa bấm Lọc), giao diện vẫn render nhưng dữ liệu trống/0, không tự động quay Spinner loading dữ liệu.
