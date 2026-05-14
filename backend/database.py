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
    # Idempotent migration: add air_temperature_c if older schema lacks it.
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(observations)")}
    if "air_temperature_c" not in existing_cols:
        conn.execute("ALTER TABLE observations ADD COLUMN air_temperature_c REAL")
    conn.commit()
    return conn


def store_observations(conn, df):
    now = datetime.now().isoformat()
    has_temp = "air_temperature_c" in df.columns
    for _, row in df.iterrows():
        temp = row["air_temperature_c"] if has_temp else None
        if pd.isna(temp):
            temp = None
        conn.execute(
            """INSERT INTO observations
                   (station_id, date, precipitation_mm, air_temperature_c, fetched_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(station_id, date) DO UPDATE SET
                   precipitation_mm = excluded.precipitation_mm,
                   air_temperature_c = COALESCE(excluded.air_temperature_c, observations.air_temperature_c),
                   fetched_at = excluded.fetched_at""",
            (row["station_id"], row["date"], row["precipitation_mm"], temp, now),
        )
    conn.commit()


def get_observations(conn, start_date, end_date, station_id=None):
    query = ("SELECT station_id, date, precipitation_mm, air_temperature_c "
             "FROM observations WHERE date >= ? AND date <= ?")
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
