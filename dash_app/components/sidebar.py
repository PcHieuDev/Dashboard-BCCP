# -*- coding: utf-8 -*-
"""
Component Sidebar chứa các bộ lọc đa chiều (Thời gian, Dịch vụ, Địa lý, Loại KH, Hợp đồng).
Tích hợp hiển thị thông tin tài khoản đăng nhập và tự động khóa/phân quyền địa lý theo Cụm.
"""

from datetime import date, datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_login import current_user

def create_sidebar_layout(filter_opts):
    """
    Tạo cấu trúc Layout cho Sidebar dựa trên danh sách dữ liệu lọc được cung cấp.
    Đồng thời áp dụng phân quyền hiển thị theo tài khoản đăng nhập.
    
    Args:
        filter_opts (dict): Từ điển chứa danh sách các năm, nhóm dịch vụ, spdv, cụm, bdx, bưu cục.
    
    Returns:
        html.Div: Component sidebar của Dash.
    """
    # Lấy thời gian hiện tại làm mặc định
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    default_year = current_year if (filter_opts["years"] and current_year in filter_opts["years"]) else (filter_opts["years"][0] if filter_opts["years"] else 2026)

    # 1. Tạo hộp thông tin tài khoản đăng nhập (Profile Box)
    profile_box = None
    if current_user and current_user.is_authenticated:
        display_role = "Admin" if current_user.role == "admin" else "Nhân viên"
        profile_box = html.Div([
            html.Div([
                html.Span(f"👤 {current_user.username}", className="user-name"),
                html.Span(f"Quyền: {display_role}" + (f" ({current_user.assigned_cum})" if current_user.assigned_cum else ""), className="user-role"),
            ], className="user-profile-info"),
            dbc.Button("Đăng xuất", id="btn-logout", color="danger", size="sm", className="btn-logout-sidebar")
        ], className="user-profile-box")

    # 2. Phân quyền bộ lọc Cụm dựa trên vai trò người dùng
    cum_value = "Tất cả"
    cum_options = [{"label": "Tất cả Cụm", "value": "Tất cả"}] + [{"label": c, "value": c} for c in filter_opts["cum"]]
    cum_disabled = False
    
    if current_user and current_user.is_authenticated and current_user.role == 'user' and current_user.assigned_cum:
        cum_value = current_user.assigned_cum
        cum_options = [{"label": current_user.assigned_cum, "value": current_user.assigned_cum}]
        cum_disabled = True

    # Tạo menu điều hướng dạng Accordion
    nav_menu = html.Div([
        html.H3("📂 Dịch vụ", className="section-header", style={"marginTop": 0}),
        
        # Link Tổng quan chung
        dcc.Link("📊 Tổng quan chung", href="/", id="nav-global-overview", className="sidebar-menu-item"),
        
        dbc.Accordion([
            # Bưu chính chuyển phát (BCCP)
            dbc.AccordionItem([
                dcc.Link("📈 KPI & Biểu đồ", href="/bccp", id="nav-bccp-kpi", className="sidebar-menu-item"),
                dcc.Link("🔍 Chi tiết khách hàng", href="/bccp/customer", id="nav-bccp-customer", className="sidebar-menu-item"),
                dcc.Link("🆕 Khách hàng mới", href="/bccp/new-customer", id="nav-bccp-new-customer", className="sidebar-menu-item"),
                dcc.Link("🔄 KH hiện hữu", href="/bccp/retention", id="nav-bccp-retention", className="sidebar-menu-item"),
                dcc.Link("📦 Thống kê SP-DV", href="/bccp/service-analysis", id="nav-bccp-service-analysis", className="sidebar-menu-item"),
                dcc.Link("🚨 Cảnh báo doanh thu", href="/bccp/alerts", id="nav-bccp-alerts", className="sidebar-menu-item"),
            ], title="📦 Bưu chính chuyển phát", item_id="menu-bccp"),
            
            # Hành chính công (HCC)
            dbc.AccordionItem([
                dcc.Link("📊 Tổng quan & Chi tiết", href="/hcc", id="nav-hcc-overview", className="sidebar-menu-item"),
                dcc.Link("📊 Báo cáo doanh thu", href="/hcc/revenue", id="nav-hcc-revenue", className="sidebar-menu-item"),
            ], title="🏢 Hành chính công", item_id="menu-hcc"),
            
            # Tài chính Bưu chính (TCBC)
            dbc.AccordionItem([
                dcc.Link("📊 Tổng quan & Chi tiết", href="/tcbc", id="nav-tcbc-overview", className="sidebar-menu-item"),
            ], title="💰 Tài chính Bưu chính", item_id="menu-tcbc"),
            
            # Phân phối bán lẻ (PPBL)
            dbc.AccordionItem([
                dcc.Link("📊 Tổng quan & Chi tiết", href="/ppbl", id="nav-ppbl-overview", className="sidebar-menu-item"),
            ], title="🛍️ Phân phối bán lẻ", item_id="menu-ppbl"),
        ], id="sidebar-accordion", active_item="menu-bccp", flush=True, className="sidebar-accordion")
    ], style={"marginBottom": "20px"})

    return html.Div([
        # Hiển thị profile box ở đầu sidebar
        profile_box if profile_box else html.Div(),
        
        # Menu điều hướng mới
        nav_menu
    ], className="sidebar")
