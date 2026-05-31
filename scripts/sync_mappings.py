# -*- coding: utf-8 -*-
"""
Script đồng bộ dữ liệu mapping từ các file CSV trong thư mục data/ vào Database SQLite.
Chạy script này sau khi bổ sung sản phẩm dịch vụ mới hoặc bưu cục mới trong file CSV.

Cách dùng:
    python scripts/sync_mappings.py
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Thêm thư mục gốc vào path để import settings
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH, MAPPING_PATH, MAPPING_GEOGRAPHY_PATH

def sync_spdv(conn):
    """Đồng bộ mapping sản phẩm dịch vụ từ CSV vào bảng dim_spdv."""
    if not MAPPING_PATH.exists():
        print(f"⚠️  Không tìm thấy file mapping sản phẩm tại: {MAPPING_PATH}")
        return 0

    # Đọc CSV mapping (thử nhiều encoding phòng trường hợp Excel lưu dạng ANSI/CP1252)
    df = None
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            df = pd.read_csv(MAPPING_PATH, encoding=enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
            
    if df is None:
        print(f"❌ Lỗi: Không thể đọc file mapping sản phẩm {MAPPING_PATH} với bất kỳ encoding nào.")
        return 0
        
    # Chuẩn hóa tên cột
    df.columns = [c.strip().lower() for c in df.columns]
    
    expected_cols = ["ma_spdv", "ten_spdv", "nhom_dich_vu"]
    for col in expected_cols:
        if col not in df.columns:
            print(f"❌ Lỗi: Cột '{col}' không tồn tại trong file CSV mapping sản phẩm.")
            print(f"   Các cột đang có: {list(df.columns)}")
            return 0

    # Thêm cột ghi_chu nếu chưa có
    if "ghi_chu" not in df.columns:
        df["ghi_chu"] = None

    # Ghi đè vào DB
    cursor = conn.cursor()
    rows_synced = 0
    for _, row in df.iterrows():
        ma_spdv = str(row["ma_spdv"]).strip()
        if not ma_spdv or pd.isna(row["ma_spdv"]):
            continue
        cursor.execute(
            """INSERT OR REPLACE INTO dim_spdv (ma_spdv, ten_spdv, nhom_dich_vu, ghi_chu)
               VALUES (?, ?, ?, ?)""",
            (ma_spdv, str(row["ten_spdv"]).strip(), str(row["nhom_dich_vu"]).strip(), row.get("ghi_chu")),
        )
        rows_synced += 1

    conn.commit()
    print(f"✅ Đã đồng bộ thành công {rows_synced} sản phẩm vào bảng dim_spdv.")
    return rows_synced

def sync_buucuc(conn):
    """Đồng bộ mapping bưu cục từ CSV vào bảng dim_buucuc."""
    if not MAPPING_GEOGRAPHY_PATH.exists():
        print(f"⚠️  Không tìm thấy file mapping bưu cục tại: {MAPPING_GEOGRAPHY_PATH}")
        return 0

    # Đọc CSV mapping (thử nhiều encoding)
    df = None
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            df = pd.read_csv(MAPPING_GEOGRAPHY_PATH, encoding=enc, dtype=str)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
            
    if df is None:
        print(f"❌ Lỗi: Không thể đọc file mapping bưu cục {MAPPING_GEOGRAPHY_PATH} với bất kỳ encoding nào.")
        return 0
        
    # Chuẩn hóa tên cột
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Kiểm tra cột bắt buộc
    required_cols = ['ma_bc', 'ten_buu_cuc', 'ma_bdx', 'ten_bdx', 'ten_cum']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Lỗi: Cột '{col}' không tồn tại trong file CSV mapping bưu cục.")
            print(f"   Các cột đang có: {list(df.columns)}")
            return 0

    cursor = conn.cursor()
    rows_synced = 0
    for _, row in df.iterrows():
        ma_bc = str(row.get('ma_bc', '')).strip()
        if not ma_bc or pd.isna(row.get('ma_bc')):
            continue
            
        cursor.execute(
            """INSERT OR REPLACE INTO dim_buucuc (ma_bc, ten_buu_cuc, ma_bdx, ten_bdx, ten_cum)
               VALUES (?, ?, ?, ?, ?)""",
            (
                ma_bc,
                str(row.get('ten_buu_cuc', '')).strip(),
                str(row.get('ma_bdx', '')).strip(),
                str(row.get('ten_bdx', '')).strip(),
                str(row.get('ten_cum', '')).strip()
            ),
        )
        rows_synced += 1

    conn.commit()
    print(f"✅ Đã đồng bộ thành công {rows_synced} bưu cục vào bảng dim_buucuc.")
    return rows_synced

def clear_caches():
    """Xóa bộ nhớ đệm cache để Dashboard nhận dữ liệu mới lập tức."""
    try:
        from callbacks.utils import clear_query_cache
        from db.connection import clear_db_cache
        clear_query_cache()
        clear_db_cache()
        print("🧹 Đã làm sạch bộ nhớ cache của Dashboard.")
    except Exception:
        # Nếu đang chạy độc lập ngoài app thì bỏ qua cache clear
        pass

def main():
    # Cấu hình encoding utf-8 cho Windows console khi in
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("🔄 Bắt đầu đồng bộ danh mục từ tệp CSV...")
    if not DB_PATH.exists():
        print(f"❌ Lỗi: Cơ sở dữ liệu không tồn tại tại {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(str(DB_PATH))
    try:
        sync_spdv(conn)
        sync_buucuc(conn)
        clear_caches()
        print("\n🎉 Tất cả danh mục đã được cập nhật thành công!")
    except Exception as e:
        print(f"❌ Lỗi xảy ra trong quá trình đồng bộ: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
