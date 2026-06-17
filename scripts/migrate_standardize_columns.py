# -*- coding: utf-8 -*-
"""
Script migration: Chuẩn hóa tên cột trong SQLite
- Xóa 2 bảng backup cũ
- Đổi tên cột buu_cuc/ma_bc → ma_buu_cuc
- Đổi tên cột san_pham_dv → ten_dich_vu
- Đổi tên cột nhom_dv → nhom_dich_vu
"""

import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path("E:/z.Database-TTKD-Data/dashboard.db")
BACKUP_PATH = DB_PATH.with_name(f"dashboard.db.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")


def backup_db():
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"[OK] Backup: {BACKUP_PATH}")


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Kiểm tra version SQLite
    cursor.execute("SELECT sqlite_version()")
    version = cursor.fetchone()[0]
    print(f"[INFO] SQLite version: {version}")

    steps = [
        # 1. Xóa 2 bảng backup cũ
        ("Xóa dim_buucuc_backup_old", "DROP TABLE IF EXISTS dim_buucuc_backup_old"),
        ("Xóa dim_dichvu_backup_old", "DROP TABLE IF EXISTS dim_dichvu_backup_old"),
        ("Xóa plans_backup_old",      "DROP TABLE IF EXISTS plans_backup_old"),

        # 2. dim_buucuc: ma_bc → ma_buu_cuc
        ("dim_buucuc: ma_bc → ma_buu_cuc",
         "ALTER TABLE dim_buucuc RENAME COLUMN ma_bc TO ma_buu_cuc"),

        # 3. transactions: buu_cuc → ma_buu_cuc
        ("transactions: buu_cuc → ma_buu_cuc",
         "ALTER TABLE transactions RENAME COLUMN buu_cuc TO ma_buu_cuc"),

        # 4. transactions: san_pham_dv → ten_dich_vu
        ("transactions: san_pham_dv → ten_dich_vu",
         "ALTER TABLE transactions RENAME COLUMN san_pham_dv TO ten_dich_vu"),

        # 5. agg_monthly: buu_cuc → ma_buu_cuc
        ("agg_monthly: buu_cuc → ma_buu_cuc",
         "ALTER TABLE agg_monthly RENAME COLUMN buu_cuc TO ma_buu_cuc"),

        # 6. agg_monthly_customer: buu_cuc → ma_buu_cuc
        ("agg_monthly_customer: buu_cuc → ma_buu_cuc",
         "ALTER TABLE agg_monthly_customer RENAME COLUMN buu_cuc TO ma_buu_cuc"),

        # 7. agg_weekly: buu_cuc → ma_buu_cuc
        ("agg_weekly: buu_cuc → ma_buu_cuc",
         "ALTER TABLE agg_weekly RENAME COLUMN buu_cuc TO ma_buu_cuc"),

        # 8. new_customers: buu_cuc → ma_buu_cuc
        ("new_customers: buu_cuc → ma_buu_cuc",
         "ALTER TABLE new_customers RENAME COLUMN buu_cuc TO ma_buu_cuc"),

        # 9. new_customers: nhom_dv → nhom_dich_vu
        ("new_customers: nhom_dv → nhom_dich_vu",
         "ALTER TABLE new_customers RENAME COLUMN nhom_dv TO nhom_dich_vu"),
    ]

    for label, sql in steps:
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"[OK] {label}")
        except sqlite3.OperationalError as e:
            print(f"[WARN] {label}: {e}")

    conn.close()


def verify():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    checks = [
        ("dim_buucuc", ["ma_buu_cuc", "ten_buu_cuc"]),
        ("transactions", ["ma_buu_cuc", "ten_dich_vu"]),
        ("agg_monthly", ["ma_buu_cuc", "nhom_dich_vu"]),
        ("agg_monthly_customer", ["ma_buu_cuc", "nhom_dich_vu"]),
        ("agg_weekly", ["ma_buu_cuc", "nhom_dich_vu"]),
        ("new_customers", ["ma_buu_cuc", "nhom_dich_vu"]),
        ("plans", ["ma_buu_cuc", "nhom_dich_vu"]),
    ]
    print("\n=== XÁC MINH ===")
    all_ok = True
    for table, expected_cols in checks:
        cursor.execute(f"PRAGMA table_info({table})")
        actual_cols = [r[1] for r in cursor.fetchall()]
        missing = [c for c in expected_cols if c not in actual_cols]
        old_cols = [c for c in ["buu_cuc", "ma_bc", "san_pham_dv", "nhom_dv"] if c in actual_cols]
        if missing:
            print(f"[FAIL] {table}: thiếu {missing}")
            all_ok = False
        elif old_cols:
            print(f"[FAIL] {table}: vẫn còn cột cũ {old_cols}")
            all_ok = False
        else:
            print(f"[OK]   {table}: {actual_cols}")

    # Kiểm tra bảng backup đã xóa chưa
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%backup_old'")
    leftover = cursor.fetchall()
    if leftover:
        print(f"[WARN] Còn bảng backup: {leftover}")
    else:
        print("[OK]   Đã xóa tất cả bảng backup_old")

    conn.close()
    return all_ok


if __name__ == "__main__":
    print("=== MIGRATION: Chuẩn hóa tên cột ===\n")
    backup_db()
    run_migration()
    ok = verify()
    if ok:
        print("\n✅ Migration hoàn thành thành công!")
    else:
        print(f"\n❌ Có lỗi. Backup tại: {BACKUP_PATH}")
