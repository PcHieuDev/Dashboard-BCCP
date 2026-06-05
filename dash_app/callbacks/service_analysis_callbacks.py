# -*- coding: utf-8 -*-
"""
Callbacks cho trang Thống kê SP-DV.
"""

import dash
from dash import Output, Input, State, dash_table, dcc
from datetime import datetime
import pandas as pd
from callbacks.utils import resolve_filters_and_query
from components.data_table import render_revenue_datatable

def register_service_analysis_callbacks(app):
    @app.callback(
        Output("service-analysis-table-container", "children"),
        [Input("btn-apply-filter", "n_clicks"),
         Input("service-analysis-compare-opt", "value")],
        [State("url", "pathname"),
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-nhom-dv", "data"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "data"),
         State("sidebar-hop-dong", "data")],
        prevent_initial_call=True
    )
    def update_service_analysis_table(n_clicks, compare_opt, pathname, year, period, start_date, end_date, week_idx, month_val,
                                      nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        if pathname != "/bccp/service-analysis":
            return dash.no_update
            
        spdv = None
        compare_prev = compare_opt != "none"
        compare_mode = compare_opt if compare_prev else "prev_period"
        
        _, _, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='dich_vu', group_by_secondary=None, compare_prev=compare_prev
        )
        
        table = render_revenue_datatable(df, ['dich_vu'], compare_opt)
        if isinstance(table, dash_table.DataTable if hasattr(dash_table, 'DataTable') else object):
            table.id = "service-analysis-datatable"
        return table

    @app.callback(
        Output("service-analysis-download", "data"),
        [Input("service-analysis-btn-export", "n_clicks")],
        [State("url", "pathname"),
         State("service-analysis-compare-opt", "value"),
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-nhom-dv", "data"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "data"),
         State("sidebar-hop-dong", "data")],
        prevent_initial_call=True
    )
    def export_service_analysis(n_clicks, pathname, compare_opt, year, period, start_date, end_date, week_idx, month_val,
                                nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        if not n_clicks or pathname != "/bccp/service-analysis":
            return dash.no_update
            
        spdv = None
        compare_prev = compare_opt != "none"
        compare_mode = compare_opt if compare_prev else "prev_period"
        
        date_from, date_to, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='dich_vu', group_by_secondary=None, compare_prev=compare_prev
        )
        
        filter_info = {
            "Năm dữ liệu": year,
            "Chu kỳ báo cáo": period,
            "Khoảng thời gian": f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}",
            "Nhóm dịch vụ": ", ".join(nhom_dv) if nhom_dv else "Tất cả",
            "Cụm địa lý": cum,
            "Phân loại KH": ", ".join(loai_kh) if loai_kh else "Tất cả"
        }
        
        from callbacks.export_helpers import generate_excel_report
        excel_bytes = generate_excel_report(df, ['dich_vu'], compare_opt, filter_info)
        filename = f"ThongKe_SPDV_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return dcc.send_bytes(excel_bytes, filename)
