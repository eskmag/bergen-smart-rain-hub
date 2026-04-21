import pandas as pd
import numpy as np
import pytest

from backend.analysis import (
    Building,
    water_collected,
    emergency_supply_days,
    storage_simulation,
    find_dry_spells,
    recommend_tank_size,
    calculate_rain_energy,
    co2_offset,
    practical_equivalents,
    monthly_summary,
    seasonal_summary,
    daily_collection,
    WATER_NEEDS,
    G,
)


def make_df(precip_values):
    """Helper: create a precipitation DataFrame from a list of mm values."""
    dates = pd.date_range("2025-01-01", periods=len(precip_values), freq="D")
    return pd.DataFrame({
        "station_id": "SN50540",
        "date": dates.strftime("%Y-%m-%d"),
        "precipitation_mm": precip_values,
    })


# --- water_collected ---

class TestWaterCollected:
    def test_basic(self):
        # 10mm on 100m² roof at 85% efficiency = 850 liters
        assert water_collected(10, 100) == pytest.approx(850.0)

    def test_zero_rain(self):
        assert water_collected(0, 100) == 0.0

    def test_zero_roof(self):
        assert water_collected(10, 0) == 0.0

    def test_custom_efficiency(self):
        assert water_collected(10, 100, 1.0) == pytest.approx(1000.0)

    def test_one_mm_one_m2(self):
        # 1mm on 1m² = 1 liter (at 100% efficiency)
        assert water_collected(1, 1, 1.0) == pytest.approx(1.0)


# --- emergency_supply_days ---

class TestEmergencySupplyDays:
    def test_basic(self):
        # 1300 liters, 10 people, 13 L/person/day = 10 days
        result = emergency_supply_days(1300, 10, "survival_total")
        assert result == pytest.approx(10.0)

    def test_one_person(self):
        result = emergency_supply_days(130, 1, "survival_total")
        assert result == pytest.approx(10.0)

    def test_zero_population(self):
        assert emergency_supply_days(1000, 0) == 0

    def test_normal_usage(self):
        # 1500 liters / (1 * 150 L/day) = 10 days
        result = emergency_supply_days(1500, 1, "normal_usage")
        assert result == pytest.approx(10.0)


# --- storage_simulation ---

class TestStorageSimulation:
    def test_fills_up(self):
        # Heavy rain, small consumption, tank should fill
        df = make_df([50, 50, 50])
        buildings = [Building("Test", roof_area_m2=100)]
        sim = storage_simulation(df, buildings, 10000, 1)
        assert sim["tank_level_liters"].iloc[-1] > 0

    def test_drains_dry(self):
        # No rain, large population
        df = make_df([0, 0, 0, 0, 0, 0, 0])
        buildings = [Building("Test", roof_area_m2=100)]
        sim = storage_simulation(df, buildings, 100, 100)
        assert sim["tank_level_liters"].iloc[-1] == 0

    def test_tank_capped(self):
        # Massive rain shouldn't exceed tank capacity
        df = make_df([500])
        buildings = [Building("Test", roof_area_m2=1000)]
        sim = storage_simulation(df, buildings, 1000, 1)
        assert sim["tank_level_liters"].iloc[0] <= 1000

    def test_starts_half_full(self):
        # With no rain and no people, tank stays at 50%
        df = make_df([0])
        buildings = [Building("Test", roof_area_m2=100)]
        sim = storage_simulation(df, buildings, 1000, 0)
        assert sim["tank_level_liters"].iloc[0] == pytest.approx(500.0)

    def test_output_columns(self):
        df = make_df([10])
        buildings = [Building("Test", roof_area_m2=100)]
        sim = storage_simulation(df, buildings, 1000, 1)
        expected_cols = {"date", "precipitation_mm", "inflow_liters", "consumption_liters",
                         "tank_level_liters", "tank_pct", "days_remaining"}
        assert set(sim.columns) == expected_cols


# --- find_dry_spells ---

class TestFindDrySpells:
    def test_finds_dry_spell(self):
        # 5 dry days in a row
        df = make_df([10, 0, 0, 0, 0, 0, 10])
        spells = find_dry_spells(df, min_days=3)
        assert len(spells) == 1
        assert spells.iloc[0]["days"] == 5

    def test_no_dry_spells(self):
        df = make_df([10, 10, 10, 10])
        spells = find_dry_spells(df, min_days=3)
        assert spells.empty

    def test_short_spell_filtered(self):
        # 2 dry days, below min_days=3
        df = make_df([10, 0, 0, 10])
        spells = find_dry_spells(df, min_days=3)
        assert spells.empty

    def test_multiple_spells(self):
        df = make_df([10, 0, 0, 0, 10, 0, 0, 0, 0, 10])
        spells = find_dry_spells(df, min_days=3)
        assert len(spells) == 2


# --- recommend_tank_size ---

class TestRecommendTankSize:
    def test_returns_three_options(self):
        options = recommend_tank_size(100000, 4)
        assert len(options) == 3

    def test_labels(self):
        options = recommend_tank_size(100000, 4)
        labels = [o["label"] for o in options]
        assert labels == ["Minimum", "Anbefalt", "Robust"]

    def test_ascending_size(self):
        options = recommend_tank_size(100000, 4)
        sizes = [o["liters"] for o in options]
        assert sizes[0] < sizes[1] < sizes[2]


# --- calculate_rain_energy ---

class TestRainEnergy:
    def test_basic(self):
        liters, energy_wh = calculate_rain_energy(10, 100, 10)
        assert liters == pytest.approx(1000.0)
        # E = mgh = 1000 * 9.81 * 10 = 98100 J = 27.25 Wh
        expected_wh = 1000 * G * 10 / 3600
        assert energy_wh == pytest.approx(expected_wh)

    def test_zero_height(self):
        _, energy_wh = calculate_rain_energy(10, 100, 0)
        assert energy_wh == 0.0

    def test_zero_rain(self):
        liters, energy_wh = calculate_rain_energy(0, 100, 10)
        assert liters == 0.0
        assert energy_wh == 0.0


# --- co2_offset ---

class TestCO2Offset:
    def test_keys(self):
        result = co2_offset(1000)
        assert "NO" in result
        assert "EU" in result

    def test_eu_higher_than_norway(self):
        result = co2_offset(1000)
        assert result["EU"] > result["NO"]


# --- practical_equivalents ---

class TestPracticalEquivalents:
    def test_keys(self):
        result = practical_equivalents(1000)
        assert set(result.keys()) == {"phone_charges", "led_bulb_hours", "laptop_charges", "electric_bike_km"}

    def test_positive(self):
        result = practical_equivalents(1000)
        assert all(v > 0 for v in result.values())


# --- monthly_summary / seasonal_summary ---

class TestSummaries:
    def test_monthly_summary(self):
        df = make_df([5] * 60)  # 60 days of 5mm rain
        ms = monthly_summary(df)
        assert len(ms) >= 1
        assert "total_mm" in ms.columns

    def test_seasonal_summary(self):
        df = make_df([5] * 60)
        ss = seasonal_summary(df)
        assert len(ss) >= 1
        assert "total_mm" in ss.columns


# --- daily_collection ---

class TestDailyCollection:
    def test_output(self):
        df = make_df([10, 20])
        buildings = [Building("A", 100)]
        result = daily_collection(df, buildings)
        assert len(result) == 2
        assert result["liters"].iloc[0] == pytest.approx(water_collected(10, 100))

    def test_multiple_buildings(self):
        df = make_df([10])
        buildings = [Building("A", 100), Building("B", 200)]
        result = daily_collection(df, buildings)
        assert len(result) == 2  # 1 day * 2 buildings
