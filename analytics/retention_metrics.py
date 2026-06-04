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
    Trả về set các mã CMS là Khách hàng Hiện hữu (KHHH) của tháng target.
    KHHH của tháng T là các khách hàng có giao dịch trong ít nhất 1 trong 3 tháng trước đó (T-1, T-2, T-3).
    Loại trừ vãng lai. Lọc theo địa lý nếu có yêu cầu.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tính 3 tháng trước đó
    lookback = []
    curr_y, curr_m = nam, thang
    for _ in range(3):
        curr_y, curr_m = get_prev_month(curr_y, curr_m)
        lookback.append((curr_y, f"T{curr_m:02d}"))
        
    query = """
        SELECT DISTINCT t.cms 
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE (
            (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
        )
        AND t.cms IS NOT NULL AND t.cms != '' 
        AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params = []
    for y, m_str in lookback:
        params.extend([y, m_str])
        
    if cum and cum != "Tất cả":
        query += " AND b.ten_cum = ?"
        params.append(cum)
    if bdx and bdx != "Tất cả":
        query += " AND b.ten_bdx = ?"
        params.append(bdx)
        
    try:
        cursor.execute(query, params)
        cms_set = {row[0].strip() for row in cursor.fetchall() if row[0]}
    except Exception as e:
        print(f"Lỗi trong get_khhh_list: {e}")
        cms_set = set()
    finally:
        conn.close()
        
    return cms_set

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
    """
    Lọc KHHH có nguy cơ rời bỏ:
    - Điều kiện 1: Đang là KHHH (có GD trong 3 tháng trước: T-1, T-2, T-3)
    - Điều kiện 2A: DT/SL giảm > 20% so trung bình 3 tháng trước
    - Điều kiện 2B: HOẶC không phát sinh GD trong 7 ngày gần nhất
    
    Returns: DataFrame(cms, ten_buu_cuc, dt_ky_nay, dt_tb_3thang, pct_giam, ngay_gd_cuoi, ly_do)
    """
    from datetime import datetime
    import calendar
    
    # 1. Lấy danh sách KHHH trong tháng/năm này
    khhh_set = get_khhh_list(db_path, year, month, cum, bdx)
    if not khhh_set:
        return pd.DataFrame(columns=['cms', 'ten_buu_cuc', 'dt_ky_nay', 'dt_tb_3thang', 'pct_giam', 'ngay_gd_cuoi', 'ly_do'])
        
    # Tính 3 tháng trước đó
    lookback = []
    curr_y, curr_m = year, month
    for _ in range(3):
        curr_y, curr_m = get_prev_month(curr_y, curr_m)
        lookback.append((curr_y, f"T{curr_m:02d}"))
        
    conn = sqlite3.connect(db_path)
    
    # Lấy ngày giao dịch cuối cùng của tháng này
    thang_str = f"T{month:02d}"
    cursor = conn.cursor()
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

    # Query DT trung bình 3 tháng trước
    query_3m = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) / 3.0 as dt_tb, MAX(b.ten_bdx) as bdx
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE (
            (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
        )
        AND t.cms IS NOT NULL AND t.cms != ''
        AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_3m = []
    for y, m_str in lookback:
        params_3m.extend([y, m_str])
        
    if cum and cum != "Tất cả":
        query_3m += " AND b.ten_cum = ?"
        params_3m.append(cum)
    if bdx and bdx != "Tất cả":
        query_3m += " AND b.ten_bdx = ?"
        params_3m.append(bdx)
        
    query_3m += " GROUP BY t.cms"
    
    df_3m = pd.read_sql_query(query_3m, conn, params=params_3m)
    dict_3m_dt = dict(zip(df_3m['cms'], df_3m['dt_tb']))
    dict_bdx = dict(zip(df_3m['cms'], df_3m['bdx']))
    
    # Query DT tháng này và ngày GD cuối cùng
    query_cur = """
        SELECT t.cms, SUM(t.cuoc_tt_tong) as dt_cur, MAX(t.ngay_chap_nhan) as max_date_cur, MAX(b.ten_bdx) as bdx
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
    dict_cur_date = dict(zip(df_cur['cms'], df_cur['max_date_cur']))
    
    # Cập nhật thêm bưu cục từ tháng này nếu tháng trước chưa có
    for c, b in zip(df_cur['cms'], df_cur['bdx']):
        if c not in dict_bdx or not dict_bdx[c]:
            dict_bdx[c] = b
            
    # Lấy ngày GD cuối cùng trong quá khứ nếu tháng này không có GD
    query_last_all = """
        SELECT t.cms, MAX(t.ngay_chap_nhan) as last_all
        FROM transactions t
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE (
            (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
            OR (t.nam_du_lieu = ? AND t.thang_du_lieu = ?)
        )
        AND t.cms IS NOT NULL AND t.cms != ''
        AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none'
    """
    params_all = [year, thang_str]
    for y, m_str in lookback:
        params_all.extend([y, m_str])
        
    if cum and cum != "Tất cả":
        query_last_all += " AND b.ten_cum = ?"
        params_all.append(cum)
    if bdx and bdx != "Tất cả":
        query_last_all += " AND b.ten_bdx = ?"
        params_all.append(bdx)
        
    query_last_all += " GROUP BY t.cms"
    df_last_all = pd.read_sql_query(query_last_all, conn, params=params_all)
    dict_last_all = dict(zip(df_last_all['cms'], df_last_all['last_all']))
    
    conn.close()
    
    alerts = []
    for cms in khhh_set:
        dt_tb_3thang = dict_3m_dt.get(cms, 0.0)
        dt_ky_nay = dict_cur_dt.get(cms, 0.0)
        
        if dt_tb_3thang > 0:
            pct_giam = ((dt_ky_nay - dt_tb_3thang) / dt_tb_3thang) * 100.0
        else:
            pct_giam = -100.0 if dt_ky_nay == 0 else 0.0
            
        # Ngày giao dịch cuối
        ngay_gd_cuoi = dict_cur_date.get(cms)
        if not ngay_gd_cuoi:
            ngay_gd_cuoi = dict_last_all.get(cms, "-")
            
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
            except Exception as e:
                pass
        else:
            is_inactive = True
            reasons.append("Không phát sinh GD")
            
        if is_dt_reduced or is_inactive:
            ly_do = ", ".join(reasons)
            alerts.append({
                'cms': cms,
                'ten_buu_cuc': dict_bdx.get(cms, "-"),
                'dt_ky_nay': dt_ky_nay,
                'dt_tb_3thang': dt_tb_3thang,
                'pct_giam': pct_giam,
                'ngay_gd_cuoi': ngay_gd_cuoi,
                'ly_do': ly_do
            })
            
    df_alerts = pd.DataFrame(alerts)
    if not df_alerts.empty:
        df_alerts = df_alerts.sort_values(by='pct_giam', ascending=True)
    return df_alerts

