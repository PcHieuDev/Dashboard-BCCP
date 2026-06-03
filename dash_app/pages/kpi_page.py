# -*- coding: utf-8 -*-
"""
Layout trang chủ Tổng quan KPI kết hợp biểu đồ trực quan hóa.
"""

import sys
from pathlib import Path
from dash import dcc, html
import dash_bootstrap_components as dbc

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from components.kpi_cards import create_kpi_grid

def create_kpi_page_layout():
    """
    Trả về layout hoàn chỉnh của trang tổng quan KPI gồm 5 thẻ KPI và 3 biểu đồ trực quan.
    
    Returns:
        html.Div: Layout trang KPI.
    """
    grid_layout = create_kpi_grid()
    
    charts_layout = html.Div([
        html.Br(),
        # Hàng biểu đồ 1: Donut (col-4) + Line (col-8)
        dbc.Row([
            # 1. Donut cơ cấu DV (Pie chart)
            dbc.Col([
                html.Div([
                    html.H4("🍕 Cơ cấu doanh thu theo Nhóm dịch vụ", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-service-pie", style={'height': '320px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], md=4, xs=12),
            
            # 2. Line xu hướng doanh thu theo ngày
            dbc.Col([
                html.Div([
                    html.H4("📈 Xu hướng doanh thu theo thời gian", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-revenue-trend", style={'height': '320px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], md=8, xs=12)
        ], className="mb-4", style={"marginBottom": "20px"}),
        
        # Hàng biểu đồ 2: Bar so sánh Cụm (col-12)
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("🏢 So sánh doanh thu giữa các Cụm địa lý", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-cluster-bar", style={'height': '400px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], md=12)
        ])
    ])
    
    return html.Div([
        grid_layout,
        charts_layout
    ])
