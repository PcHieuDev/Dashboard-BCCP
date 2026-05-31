# -*- coding: utf-8 -*-
"""
Các callbacks quản lý hành vi và tương tác của bộ lọc trên Sidebar.
"""

import sqlite3
import pandas as pd
from datetime import date, datetime
from dash import Output, Input, html
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from config.week_calendar import get_week_list

def register_sidebar_callbacks(app):
    """
    Đăng ký các callback của Sidebar với ứng dụng Dash.
    """
    
    # 1. Callback chuyển đổi hiển thị của DatePickerRange, Tuần, Tháng theo chu kỳ chọn
    @app.callback(
        [Output("filter-container-day", "style"),
         Output("filter-container-week", "style"),
         Output("filter-container-month", "style")],
        [Input("sidebar-period", "value")]
    )
    def toggle_period_filters(period):
        if period == "Ngày":
            return {"display": "block"}, {"display": "none"}, {"display": "none"}
        elif period == "Tuần":
            return {"display": "none"}, {"display": "block"}, {"display": "none"}
        else:  # Tháng
            return {"display": "none"}, {"display": "none"}, {"display": "block"}

    # 2. Callback cập nhật danh sách Tuần theo Năm đã chọn (Đã sửa lỗi ValueError unpack 3-tuple)
    @app.callback(
        [Output("sidebar-week-select", "options"),
         Output("sidebar-week-select", "value")],
        [Input("sidebar-year", "value")]
    )
    def update_week_dropdown(year):
        if not year:
            return [], None
        weeks = get_week_list(int(year))
        options = []
        for i, (w_num, w_from, w_to) in enumerate(weeks):
            options.append({
                "label": f"Tuần {w_num:02d} ({w_from.strftime('%d/%m')} - {w_to.strftime('%d/%m')})",
                "value": i
            })
        # Mặc định chọn tuần đầu tiên (index 0)
        return options, 0 if options else None

    # 3. Callback lọc động địa lý: Cụm -> BĐX -> Bưu cục
    @app.callback(
        [Output("sidebar-bdx", "options"),
         Output("sidebar-buu-cuc", "options")],
        [Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value")]
    )
    def update_geographic_filters(cum_val, bdx_val):
        if not DB_PATH.exists():
            return [{"label": "Tất cả BĐX", "value": "Tất cả"}], [{"label": "Tất cả Bưu cục", "value": "Tất cả"}]
            
        conn = sqlite3.connect(str(DB_PATH))
        try:
            # Lọc danh sách BĐX theo Cụm
            query_bdx = "SELECT DISTINCT ten_BDX FROM dim_buucuc WHERE ten_BDX IS NOT NULL"
            params_bdx = []
            if cum_val and cum_val != "Tất cả":
                query_bdx += " AND ten_Cum = ?"
                params_bdx.append(cum_val)
            query_bdx += " ORDER BY ten_BDX"
            df_bdx = pd.read_sql_query(query_bdx, conn, params=params_bdx)
            bdx_opts = [{"label": "Tất cả BĐX", "value": "Tất cả"}] + [{"label": b, "value": b} for b in df_bdx["ten_BDX"].tolist()]
            
            # Lọc danh sách Bưu cục theo Cụm và BĐX
            query_bc = "SELECT ma_bc, ten_Buu_cuc FROM dim_buucuc WHERE ma_bc IS NOT NULL"
            params_bc = []
            if cum_val and cum_val != "Tất cả":
                query_bc += " AND ten_Cum = ?"
                params_bc.append(cum_val)
            # Chỉ lọc theo BĐX nếu bdx_val hợp lệ và nằm trong Cụm được chọn
            if bdx_val and bdx_val != "Tất cả" and bdx_val in df_bdx["ten_BDX"].tolist():
                query_bc += " AND ten_BDX = ?"
                params_bc.append(bdx_val)
            query_bc += " ORDER BY ma_bc"
            df_bc = pd.read_sql_query(query_bc, conn, params=params_bc)
            bc_opts = [{"label": "Tất cả Bưu cục", "value": "Tất cả"}] + [{"label": f"{r['ma_bc']} - {r['ten_Buu_cuc']}", "value": r['ma_bc']} for _, r in df_bc.iterrows()]
            
        except Exception as e:
            print(f"Error dynamic filters: {e}")
            bdx_opts = [{"label": "Tất cả BĐX", "value": "Tất cả"}]
            bc_opts = [{"label": "Tất cả Bưu cục", "value": "Tất cả"}]
        finally:
            conn.close()
            
        return bdx_opts, bc_opts

    # 4. Callback cập nhật phụ đề Tiêu đề thời kỳ ở Header
    @app.callback(
        Output("header-sub-title", "children"),
        [Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value")]
    )
    def update_header_subtitle(year, period, start_date, end_date, week_idx, month_val):
        if not year:
            return ""
        if period == "Ngày":
            df = f"từ {datetime.fromisoformat(start_date).strftime('%d/%m/%Y') if start_date else ''} đến {datetime.fromisoformat(end_date).strftime('%d/%m/%Y') if end_date else ''}"
        elif period == "Tuần":
            weeks = get_week_list(int(year))
            if week_idx is not None and 0 <= week_idx < len(weeks):
                w_num, w_start, w_end = weeks[week_idx]
                df = f"Tuần {w_num:02d} ({w_start.strftime('%d/%m/%Y')} - {w_end.strftime('%d/%m/%Y')})"
            else:
                df = f"Tuần trong năm {year}"
        else:  # Tháng
            df = f"Tháng {month_val:02d}/{year}"
        return html.Span(["Báo cáo doanh thu thời kỳ ", html.B(df), f" ({period})"])
