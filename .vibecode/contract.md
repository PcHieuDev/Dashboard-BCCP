# CONTRACT: Dashboard BCCP (Nâng cấp Code)

## DELIVERABLES
| # | Item | Details | Requirements |
|---|------|---------|--------------|
| 1 | Hệ thống Logging | `config/logger.py`, ghi log ra file và console, dọn dẹp các lệnh `print()` cũ | REQ-001 |
| 2 | Môi trường Test | Thư mục `tests/` với các file test mẫu cơ bản, file `chay_kiem_thu.bat` | REQ-002 |
| 3 | Môi trường Linting | File cấu hình `.flake8`, file `kiem_tra_code.bat` | REQ-003 |

## TECH STACK
- Thư viện: `pytest`, `pytest-cov`, `flake8`, `logging` (Python stdlib)

## TASK GRAPH SUMMARY
3 TIPs, dự kiến hoàn thành trong 60 phút.

## NOT INCLUDED (Các hạng mục không bao gồm)
- **Không viết test cho 100% dự án**: Chỉ viết bộ khung và các bài test mẫu đại diện cho chức năng cốt lõi (ví dụ: ETL và Analytics), để dành không gian cho việc viết test dần dần sau này.
- **Không đập đi xây lại code cũ**: Nếu công cụ Linting phát hiện lỗi phong cách (style) ở code cũ quá nhiều, tôi sẽ cấu hình bỏ qua, chỉ sửa các lỗi nghiêm trọng gây sập app.
- **Không chuyển đổi PostgreSQL**: Hoãn sang Phase sau theo chỉ đạo.

## CONFIRM
Reply "CONFIRM" to receive the Task Graph.
