# BUILD LOG: Dashboard-BCCP
Branch: fix/critical-callbacks
Builder started: 2026-06-24T11:00:00+07:00

---

## TIP-cb-001: Sửa crash KPI Top CMS SQL params + duplicate callback name
- Status: DONE
- Started: 2026-06-24T11:00:00+07:00
- Completed: 2026-06-24T11:04:00+07:00
- Files: 0 created, 2 modified (kpi_callbacks.py, service_callbacks.py)
- Tests: 2/2 AC passed (syntax check OK)
- Commit: `fix(callbacks): TIP-cb-001 -- sua crash KPI Top CMS SQL params + duplicate callback name`
- Commit hash: a91e78e
- Issues: None
  - H-05: params_cur nhân đôi bằng list concatenation (`params_cur + params_cur`)
  - H-08: __name__ trick đặt tên unique cho 3 inner functions per prefix

---

## TIP-cb-002: Sửa TypeError format month/week + thứ tự tab_val check
- Status: DONE
- Started: 2026-06-24T11:04:00+07:00
- Completed: 2026-06-24T11:04:30+07:00
- Files: 0 created, 4 modified (sidebar_callbacks.py, new_customer_callbacks.py, kpi_callbacks.py, customer_callbacks.py)
- Tests: 3/3 AC passed (syntax check OK, guard logic verified)
- Commit: `fix(callbacks): TIP-cb-002 -- sua TypeError format month/week + thu tu tab_val check`
- Commit hash: 0530b76
- Issues: None — bonus: đã sửa 2 chỗ month:02d trong new_customer (TIP chỉ đề cập 1 chỗ)

---

## TIP-cb-003: Sửa sparkline column + division zero + StringIO + dead cursor
- Status: DONE
- Started: 2026-06-24T11:06:00+07:00
- Completed: 2026-06-24T11:07:15+07:00
- Files: 0 created, 4 modified (kpi_callbacks.py, service_detail_callbacks.py, db/connection.py, service_callbacks.py)
- Tests: 2/2 AC passed (syntax check OK)
- Commit: `fix(callbacks): TIP-cb-003 -- sua sparkline column + division zero + StringIO + dead cursor`
- Commit hash: 9a08580
- Issues: None
  - H-06: Sửa tên cột nhom_dv → nhom_dich_vu với fallback an toàn
  - H-11: elif curr > 0: return 100.0 cho dịch vụ mới
  - M-12: StringIO wrapper cho pd.read_json
  - M-13: Xóa 2 dead cursor trong query_sub_service_data và _ytd

---

## SUMMARY
- Branch: fix/critical-callbacks
- Total TIPs: 3
- DONE: 3 (TIP-cb-001, TIP-cb-002, TIP-cb-003)
- BLOCKED: 0
- Commits: a91e78e, 0530b76, 9a08580
- Overall: READY FOR VERIFY
