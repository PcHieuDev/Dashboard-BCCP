# TIP-db-002: Cập nhật agg_weekly cho 2025 + tạo plans_weekly

## HEADER
- TIP-ID: TIP-db-002
- Branch: feat/db-summary
- Project: Dashboard BCCP v2.0
- Module: ETL / Database
- Depends on: TIP-db-001
- Priority: P0
- Estimated effort: 60 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-db-summary
- Key files to reference:
  - `config/week_calendar.py` → hàm `get_week_list(year)` trả về danh sách tuần (start_date, end_date, week_number)
  - `etl/aggregator.py` (vừa tạo ở TIP-db-001) → pattern rebuild
  - Bảng `plans` trong DB: schema (nam, thang, nhom_dich_vu, ten_dich_vu, ma_buu_cuc, ke_hoach_doanh_thu)
  - Bảng `agg_weekly` trong DB: schema (tuan_bat_dau, tuan_ket_thuc, tuan_so, nam, buu_cuc, nhom_dich_vu, tong_doanh_thu, tong_san_luong, so_kh_phat_sinh, so_kh_moi, so_kh_tai_ban)

## TASK
2 phần công việc:

### Phần A: Cập nhật agg_weekly cho 2025
Bảng `agg_weekly` hiện chỉ có dữ liệu 2026. Cần bổ sung hàm rebuild trong `etl/aggregator.py` để tạo dữ liệu 2025.

### Phần B: Tạo bảng plans_weekly + hàm phân bổ kế hoạch
Phân bổ kế hoạch tháng → tuần theo số ngày lịch (calendar days).

## SPECIFICATIONS

### Phần A — Hàm `rebuild_weekly(conn, nam: int)`
- Đọc danh sách tuần từ `week_calendar.get_week_list(nam)`
- Mỗi tuần (start_date, end_date, week_number): query transactions WHERE ngay_chap_nhan BETWEEN start AND end
- GROUP BY buu_cuc, nhom_dich_vu (join dim_dichvu)
- Tính: tong_doanh_thu, tong_san_luong, so_kh_phat_sinh (COUNT DISTINCT cms hợp lệ)
- so_kh_moi, so_kh_tai_ban = 0 (sẽ tính riêng sau)
- DELETE cũ trước (WHERE nam = ?)
- INSERT mới

### Phần B — Bảng `plans_weekly`
```sql
CREATE TABLE IF NOT EXISTS plans_weekly (
    nam               INTEGER NOT NULL,
    tuan_so           INTEGER NOT NULL,
    tuan_bat_dau      DATE    NOT NULL,
    tuan_ket_thuc     DATE    NOT NULL,
    ma_buu_cuc        TEXT    NOT NULL,
    nhom_dich_vu      TEXT,
    ke_hoach_doanh_thu REAL DEFAULT 0,
    PRIMARY KEY (nam, tuan_so, ma_buu_cuc, nhom_dich_vu)
);
```

### Phần B — Hàm `allocate_weekly_plan(year)` trong `config/week_calendar.py`
Trả về dict mapping: `{(week_number, month): ratio}` cho mỗi tuần trong năm.

Logic:
- Với tuần thuần (nằm trọn 1 tháng), ví dụ tuần 12 (20/3-26/3): ratio tháng 3 = 7/31
- Với tuần qua 2 tháng, ví dụ tuần 13 (27/3-2/4):
  - ratio tháng 3 = 5/31 (27,28,29,30,31 tháng 3)
  - ratio tháng 4 = 2/30 (1,2 tháng 4)
- Trả về list of tuples: `[(week_number, start_date, end_date, [(month, year_of_month, days_in_week_for_month, days_in_month)])]`

### Phần B — Hàm `rebuild_plans_weekly(conn, nam: int)` trong `etl/aggregator.py`
- Gọi `allocate_weekly_plan(nam)` để lấy phân bổ
- Đọc bảng `plans` WHERE nam = ?
- Với mỗi tuần, với mỗi (ma_buu_cuc, nhom_dich_vu):
  - ke_hoach_tuan = SUM over các tháng trong tuần: plans[thang].ke_hoach_doanh_thu × (days_in_week_for_month / days_in_month)
- DELETE cũ (WHERE nam = ?)
- INSERT mới

## ACCEPTANCE CRITERIA
- Given: transactions có dữ liệu 2025 và plans có kế hoạch 2026
- When: Chạy rebuild_weekly(conn, 2025) và rebuild_plans_weekly(conn, 2026)
- Then:
  - agg_weekly có dữ liệu 2025 (kiểm tra COUNT > 0 WHERE nam = 2025)
  - plans_weekly có dữ liệu 2026
  - Với tuần thuần tháng 1: ke_hoach_tuan ≈ plans tháng 1 × 7/31 (sai số < 1 đồng)
  - Với tuần qua 2 tháng: ke_hoach_tuan = tổng phân bổ từ 2 tháng

## CONSTRAINTS
- CHỈ sửa `etl/aggregator.py` và `config/week_calendar.py`
- KHÔNG thay đổi schema bảng agg_weekly hiện có
- KHÔNG thay đổi hàm get_week_list() hiện có, chỉ THÊM hàm mới
- Dùng calendar.monthrange(year, month) để lấy số ngày trong tháng
