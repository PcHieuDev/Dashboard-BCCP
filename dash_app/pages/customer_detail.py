# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Doanh thu Chi tiết theo Khách hàng (CMS).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def create_customer_detail_layout():
    """
    Tạo Layout cho trang Chi tiết Khách hàng (CMS) với pivot table.
    
    Returns:
        html.Div: Layout trang báo cáo chi tiết khách hàng.
    """
    return html.Div([
        html.Div("🔍 Chi tiết Doanh thu theo Khách hàng (CMS)", className="section-header"),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("📥 Xuất Excel", id="customer-btn-export-excel", color="success", size="sm"),
                dcc.Download(id="customer-download")
            ], width=12, style={"textAlign": "right"})
        ], style={"marginBottom": "15px"}),
        
        html.Hr(),
        
        # Vùng chứa bảng dữ liệu động (bọc bởi Spinner)
        dbc.Spinner(
            html.Div(id="customer-table-container"),
            color="primary"
        )
    ])
