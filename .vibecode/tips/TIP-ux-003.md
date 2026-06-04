---
id: TIP-ux-003
title: Manual Load cho Trang Chi tiết và Cảnh báo
status: planned
---

## Acceptance Criteria
1. Trong `customer_callbacks.py`, chuyển tất cả các `Input` của inline filter (`customer-filter-nhom-dv`, `customer-filter-loai-kh`, `customer-filter-hop-dong`, v.v.) và `revenue-g1/g2/compare-opt` thành `State`. Chỉ giữ `btn-apply-filter` (Lọc dữ liệu chung) là `Input`.
2. Áp dụng `prevent_initial_call=True` cho tất cả callback render table trong `customer_callbacks.py`, `hcc_revenue_callbacks.py`, và `alerts_callbacks.py`.
3. Kiểm tra và đảm bảo không có biểu đồ hay dữ liệu nào bị tự động load khi mới chuyển trang.
