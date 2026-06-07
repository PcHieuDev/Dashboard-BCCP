# -*- coding: utf-8 -*-
"""
Các callbacks quản lý hành vi điều hướng của Sidebar, highlight menu hoạt động,
và xử lý đăng xuất.
"""

from datetime import datetime
from dash import Output, Input, html
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.week_calendar import get_week_list

def register_sidebar_callbacks(app):
    """
    Đăng ký các callback của Sidebar với ứng dụng Dash.
    """
    
    # 1. Callback cập nhật phụ đề Tiêu đề thời kỳ ở Header dựa trên các bộ lọc ở Topbar
    @app.callback(
        Output("header-sub-title", "children"),
        [Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value")]
    )
    def update_header_subtitle(year, period, week_val, month_val):
        if not year:
            return ""
        if period == "Tuần":
            weeks = get_week_list(int(year))
            # Tìm tuần tương ứng (week_val là số tuần 1-indexed)
            w_info = next((w for w in weeks if w[0] == week_val), None)
            if w_info:
                w_num, w_start, w_end = w_info
                df = f"Tuần {w_num:02d} ({w_start.strftime('%d/%m/%Y')} - {w_end.strftime('%d/%m/%Y')})"
            else:
                df = f"Tuần trong năm {year}"
        else:  # Tháng
            df = f"Tháng {month_val:02d}/{year}"
        return html.Span(["Báo cáo doanh thu thời kỳ ", html.B(df), f" ({period})"])

    # 2. Callback ẩn/hiện Topbar và highlight menu item theo URL pathname
    @app.callback(
        [Output("topbar-container", "style"),
         Output("sidebar-accordion", "active_item"),
         Output("nav-global-overview", "className"),
         Output("nav-bccp-kpi", "className"),
         Output("nav-bccp-customer", "className"),
         Output("nav-bccp-new-customer", "className"),
         Output("nav-bccp-retention", "className"),
         Output("nav-bccp-service-detail", "className"),
         Output("nav-hcc-overview", "className"),
         Output("nav-tcbc-overview", "className"),
         Output("nav-ppbl-overview", "className"),
         Output("bccp-extra-filters", "style")],
        [Input("url", "pathname")]
    )
    def update_sidebar_state(pathname):
        # Mặc định tất cả các class là 'sidebar-menu-item'
        classes = {
            "global": "sidebar-menu-item",
            "bccp-kpi": "sidebar-menu-item",
            "bccp-cust": "sidebar-menu-item",
            "bccp-new-cust": "sidebar-menu-item",
            "bccp-ret": "sidebar-menu-item",
            "bccp-detail": "sidebar-menu-item",
            "hcc-over": "sidebar-menu-item",
            "tcbc-over": "sidebar-menu-item",
            "ppbl-over": "sidebar-menu-item"
        }
        
        # Ẩn hiện bộ lọc: Luôn hiển thị Topbar cho tất cả các trang
        topbar_style = {"display": "block"}
        
        bccp_filter_style = {"display": "block"} if (pathname and pathname.startswith("/bccp")) else {"display": "none"}
        
        # Xác định active accordion item: Chỉ mở khi ở trang BCCP, các trang khác thì đóng
        if pathname and pathname.startswith("/bccp"):
            active_accordion = "menu-bccp"
        else:
            active_accordion = None
                
        # Highlight active menu link
        if not pathname or pathname == "/":
            classes["global"] = "sidebar-menu-item active"
        elif pathname == "/bccp":
            classes["bccp-kpi"] = "sidebar-menu-item active active-bccp"
        elif pathname == "/bccp/customer":
            classes["bccp-cust"] = "sidebar-menu-item active active-bccp"
        elif pathname == "/bccp/new-customer":
            classes["bccp-new-cust"] = "sidebar-menu-item active active-bccp"
        elif pathname == "/bccp/retention":
            classes["bccp-ret"] = "sidebar-menu-item active active-bccp"
        elif pathname == "/bccp/service-detail":
            classes["bccp-detail"] = "sidebar-menu-item active active-bccp"
        elif pathname == "/hcc":
            classes["hcc-over"] = "sidebar-menu-item active active-hcc"
        elif pathname == "/tcbc":
            classes["tcbc-over"] = "sidebar-menu-item active active-tcbc"
        elif pathname == "/ppbl":
            classes["ppbl-over"] = "sidebar-menu-item active active-ppbl"
            
        return (
            topbar_style,
            active_accordion,
            classes["global"],
            classes["bccp-kpi"],
            classes["bccp-cust"],
            classes["bccp-new-cust"],
            classes["bccp-ret"],
            classes["bccp-detail"],
            classes["hcc-over"],
            classes["tcbc-over"],
            classes["ppbl-over"],
            bccp_filter_style
        )
