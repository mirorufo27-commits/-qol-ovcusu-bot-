from datetime import datetime, timedelta
import sqlite3
import json
from collections import defaultdict

DB_PATH = 'data/qolovcusu.db'

def _connect():
    return sqlite3.connect(DB_PATH)

def daily_report(day=None):
    conn = _connect()
    cur = conn.cursor()
    if not day:
        day = datetime.utcnow().date()
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    q = "SELECT status, COUNT(*) FROM predictions WHERE created_at BETWEEN ? AND ? GROUP BY status"
    cur.execute(q,(start.isoformat(), end.isoformat()))
    rows = cur.fetchall()
    conn.close()
    summary = {r[0]: r[1] for r in rows}
    return summary
