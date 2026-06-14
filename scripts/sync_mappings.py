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


def sync_spdv(conn):
    """Đồng bộ mapping sản phẩm dịch vụ từ CSV vào bảng dim_dichvu và dim_spdv."""
    if not MAPPING_PATH.exists():
        logger.error(f"⚠️  Không tìm thấy file mapping sản phẩm tại: {MAPPING_PATH}")
        return 0

    # Đọc CSV mapping (thử nhiều separator và encoding)
    df = None
    for sep in [",", ";"]:
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                df_temp = pd.read_csv(MAPPING_PATH, sep=sep, encoding=enc)
                df_temp.columns = [c.strip().lower() for c in df_temp.columns]
                if "ma_spdv" in df_temp.columns:
                    df = df_temp
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None:
        logger.error(f"❌ Lỗi: Không thể đọc file mapping sản phẩm {MAPPING_PATH} hoặc thiếu cột bắt buộc.")
        return 0
        
    expected_cols = ["nhom_chinh", "ma_spdv", "ten_spdv", "nhom_dich_vu"]
    for col in expected_cols:
        if col not in df.columns:
            logger.error(f"❌ Lỗi: Cột '{col}' không tồn tại trong file CSV mapping sản phẩm.")
            logger.error(f"   Các cột đang có: {list(df.columns)}")
            return 0

    # Thêm cột ghi_chu nếu chưa có
    if "ghi_chu" not in df.columns:
        df["ghi_chu"] = None

    # 1. Tự động backup bảng dim_dichvu hiện tại ra file CSV
    import datetime
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = MAPPING_PATH.parent
        backup_file = backup_dir / f"dim_dichvu_backup_{timestamp}.csv"
        
        # Đọc dữ liệu hiện tại
        df_backup = pd.read_sql_query("SELECT * FROM dim_dichvu", conn)
        df_backup.to_csv(backup_file, index=False, encoding="utf-8-sig")
        logger.error(f"💾 Đã tạo file backup bảng dim_dichvu tại: {backup_file}")
    except Exception as e:
        logger.error(f"⚠️ Cảnh báo: Không thể backup bảng dim_dichvu: {e}")

    cursor = conn.cursor()

    # 2. Xóa các dòng BCCP và mã HCC (HCC001-HCC004) để thực hiện nạp mới (TRUNCATE)
    # Giữ lại các dòng seed data cho HCC (không phải dạng mã HCC001...), TCBC, PPBL
    try:
        cursor.execute("""
            DELETE FROM dim_dichvu 
            WHERE nhom_chinh = 'BCCP' AND ma_dich_vu != 'PHBC_DEFAULT'
               OR (nhom_chinh = 'HCC' AND ma_dich_vu LIKE 'HCC%')
        """)
        conn.commit()
        logger.error("🧹 Đã làm sạch các dòng BCCP và mã HCC cũ trong bảng dim_dichvu.")
    except Exception as e:
        logger.error(f"❌ Lỗi khi làm sạch dữ liệu cũ trong dim_dichvu: {e}")
        return 0

    # 3. Ghi vào cả dim_dichvu mới và dim_spdv cũ
    rows_synced = 0
    for _, row in df.iterrows():
        ma_spdv = str(row["ma_spdv"]).strip()
        if not ma_spdv or pd.isna(row["ma_spdv"]):
            continue
            
        nhom_chinh = str(row["nhom_chinh"]).strip()
        ten_spdv = str(row["ten_spdv"]).strip()
        nhom_dich_vu = str(row["nhom_dich_vu"]).strip()
        
        # 1. Đồng bộ vào dim_dichvu (bảng đa dịch vụ mới)
        cursor.execute(
            """INSERT OR REPLACE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
               VALUES (?, ?, ?, ?)""",
            (nhom_chinh, ma_spdv, ten_spdv, nhom_dich_vu),
        )
        rows_synced += 1

    conn.commit()
    logger.error(f"✅ Đã đồng bộ thành công {rows_synced} sản phẩm vào bảng dim_dichvu và dim_spdv.")
    return rows_synced

def sync_buucuc(conn):
    """Đồng bộ mapping bưu cục từ CSV vào bảng dim_buucuc."""
    if not MAPPING_GEOGRAPHY_PATH.exists():
        logger.error(f"⚠️  Không tìm thấy file mapping bưu cục tại: {MAPPING_GEOGRAPHY_PATH}")
        return 0

    # Đọc CSV mapping (thử nhiều separator và encoding)
    df = None
    for sep in [",", ";"]:
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                df_temp = pd.read_csv(MAPPING_GEOGRAPHY_PATH, sep=sep, encoding=enc, dtype=str)
                df_temp.columns = [c.strip().lower() for c in df_temp.columns]
                if "ma_bc" in df_temp.columns:
                    df = df_temp
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None:
        logger.error(f"❌ Lỗi: Không thể đọc file mapping bưu cục {MAPPING_GEOGRAPHY_PATH} hoặc thiếu cột bắt buộc.")
        return 0
        
    # Kiểm tra cột bắt buộc
    required_cols = ['ma_bc', 'ten_buu_cuc', 'ma_bdx', 'ten_bdx', 'ten_cum']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"❌ Lỗi: Cột '{col}' không tồn tại trong file CSV mapping bưu cục.")
            logger.error(f"   Các cột đang có: {list(df.columns)}")
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
    logger.error(f"✅ Đã đồng bộ thành công {rows_synced} bưu cục vào bảng dim_buucuc.")
    return rows_synced

def clear_caches():
    """Xóa bộ nhớ đệm cache để Dashboard nhận dữ liệu mới lập tức."""
    try:
        from callbacks.utils import clear_query_cache
        from db.connection import clear_db_cache
        from analytics.global_metrics import clear_global_metrics_cache
        clear_query_cache()
        clear_db_cache()
        clear_global_metrics_cache()
        logger.error("🧹 Đã làm sạch bộ nhớ cache của Dashboard.")
    except Exception:
        # Nếu đang chạy độc lập ngoài app thì bỏ qua cache clear
        pass

def main():
    # Cấu hình encoding utf-8 cho Windows console khi in
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    logger.error("🔄 Bắt đầu đồng bộ danh mục từ tệp CSV...")
    if not DB_PATH.exists():
        logger.error(f"❌ Lỗi: Cơ sở dữ liệu không tồn tại tại {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(str(DB_PATH))
    try:
        sync_spdv(conn)
        sync_buucuc(conn)
        clear_caches()
        logger.error("\n🎉 Tất cả danh mục đã được cập nhật thành công!")
    except Exception as e:
        logger.error(f"❌ Lỗi xảy ra trong quá trình đồng bộ: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
