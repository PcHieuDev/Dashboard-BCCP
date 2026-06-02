# -*- coding: utf-8 -*-
"""
Callbacks xử lý truy vấn dữ liệu và vẽ các biểu đồ Plotly (Line, Pie, Bar).
"""

import dash
from dash import Output, Input
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from callbacks.utils import resolve_filters_and_query

def register_charts_callbacks(app):
    """
    Đăng ký các callback vẽ biểu đồ trực quan với ứng dụng Dash.
    """
    
    # 1. Callback vẽ biểu đồ xu hướng doanh thu theo thời gian (Line Chart)
    @app.callback(
        Output("chart-revenue-trend", "figure"),
        [Input("tabs-navigation", "value"),
         # Bộ lọc từ Sidebar
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_trend_chart(tab_val, year, period, start_date, end_date, week_idx, month_val,
                           nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        if tab_val != "tab-charts" or tab_val is None:
            return dash.no_update
        spdv = None
            
        # Truy vấn dữ liệu group by theo 'ngay' để vẽ xu hướng thời gian
        _, _, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, "prev_period",
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='ngay', compare_prev=False
        )
        
        fig = go.Figure()
        if df.empty or 'ngay' not in df.columns:
            fig.update_layout(title="Không có dữ liệu hiển thị")
            return fig
            
        # Sắp xếp theo ngày tăng dần
        df_sorted = df.sort_values('ngay')
        
        # Format hiển thị ngày trên trục X đẹp hơn
        df_sorted['ngay_display'] = df_sorted['ngay'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m') if pd.notna(x) else '')
        
        fig.add_trace(go.Scatter(
            x=df_sorted['ngay_display'],
            y=df_sorted['cuoc_tt_tong'],
            mode='lines+markers',
            name='Doanh thu TT',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=6, color='#1D4ED8'),
            hovertemplate="Ngày %{x}: %{y:,.0f} đ<extra></extra>"
        ))
        
        fig.update_layout(
            margin=dict(l=50, r=20, t=15, b=30),
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat=",.0f")
        )
        return fig

    # 2. Callback vẽ biểu đồ cơ cấu doanh thu theo Nhóm dịch vụ (Pie Chart)
    @app.callback(
        Output("chart-service-pie", "figure"),
        [Input("tabs-navigation", "value"),
         # Bộ lọc từ Sidebar
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_pie_chart(tab_val, year, period, start_date, end_date, week_idx, month_val,
                         nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        if tab_val != "tab-charts" or tab_val is None:
            return dash.no_update
        spdv = None
            
        # Truy vấn dữ liệu group by theo 'nhom_dv'
        _, _, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, "prev_period",
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='nhom_dv', compare_prev=False
        )
        
        fig = go.Figure()
        if df.empty or 'nhom_dv' not in df.columns:
            return fig
            
        # Bảng màu hài hòa cho các nhóm dịch vụ chính
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#64748B']
        
        fig.add_trace(go.Pie(
            labels=df['nhom_dv'],
            values=df['cuoc_tt_tong'],
            hole=.4,
            marker=dict(colors=colors),
            textinfo='percent+label',
            hovertemplate="Nhóm %{label}: %{value:,.0f} đ (%{percent})<extra></extra>"
        ))
        
        fig.update_layout(
            margin=dict(l=30, r=30, t=15, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        return fig

    # 3. Callback vẽ biểu đồ so sánh doanh thu giữa các Cụm (Horizontal Bar Chart)
    @app.callback(
        Output("chart-cluster-bar", "figure"),
        [Input("tabs-navigation", "value"),
         # Bộ lọc từ Sidebar
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_bar_chart(tab_val, year, period, start_date, end_date, week_idx, month_val,
                         nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        if tab_val != "tab-charts" or tab_val is None:
            return dash.no_update
        spdv = None
            
        # Truy vấn dữ liệu group by theo 'cum'
        _, _, _, df = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, "prev_period",
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='cum', compare_prev=False
        )
        
        fig = go.Figure()
        if df.empty or 'cum' not in df.columns:
            return fig
            
        # Lọc bỏ 'Chưa phân loại' để biểu đồ trực quan hơn, sắp xếp theo doanh thu tăng dần để vẽ từ dưới lên
        df_filtered = df[df['cum'] != 'Chưa phân loại'].sort_values('cuoc_tt_tong', ascending=True)
        
        fig.add_trace(go.Bar(
            x=df_filtered['cuoc_tt_tong'],
            y=df_filtered['cum'],
            orientation='h',
            marker_color='#10B981',
            hovertemplate="Cụm %{y}: %{x:,.0f} đ<extra></extra>"
        ))
        
        fig.update_layout(
            margin=dict(l=100, r=20, t=15, b=30),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=False)
        )
        return fig
