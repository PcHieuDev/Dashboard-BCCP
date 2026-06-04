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
    resolve_filters_and_query,
    get_bccp_week_number
)
from analytics.retention_metrics import get_retention_stats

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

def get_bccp_plan(db_path, year, month, cum=None, bdx=None, buu_cuc=None):
    """Lấy kế hoạch doanh thu của nhóm BCCP dựa theo thời gian và bộ lọc địa lý"""
    if not db_path.exists():
        return 0.0
    sql = """
        SELECT SUM(p.ke_hoach_doanh_thu)
        FROM plans p
        INNER JOIN dim_buucuc b ON p.ma_buu_cuc = b.ma_bc
        WHERE p.nam = :nam AND p.thang = :thang AND p.nhom_dich_vu = 'BCCP'
    """
    params = {"nam": year, "thang": month}
    if cum and cum != "Tất cả":
        sql += " AND b.ten_cum = :cum"
        params["cum"] = cum
    if bdx and bdx != "Tất cả":
        sql += " AND b.ten_bdx = :bdx"
        params["bdx"] = bdx
    if buu_cuc and buu_cuc != "Tất cả":
        sql += " AND p.ma_buu_cuc = :buu_cuc"
        params["buu_cuc"] = buu_cuc
        
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0.0
    except Exception as e:
        print(f"Error querying BCCP plan: {e}")
        return 0.0
    finally:
        conn.close()

def get_new_customers_metrics(db_path, year, month, cum=None, bdx=None, buu_cuc=None):
    """Lấy số lượng và tổng doanh thu của KHM từ bảng new_customers"""
    if not db_path.exists():
        return 0, 0.0, 0, 0.0
        
    sql = """
        SELECT COUNT(cms), SUM(tong_doanh_thu)
        FROM new_customers
        WHERE nam = :nam AND thang = :thang
    """
    params = {"nam": year, "thang": month}
    
    if cum and cum != "Tất cả":
        sql += " AND ten_cum = :cum"
        params["cum"] = cum
    if bdx and bdx != "Tất cả":
        sql += " AND ma_bdx = :bdx"
        params["bdx"] = bdx
    if buu_cuc and buu_cuc != "Tất cả":
        sql += " AND buu_cuc = :buu_cuc"
        params["buu_cuc"] = buu_cuc
        
    # Tính tháng trước
    prev_year = year
    prev_month = month - 1
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1
        
    params_prev = {"nam": prev_year, "thang": prev_month}
    sql_prev = """
        SELECT COUNT(cms), SUM(tong_doanh_thu)
        FROM new_customers
        WHERE nam = :nam AND thang = :thang
    """
    if cum and cum != "Tất cả":
        sql_prev += " AND ten_cum = :cum"
        params_prev["cum"] = cum
    if bdx and bdx != "Tất cả":
        sql_prev += " AND ma_bdx = :bdx"
        params_prev["bdx"] = bdx
    if buu_cuc and buu_cuc != "Tất cả":
        sql_prev += " AND buu_cuc = :buu_cuc"
        params_prev["buu_cuc"] = buu_cuc

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        r = cursor.fetchone()
        curr_count = r[0] if r and r[0] is not None else 0
        curr_rev = r[1] if r and r[1] is not None else 0.0
        
        cursor.execute(sql_prev, params_prev)
        r_prev = cursor.fetchone()
        prev_count = r_prev[0] if r_prev and r_prev[0] is not None else 0
        prev_rev = r_prev[1] if r_prev and r_prev[1] is not None else 0.0
        
        return curr_count, curr_rev, prev_count, prev_rev
    except Exception as e:
        print(f"Error getting new customer metrics: {e}")
        return 0, 0.0, 0, 0.0
    finally:
        conn.close()


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
         # Card: Sản lượng tổng
         Output("kpi-sl-value", "children"), Output("kpi-sl-sparkline", "children"),
         Output("kpi-sl-delta-prev", "children"), Output("kpi-sl-delta-yoy", "children"),
         # Card: % Kế hoạch
         Output("kpi-plan-value", "children"), Output("kpi-plan-subtext", "children"),
         # Customer Health row
         Output("health-gauge-retention", "figure"),
         Output("health-khm-card", "children"),
         Output("health-vanglai-card", "children"),
         # 4 Biểu đồ trực quan (Pie DV, Pie KH, Line trend, Bar Cụm)
         Output("chart-service-pie", "figure"),
         Output("chart-customer-pie", "figure"),
         Output("chart-revenue-trend", "figure"),
         Output("chart-cluster-bar", "figure"),
         # Top 10 CMS Table
         Output("top-cms-table-container", "children")],

        [Input("btn-apply-filter", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-compare-mode", "value"),
         State("sidebar-nhom-dv", "data"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "data"),
         State("sidebar-hop-dong", "data")],
        prevent_initial_call=True
    )
    def update_kpi_cards(n_clicks, tab_val, year, period, start_date, end_date, week_idx, month_val, compare_mode,
                         nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ xử lý khi đang ở Tab Tổng quan KPI
        if tab_val != "tab-kpi" or tab_val is None:
            return [dash.no_update] * 35

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

        # Tính toán các chỉ số hiện tại, kỳ trước, yoy cho các thẻ
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

        # 6. Sản lượng tổng
        sl_cur = df_cur['san_luong'].sum() if not df_cur.empty else 0.0
        sl_prev = df_prev['san_luong'].sum() if not df_prev.empty else 0.0
        sl_yoy = df_yoy['san_luong'].sum() if not df_yoy.empty else 0.0

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
        y_sl = get_trend_series(df_trend, metric='san_luong')

        # Helper render các output cho 1 thẻ KPI
        def render_card_outputs(val_now, val_prev, val_yoy, y_series, color, is_count_card=False):
            display_now = f"{val_now:,.0f}" if is_count_card else format_revenue(val_now)
            display_prev = f"{val_prev:,.0f}" if is_count_card else format_revenue(val_prev)
            display_yoy = f"{val_yoy:,.0f}" if is_count_card else format_revenue(val_yoy)
            
            spark_svg = html.Img(src=generate_svg_sparkline_src(y_series, color), width="100%", height="35px", style={"display": "block", "margin": "2px 0"})
            
            delta_p_div = None
            if (compare_mode in ('prev_period', 'both')) and val_prev != 0:
                pct_p = (val_now - val_prev) * 100.0 / val_prev
                badge_class = "delta-badge positive" if pct_p >= 0 else "delta-badge negative"
                icon_p = "▲" if pct_p >= 0 else "▼"
                delta_p_div = html.Div([
                    html.Span(f"{icon_p} {abs(pct_p):.1f}%", className=badge_class),
                    html.Span(f"so với kỳ trước ({display_prev})", className="delta-label")
                ])
                
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
        sl_n, sl_s, sl_p, sl_y    = render_card_outputs(sl_cur,   sl_prev,   sl_yoy,   y_sl,   "#2196F3", is_count_card=True)

        # 🎯 Tính % Hoàn thành kế hoạch
        target_year = year if year else date_from.year
        target_month = month_val if month_val else date_from.month
        plan_val = get_bccp_plan(DB_PATH, target_year, target_month, cum, bdx, buu_cuc)
        
        if plan_val > 0:
            plan_rate = (bccp_cur * 100.0 / plan_val)
            plan_val_str = f"{plan_rate:.1f}%"
            plan_subtext = f"Kế hoạch tháng: {format_revenue(plan_val)}"
        else:
            plan_val_str = "— %"
            plan_subtext = "🎯 Chưa giao kế hoạch"

        # 🏥 Tính sức khỏe khách hàng: Retention Rate
        # Tính tháng trước
        y_prev, m_prev = pyear, pmonth
        try:
            ret_stats = get_retention_stats(str(DB_PATH), target_year, target_month, cum, bdx)
            retention_rate = ret_stats['retention_rate_sl']
            
            ret_stats_prev = get_retention_stats(str(DB_PATH), y_prev, m_prev, cum, bdx)
            prev_retention_rate = ret_stats_prev['retention_rate_sl']
        except Exception as e:
            print(f"Error calculating retention rate: {e}")
            retention_rate = 0.0
            prev_retention_rate = 0.0

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=retention_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Tỷ lệ duy trì KH (%)", 'font': {'size': 14}},
            delta={'reference': prev_retention_rate, 'relative': False, 'valueformat': "+.1f%"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "#ffcccc"},
                    {'range': [50, 80], 'color': "#fff3cd"},
                    {'range': [80, 100], 'color': "#d4edda"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}
            }
        ))
        fig_gauge.update_layout(
            height=200,
            margin=dict(t=30, b=10, l=30, r=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        # 🏥 Card KHM/Tái bán phát sinh
        khm_count, khm_rev, khm_prev_count, khm_prev_rev = get_new_customers_metrics(DB_PATH, target_year, target_month, cum, bdx, buu_cuc)
        khm_count_diff = khm_count - khm_prev_count
        khm_badge = "▲" if khm_count_diff >= 0 else "▼"
        khm_badge_class = "delta-badge positive" if khm_count_diff >= 0 else "delta-badge negative"
        khm_card_children = html.Div([
            html.Div([
                html.Div("🆕 KH Mới / Tái bán phát sinh", className="kpi-title"),
                html.Span("🆕", style={"fontSize": "20px", "float": "right", "marginTop": "-24px"})
            ]),
            html.Div(f"{khm_count:,} KH", className="kpi-value"),
            html.Div([
                html.Span(f"{khm_badge} {abs(khm_count_diff)} KH", className=khm_badge_class),
                html.Span("so với tháng trước", className="delta-label")
            ], className="delta-row", style={"marginTop": "8px"}),
            html.Div(f"Tổng DT bán mới: {format_revenue(khm_rev)}", style={"marginTop": "8px", "color": "#64748B", "fontSize": "13px"})
        ], className="kpi-card", style={"height": "100%"})

        # 🏥 Card % DT Vãng lai
        conn_tmp = sqlite3.connect(str(DB_PATH))
        try:
            cum_f = None if cum == "Tất cả" else cum
            bdx_f = None if bdx == "Tất cả" else bdx
            bc_f = None if buu_cuc == "Tất cả" else buu_cuc
            hd_f = None if hop_dong == "Tất cả" else hop_dong
            df_kh_breakdown = query_revenue(
                conn=conn_tmp, date_from=date_from, date_to=date_to, date_column=date_column,
                nhom_dv=nhom_dv, dich_vu=spdv, cum=cum_f, bdx=bdx_f, buu_cuc=bc_f, loai_kh=loai_kh, hop_dong=hd_f,
                group_by_primary='loai_kh', compare_prev=False
            )
        except Exception as e:
            print(f"Error querying customer breakdown: {e}")
            df_kh_breakdown = pd.DataFrame()
        finally:
            conn_tmp.close()

        dt_vanglai = df_kh_breakdown[df_kh_breakdown['loai_kh'] == 'Vãng lai']['cuoc_tt_tong'].sum() if not df_kh_breakdown.empty else 0.0
        dt_tong = df_kh_breakdown['cuoc_tt_tong'].sum() if not df_kh_breakdown.empty else 0.0
        pct_vanglai = (dt_vanglai * 100.0 / dt_tong) if dt_tong > 0 else 0.0

        val_color = "#10B981" if pct_vanglai <= 30 else "#EF4444"
        icon_str = "✅" if pct_vanglai <= 30 else "⚠️"
        status_text = "Tỷ lệ an toàn (≤30%)" if pct_vanglai <= 30 else "Cảnh báo: Tỷ lệ cao (>30%)"
        
        vanglai_card_children = html.Div([
            html.Div([
                html.Div("📊 Tỷ lệ doanh thu Vãng lai", className="kpi-title"),
                html.Span(icon_str, style={"fontSize": "20px", "float": "right", "marginTop": "-24px"})
            ]),
            html.Div(f"{pct_vanglai:.1f}%", className="kpi-value", style={"color": val_color}),
            html.Div([
                html.Span(status_text, style={"color": val_color, "fontWeight": "bold", "fontSize": "13px"})
            ], className="delta-row", style={"marginTop": "8px"}),
            html.Div(f"DT Vãng lai: {format_revenue(dt_vanglai)}", style={"marginTop": "8px", "color": "#64748B", "fontSize": "13px"})
        ], className="kpi-card", style={"height": "100%"})

        # ── Vẽ biểu đồ 1: Cơ cấu dịch vụ (Pie Chart - Không Donut) ──────────────────
        fig_pie_dv = go.Figure()
        if not df_cur.empty and 'nhom_dv' in df_cur.columns:
            pie_colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
            fig_pie_dv.add_trace(go.Pie(
                labels=df_cur['nhom_dv'],
                values=df_cur['cuoc_tt_tong'],
                hole=0,
                marker=dict(colors=pie_colors),
                textinfo='percent+label',
                hovertemplate="Nhóm %{label}: %{value:,.0f} đ (%{percent})<extra></extra>"
            ))
            fig_pie_dv.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                height=280,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
        else:
            fig_pie_dv.update_layout(title="Không có dữ liệu cơ cấu")

        # ── Vẽ biểu đồ 1b: Cơ cấu loại khách hàng (Pie Chart - Không Donut) ─────────
        fig_pie_kh = go.Figure()
        if not df_kh_breakdown.empty and 'loai_kh' in df_kh_breakdown.columns:
            kh_colors = ['#94A3B8', '#3B82F6', '#10B981']  # Vãng lai (xám), KHM (xanh dương), Hiện hữu (xanh lá)
            fig_pie_kh.add_trace(go.Pie(
                labels=df_kh_breakdown['loai_kh'],
                values=df_kh_breakdown['cuoc_tt_tong'],
                hole=0,
                marker=dict(colors=kh_colors),
                textinfo='percent+label',
                hovertemplate="Loại %{label}: %{value:,.0f} đ (%{percent})<extra></extra>"
            ))
            fig_pie_kh.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                height=280,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
        else:
            fig_pie_kh.update_layout(title="Không có dữ liệu cơ cấu KH")

        # ── Vẽ biểu đồ 2: Xu hướng theo tuần BCCP (Line Chart) ───────────────
        fig_trend = go.Figure()
        if not df_trend.empty and 'ngay' in df_trend.columns:
            df_trend_weekly = df_trend.copy()
            df_trend_weekly = df_trend_weekly[df_trend_weekly['ngay'] != 'Chưa phân loại']
            df_trend_weekly['bccp_week'] = df_trend_weekly['ngay'].apply(lambda d: get_bccp_week_number(d, year))
            
            df_weekly = df_trend_weekly.groupby('bccp_week')['cuoc_tt_tong'].sum().reset_index()
            df_weekly = df_weekly.sort_values('bccp_week')
            
            fig_trend.add_trace(go.Scatter(
                x=[f"Tuần {w}" for w in df_weekly['bccp_week']],
                y=df_weekly['cuoc_tt_tong'],
                mode='lines+markers',
                name='Doanh thu',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=6, color='#1D4ED8'),
                fill='tozeroy',
                hovertemplate="Tuần %{x}: %{y:,.0f} đ<extra></extra>"
            ))
            fig_trend.update_layout(
                margin=dict(l=50, r=20, t=15, b=20),
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat=",.0f")
            )
        else:
            fig_trend.update_layout(title="Không có dữ liệu xu hướng")

        # ── Vẽ biểu đồ 3: So sánh doanh thu giữa các Cụm (Bar Chart) ─────
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

        # Area chart has been removed as per TIP-11-001.
        fig_area = go.Figure()
        fig_area.update_layout(title="Biểu đồ đã bị ẩn")

        # ── Top 10 CMS DataTable ───────────────────────────────────────────
        conn_tmp = sqlite3.connect(str(DB_PATH))
        try:
            where_clauses = [
                "cms IS NOT NULL", "cms != ''", "cms != 'NONE'", "cms NOT LIKE 'VANGLAI_%'",
                "san_pham_dv IN (SELECT ma_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'BCCP' OR nhom_chinh IS NULL)"
            ]
            params_cur = []
            
            if date_column == 'thang_du_lieu':
                start_month = f"T{date_from.month:02d}"
                end_month = f"T{date_to.month:02d}"
                where_clauses.append("thang_du_lieu BETWEEN ? AND ?")
                params_cur.extend([start_month, end_month])
                if year is not None:
                    where_clauses.append("nam_du_lieu = ?")
                    params_cur.append(year)
            else:
                where_clauses.append("ngay_chap_nhan BETWEEN ? AND ?")
                params_cur.extend([date_from.isoformat(), date_to.isoformat()])
                
            if nhom_dv:
                ph_dv = ",".join(["?"] * len(nhom_dv))
                where_clauses.append(f"san_pham_dv IN (SELECT ma_dich_vu FROM dim_dichvu WHERE nhom_dich_vu IN ({ph_dv}))")
                params_cur.extend(nhom_dv)
            if spdv:
                ph_spdv = ",".join(["?"] * len(spdv))
                where_clauses.append(f"san_pham_dv IN ({ph_spdv})")
                params_cur.extend(spdv)
            if cum_f and cum_f != "Tất cả":
                where_clauses.append("buu_cuc IN (SELECT ma_bc FROM dim_buucuc WHERE ten_cum = ?)")
                params_cur.append(cum_f)
            if bdx_f and bdx_f != "Tất cả":
                where_clauses.append("buu_cuc IN (SELECT ma_bc FROM dim_buucuc WHERE ten_bdx = ?)")
                params_cur.append(bdx_f)
            if bc_f and bc_f != "Tất cả":
                where_clauses.append("buu_cuc = ?")
                params_cur.append(bc_f)
            if hd_f == "Có HĐ":
                where_clauses.append("ma_hop_dong IS NOT NULL AND ma_hop_dong != ''")
            elif hd_f == "Không HĐ":
                where_clauses.append("(ma_hop_dong IS NULL OR ma_hop_dong = '')")
                
            where_str = " AND ".join(where_clauses)
            
            sql_cur = f"""
                WITH top_cms AS (
                    SELECT cms, SUM(cuoc_tt_tong) as cuoc_tt_tong
                    FROM transactions
                    WHERE {where_str}
                    GROUP BY cms
                    ORDER BY cuoc_tt_tong DESC
                    LIMIT 20
                )
                SELECT t.cms, t.cuoc_tt_tong, 
                       (SELECT d.nhom_dich_vu 
                        FROM transactions t2 
                        LEFT JOIN dim_dichvu d ON t2.san_pham_dv = d.ma_dich_vu 
                        WHERE t2.cms = t.cms AND {where_str}
                        GROUP BY d.nhom_dich_vu 
                        ORDER BY SUM(t2.cuoc_tt_tong) DESC LIMIT 1) as nhom_dv_chinh
                FROM top_cms t
            """
            df_cur_cms_tot = pd.read_sql_query(sql_cur, conn_tmp, params=params_cur)
            df_main_dv = df_cur_cms_tot[['cms', 'nhom_dv_chinh']].copy() if not df_cur_cms_tot.empty else pd.DataFrame(columns=['cms', 'nhom_dv_chinh'])
            
            if prev_from and prev_to and not df_cur_cms_tot.empty:
                where_prev = [
                    "cms IS NOT NULL", "cms != ''", "cms != 'NONE'", "cms NOT LIKE 'VANGLAI_%'",
                    "san_pham_dv IN (SELECT ma_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'BCCP' OR nhom_chinh IS NULL)"
                ]
                params_prev = []
                if date_column == 'thang_du_lieu':
                    where_prev.append("thang_du_lieu BETWEEN ? AND ?")
                    params_prev.extend([f"T{prev_from.month:02d}", f"T{prev_to.month:02d}"])
                    if year is not None:
                        where_prev.append("nam_du_lieu = ?")
                        params_prev.append(prev_from.year)
                else:
                    where_prev.append("ngay_chap_nhan BETWEEN ? AND ?")
                    params_prev.extend([prev_from.isoformat(), prev_to.isoformat()])
                    
                if nhom_dv:
                    where_prev.append(f"san_pham_dv IN (SELECT ma_dich_vu FROM dim_dichvu WHERE nhom_dich_vu IN ({ph_dv}))")
                    params_prev.extend(nhom_dv)
                if spdv:
                    where_prev.append(f"san_pham_dv IN ({ph_spdv})")
                    params_prev.extend(spdv)
                if cum_f and cum_f != "Tất cả":
                    where_prev.append("buu_cuc IN (SELECT ma_bc FROM dim_buucuc WHERE ten_cum = ?)")
                    params_prev.append(cum_f)
                if bdx_f and bdx_f != "Tất cả":
                    where_prev.append("buu_cuc IN (SELECT ma_bc FROM dim_buucuc WHERE ten_bdx = ?)")
                    params_prev.append(bdx_f)
                if bc_f and bc_f != "Tất cả":
                    where_prev.append("buu_cuc = ?")
                    params_prev.append(bc_f)
                if hd_f == "Có HĐ":
                    where_prev.append("ma_hop_dong IS NOT NULL AND ma_hop_dong != ''")
                elif hd_f == "Không HĐ":
                    where_prev.append("(ma_hop_dong IS NULL OR ma_hop_dong = '')")
                    
                cms_list = df_cur_cms_tot['cms'].tolist()
                ph_cms = ",".join(["?"] * len(cms_list))
                where_prev.append(f"cms IN ({ph_cms})")
                params_prev.extend(cms_list)
                
                sql_prev = f"SELECT cms, SUM(cuoc_tt_tong) as cuoc_tt_tong FROM transactions WHERE {' AND '.join(where_prev)} GROUP BY cms"
                df_prev_cms_tot = pd.read_sql_query(sql_prev, conn_tmp, params=params_prev)
            else:
                df_prev_cms_tot = pd.DataFrame(columns=['cms', 'cuoc_tt_tong'])
                
        except Exception as e:
            print(f"Error querying Top 10 CMS: {e}")
            df_cur_cms_tot = pd.DataFrame()
            df_prev_cms_tot = pd.DataFrame(columns=['cms', 'cuoc_tt_tong'])
            df_main_dv = pd.DataFrame()
        finally:
            conn_tmp.close()

        if not df_cur_cms_tot.empty:
            df_cur_cms_tot = df_cur_cms_tot[~df_cur_cms_tot['cms'].str.startswith('VANGLAI_', na=False)]
            df_cur_cms_tot = df_cur_cms_tot[df_cur_cms_tot['cms'].str.upper() != 'NONE']
            df_cur_cms_tot = df_cur_cms_tot[df_cur_cms_tot['cms'].str.strip() != 'Chưa phân loại']
            df_cur_cms_tot = df_cur_cms_tot[df_cur_cms_tot['cms'].str.strip() != '']
            
            df_merge = df_cur_cms_tot.merge(df_prev_cms_tot, on='cms', suffixes=('', '_prev'), how='left')
            df_merge['cuoc_tt_tong_prev'] = df_merge['cuoc_tt_tong_prev'].fillna(0)
            
            def calc_pct(row):
                cur = row['cuoc_tt_tong']
                prv = row['cuoc_tt_tong_prev']
                if prv <= 0:
                    return 100.0 if cur > 0 else 0.0
                return round((cur - prv) * 100.0 / prv, 1)
                
            df_merge['pct_change'] = df_merge.apply(calc_pct, axis=1)
            df_merge = df_merge.merge(df_main_dv, on='cms', how='left')
            df_merge['nhom_dv_chinh'] = df_merge['nhom_dv_chinh'].fillna('Chưa rõ')
            df_merge['canh_bao'] = df_merge['pct_change'].apply(lambda x: '🔴' if x < -20 else '')
            
            df_top = df_merge.nlargest(10, 'cuoc_tt_tong')
            df_top_display = df_top.copy()
            df_top_display['Doanh thu'] = df_top_display['cuoc_tt_tong'].apply(lambda x: f"{x:,.0f} đ")
            df_top_display['Tăng trưởng'] = df_top_display['pct_change'].apply(lambda x: f"{x:+.1f}%")
            
            from dash import dash_table
            top_table = dash_table.DataTable(
                id="top-cms-table",
                data=df_top_display.to_dict("records"),
                columns=[
                    {"name": "CMS", "id": "cms"},
                    {"name": "Doanh thu kỳ này", "id": "Doanh thu"},
                    {"name": "% Tăng trưởng", "id": "Tăng trưởng"},
                    {"name": "Nhóm DV chính", "id": "nhom_dv_chinh"},
                    {"name": "⚠️", "id": "canh_bao"}
                ],
                sort_action='native',
                filter_action='native',
                style_table={"overflowX": "auto", "borderRadius": "8px", "border": "1px solid #E2E8F0"},
                style_header={
                    "backgroundColor": "#F8FAFC",
                    "fontWeight": "bold",
                    "color": "#1E293B",
                    "border": "1px solid #CBD5E1"
                },
                style_cell={
                    "padding": "8px 10px",
                    "textAlign": "left",
                    "fontSize": "12px",
                    "fontFamily": "Inter, sans-serif"
                },
                style_data_conditional=[
                    {
                        "if": {
                            "column_id": "Tăng trưởng",
                            "filter_query": "{pct_change} < 0"
                        },
                        "color": "#DC2626",
                        "fontWeight": "bold"
                    },
                    {
                        "if": {
                            "column_id": "Tăng trưởng",
                            "filter_query": "{pct_change} >= 0"
                        },
                        "color": "#059669",
                        "fontWeight": "bold"
                    },
                    {
                        "if": {
                            "column_id": "cms",
                            "filter_query": '{canh_bao} = "🔴"'
                        },
                        "backgroundColor": "#FEE2E2"
                    }
                ]
            )
        else:
            top_table = html.Div("Không có dữ liệu Top CMS")

        return [
            phbc_n, phbc_s, phbc_p, phbc_y,
            tt_n,   tt_s,   tt_p,   tt_y,
            tmdt_n, tmdt_s, tmdt_p, tmdt_y,
            qt_n,   qt_s,   qt_p,   qt_y,
            kh_n,   kh_s,   kh_p,   kh_y,
            sl_n,   sl_s,   sl_p,   sl_y,
            plan_val_str, plan_subtext,
            fig_gauge,
            khm_card_children,
            vanglai_card_children,
            fig_pie_dv,
            fig_pie_kh,
            fig_trend,
            fig_bar,
            top_table
        ]


