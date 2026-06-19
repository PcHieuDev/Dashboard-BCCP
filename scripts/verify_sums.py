# -*- coding: utf-8 -*-
import sys
import sqlite3
from pathlib import Path

# Đảm bảo in tiếng Việt chính xác trên Windows Console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH

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


def verify():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    logger.error("=== ĐỐI CHIẾU SỐ LIỆU DOANH THU & SẢN LƯỢNG NĂM 2026 ===")
    
    # 1. Đối chiếu tổng hợp tháng (agg_monthly) với bảng thô
    logger.error("\n--- 1. BẢNG TỔNG HỢP THÁNG (agg_monthly) vs BẢNG THÔ ---")
    
    # Doanh thu / sản lượng trong transactions_hcc 2026
    raw_hcc_dt, raw_hcc_sl = c.execute("SELECT SUM(doanh_thu), SUM(san_luong) FROM transactions_hcc WHERE nam_du_lieu = 2026").fetchone()
    raw_hcc_dt = raw_hcc_dt or 0.0
    raw_hcc_sl = raw_hcc_sl or 0
    
    # Doanh thu / sản lượng trong agg_monthly cho các nhóm dịch vụ thuộc transactions_hcc
    # (Tên dịch vụ con trong transactions_hcc)
    c.execute("SELECT DISTINCT ten_dich_vu FROM transactions_hcc WHERE nam_du_lieu = 2026")
    hcc_services = [r[0] for r in c.fetchall()]
    
    agg_hcc_dt, agg_hcc_sl = 0.0, 0
    if hcc_services:
        placeholders = ','.join('?' for _ in hcc_services)
        query = f"""
            SELECT SUM(tong_doanh_thu), SUM(tong_san_luong) 
            FROM agg_monthly 
            WHERE nam = 2026 AND nhom_dich_vu IN ({placeholders})
        """
        agg_hcc_dt, agg_hcc_sl = c.execute(query, hcc_services).fetchone()
        agg_hcc_dt = agg_hcc_dt or 0.0
        agg_hcc_sl = agg_hcc_sl or 0
        
    logger.error(f"HCC Thô:   Doanh thu = {raw_hcc_dt:,.2f}, Sản lượng = {raw_hcc_sl:,}")
    logger.error(f"HCC Tháng: Doanh thu = {agg_hcc_dt:,.2f}, Sản lượng = {agg_hcc_sl:,}")
    logger.error(f"-> Chênh lệch Doanh thu = {agg_hcc_dt - raw_hcc_dt:.6f}")
    logger.error(f"-> Chênh lệch Sản lượng = {agg_hcc_sl - raw_hcc_sl}")
    
    # 2. Đối chiếu tổng hợp tuần (agg_weekly) với bảng thô
    logger.error("\n--- 2. BẢNG TỔNG HỢP TUẦN (agg_weekly) vs BẢNG THÔ ---")
    
    agg_week_hcc_dt, agg_week_hcc_sl = 0.0, 0
    if hcc_services:
        placeholders = ','.join('?' for _ in hcc_services)
        query = f"""
            SELECT SUM(tong_doanh_thu), SUM(tong_san_luong) 
            FROM agg_weekly 
            WHERE nam = 2026 AND nhom_dich_vu IN ({placeholders})
        """
        agg_week_hcc_dt, agg_week_hcc_sl = c.execute(query, hcc_services).fetchone()
        agg_week_hcc_dt = agg_week_hcc_dt or 0.0
        agg_week_hcc_sl = agg_week_hcc_sl or 0
        
    logger.error(f"HCC Thô:  Doanh thu = {raw_hcc_dt:,.2f}, Sản lượng = {raw_hcc_sl:,}")
    logger.error(f"HCC Tuần: Doanh thu = {agg_week_hcc_dt:,.2f}, Sản lượng = {agg_week_hcc_sl:,}")
    logger.error(f"-> Chênh lệch Doanh thu = {agg_week_hcc_dt - raw_hcc_dt:,.6f}")
    logger.error(f"-> Chênh lệch Sản lượng = {agg_week_hcc_sl - raw_hcc_sl}")
    
    # 3. Đối chiếu tổng hợp ngày (agg_daily) với bảng thô
    logger.error("\n--- 3. BẢNG TỔNG HỢP NGÀY (agg_daily) vs BẢNG THÔ NĂM 2026 ---")
    
    # 3.1. Tính tổng từ các nguồn thô
    # Từ transactions (BCCP)
    raw_bccp_dt, raw_bccp_sl = c.execute("SELECT SUM(cuoc_tt_tong), SUM(san_luong) FROM transactions WHERE nam_du_lieu = 2026").fetchone()
    raw_bccp_dt = raw_bccp_dt or 0.0
    raw_bccp_sl = raw_bccp_sl or 0
    
    # Từ các bảng phụ (HCC, TCBC, PPBL, PHBC)
    raw_subs_dt, raw_subs_sl = c.execute("""
        SELECT SUM(doanh_thu), SUM(san_luong) 
        FROM (
            SELECT doanh_thu, san_luong, tu_nam FROM transactions_hcc
            UNION ALL
            SELECT doanh_thu, san_luong, tu_nam FROM transactions_tcbc
            UNION ALL
            SELECT doanh_thu, san_luong, tu_nam FROM transactions_ppbl
            UNION ALL
            SELECT doanh_thu, san_luong, tu_nam FROM transactions_phbc
        ) 
        WHERE tu_nam = 2026
    """).fetchone()
    raw_subs_dt = raw_subs_dt or 0.0
    raw_subs_sl = raw_subs_sl or 0
    
    total_raw_dt = raw_bccp_dt + raw_subs_dt
    total_raw_sl = raw_bccp_sl + raw_subs_sl
    
    # 3.2. Tính tổng từ bảng agg_daily
    agg_daily_dt, agg_daily_sl = c.execute("SELECT SUM(tong_doanh_thu), SUM(tong_san_luong) FROM agg_daily WHERE nam = 2026").fetchone()
    agg_daily_dt = agg_daily_dt or 0.0
    agg_daily_sl = agg_daily_sl or 0
    
    logger.error(f"Tổng Thô 2026 (BCCP + Phụ): Doanh thu = {total_raw_dt:,.2f}, Sản lượng = {total_raw_sl:,}")
    logger.error(f"Tổng Ngày 2026 (agg_daily):  Doanh thu = {agg_daily_dt:,.2f}, Sản lượng = {agg_daily_sl:,}")
    logger.error(f"-> Chênh lệch Doanh thu = {agg_daily_dt - total_raw_dt:,.6f}")
    logger.error(f"-> Chênh lệch Sản lượng = {agg_daily_sl - total_raw_sl}")
    
    conn.close()

if __name__ == "__main__":
    verify()
