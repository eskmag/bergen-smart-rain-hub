import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from backend.config import DB_PATH


def init_db(db_path=None):
    db_path = db_path or DB_PATH
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            date TEXT NOT NULL,
            precipitation_mm REAL NOT NULL,
            fetched_at TEXT NOT NULL,
            UNIQUE(station_id, date)
        )
    """)
    conn.commit()
    return conn


def store_observations(conn, df):
    now = datetime.now().isoformat()
    for _, row in df.iterrows():
        conn.execute(
            "INSERT OR IGNORE INTO observations (station_id, date, precipitation_mm, fetched_at) VALUES (?, ?, ?, ?)",
            (row["station_id"], row["date"], row["precipitation_mm"], now),
        )
    conn.commit()


def get_observations(conn, start_date, end_date, station_id=None):
    query = "SELECT station_id, date, precipitation_mm FROM observations WHERE date >= ? AND date <= ?"
    params = [start_date, end_date]
    if station_id:
        query += " AND station_id = ?"
        params.append(station_id)
    query += " ORDER BY date"
    return pd.read_sql_query(query, conn, params=params)


if __name__ == "__main__":
    conn = init_db()
    print("Database initialized successfully.")
    conn.close()
