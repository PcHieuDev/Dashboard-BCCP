# -*- coding: utf-8 -*-
"""
Callbacks xử lý dữ liệu trang Báo cáo Duy trì & Biến động Khách hàng Hiện hữu (/bccp/retention).
"""

import sqlite3
import pandas as pd
import dash
from dash import Output, Input, State, html, dcc, dash_table
import dash_bootstrap_components as dbc
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
from analytics.retention_metrics import get_retention_stats, get_khhh_changes, get_churn_alerts

def register_retention_callbacks(app):
    """
    Đăng ký các callback của trang Retention.
    """

    # (Đã xóa cascade callback update_ret_bdx_dropdown - không còn lọc BĐX)

    # ==============================================================================
    # 2. HELPER XỬ LÝ BẢNG BIẾN ĐỘNG
    # ==============================================================================
    def build_changes_df(changes_dict):
        """Dựng DataFrame từ dict kết quả của get_khhh_changes."""
        rows = [
            {
                'loai': '📈 Doanh thu tăng',
                'count': changes_dict['tang']['count'],
                'change_dt': changes_dict['tang']['total_dt_change']
            },
            {
                'loai': '📉 Doanh thu giảm',
                'count': changes_dict['giam']['count'],
                'change_dt': changes_dict['giam']['total_dt_change']  # thường là số âm
            },
            {
                'loai': '❌ Khách hàng mất đi',
                'count': changes_dict['mat']['count'],
                'change_dt': changes_dict['mat']['total_dt_change']   # thường là số âm
            },
            {
                'loai': '✅ Duy trì (Ổn định)',
                'count': changes_dict['duy_tri']['count'],
                'change_dt': 0.0
            }
        ]
        return pd.DataFrame(rows)

    # ==============================================================================
    # 3. CALLBACK CHÍNH CẬP NHẬT GIAO DIỆN
    # ==============================================================================
    @app.callback(
        [# Block 1: KPI Cards
         Output("ret-kpi-prev-count-value", "children"), Output("ret-kpi-prev-count-subtext", "children"),
         Output("ret-kpi-retained-revenue-value", "children"), Output("ret-kpi-retained-revenue-subtext", "children"),
         Output("ret-kpi-lost-count-value", "children"), Output("ret-kpi-lost-count-subtext", "children"),
         # Block 2: Chỉ số duy trì (Gauges)
         Output("ret-gauge-sl", "figure"),
         Output("ret-gauge-dt", "figure"),
         # Block 3: Waterfall Chart & Bảng phân tích biến động
         Output("ret-waterfall-chart", "figure"),
         Output("ret-table-container", "children"),
         # Block 4: Churn Alerts Table
         Output("ret-churn-table-container", "children")],
        [Input("btn-apply-filter", "n_clicks"),
         Input("tabs-navigation", "value")],
        [State("sidebar-year", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-cum", "value")]
    )
    def update_retention_page(n_clicks, tab_val, year, month, cum_val):
        bdx_val = None  # Không còn lọc theo BĐX
        if tab_val != "tab-retention" or tab_val is None:
            return [dash.no_update] * 11
            
        db_str = str(DB_PATH)
        
        # 1. Tính toán thống kê duy trì (get_retention_stats)
        stats = get_retention_stats(db_str, year, month, cum_val, bdx_val)
        
        # 2. Tính toán phân tích biến động (get_khhh_changes)
        changes = get_khhh_changes(db_str, year, month, cum_val, bdx_val)
        df_changes = build_changes_df(changes)
        
        # Format Block 1 (KPI Cards)
        val_prev_count = f"{stats['khhh_prev_count']:,} KH"
        sub_prev_count = f"KHHH = KH có GD trừ KH mới"
        
        val_retained_rev = format_revenue(stats['dt_retained'])
        sub_retained_rev = f"Doanh thu tháng {month:02d} từ KH duy trì"
        
        val_lost_count = f"{stats['lost_count']:,} KH"
        sub_lost_count = f"Mất đi (không phát sinh tháng {month:02d})"
        
        # Format Block 2 (Gauges)
        import plotly.graph_objects as go
        fig_gauge_sl = go.Figure(go.Indicator(
            mode="gauge+number",
            value=stats['retention_rate_sl'],
            number={"suffix": "%", "font": {"size": 22}},
            title={'text': "Retention SL", 'font': {'size': 12, 'color': '#64748B', 'fontWeight': 'bold'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
                'bar': {'color': "#0F766E"},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#E2E8F0",
                'steps': [
                    {'range': [0, 50], 'color': "#FEE2E2"},
                    {'range': [50, 80], 'color': "#FEF3C7"},
                    {'range': [80, 100], 'color': "#D1FAE5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 3},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge_sl.update_layout(
            height=140,
            margin=dict(t=25, b=5, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        fig_gauge_dt = go.Figure(go.Indicator(
            mode="gauge+number",
            value=stats['retention_rate_dt'],
            number={"suffix": "%", "font": {"size": 22}},
            title={'text': "Retention DT", 'font': {'size': 12, 'color': '#64748B', 'fontWeight': 'bold'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
                'bar': {'color': "#2563EB"},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#E2E8F0",
                'steps': [
                    {'range': [0, 50], 'color': "#FEE2E2"},
                    {'range': [50, 80], 'color': "#FEF3C7"},
                    {'range': [80, 100], 'color': "#D1FAE5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 3},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge_dt.update_layout(
            height=140,
            margin=dict(t=25, b=5, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        # Waterfall Chart
        fig_waterfall = go.Figure(go.Waterfall(
            name="Biến động KHHH",
            orientation="v",
            x=["KHHH T-1", "Mất đi", "Giảm DT", "Tăng DT", "KHHH T0"],
            y=[stats['khhh_prev_count'], -changes['mat']['count'], -changes['giam']['count'], changes['tang']['count'], None],
            measure=["absolute", "relative", "relative", "relative", "total"],
            connector={"line": {"color": "#64748B", "width": 1.5}},
            decreasing={"marker": {"color": "#EF4444"}},
            increasing={"marker": {"color": "#10B981"}},
            totals={"marker": {"color": "#3B82F6"}}
        ))
        fig_waterfall.update_layout(
            margin=dict(t=10, b=10, l=40, r=20),
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        # Format Block 3 (Bảng biến động)
        tot_count = df_changes['count'].sum()
        tot_change = df_changes['change_dt'].sum()
        
        total_row = {
            'loai': 'TỔNG CỘNG',
            'count': tot_count,
            'change_dt': tot_change
        }
        df_table = pd.concat([df_changes, pd.DataFrame([total_row])], ignore_index=True)
        
        df_display = df_table.copy()
        df_display['count'] = df_display['count'].apply(lambda x: f"{x:,}")
        df_display['change_dt'] = df_display['change_dt'].apply(lambda x: f"{x:+, .0f} đ" if x != 0 else "0 đ")
        df_display['change_dt'] = df_display['change_dt'].str.replace("+ -", "-", regex=False).str.replace("+ ", "", regex=False)
        
        columns = [
            {"name": "Nhóm biến động", "id": "loai"},
            {"name": "Số lượng khách hàng (CMS)", "id": "count"},
            {"name": "Doanh thu thay đổi so với tháng trước", "id": "change_dt"}
        ]
        
        table_element = dash_table.DataTable(
            columns=columns,
            data=df_display.to_dict('records'),
            sort_action='native',
            filter_action='native',
            style_table={'overflowX': 'auto', 'minWidth': '100%', 'maxHeight': '280px', 'overflowY': 'auto'},
            style_header={
                'backgroundColor': '#F1F5F9',
                'fontWeight': 'bold',
                'color': '#1E293B',
                'border': '1px solid #E2E8F0',
                'textAlign': 'left',
                'fontSize': '12px',
                'padding': '8px 10px'
            },
            style_cell={
                'border': '1px solid #E2E8F0',
                'padding': '8px 10px',
                'fontSize': '12px',
                'color': '#334155',
                'fontFamily': 'Inter, sans-serif'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{loai} = "📈 Doanh thu tăng"'},
                    'color': '#15803d',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{loai} = "📉 Doanh thu giảm"'},
                    'color': '#b91c1c',
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{loai} = "❌ Khách hàng mất đi"'},
                    'color': '#7f1d1d',
                    'backgroundColor': '#fef2f2'
                },
                {
                    'if': {'filter_query': '{loai} = "TỔNG CỘNG"'},
                    'backgroundColor': '#F1F5F9',
                    'fontWeight': 'bold',
                    'color': '#0F766E'
                }
            ]
        )
        
        # 4. Churn Alerts Table
        df_churn = get_churn_alerts(db_str, year, month, cum_val, bdx_val)
        if df_churn.empty:
            churn_table_element = dbc.Alert("Không phát hiện khách hàng rời bỏ có nguy cơ cao cho bộ lọc hiện tại.", color="success", className="m-3")
        else:
            df_churn_display = df_churn.copy()
            df_churn_display['DT kỳ này'] = df_churn_display['dt_ky_nay'].apply(lambda x: f"{x:,.0f} đ")
            df_churn_display['DT TB 3 tháng'] = df_churn_display['dt_tb_3thang'].apply(lambda x: f"{x:,.0f} đ")
            df_churn_display['% Giảm'] = df_churn_display['pct_giam'].apply(lambda x: f"{x:.1f}%")
            
            churn_table_element = dash_table.DataTable(
                id="churn-alerts-table",
                columns=[
                    {"name": "CMS", "id": "cms"},
                    {"name": "Bưu cục", "id": "ten_buu_cuc"},
                    {"name": "DT kỳ này", "id": "DT kỳ này"},
                    {"name": "DT TB 3 tháng", "id": "DT TB 3 tháng"},
                    {"name": "% Giảm", "id": "% Giảm"},
                    {"name": "Ngày GD cuối", "id": "ngay_gd_cuoi"},
                    {"name": "Lý do", "id": "ly_do"},
                ],
                data=df_churn_display.to_dict('records'),
                style_table={'overflowX': 'auto', 'maxHeight': '300px', 'overflowY': 'auto'},
                style_header={
                    'backgroundColor': '#F1F5F9',
                    'fontWeight': 'bold',
                    'color': '#1E293B',
                    'border': '1px solid #E2E8F0',
                    'textAlign': 'left',
                    'fontSize': '12px',
                    'padding': '8px'
                },
                style_cell={
                    'border': '1px solid #E2E8F0',
                    'padding': '6px 8px',
                    'fontSize': '12px',
                    'color': '#334155',
                    'fontFamily': 'Inter, sans-serif'
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{ly_do} contains "Không GD"'},
                        'backgroundColor': '#FEE2E2',
                        'fontWeight': 'bold',
                        'color': '#991B1B'
                    },
                    {
                        'if': {'filter_query': '{pct_giam} < -30'},
                        'backgroundColor': '#FEF3C7',
                        'color': '#92400E'
                    }
                ],
                page_size=15,
                sort_action="native",
                filter_action="native"
            )
        
        return [
            val_prev_count, sub_prev_count,
            val_retained_rev, sub_retained_rev,
            val_lost_count, sub_lost_count,
            fig_gauge_sl, fig_gauge_dt,
            fig_waterfall, table_element,
            churn_table_element
        ]

    # ==============================================================================
    # 4. CALLBACK EXPORT EXCEL
    # ==============================================================================
    @app.callback(
        Output("ret-download", "data"),
        [Input("ret-btn-export-excel", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("sidebar-year", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-cum", "value")],
        prevent_initial_call=True
    )
    def export_retention_excel(n_clicks, tab_val, year, month, cum_val):
        bdx_val = None  # Không còn lọc theo BĐX
        if not n_clicks or tab_val != "tab-retention" or tab_val is None:
            return dash.no_update
            
        db_str = str(DB_PATH)
        stats = get_retention_stats(db_str, year, month, cum_val, bdx_val)
        changes = get_khhh_changes(db_str, year, month, cum_val, bdx_val)
        df_changes = build_changes_df(changes)
        
        # Tạo file Excel in-memory bằng openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Biến Động KHHH"
        
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
        ws['A1'] = f"BÁO CÁO DUY TRÌ VÀ BIẾN ĐỘNG KHÁCH HÀNG HIỆN HỮU - THÁNG {month:02d}/{year}"
        ws['A1'].font = title_font
        
        cum_txt = cum_val if cum_val else "Tất cả"
        bdx_txt = bdx_val if bdx_val else "Tất cả"
        ws['A2'] = f"Bộ lọc: Cụm: {cum_txt} | BĐX: {bdx_txt}"
        ws['A2'].font = sub_font
        
        # Ghi một số chỉ số KPIs tổng hợp ở đầu
        ws['A4'] = "CHỈ SỐ DUY TRÌ TỔNG HỢP"
        ws['A4'].font = Font(name="Arial", size=11, bold=True, color="0F766E")
        
        kpis_list = [
            ("Tập KHHH tháng trước (T-1)", stats['khhh_prev_count'], "KH"),
            ("Số lượng KH duy trì (T)", stats['retained_count'], "KH"),
            ("Số lượng KH mất đi (T)", stats['lost_count'], "KH"),
            ("Tỷ lệ duy trì khách hàng (SL)", stats['retention_rate_sl'] / 100, "0.0%"),
            ("Doanh thu KH duy trì kỳ trước (T-1)", stats['dt_prev'], "đ"),
            ("Doanh thu KH duy trì kỳ này (T)", stats['dt_retained'], "đ"),
            ("Tỷ lệ duy trì doanh thu (DT)", stats['retention_rate_dt'] / 100, "0.0%")
        ]
        
        cur_row = 5
        for label, val, unit in kpis_list:
            ws.cell(row=cur_row, column=1, value=label).font = data_font
            ws.cell(row=cur_row, column=1).border = thin_border
            
            val_cell = ws.cell(row=cur_row, column=2, value=val)
            val_cell.font = Font(name="Arial", size=10, bold=True)
            val_cell.border = thin_border
            val_cell.alignment = Alignment(horizontal="right")
            
            if unit == "KH":
                val_cell.number_format = '#,##0" KH"'
            elif unit == "đ":
                val_cell.number_format = '#,##0" đ"'
            elif unit == "0.0%":
                val_cell.number_format = '0.00%'
                
            cur_row += 1
            
        cur_row += 1
        # Headers cho bảng biến động
        ws.cell(row=cur_row, column=1, value="BẢNG PHÂN TÍCH BIẾN ĐỘNG DOANH THU").font = Font(name="Arial", size=11, bold=True, color="0F766E")
        
        cur_row += 1
        headers = ["Nhóm biến động", "Số lượng khách hàng (CMS)", "Doanh thu thay đổi so với tháng trước"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=cur_row, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
            
        ws.row_dimensions[cur_row].height = 24
        
        # Ghi dữ liệu biến động
        for idx, r in df_changes.iterrows():
            cur_row += 1
            ws.row_dimensions[cur_row].height = 20
            
            ws.cell(row=cur_row, column=1, value=r['loai']).alignment = Alignment(horizontal="left", vertical="center")
            ws.cell(row=cur_row, column=2, value=r['count']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=cur_row, column=3, value=r['change_dt']).alignment = Alignment(horizontal="right", vertical="center")
            
            # Format
            for col_idx in range(1, 4):
                cell = ws.cell(row=cur_row, column=col_idx)
                cell.font = data_font
                cell.border = thin_border
                if col_idx == 2:
                    cell.number_format = '#,##0'
                elif col_idx == 3:
                    cell.number_format = '+#,##0" đ";-#,##0" đ";0" đ"'
                    
        # Dòng TỔNG CỘNG cho bảng biến động
        cur_row += 1
        ws.row_dimensions[cur_row].height = 22
        
        tot_count = df_changes['count'].sum()
        tot_change = df_changes['change_dt'].sum()
        
        ws.cell(row=cur_row, column=1, value="TỔNG CỘNG").alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=cur_row, column=2, value=tot_count)
        ws.cell(row=cur_row, column=3, value=tot_change)
        
        for col_idx in range(1, 4):
            cell = ws.cell(row=cur_row, column=col_idx)
            cell.font = total_font
            cell.fill = total_fill
            cell.border = thin_border
            if col_idx == 2:
                cell.number_format = '#,##0'
            elif col_idx == 3:
                cell.number_format = '+#,##0" đ";-#,##0" đ";0" đ"'
                
        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if "+#,##0" in str(cell.number_format) and isinstance(cell.value, (int, float)):
                    val = f"+{cell.value:,.0f} đ" if cell.value > 0 else f"{cell.value:,.0f} đ"
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)
            
        ws.column_dimensions['A'].width = 40
        
        # Lưu ra bytes
        output_stream = io.BytesIO()
        wb.save(output_stream)
        excel_bytes = output_stream.getvalue()
        output_stream.close()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bao_cao_bien_dong_khhh_{timestamp}.xlsx"
        return dcc.send_bytes(excel_bytes, filename=filename)

    # ==============================================================================
    # 5. CALLBACK EXPORT CHURN ALERTS
    # ==============================================================================
    @app.callback(
        Output("ret-download-churn", "data"),
        [Input("ret-btn-export-churn", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("sidebar-year", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-cum", "value")],
        prevent_initial_call=True
    )
    def export_churn_alerts_excel(n_clicks, tab_val, year, month, cum_val):
        bdx_val = None  # Không còn lọc theo BĐX
        if not n_clicks or tab_val != "tab-retention" or tab_val is None:
            return dash.no_update
            
        db_str = str(DB_PATH)
        df_churn = get_churn_alerts(db_str, year, month, cum_val, bdx_val)
        
        if df_churn.empty:
            return dash.no_update
            
        # Tạo file Excel openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Canh Bao Churn"
        ws.views.sheetView[0].showGridLines = True
        
        title_font = Font(name="Arial", size=14, bold=True, color="B91C1C")
        sub_font = Font(name="Arial", size=10, italic=True)
        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        data_font = Font(name="Arial", size=10)
        
        header_fill = PatternFill(start_color="B91C1C", end_color="B91C1C", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )
        
        ws['A1'] = f"DANH SÁCH CẢNH BÁO KHÁCH HÀNG CÓ NGUY CƠ RỜI BỎ - THÁNG {month:02d}/{year}"
        ws['A1'].font = title_font
        
        cum_txt = cum_val if cum_val else "Tất cả"
        bdx_txt = bdx_val if bdx_val else "Tất cả"
        ws['A2'] = f"Bộ lọc: Cụm: {cum_txt} | BĐX: {bdx_txt}"
        ws['A2'].font = sub_font
        
        headers = ["CMS", "Bưu cục", "DT Kỳ Này", "DT TB 3 Tháng", "% Giảm", "Ngày GD Cuối", "Lý Do Cảnh Báo"]
        row_num = 4
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_num, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
            
        ws.row_dimensions[row_num].height = 24
        
        for idx, r in df_churn.iterrows():
            row_num += 1
            ws.row_dimensions[row_num].height = 20
            
            ws.cell(row=row_num, column=1, value=r['cms']).alignment = Alignment(horizontal="left", vertical="center")
            ws.cell(row=row_num, column=2, value=r['ten_buu_cuc']).alignment = Alignment(horizontal="left", vertical="center")
            ws.cell(row=row_num, column=3, value=r['dt_ky_nay']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=4, value=r['dt_tb_3thang']).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=5, value=r['pct_giam'] / 100 if pd.notna(r['pct_giam']) else "").alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row_num, column=6, value=r['ngay_gd_cuoi']).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(row=row_num, column=7, value=r['ly_do']).alignment = Alignment(horizontal="left", vertical="center")
            
            for col_idx in range(1, 8):
                cell = ws.cell(row=row_num, column=col_idx)
                cell.font = data_font
                cell.border = thin_border
                if col_idx in [3, 4]:
                    cell.number_format = '#,##0" đ"'
                elif col_idx == 5:
                    cell.number_format = '0.0%'
                    
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
        output_stream = io.BytesIO()
        wb.save(output_stream)
        excel_bytes = output_stream.getvalue()
        output_stream.close()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"danh_sach_canh_bao_churn_{timestamp}.xlsx"
        return dcc.send_bytes(excel_bytes, filename=filename)
