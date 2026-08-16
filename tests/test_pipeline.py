import sqlite3
from unittest.mock import patch

import pandas as pd

from backend import pipeline


def _fake_df(station_id):
    return pd.DataFrame([{
        "station_id": station_id,
        "date": "2025-01-01",
        "precipitation_mm": 5.0,
        "air_temperature_c": 4.0,
    }])


def test_run_fetches_every_station(tmp_path):
    calls = []

    def fake_fetch(station_id=None, days=365):
        calls.append((station_id, days))
        return _fake_df(station_id)

    with patch.object(pipeline, "get_rainfall_data", side_effect=fake_fetch):
        pipeline.run(db_path=str(tmp_path / "test.db"), days=3650)

    from backend.config import STATIONS
    assert sorted(c[0] for c in calls) == sorted(STATIONS)
    assert all(c[1] == 3650 for c in calls)


def test_run_single_station_stores_data(tmp_path):
    """run() with a specific stations list only fetches that station,
    and the row is actually persisted to the DB."""
    db_path = str(tmp_path / "test.db")

    def fake_fetch(station_id=None, days=365):
        return _fake_df(station_id)

    with patch.object(pipeline, "get_rainfall_data", side_effect=fake_fetch):
        rows_stored = pipeline.run(db_path=db_path, days=100, stations=["SN50540"])

    # Only one station fetched → one row stored
    assert rows_stored == 1

    # Verify the data round-trips through the DB
    conn = sqlite3.connect(db_path)
    result = conn.execute(
        "SELECT station_id, date, precipitation_mm FROM observations"
    ).fetchall()
    conn.close()

    assert len(result) == 1
    station_id, date, precip = result[0]
    assert station_id == "SN50540"
    assert date == "2025-01-01"
    assert precip == 5.0
