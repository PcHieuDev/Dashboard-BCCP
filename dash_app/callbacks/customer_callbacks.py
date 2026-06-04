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
import sqlite3
import pandas as pd

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
    # 0. CALLBACK CASCADE: NHÓM DV -> MÃ DỊCH VỤ CỤ THỂ
    # ==============================================================================
    @app.callback(
        Output("customer-filter-spdv", "options"),
        [Input("customer-filter-nhom-dv", "value")]
    )
    def update_spdv_options(nhom_dv_selected):
        """Load SPDV options dựa trên nhóm DV đã chọn."""
        if not DB_PATH.exists():
            return []
            
        conn = sqlite3.connect(str(DB_PATH))
        try:
            query = "SELECT DISTINCT ma_dich_vu, ten_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'BCCP'"
            params = []
            if nhom_dv_selected:
                placeholders = ",".join(["?"] * len(nhom_dv_selected))
                query += f" AND nhom_dich_vu IN ({placeholders})"
                params.extend(nhom_dv_selected)
            query += " ORDER BY ma_dich_vu"
            
            df = pd.read_sql_query(query, conn, params=params)
            options = [{"label": f"{r['ma_dich_vu']} - {r['ten_dich_vu']}", "value": r['ma_dich_vu']} for _, r in df.iterrows()]
        except Exception as e:
            print(f"Error loading SPDV options: {e}")
            options = []
        finally:
            conn.close()
            
        return options

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
         Input("customer-filter-hop-dong", "value"),
         Input("customer-filter-spdv", "value")],
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
    def update_revenue_table(n_clicks, tab_val, g1, g2, compare_opt, nhom_dv, loai_kh, hop_dong, spdv,
                             year, period, start_date, end_date, week_idx, month_val, cum, bdx, buu_cuc):
        # Chạy khi ở tab Chi tiết Khách hàng (do đã gộp trang)
        if tab_val != "tab-customer" or tab_val is None:
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

    # ==============================================================================
    # 2. ĐÃ XÓA CALLBACK XUẤT EXCEL BẢNG DOANH THU THEO YÊU CẦU TIP-11-002
    # ==============================================================================

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
         Input("customer-filter-hop-dong", "value"),
         Input("customer-filter-spdv", "value")],
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
    def update_customer_table(n_clicks, tab_val, nhom_dv, loai_kh, hop_dong, spdv,
                              year, period, start_date, end_date, week_idx, month_val, cum, bdx, buu_cuc):
        # Chỉ chạy khi đang ở Tab Chi tiết Khách hàng
        if tab_val != "tab-customer" or tab_val is None:
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
            'cms': 'Mã CMS',
            'loai_kh': 'Tên Khách hàng', # Thay thế tạm vì không có cột tên
            'nhom_dv_chinh': 'Nhóm DV chính',
            'Tổng SL': 'Sản lượng',
            'Tổng Cước TT': 'Cước không VAT'
        }
        
        if not df.empty:
            cuoc_cols = [c for c in df.columns if '] Cước TT' in c]
            def get_main_dv(row):
                max_val = 0
                main_dv = 'Chưa rõ'
                for c in cuoc_cols:
                    if row[c] > max_val:
                        max_val = row[c]
                        main_dv = c.split(']')[0].replace('[', '')
                return main_dv
            df['nhom_dv_chinh'] = df.apply(get_main_dv, axis=1) if cuoc_cols else 'Chưa rõ'
        
        keep_cols = ['cms', 'loai_kh', 'nhom_dv_chinh', 'Tổng SL', 'Tổng Cước TT']
        columns = []
        for c in keep_cols:
            if c in df.columns:
                name = col_labels.get(c, c)
                col_def = {"name": name, "id": c}
                if c not in ['cms', 'loai_kh', 'nhom_dv_chinh']:
                    col_def["type"] = "numeric"
                    col_def["format"] = Format(group=Group.yes)
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
         State("customer-filter-hop-dong", "value"),
         State("customer-filter-spdv", "value")],
        prevent_initial_call=True
    )
    def export_customer_table(n_clicks, tab_val, year, period, start_date, end_date, week_idx, month_val,
                              nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong, spdv):
        ctx = dash.callback_context
        if not ctx.triggered or tab_val != "tab-customer" or tab_val is None:
            return dash.no_update
            
        # 1. Truy vấn toàn bộ dữ liệu
        _, _, _, df = resolve_filters_and_query_customer(
            year, period, start_date, end_date, week_idx, month_val,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong
        )
        
        if df.empty:
            return dash.no_update
            
        if not df.empty:
            cuoc_cols = [c for c in df.columns if '] Cước TT' in c]
            def get_main_dv(row):
                max_val = 0
                main_dv = 'Chưa rõ'
                for c in cuoc_cols:
                    if row[c] > max_val:
                        max_val = row[c]
                        main_dv = c.split(']')[0].replace('[', '')
                return main_dv
            df['nhom_dv_chinh'] = df.apply(get_main_dv, axis=1) if cuoc_cols else 'Chưa rõ'
            
        keep_cols = ['cms', 'loai_kh', 'nhom_dv_chinh', 'Tổng SL', 'Tổng Cước TT']
        df = df[[c for c in keep_cols if c in df.columns]]
        
        col_rename = {
            'cms': 'Mã CMS',
            'loai_kh': 'Tên Khách hàng',
            'nhom_dv_chinh': 'Nhóm DV chính',
            'Tổng SL': 'Sản lượng',
            'Tổng Cước TT': 'Cước không VAT'
        }
        df = df.rename(columns=col_rename)
        
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
        if spdv:
            filter_parts.append(f"SPDV cụ thể: {', '.join(spdv)}")
            
        filter_info = " | ".join(filter_parts)
        
        # 3. Tạo file Excel qua export_helpers
        excel_bytes = generate_customer_excel(df, filter_info)
        
        # 4. Trả về dcc.Download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bao_cao_chi_tiet_khach_hang_{timestamp}.xlsx"
        
        return dcc.send_bytes(excel_bytes, filename=filename)
