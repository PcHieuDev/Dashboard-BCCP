# -*- coding: utf-8 -*-
"""
Module tính toán các chỉ số duy trì khách hàng hiện hữu (retention) và biến động doanh thu.
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path

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

def get_prev_period_info(period_type, period_value, year):
    """Tìm kỳ trước và năm tương ứng"""
    import config.week_calendar as calendar_helper
    if period_type == 'Tháng':
        if period_value == 1:
            return 12, year - 1
        return period_value - 1, year
    else: # Tuần
        if period_value == 1:
            prev_yr = year - 1
            weeks = calendar_helper.get_week_list(prev_yr)
            prev_val = weeks[-1][0] if weeks else 52
            return prev_val, prev_yr
        return period_value - 1, year


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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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
        logger.error(f"Lỗi truy vấn GD: {e}")
        cms_gd = set()
        
    # 2. Lấy KH mới tháng này
    query_new = """
        SELECT DISTINCT nc.cms 
        FROM new_customers nc
        LEFT JOIN dim_buucuc b ON nc.ma_buu_cuc = b.ma_buu_cuc
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
        logger.error(f"Lỗi truy vấn KH mới: {e}")
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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
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


def get_khhh_changes_v2(db_path: str, nam: int, thang: int, cum: str = None, bdx: str = None) -> dict:
    """
    Phân tích biến động hiện hữu theo định nghĩa mới v2.0:
    - Tăng: DT(T) > DT(T-1) > 0
    - Giảm: 0 < DT(T) < DT(T-1)
    - Rời bỏ (Churn): 3 tháng gần nhất (T-1, T-2, T-3) có doanh thu dương, nhưng tháng T không có doanh thu (DT(T) = 0)
    - Duy trì (Ổn định): DT(T) == DT(T-1) và cả hai đều dương (> 0)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Xác định 3 tháng liền trước (T-1, T-2, T-3)
    lookback = []
    curr_m, curr_y = thang, nam
    for _ in range(3):
        curr_m -= 1
        if curr_m == 0:
            curr_m = 12
            curr_y -= 1
        lookback.append((curr_m, curr_y))
        
    thang_str = f"T{thang:02d}"
    t_minus_1_m, t_minus_1_y = lookback[0]
    t_minus_1_str = f"T{t_minus_1_m:02d}"
    
    # 2. Xây dựng điều kiện lọc địa lý cho bưu cục
    geo_where = []
    geo_params = []
    if cum and cum != "Tất cả":
        geo_where.append("b.ten_cum = ?")
        geo_params.append(cum)
    if bdx and bdx != "Tất cả":
        geo_where.append("b.ten_bdx = ?")
        geo_params.append(bdx)
    geo_where_str = " AND " + " AND ".join(geo_where) if geo_where else ""
    
    # 3. Lấy tất cả CMS có doanh thu trong tháng target (T) và bưu cục của họ
    # Vì 1 CMS có thể giao dịch nhiều bưu cục, ta lấy bưu cục lớn nhất làm đại diện
    q_curr = f"""
        WITH cms_bc AS (
            SELECT t.cms, t.ma_buu_cuc as buu_cuc, SUM(t.cuoc_tt_tong) as dt,
                   ROW_NUMBER() OVER (PARTITION BY t.cms ORDER BY SUM(t.cuoc_tt_tong) DESC) as rn
            FROM transactions t
            LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ? AND t.cuoc_tt_tong > 0 {geo_where_str}
            GROUP BY t.cms, t.ma_buu_cuc
        )
        SELECT cms, buu_cuc, dt FROM cms_bc WHERE rn = 1
    """
    df_curr = pd.read_sql_query(q_curr, conn, params=[nam, thang_str] + geo_params)
    cms_curr_rev = dict(zip(df_curr['cms'], df_curr['dt']))
    
    # 4. Lấy tất cả CMS có doanh thu trong tháng T-1 và bưu cục
    q_prev = f"""
        WITH cms_bc AS (
            SELECT t.cms, t.ma_buu_cuc as buu_cuc, SUM(t.cuoc_tt_tong) as dt,
                   ROW_NUMBER() OVER (PARTITION BY t.cms ORDER BY SUM(t.cuoc_tt_tong) DESC) as rn
            FROM transactions t
            LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ? AND t.cuoc_tt_tong > 0 {geo_where_str}
            GROUP BY t.cms, t.ma_buu_cuc
        )
        SELECT cms, buu_cuc, dt FROM cms_bc WHERE rn = 1
    """
    df_prev = pd.read_sql_query(q_prev, conn, params=[t_minus_1_y, t_minus_1_str] + geo_params)
    cms_prev_rev = dict(zip(df_prev['cms'], df_prev['dt']))
    
    # 5. Phân tích Tăng, Giảm, Duy trì
    # Lấy tập hợp CMS chung có doanh thu dương ở cả 2 tháng T và T-1
    common_cms = set(cms_curr_rev.keys()) & set(cms_prev_rev.keys())
    
    # Cần join thêm địa lý dim_buucuc
    df_buucuc = pd.read_sql_query("SELECT ma_buu_cuc as buu_cuc, ten_bdx, ten_cum FROM dim_buucuc", conn)
    
    list_tang = []
    list_giam = []
    duy_tri_count = 0
    
    # Map nhanh thông tin địa lý từ df_curr và df_prev
    df_geo_map = pd.concat([df_curr[['cms', 'buu_cuc']], df_prev[['cms', 'buu_cuc']]]).drop_duplicates(subset=['cms'])
    df_geo_final = pd.merge(df_geo_map, df_buucuc, on='buu_cuc', how='inner')
    geo_dict = df_geo_final.set_index('cms')[['ten_cum', 'ten_bdx']].to_dict('index')
    
    for cms in common_cms:
        dt_c = cms_curr_rev[cms]
        dt_p = cms_prev_rev[cms]
        g = geo_dict.get(cms, {'ten_cum': 'Khác', 'ten_bdx': 'Khác'})
        
        row_d = {
            'cms': cms,
            'ten_cum': g['ten_cum'],
            'ten_bdx': g['ten_bdx'],
            'sl_ky_nay': 1, # Số lượng bưu gửi hoặc đếm giao dịch có thể điền 1
            'dt_ky_nay': dt_c,
            'sl_ky_truoc': 1,
            'dt_ky_truoc': dt_p,
            'chenh_lech': dt_c - dt_p
        }
        
        if dt_c > dt_p:
            list_tang.append(row_d)
        elif dt_c < dt_p:
            list_giam.append(row_d)
        else:
            duy_tri_count += 1
            
    # 6. Phân tích Rời bỏ (Churn) 3 tháng
    # Churn = Có doanh thu dương ở T-1, T-2 hoặc T-3 nhưng tháng T = 0
    # Lấy danh sách CMS có doanh thu trong 3 tháng lookback
    lookback_cms_dict = {} # cms -> (thang_gần_nhất, nam_gần_nhất, doanh_thu_tháng_đó, buu_cuc_đó)
    for idx, (m, y) in enumerate(lookback):
        m_str = f"T{m:02d}"
        q_l = f"""
            WITH cms_bc AS (
                SELECT t.cms, t.ma_buu_cuc as buu_cuc, SUM(t.cuoc_tt_tong) as dt,
                       ROW_NUMBER() OVER (PARTITION BY t.cms ORDER BY SUM(t.cuoc_tt_tong) DESC) as rn
                FROM transactions t
                LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
                WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ? AND t.cuoc_tt_tong > 0
                  AND t.cms IS NOT NULL AND t.cms != ''
                  AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' {geo_where_str}
                GROUP BY t.cms, t.ma_buu_cuc
            )
            SELECT cms, buu_cuc, dt FROM cms_bc WHERE rn = 1
        """
        df_l = pd.read_sql_query(q_l, conn, params=[y, m_str] + geo_params)
        
        for _, row in df_l.iterrows():
            c = row['cms']
            if c not in lookback_cms_dict:
                # Vì lookback sắp xếp giảm dần từ T-1 -> T-3, nên lần đầu bắt gặp chính là tháng gần nhất
                lookback_cms_dict[c] = {
                    'thang_gan_nhat': m,
                    'nam_gan_nhat': y,
                    'dt_gan_nhat': row['dt'],
                    'buu_cuc': row['buu_cuc']
                }
                
    # Lọc ra các CMS thuộc lookback nhưng KHÔNG có trong tháng hiện tại T
    churn_cms = set(lookback_cms_dict.keys()) - set(cms_curr_rev.keys())
    
    list_roi_bo = []
    for cms in churn_cms:
        info = lookback_cms_dict[cms]
        bc = info['buu_cuc']
        
        # Lấy địa lý bưu cục
        cursor.execute("SELECT ten_bdx, ten_cum FROM dim_buucuc WHERE ma_buu_cuc = ? LIMIT 1", (bc,))
        bc_row = cursor.fetchone()
        ten_cum = bc_row[1] if bc_row else "Khác"
        ten_bdx = bc_row[0] if bc_row else "Khác"
        
        list_roi_bo.append({
            'cms': cms,
            'ten_cum': ten_cum,
            'ten_bdx': ten_bdx,
            'sl_gan_nhat': 1,
            'dt_gan_nhat': info['dt_gan_nhat'],
            'thang_gan_nhat': f"T{info['thang_gan_nhat']:02d}/{info['nam_gan_nhat']}"
        })
        
    conn.close()
    
    return {
        'tang': list_tang,
        'giam': list_giam,
        'roi_bo': list_roi_bo,
        'duy_tri_count': duy_tri_count
    }


def get_weekly_changes(db_path: str, year: int, week: int, cum: str = None, bdx: str = None) -> dict:
    """
    Phân tích biến động tuần theo định nghĩa tuần-tuần.
    - Tăng: DT tuần hiện tại > DT tuần trước > 0
    - Giảm: 0 < DT tuần hiện tại < DT tuần trước
    - Rời bỏ: Tuần trước có DT > 0, tuần hiện tại không có (DT=0)
    - Duy trì: DT tuần hiện tại == DT tuần trước và > 0
    """
    import config.week_calendar as calendar_helper
    conn = sqlite3.connect(db_path)
    
    # 1. Xác định tuần trước
    prev_w, prev_yr = get_prev_period_info('Tuần', week, year)
    
    # Lấy ngày của tuần hiện tại và tuần trước để query transactions
    weeks_list = calendar_helper.get_week_list(year)
    c_start, c_end = None, None
    for w_num, s_d, e_d in weeks_list:
        if w_num == week:
            c_start, c_end = s_d.isoformat(), e_d.isoformat()
            break
            
    prev_weeks_list = calendar_helper.get_week_list(prev_yr)
    p_start, p_end = None, None
    for w_num, s_d, e_d in prev_weeks_list:
        if w_num == prev_w:
            p_start, p_end = s_d.isoformat(), e_d.isoformat()
            break
            
    if not c_start or not p_start:
        conn.close()
        return {'tang': [], 'giam': [], 'roi_bo': [], 'duy_tri_count': 0}
        
    geo_where = []
    geo_params = []
    if cum and cum != "Tất cả":
        geo_where.append("b.ten_cum = ?")
        geo_params.append(cum)
    if bdx and bdx != "Tất cả":
        geo_where.append("b.ten_bdx = ?")
        geo_params.append(bdx)
    geo_where_str = " AND " + " AND ".join(geo_where) if geo_where else ""
    
    # Query doanh thu tuần hiện tại
    q_curr = f"""
        WITH cms_bc AS (
            SELECT t.cms, t.ma_buu_cuc as buu_cuc, SUM(t.cuoc_tt_tong) as dt,
                   ROW_NUMBER() OVER (PARTITION BY t.cms ORDER BY SUM(t.cuoc_tt_tong) DESC) as rn
            FROM transactions t
            LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.ngay_chap_nhan BETWEEN ? AND ? AND t.cuoc_tt_tong > 0
              AND t.cms IS NOT NULL AND t.cms != ''
              AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' {geo_where_str}
            GROUP BY t.cms, t.ma_buu_cuc
        )
        SELECT cms, buu_cuc, dt FROM cms_bc WHERE rn = 1
    """
    df_curr = pd.read_sql_query(q_curr, conn, params=[c_start, c_end] + geo_params)
    cms_curr_rev = dict(zip(df_curr['cms'], df_curr['dt']))
    
    # Query doanh thu tuần trước
    q_prev = f"""
        WITH cms_bc AS (
            SELECT t.cms, t.ma_buu_cuc as buu_cuc, SUM(t.cuoc_tt_tong) as dt,
                   ROW_NUMBER() OVER (PARTITION BY t.cms ORDER BY SUM(t.cuoc_tt_tong) DESC) as rn
            FROM transactions t
            LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.ngay_chap_nhan BETWEEN ? AND ? AND t.cuoc_tt_tong > 0
              AND t.cms IS NOT NULL AND t.cms != ''
              AND t.cms NOT LIKE 'VANGLAI_%' AND LOWER(t.cms) != 'none' {geo_where_str}
            GROUP BY t.cms, t.ma_buu_cuc
        )
        SELECT cms, buu_cuc, dt FROM cms_bc WHERE rn = 1
    """
    df_prev = pd.read_sql_query(q_prev, conn, params=[p_start, p_end] + geo_params)
    cms_prev_rev = dict(zip(df_prev['cms'], df_prev['dt']))
    
    # Phân rã
    common_cms = set(cms_curr_rev.keys()) & set(cms_prev_rev.keys())
    df_buucuc = pd.read_sql_query("SELECT ma_buu_cuc as buu_cuc, ten_bdx, ten_cum FROM dim_buucuc", conn)
    
    list_tang = []
    list_giam = []
    duy_tri_count = 0
    
    df_geo_map = pd.concat([df_curr[['cms', 'buu_cuc']], df_prev[['cms', 'buu_cuc']]]).drop_duplicates(subset=['cms'])
    df_geo_final = pd.merge(df_geo_map, df_buucuc, on='buu_cuc', how='inner')
    geo_dict = df_geo_final.set_index('cms')[['ten_cum', 'ten_bdx']].to_dict('index')
    
    for cms in common_cms:
        dt_c = cms_curr_rev[cms]
        dt_p = cms_prev_rev[cms]
        g = geo_dict.get(cms, {'ten_cum': 'Khác', 'ten_bdx': 'Khác'})
        
        row_d = {
            'cms': cms,
            'ten_cum': g['ten_cum'],
            'ten_bdx': g['ten_bdx'],
            'sl_ky_nay': 1,
            'dt_ky_nay': dt_c,
            'sl_ky_truoc': 1,
            'dt_ky_truoc': dt_p,
            'chenh_lech': dt_c - dt_p
        }
        
        if dt_c > dt_p:
            list_tang.append(row_d)
        elif dt_c < dt_p:
            list_giam.append(row_d)
        else:
            duy_tri_count += 1
            
    # Churn tuần: Tuần trước có DT, tuần này không có
    churn_cms = set(cms_prev_rev.keys()) - set(cms_curr_rev.keys())
    list_roi_bo = []
    
    df_prev_indexed = df_prev.set_index('cms')
    for cms in churn_cms:
        g = geo_dict.get(cms, {'ten_cum': 'Khác', 'ten_bdx': 'Khác'})
        list_roi_bo.append({
            'cms': cms,
            'ten_cum': g['ten_cum'],
            'ten_bdx': g['ten_bdx'],
            'sl_gan_nhat': 1,
            'dt_gan_nhat': cms_prev_rev[cms],
            'thang_gan_nhat': f"Tuần {prev_w}/{prev_yr}"
        })
        
    conn.close()
    
    return {
        'tang': list_tang,
        'giam': list_giam,
        'roi_bo': list_roi_bo,
        'duy_tri_count': duy_tri_count
    }

