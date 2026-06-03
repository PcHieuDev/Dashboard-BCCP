# Context — Nâng cấp Module BCCP (Phase 8)

## 1. Project Overview
Dashboard doanh thu bưu chính chuyển phát phục vụ 20+ người dùng. Đang nâng cấp module `/bccp` với các trang mới (KH mới, KHHH) và tái cấu trúc trang hiện tại.

## 2. Tech Stack
- **Language**: Python 3.13/3.14
- **Framework**: Dash + dash-bootstrap-components + Plotly
- **Database**: SQLite tại `E:\OneDrive\z.Database-TTKD-Data\dashboard.db`
- **Auth**: Flask-Login (hiện đang bypass)
- **Config**: `config/settings.py` chứa `DB_PATH`

## 3. Architecture

### Cấu trúc thư mục:
```
E:\Projects\worktrees\Dashboard-BCCP\feat-bccp-upgrade\
├── config/settings.py          ← DB_PATH, cấu hình chung
├── analytics/                  ← Logic tính toán nghiệp vụ
│   ├── kpi_metrics.py          ← Tính KPI BCCP (revenue, classify_customers)
│   ├── customer_classifier.py  ← Phân loại KH: Vãng lai / KHM-Tái bán / Hiện hữu
│   ├── global_metrics.py       ← Tính doanh thu 4 nhóm DV (BCCP/HCC/TCBC/PPBL)
│   └── [MỚI] new_customer_calculator.py
│   └── [MỚI] retention_metrics.py
├── etl/importer.py             ← Import file Excel vào DB
├── dash_app/
│   ├── app.py                  ← Entry point, routing, register callbacks
│   ├── assets/style.css        ← CSS chung
│   ├── components/
│   │   ├── sidebar.py          ← Menu điều hướng + bộ lọc
│   │   ├── kpi_cards.py        ← Component thẻ KPI tái sử dụng
│   │   └── data_table.py       ← Component bảng dữ liệu
│   ├── pages/                  ← Layout các trang
│   │   ├── kpi_page.py         ← /bccp — KPI cards
│   │   ├── charts.py           ← /bccp/charts — SẼ XÓA
│   │   ├── revenue_detail.py   ← /bccp/revenue — SẼ XÓA
│   │   ├── customer_detail.py  ← /bccp/customer — SẼ CẬP NHẬT
│   │   ├── alerts.py           ← /bccp/alerts — GIỮ NGUYÊN
│   │   └── import_data.py      ← /import — GIỮ NGUYÊN
│   └── callbacks/              ← Xử lý tương tác
│       ├── kpi_callbacks.py    ← Callback cho /bccp
│       ├── charts_callbacks.py ← SẼ XÓA
│       ├── revenue_callbacks.py← SẼ XÓA
│       ├── customer_callbacks.py ← SẼ CẬP NHẬT
│       ├── import_callbacks.py ← SẼ CẬP NHẬT (thêm trigger)
│       ├── alerts_callbacks.py ← GIỮ NGUYÊN
│       ├── utils.py            ← format_revenue(), normalize_compare_mode()
│       └── export_helpers.py   ← Xuất Excel/PDF
├── data/
│   ├── mapping-BC-BDX-Cum.csv  ← Mapping ma_BC → ma_BDX → ten_BDX → ten_Cum
│   └── ke-hoach-2026/          ← File KH (đã import vào DB)
└── scripts/
    └── import_ke_hoach_2026.py ← Script import KH (đã chạy xong)
```

### Database Schema (các bảng liên quan):
- `transactions` (829K rows): Giao dịch BCCP — cms, buu_cuc, san_pham_dv, cuoc_tt_tong, thang_du_lieu, nam_du_lieu
- `transactions_phbc`: Giao dịch PHBC — ma_buu_cuc, doanh_thu
- `plans` (19,884 rows): KH doanh thu — nhom_dich_vu='BCCP'/'PHBC', ten_dich_vu, ma_buu_cuc, ke_hoach_doanh_thu
- `plans_new_customer` (2,472 rows): KH bán mới — ma_xa, nhom_dich_vu, ke_hoach_doanh_thu
- `dim_buucuc` (636 rows): ma_bc, ten_buu_cuc, ten_bdx, ten_cum
- `dim_dichvu`: nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu
- `new_customers` ← **SẼ TẠO MỚI** bởi TIP-001

### Mapping quan trọng:
- `mapping-BC-BDX-Cum.csv`: Cột `ma_BDX` (4 chữ số) = mã xã = khớp với `plans_new_customer.ma_xa`
- Mỗi `ma_BDX` → nhiều `ma_BC` (bưu cục) → 1 `ten_BDX` → 1 `ten_Cum`
- `dim_buucuc` cũng có `ten_bdx`, `ten_cum` nhưng KHÔNG có `ma_BDX` riêng. Mapping qua `substr(ma_bc, 1, 4)` hoặc qua CSV

### Logic phân loại KH (đã có trong `customer_classifier.py`):
- **Vãng lai**: CMS null hoặc bắt đầu `VANGLAI_`
- **KHM/Tái bán**: Không có giao dịch trong 3 tháng liền trước
- **Hiện hữu**: Có giao dịch trong 3 tháng liền trước

## 4. Key Decisions
- Bảng `new_customers` lưu từ T10/2025 (data có từ T05/2025, đủ 3 tháng lookback)
- Import lại file BCCP → xóa + tính lại new_customers cho tháng đó
- Bộ lọc DV BCCP bỏ khỏi Sidebar, đặt inline trong `/bccp/customer`
- File CSV tỉ lệ phân kỳ có format đặc biệt (dấu phẩy = decimal) — đã xử lý xong
- KH PHBC lưu trong `plans` với `nhom_dich_vu='PHBC'`, `ma_buu_cuc` = tên Cụm

## 5. Patterns & Conventions
- **Callback pattern**: 1 callback lớn nhận Input từ sidebar filters → trả multi-Output cho trang
- **Sidebar inputs**: `sidebar-year`, `sidebar-month-select`, `sidebar-compare-mode`, `sidebar-cum`
- **Format doanh thu**: Dùng `format_revenue()` từ `callbacks/utils.py`
- **KPI card**: Dùng `make_kpi_card_layout()` từ `components/kpi_cards.py`
- **DataTable style**: Xem mẫu trong `global_callbacks.py` — header xám, dòng đầu highlight, phân trang
- **Commit convention**: `feat(bccp): TIP-bccp-XXX — mô tả`
- **Encoding**: UTF-8 toàn bộ, `sys.stdout.reconfigure(encoding='utf-8')` cho scripts
