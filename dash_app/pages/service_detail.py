# -*- coding: utf-8 -*-
"""
Layout trang Chi tiết sản phẩm dịch vụ BCCP (/bccp/service-detail) v2.0.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def create_service_detail_layout():
    """Tạo Layout trang Chi tiết sản phẩm dịch vụ BCCP"""
    return html.Div([
        html.Div([
            html.Div([
                html.H4("📊 Chi tiết Sản phẩm Dịch vụ BCCP", style={"margin": 0, "fontWeight": "bold", "color": "#1E3A8A"}),
                html.P("Thống kê chi tiết doanh thu theo mã sản phẩm dịch vụ và cơ cấu tỷ trọng nhóm dịch vụ.", style={"margin": "5px 0 0 0", "color": "#64748B", "fontSize": "13px"})
            ], className="section-header", style={"borderLeftColor": "#3B82F6", "marginTop": 0}),
        ], style={"marginBottom": "20px"}),
        
        dbc.Row([
            # Cột trái: Bảng thống kê mã sản phẩm dịch vụ
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Bảng thống kê doanh thu theo mã SPDV", style={"fontWeight": "bold", "backgroundColor": "#F8FAFC"}),
                    dbc.CardBody([
                        dbc.Spinner(html.Div(id="spdv-table-container"), color="primary")
                    ])
                ], style={"boxShadow": "0 1px 3px rgba(0,0,0,0.1)", "border": "1px solid #E2E8F0"})
            ], lg=7, md=12, className="mb-4"),
            
            # Cột phải: Biểu đồ cơ cấu nhóm dịch vụ
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cơ cấu tỷ trọng doanh thu theo nhóm dịch vụ", style={"fontWeight": "bold", "backgroundColor": "#F8FAFC"}),
                    dbc.CardBody([
                        dbc.Spinner(dcc.Graph(id="spdv-pie-chart", style={"height": "350px"}), color="primary")
                    ])
                ], style={"boxShadow": "0 1px 3px rgba(0,0,0,0.1)", "border": "1px solid #E2E8F0"})
            ], lg=5, md=12, className="mb-4")
        ])
    ])
