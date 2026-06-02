# -*- coding: utf-8 -*-
"""
Callbacks quản lý giao diện, tính toán số liệu và xuất Excel cho các trang HCC, TCBC, PPBL.
"""

import sys
import io
import sqlite3
import pandas as pd
from pathlib import Path
from dash import Output, Input, State, html, dash_table, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from flask_login import current_user

# Setup sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from callbacks.utils import format_revenue

def get_prev_month_year(year, month):
    """Helper tìm tháng trước và năm tương ứng"""
    if month == 1:
        return year - 1, 12
    return year, month - 1

def register_service_callbacks(app):
    """Đăng ký các callback cho trang dịch vụ dùng chung"""
    
    # 1. Khởi tạo bộ lọc (Cụm, Năm) dựa theo dịch vụ và phân quyền người dùng
    @app.callback(
        [Output("service-filter-year", "options"),
         Output("service-filter-cum", "options"),
         Output("service-filter-cum", "value"),
         Output("service-filter-cum", "disabled")],
        [Input("service-type-store", "data")]
    )
    def init_service_filters(service_type):
        if not service_type or not DB_PATH.exists():
            return [{"label": "2026", "value": 2026}], [{"label": "Tất cả Cụm", "value": "Tất cả"}], "Tất cả", False
            
        conn = sqlite3.connect(str(DB_PATH))
        try:
            # Lấy danh sách năm
            # Do transactions có thể chứa dữ liệu cũ, ta query cột nam_du_lieu
            df_years = pd.read_sql_query("SELECT DISTINCT nam_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL ORDER BY nam_du_lieu DESC", conn)
            years_opts = [{"label": str(y), "value": y} for y in df_years["nam_du_lieu"].tolist()] if not df_years.empty else [{"label": "2026", "value": 2026}]
            
            # Lấy danh sách cụm
            df_cums = pd.read_sql_query("SELECT DISTINCT ten_cum FROM dim_buucuc WHERE ten_cum IS NOT NULL ORDER BY ten_cum", conn)
            cums = df_cums["ten_cum"].tolist()
        except Exception as e:
            print(f"Lỗi load filter trong service_callbacks: {e}")
            years_opts = [{"label": "2026", "value": 2026}]
            cums = []
        finally:
            conn.close()
            
        # Áp dụng phân quyền
        cum_value = "Tất cả"
        cum_options = [{"label": "Tất cả Cụm", "value": "Tất cả"}] + [{"label": c, "value": c} for c in cums]
        cum_disabled = False
        
        if current_user and current_user.is_authenticated and current_user.role == 'user' and current_user.assigned_cum:
            cum_value = current_user.assigned_cum
            cum_options = [{"label": current_user.assigned_cum, "value": current_user.assigned_cum}]
            cum_disabled = True
            
        return years_opts, cum_options, cum_value, cum_disabled

    # Hàm truy vấn dữ liệu chi tiết của 1 dịch vụ
    def query_service_data(service_type, year, month):
        """
        Truy vấn dữ liệu doanh thu chi tiết từ DB SQLite.
        Đặc biệt xử lý riêng trường hợp HCC: gộp 'Chuyển phát HCC' trong BCCP và data transactions_hcc.
        """
        thang_str = f"T{month:02d}"
        results = [] # list of dicts: {"ma_bc": ..., "ten_dich_vu": ..., "doanh_thu": ...}
        
        if not DB_PATH.exists():
            return pd.DataFrame()
            
        conn = sqlite3.connect(str(DB_PATH))
        try:
            if service_type == "HCC":
                # A. Lấy 'Chuyển phát HCC' từ bảng transactions chính
                sql_cp = """
                    SELECT t.buu_cuc as ma_bc, 'Chuyển phát HCC' as ten_dich_vu, SUM(t.cuoc_tt_tong) as dt
                    FROM transactions t
                    INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
                    WHERE d.nhom_chinh = 'HCC' AND t.nam_du_lieu = :nam AND t.thang_du_lieu = :thang
                    GROUP BY t.buu_cuc
                """
                df_cp = pd.read_sql_query(sql_cp, conn, params={"nam": year, "thang": thang_str})
                for _, r in df_cp.iterrows():
                    results.append({
                        "ma_bc": r["ma_bc"],
                        "ten_dich_vu": r["ten_dich_vu"],
                        "doanh_thu": r["dt"] or 0.0
                    })
                    
                # B. Lấy 5 dịch vụ khác từ transactions_hcc
                sql_hcc = """
                    SELECT ma_buu_cuc as ma_bc, ten_dich_vu, SUM(doanh_thu) as dt
                    FROM transactions_hcc
                    WHERE nam_du_lieu = :nam AND thang_du_lieu = :thang
                    GROUP BY ma_buu_cuc, ten_dich_vu
                """
                df_hcc = pd.read_sql_query(sql_hcc, conn, params={"nam": year, "thang": thang_str})
                for _, r in df_hcc.iterrows():
                    results.append({
                        "ma_bc": r["ma_bc"],
                        "ten_dich_vu": r["ten_dich_vu"],
                        "doanh_thu": r["dt"] or 0.0
                    })
                    
            elif service_type == "TCBC":
                sql_tc = """
                    SELECT ma_buu_cuc as ma_bc, ten_dich_vu, SUM(doanh_thu) as dt
                    FROM transactions_tcbc
                    WHERE nam_du_lieu = :nam AND thang_du_lieu = :thang
                    GROUP BY ma_buu_cuc, ten_dich_vu
                """
                df_tc = pd.read_sql_query(sql_tc, conn, params={"nam": year, "thang": thang_str})
                for _, r in df_tc.iterrows():
                    results.append({
                        "ma_bc": r["ma_bc"],
                        "ten_dich_vu": r["ten_dich_vu"],
                        "doanh_thu": r["dt"] or 0.0
                    })
                    
            elif service_type == "PPBL":
                sql_pp = """
                    SELECT ma_buu_cuc as ma_bc, ten_dich_vu, SUM(doanh_thu) as dt
                    FROM transactions_ppbl
                    WHERE nam_du_lieu = :nam AND thang_du_lieu = :thang
                    GROUP BY ma_buu_cuc, ten_dich_vu
                """
                df_pp = pd.read_sql_query(sql_pp, conn, params={"nam": year, "thang": thang_str})
                for _, r in df_pp.iterrows():
                    results.append({
                        "ma_bc": r["ma_bc"],
                        "ten_dich_vu": r["ten_dich_vu"],
                        "doanh_thu": r["dt"] or 0.0
                    })
        except Exception as e:
            print(f"Lỗi query service data: {e}")
        finally:
            conn.close()
            
        return pd.DataFrame(results)

    def process_and_pivot_data(df, service_type, cum):
        """
        Xử lý, JOIN danh mục địa lý, Pivot và thêm dòng tổng hợp.
        Nếu cum == 'Tất cả' -> Group by Cụm
        Nếu cum == cụm cụ thể -> Group by Bưu cục thuộc Cụm đó
        """
        if df.empty or not DB_PATH.exists():
            return pd.DataFrame(), []
            
        # 1. Đọc danh sách bưu cục từ dim_buucuc
        conn = sqlite3.connect(str(DB_PATH))
        try:
            df_buucuc = pd.read_sql_query("SELECT ma_bc, ten_buu_cuc, ten_cum FROM dim_buucuc", conn)
            # Load danh mục sản phẩm của dịch vụ này từ dim_dichvu để pivot đủ cột
            df_sub_services = pd.read_sql_query("SELECT DISTINCT ten_dich_vu FROM dim_dichvu WHERE nhom_chinh = :st", conn, params={"st": service_type})
            sub_services = df_sub_services["ten_dich_vu"].tolist()
        except Exception as e:
            print(f"Lỗi đọc danh mục buucuc: {e}")
            df_buucuc = pd.DataFrame(columns=["ma_bc", "ten_buu_cuc", "ten_cum"])
            sub_services = []
        finally:
            conn.close()
            
        # Join data thực tế với danh mục bưu cục
        df_merged = pd.merge(df, df_buucuc, left_on="ma_bc", right_on="ma_bc", how="inner")
        if df_merged.empty:
            return pd.DataFrame(), sub_services
            
        # 2. Xử lý theo bộ lọc cụm
        if cum == "Tất cả":
            # Group by Cụm & Dịch vụ con
            df_grouped = df_merged.groupby(["ten_cum", "ten_dich_vu"])["doanh_thu"].sum().reset_index()
            # Pivot table
            df_pivot = df_grouped.pivot(index="ten_cum", columns="ten_dich_vu", values="doanh_thu").fillna(0.0)
            df_pivot = df_pivot.reset_index().rename(columns={"ten_cum": "Địa bàn"})
            title_col = "Địa bàn"
        else:
            # Lọc riêng cụm đó
            df_cum_filtered = df_merged[df_merged["ten_cum"] == cum]
            if df_cum_filtered.empty:
                return pd.DataFrame(), sub_services
            # Group by Bưu cục (Mã BC + Tên BC) & Dịch vụ con
            df_grouped = df_cum_filtered.groupby(["ma_bc", "ten_buu_cuc", "ten_dich_vu"])["doanh_thu"].sum().reset_index()
            df_grouped["BuuCuc"] = df_grouped["ma_bc"] + " - " + df_grouped["ten_buu_cuc"]
            # Pivot table
            df_pivot = df_grouped.pivot(index="BuuCuc", columns="ten_dich_vu", values="doanh_thu").fillna(0.0)
            df_pivot = df_pivot.reset_index().rename(columns={"BuuCuc": "Bưu cục"})
            title_col = "Bưu cục"
            
        # Đảm bảo tất cả dịch vụ con trong dim_dichvu đều có cột (kể cả khi doanh thu = 0)
        for s in sub_services:
            if s not in df_pivot.columns:
                df_pivot[s] = 0.0
                
        # Sắp xếp các cột dịch vụ con
        service_cols = [c for c in sub_services if c in df_pivot.columns]
        
        # Thêm cột Tổng cộng
        df_pivot["Tổng cộng"] = df_pivot[service_cols].sum(axis=1)
        
        # Tạo dòng Tổng (Toàn tỉnh hoặc Tổng cụm)
        sum_row = {title_col: "⭐️ TOÀN TỈNH" if cum == "Tất cả" else f"⭐️ TỔNG {cum.upper()}"}
        for s in service_cols:
            sum_row[s] = df_pivot[s].sum()
        sum_row["Tổng cộng"] = df_pivot["Tổng cộng"].sum()
        
        df_sum = pd.DataFrame([sum_row])
        df_final = pd.concat([df_sum, df_pivot], ignore_index=True)
        
        # Trả về df_final và các cột dịch vụ con
        return df_final, service_cols

    # 2. Callback chính cập nhật giao diện
    @app.callback(
        [Output("service-kpi-container", "children"),
         Output("service-bar-chart", "figure"),
         Output("service-table-title", "children"),
         Output("service-table-container", "children")],
        [Input("service-type-store", "data"),
         Input("service-filter-year", "value"),
         Input("service-filter-month", "value"),
         Input("service-filter-cum", "value")]
    )
    def update_service_page(service_type, year, month, cum):
        if not service_type:
            return html.Div(), go.Figure(), "", html.Div()
            
        # A. Query và xử lý dữ liệu
        df_raw = query_service_data(service_type, year, month)
        df_pivot, service_cols = process_and_pivot_data(df_raw, service_type, cum)
        
        # B. Check empty state
        if df_pivot.empty or len(df_pivot) <= 1 or df_pivot["Tổng cộng"].iloc[0] == 0:
            empty_state = html.Div([
                html.Div("📥", className="empty-state-icon"),
                html.Div("Chưa có dữ liệu", className="empty-state-title"),
                html.Div(f"Hệ thống chưa ghi nhận dữ liệu {service_type} cho thời kỳ Tháng {month:02d}/{year}.", className="empty-state-desc"),
                dcc.Link(dbc.Button("Đi đến trang Nhập dữ liệu", color="primary"), href="/import")
            ], className="empty-state-container")
            
            return empty_state, go.Figure(), "📋 Bảng doanh thu chi tiết", empty_state
            
        # C. Render KPI tổng hợp
        tot_rev = df_pivot["Tổng cộng"].iloc[0] # Dòng đầu tiên là dòng tổng
        
        # Tính kỳ trước để so sánh (không lũy kế, so sánh tháng liền kề)
        pyear, pmonth = get_prev_month_year(year, month)
        df_raw_prev = query_service_data(service_type, pyear, pmonth)
        df_pivot_prev, _ = process_and_pivot_data(df_raw_prev, service_type, cum)
        prev_rev = df_pivot_prev["Tổng cộng"].iloc[0] if not df_pivot_prev.empty else 0.0
        
        # Tính hoàn thành kế hoạch tháng (nếu có)
        sql_plan = "SELECT SUM(ke_hoach_doanh_thu) FROM plans WHERE nam = :nam AND thang = :thang AND nhom_dich_vu = :nt"
        params_plan = {"nam": year, "thang": month, "nt": service_type}
        if cum and cum != "Tất cả":
            sql_plan = """
                SELECT SUM(p.ke_hoach_doanh_thu) 
                FROM plans p
                INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_bc
                WHERE p.nam = :nam AND p.thang = :thang AND p.nhom_dich_vu = :nt AND b.ten_cum = :cum
            """
            params_plan["cum"] = cum
            
        plan_val = 0.0
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            try:
                cursor = conn.cursor()
                cursor.execute(sql_plan, params_plan)
                row = cursor.fetchone()
                plan_val = row[0] if row and row[0] is not None else 0.0
            except Exception as e:
                print(f"Lỗi lấy plan tháng: {e}")
            finally:
                conn.close()
                
        # Xây dựng so sánh
        compare_elements = []
        if prev_rev > 0:
            pct_prev = (tot_rev - prev_rev) * 100.0 / prev_rev
            color = "#10B981" if pct_prev >= 0 else "#EF4444"
            icon = "▲" if pct_prev >= 0 else "▼"
            compare_elements.append(html.Span([
                html.Span(f"{icon} {abs(pct_prev):.1f}%", style={"color": color, "fontWeight": "bold", "marginRight": "5px"}),
                html.Span(f"so với kỳ trước ({format_revenue(prev_rev)})  |  ", style={"color": "#64748B"})
            ]))
            
        if plan_val > 0:
            pct_plan = tot_rev * 100.0 / plan_val
            color = "#10B981" if pct_plan >= 100 else "#FF9800"
            compare_elements.append(html.Span([
                html.Span(f"🎯 Hoàn thành KH: {pct_plan:.1f}%", style={"color": color, "fontWeight": "bold", "marginRight": "5px"}),
                html.Span(f"(Chỉ tiêu: {format_revenue(plan_val)})", style={"color": "#64748B"})
            ]))
        else:
            compare_elements.append(html.Span("🎯 Chỉ tiêu KH: Chưa được giao chỉ tiêu", style={"color": "#94A3B8"}))
            
        # Thẻ KPI tổng
        kpi_card = html.Div([
            html.Div([
                html.Div("💰 Tổng doanh thu thực tế trong tháng", className="kpi-title"),
                html.Span("💵", style={"fontSize": "22px", "float": "right", "marginTop": "-24px"})
            ]),
            html.Div(format_revenue(tot_rev), className="kpi-value", style={"marginTop": "8px", "fontSize": "30px"}),
            html.Div(compare_elements, style={"marginTop": "8px"})
        ], className="kpi-card mb-4", style={"borderLeft": "5px solid #10B981"})
        
        # D. Vẽ biểu đồ cột doanh thu các dịch vụ con
        # Lấy dòng tổng hợp ở dòng index 0 ra vẽ chart
        chart_data = []
        for s in service_cols:
            val = df_pivot[s].iloc[0]
            chart_data.append({"Dịch vụ con": s, "Doanh thu": val})
        df_chart = pd.DataFrame(chart_data)
        
        # Sắp xếp giảm dần
        df_chart = df_chart.sort_values(by="Doanh thu", ascending=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_chart["Dịch vụ con"],
            x=df_chart["Doanh thu"],
            orientation="h",
            marker_color="#10B981",
            hovertemplate="<b>%{y}</b><br>Doanh thu: %{x:,.0f} đ<extra></extra>"
        ))
        fig.update_layout(
            margin=dict(t=20, b=10, l=150, r=20),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Doanh thu (VNĐ)", gridcolor="#E2E8F0"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)")
        )
        
        # E. Cấu hình bảng hiển thị DataTable
        # Tạo bảng sao lưu để định dạng chuỗi VNĐ khi render
        df_table = df_pivot.copy()
        first_col = df_table.columns[0] # "Địa bàn" hoặc "Bưu cục"
        
        for col in service_cols + ["Tổng cộng"]:
            df_table[col] = df_table[col].map(lambda x: f"{x:,.0f} đ" if x > 0 else "—")
            
        table_title = f"📋 Chi tiết doanh thu theo {'Cụm' if cum == 'Tất cả' else f'Bưu cục thuộc Cụm {cum}'}"
        
        table_component = dash_table.DataTable(
            data=df_table.to_dict("records"),
            columns=[{"name": col, "id": col} for col in df_table.columns],
            style_table={"overflowX": "auto", "borderRadius": "8px", "border": "1px solid #E2E8F0"},
            style_header={
                "backgroundColor": "#F1F5F9",
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
                    # Dòng tổng nổi bật
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
        
        return kpi_card, fig, table_title, table_component

    # 3. Callback xuất file Excel
    @app.callback(
        Output("service-download-excel", "data"),
        [Input("service-export-excel-btn", "n_clicks")],
        [State("service-type-store", "data"),
         State("service-filter-year", "value"),
         State("service-filter-month", "value"),
         State("service-filter-cum", "value")],
        prevent_initial_call=True
    )
    def export_service_excel(n_clicks, service_type, year, month, cum):
        if not n_clicks or not service_type:
            return None
            
        df_raw = query_service_data(service_type, year, month)
        df_pivot, _ = process_and_pivot_data(df_raw, service_type, cum)
        
        if df_pivot.empty:
            return None
            
        # Tạo file Excel trong memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_pivot.to_excel(writer, index=False, sheet_name="Doanh thu")
            
        output.seek(0)
        
        filename = f"Doanh_thu_{service_type}_{month:02d}_{year}.xlsx"
        if cum and cum != "Tất cả":
            filename = f"Doanh_thu_{service_type}_Cum_{cum}_{month:02d}_{year}.xlsx"
            
        return dcc.send_bytes(output.getvalue(), filename)
