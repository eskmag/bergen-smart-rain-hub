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

    def test_simulate_accepts_alternate_station(self, seeded_db):
        req = {**VALID_SIM_REQUEST, "station": "SN50500"}
        r = client.post("/api/simulate/beredskap", json=req)
        assert r.status_code == 200
