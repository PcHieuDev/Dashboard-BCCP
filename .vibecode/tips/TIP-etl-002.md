# TIP-etl-002: Đổi logger.error→info trong aggregator + kiểm tra ON CONFLICT agg_weekly

## HEADER
- TIP-ID: TIP-etl-002
- Branch: fix/etl
- Module: etl/aggregator.py
- Depends on: None
- Priority: P1
- Estimated effort: 20 phút

## CONTEXT
- Bug refs: M-05 (logger.error cho INFO), H-04 (ON CONFLICT agg_weekly có thể sai)

## TASK
1. aggregator.py: Tất cả thông báo bình thường (bắt đầu, đã gộp, hoàn thành) đang dùng logger.error() → đổi thành logger.info(). Chỉ giữ logger.error() trong khối except thực sự có lỗi.
2. aggregator.py: Tìm ON CONFLICT(tuan_bat_dau, ma_buu_cuc, nhom_dich_vu) trong rebuild_weekly. Truy vấn schema thực tế bảng agg_weekly từ E:\z.Database-TTKD-Data\dashboard.db. Nếu PRIMARY KEY không khớp, sửa ON CONFLICT cho đúng.

## ACCEPTANCE CRITERIA
Given: rebuild_monthly chạy
When: Xem log
Then: Không có ERROR giả

## CONSTRAINTS
- KHÔNG thay đổi logic tính toán
