# -*- coding: utf-8 -*-
"""
Hàm tính toán chỉ số doanh thu toàn cục cho cả 4 nhóm dịch vụ (BCCP, HCC, TCBC, PPBL).
Hỗ trợ tính toán lũy kế YTD, tỷ lệ hoàn thành kế hoạch, phân rã theo Cụm và so sánh.
"""

import sys
import time
import sqlite3
import pandas as pd
from pathlib import Path

# Setup sys.path để import cấu hình
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

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


class TTLDictCache:
    def __init__(self, ttl=300):
        self.ttl = ttl
        self.cache = {}
    
    def get(self, key):
        if key in self.cache:
            val, expiry = self.cache[key]
            if expiry > time.time():
                return val
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time() + self.ttl)
        
    def clear(self):
        self.cache.clear()

_revenue_by_cum_cache = TTLDictCache(ttl=300)

def clear_global_metrics_cache():
    _revenue_by_cum_cache.clear()

def get_weekly_yoy_query_params(year, period_value):
    """
    Trả về (prev_year, w_ratios) gồm danh sách các tuple (tuan_so, ratio) giao thoa của năm trước.
    Vì lịch tuần các năm đã đồng bộ ngày/tháng 100% với năm 2026,
    ta chỉ cần trả về tuần cùng số thứ tự với ratio = 1.0.
    """
    return year - 1, [(period_value, 1.0)]

def _get_thang_list(thang_den):
    """Tạo danh sách string 'T01', 'T02'... từ 1 đến thang_den"""
    return [f"T{i:02d}" for i in range(1, thang_den + 1)]

def _execute_query_scalar(db_path, sql, params=None):
    """Helper thực thi query trả về một giá trị duy nhất (scalar)"""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or {})
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0.0
    except Exception as e:
        logger.error(f"Lỗi truy vấn SQL scalar: {e}")
        return 0.0
    finally:
        conn.close()

def get_total_revenue_by_service(db_path, nam, thang=None, cum=None):
    """
    Tính doanh thu thực tế của 4 dịch vụ trong năm (và tháng, cụm nếu có).
    Trả về dict: {BCCP: val, HCC: val, TCBC: val, PPBL: val}
    """
    thang_str = f"T{thang:02d}" if thang else None
    
    # 1. BCCP Doanh thu: transactions (nhom_chinh = 'BCCP')
    sql_bccp = """
        SELECT SUM(t.cuoc_tt_tong) 
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
    """
    # 2. HCC Doanh thu: transactions (nhom_chinh = 'HCC') + transactions_hcc
    sql_hcc_cp = """
        SELECT SUM(t.cuoc_tt_tong) 
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
    """
    sql_hcc_new = "SELECT SUM(t.doanh_thu) FROM transactions_hcc t"
    
    # 3. TCBC Doanh thu: transactions_tcbc
    sql_tcbc = "SELECT SUM(t.doanh_thu) FROM transactions_tcbc t"
    
    # 4. PPBL Doanh thu: transactions_ppbl
    sql_ppbl = "SELECT SUM(t.doanh_thu) FROM transactions_ppbl t"
    
    # Xử lý mệnh đề WHERE & JOIN Cụm
    where_t = ["d.nhom_chinh = 'BCCP'", "t.nam_du_lieu = :nam"]
    where_hcc_cp = ["d.nhom_chinh = 'HCC'", "t.nam_du_lieu = :nam"]
    where_hcc_new = ["t.nam_du_lieu = :nam"]
    where_tcbc = ["t.nam_du_lieu = :nam"]
    where_ppbl = ["t.nam_du_lieu = :nam"]
    
    params = {"nam": nam}
    
    if thang_str:
        where_t.append("t.thang_du_lieu = :thang")
        where_hcc_cp.append("t.thang_du_lieu = :thang")
        where_hcc_new.append("t.thang_du_lieu = :thang")
        where_tcbc.append("t.thang_du_lieu = :thang")
        where_ppbl.append("t.thang_du_lieu = :thang")
        params["thang"] = thang_str
        
    if cum and cum != "Tất cả":
        sql_bccp += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_hcc_cp += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_hcc_new += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_tcbc += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_ppbl += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        
        where_t.append("b.ten_cum = :cum")
        where_hcc_cp.append("b.ten_cum = :cum")
        where_hcc_new.append("b.ten_cum = :cum")
        where_tcbc.append("b.ten_cum = :cum")
        where_ppbl.append("b.ten_cum = :cum")
        params["cum"] = cum
        
    sql_bccp += " WHERE " + " AND ".join(where_t)
    sql_hcc_cp += " WHERE " + " AND ".join(where_hcc_cp)
    sql_hcc_new += " WHERE " + " AND ".join(where_hcc_new)
    sql_tcbc += " WHERE " + " AND ".join(where_tcbc)
    sql_ppbl += " WHERE " + " AND ".join(where_ppbl)
    
    bccp_val = _execute_query_scalar(db_path, sql_bccp, params)
    hcc_cp_val = _execute_query_scalar(db_path, sql_hcc_cp, params)
    hcc_new_val = _execute_query_scalar(db_path, sql_hcc_new, params)
    hcc_val = hcc_cp_val + hcc_new_val
    
    tcbc_val = _execute_query_scalar(db_path, sql_tcbc, params)
    ppbl_val = _execute_query_scalar(db_path, sql_ppbl, params)
    
    return {
        "BCCP": bccp_val,
        "HCC": hcc_val,
        "TCBC": tcbc_val,
        "PPBL": ppbl_val
    }

def get_revenue_structure(db_path, nam, thang=None, cum=None):
    """
    Tính tỉ lệ cơ cấu % doanh thu của 4 dịch vụ.
    """
    revs = get_total_revenue_by_service(db_path, nam, thang, cum)
    total = sum(revs.values())
    
    if total == 0:
        return {k: 0.0 for k in revs}
        
    return {k: (v * 100.0 / total) for k, v in revs.items()}

def get_ytd_revenue(db_path, nam, thang_den, cum=None):
    """
    Doanh thu lũy kế YTD từ tháng 1 đến thang_den.
    """
    thang_list = _get_thang_list(thang_den)
    
    # Tương tự get_total_revenue_by_service nhưng lọc theo danh sách tháng IN (thang_list)
    sql_bccp = """
        SELECT SUM(t.cuoc_tt_tong) 
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
    """
    sql_hcc_cp = """
        SELECT SUM(t.cuoc_tt_tong) 
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
    """
    sql_hcc_new = "SELECT SUM(t.doanh_thu) FROM transactions_hcc t"
    sql_tcbc = "SELECT SUM(t.doanh_thu) FROM transactions_tcbc t"
    sql_ppbl = "SELECT SUM(t.doanh_thu) FROM transactions_ppbl t"
    
    where_t = ["d.nhom_chinh = 'BCCP'", "t.nam_du_lieu = :nam", "t.thang_du_lieu IN ({})".format(','.join(f"'{m}'" for m in thang_list))]
    where_hcc_cp = ["d.nhom_chinh = 'HCC'", "t.nam_du_lieu = :nam", "t.thang_du_lieu IN ({})".format(','.join(f"'{m}'" for m in thang_list))]
    where_hcc_new = ["t.nam_du_lieu = :nam", "t.thang_du_lieu IN ({})".format(','.join(f"'{m}'" for m in thang_list))]
    where_tcbc = ["t.nam_du_lieu = :nam", "t.thang_du_lieu IN ({})".format(','.join(f"'{m}'" for m in thang_list))]
    where_ppbl = ["t.nam_du_lieu = :nam", "t.thang_du_lieu IN ({})".format(','.join(f"'{m}'" for m in thang_list))]
    
    params = {"nam": nam}
    
    if cum and cum != "Tất cả":
        sql_bccp += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_hcc_cp += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_hcc_new += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_tcbc += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        sql_ppbl += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc"
        
        where_t.append("b.ten_cum = :cum")
        where_hcc_cp.append("b.ten_cum = :cum")
        where_hcc_new.append("b.ten_cum = :cum")
        where_tcbc.append("b.ten_cum = :cum")
        where_ppbl.append("b.ten_cum = :cum")
        params["cum"] = cum
        
    sql_bccp += " WHERE " + " AND ".join(where_t)
    sql_hcc_cp += " WHERE " + " AND ".join(where_hcc_cp)
    sql_hcc_new += " WHERE " + " AND ".join(where_hcc_new)
    sql_tcbc += " WHERE " + " AND ".join(where_tcbc)
    sql_ppbl += " WHERE " + " AND ".join(where_ppbl)
    
    bccp_val = _execute_query_scalar(db_path, sql_bccp, params)
    hcc_cp_val = _execute_query_scalar(db_path, sql_hcc_cp, params)
    hcc_new_val = _execute_query_scalar(db_path, sql_hcc_new, params)
    hcc_val = hcc_cp_val + hcc_new_val
    tcbc_val = _execute_query_scalar(db_path, sql_tcbc, params)
    ppbl_val = _execute_query_scalar(db_path, sql_ppbl, params)
    
    return {
        "BCCP": bccp_val,
        "HCC": hcc_val,
        "TCBC": tcbc_val,
        "PPBL": ppbl_val
    }

def get_ytd_plan(db_path, nam, thang_den, cum=None):
    """
    Kế hoạch lũy kế YTD từ tháng 1 đến thang_den.
    """
    sql = "SELECT nhom_chinh, SUM(ke_hoach_doanh_thu) FROM plans"
    where = ["nam = :nam", "thang >= 1", "thang <= :thang_den"]
    params = {"nam": nam, "thang_den": thang_den}
    
    if cum and cum != "Tất cả":
        sql += " INNER JOIN dim_buucuc b ON plans.ma_buu_cuc = b.ma_buu_cuc"
        where.append("b.ten_cum = :cum")
        params["cum"] = cum
        
    sql += " WHERE " + " AND ".join(where) + " GROUP BY nhom_chinh"
    
    res = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
    
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        for row in rows:
            nhom = row[0]
            val = row[1] or 0.0
            if nhom in res:
                res[nhom] = val
    except Exception as e:
        logger.error(f"Lỗi lấy kế hoạch lũy kế plans: {e}")
    finally:
        conn.close()
        
    return res

def get_ytd_completion_rate(db_path, nam, thang_den, cum=None):
    """
    Tỷ lệ hoàn thành kế hoạch lũy kế YTD = Doanh thu thực tế lũy kế / Kế hoạch lũy kế
    """
    rev = get_ytd_revenue(db_path, nam, thang_den, cum)
    plan = get_ytd_plan(db_path, nam, thang_den, cum)
    
    rate = {}
    for k in rev:
        p_val = plan.get(k)
        if p_val is not None and p_val > 0:
            rate[k] = (rev[k] * 100.0 / p_val)
        else:
            rate[k] = "-"
            
    return rate

def get_revenue_by_cum(db_path, nam, thang=None):
    """
    Lấy doanh thu phân rã theo Cụm cho cả 4 nhóm dịch vụ.
    Trả về DataFrame có cấu trúc:
    Cụm | BCCP | HCC | TCBC | PPBL | Tổng cộng
    Sử dụng in-memory TTL caching.
    """
    key = (str(db_path), nam, thang)
    cached_df = _revenue_by_cum_cache.get(key)
    if cached_df is not None:
        return cached_df.copy()

    thang_str = f"T{thang:02d}" if thang else None
    
    # Khởi tạo bảng Cụm từ danh mục địa lý để đảm bảo đủ 18 cụm
    conn = sqlite3.connect(str(db_path))
    try:
        df_cums = pd.read_sql_query("SELECT DISTINCT ten_cum FROM dim_buucuc WHERE ten_cum IS NOT NULL ORDER BY ten_cum", conn)
        cums = df_cums["ten_cum"].tolist()
    except Exception as e:
        logger.error(f"Lỗi load danh mục Cụm: {e}")
        cums = []
    finally:
        conn.close()
        
    # Tạo dict chứa kết quả tạm
    cum_data = {c: {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0} for c in cums}
    
    # Truy vấn doanh thu BCCP & HCC chuyển phát từ transactions
    sql_trans = """
        SELECT b.ten_cum, d.nhom_chinh, SUM(t.cuoc_tt_tong) as dt
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
        INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
        WHERE t.nam_du_lieu = :nam
    """
    params = {"nam": nam}
    if thang_str:
        sql_trans += " AND t.thang_du_lieu = :thang"
        params["thang"] = thang_str
    sql_trans += " GROUP BY b.ten_cum, d.nhom_chinh"
    
    conn = sqlite3.connect(str(db_path))
    try:
        # 1. Điền BCCP & HCC (chuyển phát)
        df_trans = pd.read_sql_query(sql_trans, conn, params=params)
        for _, row in df_trans.iterrows():
            c = row["ten_cum"]
            nc = row["nhom_chinh"]
            val = row["dt"] or 0.0
            if c in cum_data and nc in ["BCCP", "HCC"]:
                cum_data[c][nc] += val
                
        # 2. Điền HCC mới
        sql_hcc = """
            SELECT b.ten_cum, SUM(t.doanh_thu) as dt
            FROM transactions_hcc t
            INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.nam_du_lieu = :nam
        """
        params_hcc = {"nam": nam}
        if thang_str:
            sql_hcc += " AND t.thang_du_lieu = :thang"
            params_hcc["thang"] = thang_str
        sql_hcc += " GROUP BY b.ten_cum"
        
        df_hcc = pd.read_sql_query(sql_hcc, conn, params=params_hcc)
        for _, row in df_hcc.iterrows():
            c = row["ten_cum"]
            val = row["dt"] or 0.0
            if c in cum_data:
                cum_data[c]["HCC"] += val
                
        # 3. Điền TCBC
        sql_tcbc = """
            SELECT b.ten_cum, SUM(t.doanh_thu) as dt
            FROM transactions_tcbc t
            INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.nam_du_lieu = :nam
        """
        params_tc = {"nam": nam}
        if thang_str:
            sql_tcbc += " AND t.thang_du_lieu = :thang"
            params_tc["thang"] = thang_str
        sql_tcbc += " GROUP BY b.ten_cum"
        
        df_tc = pd.read_sql_query(sql_tcbc, conn, params=params_tc)
        for _, row in df_tc.iterrows():
            c = row["ten_cum"]
            val = row["dt"] or 0.0
            if c in cum_data:
                cum_data[c]["TCBC"] += val
                
        # 4. Điền PPBL
        sql_ppbl = """
            SELECT b.ten_cum, SUM(t.doanh_thu) as dt
            FROM transactions_ppbl t
            INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
            WHERE t.nam_du_lieu = :nam
        """
        params_pp = {"nam": nam}
        if thang_str:
            sql_ppbl += " AND t.thang_du_lieu = :thang"
            params_pp["thang"] = thang_str
        sql_ppbl += " GROUP BY b.ten_cum"
        
        df_pp = pd.read_sql_query(sql_ppbl, conn, params=params_pp)
        for _, row in df_pp.iterrows():
            c = row["ten_cum"]
            val = row["dt"] or 0.0
            if c in cum_data:
                cum_data[c]["PPBL"] += val
                
    except Exception as e:
        logger.error(f"Lỗi phân rã doanh thu theo cụm: {e}")
    finally:
        conn.close()
        
    # Tạo DataFrame kết quả
    result_rows = []
    for c, v in cum_data.items():
        tot = sum(v.values())
        result_rows.append({
            "Cụm": c,
            "BCCP": v["BCCP"],
            "HCC": v["HCC"],
            "TCBC": v["TCBC"],
            "PPBL": v["PPBL"],
            "Tổng cộng": tot
        })
        
    df_res = pd.DataFrame(result_rows)
    if df_res.empty:
        df_res = pd.DataFrame(columns=["Cụm", "BCCP", "HCC", "TCBC", "PPBL", "Tổng cộng"])
        
    # Lưu vào cache
    _revenue_by_cum_cache.set(key, df_res)
    return df_res

def get_growth_heatmap_data(db_path, year, month, compare_mode="prev", cum=None):
    """
    Tính % tăng trưởng cho mỗi Cụm × Nhóm DV.
    compare_mode: "prev" (so tháng trước) hoặc "yoy" (so cùng kỳ)
    Returns: DataFrame(index=Cụm, columns=[BCCP,HCC,TCBC,PPBL], values=% growth)
    """
    df_current = get_revenue_by_cum(db_path, year, month)
    
    if compare_mode == "yoy":
        df_prev = get_revenue_by_cum(db_path, year - 1, month)
    else:
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year
        df_prev = get_revenue_by_cum(db_path, prev_year, prev_month)
        
    df_curr_indexed = df_current.set_index("Cụm")
    df_prev_indexed = df_prev.set_index("Cụm")
    
    services = ["BCCP", "HCC", "TCBC", "PPBL"]
    df_growth = pd.DataFrame(index=df_curr_indexed.index, columns=services)
    
    for svc in services:
        curr_vals = df_curr_indexed[svc].fillna(0)
        prev_vals = df_prev_indexed[svc].fillna(0)
        
        growth_vals = []
        for c_val, p_val in zip(curr_vals, prev_vals):
            if p_val == 0:
                if c_val == 0:
                    growth_vals.append(0.0)
                else:
                    growth_vals.append(None)
            else:
                growth_vals.append((c_val - p_val) * 100.0 / p_val)
        df_growth[svc] = growth_vals
        
    if cum and cum != "Tất cả":
        if cum in df_growth.index:
            df_growth = df_growth.loc[[cum]]
            
    return df_growth


def get_top10_by_comparison(conn, period_type, period_value, year, compare_type, cum=None, bdx=None, buu_cuc=None, service_key=None):
    """
    Tính top 10 xã có tỷ lệ tăng trưởng hoặc hoàn thành kế hoạch cao nhất.
    - compare_type: 'prev' (Kỳ trước), 'yoy' (Cùng kỳ năm trước), 'plan' (Kế hoạch)
    - period_type: 'Tháng' hoặc 'Tuần'
    - period_value: Số chu kỳ (ví dụ: 5 cho Tháng 5 hoặc 20 cho Tuần 20)
    - year: Năm hiện tại
    - service_key: None (Global), 'BCCP', 'HCC', 'TCBC', 'PPBL'

    Nguyên tắc 3 cấp kế hoạch:
    - BCCP: plans.ma_buu_cuc = ma_bc (6 số) → gộp lên xã (ma_bdx) qua dim_buucuc
    - HCC:  plans.ma_buu_cuc = ma_bdx (4 số) → dùng thẳng cấp xã
    - PHBC: plans.ma_buu_cuc = CUM_XXXX  → cấp cụm, bỏ qua trong top10 xã
    """
    import config.week_calendar as calendar_helper

    # ── Xác định kỳ so sánh ──────────────────────────────────────────────────
    if compare_type in ('prev', 'yoy'):
        if compare_type == 'prev':
            if period_type == 'Tháng':
                prev_month = 12 if period_value == 1 else period_value - 1
                prev_year  = year - 1 if period_value == 1 else year
                prev_value = prev_month
            else:
                if period_value == 1:
                    prev_year  = year - 1
                    weeks      = calendar_helper.get_week_list(prev_year)
                    prev_value = weeks[-1][0] if weeks else 52
                else:
                    prev_year  = year
                    prev_value = period_value - 1
        else:  # yoy
            prev_year  = year - 1
            prev_value = period_value

    # ── Bảng agg và cột kỳ tương ứng ────────────────────────────────────────
    if period_type == 'Tháng':
        agg_tbl  = 'agg_monthly'
        prd_col  = 'thang'
        plan_tbl = 'plans'
        plan_col = 'thang'
    else:
        agg_tbl  = 'agg_weekly'
        prd_col  = 'tuan_so'
        plan_tbl = 'plans_weekly'
        plan_col = 'tuan_so'

    grp_col = "b.ma_buu_cuc" if bdx and bdx != 'Tất cả' else "b.ma_bdx"

    # ── Helper: lấy actual gộp theo ma_bdx (hoặc ma_bc) ──────────────────────
    def _actual_by_xa(period_val, yr, nhom_filter=None):
        where_nhom = ""
        if nhom_filter:
            placeholders = ",".join(f"'{n}'" for n in nhom_filter)
            where_nhom = f" AND a.nhom_dich_vu IN ({placeholders})"
        sql = f"""
            SELECT {grp_col} as ma_bdx, SUM(a.tong_doanh_thu) AS dt
            FROM {agg_tbl} a
            INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
            WHERE a.nam = ? AND a.{prd_col} = ?{where_nhom}
              AND b.ma_bdx IS NOT NULL
              AND b.ma_bdx NOT LIKE 'CUM_%'
            GROUP BY {grp_col}
        """
        return pd.read_sql_query(sql, conn, params=(yr, period_val))

    nhom_filter = None
    if service_key:
        df_nhom = pd.read_sql_query("SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?", conn, params=(service_key,))
        nhom_filter = df_nhom['nhom_dich_vu'].tolist()

    if compare_type == 'plan':
        if not service_key:
            # Global: gộp BCCP và HCC
            df_nhom_bccp = pd.read_sql_query("SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'BCCP'", conn)
            NHOM_BCCP = df_nhom_bccp['nhom_dich_vu'].tolist()
            df_nhom_hcc = pd.read_sql_query("SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'HCC'", conn)
            NHOM_HCC = df_nhom_hcc['nhom_dich_vu'].tolist()
            
            df_bccp_act = _actual_by_xa(period_value, year, NHOM_BCCP).rename(columns={'dt': 'dt_bccp'})
            df_hcc_act  = _actual_by_xa(period_value, year, NHOM_HCC).rename(columns={'dt': 'dt_hcc'})
            sql_plan_bccp = f"""
                SELECT {grp_col} as ma_bdx, SUM(p.ke_hoach_doanh_thu) AS plan_bccp
                FROM {plan_tbl} p
                INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_buu_cuc
                WHERE p.nam = ? AND p.{plan_col} = ? AND p.nhom_chinh = 'BCCP'
                  AND b.ma_bdx IS NOT NULL
                GROUP BY {grp_col}
            """
            df_plan_bccp = pd.read_sql_query(sql_plan_bccp, conn, params=(year, period_value))
            sql_plan_hcc = f"""
                SELECT p.ma_buu_cuc AS ma_bdx, SUM(p.ke_hoach_doanh_thu) AS plan_hcc
                FROM {plan_tbl} p
                WHERE p.nam = ? AND p.{plan_col} = ? AND p.nhom_chinh = 'HCC'
                GROUP BY p.ma_buu_cuc
            """
            df_plan_hcc = pd.read_sql_query(sql_plan_hcc, conn, params=(year, period_value))
            df = (df_bccp_act
                  .merge(df_hcc_act,   on='ma_bdx', how='outer')
                  .merge(df_plan_bccp, on='ma_bdx', how='outer')
                  .merge(df_plan_hcc,  on='ma_bdx', how='outer')
                  .fillna(0.0))
            df['dt_curr']  = df['dt_bccp'] + df['dt_hcc']
            df['plan_val'] = df['plan_bccp'] + df['plan_hcc']
        else:
            # Specific service
            df_act = _actual_by_xa(period_value, year, nhom_filter).rename(columns={'dt': 'dt_curr'})
            sql_plan = f"""
                SELECT {grp_col} as ma_bdx, SUM(p.ke_hoach_doanh_thu) AS plan_val
                FROM {plan_tbl} p
                INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_buu_cuc
                WHERE p.nam = ? AND p.{plan_col} = ? AND p.nhom_chinh = ?
                AND b.ma_bdx IS NOT NULL
                GROUP BY {grp_col}
            """
            df_plan = pd.read_sql_query(sql_plan, conn, params=(year, period_value, service_key))
            df = df_act.merge(df_plan, on='ma_bdx', how='outer').fillna(0.0)

        df = df[(df['dt_curr'] > 0) & (df['plan_val'] > 0)]
        if df.empty:
            return pd.DataFrame(columns=['ten_cum', 'ten_bdx', 'ratio'])
        df['ratio'] = (df['dt_curr'] / df['plan_val']) * 100.0

    else:
        # So sánh kỳ trước / cùng kỳ: áp dụng bộ lọc nhóm dịch vụ
        df_curr = _actual_by_xa(period_value, year, nhom_filter).rename(columns={'dt': 'dt_curr'})
        df_prev = _actual_by_xa(prev_value, prev_year, nhom_filter).rename(columns={'dt': 'dt_prev'})
        df = df_curr.merge(df_prev, on='ma_bdx', how='inner')
        df = df[(df['dt_curr'] > 0) & (df['dt_prev'] > 0)]
        if df.empty:
            return pd.DataFrame(columns=['ten_cum', 'ten_bdx', 'ratio'])
        df['ratio'] = ((df['dt_curr'] - df['dt_prev']) / df['dt_prev']) * 100.0

    # ── Join địa lý: lấy ten_bdx, ten_cum theo ma_bdx (hoặc ma_bc) ───────────
    if bdx and bdx != 'Tất cả':
        df_geo = pd.read_sql_query(
            "SELECT ma_buu_cuc as ma_bdx, ten_buu_cuc as display_name, ten_bdx as real_ten_bdx, ten_cum FROM dim_buucuc "
            "WHERE ma_bdx IS NOT NULL AND ma_buu_cuc != ma_bdx AND ma_buu_cuc NOT LIKE 'CUM_%'",
            conn
        )
    else:
        df_geo = pd.read_sql_query(
            "SELECT DISTINCT ma_bdx, ten_bdx as display_name, ten_bdx as real_ten_bdx, ten_cum FROM dim_buucuc "
            "WHERE ma_bdx IS NOT NULL AND ma_buu_cuc = ma_bdx AND ma_bdx NOT LIKE 'CUM_%'",
            conn
        )
    df_final = df.merge(df_geo, on='ma_bdx', how='inner')

    # ── Lọc địa lý ───────────────────────────────────────────────────────────
    if cum and cum != 'Tất cả':
        df_final = df_final[df_final['ten_cum'] == cum]
    if bdx and bdx != 'Tất cả':
        df_final = df_final[df_final['real_ten_bdx'] == bdx]
    if buu_cuc and buu_cuc != 'Tất cả':
        df_final = df_final[df_final['ma_bdx'] == buu_cuc]

    df_final['ten_bdx'] = df_final['display_name']

    # ── Top 10 ───────────────────────────────────────────────────────────────
    df_final = df_final.sort_values(by='ratio', ascending=False).head(10)
    return df_final[['ten_cum', 'ten_bdx', 'ratio']]


def get_12_periods_revenue(conn, period_type, current_period, current_year, cum=None, bdx=None, buu_cuc=None):
    """
    Truy vấn dữ liệu doanh thu của 12 kỳ liên tiếp tính đến kỳ hiện tại.
    Trả về DataFrame có: label (ví dụ: 'T01/2026' hoặc 'Tuần 12'), BCCP, HCC, TCBC, PPBL
    """
    import config.week_calendar as calendar_helper
    periods = []
    
    if period_type == 'Tháng':
        curr_m, curr_y = current_period, current_year
        for _ in range(12):
            periods.append((curr_m, curr_y, f"T{curr_m:02d}/{curr_y}"))
            curr_m -= 1
            if curr_m == 0:
                curr_m = 12
                curr_y -= 1
        periods.reverse()
    else: # Tuần
        curr_w, curr_y = current_period, current_year
        for _ in range(12):
            periods.append((curr_w, curr_y, f"Tuần {curr_w}"))
            curr_w -= 1
            if curr_w == 0:
                curr_y -= 1
                weeks = calendar_helper.get_week_list(curr_y)
                curr_w = weeks[-1][0] if weeks else 52
        periods.reverse()
        
    result_data = []
    for val, yr, label in periods:
        row_dict = {'label': label, 'BCCP': 0.0, 'HCC': 0.0, 'TCBC': 0.0, 'PPBL': 0.0}
        
        if period_type == 'Tháng':
            query = """
                SELECT nhom_dich_vu, SUM(tong_doanh_thu)
                FROM (
                    SELECT COALESCE((SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 'Khác') as nhom_dich_vu,
                           a.tong_doanh_thu
                    FROM agg_monthly a
                    INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
                    WHERE a.nam = ? AND a.thang = ?
            """
        else: # Tuần
            query = """
                SELECT nhom_dich_vu, SUM(tong_doanh_thu)
                FROM (
                    SELECT COALESCE((SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 'Khác') as nhom_dich_vu,
                           a.tong_doanh_thu
                    FROM agg_weekly a
                    INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
                    WHERE a.nam = ? AND a.tuan_so = ?
            """
            
        params = [yr, val]
        if cum and cum != "Tất cả" and cum != "Tất cả Cụm":
            query += " AND b.ten_cum = ?"
            params.append(cum)
        if bdx and bdx != "Tất cả":
            query += " AND b.ten_bdx = ?"
            params.append(bdx)
        if buu_cuc and buu_cuc != "Tất cả":
            query += " AND a.ma_buu_cuc = ?"
            params.append(buu_cuc)
            
        query += """
                )
                GROUP BY nhom_dich_vu
        """
            
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        for nhom, dt in cursor.fetchall():
            if nhom in row_dict:
                row_dict[nhom] = dt or 0.0
                
        result_data.append(row_dict)
        
    return pd.DataFrame(result_data)


def get_period_detail_by_xa(conn, period_type, period_value, year, cum=None, bdx=None, buu_cuc=None):
    """
    Lấy chi tiết doanh thu theo bưu cục/xã bao gồm cả 4 dịch vụ ở kỳ hiện tại, kỳ trước, cùng kỳ và kế hoạch.
    """
    import config.week_calendar as calendar_helper
    cursor = conn.cursor()
    
    # 1. Định nghĩa kỳ so sánh
    if period_type == 'Tháng':
        prev_month = 12 if period_value == 1 else period_value - 1
        prev_year = year - 1 if period_value == 1 else year
        prev_value = prev_month
    else: # Tuần
        if period_value == 1:
            prev_year = year - 1
            weeks = calendar_helper.get_week_list(prev_year)
            prev_value = weeks[-1][0] if weeks else 52
        else:
            prev_year = year
            prev_value = period_value - 1
            
    # 2. Query doanh thu dịch vụ kỳ hiện tại theo xã
    if period_type == 'Tháng':
        curr_sql = """
            SELECT buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM (
                SELECT a.ma_buu_cuc as buu_cuc,
                       COALESCE((SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 'Khác') as nhom_dich_vu,
                       a.tong_doanh_thu
                FROM agg_monthly a
                WHERE a.nam = ? AND a.thang = ?
            )
            GROUP BY buu_cuc, nhom_dich_vu
        """
    else: # Tuần
        curr_sql = """
            SELECT buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM (
                SELECT a.ma_buu_cuc as buu_cuc,
                       COALESCE((SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 'Khác') as nhom_dich_vu,
                       a.tong_doanh_thu
                FROM agg_weekly a
                WHERE a.nam = ? AND a.tuan_so = ?
            )
            GROUP BY buu_cuc, nhom_dich_vu
        """
        
    df_curr_raw = pd.read_sql_query(curr_sql, conn, params=(year, period_value))
    
    if not df_curr_raw.empty:
        df_curr = df_curr_raw.pivot(index='buu_cuc', columns='nhom_dich_vu', values='dt').fillna(0.0).reset_index()
    else:
        df_curr = pd.DataFrame(columns=['buu_cuc', 'BCCP', 'HCC', 'TCBC', 'PPBL'])
        
    for col in ['BCCP', 'HCC', 'TCBC', 'PPBL']:
        if col not in df_curr.columns:
            df_curr[col] = 0.0
    df_curr['tong_dt'] = df_curr[['BCCP', 'HCC', 'TCBC', 'PPBL']].sum(axis=1)
    
    # 3. Doanh thu tổng kỳ trước theo xã
    if period_type == 'Tháng':
        prev_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_prev FROM agg_monthly WHERE nam = ? AND thang = ? GROUP BY ma_buu_cuc"
    else:
        prev_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_prev FROM agg_weekly WHERE nam = ? AND tuan_so = ? GROUP BY ma_buu_cuc"
    df_prev = pd.read_sql_query(prev_sql, conn, params=(prev_year, prev_value))
    
    # 4. Doanh thu tổng cùng kỳ năm trước theo xã
    if period_type == 'Tháng':
        yoy_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_yoy FROM agg_monthly WHERE nam = ? AND thang = ? GROUP BY ma_buu_cuc"
    else:
        yoy_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_yoy FROM agg_weekly WHERE nam = ? AND tuan_so = ? GROUP BY ma_buu_cuc"
    df_yoy = pd.read_sql_query(yoy_sql, conn, params=(year - 1, period_value))
    
    # 5. Kế hoạch kỳ hiện tại theo xã
    if period_type == 'Tháng':
        plan_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans WHERE nam = ? AND thang = ? GROUP BY ma_buu_cuc"
    else:
        plan_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans_weekly WHERE nam = ? AND tuan_so = ? GROUP BY ma_buu_cuc"
    df_plan = pd.read_sql_query(plan_sql, conn, params=(year, period_value))
    
    # Load danh mục địa lý dim_buucuc
    df_geo_all = pd.read_sql_query("SELECT ma_buu_cuc, ma_bdx, ten_bdx, ten_cum, ten_buu_cuc FROM dim_buucuc", conn)
    bc_to_xa = df_geo_all.set_index('ma_buu_cuc')['ma_bdx'].dropna().to_dict()
    bc_to_ten_xa = df_geo_all.set_index('ma_buu_cuc')['ten_bdx'].dropna().to_dict()
    bc_to_cum = df_geo_all.set_index('ma_buu_cuc')['ten_cum'].dropna().to_dict()
    bc_to_ten_bc = df_geo_all.set_index('ma_buu_cuc')['ten_buu_cuc'].dropna().to_dict()
    
    df_xa_geo = df_geo_all[['ma_bdx', 'ten_bdx', 'ten_cum']].dropna().drop_duplicates(subset=['ma_bdx'])
    xa_to_ten = df_xa_geo.set_index('ma_bdx')['ten_bdx'].to_dict()
    xa_to_cum = df_xa_geo.set_index('ma_bdx')['ten_cum'].to_dict()
    
    def assign_geo_info(df, code_col='buu_cuc'):
        if df.empty:
            df['ma_bdx'] = None
            df['ten_bdx'] = None
            df['ten_cum'] = None
            df['ten_buu_cuc'] = None
            return df
        
        ma_bdx_list = []
        ten_bdx_list = []
        ten_cum_list = []
        ten_bc_list = []
        
        for val in df[code_col]:
            val_str = str(val).strip()
            if len(val_str) == 4:
                ma_bdx_list.append(val_str)
                ten_bdx_list.append(xa_to_ten.get(val_str, None))
                ten_cum_list.append(xa_to_cum.get(val_str, None))
                ten_bc_list.append(None)
            elif len(val_str) == 6:
                ma_bdx_list.append(bc_to_xa.get(val_str, None))
                ten_bdx_list.append(bc_to_ten_xa.get(val_str, None))
                ten_cum_list.append(bc_to_cum.get(val_str, None))
                ten_bc_list.append(bc_to_ten_bc.get(val_str, None))
            else:
                ma_bdx_list.append(val_str)
                ten_bdx_list.append(None)
                ten_cum_list.append(None)
                ten_bc_list.append(None)
                
        df['ma_bdx'] = ma_bdx_list
        df['ten_bdx'] = ten_bdx_list
        df['ten_cum'] = ten_cum_list
        df['ten_buu_cuc'] = ten_bc_list
        return df

    # Gán địa lý
    df_curr = assign_geo_info(df_curr, 'buu_cuc')
    df_prev = assign_geo_info(df_prev, 'buu_cuc')
    df_yoy = assign_geo_info(df_yoy, 'buu_cuc')
    df_plan = assign_geo_info(df_plan, 'buu_cuc')

    if bdx == 'Tất cả' or not bdx:
        # Cấp Cụm: So sánh giữa các Xã
        def grp_df(df, sum_cols):
            if df.empty:
                return pd.DataFrame(columns=['ma_bdx'] + sum_cols)
            df_filtered = df[df['ma_bdx'].notna() & (~df['ma_bdx'].str.startswith('CUM_'))]
            if not df_filtered.empty:
                df_filtered = df_filtered[~df_filtered['ten_bdx'].fillna('').str.contains('Đại diện Cụm', na=False)]
            return df_filtered.groupby('ma_bdx')[sum_cols].sum().reset_index()

        df_curr_grp = grp_df(df_curr, ['BCCP', 'HCC', 'TCBC', 'PPBL', 'tong_dt'])
        df_prev_grp = grp_df(df_prev, ['dt_prev'])
        df_yoy_grp = grp_df(df_yoy, ['dt_yoy'])
        df_plan_grp = grp_df(df_plan, ['plan_dt'])

        # Merge các bảng đã gộp
        df_merge = df_curr_grp
        for df_c in [df_prev_grp, df_yoy_grp, df_plan_grp]:
            df_merge = pd.merge(df_merge, df_c, on='ma_bdx', how='outer')
        df_merge = df_merge.fillna(0.0)

        # Lấy lại ten_bdx và ten_cum
        df_merge['ten_bdx'] = df_merge['ma_bdx'].map(xa_to_ten)
        df_merge['ten_cum'] = df_merge['ma_bdx'].map(xa_to_cum)

        # Áp dụng bộ lọc cụm
        if cum and cum != 'Tất cả':
            df_merge = df_merge[df_merge['ten_cum'] == cum]
            
        df_merge = df_merge[df_merge['ten_bdx'].notna()]
        return df_merge.reset_index(drop=True)
    else:
        # Cấp Xã: So sánh các bưu cục con 6 số
        df_buucuc_real = df_geo_all[
            (df_geo_all['ten_bdx'] == bdx) & 
            (df_geo_all['ten_cum'] == cum) & 
            (df_geo_all['ma_buu_cuc'].str.len() == 6) & 
            (~df_geo_all['ma_buu_cuc'].str.startswith('CUM_'))
        ]
        real_ma_bc_list = set(df_buucuc_real['ma_buu_cuc'])

        # Merge trực tiếp theo buu_cuc
        df_merge = df_curr
        for df_c in [df_prev, df_yoy, df_plan]:
            if not df_c.empty:
                df_merge = pd.merge(df_merge, df_c[['buu_cuc', 'dt_prev' if 'dt_prev' in df_c else ('dt_yoy' if 'dt_yoy' in df_c else 'plan_dt')]], on='buu_cuc', how='outer')
        df_merge = df_merge.fillna(0.0)

        # Chỉ giữ lại bưu cục con thực tế thuộc xã
        df_merge = df_merge[df_merge['buu_cuc'].isin(real_ma_bc_list)]
        
        # Chỉ giữ bưu cục thực tế có phát sinh doanh thu thực tế (tong_dt > 0)
        df_merge = df_merge[df_merge['tong_dt'] > 0]

        # Gán tên bưu cục hiển thị
        df_merge['ten_bdx'] = df_merge['buu_cuc'].map(bc_to_ten_bc)
        df_merge['ma_bdx'] = df_merge['buu_cuc']
        df_merge['ten_cum'] = cum

        return df_merge.reset_index(drop=True)


def get_ytd_detail_by_xa(conn, period_type, period_value, year, cum=None, bdx=None, buu_cuc=None):
    """
    Tương tự như get_period_detail_by_xa nhưng tính lũy kế YTD từ đầu năm đến kỳ hiện tại.
    """
    import config.week_calendar as calendar_helper
    cursor = conn.cursor()
    
    # 1. Doanh thu lũy kế kỳ hiện tại theo xã
    if period_type == 'Tháng':
        curr_sql = """
            SELECT buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM (
                SELECT a.ma_buu_cuc as buu_cuc,
                       COALESCE((SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 'Khác') as nhom_dich_vu,
                       a.tong_doanh_thu
                FROM agg_monthly a
                WHERE a.nam = ? AND a.thang <= ?
            )
            GROUP BY buu_cuc, nhom_dich_vu
        """
    else: # Tuần
        curr_sql = """
            SELECT buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM (
                SELECT a.ma_buu_cuc as buu_cuc,
                       COALESCE((SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 'Khác') as nhom_dich_vu,
                       a.tong_doanh_thu
                FROM agg_weekly a
                WHERE a.nam = ? AND a.tuan_so <= ?
            )
            GROUP BY buu_cuc, nhom_dich_vu
        """
        
    df_curr_raw = pd.read_sql_query(curr_sql, conn, params=(year, period_value))
    
    if not df_curr_raw.empty:
        df_curr = df_curr_raw.pivot(index='buu_cuc', columns='nhom_dich_vu', values='dt').fillna(0.0).reset_index()
    else:
        df_curr = pd.DataFrame(columns=['buu_cuc', 'BCCP', 'HCC', 'TCBC', 'PPBL'])
        
    for col in ['BCCP', 'HCC', 'TCBC', 'PPBL']:
        if col not in df_curr.columns:
            df_curr[col] = 0.0
    df_curr['tong_dt'] = df_curr[['BCCP', 'HCC', 'TCBC', 'PPBL']].sum(axis=1)
    
    # 2. Doanh thu lũy kế kỳ trước (YTD cùng kỳ trước liền kề)
    if period_type == 'Tháng':
        prev_val = period_value - 1
        prev_yr = year
        if prev_val == 0:
            prev_val = 12
            prev_yr = year - 1
        prev_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_prev FROM agg_monthly WHERE nam = ? AND thang BETWEEN 1 AND ? GROUP BY ma_buu_cuc"
    else: # Tuần
        prev_val = period_value - 1
        prev_yr = year
        if prev_val == 0:
            prev_yr = year - 1
            weeks = calendar_helper.get_week_list(prev_yr)
            prev_val = weeks[-1][0] if weeks else 52
        prev_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_prev FROM agg_weekly WHERE nam = ? AND tuan_so BETWEEN 1 AND ? GROUP BY ma_buu_cuc"
        
    df_prev = pd.read_sql_query(prev_sql, conn, params=(prev_yr, prev_val))
    
    # 3. Doanh thu lũy kế cùng kỳ năm trước YTD
    if period_type == 'Tháng':
        yoy_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_yoy FROM agg_monthly WHERE nam = ? AND thang BETWEEN 1 AND ? GROUP BY ma_buu_cuc"
    else:
        yoy_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(tong_doanh_thu) as dt_yoy FROM agg_weekly WHERE nam = ? AND tuan_so BETWEEN 1 AND ? GROUP BY ma_buu_cuc"
    df_yoy = pd.read_sql_query(yoy_sql, conn, params=(year - 1, period_value))
    
    # 4. Kế hoạch lũy kế YTD (kế hoạch CẢ NĂM theo yêu cầu của Sếp)
    if period_type == 'Tháng':
        plan_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans WHERE nam = ? GROUP BY ma_buu_cuc"
    else:
        plan_sql = "SELECT ma_buu_cuc as buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans_weekly WHERE nam = ? GROUP BY ma_buu_cuc"
    df_plan = pd.read_sql_query(plan_sql, conn, params=(year,))
    
    # Load danh mục địa lý dim_buucuc
    df_geo_all = pd.read_sql_query("SELECT ma_buu_cuc, ma_bdx, ten_bdx, ten_cum, ten_buu_cuc FROM dim_buucuc", conn)
    bc_to_xa = df_geo_all.set_index('ma_buu_cuc')['ma_bdx'].dropna().to_dict()
    bc_to_ten_xa = df_geo_all.set_index('ma_buu_cuc')['ten_bdx'].dropna().to_dict()
    bc_to_cum = df_geo_all.set_index('ma_buu_cuc')['ten_cum'].dropna().to_dict()
    bc_to_ten_bc = df_geo_all.set_index('ma_buu_cuc')['ten_buu_cuc'].dropna().to_dict()
    
    df_xa_geo = df_geo_all[['ma_bdx', 'ten_bdx', 'ten_cum']].dropna().drop_duplicates(subset=['ma_bdx'])
    xa_to_ten = df_xa_geo.set_index('ma_bdx')['ten_bdx'].to_dict()
    xa_to_cum = df_xa_geo.set_index('ma_bdx')['ten_cum'].to_dict()
    
    def assign_geo_info(df, code_col='buu_cuc'):
        if df.empty:
            df['ma_bdx'] = None
            df['ten_bdx'] = None
            df['ten_cum'] = None
            df['ten_buu_cuc'] = None
            return df
        
        ma_bdx_list = []
        ten_bdx_list = []
        ten_cum_list = []
        ten_bc_list = []
        
        for val in df[code_col]:
            val_str = str(val).strip()
            if len(val_str) == 4:
                ma_bdx_list.append(val_str)
                ten_bdx_list.append(xa_to_ten.get(val_str, None))
                ten_cum_list.append(xa_to_cum.get(val_str, None))
                ten_bc_list.append(None)
            elif len(val_str) == 6:
                ma_bdx_list.append(bc_to_xa.get(val_str, None))
                ten_bdx_list.append(bc_to_ten_xa.get(val_str, None))
                ten_cum_list.append(bc_to_cum.get(val_str, None))
                ten_bc_list.append(bc_to_ten_bc.get(val_str, None))
            else:
                ma_bdx_list.append(val_str)
                ten_bdx_list.append(None)
                ten_cum_list.append(None)
                ten_bc_list.append(None)
                
        df['ma_bdx'] = ma_bdx_list
        df['ten_bdx'] = ten_bdx_list
        df['ten_cum'] = ten_cum_list
        df['ten_buu_cuc'] = ten_bc_list
        return df

    # Gán địa lý
    df_curr = assign_geo_info(df_curr, 'buu_cuc')
    df_prev = assign_geo_info(df_prev, 'buu_cuc')
    df_yoy = assign_geo_info(df_yoy, 'buu_cuc')
    df_plan = assign_geo_info(df_plan, 'buu_cuc')

    if bdx == 'Tất cả' or not bdx:
        # Cấp Cụm: So sánh giữa các Xã
        def grp_df(df, sum_cols):
            if df.empty:
                return pd.DataFrame(columns=['ma_bdx'] + sum_cols)
            df_filtered = df[df['ma_bdx'].notna() & (~df['ma_bdx'].str.startswith('CUM_'))]
            if not df_filtered.empty:
                df_filtered = df_filtered[~df_filtered['ten_bdx'].fillna('').str.contains('Đại diện Cụm', na=False)]
            return df_filtered.groupby('ma_bdx')[sum_cols].sum().reset_index()

        df_curr_grp = grp_df(df_curr, ['BCCP', 'HCC', 'TCBC', 'PPBL', 'tong_dt'])
        df_prev_grp = grp_df(df_prev, ['dt_prev'])
        df_yoy_grp = grp_df(df_yoy, ['dt_yoy'])
        df_plan_grp = grp_df(df_plan, ['plan_dt'])

        # Merge các bảng đã gộp
        df_merge = df_curr_grp
        for df_c in [df_prev_grp, df_yoy_grp, df_plan_grp]:
            df_merge = pd.merge(df_merge, df_c, on='ma_bdx', how='outer')
        df_merge = df_merge.fillna(0.0)

        # Lấy lại ten_bdx và ten_cum
        df_merge['ten_bdx'] = df_merge['ma_bdx'].map(xa_to_ten)
        df_merge['ten_cum'] = df_merge['ma_bdx'].map(xa_to_cum)

        # Áp dụng bộ lọc cụm
        if cum and cum != 'Tất cả':
            df_merge = df_merge[df_merge['ten_cum'] == cum]
            
        df_merge = df_merge[df_merge['ten_bdx'].notna()]
        return df_merge.reset_index(drop=True)
    else:
        # Cấp Xã: So sánh các bưu cục con 6 số
        df_buucuc_real = df_geo_all[
            (df_geo_all['ten_bdx'] == bdx) & 
            (df_geo_all['ten_cum'] == cum) & 
            (df_geo_all['ma_buu_cuc'].str.len() == 6) & 
            (~df_geo_all['ma_buu_cuc'].str.startswith('CUM_'))
        ]
        real_ma_bc_list = set(df_buucuc_real['ma_buu_cuc'])

        # Merge trực tiếp theo buu_cuc
        df_merge = df_curr
        for df_c in [df_prev, df_yoy, df_plan]:
            if not df_c.empty:
                df_merge = pd.merge(df_merge, df_c[['buu_cuc', 'dt_prev' if 'dt_prev' in df_c else ('dt_yoy' if 'dt_yoy' in df_c else 'plan_dt')]], on='buu_cuc', how='outer')
        df_merge = df_merge.fillna(0.0)

        # Chỉ giữ lại bưu cục con thực tế thuộc xã
        df_merge = df_merge[df_merge['buu_cuc'].isin(real_ma_bc_list)]
        
        # Chỉ giữ bưu cục thực tế có phát sinh doanh thu thực tế (tong_dt > 0)
        df_merge = df_merge[df_merge['tong_dt'] > 0]

        # Gán tên bưu cục hiển thị
        df_merge['ten_bdx'] = df_merge['buu_cuc'].map(bc_to_ten_bc)
        df_merge['ma_bdx'] = df_merge['buu_cuc']
        df_merge['ten_cum'] = cum

        return df_merge.reset_index(drop=True)

