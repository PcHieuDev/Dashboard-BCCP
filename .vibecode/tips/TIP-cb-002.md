# TIP-cb-002: Sửa TypeError format month/week + thứ tự tab_val check

## HEADER
- TIP-ID: TIP-cb-002
- Branch: fix/critical-callbacks
- Project: Dashboard-BCCP
- Module: sidebar_callbacks.py, new_customer_callbacks.py, kpi_callbacks.py, customer_callbacks.py
- Depends on: None
- Priority: P0
- Estimated effort: 15 phút

## CONTEXT
- Bug refs: H-13 (sidebar month_val:02d crash), H-12 (new_customer month:02d crash), H-07 (kpi tab_val order), L-06 (customer tab_val)

## TASK
1. sidebar_callbacks.py dòng ~45: `f"Tháng {month_val:02d}/{year}"` → thêm guard `if month_val else f"Năm {year}"`
2. new_customer_callbacks.py dòng ~235: `{month:02d}` trong f-string → bọc trong `f'Tháng {month:02d}' if month else 'N/A'`
3. kpi_callbacks.py dòng ~217: `if tab_val != "tab-kpi" or tab_val is None:` → đổi thứ tự `if tab_val is None or tab_val != "tab-kpi":`
4. customer_callbacks.py dòng ~103: tương tự, đổi thứ tự check

## ACCEPTANCE CRITERIA
Given: User chọn kỳ = Tuần (month_val=None)
When: Sidebar render
Then: Không TypeError, hiển thị đúng

## CONSTRAINTS
- KHÔNG thay đổi logic query
- Sửa đúng 4 dòng
