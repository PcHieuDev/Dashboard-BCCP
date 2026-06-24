# TÀI LIỆU BÀN GIAO KỸ THUẬT & TRIỂN KHAI CHUYÊN SÂU
## HỆ THỐNG DASHBOARD DOANH THU BƯU CHÍNH CHUYỂN PHÁT (BCCP)

Tài liệu này được biên soạn theo tiêu chuẩn bàn giao công nghệ chuyên nghiệp nhằm giúp đội ngũ IT tiếp quản, vận hành, cấu hình sản xuất (production) và phát triển tiếp hệ thống Dashboard Doanh thu BCCP mà không gặp trở ngại.

---

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)
*   **Mục tiêu**: Giám sát doanh thu, sản lượng, khách hàng mới và tỷ lệ hoàn thành kế hoạch 3 cấp (Bưu cục, Xã, Cụm) của dịch vụ Bưu chính chuyển phát (BCCP) và các dịch vụ phụ (Hành chính công - HCC, Tài chính bưu chính - TCBC, Phân phối bán lẻ - PPBL, Phát hành báo chí - PHBC).
*   **Kiến trúc**: Ứng dụng Web Single-Page Application (SPA) xây dựng trên nền tảng **Python Dash** (kết hợp Flask làm WSGI backend, Plotly vẽ biểu đồ, Dash Bootstrap Components làm UI).
*   **Cơ sở dữ liệu**: SQLite 3 (Tệp tin chính: `dashboard.db`, dung lượng hiện tại ~648 MB).
*   **Đường hầm truy cập**: Sử dụng **Cloudflare Tunnel** (`dashboard.bdna.io.vn`) kết nối trực tiếp với local port `8050` mà không cần mở port modem hoặc cấu hình IP tĩnh.

---

## 2. KIẾN TRÚC & LUỒNG DỮ LIỆU (ARCHITECTURE & DATA FLOW)

### 2.1. Sơ đồ Luồng Dữ liệu (Data Flow Diagram)
```
             [Excel Files] (Doanh thu BCCP, Dịch vụ khác, Kế hoạch)
                   │
                   ▼ (Nạp qua Giao diện Web hoặc chạy script CLI)
           ┌───────────────┐
           │  etl/importer │ (Đọc dữ liệu thô, chuẩn hóa cột, phân rã ngày)
           └───────┬───────┘
                   │
                   ▼ (Ghi dữ liệu thô: transactions, transactions_hcc...)
       ┌──────────────────────┐
       │ SQLite (dashboard.db)│ <─── [scripts/sync_mappings.py] (Cập nhật danh mục)
       └───────┬──────────────┘
                   │
                   ▼ (Chạy scripts/rebuild_summaries.py)
       ┌──────────────────────┐
       │    Summary Tables    │ (agg_weekly, agg_monthly, new_customers)
       └───────┬──────────────┘
                   │
                   ▼ (analytics/global_metrics.py - Truy vấn dữ liệu đã gộp)
           ┌───────────────┐
           │   Dash App    │ (Web app chạy trên Flask + Plotly, Port 8050)
           └───────┬───────┘
                   │
                   ▼ (Áp dụng bộ lọc và kết xuất biểu đồ/bảng số liệu)
             [Web Browser] <─── [Cloudflare Tunnel] <─── (Người dùng từ xa)
```

### 2.2. Kiến trúc Phân lớp Thư mục
```
E:\Projects\Dashboard-BCCP\
├── config/                 # Cấu hình tham số hệ thống
│   ├── settings.py         # Khởi tạo đường dẫn DB, backup và cấu hình chung
│   ├── holidays.py         # Danh sách ngày lễ Việt Nam để tính ngày làm việc
│   └── week_calendar.py    # Định nghĩa lịch tuần và logic đồng bộ mốc YoY
├── data/                   # Dữ liệu và các file mẫu import
│   ├── mau-file-import/    # Thư mục chứa 3 file mẫu Excel thông minh (đã kéo Conditional Formatting & sheet Ref)
│   ├── mapping_spdv.csv    # File ánh xạ mã sản phẩm/dịch vụ -> Nhóm chính
│   └── mapping-BC-BDX-Cum.csv # File ánh xạ mã Bưu cục -> Xã/Phường -> Cụm địa lý
├── etl/                    # Các module xử lý ETL dữ liệu thô
│   ├── importer.py         # Engine đọc và import Excel thô (BCCP, dịch vụ phụ, kế hoạch)
│   └── aggregator.py       # Engine gộp số liệu thô lên các bảng summary (weekly/monthly)
├── analytics/              # Logic tính toán nghiệp vụ
│   ├── global_metrics.py   # Tính toán số liệu tổng hợp YTD, KPI, Top 10, biểu đồ 12 kỳ
│   ├── revenue.py          # Logic chi tiết doanh thu
│   └── customer_classifier.py # Phân loại Khách hàng (Mới, Hiện hữu, Tái bán)
├── scripts/                # Các công cụ dòng lệnh (CLI scripts)
│   ├── rebuild_summaries.py # Chạy lại toàn bộ gộp số liệu SQLite (UPSERT)
│   ├── sync_excel_templates.py # Tự động nhúng danh mục DB vào sheet Ref của file Excel mẫu
│   └── sync_mappings.py    # Đồng bộ file ánh xạ danh mục vào DB
├── dash_app/               # MÃ NGUỒN APP DASHBOARD
│   ├── app.py              # File khởi chạy chính (Entrypoint)
│   ├── assets/             # File CSS giao diện (style.css)
│   ├── components/         # Các khối UI tái sử dụng (Sidebar, Topbar, KPI Cards)
│   ├── callbacks/          # Xử lý sự kiện (global_callbacks, service_callbacks)
│   └── pages/              # Giao diện các trang (global_overview, service_overview, customer)
├── run_dashboard.bat       # Script khởi động nhanh Dashboard (tự động kill port 8050 bị treo)
├── requirements.txt        # Danh sách thư viện Python cần cài đặt
└── project_state.md        # Nhật ký phát triển và ghi chú logic nghiệp vụ chi tiết
```

---

## 3. CƠ SỞ DỮ LIỆU & SCHEMA (DATABASE & SCHEMA)

Hệ thống sử dụng SQLite. Để tối ưu hiệu năng cho tập dữ liệu thô lớn (~1 triệu dòng), các trang Dashboard chỉ đọc từ các bảng tổng hợp sẵn (Summary Tables) thay vì quét bảng giao dịch chi tiết.

### 3.1. Sơ đồ các bảng dữ liệu chính
```
    ┌────────────────┐         ┌───────────────────┐
    │   dim_buucuc   │         │    dim_dichvu     │
    ├────────────────┤         ├───────────────────┤
    │ ma_buucuc (PK) ◄───┐     │ ma_dichvu (PK)    ◄──┐
    │ ten_bdx        │   │     │ ten_dichvu        │  │
    │ ma_bdx         │   │     │ nhom_dichvu       │  │
    │ ten_cum        │   │     │ nhom_chinh        │  │
    └────────────────┘   │     └───────────────────┘  │
                         │                            │
    ┌────────────────┐   │     ┌───────────────────┐  │
    │  transactions  │   │     │ transactions_hcc  │  │
    ├────────────────┤   │     ├───────────────────┤  │
    │ stt            │   │     │ stt               │  │
    │ ngay           │   │     │ ngay              │  │
    │ ma_buucuc (FK) ├───┘     │ ma_buucuc (FK)    ├──┘
    │ ma_san_pham(FK)├─────────┼──►ma_dich_vu (FK) │
    │ cuoc_tt_tong   │         │ doanh_thu         │
    │ ...            │         │ ...               │
    └────────────────┘         └───────────────────┘
```

### 3.2. Mô tả Chi tiết các Bảng
1.  **Bảng Dữ liệu Thô**:
    *   `transactions`: Chứa dữ liệu doanh thu chi tiết BCCP (theo ngày).
    *   `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl`, `transactions_phbc`: Chứa dữ liệu các dịch vụ phụ (đã được phân rã chia đều về ngày từ số liệu tuần/tháng).
2.  **Bảng Tổng Hợp (Summary Tables)**:
    *   `agg_monthly`: Doanh thu, sản lượng gộp theo tháng (phục vụ biểu đồ xu hướng, KPI tháng).
    *   `agg_weekly`: Doanh thu, sản lượng gộp theo tuần (phục vụ báo cáo tuần).
    *   `new_customers`: Danh sách khách hàng mới phát sinh theo tháng (logic: phát sinh doanh thu dương trong tháng target nhưng không có doanh thu dương nào trong 3 tháng liền trước).
3.  **Bảng Danh Mục (Dim Tables)**:
    *   `dim_buucuc`: Danh sách bưu cục, liên kết mã bưu cục (6 số) -> Bưu điện xã (ma_bdx 4 số) -> Cụm địa lý (18 cụm đại diện).
    *   `dim_dichvu` / `dim_spdv`: Ánh xạ mã sản phẩm/dịch vụ -> Tên dịch vụ -> Phân hệ Nhóm chính.
4.  **Bảng Kế Hoạch**:
    *   `plans`, `plans_weekly`: Chỉ tiêu kế hoạch tháng và tuần của các dịch vụ.
5.  **Bảng Nhật Ký**:
    *   `import_log`: Ghi nhận lịch sử nạp file Excel (Tên file, thời gian nạp, số dòng, trạng thái).

---

## 4. ROUTING & CẤU HÌNH THAM SỐ (ROUTING & CONFIGURATION)

### 4.1. Các Trang Giao diện chính (Web Routes)
Ứng dụng Dash sử dụng cấu trúc đa trang (Multipage) định tuyến dựa trên URL:
*   `/` hoặc `/global-overview`: Tổng quan doanh thu toàn tỉnh (KPIs, Biểu đồ 12 kỳ, Top bưu cục).
*   `/bccp`: Báo cáo chuyên sâu dịch vụ chính Bưu chính chuyển phát (Doanh thu, kế hoạch, Top 10).
*   `/hcc`: Báo cáo chuyên sâu dịch vụ Hành chính công.
*   `/tcbc`: Báo cáo chuyên sâu dịch vụ Tài chính bưu chính.
*   `/ppbl`: Báo cáo chuyên sâu dịch vụ Phân phối bán lẻ.
*   `/customer`: Trang phân tích khách hàng mới (New Customer), khách hàng hiện hữu (Retention) và tra cứu chi tiết khách hàng (Flat Table).
*   `/import`: Trang nạp các tệp tin Excel doanh thu thô và kế hoạch.

### 4.2. Cấu hình tham số hệ thống
*   **`config/settings.py`**:
    *   `DB_PATH`: Đường dẫn tuyệt đối đến file SQLite `dashboard.db`.
    *   `BACKUP_DIR`: Thư mục lưu trữ bản sao lưu của Database trước khi ghi đè dữ liệu mới.
*   **`dash_app/app.py`**:
    *   Cấu hình cổng khởi chạy `port=8050` và chế độ `debug=False` khi chạy chính thức.

---

## 5. HƯỚNG DẪN CÀI ĐẶT & TRIỂN KHAI NHANH (QUICK START)

### Môi trường khuyến nghị: Python 3.13 (hoặc 3.11+)

1.  **Cài đặt Thư viện**:
    Kích hoạt môi trường ảo (virtual environment) và cài đặt dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Khởi động Development Server**:
    Chạy file batch tại thư mục gốc:
    ```bash
    run_dashboard.bat
    ```
    Ứng dụng sẽ hoạt động tại địa chỉ: `http://127.0.0.1:8050`

---

## 6. HƯỚNG DẪN TRIỂN KHAI PRODUCTION (PRODUCTION DEPLOYMENT)

Không sử dụng server debug của Flask (`app.run_server(debug=True)`) khi triển khai thực tế. IT cần cấu hình WSGI HTTP Server.

### Cách 1: Triển khai trên máy chủ Windows (Sử dụng Waitress)
Waitress là một WSGI server thuần Python hiệu năng cao, hoạt động ổn định trên nền tảng Windows.
1.  Cài đặt `waitress`:
    ```bash
    pip install waitress
    ```
2.  Tạo file khởi chạy `wsgi.py` ở thư mục gốc:
    ```python
    from waitress import serve
    from dash_app.app import app
    
    if __name__ == '__main__':
        print("Starting production server on http://0.0.0.0:8050...")
        serve(app.server, host='0.0.0.0', port=8050, threads=8)
    ```
3.  Cấu hình chạy như một Windows Service thông qua công cụ NSSM (Non-Sucking Service Manager) để tự động khởi động cùng hệ thống.

### Cách 2: Triển khai trên máy chủ Linux/Docker (Sử dụng Gunicorn)
1.  Cài đặt `gunicorn`:
    ```bash
    pip install gunicorn
    ```
2.  Khởi chạy bằng lệnh:
    ```bash
    gunicorn dash_app.app:app.server -b 0.0.0.0:8050 --workers 4 --threads 2
    ```

---

## 7. QUY TRÌNH VẬN HÀNH & CÁC TÁC VỤ THƯỜNG GẶP (COMMON TASKS)

### 7.1. Cập nhật danh mục mới vào 3 file mẫu Excel
Khi có bưu cục mới hoặc sản phẩm mới, IT cần nạp vào DB trước, sau đó chạy script dưới đây để cập nhật tự động sheet `Ref` trong các file mẫu Excel để người dùng không nhập sai mã:
```bash
python scripts/sync_excel_templates.py
```

### 7.2. Chạy tính toán lại số liệu thủ công qua dòng lệnh (CLI)
Khi người dùng import file dữ liệu lớn qua web hoặc IT import trực tiếp qua terminal, cần chạy script sau để cập nhật lại các bảng tổng hợp:
```bash
python scripts/rebuild_summaries.py
```
*Lưu ý: Script này sử dụng SQLite UPSERT `ON CONFLICT DO UPDATE` để tự động cộng dồn/triệt tiêu sai số giữa các lần import ghi đè.*

---

## 8. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

*   **Sự cố 1: Lỗi `sqlite3.OperationalError: database is locked`**
    *   *Nguyên nhân:* SQLite khóa độc quyền (Exclusive Lock) khi ghi dữ liệu. Lỗi xảy ra nếu người dùng import file Excel quá lớn hoặc chạy rebuild summaries trong khi có nhiều người đang đọc dữ liệu trên Dashboard.
    *   *Khắc phục:* Khởi động lại ứng dụng. Giải pháp lâu dài là chuyển đổi sang PostgreSQL/SQL Server.
*   **Sự cố 2: Cổng `8050` bị treo khi khởi động lại**
    *   *Nguyên nhân:* Tiến trình Python cũ chưa giải phóng cổng mạng.
    *   *Khắc phục:* Sử dụng script `run_dashboard.bat` (đã tích hợp lệnh `taskkill` giải phóng port tự động) hoặc chạy thủ công trong CMD/Powershell:
        ```cmd
        taskkill /f /im python.exe
        ```
*   **Sự cố 3: Lỗi `UnicodeEncodeError` khi chạy CLI trên Terminal Windows**
    *   *Nguyên nhân:* Bảng mã terminal mặc định của Windows không phải UTF-8.
    *   *Khắc phục:* Chạy lệnh sau để chuyển bảng mã console sang UTF-8 trước khi thực thi script Python:
        ```cmd
        chcp 65001
        ```
*   **Sự cố 4: Lỗi `File is not a zip file` khi đọc tệp Excel `.xls`**
    *   *Nguyên nhân:* Tệp tin bị hỏng trong quá trình truyền tải hoặc không đúng định dạng.
    *   *Khắc phục:* Tải lại tệp dữ liệu sạch từ CAS và đảm bảo cài đặt thư viện `xlrd>=2.0.1` để xử lý định dạng `.xls` đời cũ.

---

## 9. CÁC HẠNG MỤC IT CẦN TRIỂN KHAI TIẾP THEO (PENDING BACKLOG)
1.  **Chuyển đổi CSDL sang PostgreSQL/SQL Server:** Chuyển đổi kết nối trong `config/settings.py` để hỗ trợ đa người dùng và chấm dứt tình trạng Database Lock.
2.  **Tích hợp Xác thực & Phân quyền (AD/LDAP):** Kết nối trang Đăng nhập trong `dash_app/app.py` với Active Directory của đơn vị để lấy thông tin `role` và `ma_cum` để tự động khóa cứng bộ lọc địa lý.
3.  **Tự động hóa luồng lấy số liệu:** Viết API/script SQL lấy dữ liệu trực tiếp định kỳ hàng ngày từ hệ thống nghiệp vụ CAS thay thế cho phương pháp import file Excel thủ công.
