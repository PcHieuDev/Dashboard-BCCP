# TIP-core-001: Data Core Refactoring

## HEADER
- TIP-ID: TIP-core-001
- Branch: feat-ux-filters
- Project: Dashboard BCCP
- Module: Data Core
- Depends on: None
- Priority: P0
- Estimated effort: 30 minutes

## TASK
Sửa Data Layer hỗ trợ start_date, end_date và Delta Days.

## ACCEPTANCE CRITERIA
Given: utils.py, evenue.py, week_calendar.py updated
When: UI truyền start_date và end_date
Then: Cache trả về đúng dữ liệu, logic So sánh dùng delta_days hoạt động tốt.
