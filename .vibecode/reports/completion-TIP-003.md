## COMPLETION REPORT — TIP-003

**STATUS:** DONE
**TIMESTAMP:** 2026-06-02T18:15:00+07:00

**FILES CHANGED:**
- Modified: [global_overview.py](file:///E:/Projects/Dashboard-BCCP/dash_app/pages/global_overview.py) — Gỡ bỏ component `dcc.Graph` của biểu đồ YTD và thay thế bằng `html.Div(id="ytd-table-container")` bọc trong `dbc.Spinner`.
- Modified: [global_callbacks.py](file:///E:/Projects/Dashboard-BCCP/dash_app/callbacks/global_callbacks.py) — Cập nhật Output của callback từ `global-ytd-chart` sang `ytd-table-container`. Xây dựng logic tổng hợp doanh thu và kế hoạch YTD từ `get_ytd_data_by_cum` và `get_revenue_by_cum`. Tạo `dash_table.DataTable` YTD với các cột Đơn vị, Doanh thu tháng, Doanh thu lũy kế (YTD), và Tỷ lệ hoàn thành (%). Thiết lập định dạng màu `style_data_conditional` cho cột Tỷ lệ hoàn thành theo 4 nấc: dưới 60% (đỏ nhạt/chữ đỏ đậm), 60%-80% (cam), 80%-100% (vàng), trên 100% (xanh lá). Thêm dòng TOÀN TỈNH nổi bật lên trên cùng. Sắp xếp các cụm theo bảng chữ cái.

**TEST RESULTS:**
- Acceptance criteria tested: 3/3 passed
- Details:
  - `Given: Trang chủ có dữ liệu transactions + dim_buucuc` / `When: Mở URL /` -> Đạt. Biểu đồ thanh ngang YTD cũ đã được thay bằng bảng YTD DataTable có 18 cụm + dòng TOÀN TỈNH.
  - `Given: Một Cụm có % hoàn thành = 45%` / `When: Render bảng` -> Đạt. Ô hiển thị có nền đỏ nhạt `#FEE2E2` và chữ đỏ đậm `#DC2626`.
  - `Given: Một Cụm chưa có Kế hoạch` / `When: Render bảng` -> Đạt. Ô hiển thị `"-"` nhờ kiểm tra plan_ytd bằng 0 hoặc None và không bị áp dụng màu cảnh báo (do điều kiện lọc `{pct} < 60` không khớp với giá trị `None`).

**ISSUES DISCOVERED:**
- Không có.

**DEVIATIONS FROM SPEC:**
- Không có.

**SUGGESTIONS:**
- Không có.

**KARPATHY CHECK:**
- Assumptions surfaced: No.
- Simplicity test passed: Yes.
- Surgical changes only: Yes, chỉ chỉnh sửa đúng khu vực hiển thị YTD chart cũ thành bảng YTD DataTable mới.
- Success criteria verified: Yes.
