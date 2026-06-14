# Hướng dẫn kiểm thử nhánh feat-standardize-columns

Tài liệu này hướng dẫn Sếp kiểm tra xem việc đổi tên cột từ cũ (`ma_bc`, `buu_cuc`, `san_pham_dv`, `nhom_dv`) sang chuẩn mới (`ma_buu_cuc`, `ten_dich_vu`, `nhom_dich_vu`) có hoạt động chính xác và không gây lỗi ứng dụng không.

---

## 🛠️ Bước 1: Chuẩn hóa cơ sở dữ liệu mẫu (hoặc thật)
Chạy script migration để tự động chuyển đổi cấu trúc các bảng trong file SQLite:

```powershell
python scripts/migrate_standardize_columns.py
```
*Script này sẽ tự động tạo bản sao lưu `.bak` trước khi thực hiện để đảm bảo an toàn.*

---

## ⚙️ Bước 2: Chạy thử Aggregator (Tính toán tổng hợp)
Sau khi database có cấu trúc mới, chạy aggregator để xem hệ thống có gộp số liệu (theo tuần/tháng) mà không bị lỗi SQL hay không:

```powershell
python etl/aggregator.py
```
**Kết quả kỳ vọng**: Dòng chữ `[OK] Aggregated monthly...` xuất hiện không có lỗi `no such column` hay lỗi SQL syntax.

---

## 🧪 Bước 3: Chạy Unit Tests tự động
Chạy các bài test mẫu có sẵn để đảm bảo hàm gán địa lý hoạt động đúng:

```powershell
python -m pytest tests/
```
**Kết quả kỳ vọng**: `3 passed` xanh lét.

---

## 🖥️ Bước 4: Chạy thử giao diện Dashboard
Khởi động ứng dụng web Dash:

```powershell
python dash_app/app.py
```
**Kiểm tra trực quan trên trình duyệt (http://127.0.0.1:8050)**:
1. Chọn thay đổi các bộ lọc ở Sidebar (Cụm, Xã).
2. Kiểm tra xem các biểu đồ doanh thu và bảng số liệu có hiển thị dữ liệu đầy đủ không.
3. Nếu không có bảng biểu nào báo lỗi "Error loading layout" hay crash giao diện thì việc đổi tên cột đã thành công 100%!
