# -*- coding: utf-8 -*-
"""
Các hàm helper hỗ trợ xuất báo cáo doanh thu ra định dạng Excel (openpyxl) và PDF (reportlab).
Hỗ trợ Unicode tiếng Việt đầy đủ và format số liệu đẹp mắt.
"""

import io
import os
import pandas as pd
from datetime import datetime

# Import thư viện Excel
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# Import thư viện PDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from components.data_table import COL_LABEL_MAP

# --------------------------------------------------------------------------
# ĐĂNG KÝ FONT TIẾNG VIỆT CHO PDF
# --------------------------------------------------------------------------
FONT_NAME = 'Helvetica' # Mặc định fallback
try:
    # Thử tìm font Arial trên Windows
    win_font = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf')
    if os.path.exists(win_font):
        pdfmetrics.registerFont(TTFont('Arial-Viet', win_font))
        FONT_NAME = 'Arial-Viet'
    else:
        # Thử tìm font Times New Roman
        win_font_times = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'times.ttf')
        if os.path.exists(win_font_times):
            pdfmetrics.registerFont(TTFont('Times-Viet', win_font_times))
            FONT_NAME = 'Times-Viet'
except Exception as e:
    print(f"Không thể đăng ký font tiếng Việt cho PDF: {e}. Dùng font fallback {FONT_NAME}")


# --------------------------------------------------------------------------
# HÀM TẠO EXCEL
# --------------------------------------------------------------------------
def generate_excel_report(df: pd.DataFrame, groupby_cols: list, compare_opt: str, filter_info: dict) -> bytes:
    """
    Tạo báo cáo Excel chuyên nghiệp từ DataFrame và thông tin bộ lọc.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Báo cáo Doanh thu"
    
    font_name = "Arial"
    
    # 1. Tiêu đề báo cáo
    ws.merge_cells("A1:H1")
    ws["A1"] = "BÁO CÁO DOANH THU ĐIỀU HÀNH BCCP"
    ws["A1"].font = Font(name=font_name, size=16, bold=True, color="003366")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40
    
    # 2. Thông tin bộ lọc
    ws["A3"] = "Thông tin bộ lọc:"
    ws["A3"].font = Font(name=font_name, size=11, bold=True, italic=True, color="555555")
    
    row_idx = 4
    for k, v in filter_info.items():
        ws.cell(row=row_idx, column=1, value=f"• {k}: {v}").font = Font(name=font_name, size=10, italic=True)
        row_idx += 1
        
    ws.cell(row=row_idx, column=1, value=f"• Ngày xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}").font = Font(name=font_name, size=10, italic=True)
    row_idx += 2  # Để trống 1 dòng
    
    # 3. Định nghĩa các cột cần xuất
    columns = []
    for col in groupby_cols:
        columns.append(col)
    
    metrics = ['san_luong', 'khoi_luong_thuc', 'cuoc_cb_tong', 'cuoc_tt_tong', 'cuoc_tt_gom_vat', 'so_kh']
    for col in metrics:
        columns.append(col)
        
    if compare_opt in ('prev_period', 'both'):
        for m in metrics:
            columns.append(f"{m}_prev")
            columns.append(f"{m}_pct_change")
            
    if compare_opt in ('yoy', 'both'):
        for m in metrics:
            columns.append(f"{m}_yoy")
            columns.append(f"{m}_yoy_pct_change")
            
    # 4. Vẽ header bảng dữ liệu
    header_row = row_idx
    ws.row_dimensions[header_row].height = 28
    
    header_fill = PatternFill(start_color="0056B3", end_color="0056B3", fill_type="solid") # Màu xanh dương bưu điện
    header_font = Font(name=font_name, size=10, bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border_thin = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)
    
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=COL_LABEL_MAP.get(col_name, col_name))
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = cell_border
        
    # 5. Điền dữ liệu
    data_start_row = header_row + 1
    for r_idx, row_data in enumerate(df.to_dict('records'), start=data_start_row):
        ws.row_dimensions[r_idx].height = 20
        # Xen kẽ màu dòng
        is_odd = (r_idx % 2 == 1)
        row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") if is_odd else PatternFill(fill_type=None)
        
        for c_idx, col_name in enumerate(columns, start=1):
            val = row_data.get(col_name, None)
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = cell_border
            if row_fill.fill_type:
                cell.fill = row_fill
                
            # Phân loại format
            if pd.isna(val) or val is None:
                cell.value = "-"
                cell.alignment = Alignment(horizontal="center")
            elif col_name in groupby_cols:
                cell.value = str(val)
                cell.alignment = Alignment(horizontal="left", vertical="center")
                cell.font = Font(name=font_name, size=9, bold=True)
            elif 'pct_change' in col_name:
                # Đổi thành tỉ lệ thực tế để Excel tự nhân 100 khi định dạng %
                cell.value = float(val) / 100.0
                cell.number_format = '+0.0%;-0.0%;"0.0%"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                # Màu đỏ nếu âm, xanh nếu dương
                if val < 0:
                    cell.font = Font(name=font_name, size=9, color="DC2626")
                elif val > 0:
                    cell.font = Font(name=font_name, size=9, color="16A34A")
                else:
                    cell.font = Font(name=font_name, size=9)
            elif col_name in ('san_luong', 'san_luong_prev', 'san_luong_yoy', 'so_kh', 'so_kh_prev', 'so_kh_yoy'):
                cell.value = int(val)
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.font = Font(name=font_name, size=9)
            elif 'khoi_luong_thuc' in col_name:
                # Chuyển đổi gram -> kg
                cell.value = float(val) / 1000.0
                cell.number_format = '#,##0.0" kg"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.font = Font(name=font_name, size=9)
            elif 'cuoc_' in col_name:
                cell.value = float(val)
                cell.number_format = '#,##0" đ"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.font = Font(name=font_name, size=9)
            else:
                cell.value = val
                cell.alignment = Alignment(horizontal="left", vertical="center")
                
    # 6. Thêm dòng tổng cộng ở cuối
    total_row = data_start_row + len(df)
    ws.row_dimensions[total_row].height = 22
    total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    
    # Ghi nhãn "Tổng cộng" ở cột 1
    cell_tot_lbl = ws.cell(row=total_row, column=1, value="Tổng cộng")
    cell_tot_lbl.font = Font(name=font_name, size=10, bold=True, color="000000")
    cell_tot_lbl.alignment = Alignment(horizontal="left", vertical="center")
    cell_tot_lbl.fill = total_fill
    cell_tot_lbl.border = cell_border
    
    # Tô nền các cột groupby còn lại (nếu có)
    for c_idx in range(2, len(groupby_cols) + 1):
        cell_empty = ws.cell(row=total_row, column=c_idx, value="")
        cell_empty.fill = total_fill
        cell_empty.border = cell_border
        
    # Tính tổng cho từng cột metrics
    for c_idx, col_name in enumerate(columns[len(groupby_cols):], start=len(groupby_cols) + 1):
        cell = ws.cell(row=total_row, column=c_idx)
        cell.fill = total_fill
        cell.border = cell_border
        cell.font = Font(name=font_name, size=9, bold=True)
        
        # Chỉ tính SUM cho các cột số lượng, cước, khối lượng.
        # Với cột phần trăm biến động, ta sẽ tính lại dựa trên tổng.
        if 'pct_change' in col_name:
            # Rút gọn: tính trung bình hoặc để trống
            cell.value = "-"
            cell.alignment = Alignment(horizontal="center")
        elif col_name in ('so_kh', 'so_kh_prev', 'so_kh_yoy'):
            # Số lượng khách hàng tổng: lấy sum (gần đúng)
            col_letter = get_column_letter(c_idx)
            cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row-1})"
            cell.number_format = '#,##0'
            cell.alignment = Alignment(horizontal="right")
        elif 'khoi_luong_thuc' in col_name:
            col_letter = get_column_letter(c_idx)
            cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row-1})"
            cell.number_format = '#,##0.0" kg"'
            cell.alignment = Alignment(horizontal="right")
        elif col_name in ('san_luong', 'san_luong_prev', 'san_luong_yoy') or 'cuoc_' in col_name:
            col_letter = get_column_letter(c_idx)
            cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row-1})"
            if 'cuoc_' in col_name:
                cell.number_format = '#,##0" đ"'
            else:
                cell.number_format = '#,##0'
            cell.alignment = Alignment(horizontal="right")
            
    # 7. Tự động giãn cột phù hợp dữ liệu
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        
        # Kiểm tra độ dài tiêu đề hiển thị
        for cell in col:
            # Bỏ qua hàng tiêu đề chính dòng 1 đã merge
            if cell.row == 1:
                continue
            val_str = str(cell.value or '')
            # Tối ưu đo độ dài
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    # Xuất dữ liệu nhị phân
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# --------------------------------------------------------------------------
# HÀM TẠO PDF
# --------------------------------------------------------------------------
def generate_pdf_report(df: pd.DataFrame, groupby_cols: list, compare_opt: str, filter_info: dict) -> bytes:
    """
    Tạo báo cáo PDF chuyên nghiệp (Khổ ngang A4) hiển thị bảng báo cáo doanh thu điều hành.
    """
    output = io.BytesIO()
    
    # Thiết lập lề 15mm
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Tạo style tùy chỉnh hỗ trợ font tiếng Việt đã đăng ký
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#003366'),
        spaceAfter=15
    )
    
    filter_style = ParagraphStyle(
        'FilterInfo',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        spaceAfter=3
    )
    
    header_style = ParagraphStyle(
        'TableHeader',
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        alignment=1, # Center
        textColor=colors.white
    )
    
    cell_style_left = ParagraphStyle(
        'CellLeft',
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        alignment=0 # Left
    )
    
    cell_style_right = ParagraphStyle(
        'CellRight',
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        alignment=2 # Right
    )
    
    cell_style_right_bold = ParagraphStyle(
        'CellRightBold',
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        alignment=2 # Right
    )
    
    elements = []
    
    # 1. Tiêu đề
    elements.append(Paragraph("BÁO CÁO DOANH THU ĐIỀU HÀNH BCCP", title_style))
    elements.append(Spacer(1, 5))
    
    # 2. Thông tin bộ lọc
    elements.append(Paragraph("<b>Thông tin bộ lọc áp dụng:</b>", filter_style))
    for k, v in filter_info.items():
        elements.append(Paragraph(f"• {k}: {v}", filter_style))
    elements.append(Paragraph(f"• Ngày xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", filter_style))
    elements.append(Spacer(1, 15))
    
    # 3. Chuẩn bị bảng dữ liệu
    columns = []
    for col in groupby_cols:
        columns.append(col)
    
    # Để PDF khổ ngang A4 không bị quá tải cột, ta chỉ hiển thị một số cột chỉ số chính:
    # Sản lượng, Khối lượng, Cước TT, Số KH.
    # Nếu có so sánh, ta hiển thị thêm cước TT kỳ trước/yoy và % biến động.
    metrics_to_export = ['san_luong', 'khoi_luong_thuc', 'cuoc_tt_tong', 'so_kh']
    for m in metrics_to_export:
        columns.append(m)
        if compare_opt in ('prev_period', 'both'):
            columns.append(f"{m}_prev")
            columns.append(f"{m}_pct_change")
        if compare_opt in ('yoy', 'both'):
            columns.append(f"{m}_yoy")
            columns.append(f"{m}_yoy_pct_change")
            
    # Tạo Header data
    table_data = []
    header_row = [Paragraph(f"<b>{COL_LABEL_MAP.get(c, c)}</b>", header_style) for c in columns]
    table_data.append(header_row)
    
    # Định dạng tiền tệ VND rút gọn trong PDF
    def format_money_short(val):
        if val is None or pd.isna(val):
            return "0 đ"
        if abs(val) >= 1_000_000_000:
            return f"{val / 1_000_000_000:.2f} tỷ"
        elif abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.1f} tr"
        else:
            return f"{val:,.0f} đ"
            
    # Điền dữ liệu hàng (Giới hạn tối đa 60 dòng để tránh PDF quá dài và tràn trang)
    df_limited = df.head(60)
    
    for _, row in df_limited.iterrows():
        row_cells = []
        for col in columns:
            val = row.get(col, None)
            if pd.isna(val) or val is None:
                row_cells.append(Paragraph("-", cell_style_right))
            elif col in groupby_cols:
                row_cells.append(Paragraph(f"<b>{str(val)}</b>", cell_style_left))
            elif 'pct_change' in col:
                color_hex = '#DC2626' if val < 0 else ('#16A34A' if val > 0 else '#334155')
                pct_style = ParagraphStyle(
                    'PctCol', parent=cell_style_right,
                    textColor=colors.HexColor(color_hex)
                )
                row_cells.append(Paragraph(f"{val:+.1f}%" if val != 0 else "-", pct_style))
            elif col in ('san_luong', 'san_luong_prev', 'san_luong_yoy', 'so_kh', 'so_kh_prev', 'so_kh_yoy'):
                row_cells.append(Paragraph(f"{int(val):,}", cell_style_right))
            elif 'khoi_luong_thuc' in col:
                row_cells.append(Paragraph(f"{val/1000.0:,.1f} kg", cell_style_right))
            elif 'cuoc_' in col:
                row_cells.append(Paragraph(format_money_short(val), cell_style_right))
            else:
                row_cells.append(Paragraph(str(val), cell_style_left))
        table_data.append(row_cells)
        
    # Thêm dòng tổng cộng
    tot_row = []
    for idx, col in enumerate(columns):
        if idx == 0:
            tot_row.append(Paragraph("<b>Tổng cộng</b>", cell_style_left))
        elif idx < len(groupby_cols):
            tot_row.append(Paragraph("", cell_style_left))
        else:
            # Tính sum
            if 'pct_change' in col:
                tot_row.append(Paragraph("-", cell_style_right))
            else:
                raw_sum = df[col].sum() if col in df.columns else 0
                if col in ('san_luong', 'san_luong_prev', 'san_luong_yoy', 'so_kh', 'so_kh_prev', 'so_kh_yoy'):
                    tot_row.append(Paragraph(f"<b>{int(raw_sum):,}</b>", cell_style_right_bold))
                elif 'khoi_luong_thuc' in col:
                    tot_row.append(Paragraph(f"<b>{raw_sum/1000.0:,.1f} kg</b>", cell_style_right_bold))
                elif 'cuoc_' in col:
                    tot_row.append(Paragraph(f"<b>{format_money_short(raw_sum)}</b>", cell_style_right_bold))
                else:
                    tot_row.append(Paragraph("", cell_style_right))
    table_data.append(tot_row)
    
    # Thiết kế style cho bảng dữ liệu PDF
    col_widths = []
    # Tính toán độ rộng cột tự động dựa trên tổng số cột để vừa trang A4 ngang (760 pt khả dụng)
    total_width_avail = 760
    num_cols = len(columns)
    
    # Phân bổ chiều rộng
    for col in columns:
        if col in groupby_cols:
            col_widths.append(110) # Chiều rộng cột nhóm
        elif 'pct_change' in col:
            col_widths.append(50) # Cột % hẹp hơn
        elif 'cuoc_' in col:
            col_widths.append(70) # Cột tiền
        else:
            col_widths.append(60) # Cột số lượng/khối lượng
            
    # Chuẩn hóa độ rộng cột để khớp với chiều rộng khả dụng
    scale_factor = total_width_avail / sum(col_widths)
    col_widths = [w * scale_factor for w in col_widths]
    
    pdf_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056B3')), # Header màu bưu điện
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ])
    
    # Xen kẽ màu dòng dữ liệu
    for i in range(1, len(table_data) - 1):
        if i % 2 == 1:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F8FAFC'))
            
    # Highlight dòng tổng cộng
    table_style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0'))
    table_style.add('TOPPADDING', (0, -1), (-1, -1), 6)
    table_style.add('BOTTOMPADDING', (0, -1), (-1, -1), 6)
    
    pdf_table.setStyle(table_style)
    elements.append(pdf_table)
    
    # Hạn chế số lượng dòng nếu quá 60 dòng
    if len(df) > 60:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<i>Lưu ý: PDF chỉ hiển thị 60 dòng dữ liệu đầu tiên trên tổng số {len(df)} dòng. Vui lòng xuất Excel để xem chi tiết đầy đủ.</i>", filter_style))
        
    doc.build(elements)
    return output.getvalue()


def generate_customer_excel(df: pd.DataFrame, filter_info_str: str) -> bytes:
    """
    Tạo báo cáo Excel chuyên nghiệp với header 2 tầng và dòng tổng cộng cho dữ liệu Chi tiết Khách hàng (CMS).
    """
    import re
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Chi tiết Khách hàng"
    
    font_name = "Arial"
    
    # 1. Tiêu đề báo cáo
    ws.merge_cells("A1:H1")
    ws["A1"] = "BÁO CÁO CHI TIẾT DOANH THU THEO KHÁCH HÀNG (CMS)"
    ws["A1"].font = Font(name=font_name, size=14, bold=True, color="003366")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40
    
    # 2. Thông tin bộ lọc
    ws["A3"] = "Thông tin bộ lọc:"
    ws["A3"].font = Font(name=font_name, size=11, bold=True, italic=True, color="555555")
    
    ws["A4"] = f"• Bộ lọc áp dụng: {filter_info_str}"
    ws["A4"].font = Font(name=font_name, size=10, italic=True)
    
    ws["A5"] = f"• Ngày xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    ws["A5"].font = Font(name=font_name, size=10, italic=True)
    
    # 3. Phân tích các cột
    base_cols = ['cms', 'loai_kh', 'hop_dong', 'buu_cuc_list']
    pivot_cols = [c for c in df.columns if c not in base_cols and not c.startswith('Tổng')]
    total_cols = [c for c in ['Tổng SL', 'Tổng KL', 'Tổng Cước TT', 'Tổng Cước VAT'] if c in df.columns]
    
    columns = base_cols + pivot_cols + total_cols
    num_cols = len(columns)
    
    # 4. Thiết lập Header 2 tầng ở hàng 7 và 8
    row_1 = 7
    row_2 = 8
    
    ws.row_dimensions[row_1].height = 25
    ws.row_dimensions[row_2].height = 25
    
    col_labels = {
        'cms': 'Mã khách hàng',
        'loai_kh': 'Loại khách hàng',
        'hop_dong': 'Trạng thái HĐ',
        'buu_cuc_list': 'Danh sách Bưu cục',
    }
    
    # Cột cơ bản: Gộp đứng
    for c_idx in range(1, 5):
        col_letter = get_column_letter(c_idx)
        ws.merge_cells(f"{col_letter}{row_1}:{col_letter}{row_2}")
        col_name = columns[c_idx - 1]
        ws.cell(row=row_1, column=c_idx, value=col_labels.get(col_name, col_name))
        
    # Cột dịch vụ: Gộp ngang theo nhóm dịch vụ
    def get_group_name(col):
        match = re.match(r'^\[(.*?)\]', col)
        return match.group(1) if match else "Khác"
        
    current_g_name = None
    g_start_idx = None
    
    for idx, col in enumerate(pivot_cols, start=5):
        g_name = get_group_name(col)
        if g_name != current_g_name:
            if current_g_name is not None:
                start_letter = get_column_letter(g_start_idx)
                end_letter = get_column_letter(idx - 1)
                ws.merge_cells(f"{start_letter}{row_1}:{end_letter}{row_1}")
                ws.cell(row=row_1, column=g_start_idx, value=current_g_name)
            current_g_name = g_name
            g_start_idx = idx
            
        metric_short = col.split(']')[-1].strip()
        metric_label_map = {
            'SL': 'Sản lượng (SL)',
            'KL': 'Khối lượng (KL-kg)',
            'Cước TT': 'Cước TT',
            'Cước VAT': 'Cước gồm VAT'
        }
        ws.cell(row=row_2, column=idx, value=metric_label_map.get(metric_short, metric_short))
        
    # Merge nhóm dịch vụ cuối cùng
    if current_g_name is not None and g_start_idx is not None:
        start_letter = get_column_letter(g_start_idx)
        end_letter = get_column_letter(4 + len(pivot_cols))
        ws.merge_cells(f"{start_letter}{row_1}:{end_letter}{row_1}")
        ws.cell(row=row_1, column=g_start_idx, value=current_g_name)
        
    # Cột Tổng cộng: Gộp ngang
    if total_cols:
        start_tot_idx = 5 + len(pivot_cols)
        end_tot_idx = start_tot_idx + len(total_cols) - 1
        start_letter = get_column_letter(start_tot_idx)
        end_letter = get_column_letter(end_tot_idx)
        ws.merge_cells(f"{start_letter}{row_1}:{end_letter}{row_1}")
        ws.cell(row=row_1, column=start_tot_idx, value="Tổng cộng")
        
        total_label_map = {
            'Tổng SL': 'Tổng Sản lượng',
            'Tổng KL': 'Tổng Khối lượng (kg)',
            'Tổng Cước TT': 'Tổng Cước TT',
            'Tổng Cước VAT': 'Tổng Cước gồm VAT'
        }
        for idx, col in enumerate(total_cols, start=start_tot_idx):
            ws.cell(row=row_2, column=idx, value=total_label_map.get(col, col))
            
    # Áp dụng Style cho Header
    header_fill = PatternFill(start_color="0056B3", end_color="0056B3", fill_type="solid")
    header_font = Font(name=font_name, size=10, bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border_thin = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)
    
    for col_idx in range(1, num_cols + 1):
        cell1 = ws.cell(row=row_1, column=col_idx)
        cell2 = ws.cell(row=row_2, column=col_idx)
        for cell in (cell1, cell2):
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_align
            cell.border = cell_border
            
    # 5. Điền dữ liệu
    data_start_row = row_2 + 1
    for r_idx, row_data in enumerate(df.to_dict('records'), start=data_start_row):
        ws.row_dimensions[r_idx].height = 20
        is_odd = (r_idx % 2 == 1)
        row_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") if is_odd else PatternFill(fill_type=None)
        
        for c_idx, col_name in enumerate(columns, start=1):
            val = row_data.get(col_name, None)
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = cell_border
            if row_fill.fill_type:
                cell.fill = row_fill
                
            if pd.isna(val) or val is None:
                cell.value = "-"
                cell.alignment = Alignment(horizontal="center")
            elif col_name == 'cms':
                cell.value = str(val)
                cell.alignment = Alignment(horizontal="left", vertical="center")
                cell.font = Font(name=font_name, size=9, bold=True)
            elif col_name in ['loai_kh', 'hop_dong']:
                cell.value = str(val)
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.font = Font(name=font_name, size=9)
            elif col_name == 'buu_cuc_list':
                cell.value = str(val)
                cell.alignment = Alignment(horizontal="left", vertical="center")
                cell.font = Font(name=font_name, size=9)
            elif 'SL' in col_name or 'Tổng SL' == col_name:
                cell.value = int(val)
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.font = Font(name=font_name, size=9)
            elif 'KL' in col_name or 'Tổng KL' == col_name:
                cell.value = float(val)
                cell.number_format = '#,##0.0'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.font = Font(name=font_name, size=9)
            elif 'Cước' in col_name or 'Tổng Cước' in col_name:
                cell.value = float(val)
                cell.number_format = '#,##0" đ"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.font = Font(name=font_name, size=9)
            else:
                cell.value = val
                cell.alignment = Alignment(horizontal="left", vertical="center")
                
    # 6. Dòng tổng cộng ở cuối
    total_row = data_start_row + len(df)
    ws.row_dimensions[total_row].height = 22
    total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    
    ws.merge_cells(f"A{total_row}:D{total_row}")
    cell_tot_lbl = ws.cell(row=total_row, column=1, value="Tổng cộng")
    cell_tot_lbl.font = Font(name=font_name, size=10, bold=True, color="000000")
    cell_tot_lbl.alignment = Alignment(horizontal="left", vertical="center")
    
    for c_idx in range(1, num_cols + 1):
        cell = ws.cell(row=total_row, column=c_idx)
        cell.fill = total_fill
        cell.border = cell_border
        if c_idx > 4:
            cell.font = Font(name=font_name, size=9, bold=True)
            col_letter = get_column_letter(c_idx)
            cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row - 1})"
            cell.alignment = Alignment(horizontal="right", vertical="center")
            
            col_name = columns[c_idx - 1]
            if 'SL' in col_name or 'Tổng SL' == col_name:
                cell.number_format = '#,##0'
            elif 'KL' in col_name or 'Tổng KL' == col_name:
                cell.number_format = '#,##0.0'
            elif 'Cước' in col_name or 'Tổng Cước' in col_name:
                cell.number_format = '#,##0" đ"'
                
    # 7. Tự động điều chỉnh độ rộng cột
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in [1, 2, 3, 4, 5, 6, 7, 8]:
                continue
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
