# -*- coding: utf-8 -*-
"""
Callbacks xử lý hiển thị bảng chi tiết khách hàng (CMS), bảng Doanh thu xoay chiều,
bộ lọc inline và các chức năng xuất Excel tương ứng.
"""

import dash
from dash import Output, Input, State, html, dcc, dash_table
import sys
from pathlib import Path
from datetime import datetime
import dash_bootstrap_components as dbc
from dash.dash_table.Format import Format, Group, Scheme

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH
from callbacks.utils import resolve_filters_and_query, resolve_filters_and_query_customer
from components.data_table import render_revenue_datatable
from callbacks.export_helpers import generate_customer_excel, generate_excel_report

def register_customer_callbacks(app):
    """
    Đăng ký callbacks cho trang Chi tiết Khách hàng (CMS) và Doanh thu xoay chiều.
    """
    
    # ==============================================================================
    # 1. CALLBACK CẬP NHẬT BẢNG DOANH THU XOAY CHIỀU
    # ==============================================================================
    @app.callback(
        Output("revenue-table-container", "children"),
        [Input("btn-apply-filter", "n_clicks"),
         Input("tabs-navigation", "value"),
         Input("revenue-g1", "value"),
         Input("revenue-g2", "value"),
         Input("revenue-compare-opt", "value"),
         # Bộ lọc dịch vụ inline mới
         Input("customer-filter-nhom-dv", "value"),
         Input("customer-filter-loai-kh", "value"),
         Input("customer-filter-hop-dong", "value")],
        [# Bộ lọc địa lý từ Sidebar (State)
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value")]
    )
    def update_revenue_table(n_clicks, tab_val, g1, g2, compare_opt, nhom_dv, loai_kh, hop_dong,
                             year, period, start_date, end_date, week_idx, month_val, cum, bdx, buu_cuc):
        # Chạy khi ở tab Chi tiết Khách hàng (do đã gộp trang)
        if tab_val != "tab-customer" or tab_val is None:
            return dash.no_update
        spdv = None
            
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

    # ==============================================================================
    # 2. CALLBACK XUẤT EXCEL BẢNG DOANH THU XOAY CHIỀU
    # ==============================================================================
    @app.callback(
        Output("revenue-download", "data"),
        [Input("revenue-btn-export-excel", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("revenue-g1", "value"),
         State("revenue-g2", "value"),
         State("revenue-compare-opt", "value"),
         # Bộ lọc địa lý từ Sidebar
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         # Bộ lọc dịch vụ inline mới
         State("customer-filter-nhom-dv", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("customer-filter-loai-kh", "value"),
         State("customer-filter-hop-dong", "value")],
        prevent_initial_call=True
    )
    def export_revenue_table(n_clicks, tab_val, g1, g2, compare_opt, year, period, start_date, end_date, week_idx, month_val,
                             nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        ctx = dash.callback_context
        if not ctx.triggered or tab_val != "tab-customer" or tab_val is None:
            return dash.no_update
        spdv = None
            
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
        excel_bytes = generate_excel_report(df, groupby_cols, compare_opt, filter_info)
        filename = f"BaoCaoDoanhThu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return dcc.send_bytes(excel_bytes, filename)

    # ==============================================================================
    # 3. CALLBACK CẬP NHẬT BẢNG CHI TIẾT KHÁCH HÀNG (CMS)
    # ==============================================================================
    @app.callback(
        Output("customer-table-container", "children"),
        [Input("btn-apply-filter", "n_clicks"),
         Input("tabs-navigation", "value"),
         # Bộ lọc dịch vụ inline mới
         Input("customer-filter-nhom-dv", "value"),
         Input("customer-filter-loai-kh", "value"),
         Input("customer-filter-hop-dong", "value")],
        [# Bộ lọc địa lý từ Sidebar (State)
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value")]
    )
    def update_customer_table(n_clicks, tab_val, nhom_dv, loai_kh, hop_dong,
                              year, period, start_date, end_date, week_idx, month_val, cum, bdx, buu_cuc):
        # Chỉ chạy khi đang ở Tab Chi tiết Khách hàng
        if tab_val != "tab-customer" or tab_val is None:
            return dash.no_update
        spdv = None
            
        # 1. Truy vấn dữ liệu qua Cache
        _, _, _, df = resolve_filters_and_query_customer(
            year, period, start_date, end_date, week_idx, month_val,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong
        )
        
        # 2. Kiểm tra dữ liệu rỗng
        if df.empty or len(df) == 0:
            return dbc.Alert("Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại.", color="warning", className="m-3")
            
        # 3. Xác định cấu trúc cột hiển thị
        col_labels = {
            'cms': 'Mã khách hàng',
            'loai_kh': 'Loại khách hàng',
            'hop_dong': 'Trạng thái HĐ',
            'buu_cuc_list': 'Danh sách Bưu cục',
        }
        
        columns = []
        for c in df.columns:
            name = col_labels.get(c, c)
            col_def = {"name": name, "id": c}
            
            # Chỉ định sort và filter cho tất cả các cột
            if c in ['cms', 'loai_kh', 'hop_dong', 'buu_cuc_list']:
                pass
            else:
                col_def["type"] = "numeric"
                if 'SL' in c:
                    col_def["format"] = Format(group=Group.yes)
                elif 'KL' in c:
                    col_def["format"] = Format(group=Group.yes, precision=2, scheme=Scheme.fixed)
                else: # Cước
                    col_def["format"] = Format(group=Group.yes, precision=0, scheme=Scheme.fixed)
            columns.append(col_def)
            
        # 4. Trả về bảng DataTable được định dạng
        table = dash_table.DataTable(
            id='customer-detail-datatable',
            columns=columns,
            data=df.to_dict('records'),
            page_action='native',
            page_size=50,
            sort_action='native',
            filter_action='native',
            style_table={'overflowX': 'auto', 'maxHeight': '600px', 'overflowY': 'auto', 'minWidth': '100%'},
            style_header={
                'backgroundColor': '#F1F5F9',
                'fontWeight': 'bold',
                'color': '#1E293B',
                'border': '1px solid #E2E8F0',
                'textAlign': 'left',
                'padding': '12px 10px'
            },
            style_cell={
                'border': '1px solid #E2E8F0',
                'padding': '10px 10px',
                'fontSize': '13px',
                'color': '#334155',
                'fontFamily': 'Inter, sans-serif'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8FAFC',
                }
            ]
        )
        return table

    # ==============================================================================
    # 4. CALLBACK XUẤT EXCEL BẢNG CHI TIẾT KHÁCH HÀNG (CMS)
    # ==============================================================================
    @app.callback(
        Output("customer-download", "data"),
        [Input("customer-btn-export-excel", "n_clicks")],
        [State("tabs-navigation", "value"),
         # Bộ lọc địa lý từ Sidebar
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         # Bộ lọc dịch vụ inline mới
         State("customer-filter-nhom-dv", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("customer-filter-loai-kh", "value"),
         State("customer-filter-hop-dong", "value")],
        prevent_initial_call=True
    )
    def export_customer_table(n_clicks, tab_val, year, period, start_date, end_date, week_idx, month_val,
                              nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        ctx = dash.callback_context
        if not ctx.triggered or tab_val != "tab-customer" or tab_val is None:
            return dash.no_update
        spdv = None
            
        # 1. Truy vấn toàn bộ dữ liệu
        _, _, _, df = resolve_filters_and_query_customer(
            year, period, start_date, end_date, week_idx, month_val,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong
        )
        
        if df.empty:
            return dash.no_update
            
        # 2. Xây dựng thông tin bộ lọc
        filter_parts = [
            f"Năm dữ liệu: {year}",
            f"Chu kỳ báo cáo: {period}"
        ]
        if period == "Tháng" and month_val:
            filter_parts.append(f"Tháng: {month_val}")
        elif period == "Tuần" and week_idx is not None:
            filter_parts.append(f"Tuần index: {week_idx}")
        elif start_date and end_date:
            filter_parts.append(f"Từ ngày: {start_date} - Đến ngày: {end_date}")
            
        filter_parts.append(f"Cụm: {cum or 'Tất cả'}")
        filter_parts.append(f"Bưu điện Xã: {bdx or 'Tất cả'}")
        filter_parts.append(f"Bưu cục: {buu_cuc or 'Tất cả'}")
        filter_parts.append(f"Loại KH: {', '.join(loai_kh) if loai_kh else 'Tất cả'}")
        hop_dong_str = ", ".join(hop_dong) if isinstance(hop_dong, list) and hop_dong else (hop_dong if isinstance(hop_dong, str) and hop_dong else 'Tất cả')
        filter_parts.append(f"Trạng thái HĐ: {hop_dong_str}")
        
        filter_info = " | ".join(filter_parts)
        
        # 3. Tạo file Excel qua export_helpers
        excel_bytes = generate_customer_excel(df, filter_info)
        
        # 4. Trả về dcc.Download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bao_cao_chi_tiet_khach_hang_{timestamp}.xlsx"
        
        return dcc.send_bytes(excel_bytes, filename=filename)
