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
        
    # Tạo danh sách các cột thực tế
    cols = list(df.columns)
    
    # Tìm cột ma_spdv, ten_spdv
    if "ma_spdv" not in cols or "ten_spdv" not in cols:
        logger.error(f"❌ Lỗi: Thiếu cột ma_spdv hoặc ten_spdv trong file CSV mapping sản phẩm.")
        logger.error(f"   Các cột đang có: {cols}")
        return 0
        
    # Tìm cột nhom_dich_vu (hỗ trợ cả 'loại dịch vụ' hoặc 'nhom_dich_vu')
    nhom_dv_col = None
    for c in ["nhom_dich_vu", "loại dịch vụ"]:
        if c in cols:
            nhom_dv_col = c
            break
    if not nhom_dv_col:
        logger.error(f"❌ Lỗi: Thiếu cột nhom_dich_vu hoặc loại dịch vụ trong file CSV mapping sản phẩm.")
        logger.error(f"   Các cột đang có: {cols}")
        return 0
        
    # Tìm cột bk_e (hỗ trợ cả 'bk/e' hoặc 'bk_e')
    bk_e_col = None
    for c in ["bk/e", "bk_e"]:
        if c in cols:
            bk_e_col = c
            break

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
        logger.info(f"💾 Đã tạo file backup bảng dim_dichvu tại: {backup_file}")
    except Exception as e:
        logger.error(f"⚠️ Cảnh báo: Không thể backup bảng dim_dichvu: {e}")

    cursor = conn.cursor()

    # Thêm cột bk_e vào bảng dim_dichvu nếu chưa tồn tại
    try:
        cursor.execute("PRAGMA table_info(dim_dichvu)")
        table_cols = [row[1] for row in cursor.fetchall()]
        if 'bk_e' not in table_cols:
            logger.info("➕ Thêm cột bk_e vào bảng dim_dichvu...")
            cursor.execute("ALTER TABLE dim_dichvu ADD COLUMN bk_e TEXT")
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Lỗi khi thêm cột bk_e vào dim_dichvu: {e}")
        return 0

    # 2. Xóa các dòng BCCP và mã HCC (HCC001-HCC004) để thực hiện nạp mới (TRUNCATE)
    # Giữ lại các dòng seed data cho HCC (không phải dạng mã HCC001...), TCBC, PPBL
    try:
        cursor.execute("""
            DELETE FROM dim_dichvu
            WHERE (nhom_chinh = 'BCCP' AND ma_dich_vu != 'PHBC_DEFAULT')
               OR (nhom_chinh = 'HCC' AND ma_dich_vu LIKE 'HCC%')
        """)
        conn.commit()
        logger.info("🧹 Đã làm sạch các dòng BCCP và mã HCC cũ trong bảng dim_dichvu.")
    except Exception as e:
        logger.error(f"❌ Lỗi khi làm sạch dữ liệu cũ trong dim_dichvu: {e}")
        return 0

    # 3. Ghi vào dim_dichvu
    rows_synced = 0
    for _, row in df.iterrows():
        ma_spdv = str(row["ma_spdv"]).strip()
        if not ma_spdv or pd.isna(row["ma_spdv"]):
            continue
            
        ten_spdv = str(row["ten_spdv"]).strip()
        
        # Nhóm dịch vụ con
        nhom_dich_vu = str(row[nhom_dv_col]).strip()
        if nhom_dich_vu == 'Hành chính công':
            nhom_dich_vu = 'Chuyển phát HCC'
            
        # Xác định nhóm chính
        if nhom_dich_vu == 'Chuyển phát HCC' or ma_spdv.startswith('HCC'):
            nhom_chinh = 'HCC'
        else:
            nhom_chinh = 'BCCP'
            
        # Xác định bk_e
        bk_e_val = 'Khác'
        if bk_e_col and not pd.isna(row[bk_e_col]):
            bk_e_val = str(row[bk_e_col]).strip()
            # Theo yêu cầu của Sếp, nếu trống thì cho vào 'Khác'
            if not bk_e_val or bk_e_val.lower() == 'nan' or bk_e_val == '':
                bk_e_val = 'Khác'
        
        cursor.execute(
            """INSERT OR REPLACE INTO dim_dichvu (nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu, bk_e)
               VALUES (?, ?, ?, ?, ?)""",
            (nhom_chinh, ma_spdv, ten_spdv, nhom_dich_vu, bk_e_val),
        )
        rows_synced += 1

    conn.commit()
    logger.info(f"✅ Đã đồng bộ thành công {rows_synced} sản phẩm vào bảng dim_dichvu.")
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
                if "ma_buu_cuc" in df_temp.columns:
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
    required_cols = ['ma_buu_cuc', 'ten_buu_cuc', 'ma_bdx', 'ten_bdx', 'ten_cum']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"❌ Lỗi: Cột '{col}' không tồn tại trong file CSV mapping bưu cục.")
            logger.error(f"   Các cột đang có: {list(df.columns)}")
            return 0

    cursor = conn.cursor()
    rows_synced = 0
    for _, row in df.iterrows():
        ma_buu_cuc = str(row.get('ma_buu_cuc', '')).strip()
        if not ma_buu_cuc or pd.isna(row.get('ma_buu_cuc')):
            continue
            
        cursor.execute(
            """INSERT OR REPLACE INTO dim_buucuc (ma_buu_cuc, ten_buu_cuc, ma_bdx, ten_bdx, ten_cum)
               VALUES (?, ?, ?, ?, ?)""",
            (
                ma_buu_cuc,
                str(row.get('ten_buu_cuc', '')).strip(),
                str(row.get('ma_bdx', '')).strip(),
                str(row.get('ten_bdx', '')).strip(),
                str(row.get('ten_cum', '')).strip()
            ),
        )
        rows_synced += 1

    conn.commit()
    logger.info(f"✅ Đã đồng bộ thành công {rows_synced} bưu cục vào bảng dim_buucuc.")
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
        logger.info("🧹 Đã làm sạch bộ nhớ cache của Dashboard.")
    except Exception:
        # Nếu đang chạy độc lập ngoài app thì bỏ qua cache clear
        pass

def main():
    # Cấu hình encoding utf-8 cho Windows console khi in
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    logger.info("🔄 Bắt đầu đồng bộ danh mục từ tệp CSV...")
    if not DB_PATH.exists():
        logger.error(f"❌ Lỗi: Cơ sở dữ liệu không tồn tại tại {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(str(DB_PATH))
    try:
        sync_spdv(conn)
        sync_buucuc(conn)
        clear_caches()
        logger.info("\n🎉 Tất cả danh mục đã được cập nhật thành công!")
    except Exception as e:
        logger.error(f"❌ Lỗi xảy ra trong quá trình đồng bộ: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
