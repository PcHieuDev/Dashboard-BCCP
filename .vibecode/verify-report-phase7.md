VERIFY REPORT: Dashboard-BCCP (Phase 7)
Date: 2026-06-02 19:33
Method: Build-log review + Mini SCAN code thực tế + grep + verify_phase6.py

REQUIREMENT COVERAGE:
├── Total Requirements: 6 (REQ-022 đến REQ-027)
├── Implemented: 3 (REQ-022, REQ-023, REQ-027)
├── Missing/Incomplete: 3 (REQ-024, REQ-025, REQ-026)
└── Coverage: 3/6 = 50%

---

TIP-006 (Fix Routing): ✅ PASS
- app.py L245: `return None` thay vì `return "tab-kpi"` → ĐÚNG
- kpi_callbacks.py L87: `if tab_val != "tab-kpi" or tab_val is None:` → ĐÚNG
- sidebar-spdv: ĐÃ XÓA khỏi Input list của kpi_callbacks → ĐÚNG (không còn Input sidebar-spdv)

TIP-007 (Sidebar Filter): ✅ PASS
- sidebar_callbacks.py: `Output("bccp-extra-filters", "style")` → CÓ ở L148
- Logic: `bccp_filter_style = {"display": "block"} if pathname.startswith("/bccp")` → L172 ĐÚNG
- Return tuple: `bccp_filter_style` được thêm ở cuối L227 → ĐÚNG
- Cần kiểm tra thêm: `bccp-extra-filters` container có tồn tại trong `sidebar.py` không

TIP-008 (PHBC KPI Card): ❌ NOT DONE
- kpi_page.py: Không tìm thấy "kpi-phbc" cũng không tìm thấy PHBC hay Phát hành báo chí
- kpi_page.py: Cũng không tìm thấy "kpi-hcc" nữa → Thợ có thể đã xóa HCC nhưng chưa thêm PHBC
- kpi_callbacks.py L87: Input sidebar-spdv đã bị xóa (tốt), nhưng chưa thấy phbc logic
- FIX-002 required

TIP-009 (DB + ETL PHBC): ❌ NOT DONE
- scripts/migrate_add_phbc.py: Không tìm thấy trong project
- etl/importer.py: Không tìm thấy hàm import_phbc_excel
- dashboard.db: Không có bảng transactions_phbc (không tạo script)
- FIX-002 required

TIP-010 (Import UI PHBC): ❌ NOT DONE
- import_data.py: Không tìm thấy option "PHBC" trong dropdown
- import_callbacks.py: Không tìm thấy case PHBC
- FIX-002 required

---

CRITICAL ISSUES:
1. FIX-002 (Major): TIP-008, TIP-009, TIP-010 chưa được thực hiện.
   - Bảng transactions_phbc chưa tồn tại trong DB
   - Card PHBC chưa có trong trang /bccp KPI
   - Import UI chưa có option PHBC
   → FIX-002.md tạo tại .vibecode/fix-tips/

ADDITIONAL FIXES NEEDED BY CONTRACTOR (Chủ thầu):
- TIP-007: Cần verify container "bccp-extra-filters" có trong sidebar.py layout không
  → Nếu container không tồn tại trong DOM thì Output sẽ báo lỗi

OVERALL STATUS: NEEDS FIXES (FIX-002 — 3 TIPs chưa xong)
