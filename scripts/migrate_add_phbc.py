import sqlite3
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent
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


def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions_phbc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thang_du_lieu TEXT NOT NULL,
                nam_du_lieu INTEGER NOT NULL,
                ma_buu_cuc TEXT NOT NULL,
                doanh_thu REAL DEFAULT 0,
                import_batch TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_phbc_unique
            ON transactions_phbc (thang_du_lieu, nam_du_lieu, ma_buu_cuc)
        """)
        conn.commit()
        logger.error("[DONE] Bảng transactions_phbc đã sẵn sàng.")
    except Exception as e:
        logger.error(f"[ERROR] {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
