# -*- coding: utf-8 -*-
"""
Callbacks quản lý các biểu đồ, KPI cards và bảng dữ liệu trang Tổng quan chung.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from dash import Output, Input, html, dash_table
import plotly.graph_objects as go

# Setup sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from callbacks.utils import format_revenue
from analytics.global_metrics import (
    get_total_revenue_by_service,
    get_revenue_structure,
    get_ytd_revenue,
    get_ytd_plan,
    get_revenue_by_cum
)

def get_prev_month_year(year, month):
    """Helper tìm tháng trước và năm tương ứng"""
    if month == 1:
        return year - 1, 12
    return year, month - 1

def get_plans_current_month(db_path, year, month, cum):
    """Helper lấy kế hoạch doanh thu của 4 dịch vụ trong tháng hiện tại"""
    sql = "SELECT nhom_dich_vu, SUM(ke_hoach_doanh_thu) FROM plans WHERE nam = :nam AND thang = :thang"
    params = {"nam": year, "thang": month}
    if cum and cum != "Tất cả":
        sql = """
            SELECT p.nhom_dich_vu, SUM(p.ke_hoach_doanh_thu) 
            FROM plans p
            INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_bc
            WHERE p.nam = :nam AND p.thang = :thang AND b.ten_cum = :cum
        """
        params["cum"] = cum
    sql += " GROUP BY nhom_dich_vu"
    
    res = {"BCCP": 0.0, "HCC": 0.0, "TCBC": 0.0, "PPBL": 0.0}
    if not db_path.exists():
        return res
        
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        for r in cursor.fetchall():
            if r[0] in res:
                res[r[0]] = r[1] or 0.0
    except Exception as e:
        print(f"Lỗi lấy kế hoạch tháng: {e}")
    finally:
        conn.close()
    return res

def get_ytd_data_by_cum(db_path, year, month_den):
    """Helper lấy doanh thu & kế hoạch lũy kế YTD theo Cụm để vẽ biểu đồ thanh ngang"""
    thang_list = [f"T{i:02d}" for i in range(1, month_den + 1)]
    
    # 1. Load danh sách Cụm để đảm bảo đủ cụm
    conn = sqlite3.connect(str(db_path))
    try:
        df_cums = pd.read_sql_query("SELECT DISTINCT ten_cum FROM dim_buucuc WHERE ten_cum IS NOT NULL ORDER BY ten_cum", conn)
        cums = df_cums["ten_cum"].tolist()
    except Exception as e:
        print(f"Lỗi load cụm: {e}")
        cums = []
    finally:
        conn.close()
        
    res = {c: {"actual": 0.0, "plan": 0.0} for c in cums}
    
    # 2. Query doanh thu thực tế lũy kế từ transactions (BCCP & HCC cp)
    sql_trans = """
        SELECT b.ten_cum, SUM(t.cuoc_tt_tong) as dt
        FROM transactions t
        INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = :nam AND t.thang_du_lieu IN ({})
        GROUP BY b.ten_cum
    """.format(','.join(f"'{m}'" for m in thang_list))
    
    # 3. Query doanh thu thực tế lũy kế từ 3 bảng mới
    sql_other = """
        SELECT b.ten_cum, SUM(t.doanh_thu) as dt
        FROM (
            SELECT ma_buu_cuc, doanh_thu, nam_du_lieu, thang_du_lieu FROM transactions_hcc
            UNION ALL
            SELECT ma_buu_cuc, doanh_thu, nam_du_lieu, thang_du_lieu FROM transactions_tcbc
            UNION ALL
            SELECT ma_buu_cuc, doanh_thu, nam_du_lieu, thang_du_lieu FROM transactions_ppbl
        ) t
        INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc
        WHERE t.nam_du_lieu = :nam AND t.thang_du_lieu IN ({})
        GROUP BY b.ten_cum
    """.format(','.join(f"'{m}'" for m in thang_list))
    
    # 4. Query kế hoạch lũy kế từ plans
    sql_plan = """
        SELECT b.ten_cum, SUM(p.ke_hoach_doanh_thu) as dt
        FROM plans p
        INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_bc
        WHERE p.nam = :nam AND p.thang >= 1 AND p.thang <= :thang_den
        GROUP BY b.ten_cum
    """
    
    conn = sqlite3.connect(str(db_path))
    try:
        # Thực tế transactions
        df_t = pd.read_sql_query(sql_trans, conn, params={"nam": year})
        for _, r in df_t.iterrows():
            c = r["ten_cum"]
            if c in res:
                res[c]["actual"] += r["dt"] or 0.0
                
        # Thực tế khác
        df_o = pd.read_sql_query(sql_other, conn, params={"nam": year})
        for _, r in df_o.iterrows():
            c = r["ten_cum"]
            if c in res:
                res[c]["actual"] += r["dt"] or 0.0
                
        # Kế hoạch plans
        df_p = pd.read_sql_query(sql_plan, conn, params={"nam": year, "thang_den": month_den})
        for _, r in df_p.iterrows():
            c = r["ten_cum"]
            if c in res:
                res[c]["plan"] += r["dt"] or 0.0
                
    except Exception as e:
        print(f"Lỗi truy vấn YTD theo cụm: {e}")
    finally:
        conn.close()
        
    return res

def register_global_callbacks(app):
    """Đăng ký các callback cho trang Tổng quan chung"""
    
    @app.callback(
        [Output("global-kpi-bccp-value", "children"),
         Output("global-kpi-bccp-compare-info", "children"),
         Output("global-kpi-hcc-value", "children"),
         Output("global-kpi-hcc-compare-info", "children"),
         Output("global-kpi-tcbc-value", "children"),
         Output("global-kpi-tcbc-compare-info", "children"),
         Output("global-kpi-ppbl-value", "children"),
         Output("global-kpi-ppbl-compare-info", "children"),
         Output("global-donut-chart", "figure"),
         Output("ytd-table-container", "children"),
         Output("global-cum-table-container", "children")],
        [Input("sidebar-year", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-compare-mode", "value"),
         Input("sidebar-cum", "value")]
    )
    def update_global_overview(year, month, compare_mode, cum):
        if not year or not month:
            return ["—"] * 8 + [go.Figure(), go.Figure(), html.Div("Vui lòng chọn bộ lọc thời gian.")]
            
        # 1. Lấy doanh thu thực tế kỳ hiện tại
        rev_cur = get_total_revenue_by_service(DB_PATH, year, month, cum)
        
        # 2. Lấy doanh thu thực tế kỳ trước
        pyear, pmonth = get_prev_month_year(year, month)
        rev_prev = get_total_revenue_by_service(DB_PATH, pyear, pmonth, cum)
        
        # 3. Lấy doanh thu thực tế cùng kỳ năm trước (YoY)
        rev_yoy = get_total_revenue_by_service(DB_PATH, year - 1, month, cum)
        
        # 4. Lấy kế hoạch doanh thu tháng hiện tại
        rev_plan = get_plans_current_month(DB_PATH, year, month, cum)
        
        # 5. Xây dựng nội dung so sánh cho mỗi thẻ KPI
        def build_compare_info(service_key):
            now_val = rev_cur.get(service_key, 0.0)
            elements = []
            
            # So sánh Kỳ trước
            if "prev_period" in compare_mode:
                prev_val = rev_prev.get(service_key, 0.0)
                if prev_val > 0:
                    pct = (now_val - prev_val) * 100.0 / prev_val
                    color = "#10B981" if pct >= 0 else "#EF4444"
                    icon = "▲" if pct >= 0 else "▼"
                    elements.append(html.Div([
                        html.Span(f"{icon} {abs(pct):.1f}%", style={"color": color, "fontWeight": "bold", "marginRight": "5px"}),
                        html.Span(f"so với kỳ trước ({format_revenue(prev_val)})", style={"color": "#64748B"})
                    ], style={"marginBottom": "2px"}))
                else:
                    elements.append(html.Div("— so với kỳ trước", style={"color": "#94A3B8", "marginBottom": "2px"}))
                    
            # So sánh Cùng kỳ (YoY)
            if "yoy" in compare_mode:
                yoy_val = rev_yoy.get(service_key, 0.0)
                if yoy_val > 0:
                    pct = (now_val - yoy_val) * 100.0 / yoy_val
                    color = "#10B981" if pct >= 0 else "#EF4444"
                    icon = "▲" if pct >= 0 else "▼"
                    elements.append(html.Div([
                        html.Span(f"{icon} {abs(pct):.1f}%", style={"color": color, "fontWeight": "bold", "marginRight": "5px"}),
                        html.Span(f"so với cùng kỳ ({format_revenue(yoy_val)})", style={"color": "#64748B"})
                    ], style={"marginBottom": "2px"}))
                else:
                    elements.append(html.Div("— so với cùng kỳ", style={"color": "#94A3B8", "marginBottom": "2px"}))
                    
            # So sánh Kế hoạch
            if "plan" in compare_mode:
                plan_val = rev_plan.get(service_key, 0.0)
                if plan_val > 0:
                    pct = now_val * 100.0 / plan_val
                    color = "#10B981" if pct >= 100 else "#FF9800"
                    elements.append(html.Div([
                        html.Span(f"🎯 {pct:.1f}%", style={"color": color, "fontWeight": "bold", "marginRight": "5px"}),
                        html.Span(f"KH: {format_revenue(plan_val)}", style={"color": "#64748B"})
                    ]))
                else:
                    elements.append(html.Div("🎯 — (Chưa giao KH)", style={"color": "#94A3B8"}))
                    
            return html.Div(elements)
            
        bccp_val_str = format_revenue(rev_cur["BCCP"])
        bccp_info = build_compare_info("BCCP")
        
        hcc_val_str = format_revenue(rev_cur["HCC"])
        hcc_info = build_compare_info("HCC")
        
        tcbc_val_str = format_revenue(rev_cur["TCBC"])
        tcbc_info = build_compare_info("TCBC")
        
        ppbl_val_str = format_revenue(rev_cur["PPBL"])
        ppbl_info = build_compare_info("PPBL")
        
        # 6. Biểu đồ Donut cơ cấu doanh thu
        donut_fig = go.Figure()
        labels = ["BCCP", "HCC", "TCBC", "PPBL"]
        values = [rev_cur["BCCP"], rev_cur["HCC"], rev_cur["TCBC"], rev_cur["PPBL"]]
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]
        
        if sum(values) > 0:
            donut_fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                marker=dict(colors=colors),
                textinfo="percent",
                hoverinfo="label+value+percent",
                hovertemplate="<b>%{label}</b><br>Doanh thu: %{value:,.0f} đ<br>Tỉ lệ: %{percent}<extra></extra>"
            ))
        else:
            # Empty placeholder
            donut_fig.add_trace(go.Pie(
                labels=["Không có dữ liệu"],
                values=[1],
                hole=0.5,
                marker=dict(colors=["#E2E8F0"]),
                textinfo="none",
                showlegend=False
            ))
            
        donut_fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        # 7. Bảng doanh thu YTD (lũy kế từ đầu năm đến tháng hiện tại)
        ytd_cum_data = get_ytd_data_by_cum(DB_PATH, year, month)
        df_cum = get_revenue_by_cum(DB_PATH, year, month)
        
        # Tạo bảng YTD DataTable
        ytd_rows = []
        for c in sorted(ytd_cum_data.keys()):
            # Lấy doanh thu tháng từ df_cum (nếu tồn tại)
            month_val = 0.0
            if not df_cum.empty:
                match = df_cum[df_cum["Cụm"] == c]
                if not match.empty:
                    month_val = match.iloc[0]["Tổng cộng"]
            
            actual_ytd = ytd_cum_data[c]["actual"]
            plan_ytd = ytd_cum_data[c]["plan"]
            
            # Tính % hoàn thành
            if plan_ytd is not None and plan_ytd > 0:
                pct = (actual_ytd * 100.0 / plan_ytd)
            else:
                pct = None
                
            ytd_rows.append({
                "Cụm": c,
                "month_val": month_val,
                "actual_ytd": actual_ytd,
                "pct": pct,
                "pct_display": f"{pct:.1f}%" if pct is not None else "-"
            })
            
        df_ytd = pd.DataFrame(ytd_rows)
        
        # Thêm dòng Toàn tỉnh
        ytd_provincial_actual = sum(item["actual"] for item in ytd_cum_data.values())
        ytd_provincial_plan = sum(item["plan"] for item in ytd_cum_data.values())
        prov_month_val = df_cum["Tổng cộng"].sum() if not df_cum.empty else 0.0
        
        if ytd_provincial_plan > 0:
            prov_pct = (ytd_provincial_actual * 100.0 / ytd_provincial_plan)
        else:
            prov_pct = None
            
        prov_row = pd.DataFrame([{
            "Cụm": "⭐️ TOÀN TỈNH",
            "month_val": prov_month_val,
            "actual_ytd": ytd_provincial_actual,
            "pct": prov_pct,
            "pct_display": f"{prov_pct:.1f}%" if prov_pct is not None else "-"
        }])
        
        df_ytd = pd.concat([prov_row, df_ytd], ignore_index=True)
        
        # Định dạng hiển thị các cột
        df_ytd_display = df_ytd.copy()
        df_ytd_display["Doanh thu tháng"] = df_ytd_display["month_val"].apply(lambda x: f"{x:,.0f} đ" if x > 0 else "0 đ")
        df_ytd_display["Doanh thu lũy kế (YTD)"] = df_ytd_display["actual_ytd"].apply(lambda x: f"{x:,.0f} đ" if x > 0 else "0 đ")
        df_ytd_display["Tỷ lệ hoàn thành (%)"] = df_ytd_display["pct_display"]
        df_ytd_display["Đơn vị"] = df_ytd_display["Cụm"]
        
        ytd_columns = [
            {"name": "Đơn vị", "id": "Đơn vị"},
            {"name": "Doanh thu tháng", "id": "Doanh thu tháng"},
            {"name": "Doanh thu lũy kế (YTD)", "id": "Doanh thu lũy kế (YTD)"},
            {"name": "Tỷ lệ hoàn thành (%)", "id": "Tỷ lệ hoàn thành (%)"}
        ]
        
        ytd_table = dash_table.DataTable(
            id="ytd-revenue-datatable",
            data=df_ytd_display.to_dict("records"),
            columns=ytd_columns,
            sort_action="native",
            style_table={"overflowX": "auto", "borderRadius": "8px", "border": "1px solid #E2E8F0"},
            style_header={
                "backgroundColor": "#F1F5F9",
                "fontWeight": "bold",
                "color": "#1E293B",
                "border": "1px solid #CBD5E1"
            },
            style_cell={
                "padding": "10px 12px",
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
                    "if": {
                        "column_id": "Tỷ lệ hoàn thành (%)",
                        "filter_query": "{pct} < 60"
                    },
                    "backgroundColor": "#FEE2E2",
                    "color": "#DC2626",
                    "fontWeight": "bold"
                },
                {
                    "if": {
                        "column_id": "Tỷ lệ hoàn thành (%)",
                        "filter_query": "{pct} >= 60 && {pct} < 80"
                    },
                    "backgroundColor": "#FFEDD5",
                    "color": "#EA580C",
                    "fontWeight": "bold"
                },
                {
                    "if": {
                        "column_id": "Tỷ lệ hoàn thành (%)",
                        "filter_query": "{pct} >= 80 && {pct} < 100"
                    },
                    "backgroundColor": "#FEF9C3",
                    "color": "#CA8A04",
                    "fontWeight": "bold"
                },
                {
                    "if": {
                        "column_id": "Tỷ lệ hoàn thành (%)",
                        "filter_query": "{pct} >= 100"
                    },
                    "backgroundColor": "#DCFCE7",
                    "color": "#16A34A",
                    "fontWeight": "bold"
                }
            ]
        )
        
        # 8. Bảng phân rã Cụm doanh thu chi tiết (đã có df_cum ở trên)
        # Thêm dòng Toàn tỉnh
        if not df_cum.empty:
            prov_cum_row = pd.DataFrame([{
                "Cụm": "⭐️ TOÀN TỈNH",
                "BCCP": df_cum["BCCP"].sum(),
                "HCC": df_cum["HCC"].sum(),
                "TCBC": df_cum["TCBC"].sum(),
                "PPBL": df_cum["PPBL"].sum(),
                "Tổng cộng": df_cum["Tổng cộng"].sum()
            }])
            df_cum = pd.concat([prov_cum_row, df_cum], ignore_index=True)
            
            # Định dạng các cột số
            for col in ["BCCP", "HCC", "TCBC", "PPBL", "Tổng cộng"]:
                df_cum[col] = df_cum[col].map(lambda x: f"{x:,.0f} đ" if x > 0 else "—")
                
        table = dash_table.DataTable(
            data=df_cum.to_dict("records"),
            columns=[{"name": col, "id": col} for col in df_cum.columns],
            style_table={"overflowX": "auto", "borderRadius": "8px", "border": "1px solid #E2E8F0"},
            style_header={
                "backgroundColor": "#F1F5F9",
                "fontWeight": "bold",
                "color": "#1E293B",
                "border": "1px solid #CBD5E1"
            },
            style_cell={
                "padding": "10px 12px",
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
                    "if": {"column_id": "Tổng cộng"},
                    "fontWeight": "bold"
                }
            ]
        )
        
        return (
            bccp_val_str, bccp_info,
            hcc_val_str, hcc_info,
            tcbc_val_str, tcbc_info,
            ppbl_val_str, ppbl_info,
            donut_fig,
            ytd_table,
            table
        )
