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

    # 4. Bảng agg_daily (Tổng hợp cấp ngày)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agg_daily (
        ngay           DATE    NOT NULL,
        nam            INTEGER NOT NULL,
        thang          INTEGER NOT NULL,
        ma_buu_cuc     TEXT    NOT NULL,
        nhom_dich_vu   TEXT    NOT NULL,
        bk_e           TEXT    NOT NULL,
        tong_doanh_thu    REAL DEFAULT 0,
        tong_san_luong    INTEGER DEFAULT 0,
        so_kh_phat_sinh   INTEGER DEFAULT 0,
        PRIMARY KEY (ngay, ma_buu_cuc, nhom_dich_vu, bk_e)
    );
    """)
    
    # Chỉ mục tối ưu hóa tìm kiếm cho bảng agg_daily
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_agg_daily_date_bc ON agg_daily (ngay, ma_buu_cuc);
    """)
    
    conn.commit()
    logger.info("[Aggregator] Đã tạo hoặc xác minh sự tồn tại của các bảng summary.")

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
    logger.info(f"[Aggregator] Đã rebuild agg_monthly cho T{thang:02d}/{nam} — Đã ghi nhận {inserted_rows} dòng.")
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
    logger.info(f"[Aggregator] Đã rebuild agg_monthly_customer cho T{thang:02d}/{nam} — Đã ghi nhận {inserted_rows} dòng.")
    return inserted_rows

def rebuild_all_monthly(conn):
    """
    Quét tất cả các cặp (nam_du_lieu, thang_du_lieu) có trong transactions và rebuild lại.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT nam_du_lieu, thang_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL AND thang_du_lieu IS NOT NULL")
    pairs = cursor.fetchall()
    
    logger.info(f"[Aggregator] Tìm thấy {len(pairs)} cặp Năm-Tháng cần rebuild.")
    for nam_du_lieu, thang_str in sorted(pairs):
        try:
            # Parse 'T01' -> 1
            thang = int(thang_str[1:])
            rebuild_monthly(conn, nam_du_lieu, thang)
            rebuild_monthly_customer(conn, nam_du_lieu, thang)
        except Exception as e:
            logger.error(f"[Aggregator] [LỖI] Không thể rebuild tháng {thang_str}/{nam_du_lieu}: {e}")

def rebuild_weekly(conn, nam: int, thang_filter: int = None):
    """
    Rebuild dữ liệu cho bảng agg_weekly của năm chỉ định.
    Gồm 2 bước:
    Bước 1: Tổng hợp doanh thu tuần có ngày cụ thể từ transactions (BCCP & HCC chuyển phát).
    Bước 2: Gộp trực tiếp doanh thu tuần từ 4 bảng dịch vụ phụ dựa trên ngày cụ thể (ngày phân rã).
    """
    from config.week_calendar import get_week_list
    cursor = conn.cursor()
    
    # Lấy danh sách các tuần trong năm
    weeks = get_week_list(nam)
    # 1. Xóa dữ liệu cũ của các tuần bị ảnh hưởng
    if thang_filter is not None:
        # Lọc ra các tuần giao thoa với tháng đó (bắt đầu hoặc kết thúc trong tháng)
        weeks = [w for w in weeks if w[1].month == thang_filter or w[2].month == thang_filter]
        if weeks:
            week_nums = [w[0] for w in weeks]
            placeholders = ",".join("?" for _ in week_nums)
            cursor.execute(f"DELETE FROM agg_weekly WHERE nam = ? AND tuan_so IN ({placeholders})", (nam, *week_nums))
    else:
        cursor.execute("DELETE FROM agg_weekly WHERE nam = ?", (nam,))
    logger.info(f"[Aggregator] Đang rebuild agg_weekly cho năm {nam} ({len(weeks)} tuần)...")
    
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
    logger.info(f"[Aggregator] Bước 1: Hoàn tất transactions weekly (BCCP). Đã ghi nhận {total_inserted} records.")
    
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
    logger.info(f"[Aggregator] Bước 2: Hoàn tất gộp weekly cho 4 dịch vụ phụ (HCC/TCBC/PPBL/PHBC) - Đã ghi nhận thêm {total_sub_inserted} records.")
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
    
    logger.info(f"[Aggregator] Đang phân bổ plans_weekly cho năm {nam}...")
    
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
    logger.info(f"[Aggregator] Hoàn tất rebuild plans_weekly {nam}. Đã chèn {total_inserted} dòng.")
    return total_inserted


def rebuild_daily(conn, nam: int, thang_filter: int = None):
    """
    Rebuild dữ liệu cho bảng agg_daily của năm chỉ định.
    Gộp từ bảng transactions và 4 bảng dịch vụ phụ.
    """
    cursor = conn.cursor()
    
    # 1. Xóa dữ liệu cũ
    if thang_filter is not None:
        cursor.execute("DELETE FROM agg_daily WHERE nam = ? AND thang = ?", (nam, thang_filter))
    else:
        cursor.execute("DELETE FROM agg_daily WHERE nam = ?", (nam,))
    conn.commit()
    
    # Hàm hỗ trợ phân loại sơ bộ nhóm dịch vụ (Heuristic) khi thiếu mapping
    def get_rough_nhom_dich_vu(ma_sp):
        ma_sp = str(ma_sp).upper().strip()
        if ma_sp.startswith('HCC'):
            return 'Chuyển phát HCC'
        elif ma_sp.startswith('KT1') or ma_sp.startswith('RTN') or ma_sp.startswith('TTN'):
            return 'Truyền thống'
        elif ma_sp.startswith('CTN'):
            tmdt_codes = {'CTN007', 'CTN008', 'CTN009', 'CTN019', 'CTN020', 'CTN022', 'CTN028', 'CTN031'}
            if ma_sp in tmdt_codes:
                return 'TMĐT'
            return 'Truyền thống'
        elif ma_sp.startswith('ETN'):
            tmdt_ems = {'ETN031', 'ETN037', 'ETN048', 'ETN051'}
            if ma_sp in tmdt_ems:
                return 'TMĐT'
            return 'Truyền thống'
        elif any(ma_sp.startswith(p) for p in ['CQT', 'EQT', 'RQT', 'TQT', 'LQT', 'PRM', 'DHL', 'UPS']):
            return 'Quốc tế'
        return 'Khác'

    # 2. Quét cảnh báo mapping thiếu cho 4 nhóm dịch vụ chính (BCCP & HCC)
    try:
        # Quét từ transactions
        cursor.execute("""
            SELECT DISTINCT t.ten_dich_vu
            FROM transactions t
            LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
            WHERE t.nam_du_lieu = ? 
              AND (d.ma_dich_vu IS NULL OR d.bk_e IS NULL)
        """, (nam,))
        unmapped = set(row[0] for row in cursor.fetchall())
        
        # Quét từ các bảng phụ
        for tbl in ['transactions_hcc', 'transactions_tcbc', 'transactions_ppbl', 'transactions_phbc']:
            cursor.execute(f"""
                SELECT DISTINCT t.ten_dich_vu
                FROM {tbl} t
                LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
                WHERE t.tu_nam = ? 
                  AND (d.ma_dich_vu IS NULL OR d.bk_e IS NULL)
            """, (nam,))
            for row in cursor.fetchall():
                unmapped.add(row[0])
                
        # Phân loại và in cảnh báo
        warnings = []
        for ma_sp in sorted(unmapped):
            cursor.execute("SELECT nhom_dich_vu FROM dim_dichvu WHERE ma_dich_vu = ? OR ten_dich_vu = ?", (ma_sp, ma_sp))
            row = cursor.fetchone()
            nhom = row[0] if row else get_rough_nhom_dich_vu(ma_sp)
            
            if nhom in ['Truyền thống', 'TMĐT', 'Quốc tế', 'Chuyển phát HCC']:
                warnings.append(f"Mã dịch vụ '{ma_sp}' (thuộc nhóm '{nhom}') chưa được cấu hình phân loại BK/E trong CSV mapping.")
                
        if warnings:
            logger.error("\n" + "="*80)
            logger.error(f"[WARNING] PHÁT HIỆN THIẾU MAPPING BK/E TRONG NĂM {nam}:")
            for w in warnings:
                logger.error(f"  ⚠️  {w}")
            logger.error("Vui lòng cập nhật file mapping và chạy lại import / rebuild để sửa chữa số liệu.")
            logger.error("="*80 + "\n")
    except Exception as e:
        logger.error(f"[Aggregator] Lỗi khi quét cảnh báo mapping: {e}")

    logger.info(f"[Aggregator] Đang rebuild agg_daily cho năm {nam} (tháng={thang_filter})...")
    
    # 3. Gộp BCCP (từ transactions)
    thang_cond = ""
    params_trans = [nam, nam]
    if thang_filter is not None:
        thang_cond = " AND CAST(strftime('%m', t.ngay_chap_nhan) as INTEGER) = ?"
        params_trans.append(thang_filter)

    query_trans = """
    INSERT INTO agg_daily (ngay, nam, thang, ma_buu_cuc, nhom_dich_vu, bk_e, tong_doanh_thu, tong_san_luong, so_kh_phat_sinh)
    SELECT 
        t.ngay_chap_nhan as ngay,
        ? as nam,
        CAST(strftime('%m', t.ngay_chap_nhan) as INTEGER) as thang,
        t.ma_buu_cuc,
        COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
        -- [NGHIỆP VỤ] Cột bk_e có 4 giá trị hợp lệ: 'BK', 'E', 'Khác', 'Không phân loại'.
        -- Khi dịch vụ thuộc nhóm chính (TT/TMĐT/Quốc tế/HCC) mà cột bk_e chưa được
        -- điền trong dim_dichvu (= NULL), COALESCE trả về 'Khác' — đây là ĐÚNG NGHIỆP VỤ:
        -- dịch vụ chưa phân loại BK/E được xếp vào nhóm 'Khác'.
        -- Dịch vụ không thuộc 4 nhóm chính → 'Không phân loại' (ví dụ: PHBC, dịch vụ phụ).
        -- KHÔNG SỬA logic này trừ khi Sếp yêu cầu.
        CASE 
            WHEN COALESCE(d.nhom_dich_vu, 'Khác') IN ('Truyền thống', 'TMĐT', 'Quốc tế', 'Chuyển phát HCC') THEN
                COALESCE(d.bk_e, 'Khác')
            ELSE
                'Không phân loại'
        END as bk_e,
        SUM(t.cuoc_tt_tong) as tong_doanh_thu,
        SUM(t.san_luong) as tong_san_luong,
        COUNT(DISTINCT CASE 
            WHEN t.cms IS NOT NULL AND t.cms != '' 
                 AND t.cms NOT LIKE 'VANGLAI_%' 
                 AND LOWER(t.cms) != 'none' 
            THEN t.cms 
        END) as so_kh_phat_sinh
    FROM transactions t
    LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
    WHERE t.nam_du_lieu = ? {thang_cond}
    GROUP BY 
        t.ngay_chap_nhan, 
        t.ma_buu_cuc, 
        COALESCE(d.nhom_dich_vu, 'Khác'),
        CASE 
            WHEN COALESCE(d.nhom_dich_vu, 'Khác') IN ('Truyền thống', 'TMĐT', 'Quốc tế', 'Chuyển phát HCC') THEN
                COALESCE(d.bk_e, 'Khác')
            ELSE
                'Không phân loại'
        END
    """.format(thang_cond=thang_cond)
    
    cursor.execute(query_trans, tuple(params_trans))
    rows_bccp = cursor.rowcount
    conn.commit()
    logger.info(f"[Aggregator] Đã gộp agg_daily từ transactions (BCCP): {rows_bccp} dòng.")

    # 4. Gộp các bảng phụ (HCC, TCBC, PPBL, PHBC) bằng UPSERT
    sub_thang_cond = ""
    params_sub = [nam]
    if thang_filter is not None:
        sub_thang_cond = " WHERE tu_thang = ?"
        # Cần truyền tham số cho từng subquery trong UNION ALL
        # Có 4 subquery, mỗi subquery cần truyền tu_thang = thang_filter
        # Cộng thêm tham số tu_nam ở ngoài
        sub_params = []
        for _ in range(4):
            sub_params.append(thang_filter)
        params_sub = sub_params + [nam]
    else:
        # Nếu không có thang_filter, không truyền gì cho subquery
        pass

    query_sub = """
    INSERT INTO agg_daily (ngay, nam, thang, ma_buu_cuc, nhom_dich_vu, bk_e, tong_doanh_thu, tong_san_luong, so_kh_phat_sinh)
    SELECT 
        printf('%04d-%02d-%02d', t.tu_nam, t.tu_thang, t.tu_ngay) as ngay,
        ? as nam,
        t.tu_thang as thang,
        t.ma_buu_cuc,
        COALESCE(d.nhom_dich_vu, t.ten_dich_vu) as nhom_dich_vu,
        CASE 
            WHEN COALESCE(d.nhom_dich_vu, t.ten_dich_vu) IN ('Truyền thống', 'TMĐT', 'Quốc tế', 'Chuyển phát HCC') THEN
                COALESCE(d.bk_e, 'Khác')
            ELSE
                'Không phân loại'
        END as bk_e,
        SUM(t.doanh_thu) as tong_doanh_thu,
        SUM(t.san_luong) as tong_san_luong,
        0 as so_kh_phat_sinh
    FROM (
        SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_hcc {sub_thang_cond}
        UNION ALL
        SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_tcbc {sub_thang_cond}
        UNION ALL
        SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_ppbl {sub_thang_cond}
        UNION ALL
        SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam FROM transactions_phbc {sub_thang_cond}
    ) t
    LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu OR t.ten_dich_vu = d.ten_dich_vu
    WHERE t.tu_nam = ?
    GROUP BY 
        printf('%04d-%02d-%02d', t.tu_nam, t.tu_thang, t.tu_ngay),
        t.ma_buu_cuc,
        COALESCE(d.nhom_dich_vu, t.ten_dich_vu),
        CASE 
            WHEN COALESCE(d.nhom_dich_vu, t.ten_dich_vu) IN ('Truyền thống', 'TMĐT', 'Quốc tế', 'Chuyển phát HCC') THEN
                COALESCE(d.bk_e, 'Khác')
            ELSE
                'Không phân loại'
        END
    ON CONFLICT(ngay, ma_buu_cuc, nhom_dich_vu, bk_e) DO UPDATE SET
        tong_doanh_thu = tong_doanh_thu + excluded.tong_doanh_thu,
        tong_san_luong = tong_san_luong + excluded.tong_san_luong
    """.format(sub_thang_cond=sub_thang_cond)
    
    # Ở trên ta truyền: ? as nam ở đầu SELECT, và ? ở WHERE t.tu_nam = ?
    # Do đó, danh sách tham số đầy đủ cho cursor.execute là:
    # [nam] + params_sub (chứa 4*thang_filter + [nam])
    # Tổng cộng params cho execute: (nam, params_sub[0], params_sub[1], params_sub[2], params_sub[3], nam)
    # Hãy chuẩn hóa danh sách execute_params cho rõ ràng:
    execute_params = []
    execute_params.append(nam) # ? thứ 1: ? as nam
    if thang_filter is not None:
        execute_params.extend([thang_filter, thang_filter, thang_filter, thang_filter]) # 4 dấu ? trong UNION ALL
    execute_params.append(nam) # ? cuối cùng: WHERE t.tu_nam = ?

    cursor.execute(query_sub, tuple(execute_params))
    rows_sub = cursor.rowcount
    conn.commit()
    logger.info(f"[Aggregator] Đã gộp/UPSERT agg_daily từ 4 bảng phụ: {rows_sub} dòng.")
    return rows_bccp + rows_sub

