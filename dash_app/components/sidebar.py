# -*- coding: utf-8 -*-
"""
Component Sidebar chỉ chứa thông tin tài khoản đăng nhập (Profile Box)
và Menu điều hướng các trang dịch vụ. Đã lược bỏ toàn bộ phần bộ lọc.
"""

from datetime import datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_login import current_user

def create_sidebar_layout() -> html.Div:
    """
    Tạo cấu trúc Layout cho Sidebar chỉ chứa Menu điều hướng và hộp thông tin tài khoản.
    
    Returns:
        html.Div: Component sidebar của Dash.
    """
    # 1. Hộp thông tin tài khoản đăng nhập (Profile Box)
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

    # 2. Menu điều hướng dạng Accordion thu gọn
    nav_menu = html.Div([
        html.H3("📂 Dịch vụ", className="section-header", style={"marginTop": 0}),
        
        # Link Tổng quan chung
        dcc.Link("📊 Tổng quan chung", href="/", id="nav-global-overview", className="sidebar-menu-item"),
        
        dbc.Accordion([
            # Bưu chính chuyển phát (BCCP)
            dbc.AccordionItem([
                dcc.Link("📈 Tổng quan dịch vụ", href="/bccp", id="nav-bccp-kpi", className="sidebar-menu-item"),
                dcc.Link("🆕 Khách hàng mới/tái bán", href="/bccp/new-customer", id="nav-bccp-new-customer", className="sidebar-menu-item"),
                dcc.Link("🔄 KH hiện hữu", href="/bccp/retention", id="nav-bccp-retention", className="sidebar-menu-item"),
                dcc.Link("🔍 Chi tiết khách hàng", href="/bccp/customer", id="nav-bccp-customer", className="sidebar-menu-item"),
                dcc.Link("📋 Chi tiết sản phẩm dịch vụ", href="/bccp/service-detail", id="nav-bccp-service-detail", className="sidebar-menu-item"),
            ], title="📦 Bưu chính chuyển phát", item_id="menu-bccp"),
            
            # Hành chính công (HCC)
            dbc.AccordionItem([
                dcc.Link("📈 Tổng quan dịch vụ", href="/hcc", id="nav-hcc-overview", className="sidebar-menu-item"),
            ], title="🏢 Hành chính công", item_id="menu-hcc"),
            
            # Tài chính Bưu chính (TCBC)
            dbc.AccordionItem([
                dcc.Link("📈 Tổng quan dịch vụ", href="/tcbc", id="nav-tcbc-overview", className="sidebar-menu-item"),
            ], title="💰 Tài chính Bưu chính", item_id="menu-tcbc"),
            
            # Phân phối bán lẻ (PPBL)
            dbc.AccordionItem([
                dcc.Link("📈 Tổng quan dịch vụ", href="/ppbl", id="nav-ppbl-overview", className="sidebar-menu-item"),
            ], title="🛍️ Phân phối bán lẻ", item_id="menu-ppbl"),
        ], id="sidebar-accordion", active_item=None, flush=True, className="sidebar-accordion")
    ], style={"marginBottom": "20px"})

    return html.Div([
        # Hiển thị profile box ở đầu sidebar
        profile_box if profile_box else html.Div(),
        
        # Menu điều hướng
        nav_menu
    ], className="sidebar")
