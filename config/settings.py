# -*- coding: utf-8 -*-
"""
Cấu hình chung cho hệ thống BCCP Database.
Tất cả đường dẫn được tính relative từ vị trí file settings.py này.
"""

from pathlib import Path

# Thư mục gốc dự án: z.Database-TTKD/
_CONFIG_DIR = Path(__file__).resolve().parent          # config/
PROJECT_DIR = _CONFIG_DIR.parent                       # z.Database-TTKD/

# Database SQLite (OneDrive — tự đồng bộ giữa 2 máy)
# Tách biệt khỏi mã nguồn để Git không track file DB nặng
DATA_DIR = Path(r"E:\OneDrive\z.Database-TTKD-Data")
DB_PATH = DATA_DIR / "dashboard.db"
PHAN_QUYEN_PATH = DATA_DIR / "phan_quyen_url.xlsx"

# Thư mục chứa dữ liệu gốc đã gộp theo tháng (absolute path)
DATA_PATH = Path(r"E:\OneDrive\TTKD - Công việc hàng ngày\0. KHM, tai ban hang thang\chi-tiet-KH-hopdong-loaidichvu\du-lieu-goc-4.2.4-casreport\ket-qua-gop-tung-thang")

# File mapping sản phẩm dịch vụ và địa lý
MAPPING_PATH = PROJECT_DIR / "data" / "mapping-spdv.csv"
MAPPING_GEOGRAPHY_PATH = PROJECT_DIR / "data" / "mapping-BC-BDX-Cum.csv"

# ==============================================================================
# CẤU HÌNH EXCEL
# ==============================================================================
# Dòng bắt đầu chứa data (1-indexed), header là 2 dòng đầu
EXCEL_DATA_START_ROW = 3

# Số cột dữ liệu (A-V = 22 cột)
EXCEL_NUM_COLS = 22

# Mapping cột Excel → tên cột Database (Thứ tự cột A → V)
COLUMN_NAMES = [
    'stt',              # A - STT
    'cms',              # B - Mã khách hàng
    'ma_hop_dong',      # C - Mã hợp đồng
    'buu_cuc',          # D - Bưu cục (mã 6 chữ số)
    'san_pham_dv',      # E - Sản phẩm dịch vụ
    'ngay_chap_nhan',   # F - Ngày chấp nhận (dd/mm/yyyy)
    'san_luong',        # G - Sản lượng
    'khoi_luong_thuc',  # H - Khối lượng thực
    'khoi_luong_tinh_cuoc',  # I - Khối lượng tính cước
    'cuoc_cb_cp',       # J - Cước CB Chuyển phát chưa VAT
    'cuoc_cb_gtgt',     # K - Cước CB GTGT CP chưa VAT
    'cuoc_cb_cod',      # L - Cước CB COD chưa VAT
    'cuoc_cb_tong',     # M - Cước CB Tổng chưa VAT
    'cuoc_tt_cp',       # N - Cước TT Chuyển phát chưa VAT
    'cuoc_tt_gtgt',     # O - Cước TT GTGT CP
    'cuoc_tt_cod',      # P - Cước TT COD
    'cuoc_tt_tong',     # Q - Cước TT Tổng chưa VAT ★ DOANH THU CHÍNH
    'thue_vat',         # R - Thuế VAT
    'cuoc_tt_gom_vat',  # S - Tổng cước gồm VAT
    'cuoc_chenh_lech',  # T - Cước chênh lệch
    'tien_cod',         # U - Tiền COD
    'nho_thu_khac',     # V - Nhờ thu khác
]

# CMS bất thường là tên người thay vì mã → giữ nguyên, log warning
ABNORMAL_CMS = [
    'BÙI THỊ NHUNG',
    'nguyễn mạnh cường',
]

# Cột doanh thu chính để tính toán
REVENUE_COLUMN = "cuoc_tt_tong"

# ==============================================================================
# CẤU HÌNH ĐA DỊCH VỤ (MULTI-SERVICE)
# ==============================================================================
SERVICE_GROUPS = ["BCCP", "Hành chính công", "Tài chính Bưu chính", "Phân phối bán lẻ"]

SERVICE_COLORS = {
    "BCCP": "#3B82F6",              # Xanh dương
    "Hành chính công": "#10B981",   # Xanh lá
    "Tài chính Bưu chính": "#F59E0B", # Vàng cam
    "Phân phối bán lẻ": "#8B5CF6"   # Tím
}

SERVICE_TABLES = {
    "BCCP": "transactions",
    "Hành chính công": "transactions_hcc",
    "Tài chính Bưu chính": "transactions_tcbc",
    "Phân phối bán lẻ": "transactions_ppbl"
}
