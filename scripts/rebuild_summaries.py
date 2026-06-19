# -*- coding: utf-8 -*-
"""
Script rebuild toàn bộ summary tables cho dự án Dashboard BCCP.
Sử dụng:
    python scripts/rebuild_summaries.py
    python scripts/rebuild_summaries.py --year 2025
    python scripts/rebuild_summaries.py --year 2026
"""

import sys
import sqlite3
import argparse
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
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    try:
        from config.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Rebuild toàn bộ dữ liệu summary tables.")
    parser.main_year = parser.add_argument(
        "--year", 
        type=int, 
        help="Chỉ định năm cụ thể để rebuild tuần/kế hoạch tuần (Ví dụ: 2025 hoặc 2026)"
    )
    args = parser.parse_args()
    
    start_time = time.time()
    
    db_file = str(DB_PATH)
    logger.error(f"=== BẮT ĐẦU REBUILD SUMMARY TABLES ===")
    logger.error(f"Đường dẫn Database: {db_file}")
    
    conn = sqlite3.connect(db_file)
    
    try:
        # 1. Tạo các bảng nếu chưa có
        logger.error("\n--- BƯỚC 1: Tạo/Kiểm tra các bảng summary ---")
        create_summary_tables(conn)
        
        # 2. Rebuild các bảng tổng hợp tháng
        logger.error("\n--- BƯỚC 2: Rebuild các bảng tổng hợp theo tháng (agg_monthly & agg_monthly_customer) ---")
        rebuild_all_monthly(conn)
        
        # Xác định danh sách năm cần rebuild weekly
        years_to_rebuild = []
        if args.year:
            years_to_rebuild = [args.year]
        else:
            # Tự động lấy tất cả các năm có dữ liệu giao dịch
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT nam_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL")
            years_to_rebuild = sorted([row[0] for row in cursor.fetchall()])
            
        # 3. Rebuild các bảng tuần
        logger.error(f"\n--- BƯỚC 3: Rebuild bảng tổng hợp theo tuần (agg_weekly) cho các năm: {years_to_rebuild} ---")
        for yr in years_to_rebuild:
            rebuild_weekly(conn, yr)
            
        # 4. Phân bổ kế hoạch tuần
        logger.error(f"\n--- BƯỚC 4: Phân bổ kế hoạch tuần (plans_weekly) cho các năm: {years_to_rebuild} ---")
        for yr in years_to_rebuild:
            rebuild_plans_weekly(conn, yr)
            
        # 4.5. Rebuild các bảng ngày
        logger.error(f"\n--- BƯỚC 4.5: Rebuild bảng tổng hợp theo ngày (agg_daily) cho các năm: {years_to_rebuild} ---")
        for yr in years_to_rebuild:
            rebuild_daily(conn, yr)
            
        # 5. Tính toán lại khách hàng mới
        logger.error("\n--- BƯỚC 5: Tính toán lại dữ liệu khách hàng mới (new_customers) ---")
        # Đóng kết nối tạm thời vì populate_historical_new_customers tự mở kết nối riêng
        conn.close()
        populate_historical_new_customers(db_file)
        
    except Exception as e:
        logger.error(f"\n[LỖI] Quá trình rebuild gặp sự cố: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except:
                pass
        sys.exit(1)
        
    end_time = time.time()
    elapsed = end_time - start_time
    logger.error(f"\n=== HOÀN TẤT REBUILD SUMMARY TABLES ===")
    logger.error(f"Tổng thời gian xử lý: {elapsed:.2f} giây (~{elapsed/60:.2f} phút).")

if __name__ == "__main__":
    main()
