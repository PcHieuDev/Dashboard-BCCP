# BUILD LOG: Dashboard-BCCP (Phase 6)
Builder started: 2026-06-02T18:03:00+07:00

---

## TIP-001: ETL — CSV cấu trúc mới + sync_mappings.py + backup
- Status: DONE
- Started: 2026-06-02T18:03:30+07:00
- Completed: 2026-06-02T18:05:00+07:00
- Files: 0 created, 1 modified
- Tests: 1/1 passed
- Issues: None
- Notes: Sửa hàm `sync_spdv` trong `scripts/sync_mappings.py` để tạo file backup `data/dim_dichvu_backup_YYYYMMDD_HHMMSS.csv` và chạy lệnh DELETE để làm sạch các dòng cũ của BCCP & mã HCC trong khi bảo tồn các dòng seed khác trước khi nạp lại từ CSV. Kiểm thử đồng bộ thành công 82 sản phẩm và 636 bưu cục, các mã `HCC001`-`HCC004` đã đổi nhóm chính sang `HCC`.

---

## TIP-002: Backend — Fix ten_cum + Cache + Format "-"
- Status: DONE
- Started: 2026-06-02T18:05:00+07:00
- Completed: 2026-06-02T18:10:00+07:00
- Files: 0 created, 3 modified
- Tests: 3/3 passed
- Issues: None
- Notes: Đã đổi tất cả `ten_Cum` -> `ten_cum` trong `global_metrics.py`. Cài đặt TTLDictCache in-memory cho hàm `get_revenue_by_cum`. Xử lý trả về `"-"` khi Kế hoạch = 0 hoặc None ở backend (`get_ytd_completion_rate`) và hiển thị `"-"` đối với các giá trị `inf`/`nan`/`0` tại hàm format `pct_change` của DataTable.

---

## TIP-003: Frontend — Trang chủ DataTable YTD 4 màu
- Status: DONE
- Started: 2026-06-02T18:10:00+07:00
- Completed: 2026-06-02T18:15:00+07:00
- Files: 0 created, 2 modified
- Tests: 3/3 passed
- Issues: None
- Notes: Đã gỡ bỏ `dcc.Graph` biểu đồ YTD cũ trên trang chủ và thay thế bằng `ytd-table-container` trong `dbc.Spinner`. Callback `update_global_overview` đã đổi sang render `dash_table.DataTable` chứa dữ liệu DT tháng, DT lũy kế YTD, tỷ lệ hoàn thành lũy kế kèm theo conditional formatting 4 màu (Đỏ/Cam/Vàng/Xanh lá) theo các ngưỡng tương ứng. Bảng có bật sorting native và hiển thị dòng TOÀN TỈNH nổi bật trên cùng.

---

## TIP-004: Frontend — HCC Revenue Page + Routing /bccp + Xóa PDF
- Status: DONE
- Started: 2026-06-02T18:15:00+07:00
- Completed: 2026-06-02T18:25:00+07:00
- Files: 2 created, 5 modified
- Tests: 4/4 passed
- Issues: None
- Notes: Loại bỏ hoàn toàn PDF khỏi toàn bộ dashboard (xóa nút PDF, callbacks trigger, dependencies reportlab/pdfkit và hàm generate_pdf_report). Rút gọn route `/bccp/kpi` -> `/bccp` trong app.py và sidebar.py. Xây dựng trang báo cáo doanh thu HCC mới tại `/hcc/revenue` (layout + callbacks) sử dụng engine truy vấn `query_hcc_revenue` riêng biệt, chỉ lọc nhóm chính HCC qua bảng `dim_dichvu` và hỗ trợ xuất báo cáo Excel tương tự BCCP.

---

## TIP-005: Frontend — Import UI (Upload CSV + nút Đồng bộ)
- Status: DONE
- Started: 2026-06-02T18:25:00+07:00
- Completed: 2026-06-02T18:30:00+07:00
- Files: 0 created, 2 modified
- Tests: 4/4 passed
- Issues: None
- Notes: Thêm vùng giao diện upload CSV và nút bấm "Đồng bộ danh mục Dịch vụ" ở cuối trang Import. Viết callback kiểm tra tính hợp lệ của cột `nhom_chinh` trong file CSV và ghi đè vào `data/mapping-spdv.csv`. Viết callback gọi `sync_mappings.py` thông qua subprocess với timeout 30 giây và làm sạch toàn bộ cache của Dashboard khi đồng bộ thành công.

---

## FIX-001: Còn nhiều instance ten_Cum trong callbacks — Gây lỗi bộ lọc Cụm
- Status: DONE
- Started: 2026-06-02T18:23:45+07:00
- Completed: 2026-06-02T18:24:45+07:00
- Files: 0 created, 3 modified
- Tests: 1/1 passed
- Issues: None
- Notes: Sửa toàn bộ `ten_Cum` -> `ten_cum` trong `global_callbacks.py`, `alerts_callbacks.py` và `service_callbacks.py`. Đồng thời sửa `ten_Buu_cuc` -> `ten_buu_cuc` trong `service_callbacks.py` để tránh KeyErrors từ Pandas và SQLite. Đã chạy thử nghiệm server không lỗi và bộ lọc Cụm/BĐX hoạt động 100%.

---

## TIP-006: Backend — Fix sync_url_to_tabs_navigation default
- Status: DONE
- Started: 2026-06-02T19:00:00+07:00
- Completed: 2026-06-02T19:15:00+07:00
- Files: 0 created, 6 modified
- Tests: N/A
- Issues: None
- Notes: Sửa giá trị mặc định của callback điều hướng, bổ sung logic guard bảo vệ biểu đồ KPI khi người dùng click khỏi `/bccp`.

---

## TIP-007: Frontend — Sidebar ẩn/hiện bộ lọc BCCP theo URL
- Status: DONE
- Started: 2026-06-02T19:15:00+07:00
- Completed: 2026-06-02T19:25:00+07:00
- Files: 0 created, 3 modified
- Tests: N/A
- Issues: None
- Notes: Loại bỏ hẳn giao diện "Sản phẩm Dịch vụ" cũ. Các bộ lọc Nhóm DV và Cụm giờ sẽ được toggle bằng CSS thay vì bị xóa hẳn khỏi vDOM, bảo đảm callback không crash.

---

## TIP-008: UI — Thay thẻ HCC thành thẻ PHBC (KPI)
- Status: DONE
- Started: 2026-06-02T19:28:00+07:00
- Completed: 2026-06-02T19:35:00+07:00
- Files: 0 created, 2 modified
- Tests: N/A
- Issues: None
- Notes: Sửa lại thiết kế lưới Grid của KPI cards, đổi card HCC sang PHBC. Đã cập nhật logic tính tổng doanh thu cho BCCP.

---

## TIP-009: Database & ETL — Bảng transactions_phbc + Import PHBC
- Status: DONE
- Started: 2026-06-02T19:28:00+07:00
- Completed: 2026-06-02T19:33:00+07:00
- Files: 1 created, 1 modified
- Tests: 1/1 passed
- Issues: Lỗi UTF-8 print ra console nhưng logic DB thì thành công tuyệt đối.
- Notes: Khởi tạo schema cho PHBC, code ETL nạp file logic tự nhận diện cột thông minh.

---

## TIP-010: UI — Thêm Option PHBC vào màn hình Import
- Status: DONE
- Started: 2026-06-02T19:30:00+07:00
- Completed: 2026-06-02T19:35:00+07:00
- Files: 0 created, 2 modified
- Tests: N/A
- Issues: None
- Notes: Thêm select option vào UI Dashboard để import PHBC dễ dàng.

---

## SUMMARY
- Total TIPs: 10
- Total FIXs: 1
- DONE: 11
- BLOCKED: 0
- Overall: READY FOR VERIFY
