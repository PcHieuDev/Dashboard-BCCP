import sqlite3
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

db_path = r'E:\OneDrive\z.Database-TTKD-Data\dashboard.db'
try:
    conn = sqlite3.connect(db_path)
    df2 = pd.read_sql_query("SELECT san_pham_dv, COUNT(*) as cnt, SUM(cuoc_tt_tong) as dt FROM transactions WHERE san_pham_dv LIKE '%HCC%' GROUP BY san_pham_dv", conn)
    print(df2)
    conn.close()
except Exception as e:
    print(e)

    print(df)
    conn.close()
except Exception as e:
    print(e)
