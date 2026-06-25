# -*- coding: utf-8 -*-
"""
Script xóa dữ liệu của 4 bảng dịch vụ phụ (HCC, PHBC, PPBL, TCBC) và rebuild toàn bộ summary tables.
Sử dụng:
    python scripts/clear_sub_services.py
"""

import sys
import sqlite3
import time
from pathlib import Path

# Đảm bảo in tiếng Việt chính xác trên Windows Console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Thêm thư mục gốc vào path để import
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH
from etl.backup import backup_database
from etl.aggregator import (
    create_summary_tables,
    rebuild_all_monthly,
    rebuild_weekly,
    rebuild_plans_weekly,
    rebuild_daily
)
from analytics.new_customer_calculator import populate_historical_new_customers

import logging
try:
    from config.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


def main():
    start_time = time.time()
    db_file = str(DB_PATH)

    logger.info("=== BẮT ĐẦU QUÁ TRÌNH XÓA DỮ LIỆU DỊCH VỤ PHỤ & REBUILD SUMMARY ===")
    logger.info(f"Database đích: {db_file}")

    # Bước 1: Sao lưu cơ sở dữ liệu
    logger.info("\n--- BƯỚC 1: Sao lưu cơ sở dữ liệu ---")
    backup_file = backup_database(db_file)
    if backup_file:
        logger.info(f">>> Sao lưu thành công! Bản sao lưu lưu tại: {backup_file}")
    else:
        logger.error(">>> [CẢNH BÁO] Không thể tự động sao lưu. Tiếp tục thực hiện nhưng cần cẩn thận.")

    # Kết nối CSDL
    conn = sqlite3.connect(db_file)
    # Thiết lập busy_timeout để tránh lỗi database is locked khi chạy song song
    conn.execute("PRAGMA busy_timeout=30000;")
    cursor = conn.cursor()

    try:
        # Bước 2: Xóa dữ liệu các bảng dịch vụ phụ
        logger.info("\n--- BƯỚC 2: Xóa dữ liệu 4 bảng phụ ---")
        target_tables = [
            'transactions_hcc',
            'transactions_phbc',
            'transactions_ppbl',
            'transactions_tcbc'
        ]
        
        for tbl in target_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            count_before = cursor.fetchone()[0]
            
            cursor.execute(f"DELETE FROM {tbl}")
            conn.commit()
            
            logger.info(f"  * Đã xóa {count_before} dòng từ bảng '{tbl}' (Hiện tại còn: 0 dòng).")

        # Bước 3: Rebuild các bảng tổng hợp tháng
        logger.info("\n--- BƯỚC 3: Rebuild các bảng tổng hợp theo tháng (agg_monthly & agg_monthly_customer) ---")
        rebuild_all_monthly(conn)

        # Xác định danh sách năm cần rebuild weekly/daily
        cursor.execute("SELECT DISTINCT nam_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL")
        years_to_rebuild = sorted([row[0] for row in cursor.fetchall()])

        # Bước 4: Rebuild các bảng tuần
        logger.info(f"\n--- BƯỚC 4: Rebuild bảng tổng hợp theo tuần (agg_weekly) cho các năm: {years_to_rebuild} ---")
        for yr in years_to_rebuild:
            rebuild_weekly(conn, yr)

        # Bước 5: Phân bổ kế hoạch tuần
        logger.info(f"\n--- BƯỚC 5: Phân bổ kế hoạch tuần (plans_weekly) cho các năm: {years_to_rebuild} ---")
        for yr in years_to_rebuild:
            rebuild_plans_weekly(conn, yr)

        # Bước 6: Rebuild các bảng ngày
        logger.info(f"\n--- BƯỚC 6: Rebuild bảng tổng hợp theo ngày (agg_daily) cho các năm: {years_to_rebuild} ---")
        for yr in years_to_rebuild:
            rebuild_daily(conn, yr)

    except Exception as e:
        logger.error(f"\n[LỖI] Quá trình xóa và rebuild gặp sự cố: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

    # Bước 7: Tính toán lại khách hàng mới (tự mở kết nối riêng trong module)
    logger.info("\n--- BƯỚC 7: Tính toán lại dữ liệu khách hàng mới (new_customers) ---")
    try:
        populate_historical_new_customers(db_file)
    except Exception as e:
        logger.error(f"\n[LỖI] Bước 7 gặp sự cố: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    end_time = time.time()
    elapsed = end_time - start_time
    logger.info(f"\n=== HOÀN TẤT QUÁ TRÌNH XÓA VÀ REBUILD SUMMARY TABLES ===")
    logger.info(f"Tổng thời gian xử lý: {elapsed:.2f} giây (~{elapsed/60:.2f} phút).")


if __name__ == "__main__":
    main()
