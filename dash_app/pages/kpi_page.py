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
    Trả về layout hoàn chỉnh của trang tổng quan KPI gồm các thẻ KPI, sức khỏe KH và biểu đồ trực quan.
    
    Returns:
        html.Div: Layout trang KPI.
    """
    grid_layout = create_kpi_grid()
    
    health_layout = html.Div([
        html.Div("🏥 Sức khỏe Khách hàng", className="section-header", style={"marginTop": "20px"}),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("🎯 Tỷ lệ duy trì KH (%)", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="health-gauge-retention", style={"height": "250px"}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=4, md=12, className="mb-3"),
            dbc.Col([
                dbc.Spinner(html.Div(id="health-khm-card", style={'height': '100%'}))
            ], lg=4, md=6, className="mb-3"),
            dbc.Col([
                dbc.Spinner(html.Div(id="health-vanglai-card", style={'height': '100%'}))
            ], lg=4, md=6, className="mb-3")
        ], className="mb-4", style={"marginBottom": "20px"})
    ])
    
    charts_layout = html.Div([
        html.Br(),
        # Hàng biểu đồ 1: Pie DV (col-3) + Pie KH (col-3) + Line (col-6)
        dbc.Row([
            # 1. Pie cơ cấu DV
            dbc.Col([
                html.Div([
                    html.H4("🍕 Cơ cấu DV", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-service-pie", style={'height': '320px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], lg=3, md=6, xs=12, className="mb-3"),
            
            # 2. Pie cơ cấu KH
            dbc.Col([
                html.Div([
                    html.H4("👥 Cơ cấu KH", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-customer-pie", style={'height': '320px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], lg=3, md=6, xs=12, className="mb-3"),
            
            # 3. Line xu hướng doanh thu theo tuần
            dbc.Col([
                html.Div([
                    html.H4("📈 Xu hướng tuần BCCP", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-revenue-trend", style={'height': '320px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], lg=6, md=12, xs=12, className="mb-3")
        ], className="mb-4", style={"marginBottom": "20px"}),
        
        # Hàng biểu đồ 2: Bar so sánh Cụm (col-12)
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("🏢 So sánh doanh thu giữa các Cụm địa lý", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-cluster-bar", style={'height': '400px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'})
            ], md=12, className="mb-4")
        ], className="mb-4", style={"marginBottom": "20px"}),
        
        # Hàng biểu đồ 3: Area luân chuyển KH (Col lg=7) + Top 10 CMS (Col lg=5)
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("📈 Luân chuyển KH theo tháng (DT)", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="chart-customer-area", style={'height': '350px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=7, md=12, className="mb-3"),
            dbc.Col([
                html.Div([
                    html.H4("🏆 Top 10 khách hàng CMS", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(html.Div(id="top-cms-table-container"))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=5, md=12, className="mb-3")
        ], className="g-3")
    ])
    
    return html.Div([
        grid_layout,
        health_layout,
        charts_layout
    ])
