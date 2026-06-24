# TIP-etl-001: Sửa nam=None + whitelist nhom_chinh

## HEADER
- TIP-ID: TIP-etl-001
- Branch: fix/etl
- Module: etl/importer.py
- Depends on: None
- Priority: P0
- Estimated effort: 15 phút

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\fix-etl
- Bug refs: H-01 (nam=None trước vòng lặp), H-03 (whitelist nhom_chinh)

## TASK
1. H-01: Trong import_excel_file, thêm `nam = datetime.now().year` TRƯỚC vòng lặp for chính (~dòng 221)
2. H-03: Trong import_service_excel (~dòng 842), thêm whitelist:
   VALID_NHOM = {'hcc', 'tcbc', 'ppbl', 'phbc'}
   nhom_lower = nhom_chinh.lower() if nhom_chinh else ''
   if nhom_lower not in VALID_NHOM: warnings.append(...); continue
   table_dest = f"transactions_{nhom_lower}"

## ACCEPTANCE CRITERIA
Given: File Excel không có ngày hợp lệ
When: Import
Then: `nam` = năm hiện tại, không crash

Given: nhom_chinh = 'xyz'
When: Import service
Then: Warning + bỏ qua, không crash

## CONSTRAINTS
- KHÔNG thay đổi logic import khác
