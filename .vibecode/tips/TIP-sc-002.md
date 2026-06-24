# TIP-sc-002: Sửa SQL DELETE logic sync_mappings + đổi logger level

## HEADER
- TIP-ID: TIP-sc-002
- Branch: fix/scripts-config
- Module: scripts/sync_mappings.py
- Depends on: None
- Priority: P0
- Estimated effort: 15 phút

## CONTEXT
- Bug refs: H-14 (SQL DELETE mâu thuẫn), tương tự M-05 (logger level)

## TASK
1. Tìm câu DELETE ~dòng 125-129. Đọc comment xung quanh để hiểu ý định. Thêm ngoặc rõ ràng và sửa pattern LIKE cho phù hợp ý định.
2. Tất cả logger.error() cho thông báo bình thường → logger.info()

## ACCEPTANCE CRITERIA
Given: sync_mappings chạy
When: Đồng bộ
Then: DELETE đúng mục tiêu, không xóa nhầm seed data

## CONSTRAINTS
- KHÔNG thay đổi INSERT/UPDATE
- Nếu không chắc về logic DELETE, thêm comment hỏi lại thay vì sửa bừa
