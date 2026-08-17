"""Backtest: the documented May–June 2018 Bergen drought.

Validation vehicle for the rainwater model. The 2018 spring was an
exceptionally dry period in Bergen; if the model is sound, running the real
measured 2018 rainfall (station SN50540, Bergen Florida) through
`find_dry_spells` and `storage_simulation` must surface that drought as the
year's longest dry spell.

`backtest_2018()` is a pure function returning a summary dict — consumed by the
`/api/validation` endpoint, the regression test in `tests/test_backtest.py`, and
`scripts/backtest_2018.py` (human-readable CLI printout).

This validates dry-spell detection and the yield arithmetic against measured
data. It does *not* validate against a physical installation (future work).
"""

from backend.analysis import (
    Building,
    DEFAULT_COLLECTION_EFFICIENCY,
    find_dry_spells,
    recommend_tank_size,
    storage_simulation,
    water_collected,
)
from backend.config import DB_PATH, DEFAULT_STATION_ID
from backend.database import get_observations, init_db

# Standard reference case: a typical Bergen enebolig.
ROOF_M2 = 120
POPULATION = 4


def backtest_2018(db_path=None, station_id=DEFAULT_STATION_ID):
    """Run the 2018 backtest and return a summary dict.

    Raises ValueError if the DB holds no 2018 observations for the station.
    """
    conn = init_db(db_path or DB_PATH)
    df = get_observations(conn, "2018-01-01", "2018-12-31", station_id=station_id)
    conn.close()

    if df.empty:
        raise ValueError(f"Ingen 2018-observasjoner for stasjon {station_id!r}")

    total_rainfall_mm = float(df["precipitation_mm"].sum())

    spells = find_dry_spells(df)
    if spells.empty:
        longest = {"days": 0, "start": None, "end": None}
    else:
        row = spells.loc[spells["days"].idxmax()]
        longest = {
            "days": int(row["days"]),
            "start": row["start"].strftime("%Y-%m-%d"),
            "end": row["end"].strftime("%Y-%m-%d"),
        }

    efficiency = DEFAULT_COLLECTION_EFFICIENCY
    building = Building("Enebolig", ROOF_M2)
    annual_liters = water_collected(total_rainfall_mm, ROOF_M2, efficiency)

    tiers = []
    for tier in recommend_tank_size(annual_liters, POPULATION):
        sim = storage_simulation(
            df, [building], tier["liters"], POPULATION,
            collection_efficiency=efficiency,
        )
        tiers.append({
            "label": tier["label"],
            "liters": tier["liters"],
            "days_tank_empty": int((sim["tank_level_liters"] == 0).sum()),
            "min_tank_liters": round(float(sim["tank_level_liters"].min())),
        })

    return {
        "station_id": station_id,
        "year": 2018,
        "total_rainfall_mm": round(total_rainfall_mm, 1),
        "n_dry_spells": int(len(spells)),
        "longest_dry_spell": longest,
        "case": {"roof_m2": ROOF_M2, "population": POPULATION, "efficiency": efficiency},
        "tiers": tiers,
    }
