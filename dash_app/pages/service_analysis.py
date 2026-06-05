# -*- coding: utf-8 -*-
"""
Layout trang Thống kê Sản phẩm Dịch vụ (SP-DV).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
from components.data_table import GROUP_BY_LABEL_MAP

def create_service_analysis_layout():
    return html.Div([
        html.Div("⚙️ Phân tích theo Gói cước (SP-DV)", className="section-header"),
        
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("So sánh", className="filter-label"),
                        dcc.RadioItems(
                            id="service-analysis-compare-opt",
                            options=[
                                {"label": " Không so sánh", "value": "none"},
                                {"label": " Kỳ trước", "value": "prev_period"},
                                {"label": " Cùng kỳ năm trước", "value": "yoy"},
                                {"label": " Cả hai", "value": "both"}
                            ],
                            value="none",
                            inline=True,
                            labelStyle={"marginRight": "12px"},
                            style={"paddingTop": "8px"}
                        )
                    ], md=12, xs=12)
                ])
            ])
        ], style={"marginBottom": "20px", "background": "#F8FAFC", "borderRadius": "8px", "border": "1px solid #E2E8F0"}),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("📥 Xuất Excel", id="service-analysis-btn-export", color="success", size="sm"),
                dcc.Download(id="service-analysis-download")
            ], width=12, style={"textAlign": "right"})
        ], style={"marginBottom": "10px"}),
        
        dbc.Spinner(
            html.Div(id="service-analysis-table-container", style={"marginBottom": "30px"}),
            color="primary"
        )
    ])
