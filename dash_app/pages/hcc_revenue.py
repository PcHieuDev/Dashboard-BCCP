# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Doanh thu chi tiết cho Hành chính công (HCC).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
from components.data_table import GROUP_BY_LABEL_MAP

def create_hcc_revenue_layout():
    """
    Tạo Layout cho trang Doanh thu chi tiết HCC (Group By động 2 cấp + So sánh).
    
    Returns:
        html.Div: Layout trang báo cáo doanh thu chi tiết HCC.
    """
    return html.Div([
        html.Div("🎛️ Tùy chọn chiều phân tích (HCC)", className="section-header"),
        
        dbc.Row([
            # Dropdown chọn chiều phân tích chính (Dòng)
            dbc.Col([
                html.Label("Chiều phân tích chính (Dòng)", className="filter-label"),
                dcc.Dropdown(
                    id="hcc-revenue-g1",
                    options=[{"label": k, "value": v} for k, v in GROUP_BY_LABEL_MAP.items()],
                    value="nhom_dv",
                    clearable=False
                )
            ], md=4),
            
            # Dropdown chọn chiều phân tích phụ (Cấp 2)
            dbc.Col([
                html.Label("Chiều phân tích phụ (Cấp 2)", className="filter-label"),
                dcc.Dropdown(
                    id="hcc-revenue-g2",
                    options=[{"label": "Không", "value": "None"}] + [{"label": k, "value": v} for k, v in GROUP_BY_LABEL_MAP.items()],
                    value="None",
                    clearable=False
                )
            ], md=4),
            
            # Radio chọn chế độ so sánh của riêng bảng dữ liệu
            dbc.Col([
                html.Label("So sánh", className="filter-label"),
                dcc.RadioItems(
                    id="hcc-revenue-compare-opt",
                    options=[
                        {"label": " Không so sánh", "value": "none"},
                        {"label": " Kỳ trước", "value": "prev_period"},
                        {"label": " Cùng kỳ năm trước", "value": "yoy"},
                        {"label": " Cả hai", "value": "both"}
                    ],
                    value="none",
                    inline=True,
                    labelStyle={"marginRight": "12px"}
                )
            ], md=4)
        ], style={"marginBottom": "25px"}),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("📥 Xuất Excel", id="hcc-revenue-btn-export-excel", color="success", className="me-2", size="sm"),
                dcc.Download(id="hcc-revenue-download")
            ], width=12, style={"textAlign": "right"})
        ], style={"marginBottom": "15px"}),
        
        html.Hr(),
        
        # Vùng chứa bảng dữ liệu động (bọc bởi Spinner)
        dbc.Spinner(
            html.Div(id="hcc-revenue-table-container"),
            color="primary"
        )
    ])
