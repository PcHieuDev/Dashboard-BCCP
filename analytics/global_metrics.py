# -*- coding: utf-8 -*-
"""
Hàm tính toán chỉ số doanh thu toàn cục cho cả 4 nhóm dịch vụ (BCCP, HCC, TCBC, PPBL).
Hỗ trợ tính toán lũy kế YTD, tỷ lệ hoàn thành kế hoạch, phân rã theo Cụm và so sánh.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Setup sys.path để import cấu hình
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH

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
        print(f"Lỗi truy vấn SQL scalar: {e}")
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
        INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
    """
    # 2. HCC Doanh thu: transactions (nhom_chinh = 'HCC') + transactions_hcc
    sql_hcc_cp = """
        SELECT SUM(t.cuoc_tt_tong) 
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
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
        sql_bccp += " INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc"
        sql_hcc_cp += " INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc"
        sql_hcc_new += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc"
        sql_tcbc += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc"
        sql_ppbl += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc"
        
        where_t.append("b.ten_Cum = :cum")
        where_hcc_cp.append("b.ten_Cum = :cum")
        where_hcc_new.append("b.ten_Cum = :cum")
        where_tcbc.append("b.ten_Cum = :cum")
        where_ppbl.append("b.ten_Cum = :cum")
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
        INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
    """
    sql_hcc_cp = """
        SELECT SUM(t.cuoc_tt_tong) 
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
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
        sql_bccp += " INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc"
        sql_hcc_cp += " INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc"
        sql_hcc_new += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc"
        sql_tcbc += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc"
        sql_ppbl += " INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc"
        
        where_t.append("b.ten_Cum = :cum")
        where_hcc_cp.append("b.ten_Cum = :cum")
        where_hcc_new.append("b.ten_Cum = :cum")
        where_tcbc.append("b.ten_Cum = :cum")
        where_ppbl.append("b.ten_Cum = :cum")
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
    sql = "SELECT nhom_dich_vu, SUM(ke_hoach_doanh_thu) FROM plans"
    where = ["nam = :nam", "thang >= 1", "thang <= :thang_den"]
    params = {"nam": nam, "thang_den": thang_den}
    
    if cum and cum != "Tất cả":
        sql += " INNER JOIN dim_buucuc b ON plans.ma_buu_cuc = b.ma_bc"
        where.append("b.ten_Cum = :cum")
        params["cum"] = cum
        
    sql += " WHERE " + " AND ".join(where) + " GROUP BY nhom_dich_vu"
    
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
        print(f"Lỗi lấy kế hoạch lũy kế plans: {e}")
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
        p_val = plan.get(k, 0.0)
        if p_val > 0:
            rate[k] = (rev[k] * 100.0 / p_val)
        else:
            rate[k] = 0.0
            
    return rate

def get_revenue_by_cum(db_path, nam, thang=None):
    """
    Lấy doanh thu phân rã theo Cụm cho cả 4 nhóm dịch vụ.
    Trả về DataFrame có cấu trúc:
    Cụm | BCCP | HCC | TCBC | PPBL | Tổng cộng
    """
    thang_str = f"T{thang:02d}" if thang else None
    
    # Khởi tạo bảng Cụm từ danh mục địa lý để đảm bảo đủ 18 cụm
    conn = sqlite3.connect(str(db_path))
    try:
        df_cums = pd.read_sql_query("SELECT DISTINCT ten_Cum FROM dim_buucuc WHERE ten_Cum IS NOT NULL ORDER BY ten_Cum", conn)
        cums = df_cums["ten_Cum"].tolist()
    except Exception as e:
        print(f"Lỗi load danh mục Cụm: {e}")
        cums = []
    finally:
        conn.close()
        
    # Tạo dict chứa kết quả tạm
    cum_data = {c: {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0} for c in cums}
    
    # Truy vấn doanh thu BCCP & HCC chuyển phát từ transactions
    sql_trans = """
        SELECT b.ten_Cum, d.nhom_chinh, SUM(t.cuoc_tt_tong) as dt
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
        INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = :nam
    """
    params = {"nam": nam}
    if thang_str:
        sql_trans += " AND t.thang_du_lieu = :thang"
        params["thang"] = thang_str
    sql_trans += " GROUP BY b.ten_Cum, d.nhom_chinh"
    
    conn = sqlite3.connect(str(db_path))
    try:
        # 1. Điền BCCP & HCC (chuyển phát)
        df_trans = pd.read_sql_query(sql_trans, conn, params=params)
        for _, row in df_trans.iterrows():
            c = row["ten_Cum"]
            nc = row["nhom_chinh"]
            val = row["dt"] or 0.0
            if c in cum_data and nc in ["BCCP", "HCC"]:
                cum_data[c][nc] += val
                
        # 2. Điền HCC mới
        sql_hcc = """
            SELECT b.ten_Cum, SUM(t.doanh_thu) as dt
            FROM transactions_hcc t
            INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc
            WHERE t.nam_du_lieu = :nam
        """
        params_hcc = {"nam": nam}
        if thang_str:
            sql_hcc += " AND t.thang_du_lieu = :thang"
            params_hcc["thang"] = thang_str
        sql_hcc += " GROUP BY b.ten_Cum"
        
        df_hcc = pd.read_sql_query(sql_hcc, conn, params=params_hcc)
        for _, row in df_hcc.iterrows():
            c = row["ten_Cum"]
            val = row["dt"] or 0.0
            if c in cum_data:
                cum_data[c]["HCC"] += val
                
        # 3. Điền TCBC
        sql_tcbc = """
            SELECT b.ten_Cum, SUM(t.doanh_thu) as dt
            FROM transactions_tcbc t
            INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc
            WHERE t.nam_du_lieu = :nam
        """
        params_tc = {"nam": nam}
        if thang_str:
            sql_tcbc += " AND t.thang_du_lieu = :thang"
            params_tc["thang"] = thang_str
        sql_tcbc += " GROUP BY b.ten_Cum"
        
        df_tc = pd.read_sql_query(sql_tcbc, conn, params=params_tc)
        for _, row in df_tc.iterrows():
            c = row["ten_Cum"]
            val = row["dt"] or 0.0
            if c in cum_data:
                cum_data[c]["TCBC"] += val
                
        # 4. Điền PPBL
        sql_ppbl = """
            SELECT b.ten_Cum, SUM(t.doanh_thu) as dt
            FROM transactions_ppbl t
            INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc
            WHERE t.nam_du_lieu = :nam
        """
        params_pp = {"nam": nam}
        if thang_str:
            sql_ppbl += " AND t.thang_du_lieu = :thang"
            params_pp["thang"] = thang_str
        sql_ppbl += " GROUP BY b.ten_Cum"
        
        df_pp = pd.read_sql_query(sql_ppbl, conn, params=params_pp)
        for _, row in df_pp.iterrows():
            c = row["ten_Cum"]
            val = row["dt"] or 0.0
            if c in cum_data:
                cum_data[c]["PPBL"] += val
                
    except Exception as e:
        print(f"Lỗi phân rã doanh thu theo cụm: {e}")
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
    return df_res
