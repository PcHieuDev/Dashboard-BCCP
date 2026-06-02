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
                dcc.Link("📈 KPI tổng hợp", href="/bccp", id="nav-bccp-kpi", className="sidebar-menu-item"),
                dcc.Link("📊 Doanh thu chi tiết", href="/bccp/revenue", id="nav-bccp-revenue", className="sidebar-menu-item"),
                dcc.Link("🔍 Chi tiết khách hàng", href="/bccp/customer", id="nav-bccp-customer", className="sidebar-menu-item"),
                dcc.Link("📈 Biểu đồ trực quan", href="/bccp/charts", id="nav-bccp-charts", className="sidebar-menu-item"),
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
                dcc.Link("📊 Doanh thu chi tiết", href="/tcbc", id="nav-tcbc-revenue", className="sidebar-menu-item", style={"display": "none"}),
            ], title="💰 Tài chính Bưu chính", item_id="menu-tcbc"),
            
            # Phân phối bán lẻ (PPBL)
            dbc.AccordionItem([
                dcc.Link("📊 Tổng quan & Chi tiết", href="/ppbl", id="nav-ppbl-overview", className="sidebar-menu-item"),
                dcc.Link("📊 Doanh thu chi tiết", href="/ppbl", id="nav-ppbl-revenue", className="sidebar-menu-item", style={"display": "none"}),
            ], title="🛍️ Phân phối bán lẻ", item_id="menu-ppbl"),
        ], id="sidebar-accordion", active_item="menu-bccp", flush=True, className="sidebar-accordion")
    ], style={"marginBottom": "20px"})

    return html.Div([
        # Hiển thị profile box ở đầu sidebar
        profile_box if profile_box else html.Div(),
        
        # Menu điều hướng mới
        nav_menu,
        
        # Container chứa toàn bộ bộ lọc
        html.Div([
            html.Hr(),
            html.Div([
                html.H3("📅 Thời gian", className="section-header", style={"marginTop": 0}),
                
                # Chọn Năm
                html.Div([
                    html.Label("Năm", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-year",
                        options=[{"label": str(y), "value": y} for y in filter_opts["years"]],
                        value=default_year,
                        clearable=False
                    )
                ], className="filter-group"),
                
                # Chọn Chu kỳ (Ngày / Tuần / Tháng)
                html.Div([
                    html.Label("Chu kỳ", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-period",
                        options=[
                            {"label": "Ngày", "value": "Ngày"},
                            {"label": "Tuần", "value": "Tuần"},
                            {"label": "Tháng", "value": "Tháng"}
                        ],
                        value="Tháng",
                        clearable=False
                    )
                ], className="filter-group"),
                
                # Lọc theo Ngày (DatePickerRange)
                html.Div(id="filter-container-day", children=[
                    html.Label("Khoảng ngày", className="filter-label"),
                    dcc.DatePickerRange(
                        id="sidebar-date-range",
                        display_format="DD/MM/YYYY",
                        min_date_allowed=date(2025, 1, 1),
                        max_date_allowed=date(2027, 12, 31),
                        start_date=date(2026, 1, 1),
                        end_date=date(2026, 1, 31),
                        style={"width": "100%"}
                    )
                ], className="filter-group"),
                
                # Lọc theo Tuần
                html.Div(id="filter-container-week", children=[
                    html.Label("Chọn Tuần", className="filter-label"),
                    dcc.Dropdown(id="sidebar-week-select", clearable=False)
                ], className="filter-group", style={"display": "none"}),
                
                # Lọc theo Tháng
                html.Div(id="filter-container-month", children=[
                    html.Label("Chọn Tháng", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-month-select",
                        options=[{"label": f"Tháng {i:02d}", "value": i} for i in range(1, 13)],
                        value=current_month,
                        clearable=False
                    )
                ], className="filter-group"),
                
                # Chế độ so sánh (Kỳ trước / Cùng kỳ năm trước / Cả hai)
                html.Div([
                    html.Label("Chế độ so sánh", className="filter-label"),
                    # Sẽ đổi thành Checklist ở TIP-010, hiện tại giữ Radio
                    dbc.Checklist(
                        id="sidebar-compare-mode",
                        options=[
                            {"label": " Kỳ trước", "value": "prev_period"},
                            {"label": " Cùng kỳ năm trước", "value": "yoy"},
                            {"label": " Kế hoạch", "value": "plan"}
                        ],
                        value=["prev_period"],
                        inline=False,
                        labelStyle={"display": "block", "marginBottom": "4px"}
                    )
                ], className="filter-group"),
                
            ], style={"marginBottom": "20px"}),
            
            html.Hr(),
            
            html.Div([
                html.H3("🗺️ Bộ lọc chiều", className="section-header"),
                
                # Lọc Cụm (Có phân quyền)
                html.Div([
                    html.Label("Cụm", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-cum",
                        options=cum_options,
                        value=cum_value,
                        disabled=cum_disabled,
                        clearable=False
                    )
                ], className="filter-group"),
                
                # Lọc Bưu điện Huyện/Xã (BDX)
                html.Div([
                    html.Label("Bưu điện Huyện/Xã", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-bdx",
                        options=[{"label": "Tất cả BĐX", "value": "Tất cả"}] + [{"label": b, "value": b} for b in filter_opts["bdx"]],
                        value="Tất cả",
                        clearable=False
                    )
                ], className="filter-group"),
                
                # Lọc Bưu cục chấp nhận
                html.Div([
                    html.Label("Mã bưu cục", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-buu-cuc",
                        options=[{"label": "Tất cả Bưu cục", "value": "Tất cả"}] + filter_opts["buu_cuc"],
                        value="Tất cả",
                        clearable=False
                    )
                ], className="filter-group"),
            ]),
            
            # Bộ lọc dịch vụ BCCP (chỉ hiện khi ở /bccp*)
            html.Div(id="bccp-extra-filters", style={"display": "none"}, children=[
                html.H3("📋 Bộ lọc dịch vụ BCCP", className="section-header"),
                
                # Lọc Nhóm Dịch vụ
                html.Div([
                    html.Label("Nhóm dịch vụ", className="filter-label"),
                    dcc.Dropdown(
                        id="sidebar-nhom-dv",
                        options=[{"label": n, "value": n} for n in filter_opts["nhom_dv"]],
                        multi=True,
                        placeholder="Tất cả dịch vụ"
                    )
                ], className="filter-group"),
                
                # Lọc Loại Khách hàng
                html.Div([
                    html.Label("Loại khách hàng", className="filter-label"),
                    dbc.Checklist(
                        id="sidebar-loai-kh",
                        options=[
                            {"label": " Hiện hữu", "value": "Hiện hữu"},
                            {"label": " KHM/Tái bán", "value": "KHM/Tái bán"},
                            {"label": " Vãng lai", "value": "Vãng lai"}
                        ],
                        value=[],
                        className="custom-checklist",
                        labelStyle={"display": "block", "marginBottom": "4px"}
                    )
                ], className="filter-group"),
                
                # Lọc Trạng thái Hợp đồng
                html.Div([
                    html.Label("Trạng thái Hợp đồng", className="filter-label"),
                    dbc.Checklist(
                        id="sidebar-hop-dong",
                        options=[
                            {"label": " Có HĐ", "value": "Có HĐ"},
                            {"label": " Không HĐ", "value": "Không HĐ"}
                        ],
                        value=[],
                        className="custom-checklist",
                        labelStyle={"display": "block", "marginBottom": "4px"}
                    )
                ], className="filter-group"),
            ])
        ], id="sidebar-filters-container", style={"display": "block"})
    ], className="sidebar")
