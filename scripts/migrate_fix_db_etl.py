# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
import sys

# Đảm bảo in tiếng Việt chính xác trên Windows Console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Thêm thư mục gốc dự án vào sys.path để import
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH

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


def check_column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate():
    logger.error(f"Kết nối tới Database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    tables = ['transactions_hcc', 'transactions_tcbc', 'transactions_ppbl']
    columns_to_add = [
        ('tu_ngay', 'INTEGER DEFAULT 1'),
        ('tu_thang', 'INTEGER DEFAULT 1'),
        ('tu_nam', 'INTEGER'),
        ('den_ngay', 'INTEGER DEFAULT 30'),
        ('den_thang', 'INTEGER DEFAULT 12'),
        ('den_nam', 'INTEGER')
    ]
    
    try:
        for table in tables:
            logger.error(f"Kiểm tra bảng {table}...")
            # Kiểm tra xem bảng có tồn tại hay không
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                logger.error(f"  [WARNING] Bảng {table} không tồn tại trong database, bỏ qua.")
                continue
                
            for col_name, col_type in columns_to_add:
                if not check_column_exists(cursor, table, col_name):
                    logger.error(f"  Thêm cột {col_name} ({col_type}) vào bảng {table}...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                else:
                    logger.error(f"  Cột {col_name} đã tồn tại trong bảng {table}, bỏ qua.")
        conn.commit()
        logger.error("[DONE] Di cư cơ sở dữ liệu hoàn tất thành công.")
    except Exception as e:
        logger.error(f"[ERROR] Đã xảy ra lỗi khi di cư: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
