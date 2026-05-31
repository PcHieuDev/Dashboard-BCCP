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
            # Cột bên trái: Drag-drop File Excel để Import
            dbc.Col([
                html.Div([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Kéo thả hoặc ',
                            html.A('Chọn file Excel (.xlsx)')
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
                    html.Div(id='upload-status-message', style={'marginTop': '15px'})
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0'})
            ], md=6),
            
            # Cột bên phải: Hiển thị bảng 10 giao dịch import lịch sử gần nhất
            dbc.Col([
                html.Div([
                    html.H4("📜 Lịch sử nạp dữ liệu", style={'marginTop': 0, 'color': '#1E293B', 'fontSize': '16px', 'fontWeight': 'bold'}),
                    dbc.Spinner(html.Div(id='import-history-container'))
                ], style={'padding': '20px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'minHeight': '180px'})
            ], md=6)
        ])
    ])
