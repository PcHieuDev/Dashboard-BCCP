# -*- coding: utf-8 -*-
"""
Layout trang biểu đồ trực quan hóa doanh thu (Charts Page).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def create_charts_page_layout():
    """
    Tạo Layout cho trang Biểu đồ trực quan (gồm Line chart xu hướng, Bar chart so sánh Cụm, Pie chart cơ cấu).
    
    Returns:
        html.Div: Layout trang biểu đồ.
    """
    return html.Div([
        html.Div("📊 Trực quan hóa Doanh thu điều hành", className="section-header"),
        
        # Biểu đồ xu hướng (Line Chart) chiếm trọn hàng đầu tiên
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("📈 Xu hướng doanh thu theo thời gian", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-revenue-trend"))
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0'})
            ], md=12)
        ], style={"marginBottom": "20px"}),
        
        # Biểu đồ cơ cấu (Pie Chart) và so sánh Cụm (Bar Chart) chia đôi ở hàng thứ hai
        dbc.Row([
            # Cơ cấu theo nhóm dịch vụ
            dbc.Col([
                html.Div([
                    html.H4("🍕 Cơ cấu doanh thu theo Nhóm dịch vụ", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-service-pie"))
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0'})
            ], md=6),
            
            # So sánh các Cụm địa lý
            dbc.Col([
                html.Div([
                    html.H4("🏢 So sánh doanh thu giữa các Cụm", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-cluster-bar"))
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0'})
            ], md=6)
        ])
    ])
