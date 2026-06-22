# -*- coding: utf-8 -*-
"""
Script chạy lại toàn bộ database BCCP từ dữ liệu nguồn thô (Du-lieu-nguon)
áp dụng logic V2 mới (loại bỏ sản lượng trùng ở phần điều chỉnh).
"""

import os
import sys
import glob
import sqlite3
import logging
import time
from pathlib import Path

# Đảm bảo in tiếng Việt chính xác trên Windows Console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Cấu hình logging ra console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("update_db_raw")

# Định nghĩa đường dẫn dự án và database
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.settings import DB_PATH
from etl.importer import import_raw_excel_file, _auto_aggregate_after_import as real_auto_aggregate

# Monkey patch để tắt tự động rebuild sau mỗi file trong quá trình bulk import
import etl.importer
etl.importer._auto_aggregate_after_import = lambda *args, **kwargs: None

SOURCE_DIR = Path(r"E:\OneDrive\TTKD - Công việc hàng ngày\0. KHM, tai ban hang thang\chi-tiet-KH-hopdong-loaidichvu\du-lieu-goc-4.2.4-casreport\Du-lieu-nguon")

def main():
    logger.info("=" * 80)
    logger.info("BẮT ĐẦU TIẾN TRÌNH CẬP NHẬT LẠI TOÀN BỘ DATABASE BCCP TỪ NGUỒN THÔ (V2)")
    logger.info(f" - Đường dẫn DB: {DB_PATH}")
    logger.info(f" - Thư mục nguồn thô: {SOURCE_DIR}")
    logger.info("=" * 80)

    if not DB_PATH.exists():
        logger.error(f"Không tìm thấy file database tại: {DB_PATH}")
        sys.exit(1)
        
    if not SOURCE_DIR.exists():
        logger.error(f"Không tìm thấy thư mục nguồn dữ liệu thô tại: {SOURCE_DIR}")
        sys.exit(1)

    # 1. Kết nối CSDL và xóa dữ liệu transactions cũ của 2025 và 2026
    logger.info("Bước 1: Đang dọn dẹp dữ liệu cũ năm 2025 và 2026 trong bảng transactions...")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Đếm số dòng trước khi xóa
    cursor.execute("SELECT count(*) FROM transactions WHERE nam_du_lieu IN (2025, 2026)")
    old_rows = cursor.fetchone()[0]
    logger.info(f" -> Tìm thấy {old_rows:,} dòng dữ liệu cũ trong bảng transactions.")
    
    if old_rows > 0:
        cursor.execute("DELETE FROM transactions WHERE nam_du_lieu IN (2025, 2026)")
        conn.commit()
        logger.info(" -> Đã xóa thành công dữ liệu cũ của năm 2025 và 2026.")
    else:
        logger.info(" -> Bảng transactions không chứa dữ liệu cũ của năm 2025 và 2026.")
    conn.close()

    # 2. Quét tất cả các file Excel thô trong thư mục nguồn
    logger.info("\nBước 2: Quét toàn bộ file dữ liệu Excel thô trong thư mục nguồn...")
    excel_files = []
    
    # Tìm kiếm đệ quy
    for ext in ("*.xls", "*.xlsx"):
        for filepath in glob.glob(os.path.join(str(SOURCE_DIR), "**", ext), recursive=True):
            filename = os.path.basename(filepath)
            # Bỏ qua file tạm của Excel
            if filename.startswith("~$"):
                continue
            excel_files.append(filepath)
            
    # Sắp xếp các file theo đường dẫn để xử lý tuần tự
    excel_files.sort()
    
    total_files = len(excel_files)
    logger.info(f" -> Tìm thấy tổng cộng {total_files} file dữ liệu thô cần import.")
    
    if total_files == 0:
        logger.error("Không tìm thấy file dữ liệu nào để import!")
        sys.exit(1)

    # 3. Tiến hành import từng file
    logger.info("\nBước 3: Bắt đầu import dữ liệu...")
    start_time = time.time()
    
    imported_count = 0
    failed_files = []
    
    for idx, filepath in enumerate(excel_files, 1):
        rel_path = os.path.relpath(filepath, str(SOURCE_DIR))
        logger.info(f"[{idx}/{total_files}] Đang import file: {rel_path}")
        
        try:
            # Sử dụng mode='append' vì dữ liệu cũ đã được xóa sạch từ đầu
            # thang=None để hàm tự động phát hiện từ ngày chấp nhận trong file
            res = import_raw_excel_file(str(DB_PATH), filepath, thang=None, mode='append')
            
            logger.info(f"   => Thành công! Tháng phát hiện: {res.get('thang')}, Dòng nạp: {res.get('inserted')}/{res.get('total_rows')}")
            imported_count += 1
        except Exception as e:
            logger.error(f"   ❌ THẤT BẠI khi xử lý file {rel_path}: {e}")
            failed_files.append((rel_path, str(e)))

    # 4. Tự động tính toán lại (Rebuild) các bảng tổng hợp
    logger.info("\nBước 4: Tự động tính toán lại dữ liệu tổng hợp (Summary Tables)...")
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT nam_du_lieu, thang_du_lieu FROM transactions WHERE nam_du_lieu IN (2025, 2026)")
        db_pairs = cursor.fetchall()
        conn.close()
        
        rebuild_pairs = []
        for y, m in db_pairs:
            if y is not None and m is not None:
                try:
                    m_int = int(m[1:]) if str(m).startswith('T') else int(m)
                    rebuild_pairs.append((y, m_int))
                except ValueError:
                    pass
                    
        rebuild_pairs.sort()
        logger.info(f"Các cặp Tháng/Năm cần rebuild: {rebuild_pairs}")
        
        if rebuild_pairs:
            real_auto_aggregate(str(DB_PATH), 'BCCP', rebuild_pairs)
            logger.info("✅ Đã hoàn tất rebuild các bảng tổng hợp thành công.")
        else:
            logger.warning("Không tìm thấy cặp Tháng/Năm nào trong database để rebuild.")
            
    except Exception as ex_ref:
        logger.error(f"❌ Lỗi tự động rebuild bảng tổng hợp: {ex_ref}")

    # Tổng kết
    end_time = time.time()
    elapsed = end_time - start_time
    logger.info("\n" + "=" * 80)
    logger.info("TIẾN TRÌNH HOÀN TẤT")
    logger.info(f" - Tổng thời gian chạy: {elapsed:.2f} giây")
    logger.info(f" - File thành công: {imported_count}/{total_files}")
    
    if failed_files:
        logger.warning(f" - Số file thất bại: {len(failed_files)}")
        for f, err in failed_files:
            logger.warning(f"   * {f}: {err}")
    else:
        logger.info(" - Tất cả các file đã được nạp thành công 100%!")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
