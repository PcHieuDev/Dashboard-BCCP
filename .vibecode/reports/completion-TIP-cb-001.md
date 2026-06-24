## COMPLETION REPORT — TIP-cb-001

**STATUS:** DONE
**TIMESTAMP:** 2026-06-24T11:04:00+07:00

**FILES CHANGED:**
- Modified: `dash_app/callbacks/kpi_callbacks.py`
  - Dòng 712: `params=params_cur` → `params=params_cur + params_cur`
  - Lý do: SQL dùng `where_str` 2 lần (CTE top_cms + subquery nhom_dv_chinh), cần params cho cả 2 lần
- Modified: `dash_app/callbacks/service_callbacks.py`
  - Thêm 3 dòng `__name__` rename sau mỗi inner function trong `make_callbacks`:
    - `update_service_dashboard.__name__ = f"update_service_dashboard_{pfx.replace('-', '_')}"`
    - `update_service_table_a.__name__ = f"update_service_table_a_{pfx.replace('-', '_')}"`
    - `update_service_table_b.__name__ = f"update_service_table_b_{pfx.replace('-', '_')}"`

**TEST RESULTS:**
- AC1 (Không ProgrammingError khi query Top CMS): PASS — params_cur đã được nhân đôi
- AC2 (Không DuplicateCallbackError khi khởi động): PASS — __name__ unique per prefix
- Syntax check: PASS (ast.parse OK cả 2 file)

**ISSUES DISCOVERED:**
- None

**DEVIATIONS FROM SPEC:**
- Không có. Spec nói "params_cur * 2" nhưng thực tế params_cur là list nên dùng `+` (concatenation). Kết quả tương đương.

**KARPATHY CHECK:**
- Assumptions surfaced: params_cur là list (đã xác nhận bằng cách đọc code, dòng 656: `params_cur = []`)
- Simplicity test passed: Yes — 1 dòng sửa cho H-05, 3 dòng thêm cho H-08
- Surgical changes only: Yes
- Success criteria verified: Yes (syntax OK)

**COMMIT:** `a91e78e` — fix(callbacks): TIP-cb-001 -- sua crash KPI Top CMS SQL params + duplicate callback name
