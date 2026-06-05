# TIP-refactor-003: Manual Load - Tổng quan

## HEADER
- TIP-ID: TIP-refactor-003
- Branch: feat-ux-filters
- Project: Dashboard BCCP
- Module: Báo cáo Tổng quan
- Depends on: TIP-core-001, TIP-ui-002
- Priority: P1
- Estimated effort: 20 minutes

## TASK
Sửa kpi_callbacks.py và service_callbacks.py sang State và trigger bởi tn-apply-filter.

## ACCEPTANCE CRITERIA
Given: Trang KPI
When: Đổi dropdown
Then: Không load lại cho đến khi bấm Áp dụng.
