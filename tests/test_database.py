import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from backend.database import init_db, store_observations, get_observations


@pytest.fixture
def db_conn(tmp_path):
    """Create a temporary database for testing."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    yield conn
    conn.close()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "station_id": ["SN50540", "SN50540", "SN50540"],
        "date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "precipitation_mm": [5.0, 0.0, 12.3],
    })


class TestInitDb:
    def test_creates_db(self, tmp_path):
        db_path = str(tmp_path / "subdir" / "test.db")
        conn = init_db(db_path)
        assert Path(db_path).exists()
        conn.close()

    def test_returns_connection(self, db_conn):
        assert isinstance(db_conn, sqlite3.Connection)

    def test_table_exists(self, db_conn):
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='observations'"
        )
        assert cursor.fetchone() is not None


class TestStoreObservations:
    def test_inserts_rows(self, db_conn, sample_df):
        store_observations(db_conn, sample_df)
        cursor = db_conn.execute("SELECT COUNT(*) FROM observations")
        assert cursor.fetchone()[0] == 3

    def test_deduplication(self, db_conn, sample_df):
        store_observations(db_conn, sample_df)
        store_observations(db_conn, sample_df)  # insert again
        cursor = db_conn.execute("SELECT COUNT(*) FROM observations")
        assert cursor.fetchone()[0] == 3  # still 3, not 6


class TestGetObservations:
    def test_retrieves_data(self, db_conn, sample_df):
        store_observations(db_conn, sample_df)
        result = get_observations(db_conn, "2025-01-01", "2025-01-03")
        assert len(result) == 3

    def test_date_filtering(self, db_conn, sample_df):
        store_observations(db_conn, sample_df)
        result = get_observations(db_conn, "2025-01-02", "2025-01-02")
        assert len(result) == 1
        assert result.iloc[0]["precipitation_mm"] == 0.0

    def test_station_filtering(self, db_conn, sample_df):
        store_observations(db_conn, sample_df)
        result = get_observations(db_conn, "2025-01-01", "2025-01-03", station_id="INVALID")
        assert result.empty

    def test_returns_dataframe(self, db_conn, sample_df):
        store_observations(db_conn, sample_df)
        result = get_observations(db_conn, "2025-01-01", "2025-01-03")
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == {"station_id", "date", "precipitation_mm"}
