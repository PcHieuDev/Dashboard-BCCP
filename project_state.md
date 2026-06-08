# Project State - Dashboard Doanh thu BCCP

## Project Goal
Dashboard doanh thu bưu chính chuyển phát (BCCP) hỗ trợ bộ lọc đa chiều, phân loại khách hàng tự động, import dữ liệu từ Excel vào SQLite. Phục vụ **20+ người dùng** từ nhiều phòng ban, dự kiến deploy lên **server nội bộ**.

## Tech Stack
- **Language**: Python 3.13
- **Framework**: **Dash** (đã chuyển đổi hoàn toàn từ Streamlit)
- **Database**: SQLite (đang lưu trữ đồng bộ trên OneDrive) -> PostgreSQL khi deploy server
- **Dependencies**: pandas, dash, dash-bootstrap-components, plotly, openpyxl, xlrd>=2.0.1 (đọc file .xls)
- **Encoding**: UTF-8 toàn bộ

## Current State
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
