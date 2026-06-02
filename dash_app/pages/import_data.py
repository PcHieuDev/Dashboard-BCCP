# -*- coding: utf-8 -*-
"""
Layout trang Nhập dữ liệu (Upload Excel & xem lịch sử).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def create_import_page_layout():
    """
    Tạo Layout cho trang Nhập dữ liệu vào hệ thống SQLite.
    
    Returns:
        html.Div: Layout trang nhập liệu.
    """
    return html.Div([
        html.Div("📥 Nhập dữ liệu mới vào hệ thống", className="section-header"),
        
        dbc.Row([
            # Cột bên trái: Chọn loại và Upload File Excel để Import
            dbc.Col([
                html.Div([
                    # Dropdown chọn loại dữ liệu
                    html.Div([
                        html.Label("Loại dữ liệu nạp", className="filter-label"),
                        dcc.Dropdown(
                            id="import-service-type",
                            options=[
                                {"label": "Giao dịch Bưu chính chuyển phát (BCCP)", "value": "BCCP"},
                                {"label": "Giao dịch Hành chính công (HCC)", "value": "HCC"},
                                {"label": "Giao dịch Tài chính Bưu chính (TCBC)", "value": "TCBC"},
                                {"label": "Giao dịch Phân phối bán lẻ (PPBL)", "value": "PPBL"},
                                {"label": "Kế hoạch chỉ tiêu doanh thu (Plans)", "value": "PLAN"}
                            ],
                            value="BCCP",
                            clearable=False,
                            style={"marginBottom": "15px"}
                        ),
                        html.Div(id="import-format-instructions", style={
                            "fontSize": "13px",
                            "color": "#475569",
                            "backgroundColor": "#F8FAFC",
                            "padding": "12px 14px",
                            "borderRadius": "8px",
                            "border": "1px solid #E2E8F0",
                            "marginBottom": "15px"
                        })
                    ]),
                    
                    # Upload component
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Kéo thả hoặc ',
                            html.A('Chọn file Excel (.xlsx, .xls, .csv)')
                        ]),
                        style={
                            'width': '100%',
                            'height': '120px',
                            'lineHeight': '120px',
                            'borderWidth': '1.5px',
                            'borderStyle': 'dashed',
                            'borderRadius': '12px',
                            'textAlign': 'center',
                            'borderColor': '#94A3B8',
                            'cursor': 'pointer',
                            'backgroundColor': '#F8FAFC'
                        },
                        # Chỉ cho phép nạp 1 file mỗi lần
                        multiple=False
                    ),
                    # Thẻ hiển thị thông tin file đã chọn
                    html.Div(id='selected-file-info', style={'marginTop': '15px'}),
                    
                    # Nút bấm xác nhận nạp dữ liệu
                    dbc.Button(
                        "🚀 Xác nhận nạp dữ liệu",
                        id="btn-confirm-upload",
                        color="success",
                        className="w-100",
                        style={'marginTop': '15px', 'display': 'none'}
                    ),
                    
                    # Vòng xoay spinner thông báo tiến trình nạp dữ liệu
                    dbc.Spinner(
                        html.Div(id='upload-status-message', style={'marginTop': '15px'}),
                        color="success",
                        type="border",
                        fullscreen=False
                    )
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0'})
            ], md=6),
            
            # Cột bên phải: Hiển thị bảng lịch sử import
            dbc.Col([
                html.Div([
                    html.H4("📜 Lịch sử nạp dữ liệu", style={'marginTop': 0, 'color': '#1E293B', 'fontSize': '16px', 'fontWeight': 'bold'}),
                    dbc.Spinner(html.Div(id='import-history-container'))
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'minHeight': '180px'})
            ], md=6)
        ])
    ])
