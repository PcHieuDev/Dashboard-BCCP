import sqlite3
conn = sqlite3.connect(r'E:\OneDrive\z.Database-TTKD-Data\bccp.db')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    cols = [col[1] for col in c.execute(f"PRAGMA table_info({t[0]})").fetchall()]
    print(f"Table: {t[0]}")
    print(f"Columns: {cols}")
conn.close()
