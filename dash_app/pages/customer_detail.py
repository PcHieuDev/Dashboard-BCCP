# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Doanh thu Chi tiết theo Khách hàng (CMS) kết hợp Doanh thu xoay chiều
và Bộ lọc dịch vụ BCCP Inline.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
from components.data_table import GROUP_BY_LABEL_MAP

def create_customer_detail_layout():
    """
    Tạo Layout cho trang Chi tiết Khách hàng (CMS) và Doanh thu xoay chiều,
    tích hợp bộ lọc inline BCCP.
    
    Returns:
        html.Div: Layout trang báo cáo.
    """
    return html.Div([
        # ==============================================================================
        # PHẦN A & B - BỘ LỌC NÂNG CAO VÀ PHÂN TÍCH XOAY CHIỀU
        # ==============================================================================
        html.Div("⚙️ Bộ lọc Nâng cao", className="section-header"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # 1. Nhóm dịch vụ
                    dbc.Col([
                        html.Label("Nhóm dịch vụ", className="filter-label"),
                        dcc.Dropdown(
                            id="customer-filter-nhom-dv",
                            options=[{"label": x, "value": x} for x in ['Truyền thống', 'TMĐT', 'Quốc tế', 'Phát hành báo chí']],
                            value=['Truyền thống', 'TMĐT', 'Quốc tế'], # Mặc định
                            multi=True,
                            placeholder="Tất cả Nhóm DV..."
                        )
                    ], md=3, xs=12),
                    
                    # 1.1 Dịch vụ cụ thể
                    dbc.Col([
                        html.Label("Dịch vụ cụ thể", className="filter-label"),
                        dcc.Dropdown(
                            id="customer-filter-spdv",
                            multi=True,
                            placeholder="Tất cả dịch vụ...",
                            style={"fontSize": "13px"}
                        )
                    ], md=3, xs=12),
                    
                    # 2. Loại khách hàng
                    dbc.Col([
                        html.Label("Loại khách hàng", className="filter-label"),
                        dbc.Checklist(
                            id="customer-filter-loai-kh",
                            options=[
                                {"label": " Hiện hữu", "value": "Hiện hữu"},
                                {"label": " KHM/Tái bán", "value": "KHM/Tái bán"},
                                {"label": " Vãng lai", "value": "Vãng lai"}
                            ],
                            value=['Hiện hữu', 'KHM/Tái bán', 'Vãng lai'],
                            inline=True,
                            style={"paddingTop": "8px"}
                        )
                    ], md=3, xs=12),
                    
                    # 3. Trạng thái hợp đồng
                    dbc.Col([
                        html.Label("Trạng thái hợp đồng", className="filter-label"),
                        dbc.Checklist(
                            id="customer-filter-hop-dong",
                            options=[
                                {"label": " Có hợp đồng", "value": "Có HĐ"},
                                {"label": " Không hợp đồng", "value": "Không HĐ"}
                            ],
                            value=['Có HĐ', 'Không HĐ'],
                            inline=True,
                            style={"paddingTop": "8px"}
                        )
                    ], md=3, xs=12)
                ], style={"marginBottom": "20px"}),
                html.Hr(),
                dbc.Row([
                    # Dropdown chọn chiều phân tích chính (Dòng)
                    dbc.Col([
                        html.Label("Chiều phân tích chính (Dòng)", className="filter-label"),
                        dcc.Dropdown(
                            id="revenue-g1",
                            options=[{"label": k, "value": v} for k, v in GROUP_BY_LABEL_MAP.items()],
                            value="nhom_dv",
                            clearable=False
                        )
                    ], md=4, xs=12),
                    
                    # Dropdown chọn chiều phân tích phụ (Cấp 2)
                    dbc.Col([
                        html.Label("Chiều phân tích phụ (Cấp 2)", className="filter-label"),
                        dcc.Dropdown(
                            id="revenue-g2",
                            options=[{"label": "Không", "value": "None"}] + [{"label": k, "value": v} for k, v in GROUP_BY_LABEL_MAP.items()],
                            value="None",
                            clearable=False
                        )
                    ], md=4, xs=12),
                    
                    # Radio chọn chế độ so sánh
                    dbc.Col([
                        html.Label("So sánh", className="filter-label"),
                        dcc.RadioItems(
                            id="revenue-compare-opt",
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
                    ], md=4, xs=12)
                ])
            ])
        ], style={"marginBottom": "20px", "background": "#F8FAFC", "borderRadius": "8px", "border": "1px solid #E2E8F0"}),
        
        dbc.Spinner(
            html.Div(id="revenue-table-container", style={"marginBottom": "30px"}),
            color="primary"
        ),
        
        html.Hr(style={"margin": "30px 0"}),
        
        # ==============================================================================
        # PHẦN C - PIVOT CMS CHI TIẾT
        # ==============================================================================
        html.Div("🔍 Chi tiết Doanh thu theo Khách hàng (CMS)", className="section-header"),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("📥 Xuất Excel Khách hàng", id="customer-btn-export-excel", color="success", size="sm"),
                dcc.Download(id="customer-download")
            ], width=12, style={"textAlign": "right"})
        ], style={"marginBottom": "10px"}),
        
        dbc.Spinner(
            html.Div(id="customer-table-container"),
            color="primary"
        )
    ])
