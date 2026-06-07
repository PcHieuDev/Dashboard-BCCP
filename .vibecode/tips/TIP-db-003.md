# TIP-db-003: Cập nhật new_customer_calculator (cột ngày, DT>0)

## HEADER
- TIP-ID: TIP-db-003
- Branch: feat/db-summary
- Project: Dashboard BCCP v2.0
- Module: Analytics
- Depends on: None
- Priority: P0
- Estimated effort: 30 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-db-summary
- Key files to reference:
  - `analytics/new_customer_calculator.py` → logic hiện tại tính KH mới
  - `analytics/customer_classifier.py` → logic phân loại KH
  - Bảng `new_customers`: schema (id, cms, thang, nam, buu_cuc, ma_bdx, ten_cum, nhom_dv, tong_doanh_thu, ngay_tao)

## TASK
Cập nhật logic xác định khách hàng mới/tái bán theo định nghĩa mới:
1. Thêm cột `ngay_phat_sinh` vào bảng `new_customers`
2. Thêm điều kiện **doanh thu dương** (cuoc_tt_tong > 0) khi xác định KH mới
3. Cập nhật `customer_classifier.py` tương ứng

## SPECIFICATIONS

### 1. ALTER TABLE new_customers
```sql
ALTER TABLE new_customers ADD COLUMN ngay_phat_sinh DATE;
```
- Thực hiện trong hàm `init_db()` — kiểm tra cột đã tồn tại chưa bằng PRAGMA table_info trước khi ALTER
- Populate: `ngay_phat_sinh` = MIN(ngay_chap_nhan) của CMS trong tháng target từ bảng transactions

### 2. Cập nhật `calculate_new_customers()` trong new_customer_calculator.py

Thay đổi query lấy CMS target:
```sql
-- CŨ: chỉ filter cms IS NOT NULL, NOT LIKE 'VANGLAI_%'
-- MỚI: thêm AND cuoc_tt_tong > 0
SELECT DISTINCT cms 
FROM transactions 
WHERE nam_du_lieu = ? AND thang_du_lieu = ?
  AND cms IS NOT NULL AND cms != '' 
  AND cms NOT LIKE 'VANGLAI_%' AND LOWER(cms) != 'none'
  AND cuoc_tt_tong > 0  -- ĐK MỚI
```

Thay đổi query lookback 3 tháng:
```sql
-- CŨ: chỉ check CMS có giao dịch
-- MỚI: thêm AND cuoc_tt_tong > 0 (chỉ tính CMS có doanh thu dương)
SELECT DISTINCT cms 
FROM transactions 
WHERE nam_du_lieu = ? AND thang_du_lieu = ?
  AND cms IS NOT NULL AND cms != '' 
  AND cms NOT LIKE 'VANGLAI_%' AND LOWER(cms) != 'none'
  AND cuoc_tt_tong > 0  -- ĐK MỚI
```

Bổ sung query lấy ngày phát sinh:
```sql
SELECT cms, MIN(ngay_chap_nhan) as ngay_phat_sinh
FROM transactions
WHERE nam_du_lieu = ? AND thang_du_lieu = ? AND cms IN (...)
  AND cuoc_tt_tong > 0
GROUP BY cms
```

Bổ sung cột `ngay_phat_sinh` vào INSERT:
```sql
INSERT INTO new_customers (cms, thang, nam, buu_cuc, ma_bdx, ten_cum, nhom_dv, tong_doanh_thu, ngay_phat_sinh)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
```

### 3. Cập nhật `classify_customers()` trong customer_classifier.py
- Query tìm CMS có giao dịch trong tháng: thêm `AND cuoc_tt_tong > 0`
- Query tìm CMS active trong 3 tháng trước: thêm `AND cuoc_tt_tong > 0`

## ACCEPTANCE CRITERIA
- Given: Bảng transactions có dữ liệu T01-T06/2026
- When: Chạy `populate_historical_new_customers(db_path)`
- Then:
  - Bảng new_customers có cột ngay_phat_sinh được populate (không NULL)
  - KH mới chỉ bao gồm CMS có cuoc_tt_tong > 0
  - Số lượng KH mới có thể khác bản cũ (do thêm điều kiện DT > 0)

## CONSTRAINTS
- CHỈ sửa `analytics/new_customer_calculator.py` và `analytics/customer_classifier.py`
- GIỮ NGUYÊN signature các hàm public (calculate_new_customers, classify_customers)
- GIỮ NGUYÊN hàm populate_historical_new_customers() — chỉ sửa logic bên trong
- KHÔNG xóa dữ liệu new_customers cũ cho đến khi rebuild
