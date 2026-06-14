# Project State - Dashboard Doanh thu BCCP

## 📌 Tóm Tắt Trạng Thái Dự Án (Nhanh)

### 1. Mục tiêu cuối cùng của dự án (Project Goal)
- Xây dựng hệ thống Dashboard doanh thu bưu chính chuyển phát (BCCP) chuyên nghiệp bằng Dash (Python).
- Hỗ trợ bộ lọc đa chiều (Thời gian, Địa lý 3 cấp: Cụm/Bưu cục/Xã, Nhóm dịch vụ) ổn định trên cả giao diện web và đồng bộ URL.
- Tự động phân loại khách hàng (Mới, Hiện hữu, Tái bán, Vãng lai).
- Import dữ liệu trực tiếp từ các file Excel báo cáo thô vào cơ sở dữ liệu SQLite (sẽ chuyển sang PostgreSQL khi deploy).
- Phục vụ cho hơn 20 người dùng từ các phòng ban nghiệp vụ và deploy lên server nội bộ để truy cập qua mạng LAN hoặc đường hầm Cloudflare (`dashboard.bdna.io.vn`).

### 2. Các công việc chính đã hoàn thành (Completed Milestones)
- **Phase 18 (14/06/2026): Đồng bộ danh mục CSDL SQLite vào 3 file mẫu nhập liệu và đồng nhất công thức đối chiếu thông minh chống lệch định dạng**:
  - **Đồng bộ tham chiếu mới nhất:** Tạo và thực thi script [sync_excel_templates.py](file:///E:/Projects/Dashboard-BCCP/scripts/sync_excel_templates.py) giúp tự động nạp danh sách 777 bưu cục (bao gồm cả mã xã 4 số và mã cụm đại diện) từ bảng `dim_buucuc` và 102 sản phẩm dịch vụ từ bảng `dim_dichvu` vào các sheet Ref của cả 3 file Excel mẫu nhập liệu.
  - **Công thức đối chiếu thông minh thống nhất:** Cập nhật đồng nhất toàn bộ 5,000 -> 10,000 dòng ở tất cả 3 file mẫu sang công thức so khớp thông minh: `=IF(B2="","",IF(OR(ISNUMBER(MATCH(B2,Ref_BuuCuc!$A$2:$A$10000,0)),ISNUMBER(MATCH(B2&"",Ref_BuuCuc!$A$2:$A$10000,0)),IFERROR(ISNUMBER(MATCH(VALUE(B2),Ref_BuuCuc!$A$2:$A$10000,0)),FALSE)),"OK","Sai mã bưu cục"))`. Tự động nhận diện chính xác kể cả khi người dùng nhập mã bưu cục dưới dạng Số hay dạng Chuỗi (Text), tránh tuyệt đối lỗi cảnh báo giả khi copy dán dữ liệu.
- **Phase 17 (11/06/2026): Nạp Kế hoạch 2026 mới, Bổ sung Bưu cục, Import dữ liệu tháng 6, Gộp kế hoạch vào nhóm chính, Fix Bug DB Lock & Rebuild summaries sạch sẽ**:
  - **Kế hoạch mới & Gộp nhóm:** Xóa toàn bộ kế hoạch cũ (`plans` và `plans_weekly`), nạp kế hoạch mới năm 2026 từ file [import_ke_hoach_TT_TMDT_QT_HCC_2026.xlsx](file:///E:/Projects/Dashboard-BCCP/data/du-lieu-new/import_ke_hoach_TT_TMDT_QT_HCC_2026.xlsx) (20,820 chỉ tiêu kế hoạch tháng phân bổ) và phân bổ lại kế hoạch tuần. Theo yêu cầu của Sếp, đã chạy script gộp kế hoạch các nhóm dịch vụ con (TMĐT, Truyền thống, Quốc tế, Chuyển phát HCC) vào nhóm chính (BCCP, HCC) để quản lý kế hoạch chung ở cấp cao nhất.
  - **Bổ sung bưu cục:** Nạp bổ sung danh sách bưu cục từ file [bo_sung_buu_cuc.xlsx](file:///E:/Projects/Dashboard-BCCP/data/du-lieu-new/bo_sung_buu_cuc.xlsx) vào bảng `dim_buucuc` (3 bưu cục mới).
  - **Import dữ liệu BCCP tháng 6:** Nạp thành công dữ liệu thô BCCP từ 4 tệp Excel tháng 6 (`06-07.06.xls`, `08.06.xls`, `09.06.xls`, `10.06.xls`) trong thư mục `2026\T06`.
  - **Rebuild CSDL & Backup:** Chạy lại toàn bộ tiến trình rebuild summaries để đồng bộ hóa số liệu tổng hợp tuần/tháng/khách hàng mới trên CSDL mới. Tạo bản sao lưu mới nhất tại `backups/` và dọn dẹp (xóa sạch) toàn bộ các bản sao lưu cũ khác (chỉ giữ bản mới nhất), di dời tệp `dashboard_corrupted.db` ra khỏi OneDrive về thư mục `scratch`.
  - **Nâng cấp đối chiếu file mẫu:** Chạy script tự động cập nhật danh sách bưu cục/dịch vụ mới nhất vào sheet Ref của các file Excel mẫu và copy toàn bộ các file mẫu đã cập nhật sang thư mục code chính `E:\Projects\Dashboard-BCCP\data\mau-file-import`.
  - **Sửa lỗi Database Lock:** Sửa triệt để lỗi `sqlite3.OperationalError: database is locked` do mở kết nối lồng nhau trong `check_missing_mappings` khi chạy ở chế độ SQLite không WAL (`delete`).
- **Phase 16 (11/06/2026): Tối ưu hóa ETL Import thô phân rã ngày, chế độ ghi đè sửa chữa, tối ưu hóa gộp số liệu SQLite UPSERT, sửa tràn bảng Lịch sử import, và nâng cấp file mẫu Excel đối chiếu thông minh**:
  - **Cấu trúc bảng thô dịch vụ phụ (`transactions_hcc/tcbc/ppbl/phbc`):** Đồng nhất 100% cấu trúc, thêm các trường khoảng ngày (`tu_ngay`, `tu_thang`, `tu_nam`...), cột `ten_dich_vu`, `san_luong`, `stt` (Số thứ tự dòng gốc) và hàm tự động kiểm tra nâng cấp di cư CSDL.
  - **Phân rã ngày từ import:** Hàm `import_service_excel` tự động phân rã dòng tuần/tháng thành từng ngày cụ thể; Doanh thu chia đều dạng REAL, Sản lượng phân bổ làm tròn tích lũy dạng INTEGER, giữ nguyên STT dòng.
  - **Ghi đè sửa chữa (`mode == 'overwrite'`):** Xóa sạch chính xác dữ liệu cũ trùng bưu cục/dịch vụ/ngày cụ thể của dữ liệu nạp mới trước khi ghi đè, bảo toàn dữ liệu ngày khác.
  - **Gộp tuần/tháng SQLite UPSERT:** Viết lại `rebuild_monthly` và `rebuild_weekly` gộp số liệu trực tiếp bằng SQL dựa trên ngày cụ thể, sử dụng SQLite UPSERT `ON CONFLICT DO UPDATE` để tự động cộng dồn/triệt tiêu sai số. Tốc độ gộp siêu nhanh và chính xác 100%.
  - **Sửa giao diện bảng Lịch sử:** Cấu hình DataTable cột `file_name` hiển thị dấu ba chấm (`ellipsis`, `maxWidth: '220px'`), giúp bảng ngay ngắn không bị tràn ngang.
  - **Nâng cấp file mẫu Excel đối chiếu:** Bổ sung sheet Ref và công thức đối chiếu thông minh chống lỗi định dạng Số/Chuỗi; kéo sẵn cho **5,000 dòng** (dịch vụ khác, kế hoạch) và **10,000 dòng** (doanh thu BCCP); nhúng **Conditional Formatting Premium Pastel** tô màu xanh pastel (`OK`) và đỏ pastel (`Sai...`), giữ các ô trống không có dữ liệu màu trắng sạch sẽ.
- **Phase 13 (10/06/2026): Đồng bộ lịch tuần & Chuẩn hóa so sánh Doanh thu / Kế hoạch 3 cấp**:
  - Đồng bộ mốc lịch tuần các năm cũ (2025) theo mốc ngày năm 2026 trong [week_calendar.py](file:///E:/Projects/Dashboard-BCCP/config/week_calendar.py), fix lệch ngày so sánh YoY.
  - Chuẩn hóa logic gộp Doanh thu & Kế hoạch 3 cấp trong [global_metrics.py](file:///E:/Projects/Dashboard-BCCP/analytics/global_metrics.py): Cấp Cụm dùng `outer join` gom nhóm theo xã thực tế và kế hoạch HCC, loại trừ xã ảo `"Đại diện Cụm"`; Cấp Xã so sánh bưu cục thực tế có phát sinh doanh thu (`tong_dt > 0`), hiển thị `"Không có KH"` nếu kế hoạch bằng 0.
  - Thay đổi dòng đầu tiên ở 2 bảng Chi tiết doanh thu và Lũy kế YTD thành nhãn động theo bộ lọc địa lý (`"⭐️ CỤM: <tên cụm>"`, `"⭐️ XÃ: <tên xã>"`, hoặc `"⭐️ BC: <tên bưu cục>"`).
  - Sửa đổi hiển thị `% hoàn thành kế hoạch` ở Top 10 Bưu điện Xã nổi bật chỉ hiện chữ số màu đen, loại bỏ mũi tên lên/xuống và màu xanh/đỏ.
  - Rebuild thành công toàn bộ summary tables khớp theo lịch tuần đồng bộ mới.
  - Cập nhật file chạy [run_dashboard.bat](file:///E:/Projects/Dashboard-BCCP/run_dashboard.bat) tự động giải phóng port 8050 bị treo và in thông báo chào Sếp bằng tiếng Việt UTF-8 có dấu.
- **Framework & Giao diện**: Chuyển đổi hoàn toàn từ Streamlit sang Dash, hoàn thiện giao diện Phase 11 ổn định.
- **Sửa 4 nhóm bug logic và UI (09/06/2026 sáng)**:
  - Sửa lỗi bảng Lũy kế YTD không nhận bộ lọc Bưu điện Xã.
  - Sửa lỗi các bảng Top 10 trong trang con (/bccp, /hcc, /tcbc, /ppbl) lấy sai Kế hoạch toàn cục thay vì kế hoạch riêng của từng dịch vụ.
  - Fix lỗi bảng chi tiết không phân rã theo bưu cục khi chọn bộ lọc cấp Xã ở các trang con.
  - Cập nhật các bảng Top 10, biểu đồ 12 kỳ, KPI thẻ màu ở trang chủ để đáp ứng chuẩn xác bộ lọc Cụm, Xã, Bưu cục.
  - Sửa lỗi URL dư dấu `/` ở nút "Lọc Dữ liệu".
- **Kiểm tra & Fix toàn diện 4 nội dung (09/06/2026 tối — Phase 12)**:
  - ✅ Xác minh template trang chủ (nhom_chinh) vs trang con (nhom_dich_vu) khớp 100%.
  - ✅ Xác minh bộ lọc địa lý 3 cấp hoạt động đúng (Toàn tỉnh → Cụm → BĐX → Bưu cục).
  - 🔧 **Fix bug crash Tuần 1**: Xóa `return prev_value, prev_year` sai tại dòng 711 `global_metrics.py`.
  - 🔧 **Fix auto-select tuần**: Sửa từ ISO week sang custom week (ISO=24 ≠ Custom=23).
  - 🔧 **Fix reset chu kỳ**: Thêm callback reset tháng/tuần về hiện tại khi switch Tháng↔Tuần.
  - 🔧 **Fix KH Lũy kế YTD**: `plans WHERE thang <= period_value` thay vì lấy cả năm.
  - 🔧 **Fix UI Bảng B**: Xóa option "Kỳ trước" khỏi bảng Lũy kế (global & service overview) — bảng lũy kế chỉ có Cùng kỳ và Kế hoạch.
- **Khắc phục triệt để lỗi Bộ lọc & Logic (09/06/2026)**:
  - Sửa lỗi nhân bản doanh thu (multiplied totals) khi lọc số liệu qua bảng danh mục.
  - Sửa lỗi bảng Lũy kế YTD so sánh nhầm kế hoạch tháng (đã chuyển sang so sánh kế hoạch cả năm).
  - Khắc phục lỗi hiển thị mã Đại diện Cụm / Xã (ảo) tại Top 10 Bưu điện Xã.
  - Sửa lỗi bộ lọc Tuần bất ổn định và bị nhảy sai số khi chuyển qua lại giữa các trang.
  - Hoàn thiện Sidebar Menu Accordion, giữ trạng thái Active chính xác cho mọi trang con.
- **Quy tắc Kế hoạch 3 cấp**: BCCP (cấp Bưu cục), HCC (cấp Xã), PHBC (cấp Cụm) hoạt động trơn tru. Sửa triệt để lỗi tỷ lệ hoàn thành >300%.
- **Import & ETL**: Chuẩn hóa các mẫu Excel import mới rút gọn cột cốt lõi. Tự động hóa phân bổ kế hoạch năm ra 12 tháng theo tỷ lệ. Nạp thành công kế hoạch HCC 2026 và dữ liệu lịch sử tháng 4, 5, 6 năm 2025/2026.

### 3. Trạng thái các file cốt lõi hiện tại (File Status)
- [app.py](file:///E:/Projects/Dashboard-BCCP/dash_app/app.py): Đóng vai trò khởi chạy ứng dụng Dash. Đã fix lỗi trailing slash ở URL pathname.
- Thư mục [callbacks/](file:///E:/Projects/Dashboard-BCCP/dash_app/callbacks/): Chứa các logic tương tác. Đã vá thành công các tệp `global_callbacks.py` và `service_callbacks.py` để bổ sung logic phân rã cấp bưu cục và service_key.
- [global_metrics.py](file:///E:/Projects/Dashboard-BCCP/analytics/global_metrics.py): Cập nhật các hàm truy vấn SQL YTD, Top 10, biểu đồ 12 kỳ hỗ trợ bộ lọc bưu cục và service_key. **Fix bug 711 (crash tuần 1) và fix KH YTD lũy kế.**
- [topbar_callbacks.py](file:///E:/Projects/Dashboard-BCCP/dash_app/callbacks/topbar_callbacks.py): **Fix auto-select custom week và thêm callback reset tháng/tuần về hiện tại.**
- [global_overview.py](file:///E:/Projects/Dashboard-BCCP/dash_app/pages/global_overview.py): **Xóa option "Kỳ trước" khỏi bảng Lũy kế B.**
- [service_overview.py](file:///E:/Projects/Dashboard-BCCP/dash_app/pages/service_overview.py): **Xóa option "Kỳ trước" khỏi bảng Lũy kế B cho 4 trang dịch vụ.**
- [importer.py](file:///E:/Projects/Dashboard-BCCP/etl/importer.py) & [aggregator.py](file:///E:/Projects/Dashboard-BCCP/etl/aggregator.py): Hoạt động chuẩn xác, hỗ trợ nạp song song cả cấu trúc file cũ và file mẫu tinh giản mới.
- [rebuild_summaries.py](file:///E:/Projects/Dashboard-BCCP/scripts/rebuild_summaries.py): Tính toán lại các bảng tổng hợp khi CSDL thay đổi.
- [dashboard.db](file:///E:/OneDrive/z.Database-TTKD-Data/dashboard.db): Chứa dữ liệu sạch, đã đồng bộ kế hoạch HCC mới nhất.
- Thư mục [mau-file-import/](file:///E:/Projects/Dashboard-BCCP/data/mau-file-import/): Chứa 3 file mẫu chuẩn hóa và file danh mục tham chiếu.



## Project Goal
- Xây dựng hệ thống Dashboard doanh thu bưu chính chuyển phát (BCCP) chuyên nghiệp bằng Dash (Python).
- Hỗ trợ bộ lọc đa chiều (Thời gian, Địa lý 3 cấp: Cụm/Bưu cục/Xã, Nhóm dịch vụ) ổn định trên cả giao diện web và đồng bộ URL.
- Tự động phân loại khách hàng (Mới, Hiện hữu, Tái bán, Vãng lai).
- Import dữ liệu trực tiếp từ các file Excel báo cáo thô vào cơ sở dữ liệu SQLite (sẽ chuyển sang PostgreSQL khi deploy).
- Phục vụ cho hơn 20 người dùng từ các phòng ban nghiệp vụ và deploy lên server nội bộ để truy cập qua mạng LAN hoặc đường hầm Cloudflare (`dashboard.bdna.io.vn`).

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đã chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite (đang lưu trữ đồng bộ trên OneDrive) -> PostgreSQL khi deploy server
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl, xlrd>=2.0.1 (đọc file .xls)
- **Encoding**: UTF-8 toàn bộ

## Current State
- **Đồng bộ Lịch Tuần & Chuẩn hóa So sánh Doanh thu / Kế hoạch 3 cấp (Phase 13 - 10/06/2026)**:
  - **Đồng bộ mốc lịch tuần**: Sửa đổi [week_calendar.py](file:///E:/Projects/Dashboard-BCCP/config/week_calendar.py) để đồng bộ mốc ngày của năm trước (2025) theo mốc ngày của năm chuẩn 2026, giải quyết triệt để lệch ngày khi so sánh cùng kỳ YoY theo tuần.
  - **Chuẩn hóa gộp Doanh thu & Kế hoạch 3 cấp**:
    - *Cấp Cụm (so sánh các Xã)*: Nhóm theo xã (`ma_bdx`), sử dụng outer join để tích hợp đầy đủ doanh thu thực tế và kế hoạch HCC của từng xã. Loại bỏ các xã ảo dạng `"Đại diện Cụm ..."` khỏi bộ lọc và bảng dữ liệu.
    - *Cấp Xã (so sánh các bưu cục 6 số)*: Chỉ giữ lại các bưu cục thực tế có phát sinh doanh thu (`tong_dt > 0`). Đối với chỉ tiêu không giao kế hoạch (hoặc kế hoạch = 0) hiển thị rõ `"Không có KH"` thay vì tính % hoàn thành kế hoạch vô lý.
  - **Nhãn tổng hợp dòng đầu động**: Thay vì hiển thị cứng `"⭐️ TOÀN TỈNH"`, dòng đầu tiên ở bảng Chi tiết doanh thu và Lũy kế YTD hiển thị động theo cấp bộ lọc: `"⭐️ CỤM: <tên cụm>"`, `"⭐️ XÃ: <tên xã>"`, hoặc `"⭐️ BC: <tên bưu cục>"` tại [global_callbacks.py](file:///E:/Projects/Dashboard-BCCP/dash_app/callbacks/global_callbacks.py) và [service_callbacks.py](file:///E:/Projects/Dashboard-BCCP/dash_app/callbacks/service_callbacks.py).
  - **Cập nhật Top 10 HCC**: Chỉnh sửa hiển thị chỉ số % hoàn thành kế hoạch ở bảng Top 10 xã nổi bật (HCC) chỉ hiện chữ số màu đen thông thường, loại bỏ mũi tên lên/xuống và màu xanh/đỏ.
  - **Rebuild cơ sở dữ liệu**: Thực thi thành công `rebuild_summaries.py` đồng bộ hóa lại toàn bộ các bảng tổng hợp (`agg_weekly`, `plans_weekly`, `new_customers`) theo lịch tuần đồng bộ mới.
  - **Giải phóng port 8050 khi khởi động**: Nâng cấp [run_dashboard.bat](file:///E:/Projects/Dashboard-BCCP/run_dashboard.bat) để tự động kiểm tra và kill tiến trình Python cũ đang chiếm dụng cổng 8050 (nếu có) bằng lệnh `taskkill`, đồng thời in ra câu chào tiếng Việt có dấu.
- **Sửa lỗi Phân loại Sản phẩm & Tinh gọn File Nhập (08/06/2026)**:
  - Phân loại lại 4 mã `HCC001`-`HCC004` sang nhóm `Chuyển phát HCC` và xóa mã ảo thừa trong danh mục, xuất lại file tham chiếu `ma_tham_chieu.xlsx`.
  - Tinh gọn mẫu Excel nhập kế hoạch (`mau_import_ke_hoach.xlsx`), xóa bỏ cột Tháng và Sản lượng. Nâng cấp ETL `import_plan_excel` tự động phân bổ Kế hoạch Doanh thu Năm thành 12 Tháng bằng mảng tỷ lệ trích xuất từ file `ty-le.xlsx`.
  - Nghiệm thu nạp file thực tế: Đã import thành công Kế hoạch HCC chuẩn từ 103 Bưu cục/Xã, tự động phân bổ ra 1,236 bản ghi Kế hoạch tháng (Tổng KH: 14.77 tỷ đồng). Tiến trình `rebuild_summaries` đã hoàn tất để đồng bộ dữ liệu Dashboard.
- **Đại tu Kế hoạch & Bưu cục Xã (08/06/2026)**:
  - Sửa lỗi cột Kế hoạch: Đổi tên cột `nhom_dich_vu` -> `nhom_chinh` và `ten_dich_vu` -> `nhom_dich_vu` trong các bảng `plans`, `plans_weekly`.
  - Khởi tạo 123 Bưu cục ảo cấp Xã (mã 4 số khớp `ma_bdx`) để hệ thống ghi nhận và phân bổ kế hoạch/doanh thu chính xác ở cấp Xã.
  - Sinh file Excel `ma_tham_chieu.xlsx` gồm 3 sheet (Nhóm dịch vụ, Danh mục bưu cục, Sản phẩm) hỗ trợ tra cứu mã nạp file.
  - Xóa sạch 100% dữ liệu kế hoạch (tháng/tuần) của nhóm `HCC` cũ để sẵn sàng nạp kế hoạch mới theo cấu trúc chuẩn.
- **Fix "Bug Tàng Hình" Tuần & Hoàn thiện Bộ Lọc Cụm Trang Chủ (08/06/2026)**:
  - Khắc phục lỗi Off-by-one truy xuất nhầm số liệu tuần (chọn Tuần 22 hiển thị Tuần 23) tại file `utils.py` do sử dụng sai cấu trúc index mảng thay vì đối chiếu ID tuần.
  - Sửa lỗi Bộ lọc Địa lý (Cụm) không hoạt động ở trang Tổng quan: Bổ sung liên kết `State("sidebar-cum")` vào `global_callbacks.py` và nhúng cơ chế gọt số liệu theo Cụm (`WHERE ten_cum = ?`) vào các hàm truy vấn DB như `get_period_detail_by_xa`, `get_ytd_detail_by_xa`, `get_12_periods_revenue`.
- **Hoàn thiện nguyên tắc kế hoạch 3 cấp & Sửa logic Top 10 (07/06/2026)**:
  - Đã xử lý triệt để lỗi tỷ lệ hoàn thành >300% ở bảng Top 10 Xã bằng cách áp dụng nguyên tắc: "Nạp cấp nào, so sánh cấp đó, cộng dồn lên cấp cao hơn".
  - Chuẩn hóa dữ liệu Kế hoạch PHBC: Đồng bộ 18 mã cụm đại diện (ví dụ `CUM_ANHSON`) vào bảng `dim_buucuc` và cập nhật dữ liệu `plans` PHBC khớp 100% với file Excel `KH-PHBC-2026.xlsx` (tổng 8,98 tỷ đồng).
  - Code được thực thi và commit trên nhánh `fix-top10-plan-xa`.
- **Chuẩn hóa & Tái cấu trúc Mẫu File Import (07/06/2026)**:
  - Hợp nhất và tinh giản các cột nhập liệu giúp giảm sai sót khi chuẩn bị file Excel nạp hệ thống.
  - **Mẫu doanh thu BCCP (`mau_import_doanh_thu_BCCP.xlsx`)**: Rút gọn từ 22 cột thừa xuống **12 cột cốt lõi**. Bộ phân tích dữ liệu (`importer.py`) đã được viết lại để tự động nhận diện và hỗ trợ song song cả chuẩn cũ (22 cột) và chuẩn mới (12 cột).
  - **Mẫu kế hoạch (`mau_import_ke_hoach.xlsx`)**: Hỗ trợ nạp chỉ tiêu kế hoạch đồng thời cho cả 3 cấp (Bưu cục, Xã, Cụm).
  - **Mẫu dịch vụ khác (`mau_import_dich_vu_khac.xlsx`)**: Hỗ trợ nạp doanh thu theo tuần hoặc tháng đối với các dịch vụ không phát sinh dữ liệu theo ngày.
  - **Mẫu danh mục dịch vụ (`mau_import_danh_muc_dich_vu.xlsx`)**: Sếp điền thông tin nhóm và sản phẩm, lưu dưới dạng tệp `.csv` (đặt tên là `mapping_spdv.csv`) rồi đưa vào hệ thống để tự động cập nhật danh mục.
- **Tối ưu hóa Phân loại "Chuyển phát HCC" (07/06/2026)**:
  - Khắc phục lỗi phân loại nhầm: Các mã sản phẩm hành chính công `HCC001` - `HCC004` (chuyển phát CCCD, hộ chiếu...) trước đây bị gộp chung vào nhóm BCCP. 
  - Đã điều chỉnh trong file `mapping-spdv.csv` và logic ETL (`sync_mappings.py`, `migrate_dim_dichvu.py`) để chuyển toàn bộ doanh thu này sang đúng phân hệ **Hành chính công (HCC)**.
- **Khắc phục Lỗi Hồi quy Bộ lọc & Cache (07/06/2026)**:
  - Lỗi xảy ra khi Sếp chuyển bộ lọc so sánh ở Sidebar từ dạng chọn một (Radio) sang chọn nhiều (Checklist). Callback trả về một danh sách (list), dẫn đến lỗi `TypeError: unhashable type: 'list'` khi lưu trữ vào bộ nhớ đệm cache (`@functools.lru_cache`).
  - Đã sửa triệt để tại `utils.py` và `kpi_callbacks.py` bằng cách tự động chuẩn hóa danh sách bộ lọc so sánh thành chuỗi văn bản đơn giản trước khi lưu vào cache hoặc SQLite.
- **Tối ưu hiệu năng bằng Summary Tables (07/06/2026)**:
  - Xây dựng các bảng tổng hợp trung gian: `agg_monthly`, `agg_monthly_customer`, `plans_weekly`, `new_customers` (tối ưu hóa logic khách hàng mới, chỉ tính doanh thu dương).
  - Các trang Tổng quan, BCCP, Khách hàng... đã chuyển sang đọc từ các bảng này, cải thiện hiệu suất tải trang gấp nhiều lần. Tự động cập nhật summary khi có thay đổi dữ liệu từ file Excel.
- **Điều chỉnh Doanh thu tháng 10/2025 (07/06/2026)**:
  - Chuyển giao dịch điều chỉnh âm -7,42 tỷ của khách hàng `C002362753` từ `01/10/2025` về `30/09/2025` để đối trừ với giao dịch dương cùng kỳ, giúp phục hồi doanh thu thực tế chính xác. Rebuild thành công toàn bộ summary tables.
- **Nạp dữ liệu Tháng 04/2025 (08/06/2026)**:
  - Đã import thành công **70.543 dòng** dữ liệu thô (RAW từ CAS) của tháng 04/2025 từ 5 tệp Excel nguồn vào cơ sở dữ liệu.
  - Đã hoàn thành tiến trình cập nhật và làm mới lại toàn bộ các bảng số liệu tổng hợp (rebuild summaries) để đồng bộ Dashboard.
- **Hoàn thành & Hủy bỏ (Rollback) nhánh `feat-ux-filters` (06/06/2026 - 07/06/2026)**:
  - Nhánh đã được nghiệm thu và gộp thành công vào `main`, nhưng sau đó theo yêu cầu của Sếp, hệ thống đã thực hiện **rollback hoàn toàn** bản cập nhật này. Giao diện và logic code của `main` hiện tại quay về trạng thái ổn định của **Phase 11**.
- **Sửa lỗi mã hóa tập tin thực thi Batch `.bat` (07/06/2026)**:
  - Khắc phục lỗi Command Prompt do tệp `bat_duong_ham.bat` và `dung_duong_ham.bat` bị mã hóa UTF-16, chuyển sang chuẩn UTF-8/ASCII để chạy ổn định khi phân quyền UAC.
- **Sửa lỗi Import CSV Mapping (04/06/2026)**:
  - Khắc phục lỗi `❌ Tệp CSV thiếu cột bắt buộc 'nhom_chinh'` bằng cách hỗ trợ cả dấu phân tách `;` và `,`. Tự động gộp (merge) danh mục cũ và danh mục mới.
- **Đường dẫn Workspace hoạt động**:
  - Mã nguồn: `E:\Projects\Dashboard-BCCP`
  - Cơ sở dữ liệu: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- **Cloudflare Tunnel (Truy cập từ xa)**:
  - Tên miền: `dashboard.bdna.io.vn` trỏ về `http://127.0.0.1:8050`.
  - Trạng thái: Dịch vụ Windows Service `cloudflared` đang được điều phối chạy qua script nâng quyền UAC của Sếp.

## Key Decisions & Architecture
- **Mã nguồn tách biệt khỏi OneDrive**: Tránh xung đột đồng bộ OneDrive khi chạy cơ sở dữ liệu và code. Code chính nằm tại `E:\Projects\Dashboard-BCCP`.
- **Cơ chế Summary Tables**: Để tối ưu hiệu năng cho tập dữ liệu lớn (~1 triệu dòng), các trang số liệu đọc từ các bảng tổng hợp trước thay vì quét toàn bộ bảng transactions.
- **Nguyên tắc "Nạp cấp nào, so sánh cấp đó" (3 cấp kế hoạch)**:
  - **BCCP (Truyền thống/TMĐT/QT)**: Nạp ở cấp Bưu cục (mã 6 số). Khi xem ở cấp Xã -> Tự động JOIN dim_buucuc và SUM gộp lên.
  - **HCC (Chuyển phát HCC)**: Nạp ở cấp Xã (mã 4 số). Lấy trực tiếp khi xem ở cấp Xã.
  - **PHBC (Phát hành báo chí)**: Nạp ở cấp Cụm (mã `CUM_XXXX`). Lấy trực tiếp khi xem ở cấp Cụm.
- **Bảng Tra Cứu Mã Đại Diện 18 Cụm**:
  Khi nạp dữ liệu ở cấp Cụm (Ví dụ: kế hoạch hoặc doanh thu đặc thù Phát hành báo chí), cần sử dụng các mã đại diện cụm dưới đây điền vào cột **Mã bưu cục** để hệ thống tự động so sánh và cộng dồn:
  
  | STT | Tên Cụm | Mã Cụm đại diện (Điền vào cột Mã bưu cục) | Tên Bưu cục hiển thị |
  | :---: | :--- | :---: | :--- |
  | **1** | Anh Sơn | `CUM_ANHSON` | Đại diện Cụm Anh Sơn |
  | **2** | Con Cuông | `CUM_CONCUONG` | Đại diện Cụm Con Cuông |
  | **3** | Diễn Châu | `CUM_DIENCHAU` | Đại diện Cụm Diễn Châu |
  | **4** | Đô Lương | `CUM_DOLUONG` | Đại diện Cụm Đô Lương |
  | **5** | Hưng Nguyên | `CUM_HUNGNGUYEN` | Đại diện Cụm Hưng Nguyên |
  | **6** | Kỳ Sơn | `CUM_KYSON` | Đại diện Cụm Kỳ Sơn |
  | **7** | Nam Đàn | `CUM_NAMDAN` | Đại diện Cụm Nam Đàn |
  | **8** | Nghi Lộc | `CUM_NGHILOC` | Đại diện Cụm Nghi Lộc |
  | **9** | Quế Phong | `CUM_QUEPHONG` | Đại diện Cụm Quế Phong |
  | **10** | Quỳ Châu | `CUM_QUYCHAU` | Đại diện Cụm Quỳ Châu |
  | **11** | Quỳ Hợp | `CUM_QUYHOP` | Đại diện Cụm Quỳ Hợp |
  | **12** | Quỳnh Lưu | `CUM_QUYNHLUU` | Đại diện Cụm Quỳnh Lưu |
  | **13** | Tân Kỳ | `CUM_TANKY` | Đại diện Cụm Tân Kỳ |
  | **14** | Thái Hòa | `CUM_THAIHOA` | Đại diện Cụm Thái Hòa |
  | **15** | Thanh Chương | `CUM_THANHCHUONG` | Đại diện Cụm Thanh Chương |
  | **16** | Tương Dương | `CUM_TUONGDUONG` | Đại diện Cụm Tương Dương |
  | **17** | Vinh | `CUM_VINH` | Đại diện Cụm Vinh |
  | **18** | Yên Thành | `CUM_YENTHANH` | Đại diện Cụm Yên Thành |

- **Logic Chia Đều Số Liệu Ngày (Back-distribution)**:
  Khi import các file dữ liệu có định kỳ lớn (Ví dụ: Doanh thu dịch vụ khác theo tuần hoặc theo tháng từ file `mau_import_dich_vu_khac.xlsx`), hệ thống tự động xác định khoảng thời gian và thực hiện chia đều doanh thu đó ra các ngày trong tuần/tháng để tính toán doanh thu trung bình ngày ổn định.
- **Phân bổ Dữ liệu Tuần (Đối với HCC/TCBC/PPBL)**:
  Do các bảng dữ liệu gốc của 3 dịch vụ phụ (Hành chính công, Tài chính bưu chính, Phân phối bán lẻ) chỉ lưu trữ số liệu thực tế theo **Tháng**, nên khi Sếp xem báo cáo theo **Tuần**, hệ thống sẽ tự động phân bổ doanh thu thực tế của Tháng vào các Tuần trong tháng đó theo tỷ lệ số ngày lịch (tương tự như cách phân bổ kế hoạch tuần). Logic này sẽ được điều chỉnh khi có dữ liệu thực tế theo ngày.
- **Logic Xếp hạng Top 10 Bưu điện Xã/Phường**:
  Để tránh hiện tượng xếp hạng lặp lại cùng một xã nhiều lần do một bưu điện xã có nhiều mã bưu cục con, hệ thống thực hiện **cộng dồn doanh thu của tất cả các bưu cục trực thuộc cùng một Xã/Phường** trước khi so sánh xếp hạng. Mỗi xã/phường chỉ xuất hiện tối đa một lần trong danh sách xếp hạng.
- **Đồng bộ trạng thái Bộ lọc Toàn cục**:
  Bộ lọc trên Topbar (Năm, Tháng, Tuần, Địa lý) được đồng bộ trạng thái khi chuyển đổi giữa tất cả các trang, thay vì reset về mặc định khi đổi trang. Dữ liệu trang mới chỉ thực sự tải lại theo các bộ lọc này khi Sếp nhấn nút **"Áp dụng"** (Manual Load).
- **Phân tách Tài liệu Bàn giao**: 
  - `GEMINI.md` đóng vai trò là tài liệu tóm tắt ngắn gọn nhất để Agent/Nhân sự mới nắm bắt nhanh.
  - `project_state.md` lưu trữ chi tiết kỹ thuật chuyên sâu và lịch sử phát triển.

### Cấu trúc thư mục hiện tại:
```
E:\Projects\Dashboard-BCCP\
├── config/         (settings.py, holidays.py, week_calendar.py)
├── data/           (mapping_spdv.csv, mapping-BC-BDX-Cum.csv, ke-hoach-2026/, mau-file-import/)
├── database/       (dashboard.db)
├── etl/            (importer.py, aggregator.py)
├── analytics/      (revenue.py, customer_classifier.py, global_metrics.py)
├── scripts/        (generate_tokens.py, rebuild_summaries.py, sync_mappings.py)
├── dash_app/       ← APP CHÍNH
│   ├── app.py
│   ├── assets/style.css
│   ├── components/
│   ├── callbacks/
│   ├── pages/
│   ├── db/
│   └── requirements.txt
├── run_dashboard.bat
├── bat_duong_ham.bat
├── dung_duong_ham.bat
└── project_state.md
```

### Database Schema:
- `transactions`, `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl` — Dữ liệu giao dịch chi tiết các dịch vụ.
- `agg_monthly`, `agg_monthly_customer`, `agg_weekly` — Bảng tổng hợp doanh thu, sản lượng, số KH phát sinh theo tháng/tuần.
- `plans`, `plans_weekly` — Kế hoạch tháng/tuần theo mã bưu cục (BCCP), mã xã (HCC) và mã cụm (PHBC).
- `new_customers` — Khách hàng mới theo tháng, ghi nhận `ngay_phat_sinh` (chỉ với giao dịch có doanh thu dương).
- `dim_spdv` / `dim_dichvu` — Ánh xạ mã SPDV → nhóm dịch vụ.
- `dim_buucuc` — Ánh xạ mã bưu cục → ten_bdx (xã), ten_cum (18 Cụm `CUM_XXXX`).
- `import_log` — Lịch sử import.

### Logic phân loại KH (theo tháng, không cộng dồn):
- **Khách hàng Mới (KHM)** (Bảng `new_customers`):
  - **Định nghĩa**: Khách hàng phát sinh giao dịch có doanh thu dương (`cuoc_tt_tong > 0`) trong tháng target nhưng **không phát sinh bất kỳ giao dịch doanh thu dương nào trong 3 tháng liền trước đó** (không tính mã vãng lai `VANGLAI_%` hoặc null/none).
  - **Thông tin lưu trữ**: Bưu cục hoạt động nhiều nhất (nếu bằng thì lấy tổng doanh thu cao nhất), mã xã `ma_bdx`, tên cụm `ten_cum`, nhóm dịch vụ phát sinh đầu tiên (`nhom_dv`), tổng doanh thu trong tháng target (`tong_doanh_thu`), và ngày giao dịch đầu tiên có doanh thu dương (`ngay_phat_sinh`).
- **Khách hàng Hiện hữu (KHHH)** (Phân hệ Retention):
  - **Định nghĩa Mới (Đã áp dụng)**: **`Khách hàng hiện hữu = Khách hàng có phát sinh giao dịch trong tháng target - Khách hàng mới của tháng target`**.
  - **Lưu ý**: Công thức tối ưu mới này thay thế cho logic quét 3 tháng Lookback lịch sử cũ để khắc phục triệt để lỗi sập trang và cải thiện 100% hiệu năng tải trang `/bccp/retention`.
- **Khách hàng Tái bán (KHM/Tái bán)** (Bảng Doanh thu chi tiết / `customer_classifier.py`):
  - **Định nghĩa**: Khách hàng phi vãng lai **không hoạt động trong 3 tháng liền trước** (có thể là KHM mới tinh hoặc KH cũ quay lại sau 3 tháng gián đoạn).
- **Vãng lai**:
  - **Định nghĩa**: Các giao dịch có mã CMS là null, rỗng, bắt đầu bằng `VANGLAI_` hoặc `none`.

## Pending Tasks
1. **[COMPLETED] Cập nhật Main Branch**: Đã merge nhánh `fix-top10-plan-xa` vào `main`.
2. **[COMPLETED] Bổ sung dữ liệu**: Đã nạp thêm dữ liệu 2 ngày cuối tháng 5 (30.05 - 31.05) và dữ liệu tháng 6.
3. **[COMPLETED] Mẫu File Import**: Thiết kế lại toàn bộ 3 file mẫu import (Doanh thu, Kế hoạch 3 cấp, Dịch vụ khác) theo chuẩn mới 11/12 cột cốt lõi, xóa cột thừa, thêm sheet hướng dẫn chi tiết và thêm vào Git tracking.
4. **[COMPLETED] Dọn dẹp Dữ liệu**: Đã xóa hoặc lưu trữ các file backup `.csv` cũ trong thư mục `data`.
5. **[PENDING] Phase 5C**: Thiết lập deploy server nội bộ và chuyển sang PostgreSQL.
6. **[PENDING] Option B (Tái cấu trúc Database)**: Chuẩn hóa bảng `dim_dichvu` (thêm `ma_nhom_chinh`, `ma_nhom_dich_vu` thay vì dùng chuỗi tên nhóm). Hạng mục này đã được hoãn lại, chuyển vào danh sách nâng cấp sau (Backlog) khi hệ thống thực sự cần.

## Issues & Notes
- **Lưu ý Mã Đại diện Cụm (PHBC)**: Khi nạp dữ liệu Kế hoạch hoặc Doanh thu đặc thù cấp Cụm, bắt buộc phải dùng danh sách 18 mã đại diện như `CUM_ANHSON`, `CUM_VINH` điền vào cột "Mã bưu cục".
- **Hệ thống Bộ lọc Topbar mới (Thay thế bộ lọc Ngày/DatePicker cũ)**:
  - Lược bỏ hoàn toàn bộ lọc khoảng ngày tùy chọn (`DatePickerRange`) cũ để tránh lỗi hiệu năng và xung đột dữ liệu.
  - Hệ thống chuyển hoàn toàn sang sử dụng bộ lọc chu kỳ đặt trên Topbar toàn cục bao gồm: **Năm**, **Chu kỳ** (Tháng/Tuần), **Chọn Tháng** (dropdown từ Tháng 01 - 12) và **Chọn Tuần** (dropdown tự động cascade theo năm được chọn).
  - Đối với các trang như Khách hàng mới (`/bccp/new-customer`) và Khách hàng hiện hữu (`/bccp/retention`), các callback lấy trực tiếp giá trị Tháng/Tuần và Năm được chọn từ Topbar để tính toán, không còn sử dụng cơ chế khóa khoảng ngày nữa.
- **Biểu đồ biến động 12 kỳ (Line Chart 12 kỳ)**:
  - Chuyển từ dạng biểu đồ Bar chồng (Stack Bar) sang **biểu đồ đường (Line Chart) 5 đường** (đường nét liền Tổng doanh thu + 4 đường nét đứt biểu diễn các phân hệ dịch vụ BCCP, HCC, TCBC, PPBL) tại trang Tổng quan giúp trực quan hóa xu hướng rõ ràng hơn.
- **Tính năng Native Filter**: Bật native filtering và sorting (`filter_action='native'`, `sort_action='native'`) cho tất cả các bảng dữ liệu (DataTable) giúp Sếp lọc trực tiếp trên giao diện Dashboard.
- **Regression Bugs đã xử lý (BUG-01..05)**:
  - **Lọc vãng lai trong Retention**: Sửa lỗi lọc vãng lai trong các hàm `get_khhh_changes_v2` và `get_weekly_changes` ở `retention_metrics.py` (loại bỏ CMS vãng lai, CMS null, CMS rỗng hoặc 'none').
  - **Lỗi SQL Ambiguous Column**: Sửa lỗi SQL ambiguous column (ví dụ: `buu_cuc` hoặc `nhom_chinh` bị nhập nhằng khi JOIN) bằng cách sử dụng `COALESCE(d.nhom_chinh, 'Khác')` và chỉ định tường minh tên bảng trong câu lệnh SELECT.
- **RBAC & Authentication**: Phân quyền người dùng theo Cụm địa lý, khóa cứng bộ lọc Cụm đối với tài khoản cấp Cụm (user). Hỗ trợ route test nhanh `/test-login/<username>`. Bypass hiện tại ở `app.py`.
- **Database Lock**: Do SQLite sử dụng khóa độc quyền, quá trình chạy script `rebuild_summaries.py` sẽ tạm khóa tất cả các truy cập đọc/ghi khác.
- **Lỗi không hiển thị Alert khi nạp thành công**: Đã sửa triệt để đổi `dismissible` thành `dismissable` trong DBC Alert.
- **Lỗi CSV dấu phân tách ';'**: Đã khắc phục triệt để.

### 📚 Kinh Nghiệm Vận Hành & Các Lỗi Thường Gặp:
1. **Lỗi nạp lại Code (`File is not a zip file` khi nạp `.xls`)**:
   - **Vấn đề**: Khi sửa đổi mã nguồn hoặc cập nhật thư viện (như hỗ trợ mở rộng định dạng file `.xls`), giao diện có thể vẫn báo lỗi cũ do ứng dụng Dash đang chạy trong bộ nhớ RAM chưa nạp lại code mới.
   - **Khắc phục**: **Bắt buộc phải khởi động lại Dashboard** (tắt cửa sổ Terminal/Command Prompt chạy app và chạy lại file `run_dashboard.bat`).
2. **Quy trình lưu và nạp file Danh mục Dịch vụ (CSV Mapping)**:
   - **Vấn đề**: File mẫu Excel trên OneDrive được chia làm **2 Sheet** (Sheet 1: Hướng dẫn, Sheet 2: Mẫu nạp). Nếu lưu trực tiếp mà không chọn sheet, Pandas sẽ đọc nhầm tiêu đề lớn của Sheet 1 làm tên cột và báo lỗi `Thiếu cột nhom_chinh`.
   - **Khắc phục**: Sếp cần mở file Excel mẫu, click chọn đúng **Sheet 2** (`Mẫu Danh Mục Dịch Vụ`), sau đó thực hiện File -> Save As -> Định dạng **CSV UTF-8 (Comma delimited) (.csv)** trước khi nạp vào Dashboard.
3. **Logic gộp mã CMS dòng nhóm (ETL thô)**:
   - **Vấn đề**: Khi nạp dữ liệu thô, logic import cũ gán nhầm mã CMS của khách hàng dòng trên cho các dòng nhóm phụ không có mã CMS (ví dụ nhóm `1.313`).
   - **Khắc phục**: Đã bổ sung logic reset cache mã CMS khi đọc qua các dòng nhóm phân cấp của tệp Excel nguồn.
4. **Lỗi Số thứ tự (STT) hiển thị sai lệch trong bảng xếp hạng**:
   - **Vấn đề**: Bảng Top 10 hiển thị số thứ tự STT lộn xộn (như 189, 311) do Dash DataTable lấy trực tiếp cột chỉ mục (index) gốc của Pandas DataFrame sau khi lọc.
   - **Khắc phục**: Sử dụng `df.reset_index(drop=True)` để reset chỉ mục và thiết lập hiển thị STT từ 1-10 tăng dần trên giao diện.
5. **Thiết kế trang Khách hàng Chi tiết (CMS Detail)**:
   - Thay đổi từ giao diện xoay chiều (Pivot Table) có hiệu năng kém ở bản cũ sang **bảng phẳng (Flat Table) với các cột dữ liệu cố định** tại Phase 11 để tăng tốc độ phản hồi và xuất dữ liệu.
