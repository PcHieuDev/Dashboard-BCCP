# BUILD LOG: Dashboard-BCCP
Branch: fix/etl
Builder started: 2026-06-24 18:12 (ICT)

---

## TIP-etl-001: Sửa nam=None + whitelist nhom_chinh
- Status: DONE
- Started: 18:12
- Completed: 18:15
- Files: 0 created, 1 modified (etl/importer.py)
- Tests: 2/2 passed
- Commit: `fix(etl): TIP-etl-001+002 — nam fallback, whitelist nhom_chinh, aggregator logger.info`
- Commit hash: 7e17323
- Issues: `row_data_line` không tồn tại trong scope → dùng `nhom_chinh` trực tiếp trong message

---

## TIP-etl-002: Đổi logger.error→info trong aggregator + kiểm tra ON CONFLICT agg_weekly
- Status: DONE
- Started: 18:12
- Completed: 18:15
- Files: 0 created, 1 modified (etl/aggregator.py)
- Tests: 2/2 passed
- Commit: `fix(etl): TIP-etl-001+002 — nam fallback, whitelist nhom_chinh, aggregator logger.info`
- Commit hash: 7e17323
- Issues: H-04 (ON CONFLICT) — schema đã đúng, không cần sửa (PRIMARY KEY thực tế khớp hoàn toàn)

---

## TIP-etl-003: Sửa backup busy_timeout + importer rowcount
- Status: DONE
- Started: 18:15
- Completed: 18:16
- Files: 0 created, 2 modified (etl/backup.py, etl/importer.py)
- Tests: 2/2 passed
- Commit: `fix(etl): TIP-etl-003 — backup busy_timeout 30s, importer rowcount total_changes`
- Commit hash: 5fe52e1
- Issues: None

---

## SUMMARY
- Branch: fix/etl
- Total TIPs: 3
- DONE: 3
- BLOCKED: 0
- Commits: [7e17323, 5fe52e1]
- Overall: READY FOR VERIFY
