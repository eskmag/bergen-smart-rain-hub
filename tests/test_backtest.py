"""Regression test for the 2018 dry-spring backtest.

Guarded by local data availability: CI without a seeded DB skips cleanly.
Where the DB holds 2018 observations, the model must keep detecting the
documented May–June 2018 Bergen drought.
"""

import sqlite3
from pathlib import Path

import pytest

from backend.config import DB_PATH


def _has_2018_data():
    if not Path(DB_PATH).exists():
        return False
    conn = sqlite3.connect(DB_PATH)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM observations WHERE date LIKE '2018-%'"
        ).fetchone()[0]
    finally:
        conn.close()
    return count >= 300


requires_2018 = pytest.mark.skipif(
    not _has_2018_data(),
    reason="2018 observations not in local DB (run backend.pipeline --days 3650)",
)


@requires_2018
def test_2018_dry_spring_detected():
    from backend.backtest import backtest_2018

    result = backtest_2018()
    ls = result["longest_dry_spell"]
    # Documented drought: 25-day spell starting 2018-05-17. Threshold has margin
    # for minor data-refresh drift but still fails if detection regresses.
    assert ls["days"] >= 20
    assert ls["start"] == "2018-05-17"


@requires_2018
def test_backtest_reports_all_three_tiers():
    from backend.backtest import backtest_2018

    result = backtest_2018()
    assert len(result["tiers"]) == 3
    for tier in result["tiers"]:
        assert set(tier) >= {"label", "liters", "days_tank_empty", "min_tank_liters"}
