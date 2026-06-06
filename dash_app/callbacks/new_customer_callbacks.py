# -*- coding: utf-8 -*-
"""
Callbacks xử lý dữ liệu trang Khách hàng bán mới (/bccp/new-customer).
Bao gồm: Lọc động BĐX theo Cụm, Tính toán KPI, Hiển thị bảng dữ liệu BĐX và xuất Excel.
"""

import sqlite3
import pandas as pd
import dash
from dash import Output, Input, State, html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dash_table.Format import Format, Group, Scheme
from datetime import datetime
import io
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH
from callbacks.utils import format_revenue

def register_new_customer_callbacks(app):
    """
    Đăng ký các callback của trang Khách hàng mới.
    """

    # ==============================================================================
    # 1. ĐÃ XÓA CALLBACK DROPDOWN BĐX THEO YÊU CẦU TIP-11-003
    # ==============================================================================

    # ==============================================================================
    # 2. HELPER QUERY VÀ XỬ LÝ DỮ LIỆU
    # ==============================================================================
    def query_and_process_new_customers(year, month, cum_val, bdx_val):
        """
        Query dữ liệu new_customers và plans_new_customer từ DB,
        lọc theo Cụm và BĐX, sau đó tính toán KPIs và bảng kết quả.
        """
        if not DB_PATH.exists():
            return pd.DataFrame(), {}, {}
            
        conn = sqlite3.connect(str(DB_PATH))
        try:
            # A. Query thực tế từ new_customers (JOIN dim_buucuc để lấy ten_bdx)
            query_act = """
                SELECT nc.cms, nc.tong_doanh_thu, nc.nhom_dv, nc.ma_bdx, b.ten_bdx, nc.ten_cum
                FROM new_customers nc
                LEFT JOIN (SELECT DISTINCT ma_bdx, ten_bdx FROM dim_buucuc) b ON nc.ma_bdx = b.ma_bdx
                WHERE nc.nam = ? AND nc.thang = ?
            """
            df_act = pd.read_sql_query(query_act, conn, params=[year, month])
            
            # B. Query kế hoạch từ plans_new_customer (JOIN dim_buucuc để lấy ten_bdx, ten_cum)
            query_plan = """
                SELECT p.ma_xa, p.nhom_dich_vu, p.ke_hoach_doanh_thu, b.ten_bdx, b.ten_cum
                FROM plans_new_customer p
                LEFT JOIN (SELECT DISTINCT ma_bdx, ten_bdx, ten_cum FROM dim_buucuc) b ON p.ma_xa = b.ma_bdx
                WHERE p.nam = ? AND p.thang = ?
            """
            df_plan = pd.read_sql_query(query_plan, conn, params=[year, month])
            
        except Exception as e:
            print(f"Error querying new customer data: {e}")
            df_act = pd.DataFrame()
            df_plan = pd.DataFrame()
        finally:
            conn.close()
            
        # Áp dụng bộ lọc địa lý (Cụm và BĐX)
        if not df_act.empty:
            if cum_val and cum_val != "Tất cả":
                df_act = df_act[df_act['ten_cum'] == cum_val]
            if bdx_val and bdx_val != "Tất cả":
                df_act = df_act[df_act['ten_bdx'] == bdx_val]
                
        if not df_plan.empty:
            if cum_val and cum_val != "Tất cả":
                df_plan = df_plan[df_plan['ten_cum'] == cum_val]
            if bdx_val and bdx_val != "Tất cả":
                df_plan = df_plan[df_plan['ten_bdx'] == bdx_val]
                
        # 1. Tính toán KPIs tổng hợp
        tot_sl = df_act['cms'].nunique() if not df_act.empty else 0
        tot_dt = df_act['tong_doanh_thu'].sum() if not df_act.empty else 0.0
        tot_kh = df_plan['ke_hoach_doanh_thu'].sum() if not df_plan.empty else 0.0
        tot_pct = (tot_dt / tot_kh * 100) if tot_kh > 0 else None
        
        kpi_totals = {
            'count': tot_sl,
            'revenue': tot_dt,
            'plan': tot_kh,
            'percent': tot_pct
        }
        
        # 2. Tính toán KPIs theo Nhóm Dịch Vụ
        # Dịch vụ Truyền thống
        tt_act = df_act[df_act['nhom_dv'] == 'Truyền thống'] if not df_act.empty else pd.DataFrame()
        tt_sl = tt_act['cms'].nunique() if not tt_act.empty else 0
        tt_dt = tt_act['tong_doanh_thu'].sum() if not tt_act.empty else 0.0
        tt_kh = df_plan[df_plan['nhom_dich_vu'] == 'Truyền thống']['ke_hoach_doanh_thu'].sum() if not df_plan.empty else 0.0
        tt_pct = (tt_dt / tt_kh * 100) if tt_kh > 0 else None
        
        # Dịch vụ TMĐT
        tmdt_act = df_act[df_act['nhom_dv'] == 'TMĐT'] if not df_act.empty else pd.DataFrame()
        tmdt_sl = tmdt_act['cms'].nunique() if not tmdt_act.empty else 0
        tmdt_dt = tmdt_act['tong_doanh_thu'].sum() if not tmdt_act.empty else 0.0
        tmdt_kh = df_plan[df_plan['nhom_dich_vu'] == 'TMĐT']['ke_hoach_doanh_thu'].sum() if not df_plan.empty else 0.0
        tmdt_pct = (tmdt_dt / tmdt_kh * 100) if tmdt_kh > 0 else None
        
        kpi_services = {
            'tt': {'count': tt_sl, 'revenue': tt_dt, 'plan': tt_kh, 'percent': tt_pct},
            'tmdt': {'count': tmdt_sl, 'revenue': tmdt_dt, 'plan': tmdt_kh, 'percent': tmdt_pct}
        }
        
        # 3. Xây dựng bảng BĐX chi tiết
        all_bdx = set()
        if not df_act.empty:
            all_bdx.update(df_act['ten_bdx'].dropna().unique())
        if not df_plan.empty:
            all_bdx.update(df_plan['ten_bdx'].dropna().unique())
            
        bdx_rows = []
        for b_name in sorted(all_bdx):
            b_act = df_act[df_act['ten_bdx'] == b_name] if not df_act.empty else pd.DataFrame()
            b_plan = df_plan[df_plan['ten_bdx'] == b_name] if not df_plan.empty else pd.DataFrame()
            
            # Truyền thống
            b_tt_act = b_act[b_act['nhom_dv'] == 'Truyền thống'] if not b_act.empty else pd.DataFrame()
            b_sl_tt = b_tt_act['cms'].nunique() if not b_tt_act.empty else 0
            b_dt_tt = b_tt_act['tong_doanh_thu'].sum() if not b_tt_act.empty else 0.0
            b_kh_tt = b_plan[b_plan['nhom_dich_vu'] == 'Truyền thống']['ke_hoach_doanh_thu'].sum() if not b_plan.empty else 0.0
            b_pct_tt = (b_dt_tt / b_kh_tt * 100) if b_kh_tt > 0 else None
            
            # TMĐT
            b_tmdt_act = b_act[b_act['nhom_dv'] == 'TMĐT'] if not b_act.empty else pd.DataFrame()
            b_sl_tmdt = b_tmdt_act['cms'].nunique() if not b_tmdt_act.empty else 0
            b_dt_tmdt = b_tmdt_act['tong_doanh_thu'].sum() if not b_tmdt_act.empty else 0.0
            b_kh_tmdt = b_plan[b_plan['nhom_dich_vu'] == 'TMĐT']['ke_hoach_doanh_thu'].sum() if not b_plan.empty else 0.0
            b_pct_tmdt = (b_dt_tmdt / b_kh_tmdt * 100) if b_kh_tmdt > 0 else None
            
            # Tổng cộng BĐX
            b_tot_sl = b_sl_tt + b_sl_tmdt
            b_tot_dt = b_dt_tt + b_dt_tmdt
            b_tot_kh = b_kh_tt + b_kh_tmdt
            b_tot_pct = (b_tot_dt / b_tot_kh * 100) if b_tot_kh > 0 else None
            
            bdx_rows.append({
                'ten_bdx': b_name,
                'sl_tt': b_sl_tt,
                'dt_tt': b_dt_tt,
                'kh_tt': b_kh_tt,
                'pct_tt': b_pct_tt,
                'sl_tmdt': b_sl_tmdt,
                'dt_tmdt': b_dt_tmdt,
                'kh_tmdt': b_kh_tmdt,
                'pct_tmdt': b_pct_tmdt,
                'tot_sl': b_tot_sl,
                'tot_dt': b_tot_dt,
                'tot_kh': b_tot_kh,
                'pct_dat': b_tot_pct
            })
            
        df_result = pd.DataFrame(bdx_rows)
        return df_result, kpi_totals, kpi_services

    # ==============================================================================
    # 3. CALLBACK CHÍNH CẬP NHẬT GIAO DIỆN
    # ==============================================================================
    @app.callback(
        [# Block 1
         Output("new-cust-kpi-count-value", "children"), Output("new-cust-kpi-count-subtext", "children"),
         Output("new-cust-kpi-revenue-value", "children"), Output("new-cust-kpi-revenue-subtext", "children"),
         Output("new-cust-kpi-percent-value", "children"), Output("new-cust-kpi-percent-subtext", "children"),
         # Block 2 (Truyền thống)
         Output("new-cust-svc-tt-count", "children"), Output("new-cust-svc-tt-revenue", "children"),
         Output("new-cust-svc-tt-plan", "children"), Output("new-cust-svc-tt-percent", "children"),
         # Block 2 (TMĐT)
         Output("new-cust-svc-tmdt-count", "children"), Output("new-cust-svc-tmdt-revenue", "children"),
         Output("new-cust-svc-tmdt-plan", "children"), Output("new-cust-svc-tmdt-percent", "children"),
         # Bảng chi tiết
         Output("new-cust-table-container", "children"),
         # Leaderboard Cụm + Bar chart DV + Top KHM
         Output("new-cust-leaderboard-container", "children"),
         Output("new-cust-chart-dv", "figure"),
         Output("new-cust-top-khm-container", "children")],
        [Input("btn-apply-filter", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-cum", "value")],
        prevent_initial_call=True
    )
    def update_new_cust_page(n_clicks, tab_val, start_date, end_date, cum_val):
        if tab_val != "tab-new-customer" or tab_val is None:
            return [dash.no_update] * 18

        from datetime import date
        d_from = date.fromisoformat(start_date)
        d_to = date.fromisoformat(end_date)
        if (d_to - d_from).days + 1 > 31:
            alert = dbc.Alert("⚠️ Cảnh báo: Vui lòng chọn khoảng thời gian tối đa 31 ngày để xem Khách hàng mới.", color="danger", className="m-3")
            import plotly.graph_objects as go
            return ["—"] * 6 + ["—"] * 8 + [alert, html.Div(), go.Figure(), html.Div()]
            
        year = d_from.year
        month = d_from.month
            
        # Gọi hàm xử lý dữ liệu (luôn dùng bdx="Tất cả")
        df_result, kpi_tot, kpi_svc = query_and_process_new_customers(year, month, cum_val, "Tất cả")
        
        # 1. Format các thẻ KPI tổng hợp (Block 1)
        val_count = f"{kpi_tot['count']:,} KH"
        sub_count = html.Span("Khách hàng mới phát sinh")
        
        val_rev = format_revenue(kpi_tot['revenue'])
        sub_rev = html.Span(f"Kế hoạch: {format_revenue(kpi_tot['plan'])}")
        
        val_pct = f"{kpi_tot['percent']:.1f}%" if kpi_tot['percent'] is not None else "-"
        sub_pct = html.Span("Tỷ lệ hoàn thành kế hoạch")
        
        # 2. Format chỉ số theo Nhóm dịch vụ (Block 2)
        tt_count = f"{kpi_svc['tt']['count']:,}"
        tt_rev = format_revenue(kpi_svc['tt']['revenue'])
        tt_plan = format_revenue(kpi_svc['tt']['plan'])
        tt_pct = f"{kpi_svc['tt']['percent']:.1f}%" if kpi_svc['tt']['percent'] is not None else "-"
        
        tmdt_count = f"{kpi_svc['tmdt']['count']:,}"
        tmdt_rev = format_revenue(kpi_svc['tmdt']['revenue'])
        tmdt_plan = format_revenue(kpi_svc['tmdt']['plan'])
        tmdt_pct = f"{kpi_svc['tmdt']['percent']:.1f}%" if kpi_svc['tmdt']['percent'] is not None else "-"
        
        # 3. Tạo DataTable (Block 3)
        if df_result.empty:
            table_element = dbc.Alert("Không có dữ liệu khách hàng bán mới cho bộ lọc hiện tại.", color="warning", className="m-3")
        else:
            # Tạo dòng TỔNG CỘNG
            sum_sl_tt = df_result['sl_tt'].sum()
            sum_dt_tt = df_result['dt_tt'].sum()
            sum_kh_tt = df_result['kh_tt'].sum()
            sum_pct_tt = (sum_dt_tt / sum_kh_tt * 100) if sum_kh_tt > 0 else None
            
            sum_sl_tmdt = df_result['sl_tmdt'].sum()
            sum_dt_tmdt = df_result['dt_tmdt'].sum()
            sum_kh_tmdt = df_result['kh_tmdt'].sum()
            sum_pct_tmdt = (sum_dt_tmdt / sum_kh_tmdt * 100) if sum_kh_tmdt > 0 else None
            
            sum_tot_sl = df_result['tot_sl'].sum()
            sum_tot_dt = df_result['tot_dt'].sum()
            sum_tot_kh = df_result['tot_kh'].sum()
            sum_pct_dat = (sum_tot_dt / sum_tot_kh * 100) if sum_tot_kh > 0 else None
            
            total_row = {
                'ten_bdx': 'TỔNG CỘNG',
                'sl_tt': sum_sl_tt,
                'dt_tt': sum_dt_tt,
                'kh_tt': sum_kh_tt,
                'pct_tt': sum_pct_tt,
                'sl_tmdt': sum_sl_tmdt,
                'dt_tmdt': sum_dt_tmdt,
                'kh_tmdt': sum_kh_tmdt,
                'pct_tmdt': sum_pct_tmdt,
                'tot_sl': sum_tot_sl,
                'tot_dt': sum_tot_dt,
                'tot_kh': sum_tot_kh,
                'pct_dat': sum_pct_dat
            }
            
            df_table = pd.concat([df_result, pd.DataFrame([total_row])], ignore_index=True)
            
            # Hàm định dạng dữ liệu cho DataTable
            def format_pct(val):
                return f"{val:.1f}%" if pd.notna(val) else "-"
                
            def format_money(val):
                return f"{val:,.0f} đ" if pd.notna(val) else "0 đ"
                
            df_table_display = df_table.copy()
            for col in ['dt_tt', 'kh_tt', 'dt_tmdt', 'kh_tmdt', 'tot_dt', 'tot_kh']:
                df_table_display[col] = df_table_display[col].apply(format_money)
            for col in ['pct_tt', 'pct_tmdt', 'pct_dat']:
                df_table_display[col] = df_table_display[col].apply(format_pct)
            for col in ['sl_tt', 'sl_tmdt', 'tot_sl']:
                df_table_display[col] = df_table_display[col].apply(lambda x: f"{x:,}" if pd.notna(x) else "0")
                
            columns = [
                {"name": "Bưu điện Xã/Huyện", "id": "ten_bdx"},
                {"name": "SL KH mới (TT)", "id": "sl_tt"},
                {"name": "Doanh thu (TT)", "id": "dt_tt"},
                {"name": "Kế hoạch (TT)", "id": "kh_tt"},
                {"name": "% Đạt (TT)", "id": "pct_tt"},
                {"name": "SL KH mới (TMĐT)", "id": "sl_tmdt"},
                {"name": "Doanh thu (TMĐT)", "id": "dt_tmdt"},
                {"name": "Kế hoạch (TMĐT)", "id": "kh_tmdt"},
                {"name": "% Đạt (TMĐT)", "id": "pct_tmdt"},
                {"name": "Tổng SL", "id": "tot_sl"},
                {"name": "Tổng DT", "id": "tot_dt"},
                {"name": "Tổng Kế hoạch", "id": "tot_kh"},
                {"name": "Tổng % Đạt", "id": "pct_dat"},
            ]
            
            table_element = dash_table.DataTable(
                columns=columns,
                data=df_table_display.to_dict('records'),
                page_action='native',
                page_size=20,
                sort_action='native',
                filter_action='native',
                style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto', 'minWidth': '100%'},
                style_header={
                    'backgroundColor': '#F1F5F9',
                    'fontWeight': 'bold',
                    'color': '#1E293B',
                    'border': '1px solid #E2E8F0',
                    'textAlign': 'left',
                    'fontSize': '12px',
                    'padding': '10px 8px'
                },
                style_cell={
                    'border': '1px solid #E2E8F0',
                    'padding': '8px 8px',
                    'fontSize': '12px',
                    'color': '#334155',
                    'fontFamily': 'Inter, sans-serif'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F8FAFC',
                    },
                    {
                        'if': {'filter_query': '{ten_bdx} = "TỔNG CỘNG"'},
                        'backgroundColor': '#F1F5F9',
                        'fontWeight': 'bold',
                        'color': '#0F766E'
                    }
                ]
            )
            
        # 4. Bảng xếp hạng Leaderboard Cụm
        conn_db = sqlite3.connect(str(DB_PATH))
        try:
            sql_ld = """
                SELECT ten_cum, COUNT(DISTINCT cms) as sl_khm, SUM(tong_doanh_thu) as dt_khm
                FROM new_customers
                WHERE nam = ? AND thang = ? AND ten_cum IS NOT NULL AND ten_cum != 'Khác'
                GROUP BY ten_cum
                ORDER BY dt_khm DESC
            """
            df_ld = pd.read_sql_query(sql_ld, conn_db, params=[year, month])
            
            # Top KHM giá trị cao
            query_top = """
                SELECT nc.cms, nc.buu_cuc, nc.tong_doanh_thu, nc.nhom_dv, b.ten_bdx, nc.ten_cum
                FROM new_customers nc
                LEFT JOIN (SELECT DISTINCT ma_bc, ten_bdx FROM dim_buucuc) b ON nc.buu_cuc = b.ma_bc
                WHERE nc.nam = ? AND nc.thang = ?
            """
            df_top_khm = pd.read_sql_query(query_top, conn_db, params=[year, month])
            
            # Phân rã DV KHM sử dụng
            query_chart = """
                SELECT tong_doanh_thu, nhom_dv, ten_cum, b.ten_bdx
                FROM new_customers nc
                LEFT JOIN (SELECT DISTINCT ma_bdx, ten_bdx FROM dim_buucuc) b ON nc.ma_bdx = b.ma_bdx
                WHERE nc.nam = ? AND nc.thang = ?
            """
            df_chart = pd.read_sql_query(query_chart, conn_db, params=[year, month])
        except Exception as e:
            print(f"Error query new customer components: {e}")
            df_ld = pd.DataFrame()
            df_top_khm = pd.DataFrame()
            df_chart = pd.DataFrame()
        finally:
            conn_db.close()

        # Tạo Leaderboard Element
        if not df_ld.empty:
            df_ld['rank'] = range(1, len(df_ld) + 1)
            total_dt_ld = df_ld['dt_khm'].sum()
            df_ld['pct_total'] = df_ld['dt_khm'].apply(lambda x: (x * 100.0 / total_dt_ld) if total_dt_ld > 0 else 0.0)
            
            df_ld_display = df_ld.copy()
            df_ld_display['DT bán mới'] = df_ld_display['dt_khm'].apply(lambda x: f"{x:,.0f} đ")
            df_ld_display['SL KHM'] = df_ld_display['sl_khm'].apply(lambda x: f"{x:,}")
            df_ld_display['% Toàn tỉnh'] = df_ld_display['pct_total'].apply(lambda x: f"{x:.1f}%")
            df_ld_display['#'] = df_ld_display['rank']
            df_ld_display['Cụm'] = df_ld_display['ten_cum']
            
            ld_table = dash_table.DataTable(
                id="new-cust-leaderboard",
                columns=[
                    {"name": "#", "id": "#"},
                    {"name": "Cụm", "id": "Cụm"},
                    {"name": "SL KHM", "id": "SL KHM"},
                    {"name": "DT bán mới", "id": "DT bán mới"},
                    {"name": "% Toàn tỉnh", "id": "% Toàn tỉnh"},
                ],
                data=df_ld_display.to_dict('records'),
                sort_action='native',
                filter_action='native',
                style_table={'overflowX': 'auto', 'maxHeight': '300px', 'overflowY': 'auto'},
                style_header={
                    'backgroundColor': '#F1F5F9',
                    'fontWeight': 'bold',
                    'color': '#1E293B',
                    'border': '1px solid #E2E8F0',
                    'textAlign': 'left',
                    'fontSize': '12px'
                },
                style_cell={
                    'border': '1px solid #E2E8F0',
                    'padding': '8px 8px',
                    'fontSize': '12px',
                    'color': '#334155',
                    'fontFamily': 'Inter, sans-serif'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': [0, 1, 2]},
                        'fontWeight': 'bold',
                        'backgroundColor': '#ECFDF5',
                        'color': '#065F46'
                    }
                ]
            )
        else:
            ld_table = html.Div("Không có dữ liệu xếp hạng")

        # Tạo Top KHM Element
        if not df_top_khm.empty:
            if cum_val and cum_val != "Tất cả":
                df_top_khm = df_top_khm[df_top_khm['ten_cum'] == cum_val]
                
            df_top_khm = df_top_khm.nlargest(10, 'tong_doanh_thu')
            df_top_khm_display = df_top_khm.copy()
            df_top_khm_display['Doanh thu tháng đầu'] = df_top_khm_display['tong_doanh_thu'].apply(lambda x: f"{x:,.0f} đ")
            df_top_khm_display['Bưu cục'] = df_top_khm_display['buu_cuc'].fillna("-")
            df_top_khm_display['Nhóm DV chính'] = df_top_khm_display['nhom_dv'].fillna("-")
            df_top_khm_display['#'] = range(1, len(df_top_khm_display) + 1)
            
            top_khm_table = dash_table.DataTable(
                id="new-cust-top-khm-table",
                columns=[
                    {"name": "#", "id": "#"},
                    {"name": "CMS", "id": "cms"},
                    {"name": "Bưu cục", "id": "Bưu cục"},
                    {"name": "Doanh thu tháng đầu", "id": "Doanh thu tháng đầu"},
                    {"name": "Nhóm DV chính", "id": "Nhóm DV chính"},
                ],
                data=df_top_khm_display.to_dict('records'),
                sort_action='native',
                filter_action='native',
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': '#F1F5F9',
                    'fontWeight': 'bold',
                    'color': '#1E293B',
                    'border': '1px solid #E2E8F0',
                    'textAlign': 'left',
                    'fontSize': '12px'
                },
                style_cell={
                    'border': '1px solid #E2E8F0',
                    'padding': '8px 8px',
                    'fontSize': '12px',
                    'color': '#334155',
                    'fontFamily': 'Inter, sans-serif'
                }
            )
        else:
            top_khm_table = html.Div("Không có dữ liệu Top KHM")

        # Tạo Bar Chart
        if not df_chart.empty:
            if cum_val and cum_val != "Tất cả":
                df_chart = df_chart[df_chart['ten_cum'] == cum_val]
                
            df_khm_dv = df_chart.groupby('nhom_dv')['tong_doanh_thu'].sum().reset_index()
            
            import plotly.express as px
            fig_bar_dv = px.bar(
                df_khm_dv, x='nhom_dv', y='tong_doanh_thu',
                color='nhom_dv',
                color_discrete_map={"Truyền thống": "#2196F3", "TMĐT": "#4CAF50", "Quốc tế": "#FF9800", "Phát hành báo chí": "#F97316"}
            )
            fig_bar_dv.update_layout(
                margin=dict(t=20, b=10, l=50, r=10),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis_title="Nhóm dịch vụ",
                yaxis_title="Doanh thu bán mới (đ)",
                yaxis=dict(tickformat=",.0f")
            )
        else:
            import plotly.graph_objects as go
            fig_bar_dv = go.Figure()

        return [
            val_count, sub_count,
            val_rev, sub_rev,
            val_pct, sub_pct,
            tt_count, tt_rev, tt_plan, tt_pct,
            tmdt_count, tmdt_rev, tmdt_plan, tmdt_pct,
            table_element,
            ld_table,
            fig_bar_dv,
            top_khm_table
        ]

    # ==============================================================================
    # 4a. CALLBACK EXPORT DANH SÁCH TOÀN BỘ KHM (nút mới trong section Top KHM)
    # ==============================================================================
    @app.callback(
        Output("new-cust-download-khm", "data"),
        [Input("new-cust-btn-export-khm", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-cum", "value")],
        prevent_initial_call=True
    )
    def export_all_khm(n_clicks, tab_val, start_date, end_date, cum_val):
        if not n_clicks or tab_val != "tab-new-customer":
            return dash.no_update

        from datetime import date
        d_from = date.fromisoformat(start_date)
        d_to = date.fromisoformat(end_date)
        if (d_to - d_from).days + 1 > 31:
            return dash.no_update
            
        year = d_from.year
        month = d_from.month
        
        if not DB_PATH.exists():
            return dash.no_update
        
        conn_exp = sqlite3.connect(str(DB_PATH))
        try:
            q = """
                SELECT nc.ten_cum   AS [Cum],
                       b.ten_bdx   AS [BDH/Xa],
                       nc.cms      AS [Ma CMS],
                       nc.buu_cuc  AS [Ma Buu Cuc],
                       nc.nhom_dv  AS [Nhom DV],
                       nc.tong_doanh_thu AS [Doanh thu thang dau]
                FROM new_customers nc
                LEFT JOIN (SELECT DISTINCT ma_bc, ten_bdx FROM dim_buucuc) b
                       ON nc.buu_cuc = b.ma_bc
                WHERE nc.nam = ? AND nc.thang = ?
            """
            params = [year, month]
            if cum_val and cum_val != "Tất cả":
                q += " AND nc.ten_cum = ?"
                params.append(cum_val)
            q += " ORDER BY nc.tong_doanh_thu DESC"
            df_khm = pd.read_sql_query(q, conn_exp, params=params)
        except Exception as e:
            print(f"Error export KHM: {e}")
            df_khm = pd.DataFrame()
        finally:
            conn_exp.close()
        
        if df_khm.empty:
            return dash.no_update
        
        # Tạo Excel
        wb_khm = openpyxl.Workbook()
        ws_khm = wb_khm.active
        ws_khm.title = "Danh sach KHM"
        
        title_f = Font(name="Arial", size=13, bold=True, color="1E3A8A")
        sub_f   = Font(name="Arial", size=10, italic=True)
        hdr_f   = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        dat_f   = Font(name="Arial", size=10)
        hdr_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        thin_b  = Border(
            left=Side(style='thin', color='CBD5E1'), right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),  bottom=Side(style='thin', color='CBD5E1')
        )
        
        cum_label = cum_val if (cum_val and cum_val != "Tất cả") else "Tất cả"
        ws_khm['A1'] = f"DANH SÁCH TOÀN BỘ KHÁCH HÀNG MỚI - THÁNG {month:02d}/{year}"
        ws_khm['A1'].font = title_f
        ws_khm['A2'] = f"Bộ lọc Cụm: {cum_label} | Tổng: {len(df_khm):,} KH | Sắp xếp theo DT giảm dần"
        ws_khm['A2'].font = sub_f
        
        headers_khm = list(df_khm.columns)
        row_k = 4
        for ci, h in enumerate(headers_khm, 1):
            cell = ws_khm.cell(row=row_k, column=ci, value=h)
            cell.font = hdr_f; cell.fill = hdr_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_b
        ws_khm.row_dimensions[row_k].height = 24
        
        for _, r in df_khm.iterrows():
            row_k += 1
            for ci, col_name in enumerate(headers_khm, 1):
                val = r[col_name]
                cell = ws_khm.cell(row=row_k, column=ci, value=val)
                cell.font = dat_f; cell.border = thin_b
                if "Doanh thu" in col_name:
                    cell.number_format = '#,##0" đ"'
                    cell.alignment = Alignment(horizontal="right")
                else:
                    cell.alignment = Alignment(horizontal="left")
        
        for col in ws_khm.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws_khm.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 40)
        
        out = io.BytesIO()
        wb_khm.save(out)
        excel_bytes = out.getvalue()
        out.close()
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        cum_tag = cum_val.replace(" ", "_") if (cum_val and cum_val != "Tất cả") else "TatCa"
        return dcc.send_bytes(excel_bytes, filename=f"KHM_{cum_tag}_T{month:02d}{year}_{ts}.xlsx")

    # ==============================================================================
    # 4. CALLBACK EXPORT EXCEL (bảng BĐX)
    # ==============================================================================
    @app.callback(
        Output("new-cust-download", "data"),
        [Input("new-cust-btn-export-excel", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-cum", "value")],
        prevent_initial_call=True
    )
    def export_new_cust_excel(n_clicks, tab_val, start_date, end_date, cum_val):
        if not n_clicks or tab_val != "tab-new-customer" or tab_val is None:
            return dash.no_update

        from datetime import date
        d_from = date.fromisoformat(start_date)
        d_to = date.fromisoformat(end_date)
        if (d_to - d_from).days + 1 > 31:
            return dash.no_update
            
        year = d_from.year
        month = d_from.month
            
        # Query và xử lý dữ liệu (luôn dùng bdx="Tất cả")
        df_result, kpi_tot, _ = query_and_process_new_customers(year, month, cum_val, "Tất cả")
        
        if df_result.empty:
            return dash.no_update
            
        # Tạo file Excel in-memory bằng openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "KH Bán Mới"
        
        # Bật hiển thị grid lines
        ws.views.sheetView[0].showGridLines = True
        
        # Tiêu đề báo cáo
        title_font = Font(name="Arial", size=14, bold=True, color="1E3A8A")
        sub_font = Font(name="Arial", size=10, italic=True)
        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        data_font = Font(name="Arial", size=10)
        total_font = Font(name="Arial", size=10, bold=True, color="0F766E")
        
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )
        
        # Ghi các thông tin tiêu đề
        ws['A1'] = f"BÁO CÁO PHÁT TRIỂN KHÁCH HÀNG BÁN MỚI - THÁNG {month:02d}/{year}"
        ws['A1'].font = title_font
        
        cum_txt = cum_val if cum_val else "Tất cả"
        ws['A2'] = f"Bộ lọc: Cụm: {cum_txt} | BĐX: Tất cả | Tổng KH mới trong kỳ: {kpi_tot['count']:,} KH"
        ws['A2'].font = sub_font
        
        # Headers cho bảng
        headers = [
            "Bưu điện Huyện/Xã", "SL KH mới (TT)", "Doanh thu (TT)", "Kế hoạch (TT)", "% Đạt (TT)",
            "SL KH mới (TMĐT)", "Doanh thu (TMĐT)", "Kế hoạch (TMĐT)", "% Đạt (TMĐT)",
            "Tổng SL", "Tổng Doanh thu", "Tổng Kế hoạch", "Tổng % Đạt"
        ]
        
        row_num = 4
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_num, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
            
        ws.row_dimensions[row_num].height = 28
        
        # Ghi dữ liệu
        for idx, r in df_result.iterrows():
            row_num += 1
            ws.row_dimensions[row_num].height = 20
            
            # Viết từng cột
            ws.cell(row=row_num, column=1, value=r['ten_bdx']).alignment = Alignment(horizontal="left", vertical="center")
            ws.cell(row=row_num, column=2, value=r['sl_tt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=3, value=r['dt_tt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=4, value=r['kh_tt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=5, value=r['pct_tt'] / 100 if pd.notna(r['pct_tt']) else "").alignment = Alignment(horizontal="right", vertical="center")
            
            ws.cell(row=row_num, column=6, value=r['sl_tmdt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=7, value=r['dt_tmdt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=8, value=r['kh_tmdt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=9, value=r['pct_tmdt'] / 100 if pd.notna(r['pct_tmdt']) else "").alignment = Alignment(horizontal="right", vertical="center")
            
            ws.cell(row=row_num, column=10, value=r['tot_sl']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=11, value=r['tot_dt']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=12, value=r['tot_kh']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=13, value=r['pct_dat'] / 100 if pd.notna(r['pct_dat']) else "").alignment = Alignment(horizontal="right", vertical="center")
            
            # Định dạng number format & font cho dòng dữ liệu
            for col_idx in range(1, 14):
                cell = ws.cell(row=row_num, column=col_idx)
                cell.font = data_font
                cell.border = thin_border
                
                # Định dạng tiền tệ
                if col_idx in [3, 4, 7, 8, 11, 12]:
                    cell.number_format = '#,##0" đ"'
                # Định dạng phần trăm
                elif col_idx in [5, 9, 13]:
                    cell.number_format = '0.0%'
                # Định dạng số lượng
                elif col_idx in [2, 6, 10]:
                    cell.number_format = '#,##0'
                    
        # Dòng TỔNG CỘNG
        row_num += 1
        ws.row_dimensions[row_num].height = 22
        
        sum_sl_tt = df_result['sl_tt'].sum()
        sum_dt_tt = df_result['dt_tt'].sum()
        sum_kh_tt = df_result['kh_tt'].sum()
        
        sum_sl_tmdt = df_result['sl_tmdt'].sum()
        sum_dt_tmdt = df_result['dt_tmdt'].sum()
        sum_kh_tmdt = df_result['kh_tmdt'].sum()
        
        sum_tot_sl = df_result['tot_sl'].sum()
        sum_tot_dt = df_result['tot_dt'].sum()
        sum_tot_kh = df_result['tot_kh'].sum()
        
        ws.cell(row=row_num, column=1, value="TỔNG CỘNG").alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=row_num, column=2, value=sum_sl_tt)
        ws.cell(row=row_num, column=3, value=sum_dt_tt)
        ws.cell(row=row_num, column=4, value=sum_kh_tt)
        ws.cell(row=row_num, column=5, value=(sum_dt_tt / sum_kh_tt) if sum_kh_tt > 0 else "")
        
        ws.cell(row=row_num, column=6, value=sum_sl_tmdt)
        ws.cell(row=row_num, column=7, value=sum_dt_tmdt)
        ws.cell(row=row_num, column=8, value=sum_kh_tmdt)
        ws.cell(row=row_num, column=9, value=(sum_dt_tmdt / sum_kh_tmdt) if sum_kh_tmdt > 0 else "")
        
        ws.cell(row=row_num, column=10, value=sum_tot_sl)
        ws.cell(row=row_num, column=11, value=sum_tot_dt)
        ws.cell(row=row_num, column=12, value=sum_tot_kh)
        ws.cell(row=row_num, column=13, value=(sum_tot_dt / sum_tot_kh) if sum_tot_kh > 0 else "")
        
        for col_idx in range(1, 14):
            cell = ws.cell(row=row_num, column=col_idx)
            cell.font = total_font
            cell.fill = total_fill
            cell.border = thin_border
            if col_idx in [3, 4, 7, 8, 11, 12]:
                cell.number_format = '#,##0" đ"'
            elif col_idx in [5, 9, 13]:
                cell.number_format = '0.0%'
            elif col_idx in [2, 6, 10]:
                cell.number_format = '#,##0'
                
        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if cell.number_format == '#,##0" đ"' and isinstance(cell.value, (int, float)):
                    val = f"{cell.value:,.0f} đ"
                elif cell.number_format == '0.0%' and isinstance(cell.value, (int, float)):
                    val = f"{cell.value * 100:.1f}%"
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
        # ================================================================
        # SHEET 2: Danh sách đầy đủ toàn bộ KHM theo bộ lọc Cụm
        # ================================================================
        ws2 = wb.create_sheet(title="Danh sach KHM")
        
        try:
            import sqlite3 as _sqlite3
            conn_exp = _sqlite3.connect(str(DB_PATH))
            q_khm = """
                SELECT nc.cms        AS cms,
                       nc.buu_cuc   AS ma_buu_cuc,
                       b.ten_bdx    AS bdh_xa,
                       nc.ten_cum   AS cum,
                       nc.nhom_dv   AS nhom_dv,
                       nc.tong_doanh_thu AS doanh_thu
                FROM new_customers nc
                LEFT JOIN (SELECT DISTINCT ma_bc, ten_bdx FROM dim_buucuc) b
                       ON nc.buu_cuc = b.ma_bc
                WHERE nc.nam = ? AND nc.thang = ?
            """
            params_khm = [year, month]
            if cum_val and cum_val != "Tat ca" and cum_val != "T\u1ea5t c\u1ea3":
                q_khm += " AND nc.ten_cum = ?"
                params_khm.append(cum_val)
            q_khm += " ORDER BY nc.tong_doanh_thu DESC"
            df_all_khm = pd.read_sql_query(q_khm, conn_exp, params=params_khm)
            conn_exp.close()
        except Exception as e:
            print(f"Error query all KHM: {e}")
            df_all_khm = pd.DataFrame()
        
        ws2['A1'] = f"DANH SACH TOAN BO KHACH HANG MOI - THANG {month:02d}/{year}"
        ws2['A1'].font = title_font
        cum_label = cum_val if (cum_val and cum_val not in ["T\u1ea5t c\u1ea3", "Tat ca"]) else "T\u1ea5t c\u1ea3"
        ws2['A2'] = f"Bo loc Cum: {cum_label} | Tong: {len(df_all_khm):,} KH"
        ws2['A2'].font = sub_font
        
        headers2 = ["Cum", "BDH/Xa", "Ma CMS", "Ma Buu Cuc", "Nhom DV", "Doanh thu thang dau (VND)"]
        col_map2 = ["cum", "bdh_xa", "cms", "ma_buu_cuc", "nhom_dv", "doanh_thu"]
        
        row2 = 4
        for col_idx, h in enumerate(headers2, 1):
            cell = ws2.cell(row=row2, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        ws2.row_dimensions[row2].height = 24
        
        if not df_all_khm.empty:
            for _, r in df_all_khm.iterrows():
                row2 += 1
                for col_idx, col_key in enumerate(col_map2, 1):
                    val = r[col_key] if col_key in r.index else ""
                    cell = ws2.cell(row=row2, column=col_idx, value=val)
                    cell.font = data_font
                    cell.border = thin_border
                    if col_key == "doanh_thu":
                        cell.number_format = '#,##0" \u0111"'
                        cell.alignment = Alignment(horizontal="right")
                    else:
                        cell.alignment = Alignment(horizontal="left")
            
            for col in ws2.columns:
                max_len = max((len(str(c.value or "")) for c in col), default=10)
                ws2.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 45)
        
        # Luu file
        output_stream = io.BytesIO()
        wb.save(output_stream)
        excel_bytes = output_stream.getvalue()
        output_stream.close()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cum_tag = cum_val.replace(" ", "_") if (cum_val and cum_val not in ["T\u1ea5t c\u1ea3", "Tat ca"]) else "TatCa"
        filename = f"KHM_{cum_tag}_T{month:02d}{year}_{timestamp}.xlsx"
        return dcc.send_bytes(excel_bytes, filename=filename)
