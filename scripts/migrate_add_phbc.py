import sqlite3
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from config.settings import DB_PATH

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
        print("[DONE] Bảng transactions_phbc đã sẵn sàng.")
    except Exception as e:
        print(f"[ERROR] {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
