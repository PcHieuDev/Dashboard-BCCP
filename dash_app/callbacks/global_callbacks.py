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

def get_plans_current_period(db_path, period_type, period_value, year):
    """Lấy kế hoạch doanh thu của 4 dịch vụ trong kỳ hiện tại"""
    res = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        if period_type == 'Tháng':
            sql = "SELECT nhom_dich_vu, SUM(ke_hoach_doanh_thu) FROM plans WHERE nam = ? AND thang = ? GROUP BY nhom_dich_vu"
        else:
            sql = "SELECT nhom_dich_vu, SUM(ke_hoach_doanh_thu) FROM plans_weekly WHERE nam = ? AND tuan_so = ? GROUP BY nhom_dich_vu"
        cursor.execute(sql, (year, period_value))
        for r in cursor.fetchall():
            if r[0] in res:
                res[r[0]] = r[1] or 0.0
    except Exception as e:
        print(f"Lỗi lấy kế hoạch kỳ: {e}")
    finally:
        conn.close()
    return res

def create_top10_table(df):
    """Render bảng top 10 đơn giản đẹp mắt"""
    if df.empty:
        return html.Div("Không có dữ liệu phù hợp", style={"color": "#64748B", "fontSize": "12px", "textAlign": "center", "padding": "10px"})
        
    rows = []
    for idx, row in df.iterrows():
        ratio_val = row['ratio']
        color = "#10B981" if ratio_val >= 0 else "#EF4444"
        icon = "▲" if ratio_val >= 0 else "▼"
        rows.append(html.Tr([
            html.Td(f"{idx+1}", style={"width": "30px", "fontWeight": "bold", "color": "#64748B"}),
            html.Td(row['ten_cum'], style={"color": "#475569"}),
            html.Td(row['ten_bdx'], style={"fontWeight": "medium", "color": "#0F172A"}),
            html.Td(f"{icon} {abs(ratio_val):.1f}%", style={"color": color, "fontWeight": "bold", "textAlign": "right"})
        ]))
        
    return html.Table([
        html.Tbody(rows)
    ], className="table table-sm table-borderless", style={"fontSize": "12px", "marginBottom": 0})

def create_detail_table(df, compare_type):
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
        df['ratio'] = (df['tong_dt'] / df['plan_dt']) * 100.0
        df['ratio_display'] = df['ratio'].map(lambda x: f"{x:.1f}%" if pd.notna(x) and x != float('inf') and x != float('-inf') else "—")
        ratio_col_name = "Hoàn thành Kế hoạch"
        
    # Tính dòng TOÀN TỈNH
    prov_row = pd.DataFrame([{
        "ten_cum": "⭐️ TOÀN TỈNH",
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
        prov_row['ratio_display'] = prov_row['ratio'].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        
    df_sorted = df.sort_values(by=['ten_cum', 'ten_bdx'], ascending=True)
    df_final = pd.concat([prov_row, df_sorted], ignore_index=True)
    
    # Định dạng các cột hiển thị số tiền
    df_display = df_final.copy()
    for col in ["BCCP", "HCC", "TCBC", "PPBL", "tong_dt"]:
        df_display[col] = df_display[col].map(lambda x: f"{x:,.0f} đ" if x > 0 else "0 đ")
        
    columns = [
        {"name": "Cụm", "id": "ten_cum"},
        {"name": "Xã / Bưu cục", "id": "ten_bdx"},
        {"name": "BCCP", "id": "BCCP"},
        {"name": "HCC", "id": "HCC"},
        {"name": "TCBC", "id": "TCBC"},
        {"name": "PPBL", "id": "PPBL"},
        {"name": "Tổng Doanh Thu", "id": "tong_dt"},
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
            "border": "1px solid #CBD5E1"
        },
        style_cell={
            "padding": "8px 10px",
            "textAlign": "left",
            "fontSize": "13px",
            "fontFamily": "Inter, sans-serif"
        },
        style_data_conditional=[
            {
                # Dòng Toàn tỉnh nổi bật
                "if": {"row_index": 0},
                "backgroundColor": "#EFF6FF",
                "fontWeight": "bold",
                "color": "#1E3A8A"
            },
            {
                "if": {"column_id": "tong_dt"},
                "fontWeight": "bold"
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
            State("sidebar-cycle", "value"), # 'Tháng' hoặc 'Tuần'
            State("sidebar-cum", "value")
        ]
    )
    def update_global_dashboard(n_clicks, year, month, week, cycle, cum):
        if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
            # Return empty/fallback values if filter is incomplete
            empty_kpi = ["—", "—", {"color": "#94A3B8"}, "—", {"color": "#94A3B8"}, "—", {"color": "#94A3B8"}]
            return empty_kpi * 4 + ["Không có dữ liệu", "Không có dữ liệu", "Không có dữ liệu", go.Figure()]
            
        period_val = month if cycle == 'Tháng' else week
        
        conn = sqlite3.connect(str(DB_PATH))
        
        try:
            # 1. KPI Calculation
            # Doanh thu hiện tại
            rev_cur = get_total_revenue_by_service(DB_PATH, year, period_val if cycle == 'Tháng' else None)
            
            # Với tuần, ta phải query tổng doanh thu tuần từ agg_weekly
            if cycle == 'Tuần':
                rev_cur = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT nhom_dich_vu, SUM(tong_doanh_thu) 
                    FROM agg_weekly 
                    WHERE nam = ? AND tuan_so = ?
                    GROUP BY nhom_dich_vu
                """, (year, period_val))
                for nhom, dt in cursor.fetchall():
                    if nhom in rev_cur:
                        rev_cur[nhom] = dt or 0.0
                        
            # Doanh thu kỳ trước
            prev_val, prev_yr = get_prev_period_info(cycle, period_val, year)
            rev_prev = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
            cursor = conn.cursor()
            if cycle == 'Tháng':
                cursor.execute("SELECT nhom_dich_vu, SUM(tong_doanh_thu) FROM agg_monthly WHERE nam = ? AND thang = ? GROUP BY nhom_dich_vu", (prev_yr, prev_val))
            else:
                cursor.execute("SELECT nhom_dich_vu, SUM(tong_doanh_thu) FROM agg_weekly WHERE nam = ? AND tuan_so = ? GROUP BY nhom_dich_vu", (prev_yr, prev_val))
            for nhom, dt in cursor.fetchall():
                if nhom in rev_prev:
                    rev_prev[nhom] = dt or 0.0
                    
            # Doanh thu cùng kỳ năm trước
            rev_yoy = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
            if cycle == 'Tháng':
                cursor.execute("SELECT nhom_dich_vu, SUM(tong_doanh_thu) FROM agg_monthly WHERE nam = ? AND thang = ? GROUP BY nhom_dich_vu", (year - 1, period_val))
            else:
                cursor.execute("SELECT nhom_dich_vu, SUM(tong_doanh_thu) FROM agg_weekly WHERE nam = ? AND tuan_so = ? GROUP BY nhom_dich_vu", (year - 1, period_val))
            for nhom, dt in cursor.fetchall():
                if nhom in rev_yoy:
                    rev_yoy[nhom] = dt or 0.0
                    
            # Kế hoạch kỳ hiện tại
            rev_plan = get_plans_current_period(DB_PATH, cycle, period_val, year)
            
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
            df_top_prev = get_top10_by_comparison(conn, cycle, period_val, year, 'prev')
            df_top_yoy = get_top10_by_comparison(conn, cycle, period_val, year, 'yoy')
            df_top_plan = get_top10_by_comparison(conn, cycle, period_val, year, 'plan')
            
            top10_prev_layout = create_top10_table(df_top_prev)
            top10_yoy_layout = create_top10_table(df_top_yoy)
            top10_plan_layout = create_top10_table(df_top_plan)
            
            # 3. 12 Periods Graph
            df_12p = get_12_periods_revenue(conn, cycle, period_val, year)
            
            fig = go.Figure()
            if not df_12p.empty:
                for service in ["BCCP", "HCC", "TCBC", "PPBL"]:
                    fig.add_trace(go.Bar(
                        name=service,
                        x=df_12p["label"],
                        y=df_12p[service],
                        marker_color=SERVICE_COLORS.get(service, "#64748B"),
                        hovertemplate=f"{service}: %{{y:,.0f}} đ<extra></extra>"
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
            
            return kpi_outputs + [top10_prev_layout, top10_yoy_layout, top10_plan_layout, fig]
            
        except Exception as e:
            print(f"Lỗi update global dashboard: {e}")
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
            State("sidebar-cycle", "value")
        ]
    )
    def update_table_a(n_clicks, compare_type, year, month, week, cycle):
        if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
            return html.Div("Vui lòng chọn bộ lọc thời gian để xem chi tiết.")
            
        period_val = month if cycle == 'Tháng' else week
        conn = sqlite3.connect(str(DB_PATH))
        try:
            df = get_period_detail_by_xa(conn, cycle, period_val, year)
            return create_detail_table(df, compare_type)
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
            State("sidebar-cycle", "value")
        ]
    )
    def update_table_b(n_clicks, compare_type, year, month, week, cycle):
        if not year or (cycle == 'Tháng' and not month) or (cycle == 'Tuần' and not week):
            return html.Div("Vui lòng chọn bộ lọc thời gian để xem chi tiết.")
            
        period_val = month if cycle == 'Tháng' else week
        conn = sqlite3.connect(str(DB_PATH))
        try:
            df = get_ytd_detail_by_xa(conn, cycle, period_val, year)
            return create_detail_table(df, compare_type)
        except Exception as e:
            return html.Div(f"Lỗi load bảng lũy kế YTD: {e}")
        finally:
            conn.close()
