# TIP-sc-003: rebuild_summaries logger + connection lifecycle + config/settings BACKUP_DIR fallback

## HEADER
- TIP-ID: TIP-sc-003
- Branch: fix/scripts-config
- Module: scripts/rebuild_summaries.py, config/settings.py
- Depends on: None
- Priority: P1
- Estimated effort: 20 phút

## CONTEXT
- Bug refs: C-02 (logger.error cho thường), H-04-pattern (connection lifecycle), L-13 (BACKUP_DIR fallback)

## TASK
1. rebuild_summaries.py: Đổi logger.error() → logger.info() cho thông báo trạng thái bình thường
2. rebuild_summaries.py: Refactor phần quản lý conn dùng try/finally (conn được đóng duy nhất trong finally)
3. config/settings.py: Sửa BACKUP_DIR để có fallback:
   _onedrive_backup = Path(r"E:\OneDrive\z.back-up-DB")
   BACKUP_DIR = _onedrive_backup if _onedrive_backup.parent.exists() else DATA_DIR / "backups"

## ACCEPTANCE CRITERIA
Given: OneDrive không được mount
When: backup chạy
Then: Lưu vào DATA_DIR/backups

Given: rebuild chạy thành công
When: Xem log
Then: Không ERROR giả

## CONSTRAINTS
- KHÔNG thay đổi logic rebuild
- KHÔNG thay đổi cấu trúc settings.py ngoài dòng BACKUP_DIR
