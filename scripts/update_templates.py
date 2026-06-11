# -*- coding: utf-8 -*-
import openpyxl
import os

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


def update_dich_vu_khac_template(filepath):
    logger.info(f"Updating {filepath}...")
    wb = openpyxl.load_workbook(filepath)
    
    # 1. Sheet DuLieu
    ws_data = wb['DuLieu']
    # Cột 3 (C) đổi thành "Mã dịch vụ"
    ws_data['C1'] = "Mã dịch vụ"
    # Dòng 2: HCC -> CT_LH (Chi trả lương hưu)
    ws_data['C2'] = "CT_LH"
    # Dòng 3: TCBC -> TK_TT (Tiết kiệm & Tín dụng)
    ws_data['C3'] = "TK_TT"
    
    # 2. Sheet HuongDan
    ws_guide = wb['HuongDan']
    # Ô A6: Tên dịch vụ -> Mã dịch vụ
    ws_guide['A6'] = "Mã dịch vụ"
    # Ô B6: Hướng dẫn
    ws_guide['B6'] = (
        "Mã dịch vụ viết tắt (Vd: CT_LH, TK_TT, B2B...). "
        "Tra cứu mã dịch vụ chính xác tại file ma_tham_chieu.xlsx, sheet 'Nhóm dịch vụ', "
        "cột 'Mã dịch vụ (Dùng nạp file)'."
    )
    
    wb.save(filepath)
    wb.close()
    logger.info("Done updating other services template.")

def update_ke_hoach_template(filepath):
    logger.info(f"Updating {filepath}...")
    wb = openpyxl.load_workbook(filepath)
    
    # 1. Sheet DuLieu_KeHoach
    ws_data = wb['DuLieu_KeHoach']
    
    # Điều chỉnh một số dòng dữ liệu ví dụ để đa dạng và đúng chuẩn mới
    # Dòng 2: 2026 | HCC | Chuyển phát HCC -> Giữ nguyên (nhưng đổi thành Hành chính công hoặc mã xã tương ứng nếu cần, thực tế Chuyển phát HCC là tên nhóm con hợp lệ)
    ws_data['C2'] = "Hành chính công"
    
    # Dòng 3: Đổi thành HCC | Chi trả
    ws_data['B3'] = "HCC"
    ws_data['C3'] = "Chi trả"
    ws_data['D3'] = 4673  # Mã xã
    ws_data['E3'] = 24000000
    
    # Dòng 4: Đổi thành HCC | Thu hộ
    ws_data['B4'] = "HCC"
    ws_data['C4'] = "Thu hộ"
    ws_data['D4'] = 4672  # Mã xã
    ws_data['E4'] = 36000000
    
    # Dòng 5: Đổi thành TCBC | Tiết kiệm & Tín dụng
    ws_data['B5'] = "TCBC"
    ws_data['C5'] = "Tiết kiệm & Tín dụng"
    ws_data['D5'] = 467500  # Mã bưu cục 6 số cho TCBC
    ws_data['E5'] = 120000000
    
    # Dòng 6: Đổi thành TCBC | Bảo hiểm
    ws_data['B6'] = "TCBC"
    ws_data['C6'] = "Bảo hiểm"
    ws_data['D6'] = 474100  # Mã bưu cục 6 số
    ws_data['E6'] = 48000000
    
    # Dòng 7: Đổi thành PPBL | Hàng tiêu dùng
    ws_data['B7'] = "PPBL"
    ws_data['C7'] = "Hàng tiêu dùng"
    ws_data['D7'] = 467100  # Mã bưu cục 6 số
    ws_data['E7'] = 96000000
    
    # Dòng 8: Đổi thành PPBL | Truyền thông - Phân phối
    ws_data['B8'] = "PPBL"
    ws_data['C8'] = "Truyền thông - Phân phối"
    ws_data['D8'] = 467600  # Mã bưu cục 6 số
    ws_data['E8'] = 60000000

    # Dòng 9: Đổi thành BCCP | TMĐT
    ws_data['B9'] = "BCCP"
    ws_data['C9'] = "TMĐT"
    ws_data['D9'] = 468000  # Mã bưu cục 6 số
    ws_data['E9'] = 300000000
    
    # 2. Sheet HuongDan
    ws_guide = wb['HuongDan']
    
    # Ô A2: Năm (*), Tháng (*) -> Năm (*)
    ws_guide['A2'] = "Năm (*)"
    # Ô B2: Hướng dẫn năm
    ws_guide['B2'] = "Năm giao kế hoạch (VD: 2026). Dữ liệu kiểu Số."
    
    # Ô A3: Nhóm Dịch Vụ (*) -> Nhóm Chính (*)
    ws_guide['A3'] = "Nhóm Chính (*)"
    # Ô B3: Hướng dẫn nhóm chính
    ws_guide['B3'] = "Chọn 1 trong các nhóm chính: BCCP, HCC, TCBC, PPBL, PHBC."
    
    # Ô A4: Tên Dịch Vụ -> Nhóm DV
    ws_guide['A4'] = "Nhóm DV"
    # Ô B4: Hướng dẫn nhóm DV
    ws_guide['B4'] = (
        "Tên nhóm dịch vụ con (Vd: 'Truyền thông', 'TMĐT' của BCCP; "
        "'Chi trả', 'Thu hộ' của HCC; 'Tiết kiệm & Tín dụng', 'Bảo hiểm' của TCBC; "
        "'Hàng tiêu dùng', 'Truyền thông - Phân phối' của PPBL). "
        "Tra cứu tại file ma_tham_chieu.xlsx, sheet 'Nhóm dịch vụ', cột 'Nhóm dịch vụ'."
    )
    
    # Ô B5: Hướng dẫn mã đơn vị
    ws_guide['B5'] = (
        "LƯU Ý QUAN TRỌNG VỀ CẤP ĐƠN VỊ GIAO KẾ HOẠCH:\n"
        "- Nhóm BCCP/TCBC/PPBL/PHBC: Điền Mã Bưu cục (6 số), VD: 472400\n"
        "- Nhóm HCC: Điền Mã Xã (4 số), VD: 4701 (Hoặc điền mã bưu cục nếu giao kế hoạch cấp bưu cục)\n"
        "- Nhóm PHBC: Có thể giao theo Mã Cụm (bắt đầu bằng CUM_), VD: CUM_VINH"
    )
    
    # Ô B6: Hướng dẫn Kế hoạch doanh thu
    ws_guide['B6'] = (
        "Mục tiêu doanh thu cả năm (VNĐ). Hệ thống sẽ tự động phân bổ ra 12 tháng "
        "theo tỷ lệ mùa vụ bưu điện. Dữ liệu kiểu Số."
    )
    
    wb.save(filepath)
    wb.close()
    logger.info("Done updating plan template.")

if __name__ == "__main__":
    dir_path = "data/mau-file-import"
    update_dich_vu_khac_template(os.path.join(dir_path, "mau_import_dich_vu_khac.xlsx"))
    update_ke_hoach_template(os.path.join(dir_path, "mau_import_ke_hoach.xlsx"))
