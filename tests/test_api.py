"""Endpoint tests for the FastAPI layer — serialisation and error paths.

Business logic is covered by the backend test files; these tests verify
that the thin API layer wires it up correctly.
"""

from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from backend.analysis import (
    BERGEN_ANNUAL_RAINFALL_MM,
    DEFAULT_BUILDING_HEIGHT_M,
    DEFAULT_COLLECTION_EFFICIENCY,
    TANK_RECOMMENDATION_DAYS,
    WATER_NEEDS,
)
from backend.config import DEFAULT_STATION_ID
from backend.database import init_db, store_observations

client = TestClient(app)


@pytest.fixture
def seeded_db(tmp_path, monkeypatch):
    """Temp database with 60 recent days of synthetic rain, wired into the routers."""
    db_path = tmp_path / "rain.db"
    conn = init_db(db_path)
    start = date.today() - timedelta(days=59)
    rows = [
        {
            "station_id": DEFAULT_STATION_ID,
            "date": (start + timedelta(days=i)).isoformat(),
            # every third day is dry so dry-spell detection has something to find
            "precipitation_mm": 0.0 if i % 3 == 0 else 6.0,
            "air_temperature_c": 8.0,
        }
        for i in range(60)
    ]
    store_observations(conn, pd.DataFrame(rows))
    # Also seed SN50500 so station-selection tests can use it
    rows_50500 = [
        {
            "station_id": "SN50500",
            "date": (start + timedelta(days=i)).isoformat(),
            "precipitation_mm": 0.0 if i % 3 == 0 else 5.0,
            "air_temperature_c": 7.0,
        }
        for i in range(60)
    ]
    store_observations(conn, pd.DataFrame(rows_50500))
    conn.close()
    monkeypatch.setattr("api.routers.observations.DB_PATH", db_path)
    monkeypatch.setattr("api.routers.simulate.DB_PATH", db_path)
    return db_path


@pytest.fixture
def empty_db(tmp_path, monkeypatch):
    db_path = tmp_path / "empty.db"
    init_db(db_path).close()
    monkeypatch.setattr("api.routers.observations.DB_PATH", db_path)
    monkeypatch.setattr("api.routers.simulate.DB_PATH", db_path)
    return db_path


VALID_SIM_REQUEST = {
    "buildings": [{"name": "Bygg 1", "roof_area_m2": 120.0}],
    "tank_liters": 5000,
    "population": 4,
}


class TestConfigEndpoint:
    def test_ok(self):
        r = client.get("/api/config")
        assert r.status_code == 200

    def test_water_needs_locked_minimum(self):
        body = client.get("/api/config").json()
        assert body["water_needs"]["survival_total"] == WATER_NEEDS["survival_total"]

    def test_defaults_mirror_backend_constants(self):
        defaults = client.get("/api/config").json()["defaults"]
        assert defaults["collection_efficiency"] == DEFAULT_COLLECTION_EFFICIENCY
        assert defaults["building_height_m"] == DEFAULT_BUILDING_HEIGHT_M
        assert defaults["annual_rainfall_mm"] == BERGEN_ANNUAL_RAINFALL_MM
        assert defaults["tank_recommendation_days"] == list(TANK_RECOMMENDATION_DAYS)

    def test_has_scales_and_presets(self):
        body = client.get("/api/config").json()
        assert len(body["scales"]) == 3
        assert len(body["building_presets"]) > 0
        assert len(body["climate_scenarios"]) == 3


class TestObservationsEndpoint:
    def test_returns_seeded_rows(self, seeded_db):
        r = client.get("/api/observations?days=365")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 60
        assert {"date", "precipitation_mm", "air_temperature_c"} <= rows[0].keys()

    def test_days_validation(self):
        assert client.get("/api/observations?days=0").status_code == 422
        assert client.get("/api/observations?days=99999").status_code == 422

    def test_empty_db_returns_empty_list(self, empty_db):
        r = client.get("/api/observations")
        assert r.status_code == 200
        assert r.json() == []


@pytest.fixture
def two_year_db(tmp_path, monkeypatch):
    """Temp database with 2 full synthetic years for SN50540.

    Uses the two most-recently-completed calendar years so that
    _load_df(days=3650) captures them while _load_df(days=365) also returns
    data (we seed the most recent ~365 days from year-2 as well).
    """
    db_path = tmp_path / "rain2yr.db"
    conn = init_db(db_path)
    today = date.today()
    # Two complete calendar years ending yesterday
    year2 = today.year - 1
    year1 = year2 - 1
    rows = []
    for year in (year1, year2):
        start_of_year = date(year, 1, 1)
        for i in range(365):
            d = start_of_year + timedelta(days=i)
            rows.append({
                "station_id": DEFAULT_STATION_ID,
                "date": d.isoformat(),
                # year1: wetter (8 mm on rain days); year2: drier (4 mm)
                "precipitation_mm": 0.0 if i % 3 == 0 else (8.0 if year == year1 else 4.0),
                "air_temperature_c": 8.0,
            })
    # Also seed the last 60 days of "today's" year so _load_df(days=365) is non-empty
    recent_start = today - timedelta(days=59)
    for i in range(60):
        d = recent_start + timedelta(days=i)
        rows.append({
            "station_id": DEFAULT_STATION_ID,
            "date": d.isoformat(),
            "precipitation_mm": 0.0 if i % 3 == 0 else 6.0,
            "air_temperature_c": 8.0,
        })
    store_observations(conn, pd.DataFrame(rows))
    conn.close()
    monkeypatch.setattr("api.routers.simulate.DB_PATH", db_path)
    return db_path, year1, year2


class TestSimulateEndpoint:
    def test_happy_path(self, seeded_db):
        r = client.post("/api/simulate/beredskap", json=VALID_SIM_REQUEST)
        assert r.status_code == 200
        body = r.json()
        assert body["summary"]["total_collected_liters"] > 0
        assert len(body["simulation_series"]) == 60
        assert body["dry_spells"] == [] or body["dry_spells"][0]["days"] >= 1
        # historical scenario → no comparison block
        assert body["scenario_comparison"] is None

    def test_yearly_outcomes_present_in_response(self, seeded_db):
        """yearly_outcomes key must exist and be a list (seeded fixture is only
        60 days → all years have <300 days → list is empty, but field is present)."""
        r = client.post("/api/simulate/beredskap", json=VALID_SIM_REQUEST)
        assert r.status_code == 200
        body = r.json()
        assert "yearly_outcomes" in body
        assert isinstance(body["yearly_outcomes"], list)

    def test_yearly_outcomes_two_full_years(self, two_year_db):
        """With 2 × 365-day years the response must have exactly those 2 outcome
        rows sorted by year, each with the expected keys."""
        db_path, year1, year2 = two_year_db
        r = client.post("/api/simulate/beredskap", json=VALID_SIM_REQUEST)
        assert r.status_code == 200
        outcomes = r.json()["yearly_outcomes"]
        # At least the two full seeded years must appear (current partial year skipped)
        years_in_response = [row["year"] for row in outcomes]
        assert year1 in years_in_response
        assert year2 in years_in_response
        # Sorted by year ascending
        assert years_in_response == sorted(years_in_response)
        # Each row must have the expected keys
        expected_keys = {"year", "total_collected_liters", "days_tank_empty",
                         "min_tank_pct", "longest_dry_spell_days"}
        for row in outcomes:
            assert expected_keys <= row.keys()
        # year1 (wetter, 8 mm) must collect more than year2 (drier, 4 mm)
        outcome_by_year = {row["year"]: row for row in outcomes}
        assert (outcome_by_year[year1]["total_collected_liters"]
                > outcome_by_year[year2]["total_collected_liters"])

    def test_scenario_comparison_included(self, seeded_db):
        req = {**VALID_SIM_REQUEST, "climate_scenario": "moderate"}
        body = client.post("/api/simulate/beredskap", json=req).json()
        assert body["scenario_comparison"] is not None
        assert len(body["scenario_comparison"]) == 3

    def test_defaults_applied(self, seeded_db):
        # height_m and efficiency omitted — schema defaults must kick in
        r = client.post("/api/simulate/beredskap", json=VALID_SIM_REQUEST)
        assert r.status_code == 200

    def test_missing_fields_rejected(self, seeded_db):
        r = client.post("/api/simulate/beredskap", json={"tank_liters": 5000})
        assert r.status_code == 422

    def test_empty_db_returns_503(self, empty_db):
        r = client.post("/api/simulate/beredskap", json=VALID_SIM_REQUEST)
        assert r.status_code == 503


class TestCostsEndpoint:
    def test_happy_path(self):
        r = client.get("/api/costs?population=4&scale=household")
        assert r.status_code == 200
        body = r.json()
        assert body["estimate_label"] == "Enebolig / husholdning"
        assert body["capital"] > 0
        assert len(body["all_estimates"]) == 5
        assert len(body["capital_breakdown"]) == 7

    def test_population_tier_wins_over_scale(self):
        body = client.get("/api/costs?population=50&scale=household").json()
        assert body["estimate_label"] == "Boligblokk (20 enheter)"

    def test_out_of_range_population_uses_scale_default(self):
        body = client.get("/api/costs?population=3&scale=infrastructure").json()
        assert body["estimate_label"] == "Sykehusavdeling"

    def test_unknown_scale_is_422(self):
        assert client.get("/api/costs?population=4&scale=bogus").status_code == 422

    def test_population_required(self):
        assert client.get("/api/costs").status_code == 422

    def test_cost_per_liter_only_with_annual_liters(self):
        without = client.get("/api/costs?population=4&scale=household").json()
        with_l = client.get("/api/costs?population=4&scale=household&annual_liters=100000").json()
        assert without["cost_per_liter_20"] is None
        assert with_l["cost_per_liter_20"] > 0


class TestTreatmentEndpoint:
    def test_treatment_endpoint(self):
        r = client.get("/api/treatment?material=takstein&scale=household")
        assert r.status_code == 200
        body = r.json()
        assert body["risk_class"] == "lav"
        assert body["potable"] is True
        assert "Sedimentfilter" in body["barriers"]

    def test_treatment_unknown_material_422(self):
        r = client.get("/api/treatment?material=papp123&scale=household")
        assert r.status_code == 422

    def test_treatment_infrastructure_scale(self):
        r = client.get("/api/treatment?material=takstein&scale=infrastructure")
        assert r.status_code == 200
        body = r.json()
        assert "Restklorering" in body["barriers"]

    def test_treatment_kobbertak_not_potable(self):
        r = client.get("/api/treatment?material=kobbertak")
        assert r.status_code == 200
        body = r.json()
        assert body["potable"] is False
        assert body["barriers"] == []

    def test_treatment_unknown_scale_422(self):
        r = client.get("/api/treatment?material=takstein&scale=district")
        assert r.status_code == 422

    def test_config_includes_roof_materials(self):
        r = client.get("/api/config")
        materials = r.json()["roof_materials"]
        assert any(m["key"] == "takstein" for m in materials)


class TestStationSelection:
    def test_config_includes_stations(self):
        body = client.get("/api/config").json()
        assert body["defaults"]["station_id"] == "SN50540"
        assert any(s["id"] == "SN50540" for s in body["stations"])

    def test_observations_rejects_unknown_station(self):
        r = client.get("/api/observations?station=SN99999")
        assert r.status_code == 422

    def test_observations_station_filter_returns_only_that_station(self, seeded_db):
        # seeded_db seeds exactly 60 rows for SN50500; the response must not
        # include the SN50540 rows (which would double the count to 120).
        r = client.get("/api/observations?days=365&station=SN50500")
        assert r.status_code == 200
        rows = r.json()
        # Exactly the 60 seeded SN50500 rows — not mixed with SN50540 rows.
        assert len(rows) == 60

    def test_simulate_station_param_changes_collected_volume(self, seeded_db):
        # SN50540 wet days: 6.0 mm; SN50500 wet days: 5.0 mm.
        # Same roof area and efficiency → SN50540 must collect strictly more.
        default_body = client.post(
            "/api/simulate/beredskap", json=VALID_SIM_REQUEST
        ).json()
        alt_body = client.post(
            "/api/simulate/beredskap",
            json={**VALID_SIM_REQUEST, "station": "SN50500"},
        ).json()
        default_collected = default_body["summary"]["total_collected_liters"]
        alt_collected = alt_body["summary"]["total_collected_liters"]
        # The station parameter must actually route to different data.
        assert default_collected > alt_collected, (
            f"Expected SN50540 ({default_collected} L) > SN50500 ({alt_collected} L)"
        )


class TestBydelEndpoint:
    def test_bydel_endpoint(self):
        r = client.get("/api/bydel?participation=0.2")
        assert r.status_code == 200
        body = r.json()
        assert len(body["bydeler"]) == 8
        assert 0 < body["demand_coverage_pct"] < 1000
        assert body["participation_pct"] == 0.2
        assert body["persons_covered"] > 0
        assert body["assumptions"]

    def test_bydel_default_participation(self):
        r = client.get("/api/bydel")
        assert r.status_code == 200
        assert r.json()["participation_pct"] == 0.20

    def test_bydel_zero_participation_422(self):
        r = client.get("/api/bydel?participation=0")
        assert r.status_code == 422

    def test_bydel_over_one_participation_422(self):
        r = client.get("/api/bydel?participation=1.5")
        assert r.status_code == 422
