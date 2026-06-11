# -*- coding: utf-8 -*-
import sys
import sqlite3
from pathlib import Path

# Đảm bảo in tiếng Việt chính xác trên Windows Console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH
from etl.importer import import_service_excel

import logging
try:
    from config.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    try:
        from config.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = logging.getLogger(__name__)


def test():
    db_file = str(DB_PATH)
    excel_file = r"E:\Projects\Dashboard-BCCP\data\mau-file-import\mau_import_dich_vu_khac.xlsx"
    
    logger.error(f"Database: {db_file}")
    logger.error(f"Excel file: {excel_file}")
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # 1. Đếm số dòng trước khi import
    cnt_before = c.execute("SELECT COUNT(*) FROM transactions_hcc").fetchone()[0]
    logger.error(f"Số dòng trong transactions_hcc trước khi import: {cnt_before}")
    
    # Xóa các dòng có import_batch liên quan đến file mẫu này để tránh trùng lặp nếu test lại
    c.execute("DELETE FROM transactions_hcc WHERE import_batch LIKE '%mau_import_dich_vu_khac%'")
    conn.commit()
    
    cnt_cleaned = c.execute("SELECT COUNT(*) FROM transactions_hcc").fetchone()[0]
    logger.error(f"Số dòng sau khi làm sạch: {cnt_cleaned}")
    
    # 2. Thực hiện import với tháng T05 (Năm mặc định 2026)
    logger.error("Bắt đầu chạy import_service_excel...")
    res = import_service_excel(db_file, excel_file, "HCC", thang="T05")
    logger.error(f"Kết quả import: {res}")
    
    # 3. Đếm số dòng sau khi import
    cnt_after = c.execute("SELECT COUNT(*) FROM transactions_hcc").fetchone()[0]
    logger.error(f"Số dòng trong transactions_hcc sau khi import: {cnt_after}")
    
    # 4. Hiển thị 3 dòng mới nhất kèm các cột ngày vừa import
    logger.error("\nHiển thị 3 dòng dữ liệu vừa được import:")
    rows = c.execute("""
        SELECT id, thang_du_lieu, nam_du_lieu, ma_buu_cuc, ten_dich_vu, san_luong, doanh_thu,
               tu_ngay, tu_thang, tu_nam, den_ngay, den_thang, den_nam
        FROM transactions_hcc 
        ORDER BY id DESC LIMIT 3
    """).fetchall()
    
    for r in rows:
        logger.error(r)
        
    conn.close()

if __name__ == "__main__":
    test()
