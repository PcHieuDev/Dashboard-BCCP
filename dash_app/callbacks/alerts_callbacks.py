# -*- coding: utf-8 -*-
"""
Callbacks xử lý phân tích và hiển thị danh sách Cảnh báo sụt giảm doanh thu (Alerts).
Ngưỡng sụt giảm: Vàng 15%, Đỏ 30%.
"""

import dash
from dash import Output, Input, State, html
import sys
import pandas as pd
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from callbacks.utils import resolve_filters_and_query, format_revenue
from config.settings import DB_PATH
import sqlite3
import dash_bootstrap_components as dbc

def get_prev_month_year(year, month):
    if not year or not month:
        return year, month
    if month == 1:
        return year - 1, 12
    else:
        return year, month - 1

def register_alerts_callbacks(app):
    """
    Đăng ký các callback phân tích cảnh báo doanh thu.
    """
    @app.callback(
        Output("alerts-list-container", "children"),
        [Input("btn-apply-filter", "n_clicks")],
        [State("tabs-navigation", "value"),
         State("alerts-nhom-dv-select", "value"),
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-nhom-dv", "data"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "data"),
         State("sidebar-hop-dong", "data")],
        prevent_initial_call=True
    )
    def update_alerts_list(n_clicks, tab_val, selected_service, year, period, start_date, end_date, week_idx, month_val,
                           nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        # Chỉ chạy khi đang ở Tab Cảnh báo
        if tab_val != "tab-alerts" or tab_val is None:
            return dash.no_update
        spdv = None
            
        alerts = []
        
        # ----------------------------------------------------------------------
        # LOGIC CẢNH BÁO CHO 3 DỊCH VỤ MỚI (HCC, TCBC, PPBL)
        # ----------------------------------------------------------------------
        if selected_service != "BCCP":
            if not DB_PATH.exists():
                return html.Div("Chưa có cơ sở dữ liệu để phân tích.", className="text-center text-muted p-4")
                
            pyear, pmonth = get_prev_month_year(year, month_val)
            thang_cur = f"T{month_val:02d}"
            thang_prev = f"T{pmonth:02d}"
            
            # Xây dựng SQL lấy doanh thu theo Cụm kỳ hiện tại và kỳ trước
            if selected_service == "HCC":
                sql_cur = """
SELECT b.ten_cum, SUM(t_inner.dt) as dt
FROM (
    SELECT t.buu_cuc as ma_bc, SUM(t.cuoc_tt_tong) as dt
    FROM transactions t
    INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
    WHERE d.nhom_chinh = 'HCC' AND t.nam_du_lieu = :nam AND t.thang_du_lieu = :thang
    GROUP BY t.buu_cuc
    UNION ALL
    SELECT ma_buu_cuc as ma_bc, SUM(doanh_thu) as dt
    FROM transactions_hcc
    WHERE nam_du_lieu = :nam AND thang_du_lieu = :thang
    GROUP BY ma_buu_cuc
) t_inner
INNER JOIN dim_buucuc b ON t_inner.ma_bc = b.ma_bc
GROUP BY b.ten_cum
"""
                sql_prev = sql_cur.replace(":nam", ":pnam").replace(":thang", ":pthang")
            else:
                table_name = f"transactions_{selected_service.lower()}"
                sql_cur = f"""
SELECT b.ten_cum, SUM(t.doanh_thu) as dt
FROM {table_name} t
INNER JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_bc
WHERE t.nam_du_lieu = :nam AND t.thang_du_lieu = :thang
GROUP BY b.ten_cum
"""
                sql_prev = sql_cur.replace(":nam", ":pnam").replace(":thang", ":pthang")
                
            conn = sqlite3.connect(str(DB_PATH))
            try:
                # Query kỳ hiện tại
                df_cur = pd.read_sql_query(sql_cur, conn, params={"nam": year, "thang": thang_cur})
                # Query kỳ trước
                df_prev = pd.read_sql_query(sql_prev, conn, params={"pnam": pyear, "pthang": thang_prev})
            except Exception as e:
                print(f"Lỗi phân tích cảnh báo {selected_service}: {e}")
                df_cur = pd.DataFrame()
                df_prev = pd.DataFrame()
            finally:
                conn.close()
                
            # Kiểm tra xem có dữ liệu nào không
            tot_cur = df_cur["dt"].sum() if not df_cur.empty else 0.0
            tot_prev = df_prev["dt"].sum() if not df_prev.empty else 0.0
            
            if tot_cur == 0 and tot_prev == 0:
                return html.Div(
                    f"⚠️ Chưa có dữ liệu giao dịch cho nhóm dịch vụ {selected_service} trong Tháng {month_val:02d}/{year} để thực hiện phân tích cảnh báo.",
                    className="text-center text-muted p-4 border rounded bg-light"
                )
                
            # So sánh sụt giảm theo từng Cụm
            if not df_cur.empty and not df_prev.empty:
                df_merged = pd.merge(df_cur, df_prev, on="ten_cum", how="outer", suffixes=("_cur", "_prev")).fillna(0.0)
                
                for _, r in df_merged.iterrows():
                    c_name = r["ten_cum"]
                    val_now = r["dt_cur"]
                    val_prev = r["dt_prev"]
                    
                    # Chỉ phân tích khi kỳ trước có doanh thu tối thiểu 1 triệu đồng để tránh cảnh báo rác
                    if val_prev >= 1_000_000 and val_now < val_prev:
                        pct_change = ((val_now - val_prev) / val_prev) * 100.0
                        abs_change = val_prev - val_now
                        
                        if pct_change <= -30.0:
                            alerts.append({
                                "level": "red",
                                "category": f"Cụm Địa Lý ({selected_service} - Nghiêm trọng)",
                                "target": c_name,
                                "msg": f"Doanh thu {selected_service} Cụm {c_name} sụt giảm mạnh {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với tháng trước.",
                                "detail": f"Doanh thu tháng này đạt {format_revenue(val_now)} (tháng trước đạt {format_revenue(val_prev)})."
                            })
                        elif pct_change <= -15.0:
                            alerts.append({
                                "level": "yellow",
                                "category": f"Cụm Địa Lý ({selected_service})",
                                "target": c_name,
                                "msg": f"Doanh thu {selected_service} Cụm {c_name} giảm {abs(pct_change):.1f}% (giảm {format_revenue(abs_change)}) so với tháng trước.",
                                "detail": f"Doanh thu tháng này đạt {format_revenue(val_now)} (tháng trước đạt {format_revenue(val_prev)})."
                            })
                            
        # ----------------------------------------------------------------------
        # LOGIC CẢNH BÁO CHO DỊCH VỤ GỐC (BCCP)
        # ----------------------------------------------------------------------
        else:
            compare_prev = True
            compare_mode = "prev_period"
            
            # PHÂN TÍCH 1: CẢNH BÁO THEO CỤM ĐỊA LÝ
            _, _, _, df_cum = resolve_filters_and_query(
                year, period, start_date, end_date, week_idx, month_val, compare_mode,
                nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
                group_by_primary='cum', group_by_secondary=None, compare_prev=compare_prev
            )
            
            if not df_cum.empty and 'cuoc_tt_tong_prev' in df_cum.columns:
                for _, row in df_cum.iterrows():
                    cum_name = row.get('cum', 'Không rõ Cụm')
                    if pd.isna(cum_name) or cum_name == 'Tất cả':
                        continue
                    
                    val_now = row.get('cuoc_tt_tong', 0) or 0
                    val_prev = row.get('cuoc_tt_tong_prev', 0) or 0
                    
                    if val_prev >= 5_000_000 and val_now < val_prev:
                        pct_change = ((val_now - val_prev) / val_prev) * 100.0
                        abs_change = val_prev - val_now
                        
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
                            
            # PHÂN TÍCH 2: CẢNH BÁO THEO NHÓM DỊCH VỤ CHÍNH
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
     
            # PHÂN TÍCH 3: CẢNH BÁO THEO TOP 10 KHÁCH HÀNG LỚN NHẤT
            _, _, _, df_kh = resolve_filters_and_query(
                year, period, start_date, end_date, week_idx, month_val, compare_mode,
                nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
                group_by_primary='cms', group_by_secondary=None, compare_prev=compare_prev
            )
            
            if not df_kh.empty and 'cuoc_tt_tong_prev' in df_kh.columns:
                df_kh_valid = df_kh[
                    df_kh['cms'].notna() & 
                    (~df_kh['cms'].str.startswith('VANGLAI_', na=False)) & 
                    (df_kh['cms'] != '')
                ]
                df_top_kh = df_kh_valid.nlargest(10, 'cuoc_tt_tong')
                
                for _, row in df_top_kh.iterrows():
                    kh_name = row.get('cms', 'Khách hàng ẩn danh')
                    val_now = row.get('cuoc_tt_tong', 0) or 0
                    val_prev = row.get('cuoc_tt_tong_prev', 0) or 0
                    
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
                            
            # PHÂN TÍCH 4: CẢNH BÁO THIẾU DANH MỤC MAPPING
            try:
                conn = sqlite3.connect(str(DB_PATH))
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT DISTINCT t.san_pham_dv 
                    FROM transactions t 
                    LEFT JOIN dim_spdv d ON t.san_pham_dv = d.ma_spdv 
                    WHERE d.ma_spdv IS NULL AND t.san_pham_dv IS NOT NULL AND t.san_pham_dv != ''
                """)
                missing_sp = [r[0] for r in cursor.fetchall()]
                
                cursor.execute("""
                    SELECT DISTINCT t.buu_cuc 
                    FROM transactions t 
                    LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc 
                    WHERE b.ma_bc IS NULL AND t.buu_cuc IS NOT NULL AND t.buu_cuc != ''
                """)
                missing_bc = [r[0] for r in cursor.fetchall()]
                conn.close()
                
                if missing_sp:
                    alerts.append({
                        "level": "yellow",
                        "category": "Chất Lượng Dữ Liệu (Sản Phẩm Mới)",
                        "target": ", ".join(missing_sp[:5]),
                        "msg": f"Phát hiện {len(missing_sp)} mã sản phẩm mới chưa được định nghĩa phân nhóm dịch vụ.",
                        "detail": f"Danh sách mã sản phẩm: {', '.join(missing_sp)}. Doanh thu các sản phẩm này đang tạm hiển thị dưới nhóm 'Chưa phân loại'. Sếp vui lòng cập nhật file mapping-spdv.csv và chạy đồng bộ."
                    })
                    
                if missing_bc:
                    alerts.append({
                        "level": "yellow",
                        "category": "Chất Lượng Dữ Liệu (Bưu Cục Mới)",
                        "target": ", ".join(missing_bc[:5]),
                        "msg": f"Phát hiện {len(missing_bc)} mã bưu cục mới chưa được phân Cụm địa lý.",
                        "detail": f"Danh sách mã bưu cục: {', '.join(missing_bc)}. Doanh thu các bưu cục này đang tạm hiển thị dưới Cụm 'Không rõ Cụm'. Sếp vui lòng cập nhật file mapping-BC-BDX-Cum.csv và chạy đồng bộ."
                    })
            except Exception as e:
                pass
                
        # ----------------------------------------------------------------------
        # RENDERING LIST CARDS
        # ----------------------------------------------------------------------
        if not alerts:
            return html.Div([
                html.Div(f"🎉 Không phát hiện điểm sụt giảm doanh thu bất thường cho dịch vụ {selected_service}. Hệ thống đang vận hành ổn định!", 
                         style={"padding": "25px", "textAlign": "center", "color": "#16A34A", "fontWeight": "bold", "backgroundColor": "#F0FDF4", "borderRadius": "8px", "border": "1px solid #BBF7D0"})
            ])
            
        alert_components = []
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
