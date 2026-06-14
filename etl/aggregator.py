# -*- coding: utf-8 -*-
"""
Module aggregator: Tổng hợp dữ liệu từ transactions sang các bảng summary trung gian.
"""
import sys
import sqlite3
from pathlib import Path
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


# Đảm bảo in tiếng Việt chính xác trên Windows Console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def create_summary_tables(conn):
    """
    Tạo các bảng summary trung gian nếu chưa tồn tại.
    """
    cursor = conn.cursor()
    
    # 1. Bảng agg_monthly
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agg_monthly (
        nam           INTEGER NOT NULL,
        thang         INTEGER NOT NULL,
        ma_buu_cuc    TEXT    NOT NULL,
        nhom_dich_vu  TEXT,
        tong_doanh_thu    REAL DEFAULT 0,
        tong_san_luong    INTEGER DEFAULT 0,
        so_kh_phat_sinh   INTEGER DEFAULT 0,
        PRIMARY KEY (nam, thang, ma_buu_cuc, nhom_dich_vu)
    );
    """)
    
    # 2. Bảng agg_monthly_customer
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agg_monthly_customer (
        cms           TEXT    NOT NULL,
        ma_buu_cuc    TEXT    NOT NULL,
        nam           INTEGER NOT NULL,
        thang         INTEGER NOT NULL,
        nhom_dich_vu  TEXT,
        tong_doanh_thu    REAL DEFAULT 0,
        tong_san_luong    INTEGER DEFAULT 0,
        so_giao_dich      INTEGER DEFAULT 0,
        PRIMARY KEY (cms, ma_buu_cuc, nam, thang, nhom_dich_vu)
    );
    """)
    
    # 3. Bảng plans_weekly (từ TIP-db-002)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans_weekly (
        nam               INTEGER NOT NULL,
        tuan_so           INTEGER NOT NULL,
        tuan_bat_dau      DATE    NOT NULL,
        tuan_ket_thuc     DATE    NOT NULL,
        ma_buu_cuc        TEXT    NOT NULL,
        nhom_chinh        TEXT,
        nhom_dich_vu      TEXT,
        ke_hoach_doanh_thu REAL DEFAULT 0,
        PRIMARY KEY (nam, tuan_so, ma_buu_cuc, nhom_chinh, nhom_dich_vu)
    );
    """)
    
    conn.commit()
    logger.error("[Aggregator] Đã tạo hoặc xác minh sự tồn tại của các bảng summary.")

def rebuild_monthly(conn, nam: int, thang: int):
    """
    Rebuild dữ liệu cho bảng agg_monthly của tháng và năm chỉ định.
    Gộp dữ liệu thực tế từ 5 bảng giao dịch: transactions và 4 bảng dịch vụ phụ.
    """
    cursor = conn.cursor()
    thang_str = f"T{thang:02d}"
    
    # Xóa dữ liệu cũ
    cursor.execute("DELETE FROM agg_monthly WHERE nam = ? AND thang = ?", (nam, thang))
    
    # Tính toán và Insert dữ liệu mới
    # Gộp bằng UNION ALL trước khi GROUP BY để có đầy đủ các nhóm dịch vụ con
    query = """
    INSERT INTO agg_monthly (nam, thang, ma_buu_cuc, nhom_dich_vu, tong_doanh_thu, tong_san_luong, so_kh_phat_sinh)
    SELECT nam, thang, ma_buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu), SUM(tong_san_luong), SUM(so_kh_phat_sinh)
    FROM (
        SELECT 
            t.nam_du_lieu as nam,
            ? as thang,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
            SUM(t.cuoc_tt_tong) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            COUNT(DISTINCT CASE WHEN t.cms IS NOT NULL AND t.cms != '' AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' THEN t.cms END) as so_kh_phat_sinh
        FROM transactions t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, 'Khác')
        
        UNION ALL
        
        SELECT 
            t.tu_nam as nam,
            ? as thang,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, t.ten_dich_vu) as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_hcc t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
        WHERE t.tu_nam = ? AND t.tu_thang = ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, t.ten_dich_vu)
        
        UNION ALL
        
        SELECT 
            t.tu_nam as nam,
            ? as thang,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, t.ten_dich_vu) as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_tcbc t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
        WHERE t.tu_nam = ? AND t.tu_thang = ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, t.ten_dich_vu)
        
        UNION ALL
        
        SELECT 
            t.tu_nam as nam,
            ? as thang,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, t.ten_dich_vu) as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_ppbl t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
        WHERE t.tu_nam = ? AND t.tu_thang = ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, t.ten_dich_vu)

        UNION ALL
        
        SELECT 
            t.tu_nam as nam,
            ? as thang,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, t.ten_dich_vu) as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_phbc t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
        WHERE t.tu_nam = ? AND t.tu_thang = ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, t.ten_dich_vu)
    )
    GROUP BY nam, thang, ma_buu_cuc, nhom_dich_vu
    """
    
    params = (
        thang, nam, thang_str,
        thang, nam, thang,
        thang, nam, thang,
        thang, nam, thang,
        thang, nam, thang
    )
    
    cursor.execute(query, params)
    conn.commit()
    inserted_rows = cursor.rowcount
    logger.error(f"[Aggregator] Đã rebuild agg_monthly cho T{thang:02d}/{nam} — Đã ghi nhận {inserted_rows} dòng.")
    return inserted_rows

def rebuild_monthly_customer(conn, nam: int, thang: int):
    """
    Rebuild dữ liệu cho bảng agg_monthly_customer của tháng và năm chỉ định.
    """
    cursor = conn.cursor()
    thang_str = f"T{thang:02d}"
    
    # Xóa dữ liệu cũ
    cursor.execute("DELETE FROM agg_monthly_customer WHERE nam = ? AND thang = ?", (nam, thang))
    
    # Tính toán và Insert dữ liệu mới
    # Chỉ tính các cms hợp lệ
    query = """
    INSERT INTO agg_monthly_customer (cms, ma_buu_cuc, nam, thang, nhom_dich_vu, tong_doanh_thu, tong_san_luong, so_giao_dich)
    SELECT 
        t.cms,
        t.ma_buu_cuc,
        t.nam_du_lieu as nam,
        ? as thang,
        COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
        SUM(t.cuoc_tt_tong) as tong_doanh_thu,
        SUM(t.san_luong) as tong_san_luong,
        COUNT(*) as so_giao_dich
    FROM transactions t
    LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
    WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
      AND t.cms IS NOT NULL AND t.cms != '' 
      AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    GROUP BY t.cms, t.ma_buu_cuc, t.nam_du_lieu, COALESCE(d.nhom_dich_vu, 'Khác')
    """
    cursor.execute(query, (thang, nam, thang_str))
    conn.commit()
    inserted_rows = cursor.rowcount
    logger.error(f"[Aggregator] Đã rebuild agg_monthly_customer cho T{thang:02d}/{nam} — Đã ghi nhận {inserted_rows} dòng.")
    return inserted_rows

def rebuild_all_monthly(conn):
    """
    Quét tất cả các cặp (nam_du_lieu, thang_du_lieu) có trong transactions và rebuild lại.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT nam_du_lieu, thang_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL AND thang_du_lieu IS NOT NULL")
    pairs = cursor.fetchall()
    
    logger.error(f"[Aggregator] Tìm thấy {len(pairs)} cặp Năm-Tháng cần rebuild.")
    for nam_du_lieu, thang_str in sorted(pairs):
        try:
            # Parse 'T01' -> 1
            thang = int(thang_str[1:])
            rebuild_monthly(conn, nam_du_lieu, thang)
            rebuild_monthly_customer(conn, nam_du_lieu, thang)
        except Exception as e:
            logger.error(f"[Aggregator] [LỖI] Không thể rebuild tháng {thang_str}/{nam_du_lieu}: {e}")

def rebuild_weekly(conn, nam: int):
    """
    Rebuild dữ liệu cho bảng agg_weekly của năm chỉ định.
    Gồm 2 bước:
    Bước 1: Tổng hợp doanh thu tuần có ngày cụ thể từ transactions (BCCP & HCC chuyển phát).
    Bước 2: Gộp trực tiếp doanh thu tuần từ 4 bảng dịch vụ phụ dựa trên ngày cụ thể (ngày phân rã).
    """
    from config.week_calendar import get_week_list
    cursor = conn.cursor()
    
    # 1. Xóa dữ liệu cũ của năm đó
    cursor.execute("DELETE FROM agg_weekly WHERE nam = ?", (nam,))
    
    # Lấy danh sách các tuần trong năm
    weeks = get_week_list(nam)
    logger.error(f"[Aggregator] Đang rebuild agg_weekly cho năm {nam} ({len(weeks)} tuần)...")
    
    total_inserted = 0
    
    # BƯỚC 1: Xử lý dữ liệu transactions (BCCP & HCC chuyển phát)
    for w_num, w_start, w_end in weeks:
        start_str = w_start.isoformat()
        end_str = w_end.isoformat()
        
        # Query tổng hợp doanh thu của tuần này từ transactions (dùng nhom_dich_vu con)
        query = """
        INSERT INTO agg_weekly (
            tuan_bat_dau, tuan_ket_thuc, tuan_so, nam, ma_buu_cuc, nhom_dich_vu, 
            tong_doanh_thu, tong_san_luong, so_kh_phat_sinh, so_kh_moi, so_kh_tai_ban
        )
        SELECT 
            ? as tuan_bat_dau,
            ? as tuan_ket_thuc,
            ? as tuan_so,
            ? as nam,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
            SUM(t.cuoc_tt_tong) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            COUNT(DISTINCT CASE WHEN t.cms IS NOT NULL AND t.cms != '' AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' THEN t.cms END) as so_kh_phat_sinh,
            0 as so_kh_moi,
            0 as so_kh_tai_ban
        FROM transactions t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
        WHERE t.ngay_chap_nhan BETWEEN ? AND ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, 'Khác')
        """
        cursor.execute(query, (start_str, end_str, w_num, nam, start_str, end_str))
        total_inserted += cursor.rowcount
        
    conn.commit()
    logger.error(f"[Aggregator] Bước 1: Hoàn tất transactions weekly (BCCP). Đã ghi nhận {total_inserted} records.")
    
    # BƯỚC 2: Gộp trực tiếp tuần cho 4 dịch vụ phụ (HCC, TCBC, PPBL, PHBC) dựa trên ngày cụ thể
    total_sub_inserted = 0
    for w_num, w_start, w_end in weeks:
        start_str = w_start.isoformat()
        end_str = w_end.isoformat()
        
        query_sub = """
        INSERT INTO agg_weekly (
            tuan_bat_dau, tuan_ket_thuc, tuan_so, nam, ma_buu_cuc, nhom_dich_vu, 
            tong_doanh_thu, tong_san_luong, so_kh_phat_sinh, so_kh_moi, so_kh_tai_ban
        )
        SELECT 
            ? as tuan_bat_dau,
            ? as tuan_ket_thuc,
            ? as tuan_so,
            ? as nam,
            t.ma_buu_cuc,
            COALESCE(d.nhom_dich_vu, t.ten_dich_vu) as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh,
            0 as so_kh_moi,
            0 as so_kh_tai_ban
        FROM (
            SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_hcc
            UNION ALL
            SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_tcbc
            UNION ALL
            SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_ppbl
            UNION ALL
            SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_phbc
        ) t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
        WHERE t.tu_nam = ? AND printf('%04d-%02d-%02d', t.tu_nam, t.tu_thang, t.tu_ngay) BETWEEN ? AND ?
        GROUP BY t.ma_buu_cuc, COALESCE(d.nhom_dich_vu, t.ten_dich_vu)
        ON CONFLICT(tuan_bat_dau, ma_buu_cuc, nhom_dich_vu) DO UPDATE SET
            tong_doanh_thu = tong_doanh_thu + excluded.tong_doanh_thu,
            tong_san_luong = tong_san_luong + excluded.tong_san_luong
        """
        cursor.execute(query_sub, (start_str, end_str, w_num, nam, nam, start_str, end_str))
        total_sub_inserted += cursor.rowcount
        
    conn.commit()
    logger.error(f"[Aggregator] Bước 2: Hoàn tất gộp weekly cho 4 dịch vụ phụ (HCC/TCBC/PPBL/PHBC) - Đã ghi nhận thêm {total_sub_inserted} records.")
    return total_inserted + total_sub_inserted

def rebuild_plans_weekly(conn, nam: int):
    """
    Rebuild dữ liệu cho bảng plans_weekly của năm chỉ định.
    Phân bổ kế hoạch tháng sang tuần theo tỷ lệ số ngày trong tuần của tháng đó.
    """
    from config.week_calendar import allocate_weekly_plan
    cursor = conn.cursor()
    
    # 1. Xóa dữ liệu plans_weekly của năm đó
    cursor.execute("DELETE FROM plans_weekly WHERE nam = ?", (nam,))
    
    # Lấy phân bổ các tuần
    allocations = allocate_weekly_plan(nam)
    
    # Đọc tất cả kế hoạch tháng của năm đó
    # NOTE: Không JOIN dim_dichvu vì nhom_dich_vu trong plans đã là giá trị chuẩn
    # (ví dụ: 'Truyền thống', 'TMĐT', 'Quốc tế'). JOIN OR nhiều cột gây nhân bản SUM.
    cursor.execute("""
    SELECT p.thang, p.ma_buu_cuc, p.nhom_chinh, p.nhom_dich_vu, SUM(p.ke_hoach_doanh_thu) as kh_thang
    FROM plans p
    WHERE p.nam = ?
    GROUP BY p.thang, p.ma_buu_cuc, p.nhom_chinh, p.nhom_dich_vu
    """, (nam,))
    
    plans_data = cursor.fetchall()
    if not plans_data:
        logger.error(f"[Aggregator] Không tìm thấy kế hoạch tháng nào trong bảng plans cho năm {nam}. Bỏ qua rebuild_plans_weekly.")
        return 0
        
    # Tổ chức plans_data dưới dạng dict để tra cứu nhanh: {(thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu): kh_thang}
    plans_dict = {}
    for thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu, kh_thang in plans_data:
        plans_dict[(thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu)] = kh_thang
        
    # Tập hợp danh sách tất cả các tổ hợp có trong kế hoạch
    buucuc_dichvu_pairs = set((ma_buu_cuc, nhom_chinh, nhom_dich_vu) for (_, ma_buu_cuc, nhom_chinh, nhom_dich_vu, _) in plans_data)
    
    logger.error(f"[Aggregator] Đang phân bổ plans_weekly cho năm {nam}...")
    
    total_inserted = 0
    
    for w_num, w_start, w_end, months_dist in allocations:
        start_str = w_start.isoformat()
        end_str = w_end.isoformat()
        
        for ma_buu_cuc, nhom_chinh, nhom_dich_vu in buucuc_dichvu_pairs:
            ke_hoach_tuan = 0.0
            has_value = False
            
            for thang, nam_cua_thang, days_count, total_days in months_dist:
                kh_thang = plans_dict.get((thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu), 0.0)
                if kh_thang > 0:
                    ke_hoach_tuan += kh_thang * (days_count / total_days)
                    has_value = True
                    
            if has_value and ke_hoach_tuan > 0:
                cursor.execute("""
                INSERT INTO plans_weekly (nam, tuan_so, tuan_bat_dau, tuan_ket_thuc, ma_buu_cuc, nhom_chinh, nhom_dich_vu, ke_hoach_doanh_thu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nam, w_num, start_str, end_str, ma_buu_cuc, nhom_chinh, nhom_dich_vu, ke_hoach_tuan))
                total_inserted += 1
                
    conn.commit()
    logger.error(f"[Aggregator] Hoàn tất rebuild plans_weekly {nam}. Đã chèn {total_inserted} dòng.")
    return total_inserted
