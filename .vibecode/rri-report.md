# RRI REPORT: Dashboard BCCP (Refactoring)
Generated: 2026-06-11
Complexity: Medium (Technical Refactoring)
Questions Asked: 3 (Challenge Mode)

## REQUIREMENTS MATRIX
| REQ-ID  | Requirement          | Source    | Priority | Persona    |
|---------|----------------------|-----------|----------|------------|
| REQ-001 | Triển khai Logging thay thế print() | RRI Q#1 | P0       | Operator   |
| REQ-002 | Thiết lập kiểm thử tự động (Pytest) | RRI Q#2 | P1       | QA / Tester|
| REQ-003 | Áp dụng kiểm soát code (Linting) | RRI Q#3 | P2       | Developer  |

## AUTO-ANSWERED (từ báo cáo Quét mã nguồn)
- **Cấu trúc hiện tại**: Đã chia module tốt (etl, analytics, dash_app), nên việc thêm test và logging sẽ dễ dàng khoanh vùng.
- **Database**: Vẫn giữ nguyên SQLite, chưa chuyển PostgreSQL (theo chỉ đạo của Sếp).

## DECISIONS LOG
| Decision | Options Considered | Chosen | Rationale |
|----------|--------------------|--------|-----------|
| [D-001]  | Chọn thư viện Test | pytest | Chuẩn ngành, dễ viết, dễ đọc báo cáo |
| [D-002]  | Thư mục lưu Log    | logs/  | Tách biệt khỏi thư mục code chính |

## OPEN QUESTIONS (Dành cho Sếp quyết định)
- **[OQ-001] Logging (Ghi nhật ký)**: Tôi đề xuất hệ thống sẽ lưu tối đa 5 file nhật ký gần nhất, mỗi file 10MB (đầy tự động cắt sang file mới). Sếp thấy hợp lý không?
- **[OQ-002] Testing (Kiểm thử)**: Vì Sếp không chuyên IT, tôi đề xuất chỉ tạo test cho **khâu nhập dữ liệu (ETL)** và **khâu tính toán (Analytics)** để đảm bảo số liệu báo cáo luôn đúng. Giao diện (UI) tạm thời chưa cần test tự động để tiết kiệm thời gian. Sếp đồng ý chứ?
- **[OQ-003] Linting (Kiểm tra cú pháp)**: Tôi sẽ bật mức độ kiểm tra "cơ bản" trước để không làm xáo trộn code cũ đang chạy tốt, chủ yếu để chặn các lỗi ngớ ngẩn (như viết sai tên biến) cho các đoạn code mới sau này. Sếp thấy ổn không?
