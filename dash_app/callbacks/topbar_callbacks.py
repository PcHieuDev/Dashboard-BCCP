# -*- coding: utf-8 -*-
"""
Các callbacks quản lý hành vi và tương tác của bộ lọc trên Topbar.
Xử lý chuyển đổi chu kỳ, cascade địa lý và phân quyền tài khoản cụm.
"""

import sqlite3
import pandas as pd
from datetime import date
from dash import Output, Input, State
import dash
from flask_login import current_user
from flask import has_request_context
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from config.week_calendar import get_week_list

import logging
try:
    from config.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    try:
        from config.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = logging.getLogger(__name__)


def get_user_cum():
    """Lấy tên cụm được gán của user hiện tại nếu có phân quyền."""
    if has_request_context() and current_user.is_authenticated:
        cum = getattr(current_user, 'assigned_cum', None)
        if cum and cum.strip():
            return cum.strip()
    return None

def register_topbar_callbacks(app):
    """
    Đăng ký các callback của Topbar với ứng dụng Dash.
    """

    # 1. Callback ẩn/hiện container Tuần/Tháng theo chu kỳ chọn
    @app.callback(
        [Output("week-container", "style"),
         Output("month-container", "style")],
        [Input("sidebar-period", "value")]
    )
    def toggle_period_filters(period):
        if period == "Tuần":
            return {"display": "block"}, {"display": "none"}
        else:  # Mặc định là Tháng
            return {"display": "none"}, {"display": "block"}

    @app.callback(
        [Output("sidebar-week-select", "options"),
         Output("sidebar-week-select", "value")],
        [Input("sidebar-year", "value"),
         Input("sidebar-period", "value")],
        [State("sidebar-week-select", "value")]
    )
    def update_week_dropdown(year, period, current_week):
        if not year:
            return dash.no_update, dash.no_update

        weeks = get_week_list(int(year))
        options = []
        valid_weeks = []
        for w_num, w_from, w_to in weeks:
            valid_weeks.append(w_num)
            options.append({
                "label": f"Tuần {w_num:02d} ({w_from.strftime('%d/%m')} - {w_to.strftime('%d/%m')})",
                "value": w_num
            })

        # Xác định tuần mặc định dùng CUSTOM week (không dùng ISO week)
        from datetime import date
        today = date.today()
        current_year = today.year

        default_week = None
        if int(year) == current_year:
            # Tìm tuần custom chứa ngày hôm nay
            for w_num, w_from, w_to in weeks:
                if w_from <= today <= w_to:
                    default_week = w_num
                    break
            if default_week is None and valid_weeks:
                default_week = valid_weeks[-1]
        elif valid_weeks:
            default_week = valid_weeks[-1] if int(year) < current_year else valid_weeks[0]

        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

        # Nếu user switch sang Tuần: luôn reset về tuần hiện tại
        if triggered_id == "sidebar-period" and period == "Tuần":
            final_week = default_week
        # Nếu đổi năm hoặc giữ nguyên tuần đang chọn nếu hợp lệ
        elif current_week and current_week in valid_weeks:
            final_week = current_week
        else:
            final_week = default_week

        return options, final_week

    # 2b. Callback reset tháng về tháng hiện tại khi switch sang Tháng
    @app.callback(
        Output("sidebar-month-select", "value", allow_duplicate=True),
        [Input("sidebar-period", "value")],
        prevent_initial_call=True
    )
    def reset_month_on_period_switch(period):
        if period == "Tháng":
            from datetime import date
            return date.today().month
        return dash.no_update

    # 3 & 4. Callback cascade địa lý: Cụm -> BĐX -> Bưu cục

    # Gộp chung để tránh lỗi trùng lặp output trong Dash
    @app.callback(
        [Output("sidebar-bdx", "options"),
         Output("sidebar-bdx", "value"),
         Output("sidebar-buu-cuc", "options"),
         Output("sidebar-buu-cuc", "value")],
        [Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value")]
    )
    def update_geographic_filters(cum_val, bdx_val):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""
        
        # Giá trị trả về mặc định
        bdx_opts = dash.no_update
        bdx_value = dash.no_update
        bc_opts = dash.no_update
        bc_value = dash.no_update
        
        if not DB_PATH.exists():
            return (
                [{"label": "Tất cả BĐX", "value": "Tất cả"}], "Tất cả",
                [{"label": "Tất cả Bưu cục", "value": "Tất cả"}], "Tất cả"
            )
            
        conn = sqlite3.connect(str(DB_PATH))
        try:
            # TH1: Callback kích hoạt lần đầu hoặc do đổi Cụm
            if not triggered_id or triggered_id == "sidebar-cum":
                # Lấy tất cả Xã/Phường thuộc Cụm
                query_bdx = "SELECT DISTINCT ten_bdx FROM dim_buucuc WHERE ten_bdx IS NOT NULL AND ten_bdx NOT LIKE 'Đại diện Cụm%'"
                params_bdx = []
                if cum_val and cum_val != "Tất cả":
                    query_bdx += " AND ten_cum = ?"
                    params_bdx.append(cum_val)
                query_bdx += " ORDER BY ten_bdx"
                df_bdx = pd.read_sql_query(query_bdx, conn, params=params_bdx)
                bdx_opts = [{"label": "Tất cả BĐX", "value": "Tất cả"}] + [{"label": b, "value": b} for b in df_bdx["ten_bdx"].tolist()]
                if bdx_val and bdx_val in df_bdx["ten_bdx"].tolist():
                    bdx_value = bdx_val
                else:
                    bdx_value = "Tất cả"
                
                # Lấy tất cả Bưu cục thuộc Cụm (loại bỏ mã đại diện cụm và đại diện xã)
                query_bc = "SELECT ma_bc, ten_buu_cuc FROM dim_buucuc WHERE ma_bc IS NOT NULL AND ma_bc != ma_bdx AND ma_bc NOT LIKE 'CUM_%'"
                params_bc = []
                if cum_val and cum_val != "Tất cả":
                    query_bc += " AND ten_cum = ?"
                    params_bc.append(cum_val)
                query_bc += " ORDER BY ma_bc"
                df_bc = pd.read_sql_query(query_bc, conn, params=params_bc)
                bc_opts = [{"label": "Tất cả Bưu cục", "value": "Tất cả"}] + [{"label": f"{r['ma_bc']} - {r['ten_buu_cuc']}", "value": r['ma_bc']} for _, r in df_bc.iterrows()]
                bc_value = "Tất cả"
                
            # TH2: Đổi Xã/Phường -> chỉ cascade xuống Bưu cục
            elif triggered_id == "sidebar-bdx":
                query_bc = "SELECT ma_bc, ten_buu_cuc FROM dim_buucuc WHERE ma_bc IS NOT NULL AND ma_bc != ma_bdx AND ma_bc NOT LIKE 'CUM_%'"
                params_bc = []
                if cum_val and cum_val != "Tất cả":
                    query_bc += " AND ten_cum = ?"
                    params_bc.append(cum_val)
                if bdx_val and bdx_val != "Tất cả":
                    query_bc += " AND ten_bdx = ?"
                    params_bc.append(bdx_val)
                query_bc += " ORDER BY ma_bc"
                df_bc = pd.read_sql_query(query_bc, conn, params=params_bc)
                bc_opts = [{"label": "Tất cả Bưu cục", "value": "Tất cả"}] + [{"label": f"{r['ma_bc']} - {r['ten_buu_cuc']}", "value": r['ma_bc']} for _, r in df_bc.iterrows()]
                bc_value = "Tất cả"
                
        except Exception as e:
            logger.error(f"Error in topbar geographic cascade: {e}")
        finally:
            conn.close()
            
        return bdx_opts, bdx_value, bc_opts, bc_value

    # 5. Callback phân quyền tài khoản khi load trang
    @app.callback(
        [Output("sidebar-cum", "options"),
         Output("sidebar-cum", "value"),
         Output("sidebar-cum", "disabled")],
        [Input("url", "pathname")],
        [State("global-filters-store", "data")]
    )
    def apply_user_permissions(pathname, store_data):
        assigned_cum = get_user_cum()
        stored_cum = store_data.get('cum', "Tất cả") if store_data else "Tất cả"
        
        if assigned_cum:
            # Khóa cụm được phân quyền
            options = [{"label": assigned_cum, "value": assigned_cum}]
            return options, assigned_cum, True
        else:
            # Admin: hiển thị đầy đủ cụm
            if not DB_PATH.exists():
                return [{"label": "Tất cả Cụm", "value": "Tất cả"}], stored_cum, False
                
            conn = sqlite3.connect(str(DB_PATH))
            try:
                query = "SELECT DISTINCT ten_cum FROM dim_buucuc WHERE ten_cum IS NOT NULL ORDER BY ten_cum"
                df = pd.read_sql_query(query, conn)
                options = [{"label": "Tất cả Cụm", "value": "Tất cả"}] + [{"label": c, "value": c} for c in df["ten_cum"].tolist()]
            except Exception as e:
                logger.error(f"Error loading cum options: {e}")
                options = [{"label": "Tất cả Cụm", "value": "Tất cả"}]
            finally:
                conn.close()
            return options, stored_cum, False


    # 6. Dong bo trang thai vao Store va nguoc lai
    @app.callback(
        Output('global-filters-store', 'data'),
        [Input('sidebar-year', 'value'),
         Input('sidebar-period', 'value'),
         Input('sidebar-week-select', 'value'),
         Input('sidebar-month-select', 'value'),
         Input('sidebar-cum', 'value'),
         Input('sidebar-bdx', 'value'),
         Input('sidebar-buu-cuc', 'value')],
        State('global-filters-store', 'data'),
    )
    def save_to_store(y, p, w, m, c, b, bc, data):
        new_data = {
            'year': y, 'period': p, 'week': w, 'month': m,
            'cum': c, 'bdx': b, 'buucuc': bc
        }
        if data == new_data:
            from dash import no_update
            return no_update
        return new_data

    @app.callback(
        [Output('sidebar-year', 'value', allow_duplicate=True),
         Output('sidebar-period', 'value', allow_duplicate=True),
         Output('sidebar-week-select', 'value', allow_duplicate=True),
         Output('sidebar-month-select', 'value', allow_duplicate=True),
         Output('sidebar-cum', 'value', allow_duplicate=True),
         Output('sidebar-bdx', 'value', allow_duplicate=True),
         Output('sidebar-buu-cuc', 'value', allow_duplicate=True)],
        [Input('global-filters-store', 'data')],
        prevent_initial_call=True
    )
    def load_from_store(data):
        from dash import no_update
        if not data:
            return no_update
        return (
            data.get('year', no_update),
            data.get('period', no_update),
            data.get('week', no_update),
            data.get('month', no_update),
            data.get('cum', no_update),
            data.get('bdx', no_update),
            data.get('buucuc', no_update)
        )
