# -*- coding: utf-8 -*-
"""
Callbacks xử lý trang Chi tiết sản phẩm dịch vụ BCCP (/bccp/service-detail).
"""

import sqlite3
import pandas as pd
import dash
from dash import Output, Input, State, html, dash_table
import plotly.express as px
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH
from callbacks.utils import format_revenue

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

def register_service_detail_callbacks(app):
    """Đăng ký các callback cho trang Chi tiết sản phẩm dịch vụ BCCP"""
    
    @app.callback(
        [
            Output("spdv-table-container", "children"),
            Output("spdv-pie-chart", "figure")
        ],
        [
            Input("btn-apply-filter", "n_clicks"),
            Input("tabs-navigation", "value")
        ],
        [
            State("sidebar-year", "value"),
            State("sidebar-month-select", "value"),
            State("sidebar-week-select", "value"),
            State("sidebar-period", "value"),
            State("sidebar-cum", "value")
        ]
    )
    def update_service_detail(n_clicks, tab_val, year, month, week, cycle, cum_val):
        if tab_val is None or tab_val != "tab-service-detail":
            return dash.no_update, dash.no_update
        if not year:
            return html.Div("Vui lòng chọn năm dữ liệu", style={"color": "red"}), px.Model()
            
        import config.week_calendar as calendar_helper
        
        # 1. Xác định kỳ hiện tại và kỳ trước
        prev_val, prev_yr = None, None
        
        # Điều kiện địa lý
        geo_clause = ""
        geo_params = []
        if cum_val and cum_val != "Tất cả":
            geo_clause = " AND b.ten_cum = ? "
            geo_params.append(cum_val)
            
        # Điều kiện thời gian
        curr_time_clause = ""
        prev_time_clause = ""
        curr_time_params = []
        prev_time_params = []
        
        if cycle == 'Tuần':
            if not week:
                return html.Div("Vui lòng chọn tuần dữ liệu", style={"color": "red"}), px.Model()
            # Lấy ngày tuần này
            weeks_list = calendar_helper.get_week_list(year)
            c_start, c_end = None, None
            for w_num, s_d, e_d in weeks_list:
                if w_num == week:
                    c_start, c_end = s_d.isoformat(), e_d.isoformat()
                    break
            
            prev_w, prev_yr = get_prev_period_info('Tuần', week, year)
            prev_weeks_list = calendar_helper.get_week_list(prev_yr)
            p_start, p_end = None, None
            for w_num, s_d, e_d in prev_weeks_list:
                if w_num == prev_w:
                    p_start, p_end = s_d.isoformat(), e_d.isoformat()
                    break
            
            if not c_start or not p_start:
                return html.Div("Lỗi định vị ngày tuần", style={"color": "red"}), px.Model()
                
            curr_time_clause = " t.ngay_chap_nhan BETWEEN ? AND ? "
            curr_time_params = [c_start, c_end]
            
            prev_time_clause = " t.ngay_chap_nhan BETWEEN ? AND ? "
            prev_time_params = [p_start, p_end]
            period_name = f"Tuần {week}/{year}"
            prev_period_name = f"Tuần {prev_w}/{prev_yr}"
        else:
            if not month:
                return html.Div("Vui lòng chọn tháng dữ liệu", style={"color": "red"}), px.Model()
            curr_time_clause = " t.nam_du_lieu = ? AND t.thang_du_lieu = ? "
            curr_time_params = [year, f"T{month:02d}"]
            
            prev_m, prev_yr = get_prev_period_info('Tháng', month, year)
            prev_time_clause = " t.nam_du_lieu = ? AND t.thang_du_lieu = ? "
            prev_time_params = [prev_yr, f"T{prev_m:02d}"]
            period_name = f"Tháng {month:02d}/{year}"
            prev_period_name = f"Tháng {prev_m:02d}/{prev_yr}"
            
        # 2. Truy vấn dữ liệu từ DB
        conn = sqlite3.connect(str(DB_PATH))
        try:
            # Truy vấn kỳ hiện tại
            sql_curr = f"""
                SELECT d.ma_dich_vu, d.ten_dich_vu, d.nhom_dich_vu, SUM(t.cuoc_tt_tong) as dt_curr
                FROM transactions t
                INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
                LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
                WHERE d.nhom_chinh = 'BCCP' {geo_clause} AND {curr_time_clause}
                GROUP BY d.ma_dich_vu, d.ten_dich_vu, d.nhom_dich_vu
            """
            df_curr = pd.read_sql_query(sql_curr, conn, params=geo_params + curr_time_params)
            
            # Truy vấn kỳ trước
            sql_prev = f"""
                SELECT d.ma_dich_vu, SUM(t.cuoc_tt_tong) as dt_prev
                FROM transactions t
                INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
                LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
                WHERE d.nhom_chinh = 'BCCP' {geo_clause} AND {prev_time_clause}
                GROUP BY d.ma_dich_vu
            """
            df_prev = pd.read_sql_query(sql_prev, conn, params=geo_params + prev_time_params)
            
            # Gộp dữ liệu
            if df_curr.empty:
                return html.Div("Không có dữ liệu trong kỳ hiện tại.", style={"textAlign": "center", "padding": "20px", "color": "#64748B"}), px.pie(title="Không có dữ liệu")
                
            if df_prev.empty:
                df_prev = pd.DataFrame(columns=['ma_dich_vu', 'dt_prev'])
                
            df_merged = pd.merge(df_curr, df_prev, on='ma_dich_vu', how='left')
            df_merged['dt_prev'] = df_merged['dt_prev'].fillna(0.0)
            df_merged['dt_curr'] = df_merged['dt_curr'].fillna(0.0)
            
            # Tính phần trăm thay đổi
            def calc_change(row):
                curr = row['dt_curr']
                prev = row['dt_prev']
                if prev > 0:
                    return ((curr - prev) / prev) * 100.0
                return 0.0
                
            df_merged['pct_change'] = df_merged.apply(calc_change, axis=1)
            df_merged = df_merged.sort_values(by='dt_curr', ascending=False)
            
            # 3. Tạo bảng dữ liệu
            df_table = df_merged.copy()
            df_table['dt_curr_disp'] = df_table['dt_curr'].apply(lambda x: f"{x:,.0f} đ")
            df_table['dt_prev_disp'] = df_table['dt_prev'].apply(lambda x: f"{x:,.0f} đ")
            df_table['pct_change_disp'] = df_table['pct_change'].apply(lambda x: f"{x:+.1f}%" if x != 0 else "—")
            
            columns = [
                {"name": "Mã DV", "id": "ma_dich_vu"},
                {"name": "Tên dịch vụ", "id": "ten_dich_vu"},
                {"name": "Nhóm dịch vụ", "id": "nhom_dich_vu"},
                {"name": f"DT kỳ hiện tại ({period_name})", "id": "dt_curr_disp"},
                {"name": f"DT kỳ trước ({prev_period_name})", "id": "dt_prev_disp"},
                {"name": "Thay đổi (%)", "id": "pct_change_disp"}
            ]
            
            table_element = dash_table.DataTable(
                columns=columns,
                data=df_table.to_dict('records'),
                sort_action='native',
                filter_action='native',
                page_size=12,
                style_table={'overflowX': 'auto', 'minWidth': '100%'},
                style_header={
                    'backgroundColor': '#F8FAFC',
                    'fontWeight': 'bold',
                    'color': '#1E293B',
                    'border': '1px solid #E2E8F0',
                    'textAlign': 'left',
                    'fontSize': '12px',
                    'padding': '10px'
                },
                style_cell={
                    'border': '1px solid #E2E8F0',
                    'padding': '10px',
                    'fontSize': '12px',
                    'color': '#334155',
                    'fontFamily': 'Inter, sans-serif'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F8FAFC'
                    },
                    {
                        'if': {'column_id': 'pct_change_disp', 'filter_query': '{pct_change} > 0'},
                        'color': '#16A34A',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'column_id': 'pct_change_disp', 'filter_query': '{pct_change} < 0'},
                        'color': '#DC2626',
                        'fontWeight': 'bold'
                    }
                ]
            )
            
            # 4. Tạo biểu đồ Pie
            df_pie = df_curr.groupby('nhom_dich_vu')['dt_curr'].sum().reset_index()
            fig_pie = px.pie(
                df_pie,
                values='dt_curr',
                names='nhom_dich_vu',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            
            return table_element, fig_pie
            
        except Exception as e:
            print(f"Lỗi truy vấn chi tiết SPDV: {e}")
            import traceback
            traceback.print_exc()
            return html.Div(f"Lỗi truy vấn dữ liệu: {e}", style={"color": "red"}), px.Model()
        finally:
            conn.close()
