# -*- coding: utf-8 -*-
"""
Callbacks quản lý biểu đồ, KPI cards, top 10 xã và các bảng chi tiết trang Tổng quan chung v2.0.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from dash import Output, Input, State, html, dash_table
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# Setup sys.path để import cấu hình
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH, SERVICE_COLORS
from callbacks.utils import format_revenue
from analytics.global_metrics import (
    get_total_revenue_by_service,
    get_top10_by_comparison,
    get_12_periods_revenue,
    get_period_detail_by_xa,
    get_ytd_detail_by_xa
)

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

def get_plans_current_period(db_path, period_type, period_value, year, cum=None, bdx=None, buu_cuc=None):
    """Lấy kế hoạch doanh thu của 4 dịch vụ trong kỳ hiện tại, có bộ lọc địa lý chi tiết"""
    res = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
    conn = sqlite3.connect(str(db_path))
    try:
        table = 'plans' if period_type == 'Tháng' else 'plans_weekly'
        time_col = 'thang' if period_type == 'Tháng' else 'tuan_so'
        
        sql = f"SELECT nhom_chinh, SUM(ke_hoach_doanh_thu) FROM {table}"
        where = ["nam = ?", f"{time_col} = ?"]
        params = [year, period_value]
        
        if (cum and cum != "Tất cả" and cum != "Tất cả Cụm") or (bdx and bdx != "Tất cả") or (buu_cuc and buu_cuc != "Tất cả"):
            sql += f" INNER JOIN dim_buucuc b ON {table}.ma_buu_cuc = b.ma_buu_cuc"
            
        if cum and cum != "Tất cả" and cum != "Tất cả Cụm":
            where.append("b.ten_cum = ?")
            params.append(cum)
        if bdx and bdx != "Tất cả":
            where.append("b.ten_bdx = ?")
            params.append(bdx)
        if buu_cuc and buu_cuc != "Tất cả":
            where.append(f"{table}.ma_buu_cuc = ?")
            params.append(buu_cuc)
            
        sql += " WHERE " + " AND ".join(where) + " GROUP BY nhom_chinh"
        
        cursor = conn.cursor()
        cursor.execute(sql, params)
        for r in cursor.fetchall():
            if r[0] in res:
                res[r[0]] += r[1] or 0.0
    except Exception as e:
        logger.error(f"Lỗi lấy kế hoạch kỳ: {e}")
    finally:
        conn.close()
    return res

def get_aggregated_revenue(db_path, cycle, year, period_val, cum=None, bdx=None, buu_cuc=None, w_ratios=None):
    """Tính tổng doanh thu từ bảng agg_monthly/agg_weekly theo 4 nhóm dịch vụ chính, có bộ lọc địa lý chi tiết"""
    res = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
    conn = sqlite3.connect(str(db_path))
    try:
        table = 'agg_monthly' if cycle == 'Tháng' else 'agg_weekly'
        time_col = 'thang' if cycle == 'Tháng' else 'tuan_so'
        
        if cycle == 'Tuần' and w_ratios:
            cases = []
            for w_num, ratio in w_ratios:
                cases.append(f"WHEN a.tuan_so = {w_num} THEN a.tong_doanh_thu * {ratio:.8f}")
            cases_str = " + ".join(cases)
            
            sql = f"""
                SELECT COALESCE(
                    (SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 
                    'Khác'
                ) as nhom, SUM(CASE {cases_str} ELSE 0 END)
                FROM agg_weekly a
            """
            where = ["a.nam = ?", f"a.tuan_so IN ({','.join(str(w[0]) for w in w_ratios)})"]
            params = [year]
        else:
            sql = f"""
                SELECT COALESCE(
                    (SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 
                    'Khác'
                ) as nhom, SUM(a.tong_doanh_thu)
                FROM {table} a
            """
            where = ["a.nam = ?", f"a.{time_col} = ?"]
            params = [year, period_val]
            
        if (cum and cum != "Tất cả" and cum != "Tất cả Cụm") or (bdx and bdx != "Tất cả") or (buu_cuc and buu_cuc != "Tất cả"):
            sql += " INNER JOIN dim_buucuc b ON a.ma_buu_cuc = b.ma_buu_cuc"
            
        if cum and cum != "Tất cả" and cum != "Tất cả Cụm":
            where.append("b.ten_cum = ?")
            params.append(cum)
        if bdx and bdx != "Tất cả":
            where.append("b.ten_bdx = ?")
            params.append(bdx)
        if buu_cuc and buu_cuc != "Tất cả":
            where.append("a.ma_buu_cuc = ?")
            params.append(buu_cuc)
            
        sql += " WHERE " + " AND ".join(where)
        sql += """ GROUP BY COALESCE(
            (SELECT d.nhom_chinh FROM dim_dichvu d WHERE d.nhom_dich_vu = a.nhom_dich_vu OR d.ten_dich_vu = a.nhom_dich_vu LIMIT 1), 
            'Khác'
        )"""
        logger.debug(f"DEBUG get_aggregated_revenue SQL: {sql} with params {params}")
        cursor = conn.cursor()
        cursor.execute(sql, params)
        for row in cursor.fetchall():
            nhom = row[0]
            val = row[1] or 0.0
            if nhom in res:
                res[nhom] += val
    except Exception as e:
        logger.error(f"Lỗi tính doanh thu aggregated: {e}")
    finally:
        conn.close()
    return res

def create_top10_table(df, is_plan=False):
    """Render bảng top 10 đơn giản đẹp mắt"""
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

def create_detail_table(df, compare_type, title_label="⭐️ TOÀN TỈNH"):
    """Tạo DataTable hiển thị danh sách chi tiết xã"""
    if df.empty:
        return html.Div("Không có dữ liệu", style={"textAlign": "center", "padding": "20px"})
        
    # Thêm cột % So sánh tùy thuộc compare_type
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
    prov_row = pd.DataFrame([{
        "ten_cum": title_label,
        "ten_bdx": "",
        "BCCP": df["BCCP"].sum(),
        "HCC": df["HCC"].sum(),
        "TCBC": df["TCBC"].sum(),
        "PPBL": df["PPBL"].sum(),
        "tong_dt": df["tong_dt"].sum(),
        "dt_prev": df["dt_prev"].sum(),
        "dt_yoy": df["dt_yoy"].sum(),
        "plan_dt": df["plan_dt"].sum(),
    }])
    
    # Tính lại % so sánh cho dòng Toàn tỉnh
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
    else:
        cmp_col = 'plan_dt'
        cmp_col_name = "Kế hoạch"

    # Định dạng các cột hiển thị số tiền
    df_display = df_final.copy()
    for col in ["BCCP", "HCC", "TCBC", "PPBL", "tong_dt", cmp_col]:
        if col in df_display.columns:
            df_display[col] = df_display[col].map(lambda x: f"{x:,.0f} đ" if pd.notna(x) and x > 0 else "0 đ")

    columns = [
        {"name": "Cụm", "id": "ten_cum"},
        {"name": "Xã / Bưu cục", "id": "ten_bdx"},
        {"name": "BCCP", "id": "BCCP"},
        {"name": "HCC", "id": "HCC"},
        {"name": "TCBC", "id": "TCBC"},
        {"name": "PPBL", "id": "PPBL"},
        {"name": "Tổng DT", "id": "tong_dt"},
        {"name": cmp_col_name, "id": cmp_col},
        {"name": ratio_col_name, "id": "ratio_display"}
    ]

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
            {"if": {"column_id": ["BCCP", "HCC", "TCBC", "PPBL"]}, "maxWidth": "110px", "textAlign": "right"},
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


def register_global_callbacks(app):
    """Đăng ký các callback mới cho trang Tổng quan chung v2.0"""
    
    @app.callback(
        [
            # KPI Cards (BCCP)
            Output("global-kpi-bccp-value", "children"),
            Output("global-kpi-bccp-compare-prev", "children"),
            Output("global-kpi-bccp-compare-prev", "style"),
            Output("global-kpi-bccp-compare-yoy", "children"),
            Output("global-kpi-bccp-compare-yoy", "style"),
            Output("global-kpi-bccp-compare-plan", "children"),
            Output("global-kpi-bccp-compare-plan", "style"),
            
            # KPI Cards (HCC)
            Output("global-kpi-hcc-value", "children"),
            Output("global-kpi-hcc-compare-prev", "children"),
            Output("global-kpi-hcc-compare-prev", "style"),
            Output("global-kpi-hcc-compare-yoy", "children"),
            Output("global-kpi-hcc-compare-yoy", "style"),
            Output("global-kpi-hcc-compare-plan", "children"),
            Output("global-kpi-hcc-compare-plan", "style"),
            
            # KPI Cards (TCBC)
            Output("global-kpi-tcbc-value", "children"),
            Output("global-kpi-tcbc-compare-prev", "children"),
            Output("global-kpi-tcbc-compare-prev", "style"),
            Output("global-kpi-tcbc-compare-yoy", "children"),
            Output("global-kpi-tcbc-compare-yoy", "style"),
            Output("global-kpi-tcbc-compare-plan", "children"),
            Output("global-kpi-tcbc-compare-plan", "style"),
            
            # KPI Cards (PPBL)
            Output("global-kpi-ppbl-value", "children"),
            Output("global-kpi-ppbl-compare-prev", "children"),
            Output("global-kpi-ppbl-compare-prev", "style"),
            Output("global-kpi-ppbl-compare-yoy", "children"),
            Output("global-kpi-ppbl-compare-yoy", "style"),
            Output("global-kpi-ppbl-compare-plan", "children"),
            Output("global-kpi-ppbl-compare-plan", "style"),
            
            # Top 10 Containers
            Output("global-top10-prev-container", "children"),
            Output("global-top10-yoy-container", "children"),
            Output("global-top10-plan-container", "children"),
            
            # 12 periods Graph
            Output("global-stacked-bar-12p", "figure")
        ],
        [Input("btn-apply-filter", "n_clicks")],
        [
            State("sidebar-year", "value"),
            State("sidebar-month-select", "value"),
            State("sidebar-week-select", "value"),
            State("sidebar-period", "value"), # 'Tháng' hoặc 'Tuần'
            State("sidebar-cum", "value"),
            State("sidebar-bdx", "value"),
            State("sidebar-buu-cuc", "value")
        ]
    )
    def update_global_dashboard(n_clicks, year, month, week, cycle, cum, bdx, buu_cuc):
        logger.debug(f"DEBUG update_global_dashboard: cycle={cycle}, year={year}, month={month}, week={week}, cum={cum}, bdx={bdx}, buu_cuc={buu_cuc}")
        if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
            # Return empty/fallback values if filter is incomplete
            empty_kpi = ["—", "—", {"color": "#94A3B8"}, "—", {"color": "#94A3B8"}, "—", {"color": "#94A3B8"}]
            return empty_kpi * 4 + ["Không có dữ liệu", "Không có dữ liệu", "Không có dữ liệu", go.Figure()]
            
        period_val = month if cycle == 'Tháng' else week
        
        conn = sqlite3.connect(str(DB_PATH))
        
        try:
            # 1. KPI Calculation
            # Doanh thu hiện tại
            rev_cur = get_aggregated_revenue(DB_PATH, cycle, year, period_val, cum, bdx, buu_cuc)
            
            # Doanh thu kỳ trước
            prev_val, prev_yr = get_prev_period_info(cycle, period_val, year)
            rev_prev = get_aggregated_revenue(DB_PATH, cycle, prev_yr, prev_val, cum, bdx, buu_cuc)
                    
            # Doanh thu cùng kỳ năm trước
            if cycle == 'Tháng':
                rev_yoy = get_aggregated_revenue(DB_PATH, cycle, year - 1, period_val, cum, bdx, buu_cuc)
            else:
                from analytics.global_metrics import get_weekly_yoy_query_params
                prev_yr, w_ratios = get_weekly_yoy_query_params(year, period_val)
                rev_yoy = get_aggregated_revenue(DB_PATH, cycle, prev_yr, period_val, cum, bdx, buu_cuc, w_ratios=w_ratios)
                    
            # Kế hoạch kỳ hiện tại
            rev_plan = get_plans_current_period(DB_PATH, cycle, period_val, year, cum, bdx, buu_cuc)
            
            kpi_outputs = []
            for service in ["BCCP", "HCC", "TCBC", "PPBL"]:
                cur_dt = rev_cur.get(service, 0.0)
                prev_dt = rev_prev.get(service, 0.0)
                yoy_dt = rev_yoy.get(service, 0.0)
                plan_dt = rev_plan.get(service, 0.0)
                
                # So sánh kỳ trước
                if prev_dt > 0:
                    pct_prev = (cur_dt - prev_dt) * 100.0 / prev_dt
                    pct_prev_str = f"{pct_prev:+.1f}%"
                    pct_prev_style = {"color": "#10B981" if pct_prev >= 0 else "#EF4444", "fontWeight": "bold"}
                else:
                    pct_prev_str = "—"
                    pct_prev_style = {"color": "#64748B"}
                    
                # So cùng kỳ YoY
                if yoy_dt > 0:
                    pct_yoy = (cur_dt - yoy_dt) * 100.0 / yoy_dt
                    pct_yoy_str = f"{pct_yoy:+.1f}%"
                    pct_yoy_style = {"color": "#10B981" if pct_yoy >= 0 else "#EF4444", "fontWeight": "bold"}
                else:
                    pct_yoy_str = "—"
                    pct_yoy_style = {"color": "#64748B"}
                    
                # So kế hoạch
                if plan_dt > 0:
                    pct_plan = (cur_dt / plan_dt) * 100.0
                    pct_plan_str = f"{pct_plan:.1f}%"
                    pct_plan_style = {"color": "#10B981" if pct_plan >= 100.0 else "#F59E0B", "fontWeight": "bold"}
                else:
                    pct_plan_str = "—"
                    pct_plan_style = {"color": "#64748B"}
                    
                kpi_outputs.extend([
                    format_revenue(cur_dt),
                    pct_prev_str, pct_prev_style,
                    pct_yoy_str, pct_yoy_style,
                    pct_plan_str, pct_plan_style
                ])
                
            # 2. Top 10 Tables
            df_top_prev = get_top10_by_comparison(conn, cycle, period_val, year, 'prev', cum, bdx, buu_cuc)
            df_top_yoy = get_top10_by_comparison(conn, cycle, period_val, year, 'yoy', cum, bdx, buu_cuc)
            df_top_plan = get_top10_by_comparison(conn, cycle, period_val, year, 'plan', cum, bdx, buu_cuc)
            
            top10_prev_layout = create_top10_table(df_top_prev)
            top10_yoy_layout = create_top10_table(df_top_yoy)
            top10_plan_layout = create_top10_table(df_top_plan, is_plan=True)
            
            # 3. 12 Periods Graph — Line chart (5 lines: Tổng + 4 nhóm dịch vụ)
            df_12p = get_12_periods_revenue(conn, cycle, period_val, year, cum, bdx, buu_cuc)
            
            fig = go.Figure()
            if not df_12p.empty:
                # Tính tổng doanh thu
                df_12p["Tổng"] = df_12p[["BCCP", "HCC", "TCBC", "PPBL"]].sum(axis=1)
                
                LINE_COLORS = {
                    "Tổng": "#1E293B",
                    "BCCP": SERVICE_COLORS.get("BCCP", "#3B82F6"),
                    "HCC": SERVICE_COLORS.get("HCC", "#10B981"),
                    "TCBC": SERVICE_COLORS.get("TCBC", "#F59E0B"),
                    "PPBL": SERVICE_COLORS.get("PPBL", "#8B5CF6"),
                }
                LINE_WIDTHS = {"Tổng": 3, "BCCP": 2, "HCC": 2, "TCBC": 2, "PPBL": 2}
                
                for service in ["Tổng", "BCCP", "HCC", "TCBC", "PPBL"]:
                    fig.add_trace(go.Scatter(
                        name=service,
                        x=df_12p["label"],
                        y=df_12p[service],
                        mode="lines+markers",
                        line=dict(color=LINE_COLORS[service], width=LINE_WIDTHS[service], dash="solid" if service == "Tổng" else "dot"),
                        marker=dict(size=5 if service == "Tổng" else 4),
                        hovertemplate=f"{service}: %{{y:,.0f}} đ<extra></extra>"
                    ))
                    
            fig.update_layout(
                margin=dict(t=20, b=20, l=60, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
                height=320,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
            )
            
            return kpi_outputs + [top10_prev_layout, top10_yoy_layout, top10_plan_layout, fig]
            
        except Exception as e:
            logger.error(f"Lỗi update global dashboard: {e}")
            import traceback
            traceback.print_exc()
            empty_kpi = ["—", "—", {"color": "#94A3B8"}, "—", {"color": "#94A3B8"}, "—", {"color": "#94A3B8"}]
            return empty_kpi * 4 + [f"Lỗi: {e}", f"Lỗi: {e}", f"Lỗi: {e}", go.Figure()]
        finally:
            conn.close()

    # Callback riêng cho Bảng A (Kỳ hiện tại)
    @app.callback(
        Output("global-table-a-container", "children"),
        [
            Input("btn-apply-filter", "n_clicks"),
            Input("global-table-a-compare-selector", "value")
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
    def update_table_a(n_clicks, compare_type, year, month, week, cycle, cum, bdx, buu_cuc):
        if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
            return html.Div("Vui lòng chọn bộ lọc thời gian để xem chi tiết.")
            
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
                
            df = get_period_detail_by_xa(conn, cycle, period_val, year, cum, bdx, buu_cuc)
            return create_detail_table(df, compare_type, title_label=title_label)
        except Exception as e:
            return html.Div(f"Lỗi load bảng kỳ hiện tại: {e}")
        finally:
            conn.close()

    # Callback riêng cho Bảng B (Lũy kế YTD)
    @app.callback(
        Output("global-table-b-container", "children"),
        [
            Input("btn-apply-filter", "n_clicks"),
            Input("global-table-b-compare-selector", "value")
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
    def update_table_b(n_clicks, compare_type, year, month, week, cycle, cum, bdx, buu_cuc):
        if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
            return html.Div("Vui lòng chọn bộ lọc thời gian để xem chi tiết.")
            
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
                
            df = get_ytd_detail_by_xa(conn, cycle, period_val, year, cum, bdx, buu_cuc)
            return create_detail_table(df, compare_type, title_label=title_label)
        except Exception as e:
            return html.Div(f"Lỗi load bảng lũy kế YTD: {e}")
        finally:
            conn.close()
