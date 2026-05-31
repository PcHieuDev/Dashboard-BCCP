# -*- coding: utf-8 -*-
"""
Layout trang Cảnh báo biến động doanh thu (Alerts).
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def create_alerts_page_layout():
    """
    Tạo Layout cho trang Cảnh báo sụt giảm doanh thu.
    """
    return html.Div([
        html.Div([
            html.Div([
                html.H4("🚨 Hệ thống cảnh báo tự động", style={"margin": 0, "fontWeight": "bold", "color": "#991B1B"}),
                html.P("Phát hiện tự động các điểm sụt giảm doanh thu lớn theo kỳ báo cáo hiện tại.", style={"margin": "5px 0 0 0", "color": "#7F1D1D", "fontSize": "13px"})
            ], className="section-header", style={"borderLeftColor": "#EF4444", "marginTop": 0}),
        ]),
        
        # Chú thích ngưỡng cảnh báo
        dbc.Card([
            dbc.CardBody([
                html.H5("📊 Quy ước mức độ cảnh báo sụt giảm:", style={"fontWeight": "bold", "fontSize": "14px", "marginBottom": "10px", "color": "#334155"}),
                dbc.Row([
                    dbc.Col([
                        html.Span("🟨 Cảnh báo Vàng: ", style={"color": "#D97706", "fontWeight": "bold"}),
                        html.Span("Doanh thu hoặc sản lượng sụt giảm từ ") ,
                        html.B("15.0% đến dưới 30.0%"),
                        html.Span(" so với kỳ trước / cùng kỳ năm trước.")
                    ], md=6),
                    dbc.Col([
                        html.Span("🟥 Cảnh báo Đỏ (Nghiêm trọng): ", style={"color": "#DC2626", "fontWeight": "bold"}),
                        html.Span("Doanh thu hoặc sản lượng sụt giảm từ "),
                        html.B("30.0% trở lên"),
                        html.Span(" so với kỳ trước / cùng kỳ năm trước.")
                    ], md=6)
                ], style={"fontSize": "13px", "color": "#475569"})
            ])
        ], style={"marginBottom": "25px", "border": "1px solid #FCA5A5", "backgroundColor": "#FEF2F2"}),
        
        # Danh sách cảnh báo động
        dbc.Spinner(
            html.Div(id="alerts-list-container"),
            color="danger"
        )
    ])
