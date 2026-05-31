# -*- coding: utf-8 -*-
"""
Callbacks xử lý truy vấn dữ liệu và cập nhật bảng báo cáo Doanh thu chi tiết.
"""

import dash
from dash import Output, Input, State, html, dcc
import sys
from pathlib import Path
from datetime import datetime

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from callbacks.utils import resolve_filters_and_query
from components.data_table import render_revenue_datatable

def register_revenue_callbacks(app):
    """
    Đăng ký callback cập nhật bảng Doanh thu chi tiết và xuất báo cáo với ứng dụng Dash.
    """
    
    @app.callback(
        Output("revenue-table-container", "children"),
        [Input("tabs-navigation", "value"),
         Input("revenue-g1", "value"),
         Input("revenue-g2", "value"),
         Input("revenue-compare-opt", "value"),
         # Bộ lọc từ Sidebar
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-spdv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_revenue_table(tab_val, g1, g2, compare_opt, year, period, start_date, end_date, week_idx, month_val,
                             nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ chạy khi đang ở Tab Doanh thu chi tiết
        if tab_val != "tab-revenue":
            return dash.no_update
            
        g2_actual = None if g2 == "None" else g2
        compare_prev = compare_opt != "none"
        compare_mode = compare_opt if compare_prev else "prev_period"
        
        # 1. Truy vấn dữ liệu có cache dựa vào các bộ lọc
        _, _, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary=g1, group_by_secondary=g2_actual, compare_prev=compare_prev
        )
        
        # 2. Xử lý nhóm cột và hiển thị
        groupby_cols = [g1]
        if g2_actual:
            groupby_cols.append(g2_actual)
            
        # 3. Trả về bảng DataTable được định dạng
        return render_revenue_datatable(df, groupby_cols, compare_opt)

    @app.callback(
        Output("revenue-download", "data"),
        [Input("revenue-btn-export-excel", "n_clicks"),
         Input("revenue-btn-export-pdf", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("revenue-g1", "value"),
         State("revenue-g2", "value"),
         State("revenue-compare-opt", "value"),
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-nhom-dv", "value"),
         State("sidebar-spdv", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "value"),
         State("sidebar-hop-dong", "value")],
        prevent_initial_call=True
    )
    def export_revenue_table(btn_excel, btn_pdf, tab_val, g1, g2, compare_opt, year, period, start_date, end_date, week_idx, month_val,
                             nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        ctx = dash.callback_context
        if not ctx.triggered or tab_val != "tab-revenue":
            return dash.no_update
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id not in ("revenue-btn-export-excel", "revenue-btn-export-pdf"):
            return dash.no_update
            
        g2_actual = None if g2 == "None" else g2
        compare_prev = compare_opt != "none"
        compare_mode = compare_opt if compare_prev else "prev_period"
        
        # 1. Truy vấn dữ liệu có cache dựa vào các bộ lọc
        date_from, date_to, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary=g1, group_by_secondary=g2_actual, compare_prev=compare_prev
        )
        
        groupby_cols = [g1]
        if g2_actual:
            groupby_cols.append(g2_actual)
            
        # 2. Tạo thông tin bộ lọc gửi đi
        filter_info = {
            "Năm dữ liệu": year,
            "Chu kỳ báo cáo": period,
            "Khoảng thời gian": f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}",
            "Nhóm dịch vụ": ", ".join(nhom_dv) if nhom_dv else "Tất cả",
            "Cụm địa lý": cum,
            "Mã bưu điện": bdx if bdx != "Tất cả" else "Tất cả",
            "Phân loại KH": ", ".join(loai_kh) if loai_kh else "Tất cả",
            "Trạng thái HĐ": ", ".join(hop_dong) if isinstance(hop_dong, list) and hop_dong else (hop_dong if isinstance(hop_dong, str) and hop_dong else 'Tất cả')
        }
        
        # 3. Tạo file xuất tương ứng
        if trigger_id == "revenue-btn-export-excel":
            from callbacks.export_helpers import generate_excel_report
            excel_bytes = generate_excel_report(df, groupby_cols, compare_opt, filter_info)
            filename = f"BaoCaoDoanhThu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            return dcc.send_bytes(excel_bytes, filename)
            
        elif trigger_id == "revenue-btn-export-pdf":
            from callbacks.export_helpers import generate_pdf_report
            pdf_bytes = generate_pdf_report(df, groupby_cols, compare_opt, filter_info)
            filename = f"BaoCaoDoanhThu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            return dcc.send_bytes(pdf_bytes, filename)
            
        return dash.no_update

