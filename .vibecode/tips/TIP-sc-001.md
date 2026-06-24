# TIP-sc-001: Sửa hardcoded paths trong update_service_catalog + verify_db_vs_excel

## HEADER
- TIP-ID: TIP-sc-001
- Branch: fix/scripts-config
- Module: scripts/update_service_catalog.py, scripts/verify_db_vs_excel.py
- Depends on: None
- Priority: P0
- Estimated effort: 20 phút

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\fix-scripts-config
- Bug refs: C-03 (hardcoded worktree path), C-04 (DB_PATH hardcoded), M-19 (fallback path sai 3 cấp)

## TASK

### update_service_catalog.py
1. Thêm sys.path setup ở đầu file: project_root = Path(__file__).resolve().parent.parent
2. Xóa tất cả 4 dòng hardcoded paths (DB_PATH, EXCEL_PATH, CSV_OUT_PATH, MA_REF_PATH trỏ vào worktree feat-update-services)
3. Thêm `from config.settings import DB_PATH` và tính lại EXCEL_PATH, CSV_OUT_PATH, MA_REF_PATH dùng project_root
4. Sửa fallback sys.path.append dùng parent.parent.parent (3 cấp) → parent.parent (2 cấp)
Đọc config/settings.py trước để biết chính xác tên biến có sẵn.

### verify_db_vs_excel.py
1. Thêm sys.path setup tương tự
2. Thêm `from config.settings import DB_PATH`
3. Xóa dòng `DB_PATH = Path(r"E:\z.Database-TTKD-Data\dashboard.db")` hardcoded
4. Với EXCEL_DIR: nếu không có trong settings.py, thêm comment giải thích cần tham số hóa

## ACCEPTANCE CRITERIA
Given: Chạy từ bất kỳ thư mục nào
When: Script khởi động
Then: Không FileNotFoundError, import config thành công

## CONSTRAINTS
- KHÔNG thay đổi logic xử lý
- Đọc config/settings.py trước
