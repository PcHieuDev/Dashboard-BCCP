# TIP-db-001: Tạo aggregator.py + bảng agg_monthly, agg_monthly_customer

## HEADER
- TIP-ID: TIP-db-001
- Branch: feat/db-summary
- Project: Dashboard BCCP v2.0
- Module: ETL / Database
- Depends on: None
- Priority: P0
- Estimated effort: 45 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-db-summary
- Key files to reference:
  - `config/settings.py` → DB_PATH
  - `etl/importer.py` → pattern import/insert vào SQLite
  - `analytics/global_metrics.py` → hiểu cách dữ liệu đang được truy vấn (sẽ chuyển sang đọc summary)
- Patterns to follow: Xem context.md mục 5 — DB access pattern

## TASK
Tạo file `etl/aggregator.py` chứa các hàm tổng hợp dữ liệu từ bảng `transactions` (raw ~1M dòng) vào 2 bảng trung gian mới:

1. **`agg_monthly`** — Tổng hợp doanh thu theo bưu cục/nhóm dịch vụ/tháng
2. **`agg_monthly_customer`** — Tổng hợp doanh thu theo CMS/bưu cục/tháng

## SPECIFICATIONS

### Bảng `agg_monthly`
```sql
CREATE TABLE IF NOT EXISTS agg_monthly (
    nam           INTEGER NOT NULL,
    thang         INTEGER NOT NULL,
    buu_cuc       TEXT    NOT NULL,
    nhom_dich_vu  TEXT,
    tong_doanh_thu    REAL DEFAULT 0,
    tong_san_luong    INTEGER DEFAULT 0,
    so_kh_phat_sinh   INTEGER DEFAULT 0,
    PRIMARY KEY (nam, thang, buu_cuc, nhom_dich_vu)
);
```
- `tong_doanh_thu` = SUM(cuoc_tt_tong)
- `tong_san_luong` = SUM(san_luong)
- `so_kh_phat_sinh` = COUNT(DISTINCT cms) — chỉ CMS hợp lệ (không NULL, không VANGLAI_, không 'none')
- `nhom_dich_vu` lấy từ JOIN `transactions.san_pham_dv` = `dim_dichvu.ma_dich_vu` → `dim_dichvu.nhom_dich_vu`. Nếu không map được → 'Khác'
- GROUP BY: nam_du_lieu, thang (parse từ thang_du_lieu dạng 'T01' → 1), buu_cuc, nhom_dich_vu

### Bảng `agg_monthly_customer`
```sql
CREATE TABLE IF NOT EXISTS agg_monthly_customer (
    cms           TEXT    NOT NULL,
    buu_cuc       TEXT    NOT NULL,
    nam           INTEGER NOT NULL,
    thang         INTEGER NOT NULL,
    nhom_dich_vu  TEXT,
    tong_doanh_thu    REAL DEFAULT 0,
    tong_san_luong    INTEGER DEFAULT 0,
    so_giao_dich      INTEGER DEFAULT 0,
    PRIMARY KEY (cms, buu_cuc, nam, thang, nhom_dich_vu)
);
```
- `so_giao_dich` = COUNT(*)
- Chỉ tính CMS hợp lệ

### Hàm cần tạo
1. `create_summary_tables(conn)` — CREATE TABLE IF NOT EXISTS cho cả 2 bảng
2. `rebuild_monthly(conn, nam: int, thang: int)` — DELETE dữ liệu cũ của (nam, thang), INSERT aggregate mới
3. `rebuild_monthly_customer(conn, nam: int, thang: int)` — tương tự cho bảng customer
4. `rebuild_all_monthly(conn)` — query tất cả (nam_du_lieu, thang_du_lieu) DISTINCT từ transactions, gọi rebuild cho từng cặp

### Lưu ý kỹ thuật
- Import `DB_PATH` từ `config.settings`
- Dùng `sys.stdout.reconfigure(encoding='utf-8')` ở đầu file
- Print log mỗi tháng đang xử lý và số dòng đã insert
- Đặt `conn.execute("PRAGMA journal_mode=WAL")` để tăng tốc write

## ACCEPTANCE CRITERIA
- Given: Bảng transactions có dữ liệu T01-T12/2025 và T01-T06/2026
- When: Chạy `python -c "from etl.aggregator import ...; rebuild_all_monthly(...)"`
- Then: 
  - Bảng `agg_monthly` được tạo, có dữ liệu cho tất cả tháng
  - SUM(tong_doanh_thu) trong agg_monthly khớp với SUM(cuoc_tt_tong) trong transactions cho cùng tháng
  - Bảng `agg_monthly_customer` được tạo, có dữ liệu

## CONSTRAINTS
- KHÔNG sửa bất kỳ file nào khác ngoài etl/aggregator.py
- KHÔNG thay đổi schema bảng transactions
- KHÔNG xóa dữ liệu raw
- Dùng sqlite3 thuần, KHÔNG dùng ORM
