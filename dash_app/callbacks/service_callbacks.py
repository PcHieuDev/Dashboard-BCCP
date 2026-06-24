# -*- coding: utf-8 -*-
"""
Callbacks quản lý giao diện, tính toán số liệu và xuất Excel cho các trang Tổng quan dịch vụ v2.0.
Sử dụng chung cấu trúc với Tổng quan chung nhưng lọc theo từng dịch vụ (BCCP, HCC, TCBC, PPBL).
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from dash import Output, Input, State, html, dash_table
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# Setup sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH, SERVICE_COLORS
from callbacks.utils import format_revenue
from analytics.global_metrics import get_top10_by_comparison

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

def get_plans_current_period_sub(db_path, service_key, period_type, period_value, year, cum=None, bdx=None, buu_cuc=None):
    """Lấy kế hoạch doanh thu của các dịch vụ con thuộc service_key trong kỳ hiện tại"""
    res = {}
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        if period_type == 'Tháng':
            sql = """
                SELECT p.nhom_dich_vu, SUM(p.ke_hoach_doanh_thu) 
                FROM plans p
                INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_buu_cuc
                WHERE p.nam = ? AND p.thang = ? AND p.nhom_chinh = ? AND p.nhom_dich_vu IS NOT NULL
            """
        else:
            sql = """
                SELECT p.nhom_dich_vu, SUM(p.ke_hoach_doanh_thu) 
                FROM plans_weekly p
                INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_buu_cuc
                WHERE p.nam = ? AND p.tuan_so = ? AND p.nhom_chinh = ? AND p.nhom_dich_vu IS NOT NULL
            """
        
        clauses = []
        params = [year, period_value, service_key]
        if cum and cum != "Tất cả":
            clauses.append("b.ten_cum = ?")
            params.append(cum)
        if bdx and bdx != "Tất cả":
            clauses.append("b.ten_bdx = ?")
            params.append(bdx)
        if buu_cuc and buu_cuc != "Tất cả":
            clauses.append("p.ma_buu_cuc = ?")
            params.append(buu_cuc)
            
        if clauses:
            sql += " AND " + " AND ".join(clauses)
        sql += " GROUP BY p.nhom_dich_vu"
        
        cursor.execute(sql, tuple(params))
        for r in cursor.fetchall():
            res[r[0]] = r[1] or 0.0
    except Exception as e:
        logger.error(f"Lỗi lấy kế hoạch con cho {service_key}: {e}")
    finally:
        conn.close()
    return res

def create_top10_table_sub(df, is_plan=False):
    """Tạo bảng Top 10 đơn giản cho dịch vụ con"""
    if df.empty:
        return html.Div("Không có dữ liệu phù hợp", style={"color": "#64748B", "fontSize": "12px", "textAlign": "center", "padding": "10px"})
        
    rows = []
    for idx, row in df.iterrows():
        ratio_val = row['ratio']
        if is_plan:
            color = "#0F172A"
            display_val = f"{ratio_val:.1f}%"
        else:
            color = "#10B981" if ratio_val >= 0 else "#EF4444"
            icon = "▲" if ratio_val >= 0 else "▼"
            display_val = f"{icon} {abs(ratio_val):.1f}%"
            
        rows.append(html.Tr([
            html.Td(f"{idx+1}", style={"width": "30px", "fontWeight": "bold", "color": "#64748B"}),
            html.Td(row['ten_cum'], style={"color": "#475569"}),
            html.Td(row['ten_bdx'], style={"fontWeight": "medium", "color": "#0F172A"}),
            html.Td(display_val, style={"color": color, "fontWeight": "bold", "textAlign": "right"})
        ]))
        
    return html.Table([
        html.Tbody(rows)
    ], className="table table-sm table-borderless", style={"fontSize": "12px", "marginBottom": 0})

def create_detail_table_sub(df, sub_services, compare_type, title_label="⭐️ TOÀN TỈNH"):
    """Tạo bảng DataTable hiển thị chi tiết xã theo các nhóm dịch vụ con"""
    if df.empty:
        return html.Div("Không có dữ liệu", style={"textAlign": "center", "padding": "20px"})
        
    # Thêm cột % So sánh
    if compare_type == 'prev':
        df['ratio'] = ((df['tong_dt'] - df['dt_prev']) / df['dt_prev']) * 100.0
        df['ratio_display'] = df['ratio'].map(lambda x: f"{x:+.1f}%" if pd.notna(x) and x != float('inf') and x != float('-inf') else "—")
        ratio_col_name = "Tăng trưởng vs Kỳ trước"
    elif compare_type == 'yoy':
        df['ratio'] = ((df['tong_dt'] - df['dt_yoy']) / df['dt_yoy']) * 100.0
        df['ratio_display'] = df['ratio'].map(lambda x: f"{x:+.1f}%" if pd.notna(x) and x != float('inf') and x != float('-inf') else "—")
        ratio_col_name = "Tăng trưởng vs Cùng kỳ"
    else: # plan
        df['ratio'] = df.apply(lambda r: (r['tong_dt'] / r['plan_dt'] * 100.0) if pd.notna(r['plan_dt']) and r['plan_dt'] > 0 else None, axis=1)
        df['ratio_display'] = df['ratio'].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "Không có KH")
        ratio_col_name = "Hoàn thành Kế hoạch"
        
    # Tính dòng TOÀN TỈNH
    prov_dict = {
        "ten_cum": title_label,
        "ten_bdx": "",
        "tong_dt": df["tong_dt"].sum(),
        "dt_prev": df["dt_prev"].sum(),
        "dt_yoy": df["dt_yoy"].sum(),
        "plan_dt": df["plan_dt"].sum(),
    }
    for sub in sub_services:
        prov_dict[sub] = df[sub].sum() if sub in df.columns else 0.0
        
    prov_row = pd.DataFrame([prov_dict])
    
    if compare_type == 'prev':
        p_prev = prov_row.iloc[0]['dt_prev']
        prov_row['ratio'] = ((prov_row['tong_dt'] - p_prev) / p_prev * 100.0) if p_prev > 0 else None
        prov_row['ratio_display'] = prov_row['ratio'].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    elif compare_type == 'yoy':
        p_yoy = prov_row.iloc[0]['dt_yoy']
        prov_row['ratio'] = ((prov_row['tong_dt'] - p_yoy) / p_yoy * 100.0) if p_yoy > 0 else None
        prov_row['ratio_display'] = prov_row['ratio'].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    else: # plan
        p_plan = prov_row.iloc[0]['plan_dt']
        prov_row['ratio'] = (prov_row['tong_dt'] / p_plan * 100.0) if p_plan > 0 else None
        prov_row['ratio_display'] = prov_row['ratio'].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "Không có KH")
        
    df_sorted = df.sort_values(by=['ten_cum', 'ten_bdx'], ascending=True)
    df_final = pd.concat([prov_row, df_sorted], ignore_index=True)
    
    # Xác định cột và tên hiển thị doanh thu kỳ so sánh
    if compare_type == 'prev':
        cmp_col = 'dt_prev'
        cmp_col_name = "DT Kỳ trước"
    elif compare_type == 'yoy':
        cmp_col = 'dt_yoy'
        cmp_col_name = "DT Cùng kỳ"
    else:  # plan
        cmp_col = 'plan_dt'
        cmp_col_name = "Kế hoạch"

    # Định dạng tiền
    df_display = df_final.copy()
    for col in sub_services + ["tong_dt", cmp_col]:
        if col in df_display.columns:
            df_display[col] = df_display[col].map(lambda x: f"{x:,.0f} đ" if pd.notna(x) and x > 0 else "0 đ")

    columns = [
        {"name": "Cụm", "id": "ten_cum"},
        {"name": "Xã / Bưu cục", "id": "ten_bdx"}
    ]
    for sub in sub_services:
        columns.append({"name": sub, "id": sub})

    columns.extend([
        {"name": "Tổng Doanh Thu", "id": "tong_dt"},
        {"name": cmp_col_name, "id": cmp_col},
        {"name": ratio_col_name, "id": "ratio_display"}
    ])
    
    return dash_table.DataTable(
        data=df_display.to_dict("records"),
        columns=columns,
        sort_action="native",
        page_size=15,
        style_table={"overflowX": "auto", "borderRadius": "8px", "border": "1px solid #E2E8F0"},
        style_header={
            "backgroundColor": "#F8FAFC",
            "fontWeight": "bold",
            "color": "#1E293B",
            "border": "1px solid #CBD5E1",
            "fontSize": "11px",
            "padding": "6px 6px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_cell={
            "padding": "4px 6px",
            "textAlign": "left",
            "fontSize": "11px",
            "fontFamily": "Inter, sans-serif",
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "maxWidth": "140px",
        },
        style_cell_conditional=[
            {"if": {"column_id": "ten_cum"},  "maxWidth": "90px",  "minWidth": "70px"},
            {"if": {"column_id": "ten_bdx"},  "maxWidth": "130px", "minWidth": "100px"},
            {"if": {"column_id": sub_services}, "maxWidth": "110px", "textAlign": "right"},
            {"if": {"column_id": "tong_dt"},  "maxWidth": "120px", "textAlign": "right"},
            {"if": {"column_id": cmp_col},    "maxWidth": "110px", "textAlign": "right"},
            {"if": {"column_id": "ratio_display"}, "maxWidth": "90px", "textAlign": "center"},
        ],
        style_data_conditional=[
            {
                "if": {"row_index": 0},
                "backgroundColor": "#EFF6FF",
                "fontWeight": "bold",
                "color": "#1E3A8A"
            },
            {
                "if": {"column_id": "tong_dt"},
                "fontWeight": "bold"
            },
            {
                "if": {"column_id": ["dt_prev", "dt_yoy", "plan_dt"]},
                "color": "#64748B",
                "fontStyle": "italic"
            }
        ],
        style_header_conditional=[
            {
                "if": {"column_id": ["dt_prev", "dt_yoy", "plan_dt"]},
                "backgroundColor": "#F1F5F9",
                "color": "#475569",
                "fontStyle": "italic"
            }
        ]
    )


def query_sub_service_data(conn, service_key, period_type, period_val, year, sub_services, cum=None, bdx=None, buu_cuc=None):
    """Query chi tiết doanh thu theo bưu cục xã, phân rã theo nhóm dịch vụ con"""
    import config.week_calendar as calendar_helper
    cursor = conn.cursor()
    
    # 1. Tìm kỳ trước và cùng kỳ
    prev_val, prev_yr = get_prev_period_info(period_type, period_val, year)
    
    # 2. Query doanh thu dịch vụ kỳ hiện tại
    if period_type == 'Tháng':
        sql = """
            SELECT ma_buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM agg_monthly
            WHERE nam = ? AND thang = ? AND nhom_dich_vu IN (
                SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
            )
            GROUP BY ma_buu_cuc, nhom_dich_vu
        """
    else:
        sql = """
            SELECT ma_buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM agg_weekly
            WHERE nam = ? AND tuan_so = ? AND nhom_dich_vu IN (
                SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
            )
            GROUP BY ma_buu_cuc, nhom_dich_vu
        """
        
    df_raw = pd.read_sql_query(sql, conn, params=(year, period_val, service_key))
    
    if not df_raw.empty:
        df_pivot = df_raw.pivot(index='ma_buu_cuc', columns='nhom_dich_vu', values='dt').fillna(0.0).reset_index()
    else:
        df_pivot = pd.DataFrame(columns=['ma_buu_cuc'] + sub_services)
        
    for sub in sub_services:
        if sub not in df_pivot.columns:
            df_pivot[sub] = 0.0
    df_pivot['tong_dt'] = df_pivot[sub_services].sum(axis=1)
    
    # 3. Query tổng doanh thu kỳ trước
    if period_type == 'Tháng':
        prev_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_prev 
            FROM agg_monthly 
            WHERE nam = ? AND thang = ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    else:
        prev_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_prev 
            FROM agg_weekly 
            WHERE nam = ? AND tuan_so = ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    df_prev = pd.read_sql_query(prev_sql, conn, params=(prev_yr, prev_val, service_key))
    
    # 4. Query tổng doanh thu cùng kỳ năm trước
    if period_type == 'Tháng':
        yoy_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_yoy 
            FROM agg_monthly 
            WHERE nam = ? AND thang = ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    else:
        yoy_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_yoy 
            FROM agg_weekly 
            WHERE nam = ? AND tuan_so = ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    df_yoy = pd.read_sql_query(yoy_sql, conn, params=(year - 1, period_val, service_key))
    
    # 5. Query kế hoạch
    if period_type == 'Tháng':
        plan_sql = "SELECT ma_buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans WHERE nam = ? AND thang = ? AND nhom_chinh = ? GROUP BY ma_buu_cuc"
    else:
        plan_sql = "SELECT ma_buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans_weekly WHERE nam = ? AND tuan_so = ? AND nhom_chinh = ? GROUP BY ma_buu_cuc"
    df_plan = pd.read_sql_query(plan_sql, conn, params=(year, period_val, service_key))
    
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
    df_pivot = assign_geo_info(df_pivot, 'ma_buu_cuc')
    df_prev = assign_geo_info(df_prev, 'ma_buu_cuc')
    df_yoy = assign_geo_info(df_yoy, 'ma_buu_cuc')
    df_plan = assign_geo_info(df_plan, 'ma_buu_cuc')

    if bdx == 'Tất cả' or not bdx:
        # Cấp Cụm: So sánh các Xã
        def grp_df(df, sum_cols):
            if df.empty:
                return pd.DataFrame(columns=['ma_bdx'] + sum_cols)
            df_filtered = df[df['ma_bdx'].notna() & (~df['ma_bdx'].str.startswith('CUM_'))]
            if not df_filtered.empty:
                df_filtered = df_filtered[~df_filtered['ten_bdx'].fillna('').str.contains('Đại diện Cụm', na=False)]
            return df_filtered.groupby('ma_bdx')[sum_cols].sum().reset_index()

        df_curr_grp = grp_df(df_pivot, sub_services + ['tong_dt'])
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

        # Merge trực tiếp theo ma_buu_cuc
        df_merge = df_pivot
        for df_c in [df_prev, df_yoy, df_plan]:
            if not df_c.empty:
                df_merge = pd.merge(df_merge, df_c[['ma_buu_cuc', 'dt_prev' if 'dt_prev' in df_c else ('dt_yoy' if 'dt_yoy' in df_c else 'plan_dt')]], on='ma_buu_cuc', how='outer')
        df_merge = df_merge.fillna(0.0)

        # Chỉ giữ lại bưu cục con thực tế thuộc xã
        df_merge = df_merge[df_merge['ma_buu_cuc'].isin(real_ma_bc_list)]
        
        # Chỉ giữ bưu cục thực tế có phát sinh doanh thu thực tế (tong_dt > 0)
        df_merge = df_merge[df_merge['tong_dt'] > 0]

        # Gán tên bưu cục hiển thị
        df_merge['ten_bdx'] = df_merge['ma_buu_cuc'].map(bc_to_ten_bc)
        df_merge['ma_bdx'] = df_merge['ma_buu_cuc']
        df_merge['ten_cum'] = cum

        return df_merge.reset_index(drop=True)


def query_sub_service_data_ytd(conn, service_key, period_type, period_val, year, sub_services, cum=None, bdx=None, buu_cuc=None):
    """Query chi tiết doanh thu lũy kế YTD theo bưu cục xã, phân rã theo nhóm dịch vụ con"""
    import config.week_calendar as calendar_helper
    cursor = conn.cursor()
    
    # 1. Query doanh thu YTD hiện tại
    if period_type == 'Tháng':
        sql = """
            SELECT ma_buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM agg_monthly
            WHERE nam = ? AND thang BETWEEN 1 AND ? AND nhom_dich_vu IN (
                SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
            )
            GROUP BY ma_buu_cuc, nhom_dich_vu
        """
    else:
        sql = """
            SELECT ma_buu_cuc, nhom_dich_vu, SUM(tong_doanh_thu) as dt
            FROM agg_weekly
            WHERE nam = ? AND tuan_so BETWEEN 1 AND ? AND nhom_dich_vu IN (
                SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
            )
            GROUP BY ma_buu_cuc, nhom_dich_vu
        """
        
    df_raw = pd.read_sql_query(sql, conn, params=(year, period_val, service_key))
    
    if not df_raw.empty:
        df_pivot = df_raw.pivot(index='ma_buu_cuc', columns='nhom_dich_vu', values='dt').fillna(0.0).reset_index()
    else:
        df_pivot = pd.DataFrame(columns=['ma_buu_cuc'] + sub_services)
        
    for sub in sub_services:
        if sub not in df_pivot.columns:
            df_pivot[sub] = 0.0
    df_pivot['tong_dt'] = df_pivot[sub_services].sum(axis=1)
    
    # 2. Query tổng doanh thu YTD kỳ trước (lũy kế YTD đến kỳ trước liền kề)
    if period_type == 'Tháng':
        prev_val = period_val - 1
        prev_yr = year
        if prev_val == 0:
            prev_val = 12
            prev_yr = year - 1
        prev_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_prev 
            FROM agg_monthly 
            WHERE nam = ? AND thang BETWEEN 1 AND ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    else:
        prev_val = period_val - 1
        prev_yr = year
        if prev_val == 0:
            prev_yr = year - 1
            weeks = calendar_helper.get_week_list(prev_yr)
            prev_val = weeks[-1][0] if weeks else 52
        prev_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_prev 
            FROM agg_weekly 
            WHERE nam = ? AND tuan_so BETWEEN 1 AND ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    df_prev = pd.read_sql_query(prev_sql, conn, params=(prev_yr, prev_val, service_key))
    
    # 3. Query tổng doanh thu cùng kỳ YTD
    if period_type == 'Tháng':
        yoy_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_yoy 
            FROM agg_monthly 
            WHERE nam = ? AND thang BETWEEN 1 AND ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    else:
        yoy_sql = """
            SELECT ma_buu_cuc, SUM(tong_doanh_thu) as dt_yoy 
            FROM agg_weekly 
            WHERE nam = ? AND tuan_so BETWEEN 1 AND ? AND nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            GROUP BY ma_buu_cuc
        """
    df_yoy = pd.read_sql_query(yoy_sql, conn, params=(year - 1, period_val, service_key))
    
    # 4. Query kế hoạch cả năm
    if period_type == 'Tháng':
        plan_sql = "SELECT ma_buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans WHERE nam = ? AND nhom_chinh = ? GROUP BY ma_buu_cuc"
    else:
        plan_sql = "SELECT ma_buu_cuc, SUM(ke_hoach_doanh_thu) as plan_dt FROM plans_weekly WHERE nam = ? AND nhom_chinh = ? GROUP BY ma_buu_cuc"
    df_plan = pd.read_sql_query(plan_sql, conn, params=(year, service_key))
    
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
    df_pivot = assign_geo_info(df_pivot, 'ma_buu_cuc')
    df_prev = assign_geo_info(df_prev, 'ma_buu_cuc')
    df_yoy = assign_geo_info(df_yoy, 'ma_buu_cuc')
    df_plan = assign_geo_info(df_plan, 'ma_buu_cuc')

    if bdx == 'Tất cả' or not bdx:
        # Cấp Cụm: So sánh các Xã
        def grp_df(df, sum_cols):
            if df.empty:
                return pd.DataFrame(columns=['ma_bdx'] + sum_cols)
            df_filtered = df[df['ma_bdx'].notna() & (~df['ma_bdx'].str.startswith('CUM_'))]
            if not df_filtered.empty:
                df_filtered = df_filtered[~df_filtered['ten_bdx'].fillna('').str.contains('Đại diện Cụm', na=False)]
            return df_filtered.groupby('ma_bdx')[sum_cols].sum().reset_index()

        df_curr_grp = grp_df(df_pivot, sub_services + ['tong_dt'])
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

        # Merge trực tiếp theo ma_buu_cuc
        df_merge = df_pivot
        for df_c in [df_prev, df_yoy, df_plan]:
            if not df_c.empty:
                df_merge = pd.merge(df_merge, df_c[['ma_buu_cuc', 'dt_prev' if 'dt_prev' in df_c else ('dt_yoy' if 'dt_yoy' in df_c else 'plan_dt')]], on='ma_buu_cuc', how='outer')
        df_merge = df_merge.fillna(0.0)

        # Chỉ giữ lại bưu cục con thực tế thuộc xã
        df_merge = df_merge[df_merge['ma_buu_cuc'].isin(real_ma_bc_list)]
        
        # Chỉ giữ bưu cục thực tế có phát sinh doanh thu thực tế (tong_dt > 0)
        df_merge = df_merge[df_merge['tong_dt'] > 0]

        # Gán tên bưu cục hiển thị
        df_merge['ten_bdx'] = df_merge['ma_buu_cuc'].map(bc_to_ten_bc)
        df_merge['ma_bdx'] = df_merge['ma_buu_cuc']
        df_merge['ten_cum'] = cum

        return df_merge.reset_index(drop=True)

def register_service_callbacks(app):
    """Đăng ký các callback động cho các trang dịch vụ (BCCP, HCC, TCBC, PPBL) sử dụng mô hình Pattern Matching Callbacks hoặc tương tự"""
    
    # Để tránh việc trùng lặp code và hỗ trợ prefix linh động, ta đăng ký callbacks cho 4 dịch vụ thông qua 4 bộ prefix khác nhau.
    # Các prefix: bccp-overview, hcc-overview, tcbc-overview, ppbl-overview
    for prefix in ["bccp-overview", "hcc-overview", "tcbc-overview", "ppbl-overview"]:
        
        # Hàm closure tạo callback riêng biệt cho mỗi prefix
        def make_callbacks(pfx):
            @app.callback(
                [
                    Output(f"{pfx}-top10-prev-container", "children"),
                    Output(f"{pfx}-top10-yoy-container", "children"),
                    Output(f"{pfx}-top10-plan-container", "children"),
                    Output(f"{pfx}-stacked-bar-12p", "figure")
                ] + [
                    # Output cho tối đa 10 KPI cards con
                    Output(f"{pfx}-sub-{i}-value", "children") for i in range(10)
                ] + [
                    Output(f"{pfx}-sub-{i}-compare-prev", "children") for i in range(10)
                ] + [
                    Output(f"{pfx}-sub-{i}-compare-prev", "style") for i in range(10)
                ] + [
                    Output(f"{pfx}-sub-{i}-compare-yoy", "children") for i in range(10)
                ] + [
                    Output(f"{pfx}-sub-{i}-compare-yoy", "style") for i in range(10)
                ] + [
                    Output(f"{pfx}-sub-{i}-compare-plan", "children") for i in range(10)
                ] + [
                    Output(f"{pfx}-sub-{i}-compare-plan", "style") for i in range(10)
                ],
                [Input("btn-apply-filter", "n_clicks")],
                [
                    State("sidebar-year", "value"),
                    State("sidebar-month-select", "value"),
                    State("sidebar-week-select", "value"),
                    State("sidebar-period", "value"),
                    State("sidebar-cum", "value"),
                    State("sidebar-bdx", "value"),
                    State("sidebar-buu-cuc", "value")
                ]
            )
            def update_service_dashboard(n_clicks, year, month, week, cycle, cum, bdx, buu_cuc):
                # Khởi tạo toàn bộ outputs rỗng (74 outputs = 4 + 7 * 10)
                empty_kpis = []
                for _ in range(10):
                    empty_kpis.extend(["—", "—", {"color": "#64748B"}, "—", {"color": "#64748B"}, "—", {"color": "#64748B"}])
                default_returns = ["Không có dữ liệu", "Không có dữ liệu", "Không có dữ liệu", go.Figure()] + empty_kpis
                
                service_map = {
                    "bccp-overview": "BCCP",
                    "hcc-overview": "HCC",
                    "tcbc-overview": "TCBC",
                    "ppbl-overview": "PPBL"
                }
                service_key = service_map.get(pfx)
                if not service_key:
                    return default_returns
                    
                from pages.service_overview import get_sub_services
                sub_services = get_sub_services(service_key)
                
                if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
                    return default_returns
                    
                if service_key == "BCCP":
                    order = {"Truyền thống": 0, "TMĐT": 1, "Quốc tế": 2, "Phát hành báo chí": 3}
                    sub_services = sorted(sub_services, key=lambda x: order.get(x, 99))
                
                period_val = month if cycle == 'Tháng' else week
                
                conn = sqlite3.connect(str(DB_PATH))
                
                try:
                    # 1. Query Top 10 của dịch vụ chính
                    df_top_prev = get_top10_by_comparison(conn, cycle, period_val, year, 'prev', cum=cum, bdx=bdx, buu_cuc=buu_cuc, service_key=service_key)
                    df_top_yoy = get_top10_by_comparison(conn, cycle, period_val, year, 'yoy', cum=cum, bdx=bdx, buu_cuc=buu_cuc, service_key=service_key)
                    df_top_plan = get_top10_by_comparison(conn, cycle, period_val, year, 'plan', cum=cum, bdx=bdx, buu_cuc=buu_cuc, service_key=service_key)
                    
                    top10_prev = create_top10_table_sub(df_top_prev)
                    top10_yoy = create_top10_table_sub(df_top_yoy)
                    top10_plan = create_top10_table_sub(df_top_plan, is_plan=True)
                    
                    # 2. Query doanh thu 12 kỳ của các dịch vụ con
                    df_12p = get_12_periods_revenue_sub(conn, service_key, cycle, period_val, year, sub_services, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    
                    fig = go.Figure()
                    sub_colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#6366F1", "#14B8A6"]
                    if not df_12p.empty:
                        for idx, sub in enumerate(sub_services):
                            if sub in df_12p.columns:
                                fig.add_trace(go.Bar(
                                    name=sub,
                                    x=df_12p["label"],
                                    y=df_12p[sub],
                                    marker_color=sub_colors[idx % len(sub_colors)],
                                    hovertemplate=f"{sub}: %{{y:,.0f}} đ<extra></extra>"
                                ))
                                
                    fig.update_layout(
                        barmode="stack",
                        margin=dict(t=20, b=20, l=60, r=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                        height=320,
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
                    )
                    
                    # 3. Tính toán các KPI Cards con
                    # Doanh thu kỳ này
                    rev_cur = query_sub_revenue_total(conn, service_key, cycle, period_val, year, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    
                    # Doanh thu kỳ trước
                    prev_val, prev_yr = get_prev_period_info(cycle, period_val, year)
                    rev_prev = query_sub_revenue_total(conn, service_key, cycle, prev_val, prev_yr, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    
                    # Doanh thu cùng kỳ năm trước
                    if cycle == 'Tháng':
                        rev_yoy = query_sub_revenue_total(conn, service_key, cycle, period_val, year - 1, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    else:
                        from analytics.global_metrics import get_weekly_yoy_query_params
                        prev_yr, w_ratios = get_weekly_yoy_query_params(year, period_val)
                        rev_yoy = query_sub_revenue_total(conn, service_key, cycle, period_val, prev_yr, cum=cum, bdx=bdx, buu_cuc=buu_cuc, w_ratios=w_ratios)
                    
                    # Kế hoạch
                    rev_plan = get_plans_current_period_sub(DB_PATH, service_key, cycle, period_val, year, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    
                    kpi_outputs = []
                    # Lặp qua tất cả 10 slot KPI cards
                    for i in range(10):
                        if i < len(sub_services):
                            sub = sub_services[i]
                            cur_val = rev_cur.get(sub, 0.0)
                            p_val = rev_prev.get(sub, 0.0)
                            y_val = rev_yoy.get(sub, 0.0)
                            pl_val = rev_plan.get(sub, 0.0)
                            
                            # Kỳ trước
                            if p_val > 0:
                                pct_p = (cur_val - p_val) * 100.0 / p_val
                                p_str = f"{pct_p:+.1f}%"
                                p_style = {"color": "#10B981" if pct_p >= 0 else "#EF4444", "fontWeight": "bold"}
                            else:
                                p_str = "—"
                                p_style = {"color": "#64748B"}
                                
                            # Cùng kỳ
                            if y_val > 0:
                                pct_y = (cur_val - y_val) * 100.0 / y_val
                                y_str = f"{pct_y:+.1f}%"
                                y_style = {"color": "#10B981" if pct_y >= 0 else "#EF4444", "fontWeight": "bold"}
                            else:
                                y_str = "—"
                                y_style = {"color": "#64748B"}
                                
                            # Kế hoạch
                            if pl_val > 0:
                                pct_pl = (cur_val / pl_val) * 100.0
                                pl_str = f"{pct_pl:.1f}%"
                                pl_style = {"color": "#10B981" if pct_pl >= 100 else "#F59E0B", "fontWeight": "bold"}
                            else:
                                pl_str = "—"
                                pl_style = {"color": "#64748B"}
                                
                            kpi_outputs.append(format_revenue(cur_val))
                            kpi_outputs.append(p_str)
                            kpi_outputs.append(p_style)
                            kpi_outputs.append(y_str)
                            kpi_outputs.append(y_style)
                            kpi_outputs.append(pl_str)
                            kpi_outputs.append(pl_style)
                        else:
                            # Slot không dùng thì trả về mặc định ẩn/trống
                            kpi_outputs.extend(["", "", {"display": "none"}, "", {"display": "none"}, "", {"display": "none"}])
                            
                    # Sắp xếp đúng thứ tự output: 4 containers + 70 kpi outputs
                    # Dashboard return 4 containers + 70 kpis
                    
                    # Tách kpi_outputs thành các mảng song song tương ứng với list Outputs
                    val_outputs = kpi_outputs[0::7]      # 10 values
                    p_str_outputs = kpi_outputs[1::7]    # 10 prev strings
                    p_style_outputs = kpi_outputs[2::7]  # 10 prev styles
                    y_str_outputs = kpi_outputs[3::7]    # 10 yoy strings
                    y_style_outputs = kpi_outputs[4::7]  # 10 yoy styles
                    pl_str_outputs = kpi_outputs[5::7]   # 10 plan strings
                    pl_style_outputs = kpi_outputs[6::7] # 10 plan styles
                    
                    all_final_returns = [top10_prev, top10_yoy, top10_plan, fig] + val_outputs + p_str_outputs + p_style_outputs + y_str_outputs + y_style_outputs + pl_str_outputs + pl_style_outputs
                    return all_final_returns
                    
                except Exception as e:
                    logger.error(f"Lỗi update service dashboard cho {service_key}: {e}")
                    import traceback
                    traceback.print_exc()
                    return default_returns
                finally:
                    conn.close()
            update_service_dashboard.__name__ = f"update_service_dashboard_{pfx.replace('-', '_')}"

            @app.callback(
                Output(f"{pfx}-table-a-container", "children"),
                [
                    Input("btn-apply-filter", "n_clicks"),
                    Input(f"{pfx}-table-a-compare-selector", "value")
                ],
                [
                    State("sidebar-year", "value"),
                    State("sidebar-month-select", "value"),
                    State("sidebar-week-select", "value"),
                    State("sidebar-period", "value"),
                    State("sidebar-cum", "value"),
                    State("sidebar-bdx", "value"),
                    State("sidebar-buu-cuc", "value")
                ]
            )
            def update_service_table_a(n_clicks, compare_type, year, month, week, cycle, cum, bdx, buu_cuc):
                service_map = {
                    "bccp-overview": "BCCP",
                    "hcc-overview": "HCC",
                    "tcbc-overview": "TCBC",
                    "ppbl-overview": "PPBL"
                }
                service_key = service_map.get(pfx)
                if not service_key:
                    return html.Div("Không xác định được loại dịch vụ.")
                    
                from pages.service_overview import get_sub_services
                sub_services = get_sub_services(service_key)
                
                if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
                    return html.Div("Vui lòng chọn bộ lọc thời gian để xem chi tiết.")
                    
                if service_key == "BCCP":
                    order = {"Truyền thống": 0, "TMĐT": 1, "Quốc tế": 2, "Phát hành báo chí": 3}
                    sub_services = sorted(sub_services, key=lambda x: order.get(x, 99))
                
                period_val = month if cycle == 'Tháng' else week
                
                conn = sqlite3.connect(str(DB_PATH))
                try:
                    # Tính nhãn title_label động
                    title_label = "⭐️ TOÀN TỈNH"
                    if buu_cuc and buu_cuc != "Tất cả":
                        cursor = conn.cursor()
                        cursor.execute("SELECT ten_buu_cuc FROM dim_buucuc WHERE ma_buu_cuc = ?", (buu_cuc,))
                        row = cursor.fetchone()
                        if row:
                            title_label = f"⭐️ BC: {row[0].upper()}"
                        else:
                            title_label = f"⭐️ BC: {buu_cuc.upper()}"
                    elif bdx and bdx != "Tất cả":
                        title_label = f"⭐️ XÃ: {bdx.upper()}"
                    elif cum and cum != "Tất cả" and cum != "Tất cả Cụm":
                        title_label = f"⭐️ CỤM: {cum.upper()}"
                        
                    df = query_sub_service_data(conn, service_key, cycle, period_val, year, sub_services, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    return create_detail_table_sub(df, sub_services, compare_type, title_label=title_label)
                except Exception as e:
                    return html.Div(f"Lỗi load bảng chi tiết xã: {e}")
                finally:
                    conn.close()
            update_service_table_a.__name__ = f"update_service_table_a_{pfx.replace('-', '_')}"

            @app.callback(
                Output(f"{pfx}-table-b-container", "children"),
                [
                    Input("btn-apply-filter", "n_clicks"),
                    Input(f"{pfx}-table-b-compare-selector", "value")
                ],
                [
                    State("sidebar-year", "value"),
                    State("sidebar-month-select", "value"),
                    State("sidebar-week-select", "value"),
                    State("sidebar-period", "value"),
                    State("sidebar-cum", "value"),
                    State("sidebar-bdx", "value"),
                    State("sidebar-buu-cuc", "value")
                ]
            )
            def update_service_table_b(n_clicks, compare_type, year, month, week, cycle, cum, bdx, buu_cuc):
                service_map = {
                    "bccp-overview": "BCCP",
                    "hcc-overview": "HCC",
                    "tcbc-overview": "TCBC",
                    "ppbl-overview": "PPBL"
                }
                service_key = service_map.get(pfx)
                if not service_key:
                    return html.Div("Không xác định được loại dịch vụ.")
                    
                from pages.service_overview import get_sub_services
                sub_services = get_sub_services(service_key)
                
                if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
                    return html.Div("Vui lòng chọn bộ lọc thời gian để xem chi tiết.")
                    
                if service_key == "BCCP":
                    order = {"Truyền thống": 0, "TMĐT": 1, "Quốc tế": 2, "Phát hành báo chí": 3}
                    sub_services = sorted(sub_services, key=lambda x: order.get(x, 99))
                
                period_val = month if cycle == 'Tháng' else week
                
                conn = sqlite3.connect(str(DB_PATH))
                try:
                    # Tính nhãn title_label động
                    title_label = "⭐️ TOÀN TỈNH"
                    if buu_cuc and buu_cuc != "Tất cả":
                        cursor = conn.cursor()
                        cursor.execute("SELECT ten_buu_cuc FROM dim_buucuc WHERE ma_buu_cuc = ?", (buu_cuc,))
                        row = cursor.fetchone()
                        if row:
                            title_label = f"⭐️ BC: {row[0].upper()}"
                        else:
                            title_label = f"⭐️ BC: {buu_cuc.upper()}"
                    elif bdx and bdx != "Tất cả":
                        title_label = f"⭐️ XÃ: {bdx.upper()}"
                    elif cum and cum != "Tất cả" and cum != "Tất cả Cụm":
                        title_label = f"⭐️ CỤM: {cum.upper()}"
                        
                    df = query_sub_service_data_ytd(conn, service_key, cycle, period_val, year, sub_services, cum=cum, bdx=bdx, buu_cuc=buu_cuc)
                    return create_detail_table_sub(df, sub_services, compare_type, title_label=title_label)
                except Exception as e:
                    return html.Div(f"Lỗi load bảng lũy kế YTD: {e}")
                finally:
                    conn.close()
            update_service_table_b.__name__ = f"update_service_table_b_{pfx.replace('-', '_')}"
            
        # Chạy hàm khởi tạo callbacks
        make_callbacks(prefix)

def query_sub_revenue_total(conn, service_key, period_type, period_val, year, cum=None, bdx=None, buu_cuc=None, w_ratios=None):
    """Tính tổng doanh thu hiện tại theo từng nhóm dịch vụ con"""
    res = {}
    cursor = conn.cursor()
    if period_type == 'Tháng':
        sql = """
            SELECT a.nhom_dich_vu, SUM(a.tong_doanh_thu) 
            FROM agg_monthly a
            INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
            WHERE a.nam = ? AND a.thang = ? AND a.nhom_dich_vu IN (
                SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
            )
        """
        params = [year, period_val, service_key]
    else:
        if w_ratios:
            cases = []
            for w_num, ratio in w_ratios:
                cases.append(f"WHEN a.tuan_so = {w_num} THEN a.tong_doanh_thu * {ratio:.8f}")
            cases_str = " + ".join(cases)
            sql = f"""
                SELECT a.nhom_dich_vu, SUM(CASE {cases_str} ELSE 0 END) 
                FROM agg_weekly a
                INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
                WHERE a.nam = ? AND a.tuan_so IN ({','.join(str(w[0]) for w in w_ratios)}) AND a.nhom_dich_vu IN (
                    SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
                )
            """
            params = [year, service_key]
        else:
            sql = """
                SELECT a.nhom_dich_vu, SUM(a.tong_doanh_thu) 
                FROM agg_weekly a
                INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
                WHERE a.nam = ? AND a.tuan_so = ? AND a.nhom_dich_vu IN (
                    SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?
                )
            """
            params = [year, period_val, service_key]
            
    clauses = []
    if cum and cum != "Tất cả":
        clauses.append("b.ten_cum = ?")
        params.append(cum)
    if bdx and bdx != "Tất cả":
        clauses.append("b.ten_bdx = ?")
        params.append(bdx)
    if buu_cuc and buu_cuc != "Tất cả":
        clauses.append("a.ma_buu_cuc = ?")
        params.append(buu_cuc)
        
    if clauses:
        sql += " AND " + " AND ".join(clauses)
    sql += " GROUP BY a.nhom_dich_vu"
    
    cursor.execute(sql, tuple(params))
    for nhom, dt in cursor.fetchall():
        res[nhom] = dt or 0.0
    return res

def get_12_periods_revenue_sub(conn, service_key, period_type, current_period, current_year, sub_services, cum=None, bdx=None, buu_cuc=None):
    """Lấy dữ liệu doanh thu của 12 kỳ của các dịch vụ con thuộc service_key"""
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
        row_dict = {'label': label}
        for sub in sub_services:
            row_dict[sub] = 0.0
            
        if period_type == 'Tháng':
            query = """
                SELECT a.nhom_dich_vu, SUM(a.tong_doanh_thu) as dt
                FROM agg_monthly a
                INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
                WHERE a.nam = ? AND a.thang = ? AND a.nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            """
        else: # Tuần
            query = """
                SELECT a.nhom_dich_vu, SUM(a.tong_doanh_thu) as dt
                FROM agg_weekly a
                INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc
                WHERE a.nam = ? AND a.tuan_so = ? AND a.nhom_dich_vu IN (SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = ?)
            """
        
        clauses = []
        params = [yr, val, service_key]
        if cum and cum != "Tất cả":
            clauses.append("b.ten_cum = ?")
            params.append(cum)
        if bdx and bdx != "Tất cả":
            clauses.append("b.ten_bdx = ?")
            params.append(bdx)
        if buu_cuc and buu_cuc != "Tất cả":
            clauses.append("a.ma_buu_cuc = ?")
            params.append(buu_cuc)
            
        if clauses:
            query += " AND " + " AND ".join(clauses)
        query += " GROUP BY a.nhom_dich_vu"
        
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        for nhom, dt in cursor.fetchall():
            if nhom in row_dict:
                row_dict[nhom] = dt or 0.0
                
        result_data.append(row_dict)
        
    return pd.DataFrame(result_data)