# CONTRACT: Dashboard Doanh thu BCCP (feat-ux-filters)

## DELIVERABLES
| # | Item | Details | Requirements |
|---|------|---------|--------------|
| 1 | Topbar Tinh gọn | Chỉ giữ Từ ngày-Đến ngày, Không gian, So sánh, Nút Áp dụng. | REQ-001 |
| 2 | Manual Load | 54 điểm Callbacks chuyển sang dùng State, trigger bởi btn-apply-filter. | REQ-002 |
| 3 | Core Data Refactor | `revenue.py` và `utils.py` chạy trên start_date/end_date. So sánh = Delta Days. | REQ-004, REQ-005 |
| 4 | Limit Date Selector | Chặn lịch không chọn quá 1 tháng ở trang KH Mới / KHHH. | REQ-003 |
| 5 | Trang Thống kê SPDV | Bảng báo cáo Sản lượng, Doanh thu, So sánh theo từng Gói cước. | REQ-006 |

## TECH STACK
Python 3.13, Dash, SQLite, pandas.

## TASK GRAPH SUMMARY
6 TIPs, estimated 150 minutes

## NOT INCLUDED
- Cấu trúc bảo mật và đăng nhập Flask-Login giữ nguyên (tạm bypass).
- Không động chạm đến Schema DB hiện có.
- Không sửa đổi màu sắc hay style chủ đạo của Dashboard hiện hành.

## CONFIRM
Reply "CONFIRM" hoặc "APPROVED" để nhận Task Graph và Branch Plan.
