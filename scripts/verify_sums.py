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

def verify():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    print("=== ĐỐI CHIẾU SỐ LIỆU DOANH THU & SẢN LƯỢNG NĂM 2026 ===")
    
    # 1. Đối chiếu tổng hợp tháng (agg_monthly) với bảng thô
    print("\n--- 1. BẢNG TỔNG HỢP THÁNG (agg_monthly) vs BẢNG THÔ ---")
    
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
        
    print(f"HCC Thô:   Doanh thu = {raw_hcc_dt:,.2f}, Sản lượng = {raw_hcc_sl:,}")
    print(f"HCC Tháng: Doanh thu = {agg_hcc_dt:,.2f}, Sản lượng = {agg_hcc_sl:,}")
    print(f"-> Chênh lệch Doanh thu = {agg_hcc_dt - raw_hcc_dt:.6f}")
    print(f"-> Chênh lệch Sản lượng = {agg_hcc_sl - raw_hcc_sl}")
    
    # 2. Đối chiếu tổng hợp tuần (agg_weekly) với bảng thô
    print("\n--- 2. BẢNG TỔNG HỢP TUẦN (agg_weekly) vs BẢNG THÔ ---")
    
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
        
    print(f"HCC Thô:  Doanh thu = {raw_hcc_dt:,.2f}, Sản lượng = {raw_hcc_sl:,}")
    print(f"HCC Tuần: Doanh thu = {agg_week_hcc_dt:,.2f}, Sản lượng = {agg_week_hcc_sl:,}")
    print(f"-> Chênh lệch Doanh thu = {agg_week_hcc_dt - raw_hcc_dt:,.6f}")
    print(f"-> Chênh lệch Sản lượng = {agg_week_hcc_sl - raw_hcc_sl}")
    
    conn.close()

if __name__ == "__main__":
    verify()
