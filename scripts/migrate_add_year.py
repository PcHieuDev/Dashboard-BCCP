# -*- coding: utf-8 -*-
"""
Migration script: Thêm cột nam_du_lieu vào bảng transactions và backfill từ ngay_chap_nhan.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from config.settings import DB_PATH

def migrate():
    print(f"Connecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Kiểm tra cột đã tồn tại chưa
    cols = [row[1] for row in cursor.execute("PRAGMA table_info(transactions)").fetchall()]
    
    if 'nam_du_lieu' not in cols:
        print("Adding column nam_du_lieu...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN nam_du_lieu INTEGER")
        conn.commit()
        print("Column added.")
    else:
        print("Column nam_du_lieu already exists.")
    
    # Backfill: trích năm từ ngay_chap_nhan (format YYYY-MM-DD)
    print("Backfilling nam_du_lieu from ngay_chap_nhan...")
    cursor.execute("""
        UPDATE transactions 
        SET nam_du_lieu = CAST(SUBSTR(ngay_chap_nhan, 1, 4) AS INTEGER)
        WHERE nam_du_lieu IS NULL AND ngay_chap_nhan IS NOT NULL
    """)
    updated = cursor.rowcount
    conn.commit()
    print(f"Updated {updated} rows.")
    
    # Verify
    rows = cursor.execute("SELECT nam_du_lieu, COUNT(*) FROM transactions GROUP BY nam_du_lieu").fetchall()
    print("\nVerification:")
    for year, count in rows:
        print(f"  Year {year}: {count:,} rows")
    
    conn.close()
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
