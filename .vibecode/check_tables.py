import sqlite3
conn = sqlite3.connect(r'E:/OneDrive/z.Database-TTKD-Data/dashboard.db')
c = conn.cursor()
# Check all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("All tables:", [r[0] for r in c.fetchall()])

# Check for specific tables
for t in ['transactions_hcc','transactions_tcbc','transactions_ppbl','plans','agg_monthly','agg_monthly_customer']:
    result = c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}'").fetchone()
    print(f"  {t}: {'EXISTS' if result else 'NOT FOUND'}")

# Count rows in key tables
for t in ['transactions', 'agg_weekly', 'agg_weekly_customer', 'agg_daily_customer']:
    try:
        count = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count} rows")
    except:
        print(f"  {t}: ERROR")

conn.close()
