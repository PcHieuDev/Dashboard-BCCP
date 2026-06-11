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
        # Store để lưu trạng thái nạp dữ liệu (phục vụ cập nhật bảng lịch sử không gây crash JS)
        dcc.Store(id='import-status-store', data=0),
        
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
                                {"label": "Giao dịch Dịch vụ khác (HCC, TCBC, PPBL, PHBC)", "value": "SERVICES"}
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
            ], md=12)
        ]),
        
        dbc.Row([
            # Hiển thị bảng lịch sử import chiếm trọn md=12 ngay phía dưới
            dbc.Col([
                html.Div([
                    html.H4("📜 Lịch sử nạp dữ liệu", style={'marginTop': 0, 'color': '#1E293B', 'fontSize': '16px', 'fontWeight': 'bold'}),
                    dbc.Spinner(html.Div(id='import-history-container'))
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'marginTop': '20px', 'minHeight': '180px'})
            ], md=12)
        ]),
        
        # Khu vực mới ở cuối trang: Import sửa chữa / Đè dữ liệu
        html.Div([
            html.Hr(style={"margin": "30px 0"}),
            html.Div("🛠️ Import sửa chữa / Đè dữ liệu (Xóa dữ liệu cũ & Ghi đè)", className="section-header", style={"color": "#DC2626"}),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.P(
                            "⚠️ CẢNH BÁO: Chế độ này sẽ tự động đọc file Excel nạp lên để xác định Dịch vụ và Khoảng thời gian cụ thể (Ngày/Tuần/Tháng). "
                            "Hệ thống sẽ xóa sạch dữ liệu cũ trùng khớp của dịch vụ và thời gian đó trước khi ghi đè dữ liệu mới. "
                            "Các dịch vụ khác và khoảng thời gian khác vẫn được giữ nguyên vẹn.",
                            style={"fontSize": "14px", "color": "#991B1B", "backgroundColor": "#FEF2F2", "padding": "12px", "borderRadius": "8px", "border": "1px solid #FEE2E2", "marginBottom": "15px"}
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Chọn loại dịch vụ cần sửa", className="filter-label"),
                                dcc.Dropdown(
                                    id="import-service-type-overwrite",
                                    options=[
                                        {"label": "Giao dịch Bưu chính chuyển phát (BCCP)", "value": "BCCP"},
                                        {"label": "Giao dịch Dịch vụ khác (HCC, TCBC, PPBL, PHBC)", "value": "SERVICES"}
                                    ],
                                    value="SERVICES",
                                    clearable=False,
                                    style={"marginBottom": "15px"}
                                )
                            ], md=6),
                            dbc.Col([
                                dcc.Upload(
                                    id='upload-data-overwrite',
                                    children=html.Div([
                                        'Kéo thả hoặc ',
                                        html.A('Chọn file Excel sửa chữa (.xlsx, .csv)')
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '60px',
                                        'lineHeight': '60px',
                                        'borderWidth': '1.5px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '8px',
                                        'textAlign': 'center',
                                        'borderColor': '#EF4444',
                                        'cursor': 'pointer',
                                        'backgroundColor': '#FEF2F2',
                                        'color': '#991B1B'
                                    },
                                    multiple=False
                                )
                            ], md=6)
                        ]),
                        # File info
                        html.Div(id='selected-file-info-overwrite', style={'marginTop': '15px'}),
                        # Button confirm
                        dbc.Button(
                            "🚨 Xác nhận ghi đè dữ liệu sửa chữa",
                            id="btn-confirm-upload-overwrite",
                            color="danger",
                            className="w-100",
                            style={'marginTop': '15px', 'display': 'none'}
                        ),
                        # Status message
                        dbc.Spinner(
                            html.Div(id='upload-status-message-overwrite', style={'marginTop': '15px'}),
                            color="danger",
                            type="border"
                        )
                    ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #FCA5A5'})
                ], md=12)
            ])
        ], style={"marginTop": "20px"}),
        
        # Khu vực mới ở cuối trang: Nạp Kế hoạch chỉ tiêu doanh thu
        html.Div([
            html.Hr(style={"margin": "30px 0"}),
            html.Div("🎯 Nạp Kế hoạch chỉ tiêu doanh thu (Plans)", className="section-header", style={"color": "#0F766E"}),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.P(
                            "File Excel kế hoạch doanh thu năm phân bổ cho các bưu cục. "
                            "Yêu cầu các cột tối thiểu: Năm, Nhóm Chính (BCCP/HCC/TCBC/PPBL), Nhóm DV (nếu có), Mã BC, KH Doanh thu.",
                            style={"fontSize": "14px", "color": "#334155", "marginBottom": "15px"}
                        ),
                        dbc.Row([
                            dbc.Col([
                                dcc.Upload(
                                    id='upload-data-plan',
                                    children=html.Div([
                                        'Kéo thả hoặc ',
                                        html.A('Chọn file Excel kế hoạch (.xlsx, .xls)')
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '60px',
                                        'lineHeight': '60px',
                                        'borderWidth': '1.5px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '8px',
                                        'textAlign': 'center',
                                        'borderColor': '#0F766E',
                                        'cursor': 'pointer',
                                        'backgroundColor': '#F0FDFA',
                                        'color': '#0F766E'
                                    },
                                    multiple=False
                                )
                            ], md=12)
                        ]),
                        # File info
                        html.Div(id='selected-file-info-plan', style={'marginTop': '15px'}),
                        # Button confirm
                        dbc.Button(
                            "🎯 Xác nhận nạp kế hoạch doanh thu",
                            id="btn-confirm-upload-plan",
                            color="info",
                            className="w-100",
                            style={'marginTop': '15px', 'display': 'none'}
                        ),
                        # Status message
                        dbc.Spinner(
                            html.Div(id='upload-status-message-plan', style={'marginTop': '15px'}),
                            color="info",
                            type="border"
                        )
                    ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #CCFBF1'})
                ], md=12)
            ])
        ], style={"marginTop": "20px"}),
        
        # Khu vực mới ở cuối trang: Quản lý Danh mục Dịch vụ
        html.Div([
            html.Hr(style={"margin": "30px 0"}),
            html.Div("📋 Quản lý Danh mục Dịch vụ", className="section-header"),

            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.P("Nạp file mapping sản phẩm dịch vụ mới (định dạng CSV) và bấm Đồng bộ để cập nhật hệ thống.", style={"fontSize": "14px", "color": "#475569"}),
                        dcc.Upload(
                            id="upload-csv-mapping",
                            children=html.Div([
                                "Kéo thả hoặc ",
                                html.A("Chọn file CSV cấu trúc mới (.csv)")
                            ]),
                            style={
                                "width": "100%",
                                "height": "80px",
                                "lineHeight": "80px",
                                "borderWidth": "1.5px",
                                "borderStyle": "dashed",
                                "borderRadius": "8px",
                                "textAlign": "center",
                                "borderColor": "#94A3B8",
                                "cursor": "pointer",
                                "backgroundColor": "#F8FAFC"
                            },
                            multiple=False
                        ),
                        html.Div(id="csv-file-info", style={"marginTop": "10px"}),
                        dbc.Button(
                            "🔄 Đồng bộ danh mục Dịch vụ",
                            id="btn-sync-mapping",
                            color="warning",
                            className="w-100",
                            style={"marginTop": "15px"},
                            disabled=True
                        ),
                        dbc.Spinner(
                            html.Div(id="sync-status-message", style={"marginTop": "15px"}),
                            color="warning"
                        )
                    ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0'})
                ], md=12)
            ])
        ], style={"marginTop": "20px"})
    ])
