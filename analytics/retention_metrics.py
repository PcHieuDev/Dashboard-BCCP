# -*- coding: utf-8 -*-
"""
Module tính toán các chỉ số duy trì khách hàng hiện hữu (retention) và biến động doanh thu.
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt ra console không bị lỗi trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def get_prev_month(nam: int, thang: int) -> tuple[int, int]:
    """Trả về (năm, tháng) của tháng liền trước."""
    m_prev = thang - 1
    y_prev = nam
    if m_prev == 0:
        m_prev = 12
        y_prev = nam - 1
    return y_prev, m_prev

def get_khhh_list(db_path: str, nam: int, thang: int, cum: str = None, bdx: str = None) -> set[str]:
    """
    KHHH của tháng T là các khách hàng CÓ giao dịch trong tháng T trừ đi Khách hàng mới của tháng T.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    thang_str = f"T{thang:02d}"
    
    # 1. Lấy KH có giao dịch tháng này
    query_gd = """
        SELECT DISTINCT t.cms 
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        AND t.cms IS NOT NULL AND t.cms != '' 
        AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_gd = [nam, thang_str]
    
    if cum and cum != "Tất cả":
        query_gd += " AND b.ten_cum = ?"
        params_gd.append(cum)
    if bdx and bdx != "Tất cả":
        query_gd += " AND b.ten_bdx = ?"
        params_gd.append(bdx)
        
    try:
        cursor.execute(query_gd, params_gd)
        cms_gd = {row[0].strip() for row in cursor.fetchall() if row[0]}
    except Exception as e:
        print(f"Lỗi truy vấn GD: {e}")
        cms_gd = set()
        
    # 2. Lấy KH mới tháng này
    query_new = """
        SELECT DISTINCT nc.cms 
        FROM new_customers nc
        LEFT JOIN dim_buucuc b ON nc.buu_cuc = b.ma_bc
        WHERE nc.nam = ? AND nc.thang = ?
        AND nc.cms IS NOT NULL AND nc.cms != ''
    """
    params_new = [nam, thang]
    
    if cum and cum != "Tất cả":
        query_new += " AND b.ten_cum = ?"
        params_new.append(cum)
    if bdx and bdx != "Tất cả":
        query_new += " AND b.ten_bdx = ?"
        params_new.append(bdx)
        
    try:
        cursor.execute(query_new, params_new)
        cms_new = {row[0].strip() for row in cursor.fetchall() if row[0]}
    except Exception as e:
        print(f"Lỗi truy vấn KH mới: {e}")
        cms_new = set()
        
    conn.close()
    
    # 3. KHHH = (1) - (2)
    return cms_gd - cms_new

def get_retention_stats(db_path: str, nam: int, thang: int, cum: str = None, bdx: str = None) -> dict:
    """
    Tính toán các chỉ số duy trì khách hàng hiện hữu:
    - SL KHHH tháng trước (T-1)
    - Số KH duy trì được ở tháng này (T)
    - Số KH mất đi ở tháng này
    - Tỷ lệ duy trì khách hàng (SL)
    - Doanh thu KHHH tháng trước ở kỳ T-1
    - Doanh thu của KH duy trì phát sinh ở kỳ T
    - Tỷ lệ duy trì doanh thu
    """
    y_prev, m_prev = get_prev_month(nam, thang)
    thang_str = f"T{thang:02d}"
    thang_prev_str = f"T{m_prev:02d}"
    
    # 1. Tập KHHH tháng trước (T-1)
    khhh_prev = get_khhh_list(db_path, y_prev, m_prev, cum, bdx)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Doanh thu của các CMS trong tháng target (T)
    query_cur = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) 
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
          AND t.cms IS NOT NULL AND t.cms != '' 
          AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_cur = [nam, thang_str]
    if cum and cum != "Tất cả":
        query_cur += " AND b.ten_cum = ?"
        params_cur.append(cum)
    if bdx and bdx != "Tất cả":
        query_cur += " AND b.ten_bdx = ?"
        params_cur.append(bdx)
    query_cur += " GROUP BY t.cms"
    
    cursor.execute(query_cur, params_cur)
    cms_current_revenue = {row[0].strip(): float(row[1] or 0) for row in cursor.fetchall() if row[0]}
    cms_current = set(cms_current_revenue.keys())
    
    # 3. Doanh thu của các CMS trong tháng trước (T-1)
    query_prev = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) 
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
          AND t.cms IS NOT NULL AND t.cms != '' 
          AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_prev = [y_prev, thang_prev_str]
    if cum and cum != "Tất cả":
        query_prev += " AND b.ten_cum = ?"
        params_prev.append(cum)
    if bdx and bdx != "Tất cả":
        query_prev += " AND b.ten_bdx = ?"
        params_prev.append(bdx)
    query_prev += " GROUP BY t.cms"
    
    cursor.execute(query_prev, params_prev)
    cms_prev_revenue = {row[0].strip(): float(row[1] or 0) for row in cursor.fetchall() if row[0]}
    conn.close()
    
    # 4. Tính các chỉ số
    len_prev = len(khhh_prev)
    retained_cms = khhh_prev & cms_current
    retained_count = len(retained_cms)
    lost_count = len(khhh_prev - cms_current)
    
    retention_rate_sl = (retained_count / len_prev * 100) if len_prev > 0 else 0.0
    
    dt_prev = sum(cms_prev_revenue.get(cms, 0.0) for cms in khhh_prev)
    dt_retained = sum(cms_current_revenue.get(cms, 0.0) for cms in retained_cms)
    
    retention_rate_dt = (dt_retained / dt_prev * 100) if dt_prev > 0 else 0.0
    
    return {
        'khhh_prev_count': len_prev,
        'retained_count': retained_count,
        'lost_count': lost_count,
        'retention_rate_sl': retention_rate_sl,
        'dt_prev': dt_prev,
        'dt_retained': dt_retained,
        'retention_rate_dt': retention_rate_dt
    }

def get_khhh_changes(db_path: str, nam: int, thang: int, cum: str = None, bdx: str = None) -> dict:
    """
    Phân tích biến động của tập khách hàng hiện hữu trong tháng target (T):
    - DT tăng: KH có trong KHHH tháng T và DT(T) > DT(T-1) > 0
    - DT giảm: KH có trong KHHH tháng T và 0 < DT(T) < DT(T-1)
    - Mất: KH thuộc KHHH tháng trước (T-1) nhưng không phát sinh giao dịch ở tháng T (DT(T)=0, DT(T-1)>0)
    - Duy trì: KH có trong KHHH tháng T và DT(T) == DT(T-1) > 0 hoặc các trường hợp khác.
    """
    y_prev, m_prev = get_prev_month(nam, thang)
    thang_str = f"T{thang:02d}"
    thang_prev_str = f"T{m_prev:02d}"
    
    # Lấy tập KHHH của tháng target (T) và tháng trước (T-1)
    khhh_curr = get_khhh_list(db_path, nam, thang, cum, bdx)
    khhh_prev = get_khhh_list(db_path, y_prev, m_prev, cum, bdx)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Doanh thu tháng target T
    query_cur = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) 
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
          AND t.cms IS NOT NULL AND t.cms != '' 
          AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_cur = [nam, thang_str]
    if cum and cum != "Tất cả":
        query_cur += " AND b.ten_cum = ?"
        params_cur.append(cum)
    if bdx and bdx != "Tất cả":
        query_cur += " AND b.ten_bdx = ?"
        params_cur.append(bdx)
    query_cur += " GROUP BY t.cms"
    
    cursor.execute(query_cur, params_cur)
    cms_curr_rev = {row[0].strip(): float(row[1] or 0) for row in cursor.fetchall() if row[0]}
    
    # Doanh thu tháng trước T-1
    query_prev = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) 
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
          AND t.cms IS NOT NULL AND t.cms != '' 
          AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_prev = [y_prev, thang_prev_str]
    if cum and cum != "Tất cả":
        query_prev += " AND b.ten_cum = ?"
        params_prev.append(cum)
    if bdx and bdx != "Tất cả":
        query_prev += " AND b.ten_bdx = ?"
        params_prev.append(bdx)
    query_prev += " GROUP BY t.cms"
    
    cursor.execute(query_prev, params_prev)
    cms_prev_rev = {row[0].strip(): float(row[1] or 0) for row in cursor.fetchall() if row[0]}
    conn.close()
    
    # Phân loại biến động
    tang_count = 0
    tang_dt_change = 0.0
    
    giam_count = 0
    giam_dt_change = 0.0
    
    mat_count = 0
    mat_dt_lost = 0.0
    
    duytri_count = 0
    
    # 1. Phân loại tăng / giảm / duy trì cho các KHHH tháng T
    # (Đã giao dịch trong T và thuộc diện KHHH tháng T)
    for cms in khhh_curr:
        dt_curr = cms_curr_rev.get(cms, 0.0)
        dt_prev = cms_prev_rev.get(cms, 0.0)
        
        if dt_curr > 0:
            if dt_prev > 0:
                if dt_curr > dt_prev:
                    tang_count += 1
                    tang_dt_change += (dt_curr - dt_prev)
                elif dt_curr < dt_prev:
                    giam_count += 1
                    giam_dt_change += (dt_curr - dt_prev)
                else:
                    duytri_count += 1
            else:
                # KHHH tháng T phát sinh giao dịch tháng T nhưng tháng T-1 không phát sinh (do giao dịch ở T-2 hoặc T-3)
                # Xếp vào nhóm Duy trì/Quay lại
                duytri_count += 1
                
    # 2. Nhóm Mất: Các CMS thuộc KHHH tháng trước (T-1) nhưng không phát sinh giao dịch ở tháng T (DT(T) == 0)
    for cms in khhh_prev:
        dt_curr = cms_curr_rev.get(cms, 0.0)
        dt_prev = cms_prev_rev.get(cms, 0.0)
        
        if dt_curr == 0 and dt_prev > 0:
            mat_count += 1
            mat_dt_lost += (-dt_prev)
            
    return {
        'tang': {'count': tang_count, 'total_dt_change': tang_dt_change},
        'giam': {'count': giam_count, 'total_dt_change': giam_dt_change},
        'mat': {'count': mat_count, 'total_dt_change': mat_dt_lost},
        'duy_tri': {'count': duytri_count, 'total_dt_change': 0.0}
    }

def get_churn_alerts(db_path: str, year: int, month: int, cum: str = None, bdx: str = None) -> pd.DataFrame:
    from datetime import datetime
    import calendar
    
    y_prev, m_prev = get_prev_month(year, month)
    thang_str = f"T{month:02d}"
    thang_prev_str = f"T{m_prev:02d}"
    
    # 1. Lấy danh sách KHHH của tháng T-1 (những người có thể rời bỏ ở tháng T)
    khhh_prev = get_khhh_list(db_path, y_prev, m_prev, cum, bdx)
    if not khhh_prev:
        return pd.DataFrame(columns=['cms', 'ten_buu_cuc', 'dt_ky_nay', 'dt_tb_3thang', 'pct_giam', 'ngay_gd_cuoi', 'ly_do'])
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lấy ngày giao dịch cuối cùng của tháng này
    cursor.execute("""
        SELECT MAX(ngay_chap_nhan) 
        FROM transactions 
        WHERE nam_du_lieu = ? AND thang_du_lieu = ?
    """, [year, thang_str])
    row_max = cursor.fetchone()
    max_date_str = row_max[0] if row_max and row_max[0] else None
    
    if max_date_str:
        try:
            max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
        except:
            max_date = datetime(year, month, 1)
    else:
        max_date = datetime(year, month, calendar.monthrange(year, month)[1])
        max_date_str = max_date.strftime("%Y-%m-%d")

    # Query DT tháng T-1
    query_prev = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) as dt_prev, MAX(t.ngay_chap_nhan) as last_date, MAX(b.ten_bdx) as bdx
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        AND t.cms IS NOT NULL AND t.cms != ''
        AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_prev = [y_prev, thang_prev_str]
    if cum and cum != "Tất cả":
        query_prev += " AND b.ten_cum = ?"
        params_prev.append(cum)
    if bdx and bdx != "Tất cả":
        query_prev += " AND b.ten_bdx = ?"
        params_prev.append(bdx)
    query_prev += " GROUP BY t.cms"
    
    df_prev = pd.read_sql_query(query_prev, conn, params=params_prev)
    dict_prev_dt = dict(zip(df_prev['cms'], df_prev['dt_prev']))
    dict_prev_date = dict(zip(df_prev['cms'], df_prev['last_date']))
    dict_bdx = dict(zip(df_prev['cms'], df_prev['bdx']))
    
    # Query DT tháng T
    query_cur = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) as dt_cur, MAX(t.ngay_chap_nhan) as last_date, MAX(b.ten_bdx) as bdx
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ?
        AND t.cms IS NOT NULL AND t.cms != ''
        AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_cur = [year, thang_str]
    if cum and cum != "Tất cả":
        query_cur += " AND b.ten_cum = ?"
        params_cur.append(cum)
    if bdx and bdx != "Tất cả":
        query_cur += " AND b.ten_bdx = ?"
        params_cur.append(bdx)
    query_cur += " GROUP BY t.cms"
    
    df_cur = pd.read_sql_query(query_cur, conn, params=params_cur)
    dict_cur_dt = dict(zip(df_cur['cms'], df_cur['dt_cur']))
    dict_cur_date = dict(zip(df_cur['cms'], df_cur['last_date']))
    
    for c, b in zip(df_cur['cms'], df_cur['bdx']):
        if c not in dict_bdx or not dict_bdx[c]:
            dict_bdx[c] = b
            
    conn.close()
    
    alerts = []
    for cms in khhh_prev:
        dt_t_minus_1 = dict_prev_dt.get(cms, 0.0)
        dt_ky_nay = dict_cur_dt.get(cms, 0.0)
        
        if dt_t_minus_1 > 0:
            pct_giam = ((dt_ky_nay - dt_t_minus_1) / dt_t_minus_1) * 100.0
        else:
            pct_giam = -100.0 if dt_ky_nay == 0 else 0.0
            
        # Ngày giao dịch cuối
        ngay_gd_cuoi = dict_cur_date.get(cms)
        if not ngay_gd_cuoi:
            ngay_gd_cuoi = dict_prev_date.get(cms, "-")
            
        reasons = []
        is_dt_reduced = (pct_giam < -20.0)
        if is_dt_reduced:
            reasons.append(f"DT giảm {abs(pct_giam):.1f}%")
            
        is_inactive = False
        if ngay_gd_cuoi and ngay_gd_cuoi != "-":
            try:
                last_dt = datetime.strptime(ngay_gd_cuoi, "%Y-%m-%d")
                delta_days = (max_date - last_dt).days
                if delta_days > 7:
                    is_inactive = True
                    reasons.append(f"Không GD {delta_days} ngày")
            except:
                pass
        else:
            is_inactive = True
            reasons.append("Không phát sinh GD")
            
        if is_dt_reduced or is_inactive:
            alerts.append({
                'cms': cms,
                'ten_buu_cuc': dict_bdx.get(cms, "-"),
                'dt_ky_nay': dt_ky_nay,
                'dt_tb_3thang': dt_t_minus_1,
                'pct_giam': pct_giam,
                'ngay_gd_cuoi': ngay_gd_cuoi,
                'ly_do': ", ".join(reasons)
            })
            
    df_alerts = pd.DataFrame(alerts)
    if not df_alerts.empty:
        df_alerts = df_alerts.sort_values(by='pct_giam', ascending=True)
    return df_alerts

