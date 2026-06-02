# -*- coding: utf-8 -*-
"""
Layout trang Dịch vụ dùng chung (HCC, TCBC, PPBL).
Tự động thay đổi tiêu đề, bộ lọc inline, KPI cards, bảng chi tiết và biểu đồ cột.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def create_service_page_layout(service_type):
    """
    Tạo layout động cho trang dịch vụ cụ thể.
    
    Args:
        service_type (str): HCC / TCBC / PPBL
    """
    service_names = {
        "HCC": "🏢 Hành chính công",
        "TCBC": "💰 Tài chính Bưu chính",
        "PPBL": "🛍️ Phân phối bán lẻ"
    }
    
    name = service_names.get(service_type, service_type)
    
    return html.Div([
        # Lưu trữ service_type hiện tại để callback nhận biết
        dcc.Store(id="service-type-store", data=service_type),
        
        # Block 1: Bộ lọc Inline trên đầu trang
        html.Div([
            dbc.Row([
                # Bộ lọc Năm
                dbc.Col([
                    html.Label("Năm", className="filter-label"),
                    dcc.Dropdown(
                        id="service-filter-year",
                        options=[{"label": "2026", "value": 2026}],
                        value=2026,
                        clearable=False
                    )
                ], xs=12, sm=4, md=2),
                
                # Bộ lọc Tháng
                dbc.Col([
                    html.Label("Tháng", className="filter-label"),
                    dcc.Dropdown(
                        id="service-filter-month",
                        options=[{"label": f"Tháng {i:02d}", "value": i} for i in range(1, 13)],
                        value=6, # Default tháng 6
                        clearable=False
                    )
                ], xs=12, sm=4, md=2),
                
                # Bộ lọc Cụm
                dbc.Col([
                    html.Label("Cụm địa lý", className="filter-label"),
                    dcc.Dropdown(
                        id="service-filter-cum",
                        placeholder="Tất cả Cụm",
                        value="Tất cả",
                        clearable=False
                    )
                ], xs=12, sm=4, md=3),
                
                # Nút Xuất Excel bên phải
                dbc.Col([
                    dbc.Button("📥 Xuất Excel", id="service-export-excel-btn", color="success", className="w-100", style={"marginTop": "24px"}),
                    dcc.Download(id="service-download-excel")
                ], xs=12, sm=12, md=3, className="ms-auto")
            ], className="align-items-center g-3")
        ], className="info-box mb-4", style={"padding": "15px 20px"}),
        
        # Block 2: KPI & Sparkline
        html.Div(id="service-kpi-container"),
        
        # Block 3: Biểu đồ cột dịch vụ con & Bảng chi tiết
        dbc.Row([
            # Biểu đồ cột dịch vụ con bên trái
            dbc.Col([
                html.Div([
                    html.Div("📊 Cơ cấu theo dịch vụ con", className="section-header"),
                    dcc.Graph(id="service-bar-chart", config={"displayModeBar": False})
                ], className="info-box", style={"height": "100%", "padding": "15px"})
            ], lg=5, md=12, className="mb-3"),
            
            # Bảng chi tiết bên phải
            dbc.Col([
                html.Div([
                    html.Div(id="service-table-title", className="section-header"),
                    html.Div(id="service-table-container")
                ], className="info-box", style={"height": "100%", "padding": "15px"})
            ], lg=7, md=12, className="mb-3")
        ], className="g-3", style={"marginTop": "10px"})
    ])
