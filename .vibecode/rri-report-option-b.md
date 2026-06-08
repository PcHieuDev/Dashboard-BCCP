# RRI REPORT: Nâng cấp chuẩn hóa Schema `dim_dichvu` (Option B)
Generated: 2026-06-08
Complexity: High
Persona: Data Architect & Contractor

## 1. MỤC TIÊU (REQUIREMENTS)
- **Tái cấu trúc (Refactoring)** bảng danh mục `dim_dichvu` để áp dụng triệt để nguyên tắc dùng Mã (Code) thay cho Tên (Name) khi truy vấn.
- Cấu trúc lại toàn bộ hệ thống Dash Callbacks và SQL engine để tương thích với Schema mới.
- Triển khai an toàn trên một `git worktree` riêng biệt (`feat-option-B`), chạy trên một cổng khác (8051) để không ảnh hưởng đến hệ thống hiện tại.

## 2. ĐỀ XUẤT SCHEMA BẢNG `dim_dichvu` MỚI
Cấu trúc cũ: `id, nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu`
Cấu trúc mới: `id, ma_nhom_chinh, ten_nhom_chinh, ma_nhom_dv, ten_nhom_dv, ma_dich_vu, ten_dich_vu`

### Bảng Mã hóa (Mapping Table) đề xuất:

**A. Cấp 1: Nhóm Chính (Nhóm dịch vụ cấp 1)**
| Mã Nhóm Chính (`ma_nhom_chinh`) | Tên Nhóm Chính (`ten_nhom_chinh`) |
|---------------------------------|-----------------------------------|
| `BCCP`                          | Bưu chính chuyển phát             |
| `HCC`                           | Hành chính công                   |
| `TCBC`                          | Tài chính bưu chính               |
| `PPBL`                          | Phân phối bán lẻ                  |

**B. Cấp 2: Nhóm Dịch Vụ (Nhóm dịch vụ cấp 2)**
| `ma_nhom_chinh` | Mã Nhóm DV (`ma_nhom_dv`) | Tên Nhóm Dịch Vụ (`ten_nhom_dv`) |
|-----------------|---------------------------|----------------------------------|
| `BCCP`          | `TT`                      | Truyền thống                     |
| `BCCP`          | `TMDT`                    | TMĐT                             |
| `BCCP`          | `QT`                      | Quốc tế                          |
| `BCCP`          | `LOG`                     | Logistics                        |
| `BCCP`          | `BCK`                     | Bưu chính khác                   |
| `BCCP`          | `PHBC`                    | Phát hành báo chí                |
| `HCC`           | `HCC_CP`                  | Chuyển phát HCC                  |
| `HCC`           | `HCC_BHXH`                | Chi trả lương hưu, bảo hiểm xã hội |
| `TCBC`          | `TCBC_TK`                 | Tiết kiệm                        |
| `PPBL`          | `PPBL_HBS`                | Hàng bán sỉ                      |
*(Các dịch vụ khác tương tự, quy tắc mã hóa là viết tắt không dấu, chữ hoa, ngăn cách bằng dấu gạch dưới `_`)*

## 3. PHÂN TÍCH TÁC ĐỘNG BÊN TRONG HỆ THỐNG
1. **Dữ liệu gốc (`dim_dichvu.csv`)**: Phải viết 1 script migration nhỏ để đọc file csv cũ, thêm các cột mã này vào và xuất ra csv mới.
2. **Cơ sở dữ liệu (`dashboard.db`)**: Phải sửa lại bảng `dim_dichvu`, đồng thời các bảng `agg_monthly`, `agg_weekly` cũng phải chạy lệnh UPDATE để đổi từ Tên sang Mã, hoặc Re-build lại toàn bộ bảng Aggregation từ `transactions`.
3. **Module `analytics/revenue.py`**: Thay vì nhận `nhom_dv=['Truyền thống']`, giờ sẽ nhận `ma_nhom_dv=['TT']`.
4. **Module Callbacks**: Giao diện Dropdown (UI) vẫn hiện chữ "Truyền thống", nhưng thuộc tính `value` sẽ là `"TT"`.

## 4. QUY TRÌNH DEPLOY LÊN WORKTREE (GIT)
- Khởi tạo thư mục: `git worktree add E:\Projects\worktrees\Dashboard-BCCP\feat-option-B -b feat-dim-dichvu`
- Thợ thi công vào thư mục này:
  1. Cấu hình chạy trên cổng **8051** (Sửa tham số `port=8050` thành `port=8051` trong file run).
  2. Viết script migration biến đổi CSV và update lại SQLite.
  3. Sửa toàn bộ SQL và Callback logic.

## 5. OPEN QUESTIONS (CÂU HỎI RRI)
1. **[OQ-001] Migration Dữ liệu**: Sếp muốn dùng 1 DB SQLite chung (`dashboard.db`) cho cả 2 nhánh (nếu vậy khi nhánh B thay đổi schema thì nhánh A có thể bị sụp), HAY tạo ra 1 file copy DB mới (ví dụ `dashboard_v2.db`) dành riêng cho nhánh B để an toàn tuyệt đối?
2. **[OQ-002] Tên Mã Hóa**: Với các mã nhóm dịch vụ cấp 2 (như `TT`, `TMDT`), Sếp có muốn tiền tố nhóm chính đằng trước cho đồng bộ không (Ví dụ: `BCCP_TT`, `BCCP_TMDT`) hay để ngắn gọn (`TT`, `TMDT`) là đủ ạ?
