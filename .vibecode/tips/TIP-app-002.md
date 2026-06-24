# TIP-app-002: Sửa compare_mode HCC + xóa dead code customer export

## HEADER
- TIP-ID: TIP-app-002
- Branch: fix/critical-app
- Project: Dashboard-BCCP
- Module: hcc_revenue_callbacks.py, customer_callbacks.py
- Depends on: None
- Priority: P0
- Estimated effort: 10 phút

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\fix-critical-app
- Bug refs: C-09 (compare_mode sai), C-08 (start_date NameError dead code), L-07 (return table trùng)

## TASK
1. hcc_revenue_callbacks.py: Sửa THẤT CẢ chỗ có `compare_mode = compare_opt if compare_prev else "prev_period"` → đổi "prev_period" thành "none"
2. customer_callbacks.py: Xóa khối `elif start_date and end_date:` trong hàm export_customer_table (dòng ~242)
3. customer_callbacks.py: Xóa dòng `return table` thứ 2 liền kề (dòng ~183)

## ACCEPTANCE CRITERIA
Given: User chọn "Không so sánh" trên tab HCC
When: Callback chạy
Then: compare_mode = "none"

Given: User bấm export KH
When: period không phải Tháng/Tuần
Then: Không NameError

## CONSTRAINTS
- KHÔNG sửa logic query nào
- Surgical: chỉ sửa đúng 3 điểm
