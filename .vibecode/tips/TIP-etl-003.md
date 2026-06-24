# TIP-etl-003: Sửa backup busy_timeout + importer rowcount

## HEADER
- TIP-ID: TIP-etl-003
- Branch: fix/etl
- Module: etl/backup.py, etl/importer.py
- Depends on: None
- Priority: P1
- Estimated effort: 15 phút

## CONTEXT
- Bug refs: M-07 (backup busy_timeout), M-01 (rowcount sau executemany sai)

## TASK
1. backup.py: Sau `src_conn = sqlite3.connect(db_path)`, thêm `src_conn.execute("PRAGMA busy_timeout=30000;")`
2. importer.py: Tìm tất cả các dòng pattern `cursor.executemany(...); inserted += cursor.rowcount`. Sửa thành:
   _before = conn.total_changes
   cursor.executemany(insert_sql, batch_buffer)
   inserted += conn.total_changes - _before

## ACCEPTANCE CRITERIA
Given: DB đang bị lock
When: backup chạy
Then: Chờ 30s, không fail ngay

Given: Import 1000 dòng
When: Kết quả
Then: inserted = 1000 chính xác

## CONSTRAINTS
- KHÔNG thay đổi cấu trúc hàm
