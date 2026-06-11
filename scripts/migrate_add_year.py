# -*- coding: utf-8 -*-
"""
Migration script: Thêm cột nam_du_lieu vào bảng transactions và backfill từ ngay_chap_nhan.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
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
    logger.info(f"Connecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Kiểm tra cột đã tồn tại chưa
    cols = [row[1] for row in cursor.execute("PRAGMA table_info(transactions)").fetchall()]
    
    if 'nam_du_lieu' not in cols:
        logger.info("Adding column nam_du_lieu...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN nam_du_lieu INTEGER")
        conn.commit()
        logger.info("Column added.")
    else:
        logger.info("Column nam_du_lieu already exists.")
    
    # Backfill: trích năm từ ngay_chap_nhan (format YYYY-MM-DD)
    logger.info("Backfilling nam_du_lieu from ngay_chap_nhan...")
    cursor.execute("""
        UPDATE transactions 
        SET nam_du_lieu = CAST(SUBSTR(ngay_chap_nhan, 1, 4) AS INTEGER)
        WHERE nam_du_lieu IS NULL AND ngay_chap_nhan IS NOT NULL
    """)
    updated = cursor.rowcount
    conn.commit()
    logger.info(f"Updated {updated} rows.")
    
    # Verify
    rows = cursor.execute("SELECT nam_du_lieu, COUNT(*) FROM transactions GROUP BY nam_du_lieu").fetchall()
    logger.info("\nVerification:")
    for year, count in rows:
        logger.info(f"  Year {year}: {count:,} rows")
    
    conn.close()
    logger.info("\nMigration complete!")

if __name__ == "__main__":
    migrate()
