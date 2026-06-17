import sqlite3

import logging
try:
    from config.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    try:
        from config.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = logging.getLogger(__name__)

conn = sqlite3.connect(r'E:\z.Database-TTKD-Data\bccp.db')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    cols = [col[1] for col in c.execute(f"PRAGMA table_info({t[0]})").fetchall()]
    logger.info(f"Table: {t[0]}")
    logger.info(f"Columns: {cols}")
conn.close()
