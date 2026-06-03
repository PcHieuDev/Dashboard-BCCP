# TIP-bccp-001: Data Layer — Bảng new_customers + Calculator

## Header
- **TIP-ID**: TIP-bccp-001
- **Branch**: feat/bccp-upgrade
- **Module**: analytics
- **Dependencies**: Không
- **Priority**: P0
- **Estimated effort**: Medium

## Context
- **Working directory**: `E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade`
- **Key files**: `analytics/customer_classifier.py` (tham khảo logic), `config/settings.py` (DB_PATH)
- **DB**: `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`

## Task
Tạo module `analytics/new_customer_calculator.py` với các chức năng:

### 1. Tạo bảng `new_customers` trong DB:
```sql
CREATE TABLE IF NOT EXISTS new_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cms TEXT NOT NULL,
    thang INTEGER NOT NULL,
    nam INTEGER NOT NULL,
    buu_cuc TEXT,
    ma_bdx TEXT,
    ten_cum TEXT,
    nhom_dv TEXT,
    tong_doanh_thu REAL DEFAULT 0,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cms, thang, nam)
);
```

### 2. Hàm `calculate_new_customers(db_path, nam, thang)`:
1. Query tất cả CMS DISTINCT phát sinh trong `transactions` WHERE `nam_du_lieu=nam` AND `thang_du_lieu='T{thang:02d}'`
2. Loại CMS vãng lai: `cms IS NULL` hoặc `cms LIKE 'VANGLAI_%'`
3. Tính 3 tháng lookback: (nam_prev, thang_prev) cho T-1, T-2, T-3
   - VD: T01/2026 → check T10/2025, T11/2025, T12/2025
4. Query CMS có giao dịch trong 3 tháng lookback
5. CMS phát sinh tháng target mà KHÔNG nằm trong set lookback → **bán mới**
6. Cho mỗi CMS bán mới:
   - `buu_cuc`: Mã bưu cục đầu tiên phát sinh (hoặc nhiều nhất)
   - `ma_bdx`: Lấy từ `dim_buucuc` qua `substr(ma_bc, 1, 4)` HOẶC join file mapping
   - `ten_cum`: Lấy từ `dim_buucuc`
   - `nhom_dv`: Nhóm DV phát sinh đầu tiên (JOIN `dim_dichvu`)
   - `tong_doanh_thu`: SUM(cuoc_tt_tong) của CMS trong tháng target
7. DELETE existing records cho tháng đó trước khi INSERT (để hỗ trợ re-import)
8. INSERT vào bảng `new_customers`

### 3. Hàm `populate_historical_new_customers(db_path)`:
- Chạy `calculate_new_customers` cho từng tháng từ T10/2025 đến T06/2026
- Dùng 1 lần để tạo dữ liệu lịch sử
- In tiến trình ra console

### 4. Script chạy trực tiếp:
- Thêm `if __name__ == "__main__"` để có thể chạy `python analytics/new_customer_calculator.py`

## Specifications
- Thời gian lookback: **3 tháng** (cố định, không thay đổi)
- Vãng lai: CMS IS NULL hoặc LIKE 'VANGLAI_%'
- Data phạm vi: transactions có từ T05/2025 đến T06/2026

## Acceptance Criteria
```gherkin
Given dữ liệu transactions có từ T05/2025
When chạy populate_historical_new_customers()
Then bảng new_customers có records từ T10/2025 → T06/2026

Given CMS "ABC" phát sinh T01/2026, không có giao dịch T10+T11+T12/2025
When calculate_new_customers(db_path, 2026, 1)
Then CMS "ABC" có trong bảng new_customers với thang=1, nam=2026

Given CMS "ABC" đã phát sinh T01/2026
When calculate_new_customers(db_path, 2026, 2) 
Then CMS "ABC" KHÔNG có trong new_customers thang=2 (vì T01 có giao dịch = lookback hit)

Given chạy lại calculate_new_customers(db_path, 2026, 1)
Then dữ liệu cũ bị xóa và tính lại (không duplicate)
```

## Constraints
- Dùng SQLite thuần (sqlite3 module), không ORM
- Encoding UTF-8
- Import DB_PATH từ `config.settings`
