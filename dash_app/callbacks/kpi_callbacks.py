# -*- coding: utf-8 -*-
"""
Callbacks xử lý cập nhật dữ liệu cho các thẻ KPI trên Trang chủ Tổng quan.
"""

import sqlite3
import pandas as pd
import dash
from dash import Output, Input, State, html
import plotly.graph_objects as go

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

def _get_phbc_revenue(db_path, year, month):
    """Query doanh thu PHBC từ bảng transactions_phbc. Trả về 0 nếu bảng chưa tồn tại."""
    try:
        if not year or not month: return 0.0
        conn = sqlite3.connect(str(db_path))
        thang = f"T{month:02d}"
        df = pd.read_sql_query(
            "SELECT SUM(doanh_thu) as dt FROM transactions_phbc WHERE nam_du_lieu=? AND thang_du_lieu=?",
            conn, params=[year, thang]
        )
        conn.close()
        return float(df.iloc[0]['dt'] or 0)
    except Exception:
        return 0.0

def register_kpi_callbacks(app):
    """
    Đăng ký callback cập nhật 7 thẻ KPI với ứng dụng Dash.
    """
    

    # ── Callback: Cards chi tiết cấu phần BCCP + Khách hàng + Biểu đồ ──────────
    @app.callback(
        [# Card: Phát hành báo chí
         Output("kpi-phbc-value", "children"), Output("kpi-phbc-sparkline", "children"),
         Output("kpi-phbc-delta-prev", "children"), Output("kpi-phbc-delta-yoy", "children"),
         # Card: Bưu chính Truyền thống
         Output("kpi-tt-value", "children"), Output("kpi-tt-sparkline", "children"),
         Output("kpi-tt-delta-prev", "children"), Output("kpi-tt-delta-yoy", "children"),
         # Card: Bưu chính TMĐT
         Output("kpi-tmdt-value", "children"), Output("kpi-tmdt-sparkline", "children"),
         Output("kpi-tmdt-delta-prev", "children"), Output("kpi-tmdt-delta-yoy", "children"),
         # Card: Bưu chính Quốc tế
         Output("kpi-qt-value", "children"), Output("kpi-qt-sparkline", "children"),
         Output("kpi-qt-delta-prev", "children"), Output("kpi-qt-delta-yoy", "children"),
         # Card: Khách hàng
         Output("kpi-kh-value", "children"), Output("kpi-kh-sparkline", "children"),
         Output("kpi-kh-delta-prev", "children"), Output("kpi-kh-delta-yoy", "children"),
         # 3 Biểu đồ trực quan
         Output("chart-service-pie", "figure"),
         Output("chart-revenue-trend", "figure"),
         Output("chart-cluster-bar", "figure")],

        [Input("btn-apply-filter", "n_clicks"),
         Input("tabs-navigation", "value")],
        [State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-compare-mode", "value"),
         State("sidebar-nhom-dv", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "value"),
         State("sidebar-hop-dong", "value")]
    )
    def update_kpi_cards(n_clicks, tab_val, year, period, start_date, end_date, week_idx, month_val, compare_mode,
                         nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ xử lý khi đang ở Tab Tổng quan KPI
        if tab_val != "tab-kpi" or tab_val is None:
            return [dash.no_update] * 23

        spdv = None

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
        
        # 2. Doanh thu PHBC
        pyear = year - 1 if year and month_val == 1 else year
        pmonth = 12 if month_val == 1 else (month_val - 1 if month_val else None)
        yoy_year = year - 1 if year else None
        
        phbc_cur = _get_phbc_revenue(DB_PATH, year, month_val)
        phbc_prev = _get_phbc_revenue(DB_PATH, pyear, pmonth)
        phbc_yoy = _get_phbc_revenue(DB_PATH, yoy_year, month_val)
        
        # 3. Doanh thu BCCP = Tổng
        bccp_cur = tot_cur
        bccp_prev = tot_prev
        bccp_yoy = tot_yoy
        
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
        y_bccp = get_trend_series(df_trend)
        y_phbc = []
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

        # Render output cho các thẻ KPI chi tiết
        phbc_n, phbc_s, phbc_p, phbc_y = render_card_outputs(phbc_cur, phbc_prev, phbc_yoy, y_phbc, "#F97316")
        tt_n, tt_s, tt_p, tt_y     = render_card_outputs(tt_cur,   tt_prev,   tt_yoy,   y_tt,   "#64748B")
        tmdt_n, tmdt_s, tmdt_p, tmdt_y = render_card_outputs(tmdt_cur, tmdt_prev, tmdt_yoy, y_tmdt, "#8B5CF6")
        qt_n, qt_s, qt_p, qt_y     = render_card_outputs(qt_cur,   qt_prev,   qt_yoy,   y_qt,   "#0EA5E9")
        kh_n, kh_s, kh_p, kh_y    = render_card_outputs(kh_cur,   kh_prev,   kh_yoy,   y_kh,   "#14B8A6", is_count_card=True)

        # ── Vẽ biểu đồ 1: Cơ cấu dịch vụ (Donut Chart) ──────────────────
        fig_pie = go.Figure()
        if not df_cur.empty and 'nhom_dv' in df_cur.columns:
            pie_colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#64748B']
            fig_pie.add_trace(go.Pie(
                labels=df_cur['nhom_dv'],
                values=df_cur['cuoc_tt_tong'],
                hole=.4,
                marker=dict(colors=pie_colors),
                textinfo='percent+label',
                hovertemplate="Nhóm %{label}: %{value:,.0f} đ (%{percent})<extra></extra>"
            ))
            fig_pie.update_layout(
                margin=dict(l=20, r=20, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
        else:
            fig_pie.update_layout(title="Không có dữ liệu cơ cấu")

        # ── Vẽ biểu đồ 2: Xu hướng theo ngày (Line Chart) ───────────────
        fig_trend = go.Figure()
        if not df_trend.empty and 'ngay' in df_trend.columns:
            df_trend_daily = df_trend.groupby('ngay')['cuoc_tt_tong'].sum().reset_index()
            df_sorted = df_trend_daily.sort_values('ngay')
            df_sorted['ngay_display'] = df_sorted['ngay'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m') if pd.notna(x) else '')
            
            fig_trend.add_trace(go.Scatter(
                x=df_sorted['ngay_display'],
                y=df_sorted['cuoc_tt_tong'],
                mode='lines+markers',
                name='Doanh thu TT',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=6, color='#1D4ED8'),
                hovertemplate="Ngày %{x}: %{y:,.0f} đ<extra></extra>"
            ))
            fig_trend.update_layout(
                margin=dict(l=40, r=20, t=15, b=20),
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat=",.0f")
            )
        else:
            fig_trend.update_layout(title="Không có dữ liệu xu hướng")

        # ── Vẽ biểu đồ 3: So sánh doanh thu giữa các Cụm (Bar Chart) ─────
        # Truy vấn riêng group by theo Cụm địa lý
        conn_tmp = sqlite3.connect(str(DB_PATH))
        try:
            cum_f = None if cum == "Tất cả" else cum
            bdx_f = None if bdx == "Tất cả" else bdx
            bc_f = None if buu_cuc == "Tất cả" else buu_cuc
            hd_f = None if hop_dong == "Tất cả" else hop_dong
            df_cluster = query_revenue(
                conn=conn_tmp, date_from=date_from, date_to=date_to, date_column=date_column,
                nhom_dv=nhom_dv, dich_vu=spdv, cum=cum_f, bdx=bdx_f, buu_cuc=bc_f, loai_kh=loai_kh, hop_dong=hd_f,
                group_by_primary='cum', compare_prev=False
            )
        except Exception as e:
            print(f"Error querying cluster KPI: {e}")
            df_cluster = pd.DataFrame()
        finally:
            conn_tmp.close()

        fig_bar = go.Figure()
        if not df_cluster.empty and 'cum' in df_cluster.columns:
            df_bar_filtered = df_cluster[df_cluster['cum'] != 'Chưa phân loại'].sort_values('cuoc_tt_tong', ascending=True)
            fig_bar.add_trace(go.Bar(
                x=df_bar_filtered['cuoc_tt_tong'],
                y=df_bar_filtered['cum'],
                orientation='h',
                marker_color='#10B981',
                hovertemplate="Cụm %{y}: %{x:,.0f} đ<extra></extra>"
            ))
            fig_bar.update_layout(
                margin=dict(l=100, r=20, t=15, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                yaxis=dict(showgrid=False)
            )
        else:
            fig_bar.update_layout(title="Không có dữ liệu so sánh Cụm")

        return [
            phbc_n, phbc_s, phbc_p, phbc_y,
            tt_n,   tt_s,   tt_p,   tt_y,
            tmdt_n, tmdt_s, tmdt_p, tmdt_y,
            qt_n,   qt_s,   qt_p,   qt_y,
            kh_n,   kh_s,   kh_p,   kh_y,
            fig_pie, fig_trend, fig_bar
        ]

