# -*- coding: utf-8 -*-
"""
Callbacks xử lý phân tích và hiển thị danh sách Cảnh báo sụt giảm doanh thu (Alerts).
Ngưỡng sụt giảm: Vàng 15%, Đỏ 30%.
"""

import dash
from dash import Output, Input, html
import sys
import pandas as pd
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from callbacks.utils import resolve_filters_and_query, format_revenue
import dash_bootstrap_components as dbc

def register_alerts_callbacks(app):
    """
    Đăng ký callback phân tích cảnh báo doanh thu.
    """
    
    @app.callback(
        Output("alerts-list-container", "children"),
        [Input("tabs-navigation", "value"),
         # Bộ lọc thời gian & địa lý từ Sidebar
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-spdv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_alerts_list(tab_val, year, period, start_date, end_date, week_idx, month_val,
                           nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ chạy khi đang ở Tab Cảnh báo
        if tab_val != "tab-alerts":
            return dash.no_update
            
        alerts = []
        
        # Thiết lập cấu hình query mặc định: so sánh kỳ trước
        compare_prev = True
        compare_mode = "prev_period"
        
        # ----------------------------------------------------------------------
        # PHÂN TÍCH 1: CẢNH BÁO THEO CỤM ĐỊA LÝ
        # ----------------------------------------------------------------------
        _, _, _, df_cum = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='cum', group_by_secondary=None, compare_prev=compare_prev
        )
        
        if not df_cum.empty and 'cuoc_tt_tong_prev' in df_cum.columns:
            for _, row in df_cum.iterrows():
                cum_name = row.get('cum', 'Không rõ Cụm')
                # Bỏ qua dòng tổng cộng hoặc None
                if pd.isna(cum_name) or cum_name == 'Tất cả':
                    continue
                
                val_now = row.get('cuoc_tt_tong', 0) or 0
                val_prev = row.get('cuoc_tt_tong_prev', 0) or 0
                
                # Chỉ cảnh báo khi kỳ trước có doanh thu > 5 triệu đồng để tránh cảnh báo rác
                if val_prev >= 5_000_000 and val_now < val_prev:
                    pct_change = ((val_now - val_prev) / val_prev) * 100.0
                    abs_change = val_prev - val_now
                    
                    # Ngưỡng sụt giảm: Vàng 15%, Đỏ 30%
                    if pct_change <= -30.0:
                        alerts.append({
                            "level": "red",
                            "category": "Cụm Địa Lý (Nghiêm trọng)",
                            "target": cum_name,
                            "msg": f"Doanh thu Cụm {cum_name} sụt giảm mạnh {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với kỳ trước.",
                            "detail": f"Doanh thu kỳ này đạt {format_revenue(val_now)} (kỳ trước đạt {format_revenue(val_prev)})."
                        })
                    elif pct_change <= -15.0:
                        alerts.append({
                            "level": "yellow",
                            "category": "Cụm Địa Lý",
                            "target": cum_name,
                            "msg": f"Doanh thu Cụm {cum_name} giảm {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với kỳ trước.",
                            "detail": f"Doanh thu kỳ này đạt {format_revenue(val_now)} (kỳ trước đạt {format_revenue(val_prev)})."
                        })
                        
        # ----------------------------------------------------------------------
        # PHÂN TÍCH 2: CẢNH BÁO THEO NHÓM DỊCH VỤ CHÍNH
        # ----------------------------------------------------------------------
        _, _, _, df_dv = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='nhom_dv', group_by_secondary=None, compare_prev=compare_prev
        )
        
        if not df_dv.empty and 'cuoc_tt_tong_prev' in df_dv.columns:
            for _, row in df_dv.iterrows():
                nhom_name = row.get('nhom_dv', 'Dịch vụ khác')
                if pd.isna(nhom_name) or nhom_name == 'Tất cả':
                    continue
                
                val_now = row.get('cuoc_tt_tong', 0) or 0
                val_prev = row.get('cuoc_tt_tong_prev', 0) or 0
                
                # Tránh cảnh báo rác cho dịch vụ quá nhỏ
                if val_prev >= 10_000_000 and val_now < val_prev:
                    pct_change = ((val_now - val_prev) / val_prev) * 100.0
                    abs_change = val_prev - val_now
                    
                    if pct_change <= -30.0:
                        alerts.append({
                            "level": "red",
                            "category": "Nhóm Dịch Vụ (Nghiêm trọng)",
                            "target": nhom_name,
                            "msg": f"Doanh thu dịch vụ {nhom_name} sụt giảm mạnh {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với kỳ trước.",
                            "detail": f"Doanh thu đạt {format_revenue(val_now)} (kỳ trước {format_revenue(val_prev)})."
                        })
                    elif pct_change <= -15.0:
                        alerts.append({
                            "level": "yellow",
                            "category": "Nhóm Dịch Vụ",
                            "target": nhom_name,
                            "msg": f"Doanh thu dịch vụ {nhom_name} giảm {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với kỳ trước.",
                            "detail": f"Doanh thu đạt {format_revenue(val_now)} (kỳ trước {format_revenue(val_prev)})."
                        })

        # ----------------------------------------------------------------------
        # PHÂN TÍCH 3: CẢNH BÁO THEO TOP 10 KHÁCH HÀNG LỚN NHẤT
        # ----------------------------------------------------------------------
        _, _, _, df_kh = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='cms', group_by_secondary=None, compare_prev=compare_prev
        )
        
        if not df_kh.empty and 'cuoc_tt_tong_prev' in df_kh.columns:
            # Lọc bỏ khách hàng vãng lai
            df_kh_valid = df_kh[
                df_kh['cms'].notna() & 
                (~df_kh['cms'].str.startswith('VANGLAI_', na=False)) & 
                (df_kh['cms'] != '')
            ]
            # Lấy Top 10 khách hàng lớn nhất dựa trên doanh thu kỳ này
            df_top_kh = df_kh_valid.nlargest(10, 'cuoc_tt_tong')
            
            for _, row in df_top_kh.iterrows():
                kh_name = row.get('cms', 'Khách hàng ẩn danh')
                val_now = row.get('cuoc_tt_tong', 0) or 0
                val_prev = row.get('cuoc_tt_tong_prev', 0) or 0
                
                # Tránh cảnh báo khách hàng nhỏ
                if val_prev >= 3_000_000 and val_now < val_prev:
                    pct_change = ((val_now - val_prev) / val_prev) * 100.0
                    abs_change = val_prev - val_now
                    
                    if pct_change <= -30.0:
                        alerts.append({
                            "level": "red",
                            "category": "Khách Hàng Lớn (Nghiêm trọng)",
                            "target": kh_name,
                            "msg": f"Khách hàng lớn {kh_name} sụt giảm mạnh sản lượng/doanh thu {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với kỳ trước.",
                            "detail": f"Doanh thu đạt {format_revenue(val_now)} (kỳ trước {format_revenue(val_prev)})."
                        })
                    elif pct_change <= -15.0:
                        alerts.append({
                            "level": "yellow",
                            "category": "Khách Hàng Lớn",
                            "target": kh_name,
                            "msg": f"Khách hàng {kh_name} giảm chi tiêu {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với kỳ trước.",
                            "detail": f"Doanh thu đạt {format_revenue(val_now)} (kỳ trước {format_revenue(val_prev)})."
                        })
                        
        # ----------------------------------------------------------------------
        # RENDERING LIST CARDS
        # ----------------------------------------------------------------------
        if not alerts:
            return html.Div([
                html.Div("🎉 Không phát hiện điểm sụt giảm doanh thu bất thường nào vượt ngưỡng cảnh báo (>= 15%). Hệ thống đang vận hành ổn định!", 
                         style={"padding": "25px", "textAlign": "center", "color": "#16A34A", "fontWeight": "bold", "backgroundColor": "#F0FDF4", "borderRadius": "8px", "border": "1px solid #BBF7D0"})
            ])
            
        alert_components = []
        
        # Sắp xếp cảnh báo đỏ lên trước, vàng xuống sau
        alerts_sorted = sorted(alerts, key=lambda x: 0 if x["level"] == "red" else 1)
        
        for a in alerts_sorted:
            color = "danger" if a["level"] == "red" else "warning"
            icon = "🟥" if a["level"] == "red" else "🟨"
            
            alert_components.append(
                dbc.Alert([
                    html.Div([
                        html.Span(f"{icon} ", style={"fontSize": "18px", "marginRight": "8px"}),
                        html.B(f"Cảnh báo {a['category']}: ", style={"color": "#7F1D1D" if a["level"]=="red" else "#78350F"}),
                        html.Span(a["msg"], style={"fontWeight": "500"})
                    ], style={"marginBottom": "5px"}),
                    html.Div(a["detail"], style={"fontSize": "12px", "color": "#991B1B" if a["level"]=="red" else "#92400E", "marginLeft": "26px"})
                ], color=color, style={"borderLeft": f"5px solid {'#DC2626' if a['level']=='red' else '#D97706'}", "borderRadius": "6px", "marginBottom": "12px"})
            )
            
        return html.Div(alert_components)
