# -*- coding: utf-8 -*-
"""
Callbacks xử lý cập nhật dữ liệu cho các thẻ KPI trên Trang chủ Tổng quan.
"""

import sqlite3
import pandas as pd
import dash
from dash import Output, Input, html
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from config.week_calendar import get_prev_period, get_same_period_prev_year
from analytics.revenue import query_revenue
from callbacks.utils import (
    format_revenue,
    generate_svg_sparkline_src,
    resolve_filters_and_query
)

def register_kpi_callbacks(app):
    """
    Đăng ký callback cập nhật 7 thẻ KPI với ứng dụng Dash.
    """
    
    @app.callback(
        [# Card 1: Tổng Doanh thu
         Output("kpi-tong-value", "children"), Output("kpi-tong-sparkline", "children"),
         Output("kpi-tong-delta-prev", "children"), Output("kpi-tong-delta-yoy", "children"),
         # Card 2: Doanh thu BCCP
         Output("kpi-bccp-value", "children"), Output("kpi-bccp-sparkline", "children"),
         Output("kpi-bccp-delta-prev", "children"), Output("kpi-bccp-delta-yoy", "children"),
         # Output 3: Doanh thu Hành chính công
         Output("kpi-hcc-value", "children"), Output("kpi-hcc-sparkline", "children"),
         Output("kpi-hcc-delta-prev", "children"), Output("kpi-hcc-delta-yoy", "children"),
         # Card 4: Bưu chính Truyền thống
         Output("kpi-tt-value", "children"), Output("kpi-tt-sparkline", "children"),
         Output("kpi-tt-delta-prev", "children"), Output("kpi-tt-delta-yoy", "children"),
         # Card 5: Bưu chính TMĐT
         Output("kpi-tmdt-value", "children"), Output("kpi-tmdt-sparkline", "children"),
         Output("kpi-tmdt-delta-prev", "children"), Output("kpi-tmdt-delta-yoy", "children"),
         # Card 6: Bưu chính Quốc tế
         Output("kpi-qt-value", "children"), Output("kpi-qt-sparkline", "children"),
         Output("kpi-qt-delta-prev", "children"), Output("kpi-qt-delta-yoy", "children"),
         # Card 7: Khách hàng
         Output("kpi-kh-value", "children"), Output("kpi-kh-sparkline", "children"),
         Output("kpi-kh-delta-prev", "children"), Output("kpi-kh-delta-yoy", "children")],
        [Input("tabs-navigation", "value"),
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-compare-mode", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-spdv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_kpi_cards(tab_val, year, period, start_date, end_date, week_idx, month_val, compare_mode,
                         nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ xử lý khi đang ở Tab Tổng quan KPI
        if tab_val != "tab-kpi":
            return [dash.no_update] * 28

        # Chuẩn hóa compare_mode từ list thành string để tương thích ngược với trang KPI cũ
        if isinstance(compare_mode, (list, tuple)):
            has_prev = 'prev_period' in compare_mode
            has_yoy = 'yoy' in compare_mode
            if has_prev and has_yoy:
                compare_mode = 'both'
            elif has_prev:
                compare_mode = 'prev_period'
            elif has_yoy:
                compare_mode = 'yoy'
            else:
                compare_mode = 'none'

        # 1. Truy vấn dữ liệu kỳ hiện tại
        date_from, date_to, date_column, df_cur = resolve_filters_and_query(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary='nhom_dv', compare_prev=False
        )
        
        # 2. Truy vấn kỳ trước (nếu chọn)
        prev_from, prev_to = None, None
        df_prev = pd.DataFrame()
        if compare_mode in ('prev_period', 'both'):
            prev_from, prev_to = get_prev_period(period, date_from, date_to)
            
            # Kết nối DB để thực hiện query riêng cho kỳ trước
            conn_tmp = sqlite3.connect(str(DB_PATH))
            try:
                cum_f = None if cum == "Tất cả" else cum
                bdx_f = None if bdx == "Tất cả" else bdx
                bc_f = None if buu_cuc == "Tất cả" else buu_cuc
                hd_f = None if hop_dong == "Tất cả" else hop_dong
                df_prev = query_revenue(
                    conn=conn_tmp, date_from=prev_from, date_to=prev_to, date_column=date_column,
                    nhom_dv=nhom_dv, dich_vu=spdv, cum=cum_f, bdx=bdx_f, buu_cuc=bc_f, loai_kh=loai_kh, hop_dong=hd_f,
                    group_by_primary='nhom_dv', compare_prev=False
                )
            except Exception as e:
                print(f"Error querying prev period KPI: {e}")
            finally:
                conn_tmp.close()

        # 3. Truy vấn cùng kỳ năm trước (nếu chọn)
        yoy_from, yoy_to = None, None
        df_yoy = pd.DataFrame()
        if compare_mode in ('yoy', 'both'):
            yoy_from, yoy_to = get_same_period_prev_year(period, date_from, date_to)
            yoy_year = year - 1 if year else None
            
            # Kết nối DB để thực hiện query riêng cho cùng kỳ năm trước
            conn_tmp = sqlite3.connect(str(DB_PATH))
            try:
                cum_f = None if cum == "Tất cả" else cum
                bdx_f = None if bdx == "Tất cả" else bdx
                bc_f = None if buu_cuc == "Tất cả" else buu_cuc
                hd_f = None if hop_dong == "Tất cả" else hop_dong
                df_yoy = query_revenue(
                    conn=conn_tmp, date_from=yoy_from, date_to=yoy_to, date_column=date_column,
                    nhom_dv=nhom_dv, dich_vu=spdv, cum=cum_f, bdx=bdx_f, buu_cuc=bc_f, loai_kh=loai_kh, hop_dong=hd_f,
                    group_by_primary='nhom_dv', compare_prev=False, nam=yoy_year
                )
            except Exception as e:
                print(f"Error querying YoY period KPI: {e}")
            finally:
                conn_tmp.close()

        # 4. Truy vấn xu hướng (Trend) để vẽ sparklines
        conn_tmp = sqlite3.connect(str(DB_PATH))
        try:
            cum_f = None if cum == "Tất cả" else cum
            bdx_f = None if bdx == "Tất cả" else bdx
            bc_f = None if buu_cuc == "Tất cả" else buu_cuc
            hd_f = None if hop_dong == "Tất cả" else hop_dong
            df_trend = query_revenue(
                conn=conn_tmp, date_from=date_from, date_to=date_to, date_column=date_column,
                nhom_dv=nhom_dv, dich_vu=spdv, cum=cum_f, bdx=bdx_f, buu_cuc=bc_f, loai_kh=loai_kh, hop_dong=hd_f,
                group_by_primary='ngay', group_by_secondary='nhom_dv', compare_prev=False
            )
        except Exception as e:
            print(f"Error querying trend KPI: {e}")
            df_trend = pd.DataFrame()
        finally:
            conn_tmp.close()

        # Helper lấy doanh thu theo nhóm dịch vụ
        def get_revenue_by_nhom(df, nhom_name):
            if df.empty or 'nhom_dv' not in df.columns:
                return 0.0
            filtered = df[df['nhom_dv'] == nhom_name]
            return filtered['cuoc_tt_tong'].sum() if not filtered.empty else 0.0
            
        # Helper lấy số khách hàng phát sinh
        def get_kh_by_nhom(df):
            if df.empty or 'so_kh' not in df.columns:
                return 0
            return int(df['so_kh'].sum())

        # Tính toán các chỉ số hiện tại, kỳ trước, yoy cho 7 thẻ
        # 1. Tổng doanh thu
        tot_cur = df_cur['cuoc_tt_tong'].sum() if not df_cur.empty else 0.0
        tot_prev = df_prev['cuoc_tt_tong'].sum() if not df_prev.empty else 0.0
        tot_yoy = df_yoy['cuoc_tt_tong'].sum() if not df_yoy.empty else 0.0
        
        # 2. Doanh thu Hành chính công
        hcc_cur = get_revenue_by_nhom(df_cur, 'Hành chính công')
        hcc_prev = get_revenue_by_nhom(df_prev, 'Hành chính công')
        hcc_yoy = get_revenue_by_nhom(df_yoy, 'Hành chính công')
        
        # 3. Doanh thu BCCP = Tổng - HCC
        bccp_cur = tot_cur - hcc_cur
        bccp_prev = tot_prev - hcc_prev
        bccp_yoy = tot_yoy - hcc_yoy
        
        # 4. Các cấu phần BCCP
        tt_cur = get_revenue_by_nhom(df_cur, 'Truyền thống')
        tt_prev = get_revenue_by_nhom(df_prev, 'Truyền thống')
        tt_yoy = get_revenue_by_nhom(df_yoy, 'Truyền thống')
        
        tmdt_cur = get_revenue_by_nhom(df_cur, 'TMĐT')
        tmdt_prev = get_revenue_by_nhom(df_prev, 'TMĐT')
        tmdt_yoy = get_revenue_by_nhom(df_yoy, 'TMĐT')
        
        qt_cur = get_revenue_by_nhom(df_cur, 'Quốc tế')
        qt_prev = get_revenue_by_nhom(df_prev, 'Quốc tế')
        qt_yoy = get_revenue_by_nhom(df_yoy, 'Quốc tế')
        
        # 5. Số khách hàng phát sinh
        kh_cur = get_kh_by_nhom(df_cur)
        kh_prev = get_kh_by_nhom(df_prev)
        kh_yoy = get_kh_by_nhom(df_yoy)

        # Lấy chuỗi dữ liệu trend cho sparklines
        def get_trend_series(df_tr, nhom_name=None, metric='cuoc_tt_tong'):
            if df_tr.empty or 'ngay' not in df_tr.columns:
                return []
            if nhom_name:
                filtered = df_tr[df_tr['nhom_dv'] == nhom_name]
            else:
                filtered = df_tr.groupby('ngay').sum(numeric_only=True).reset_index()
            if filtered.empty:
                return []
            return filtered.sort_values('ngay')[metric].tolist()

        y_tot = get_trend_series(df_trend)
        y_bccp = get_trend_series(df_trend[df_trend['nhom_dv'] != 'Hành chính công']) if not df_trend.empty and 'nhom_dv' in df_trend.columns else []
        y_hcc = get_trend_series(df_trend, 'Hành chính công')
        y_tt = get_trend_series(df_trend, 'Truyền thống')
        y_tmdt = get_trend_series(df_trend, 'TMĐT')
        y_qt = get_trend_series(df_trend, 'Quốc tế')
        y_kh = get_trend_series(df_trend, metric='so_kh')

        # Helper render các output cho 1 thẻ KPI
        def render_card_outputs(val_now, val_prev, val_yoy, y_series, color, is_count_card=False):
            # Định dạng hiển thị giá trị số hiện tại
            display_now = f"{val_now:,}" if is_count_card else format_revenue(val_now)
            display_prev = f"{val_prev:,}" if is_count_card else format_revenue(val_prev)
            display_yoy = f"{val_yoy:,}" if is_count_card else format_revenue(val_yoy)
            
            # Sparkline SVG
            spark_svg = html.Img(src=generate_svg_sparkline_src(y_series, color), width="100%", height="35px", style={"display": "block", "margin": "2px 0"})
            
            # Phần trăm thay đổi kỳ trước
            delta_p_div = None
            if (compare_mode in ('prev_period', 'both')) and val_prev != 0:
                pct_p = (val_now - val_prev) * 100.0 / val_prev
                badge_class = "delta-badge positive" if pct_p >= 0 else "delta-badge negative"
                icon_p = "▲" if pct_p >= 0 else "▼"
                delta_p_div = html.Div([
                    html.Span(f"{icon_p} {abs(pct_p):.1f}%", className=badge_class),
                    html.Span(f"so với kỳ trước ({display_prev})", className="delta-label")
                ])
                
            # Phần trăm thay đổi YoY
            delta_y_div = None
            if (compare_mode in ('yoy', 'both')) and val_yoy != 0:
                pct_y = (val_now - val_yoy) * 100.0 / val_yoy
                badge_class = "delta-badge positive" if pct_y >= 0 else "delta-badge negative"
                icon_y = "▲" if pct_y >= 0 else "▼"
                delta_y_div = html.Div([
                    html.Span(f"{icon_y} {abs(pct_y):.1f}%", className=badge_class),
                    html.Span(f"so với cùng kỳ năm trước ({display_yoy})", className="delta-label")
                ])
                
            return display_now, spark_svg, delta_p_div, delta_y_div

        # Render output cho từng thẻ KPI
        tong_n, tong_s, tong_p, tong_y = render_card_outputs(tot_cur, tot_prev, tot_yoy, y_tot, "#3B82F6")
        bccp_n, bccp_s, bccp_p, bccp_y = render_card_outputs(bccp_cur, bccp_prev, bccp_yoy, y_bccp, "#10B981")
        hcc_n, hcc_s, hcc_p, hcc_y = render_card_outputs(hcc_cur, hcc_prev, hcc_yoy, y_hcc, "#F59E0B")
        tt_n, tt_s, tt_p, tt_y = render_card_outputs(tt_cur, tt_prev, tt_yoy, y_tt, "#64748B")
        tmdt_n, tmdt_s, tmdt_p, tmdt_y = render_card_outputs(tmdt_cur, tmdt_prev, tmdt_yoy, y_tmdt, "#8B5CF6")
        qt_n, qt_s, qt_p, qt_y = render_card_outputs(qt_cur, qt_prev, qt_yoy, y_qt, "#0EA5E9")
        kh_n, kh_s, kh_p, kh_y = render_card_outputs(kh_cur, kh_prev, kh_yoy, y_kh, "#14B8A6", is_count_card=True)
        
        return [
            tong_n, tong_s, tong_p, tong_y,
            bccp_n, bccp_s, bccp_p, bccp_y,
            hcc_n, hcc_s, hcc_p, hcc_y,
            tt_n, tt_s, tt_p, tt_y,
            tmdt_n, tmdt_s, tmdt_p, tmdt_y,
            qt_n, qt_s, qt_p, qt_y,
            kh_n, kh_s, kh_p, kh_y
        ]
