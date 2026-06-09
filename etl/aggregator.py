# -*- coding: utf-8 -*-
"""
Module aggregator: Tổng hợp dữ liệu từ transactions sang các bảng summary trung gian.
"""
import sys
import sqlite3
from pathlib import Path
from config.settings import DB_PATH

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
        buu_cuc       TEXT    NOT NULL,
        nhom_dich_vu  TEXT,
        tong_doanh_thu    REAL DEFAULT 0,
        tong_san_luong    INTEGER DEFAULT 0,
        so_kh_phat_sinh   INTEGER DEFAULT 0,
        PRIMARY KEY (nam, thang, buu_cuc, nhom_dich_vu)
    );
    """)
    
    # 2. Bảng agg_monthly_customer
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agg_monthly_customer (
        cms           TEXT    NOT NULL,
        buu_cuc       TEXT    NOT NULL,
        nam           INTEGER NOT NULL,
        thang         INTEGER NOT NULL,
        nhom_dich_vu  TEXT,
        tong_doanh_thu    REAL DEFAULT 0,
        tong_san_luong    INTEGER DEFAULT 0,
        so_giao_dich      INTEGER DEFAULT 0,
        PRIMARY KEY (cms, buu_cuc, nam, thang, nhom_dich_vu)
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
        nhom_dich_vu      TEXT,
        ke_hoach_doanh_thu REAL DEFAULT 0,
        PRIMARY KEY (nam, tuan_so, ma_buu_cuc, nhom_dich_vu)
    );
    """)
    
    conn.commit()
    print("[Aggregator] Đã tạo hoặc xác minh sự tồn tại của các bảng summary.")

def rebuild_monthly(conn, nam: int, thang: int):
    """
    Rebuild dữ liệu cho bảng agg_monthly của tháng và năm chỉ định.
    Gộp dữ liệu thực tế từ 4 bảng giao dịch: transactions, transactions_hcc, transactions_tcbc, transactions_ppbl.
    """
    cursor = conn.cursor()
    thang_str = f"T{thang:02d}"
    
    # Xóa dữ liệu cũ
    cursor.execute("DELETE FROM agg_monthly WHERE nam = ? AND thang = ?", (nam, thang))
    
    # Tính toán và Insert dữ liệu mới
    # Gộp bằng UNION ALL trước khi GROUP BY để có đầy đủ các nhóm dịch vụ con
    query = """
    INSERT INTO agg_monthly (nam, thang, buu_cuc, nhom_dich_vu, tong_doanh_thu, tong_san_luong, so_kh_phat_sinh)
    SELECT nam, thang, buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu), SUM(tong_san_luong), SUM(so_kh_phat_sinh)
    FROM (
        SELECT 
            t.nam_du_lieu as nam,
            ? as thang,
            t.buu_cuc,
            COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
            SUM(t.cuoc_tt_tong) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            COUNT(DISTINCT CASE WHEN t.cms IS NOT NULL AND t.cms != '' AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' THEN t.cms END) as so_kh_phat_sinh
        FROM transactions t
        LEFT JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        GROUP BY t.buu_cuc, COALESCE(d.nhom_dich_vu, 'Khác')
        
        UNION ALL
        
        SELECT 
            t.nam_du_lieu as nam,
            ? as thang,
            t.ma_buu_cuc as buu_cuc,
            t.ten_dich_vu as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_hcc t
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        GROUP BY t.ma_buu_cuc, t.ten_dich_vu
        
        UNION ALL
        
        SELECT 
            t.nam_du_lieu as nam,
            ? as thang,
            t.ma_buu_cuc as buu_cuc,
            t.ten_dich_vu as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_tcbc t
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        GROUP BY t.ma_buu_cuc, t.ten_dich_vu
        
        UNION ALL
        
        SELECT 
            t.nam_du_lieu as nam,
            ? as thang,
            t.ma_buu_cuc as buu_cuc,
            t.ten_dich_vu as nhom_dich_vu,
            SUM(t.doanh_thu) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            0 as so_kh_phat_sinh
        FROM transactions_ppbl t
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        GROUP BY t.ma_buu_cuc, t.ten_dich_vu
    )
    GROUP BY nam, thang, buu_cuc, nhom_dich_vu
    """
    
    params = (
        thang, nam, thang_str,
        thang, nam, thang_str,
        thang, nam, thang_str,
        thang, nam, thang_str
    )
    
    cursor.execute(query, params)
    conn.commit()
    inserted_rows = cursor.rowcount
    print(f"[Aggregator] Đã rebuild agg_monthly cho T{thang:02d}/{nam} — Đã ghi nhận {inserted_rows} dòng.")
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
    INSERT INTO agg_monthly_customer (cms, buu_cuc, nam, thang, nhom_dich_vu, tong_doanh_thu, tong_san_luong, so_giao_dich)
    SELECT 
        t.cms,
        t.buu_cuc,
        t.nam_du_lieu as nam,
        ? as thang,
        COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
        SUM(t.cuoc_tt_tong) as tong_doanh_thu,
        SUM(t.san_luong) as tong_san_luong,
        COUNT(*) as so_giao_dich
    FROM transactions t
    LEFT JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
    WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
      AND t.cms IS NOT NULL AND t.cms != '' 
      AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    GROUP BY t.cms, t.buu_cuc, t.nam_du_lieu, COALESCE(d.nhom_dich_vu, 'Khác')
    """
    cursor.execute(query, (thang, nam, thang_str))
    conn.commit()
    inserted_rows = cursor.rowcount
    print(f"[Aggregator] Đã rebuild agg_monthly_customer cho T{thang:02d}/{nam} — Đã ghi nhận {inserted_rows} dòng.")
    return inserted_rows

def rebuild_all_monthly(conn):
    """
    Quét tất cả các cặp (nam_du_lieu, thang_du_lieu) có trong transactions và rebuild lại.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT nam_du_lieu, thang_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL AND thang_du_lieu IS NOT NULL")
    pairs = cursor.fetchall()
    
    print(f"[Aggregator] Tìm thấy {len(pairs)} cặp Năm-Tháng cần rebuild.")
    for nam_du_lieu, thang_str in sorted(pairs):
        try:
            # Parse 'T01' -> 1
            thang = int(thang_str[1:])
            rebuild_monthly(conn, nam_du_lieu, thang)
            rebuild_monthly_customer(conn, nam_du_lieu, thang)
        except Exception as e:
            print(f"[Aggregator] [LỖI] Không thể rebuild tháng {thang_str}/{nam_du_lieu}: {e}")

def rebuild_weekly(conn, nam: int):
    """
    Rebuild dữ liệu cho bảng agg_weekly của năm chỉ định.
    Gồm 2 bước:
    Bước 1: Tổng hợp doanh thu tuần có ngày cụ thể từ transactions (BCCP & HCC chuyển phát).
    Bước 2: Phân bổ doanh thu/sản lượng của các dịch vụ con (HCC mới, TCBC, PPBL) theo khoảng ngày thô và tính giao thoa ngày thực tế.
    """
    from config.week_calendar import get_week_list
    from datetime import date
    cursor = conn.cursor()
    
    # 1. Xóa dữ liệu cũ của năm đó
    cursor.execute("DELETE FROM agg_weekly WHERE nam = ?", (nam,))
    
    # Lấy danh sách các tuần trong năm
    weeks = get_week_list(nam)
    print(f"[Aggregator] Đang rebuild agg_weekly cho năm {nam} ({len(weeks)} tuần)...")
    
    total_inserted = 0
    
    # BƯỚC 1: Xử lý dữ liệu transactions (BCCP & HCC chuyển phát)
    for w_num, w_start, w_end in weeks:
        start_str = w_start.isoformat()
        end_str = w_end.isoformat()
        
        # Query tổng hợp doanh thu của tuần này từ transactions (dùng nhom_dich_vu con)
        query = """
        INSERT INTO agg_weekly (
            tuan_bat_dau, tuan_ket_thuc, tuan_so, nam, buu_cuc, nhom_dich_vu, 
            tong_doanh_thu, tong_san_luong, so_kh_phat_sinh, so_kh_moi, so_kh_tai_ban
        )
        SELECT 
            ? as tuan_bat_dau,
            ? as tuan_ket_thuc,
            ? as tuan_so,
            ? as nam,
            t.buu_cuc,
            COALESCE(d.nhom_dich_vu, 'Khác') as nhom_dich_vu,
            SUM(t.cuoc_tt_tong) as tong_doanh_thu,
            SUM(t.san_luong) as tong_san_luong,
            COUNT(DISTINCT CASE WHEN t.cms IS NOT NULL AND t.cms != '' AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' THEN t.cms END) as so_kh_phat_sinh,
            0 as so_kh_moi,
            0 as so_kh_tai_ban
        FROM transactions t
        LEFT JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
        WHERE t.ngay_chap_nhan BETWEEN ? AND ?
        GROUP BY t.buu_cuc, COALESCE(d.nhom_dich_vu, 'Khác')
        """
        cursor.execute(query, (start_str, end_str, w_num, nam, start_str, end_str))
        total_inserted += cursor.rowcount
        
    conn.commit()
    print(f"[Aggregator] Bước 1: Hoàn tất transactions weekly (BCCP). Đã ghi nhận {total_inserted} records.")
    
    # BƯỚC 2: Phân bổ dữ liệu theo ngày thô thực tế từ transactions_hcc, transactions_tcbc, transactions_ppbl
    sub_services_data = []
    for table_name in ['transactions_hcc', 'transactions_tcbc', 'transactions_ppbl']:
        cursor.execute(f"""
            SELECT ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong,
                   tu_ngay, tu_thang, tu_nam, den_ngay, den_thang, den_nam
            FROM {table_name}
            WHERE nam_du_lieu = ?
        """, (nam,))
        
        for row in cursor.fetchall():
            ma_buu_cuc, ten_dich_vu, doanh_thu, san_luong, tu_ngay, tu_thang, tu_nam, den_ngay, den_thang, den_nam = row
            sub_services_data.append({
                'buu_cuc': ma_buu_cuc,
                'nhom_dich_vu': ten_dich_vu,
                'doanh_thu': doanh_thu or 0.0,
                'san_luong': san_luong or 0,
                'tu_ngay': tu_ngay or 1,
                'tu_thang': tu_thang or 1,
                'tu_nam': tu_nam or nam,
                'den_ngay': den_ngay or 30,
                'den_thang': den_thang or 12,
                'den_nam': den_nam or nam
            })
            
    # Chuẩn bị một dict để chứa kết quả cộng dồn cho tuần:
    # Key: (tuan_so, buu_cuc, nhom_dich_vu) -> Value: (doanh_thu, san_luong)
    weekly_agg = {}
    
    for item in sub_services_data:
        try:
            ngay_bat_dau = date(item['tu_nam'], item['tu_thang'], item['tu_ngay'])
            ngay_ket_thuc = date(item['den_nam'], item['den_thang'], item['den_ngay'])
        except Exception:
            # Fallback nếu ngày không hợp lệ (ví dụ ngày 31 tháng 2)
            try:
                ngay_bat_dau = date(nam, item['tu_thang'], 1)
                m_end = item['den_thang']
                d_end = 31 if m_end in [1, 3, 5, 7, 8, 10, 12] else (30 if m_end != 2 else 28)
                ngay_ket_thuc = date(nam, m_end, d_end)
            except Exception:
                continue
                
        N = (ngay_ket_thuc - ngay_bat_dau).days + 1
        if N <= 0:
            N = 1
            
        # Tìm tất cả các tuần giao thoa và tính số ngày giao thoa
        intersections = []
        for w_num, w_start, w_end in weeks:
            intersect_start = max(ngay_bat_dau, w_start)
            intersect_end = min(ngay_ket_thuc, w_end)
            if intersect_start <= intersect_end:
                ngay_giao = (intersect_end - intersect_start).days + 1
                intersections.append((w_num, ngay_giao))
                
        # Phân bổ tích lũy để triệt tiêu sai số làm tròn số nguyên
        cum_days = 0
        prev_cum_dt = 0.0
        prev_cum_sl = 0
        
        for w_num, ngay_giao in intersections:
            cum_days += ngay_giao
            
            # Tính tỷ lệ tích lũy
            ratio = cum_days / N
            
            cum_dt = item['doanh_thu'] * ratio
            cum_sl = round(item['san_luong'] * ratio)
            
            # Chênh lệch của tuần này so với tuần trước
            dt_week = cum_dt - prev_cum_dt
            sl_week = cum_sl - prev_cum_sl
            
            # Lưu lại mốc tích lũy
            prev_cum_dt = cum_dt
            prev_cum_sl = cum_sl
            
            key = (w_num, item['buu_cuc'], item['nhom_dich_vu'])
            if key not in weekly_agg:
                weekly_agg[key] = [0.0, 0.0]
            weekly_agg[key][0] += dt_week
            weekly_agg[key][1] += sl_week
                
    # Ghi dữ liệu tuần của các dịch vụ con vào agg_weekly
    insert_weekly_sql = """
    INSERT INTO agg_weekly (
        tuan_bat_dau, tuan_ket_thuc, tuan_so, nam, buu_cuc, nhom_dich_vu,
        tong_doanh_thu, tong_san_luong, so_kh_phat_sinh, so_kh_moi, so_kh_tai_ban
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
    """
    
    week_date_map = {w_num: (w_start, w_end) for w_num, w_start, w_end in weeks}
    batch_insert = []
    
    for (w_num, bc, nhom_dv), (dt, sl) in weekly_agg.items():
        if dt > 0 or sl > 0:
            w_start, w_end = week_date_map[w_num]
            batch_insert.append((
                w_start.isoformat(),
                w_end.isoformat(),
                w_num,
                nam,
                bc,
                nhom_dv,
                dt,
                int(round(sl))
            ))
            
    if batch_insert:
        cursor.executemany(insert_weekly_sql, batch_insert)
        total_inserted += cursor.rowcount
        
    conn.commit()
    print(f"[Aggregator] Bước 2: Hoàn tất phân bổ weekly cho HCC/TCBC/PPBL. Đã ghi nhận tổng cộng {total_inserted} records.")
    return total_inserted

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
    cursor.execute("""
    SELECT thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu, SUM(ke_hoach_doanh_thu) as kh_thang
    FROM plans 
    WHERE nam = ?
    GROUP BY thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu
    """, (nam,))
    
    plans_data = cursor.fetchall()
    if not plans_data:
        print(f"[Aggregator] Không tìm thấy kế hoạch tháng nào trong bảng plans cho năm {nam}. Bỏ qua rebuild_plans_weekly.")
        return 0
        
    # Tổ chức plans_data dưới dạng dict để tra cứu nhanh: {(thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu): kh_thang}
    plans_dict = {}
    for thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu, kh_thang in plans_data:
        plans_dict[(thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu)] = kh_thang
        
    # Tập hợp danh sách tất cả các tổ hợp có trong kế hoạch
    buucuc_dichvu_pairs = set((ma_buu_cuc, nhom_chinh, nhom_dich_vu) for (_, ma_buu_cuc, nhom_chinh, nhom_dich_vu, _) in plans_data)
    
    print(f"[Aggregator] Đang phân bổ plans_weekly cho năm {nam}...")
    
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
    print(f"[Aggregator] Hoàn tất rebuild plans_weekly {nam}. Đã chèn {total_inserted} dòng.")
    return total_inserted
