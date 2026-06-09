TECH_STACK:
  Language: Python 3.13
  Framework: Dash (converted from Streamlit)
  Styling: dash-bootstrap-components, custom CSS in assets/style.css
  Database: SQLite (dashboard.db)
  Auth: Custom RBAC (in dash_app/db/auth.py)
  State: dcc.Store, functools.lru_cache, URL/QueryParams
  Other: pandas, plotly, openpyxl, xlrd

EXISTING_MODULES:
  - dash_app: Main Dash application (app.py, callbacks, components, pages, db).
  - analytics: Business logic for calculating revenue, customer retention, metrics.
  - etl: Data import and aggregation (importer.py, aggregator.py).
  - scripts: Support scripts (rebuild_summaries.py, sync_mappings.py).
  - config: App configuration (settings.py, holidays.py).
  - data: Static CSV files and Excel templates for mapping and imports.

PATTERNS_DETECTED:
  - Architecture: Separated backend logic (analytics, etl, db) from frontend callbacks.
  - Performance: Summary Tables (agg_monthly, plans_weekly) used to optimize read operations instead of querying raw transactions.
  - Caching: Extensively using `@functools.lru_cache`.
  - Routing: Multi-page Dash application (dash.page_registry).

REUSABLE_COMPONENTS:
  - dash_app/components: Contains reusable UI components (Topbar, Sidebar, Filters).

GAPS_DETECTED:
  - Debug Artifacts: Excessive use of `print()` for error logging (~130+ instances). Should ideally be replaced with a structured `logging` module.
  - Production Deployment: Currently running via batch files and SQLite. Needs migration to PostgreSQL and a proper server setup (Phase 5C is pending).
  - Testing: Lack of an automated testing suite (no `tests/` folder).

CODE_HEALTH:
  Type Safety: Partial (Relies heavily on dynamic Pandas DataFrames).
  Linting: Not explicitly configured.
  Tests: 0 files (Manual testing mainly).
  Debug Artifacts: ~130+ `print()` statements across the codebase.
  TODO/FIXME: 0 found.

ESTIMATED_SIZE:
  Files: ~50+ (.py, .md, .bat, .json, .xlsx)
  Lines of Code: ~Large
  Components/Modules: 4 core (dash_app, analytics, etl, scripts)
  API Routes/Endpoints: N/A (Dash handles routing internally)

COMPLEXITY_ASSESSMENT: Large
