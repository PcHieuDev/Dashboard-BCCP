# RRI REPORT: Dashboard-BCCP (Phase 6)
Generated: 2026-06-02
Complexity: Medium (project) → Small (scope thay đổi lần này)
Questions Asked: 15 across 5 personas

## REQUIREMENTS MATRIX
| REQ-ID  | Requirement                                                        | Source    | Priority | Persona        |
|---------|--------------------------------------------------------------------|-----------|----------|----------------|
| REQ-016 | Cập nhật cấu trúc CSV thêm cột `nhom_chinh`, thêm Upload UI trên web | Q-13, Q-14 | P0     | Operator       |
| REQ-017 | `sync_mappings.py` target `dim_dichvu`, tự backup DB trước khi chạy  | Q-11      | P0       | Developer      |
| REQ-018 | Fix lỗi `ten_Cum` → `ten_cum` trong global_metrics.py               | Scan GAP-1| P0       | Developer      |
| REQ-019 | Trang chủ: DataTable YTD 4 nấc màu (<60 đỏ, 60-80 cam, 80-100 vàng, >100 xanh), %HT = "-" nếu KH=0 | Q-01, Q-09 | P1 | End User |
| REQ-020 | Routing `/bccp/kpi` → `/bccp`. Xóa TOÀN BỘ nút PDF toàn dự án      | Q-02      | P1       | End User       |
| REQ-021 | Trang `/hcc/revenue` clone BCCP với bộ lọc nâng cao, fix "-" cho % kỳ trước rỗng | Q-05, Q-08 | P1 | End User |

## AUTO-ANSWERED (from Scan)
- AUTH: Flask-Login đã tích hợp, hiện BYPASS → Không cần thay đổi
- DB: SQLite + dim_dichvu schema đã có cột nhom_chinh → Reuse schema
- CACHE: lru_cache đã dùng trong utils.py/connection.py → Mở rộng cho global_metrics
- COMPONENTS: data_table.py + sidebar.py → Reuse cho HCC revenue page

## DECISIONS LOG
| Decision | Options Considered                                     | Chosen                        | Rationale                                      |
|----------|-------------------------------------------------------|-------------------------------|-------------------------------------------------|
| D-011    | Biểu đồ Bar YTD vs DataTable                          | DataTable 4 cột               | User yêu cầu số liệu tường minh theo từng Cụm  |
| D-012    | HCC 1 trang vs 2 trang (/hcc + /hcc/revenue)          | 2 trang                       | Nhất quán với BCCP (tổng quan riêng, chi tiết riêng) |
| D-013    | sync_mappings → dim_spdv (cũ) vs dim_dichvu (mới)     | dim_dichvu trực tiếp           | Bỏ bảng trung gian lỗi thời, hỗ trợ 4 nhóm DV  |
| D-014    | Fake data PHBC vs User tự nhập sau                     | User tự nhập                  | Tuân thủ quy trình nhập liệu chuẩn qua CSV      |
| D-015    | Giữ PDF vs Bỏ PDF                                      | Bỏ hoàn toàn PDF              | User chỉ dùng Excel, giảm tải UI và dependencies |
| D-016    | Sync qua cmd vs Tích hợp UI                            | UI Import (Upload + nút Sync) | Tiện Operator, không cần IT gõ lệnh             |
| D-017    | % tăng trưởng 0% vs "-" khi mẫu số rỗng               | Hiển thị "-"                  | Chính xác hơn, tránh hiểu nhầm                  |

## OPEN QUESTIONS
- Không còn câu hỏi mở. Tất cả 15 câu đã được trả lời.
