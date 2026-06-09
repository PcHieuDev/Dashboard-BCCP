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
                html.P("Thống kê chi tiết doanh thu và sản lượng theo mã sản phẩm dịch vụ phân rã theo nhóm dịch vụ.", style={"margin": "5px 0 0 0", "color": "#64748B", "fontSize": "13px"})
            ], className="section-header", style={"borderLeftColor": "#3B82F6", "marginTop": 0}),
        ], style={"marginBottom": "20px"}),
        
        # Biểu đồ 1: Doanh thu theo mã SPDV
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Doanh thu theo mã sản phẩm dịch vụ (SPDV)", style={"fontWeight": "bold", "backgroundColor": "#F8FAFC"}),
                    dbc.CardBody([
                        dbc.Spinner(dcc.Graph(id="spdv-revenue-chart", style={"height": "320px"}), color="primary")
                    ])
                ], style={"boxShadow": "0 1px 3px rgba(0,0,0,0.1)", "border": "1px solid #E2E8F0"})
            ], width=12, className="mb-4")
        ]),
        
        # Biểu đồ 2: Sản lượng theo mã SPDV
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sản lượng theo mã sản phẩm dịch vụ (SPDV)", style={"fontWeight": "bold", "backgroundColor": "#F8FAFC"}),
                    dbc.CardBody([
                        dbc.Spinner(dcc.Graph(id="spdv-volume-chart", style={"height": "320px"}), color="primary")
                    ])
                ], style={"boxShadow": "0 1px 3px rgba(0,0,0,0.1)", "border": "1px solid #E2E8F0"})
            ], width=12, className="mb-4")
        ]),
        
        # Bảng thống kê chi tiết theo mã SPDV
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div("Bảng thống kê chi tiết doanh thu & sản lượng theo mã SPDV", style={"display": "inline-block"}),
                        html.Div([
                            dbc.Button("📥 Tải Excel", id="btn-export-service-detail", color="success", size="sm"),
                            dcc.Download(id="download-service-detail")
                        ], style={"float": "right", "marginTop": "-4px"})
                    ], style={"fontWeight": "bold", "backgroundColor": "#F8FAFC"}),
                    dbc.CardBody([
                        dbc.Spinner(html.Div(id="spdv-table-container"), color="primary")
                    ])
                ], style={"boxShadow": "0 1px 3px rgba(0,0,0,0.1)", "border": "1px solid #E2E8F0"})
            ], width=12, className="mb-4")
        ])
    ])
