# -*- coding: utf-8 -*-
"""
Layout trang Tổng quan chung (Global Overview).
Hiển thị KPI 4 dịch vụ, biểu đồ cơ cấu và so sánh thực tế vs kế hoạch lũy kế (YTD).
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def make_global_kpi_card_layout(card_id, title, icon, border_color):
    """Tạo KPI card tùy biến cho trang Tổng quan với viền màu đặc trưng"""
    return html.Div([
        html.Div([
            html.Div(title, className="kpi-title"),
            html.Span(icon, style={"fontSize": "22px", "float": "right", "marginTop": "-24px"})
        ]),
        html.Div("— đ", id=f"{card_id}-value", className="kpi-value", style={"marginTop": "8px"}),
        # Chứa thông tin so sánh
        html.Div(id=f"{card_id}-compare-info", style={"minHeight": "60px", "marginTop": "6px"})
    ], className="kpi-card", style={"borderLeft": f"5px solid {border_color}", "height": "100%"})

def create_global_overview_layout():
    """Tạo layout chính cho trang Tổng quan chung"""
    return html.Div([
        # Block 1: 4 Thẻ KPI
        html.Div("📊 Doanh thu các nhóm dịch vụ", className="section-header", style={"marginTop": 0}),
        dbc.Row([
            dbc.Col(make_global_kpi_card_layout("global-kpi-bccp", "Bưu chính Chuyển phát (BCCP)", "📦", "#2196F3"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_global_kpi_card_layout("global-kpi-hcc", "Hành chính công (HCC)", "🏛️", "#4CAF50"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_global_kpi_card_layout("global-kpi-tcbc", "Tài chính Bưu chính (TCBC)", "💰", "#FF9800"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_global_kpi_card_layout("global-kpi-ppbl", "Phân phối bán lẻ (PPBL)", "🛍️", "#9C27B0"), lg=3, md=6, className="mb-3"),
        ], className="g-3"),
        
        # Block 2: Biểu đồ cơ cấu & so sánh thực tế vs kế hoạch
        dbc.Row([
            # Biểu đồ Donut cơ cấu bên trái
            dbc.Col([
                html.Div([
                    html.Div("🍩 Cơ cấu doanh thu", className="section-header"),
                    dcc.Graph(id="global-donut-chart", config={"displayModeBar": False})
                ], className="info-box", style={"height": "100%", "padding": "15px"})
            ], lg=4, md=12, className="mb-3"),
            
            # Biểu đồ thanh ngang YTD bên phải
            dbc.Col([
                html.Div([
                    html.Div("📈 Doanh thu Thực tế vs Kế hoạch lũy kế (YTD)", className="section-header"),
                    dcc.Graph(id="global-ytd-chart", config={"displayModeBar": False})
                ], className="info-box", style={"height": "100%", "padding": "15px"})
            ], lg=8, md=12, className="mb-3")
        ], className="g-3", style={"marginTop": "10px"}),
        
        # Block 3: Bảng doanh thu chi tiết phân cấp theo cụm
        html.Div([
            html.Div("📋 Chi tiết doanh thu theo Cụm", className="section-header"),
            html.Div(id="global-cum-table-container")
        ], style={"marginTop": "20px"})
    ])
