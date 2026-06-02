# -*- coding: utf-8 -*-
"""
Script migration: Migrate dim_spdv → dim_dichvu và tạo seed data cho HCC, TCBC, PPBL.
"""

import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DB_DIR = Path(r"E:\OneDrive\z.Database-TTKD-Data")
DB_PATH = DB_DIR / "dashboard.db"

def run_migration():
    if not DB_PATH.exists():
        print(f"Error: {DB_PATH} không tồn tại.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. Tạo bảng dim_dichvu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_dichvu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nhom_chinh TEXT NOT NULL,
        ma_dich_vu TEXT,
        ten_dich_vu TEXT NOT NULL,
        nhom_dich_vu TEXT,
        UNIQUE(nhom_chinh, ma_dich_vu)
    )
    """)

    # 2. Migrate data từ dim_spdv (BCCP)
    cursor.execute("""
    INSERT OR IGNORE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
    SELECT 'BCCP', ma_spdv, ten_spdv, nhom_dich_vu
    FROM dim_spdv
    """)

    # Thêm "Phát hành báo chí" cho BCCP (nếu chưa có mã cụ thể, tạo mã PHBC_DEFAULT)
    cursor.execute("""
    INSERT OR IGNORE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
    VALUES ('BCCP', 'PHBC_DEFAULT', 'Phát hành báo chí', 'Phát hành báo chí')
    """)

    # 3. Seed data cho HCC
    hcc_services = [
        "Chuyển phát HCC", "Chi trả lương hưu, bảo hiểm xã hội", 
        "Chi trả người có công", "Chi trả bảo trợ xã hội", 
        "Quản lý người hưởng", "CSHT"
    ]
    for svc in hcc_services:
        cursor.execute("""
        INSERT OR IGNORE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
        VALUES ('HCC', ?, ?, ?)
        """, (svc, svc, svc))

    # 4. Seed data cho TCBC
    tcbc_services = [
        "Tiết kiệm", "Tín dụng", "PTI", "Thu tiền điện", 
        "BHXH-BHYT", "Dịch vụ chuyển tiền"
    ]
    for svc in tcbc_services:
        cursor.execute("""
        INSERT OR IGNORE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
        VALUES ('TCBC', ?, ?, ?)
        """, (svc, svc, svc))

    # 5. Seed data cho PPBL
    ppbl_services = [
        "Hàng bán sỉ", "Hàng tiêu dùng bán lẻ"
    ]
    for svc in ppbl_services:
        cursor.execute("""
        INSERT OR IGNORE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
        VALUES ('PPBL', ?, ?, ?)
        """, (svc, svc, svc))

    conn.commit()
    conn.close()
    print("Migrate dim_dichvu thành công!")

if __name__ == "__main__":
    run_migration()
