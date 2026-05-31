# -*- coding: utf-8 -*-
"""
Callbacks xử lý hiển thị bảng chi tiết khách hàng (CMS) và xuất Excel.
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
    sys.path.append(str(project_root))

from callbacks.utils import resolve_filters_and_query_customer
from callbacks.export_helpers import generate_customer_excel

def register_customer_callbacks(app):
    """
    Đăng ký callback cho trang Chi tiết Khách hàng (CMS).
    """
    
    @app.callback(
        Output("customer-table-container", "children"),
        [Input("tabs-navigation", "value"),
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
    def update_customer_table(tab_val, year, period, start_date, end_date, week_idx, month_val,
                              nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ chạy khi đang ở Tab Chi tiết Khách hàng
        if tab_val != "tab-customer":
            return dash.no_update
            
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

    @app.callback(
        Output("customer-download", "data"),
        [Input("customer-btn-export-excel", "n_clicks")],
        [State("tabs-navigation", "value"),
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
    def export_customer_table(n_clicks, tab_val, year, period, start_date, end_date, week_idx, month_val,
                              nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        ctx = dash.callback_context
        if not ctx.triggered or tab_val != "tab-customer":
            return dash.no_update
            
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
