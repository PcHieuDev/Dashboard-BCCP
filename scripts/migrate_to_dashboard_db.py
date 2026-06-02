# -*- coding: utf-8 -*-
"""
Script migration: Copy bccp.db → dashboard.db và tạo các bảng mới cho 3 dịch vụ + Kế hoạch.
"""

import os
import shutil
import sqlite3
import sys
from pathlib import Path

# Cấu hình UTF-8 cho stdout trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình path
DB_DIR = Path(r"E:\OneDrive\z.Database-TTKD-Data")
OLD_DB = DB_DIR / "bccp.db"
NEW_DB = DB_DIR / "dashboard.db"

def run_migration():
    if not OLD_DB.exists():
        print(f"Error: {OLD_DB} không tồn tại.")
        return

    # 1. Copy file DB (chỉ copy nếu NEW_DB chưa tồn tại để tránh đè data)
    if not NEW_DB.exists():
        print(f"Copying {OLD_DB} to {NEW_DB}...")
        shutil.copy2(OLD_DB, NEW_DB)
        print("Copy thành công.")
    else:
        print(f"{NEW_DB} đã tồn tại. Sẽ tiếp tục tạo bảng mới (nếu chưa có).")

    # 2. Tạo các bảng mới
    print(f"Connecting to {NEW_DB}...")
    conn = sqlite3.connect(str(NEW_DB))
    cursor = conn.cursor()

    # Tạo transactions_hcc
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions_hcc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thang_du_lieu TEXT,
        nam_du_lieu INTEGER,
        ma_buu_cuc TEXT,
        ten_dich_vu TEXT,
        san_luong INTEGER,
        doanh_thu REAL,
        import_batch TEXT,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tạo transactions_tcbc
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions_tcbc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thang_du_lieu TEXT,
        nam_du_lieu INTEGER,
        ma_buu_cuc TEXT,
        ten_dich_vu TEXT,
        san_luong INTEGER,
        doanh_thu REAL,
        import_batch TEXT,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tạo transactions_ppbl
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions_ppbl (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thang_du_lieu TEXT,
        nam_du_lieu INTEGER,
        ma_buu_cuc TEXT,
        ten_dich_vu TEXT,
        san_luong INTEGER,
        doanh_thu REAL,
        import_batch TEXT,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tạo plans
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nam INTEGER,
        thang INTEGER,
        nhom_dich_vu TEXT,
        ten_dich_vu TEXT,
        ma_buu_cuc TEXT,
        ke_hoach_doanh_thu REAL,
        ke_hoach_san_luong INTEGER,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(nam, thang, nhom_dich_vu, ten_dich_vu, ma_buu_cuc)
    )
    """)

    conn.commit()
    conn.close()
    print("Tạo các bảng mới thành công: transactions_hcc, transactions_tcbc, transactions_ppbl, plans.")

if __name__ == "__main__":
    run_migration()
