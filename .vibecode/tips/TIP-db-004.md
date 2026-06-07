# TIP-db-004: Tích hợp aggregator vào importer + script rebuild

## HEADER
- TIP-ID: TIP-db-004
- Branch: feat/db-summary
- Project: Dashboard BCCP v2.0
- Module: ETL
- Depends on: TIP-db-001, TIP-db-002
- Priority: P0
- Estimated effort: 20 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-db-summary
- Key files to reference:
  - `etl/importer.py` → hàm chính import Excel. Tìm vị trí thành công để trigger rebuild
  - `etl/aggregator.py` (tạo ở TIP-db-001, TIP-db-002)
  - `analytics/new_customer_calculator.py` (sửa ở TIP-db-003)

## TASK
1. Trong `etl/importer.py`: sau khi import thành công, tự động gọi rebuild summary cho tháng vừa import
2. Tạo `scripts/rebuild_summaries.py`: entry point chạy rebuild toàn bộ

## SPECIFICATIONS

### 1. Sửa etl/importer.py
- Tìm vị trí cuối cùng khi import thành công (sau commit, trước return)
- Thêm:
```python
# Auto-refresh summary tables cho tháng vừa import
try:
    from etl.aggregator import rebuild_monthly, rebuild_monthly_customer
    rebuild_monthly(conn, nam, thang_int)
    rebuild_monthly_customer(conn, nam, thang_int)
    print(f"[Summary] Đã cập nhật agg_monthly cho T{thang_int:02d}/{nam}")
except Exception as e:
    print(f"[Summary] Lỗi cập nhật summary: {e}")
```
- Trong đó `nam` và `thang_int` parse từ tham số import hiện có (nam_du_lieu, thang_du_lieu)
- KHÔNG gọi rebuild_weekly ở đây (tốn thời gian, chạy riêng khi cần)

### 2. Tạo scripts/rebuild_summaries.py
```python
"""
Script rebuild toàn bộ summary tables.
Chạy: python scripts/rebuild_summaries.py [--year YYYY]
"""
```
- Import và gọi tuần tự:
  1. `aggregator.create_summary_tables(conn)`
  2. `aggregator.rebuild_all_monthly(conn)` — tất cả tháng
  3. `aggregator.rebuild_weekly(conn, year)` — cho từng năm có dữ liệu
  4. `aggregator.rebuild_plans_weekly(conn, year)` — cho từng năm có plans
  5. `new_customer_calculator.populate_historical_new_customers(db_path)` — tính lại KH mới
- Hỗ trợ arg `--year` để chỉ rebuild 1 năm cụ thể
- Print tổng thời gian chạy

## ACCEPTANCE CRITERIA
- Given: DB có dữ liệu transactions
- When: Chạy `python scripts/rebuild_summaries.py`
- Then:
  - Tất cả bảng summary được tạo/cập nhật
  - Print log cho mỗi bước
  - Tổng thời gian < 5 phút
- When: Import 1 file Excel mới qua giao diện
- Then: agg_monthly tự động cập nhật cho tháng vừa import

## CONSTRAINTS
- Khi sửa importer.py: CHỈ thêm code ở cuối flow import, KHÔNG sửa logic import hiện có
- KHÔNG import nặng ở đầu file importer.py (dùng lazy import trong hàm)
- scripts/rebuild_summaries.py phải chạy được độc lập từ command line
