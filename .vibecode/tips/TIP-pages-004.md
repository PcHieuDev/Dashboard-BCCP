# TIP-pages-004: Trang Retention (layout + callbacks + Churn + 3 bảng)

## HEADER
- TIP-ID: TIP-pages-004
- Branch: feat/pages-redesign
- Project: Dashboard BCCP v2.0
- Module: Pages / Callbacks / Analytics
- Depends on: feat/db-summary (summary tables)
- Priority: P0
- Estimated effort: 90 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-pages-redesign
- Key files to reference:
  - `dash_app/pages/retention.py` → layout hiện tại
  - `dash_app/callbacks/retention_callbacks.py` → callbacks hiện tại
  - `analytics/retention_metrics.py` → logic KHHH, biến động, churn alerts hiện tại
  - `dash_app/callbacks/export_helpers.py` → pattern xuất Excel

## TASK
Tái cấu trúc trang Retention theo định nghĩa nghiệp vụ mới.

## SPECIFICATIONS

### Layout mới (từ trên xuống):

#### Section 1: 4 KPI Cards biến động
4 cards ngang:
- 📈 **Tăng**: Số KH + Tổng DT thay đổi (dương)
- 📉 **Giảm**: Số KH + Tổng DT thay đổi (âm)
- 🚪 **Rời bỏ**: Số KH + Tổng DT mất
- ✅ **Duy trì (Ổn định)**: Số KH

#### Section 2: Bảng chi tiết KH Doanh thu Tăng
- Tiêu đề + nút [📥 Xuất Excel]
- Cột: Tên cụm | Tên xã | Mã CMS | SL kỳ này | DT kỳ này | SL kỳ trước | DT kỳ trước | Chênh lệch DT

#### Section 3: Bảng chi tiết KH Doanh thu Giảm
- Cùng cấu trúc Section 2

#### Section 4: Bảng chi tiết KH Rời bỏ
- Cột: Tên cụm | Tên xã | Mã CMS | SL gần nhất | DT gần nhất (tháng gần nhất có DT)

### Sửa `analytics/retention_metrics.py` — Định nghĩa mới

#### Churn (Rời bỏ) — ĐỔI ĐỊNH NGHĨA
- **CŨ**: KHHH tháng T-1 không phát sinh ở tháng T
- **MỚI**: KH có doanh thu dương trong BẤT KỲ tháng nào trong 3 tháng gần nhất (T-1, T-2, T-3), nhưng tháng T KHÔNG có doanh thu
- DT thay đổi = DT của tháng gần nhất có phát sinh (không phải chỉ T-1)

#### Duy trì (Ổn định) — ĐỔI ĐỊNH NGHĨA
- **CŨ**: DT tháng T == DT tháng T-1
- **MỚI**: DT tháng T == DT tháng T-1 **VÀ** DT phải dương (> 0)

#### Tăng/Giảm — GIỮ NGUYÊN
- Tăng: KHHH có DT(T) > DT(T-1) > 0
- Giảm: KHHH có 0 < DT(T) < DT(T-1)

#### Hàm mới cần tạo
1. `get_khhh_changes_v2(db_path, nam, thang, cum, bdx)` → dict với 4 nhóm + danh sách chi tiết
   - Trả về: `{'tang': [list_of_dicts], 'giam': [...], 'roi_bo': [...], 'duy_tri_count': int}`
   - Mỗi dict trong list: `{cms, ten_cum, ten_bdx, sl_ky_nay, dt_ky_nay, sl_ky_truoc, dt_ky_truoc}`
   - Rời bỏ: `{cms, ten_cum, ten_bdx, sl_gan_nhat, dt_gan_nhat, thang_gan_nhat}`

2. `get_weekly_changes(db_path, year, week_start, week_end, cum, bdx)` → cùng format nhưng so sánh tuần-tuần
   - Tăng: DT tuần này > DT tuần trước > 0
   - Giảm: 0 < DT tuần này < DT tuần trước
   - Rời bỏ: Tuần trước có DT, tuần này không có
   - Duy trì: DT bằng nhau và > 0

### Bỏ hoàn toàn
- Phần Tổng hợp Retention Rate (cards cũ)
- Biểu đồ biến động KHHH
- Phần Churn Alerts (bảng + filters)

### Xuất Excel
- Mỗi bảng có nút xuất riêng
- Dùng pattern từ `export_helpers.py`: dcc.Download + callback trigger
- File name: `KH_Tang_{thang}_{nam}.xlsx`, `KH_Giam_...`, `KH_Roibo_...`

## ACCEPTANCE CRITERIA
- Given: DB có dữ liệu transactions T01-T06/2026
- When: Lọc Tháng T05/2026
- Then:
  - 4 cards biến động hiện đúng số liệu
  - 3 bảng chi tiết có dữ liệu, cột đúng format
  - Nút xuất Excel tải file đúng

- Given: Lọc Tuần 20
- When: Trang render
- Then: So sánh tuần 20 vs tuần 19, 3 bảng chi tiết đúng

- Given: KH có DT ở T03 và T04 nhưng không có ở T05
- When: Lọc T05
- Then: KH đó xuất hiện trong bảng Rời bỏ, DT gần nhất = DT T04

## CONSTRAINTS
- KHÔNG giữ lại bất kỳ phần nào bị bỏ (retention rate, biểu đồ, churn alerts)
- GIỮ hàm cũ `get_retention_stats()` nhưng KHÔNG gọi từ callback (để backward compat nếu cần)
- Hàm mới đặt tên `_v2` hoặc tên mới hoàn toàn để không xung đột
- Xuất Excel dùng pandas `to_excel()` qua BytesIO
