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
                    ], md=2, xs=12),
                    
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
                    ], md=2, xs=12),
                    
                    # 4. Hành động
                    dbc.Col([
                        html.Label("Hành động", className="filter-label", style={"color": "transparent", "display": "block"}),
                        dbc.Button("🔍 Lọc Dữ liệu", id="btn-customer-filter", color="primary", style={"width": "100%", "marginTop": "-5px"})
                    ], md=2, xs=12)
                ], style={"marginBottom": "0px"})
            ])
        ], style={"marginBottom": "20px", "background": "#F8FAFC", "borderRadius": "8px", "border": "1px solid #E2E8F0"}),
        
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
