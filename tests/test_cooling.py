import pandas as pd
import pytest

from backend.analysis import (
    Building, COOLING_CONFIG, annual_cooling_simulation,
    passive_cooling_potential,
)


def make_year_df(precip_mm=3.0, year=2025):
    dates = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "precipitation_mm": [precip_mm] * 365,
    })


class TestPassiveCoolingPotential:
    def test_cool_tank_warm_room_yields_cooling(self):
        result = passive_cooling_potential(10.0, 23.0, 5000, 200)
        assert result["cooling_possible"] is True
        assert result["cooling_kwh"] > 0
        assert result["delta_t"] == pytest.approx(13.0)

    def test_warm_tank_no_cooling(self):
        # Tank at critical_tank_temp_c → cooling not viable
        result = passive_cooling_potential(16.0, 23.0, 5000, 200)
        assert result["cooling_possible"] is False
        assert result["cooling_kwh"] == 0

    def test_no_delta_no_cooling(self):
        # Tank == room temp → no cooling
        result = passive_cooling_potential(23.0, 23.0, 5000, 200)
        assert result["cooling_possible"] is False
        assert result["cooling_kwh"] == 0

    def test_inverted_delta_no_cooling(self):
        # Tank warmer than room (shouldn't happen for nedgravd, but be safe)
        result = passive_cooling_potential(15.0, 12.0, 5000, 200)
        assert result["cooling_possible"] is False

    def test_zero_available_no_cooling(self):
        result = passive_cooling_potential(10.0, 23.0, 0, 200)
        assert result["cooling_possible"] is False

    def test_mass_capped_by_floor_area(self):
        # 100 000 L available but only 50 m² floor → capped at 100 kg
        big = passive_cooling_potential(10.0, 23.0, 100_000, 50)
        small = passive_cooling_potential(10.0, 23.0, 100, 50)
        # Same mass cap, same cooling
        assert big["cooling_kwh"] == pytest.approx(small["cooling_kwh"])

    def test_mass_capped_by_available_when_smaller(self):
        # Floor area allows 1000 kg but only 200 L available
        result = passive_cooling_potential(10.0, 23.0, 200, 500)
        # Should be limited by available, not floor area
        cp = COOLING_CONFIG["specific_heat_water"]
        expected_kwh = 200 * cp * 13.0 / 3_600_000
        assert result["cooling_kwh"] == pytest.approx(expected_kwh)


class TestAnnualCoolingSimulation:
    def test_columns_present(self):
        sim = annual_cooling_simulation(
            make_year_df(), [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
        )
        for col in ["date", "air_temp_c", "tank_temp_c",
                    "available_liters", "cooling_kwh", "cooling_active"]:
            assert col in sim.columns

    def test_length_matches_input(self):
        df = make_year_df()
        sim = annual_cooling_simulation(
            df, [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
        )
        assert len(sim) == len(df)

    def test_cooling_only_in_summer(self):
        sim = annual_cooling_simulation(
            make_year_df(), [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
        )
        active_months = sim[sim["cooling_active"]]["date"].dt.month.unique()
        # Bergen summer (June-August) should be active under the 14°C threshold;
        # winter months should not.
        assert set(active_months).issubset({5, 6, 7, 8, 9})

    def test_no_cooling_in_winter(self):
        sim = annual_cooling_simulation(
            make_year_df(), [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
        )
        winter = sim[sim["date"].dt.month.isin([12, 1, 2])]
        assert (winter["cooling_kwh"] == 0).all()

    def test_respects_locked_reserve(self):
        # Crank reserve to 100% — available_liters = 0 always → no cooling
        sim = annual_cooling_simulation(
            make_year_df(), [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
            reserve_pct=1.0,
        )
        assert sim["cooling_kwh"].sum() == 0

    def test_uses_real_air_temp_when_present(self):
        # Provide air_temperature_c column with cool summer
        dates = pd.date_range("2025-06-01", periods=30, freq="D")
        df = pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"),
            "precipitation_mm": [2.0] * 30,
            "air_temperature_c": [10.0] * 30,  # cold summer → no cooling demand
        })
        sim = annual_cooling_simulation(
            df, [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
        )
        # 10°C air → below cooling threshold → no active days
        assert sim["cooling_kwh"].sum() == 0

    def test_falls_back_to_normals_when_temp_missing(self):
        # No temperature column → fallback to BERGEN_AIR_TEMP_NORMALS
        sim = annual_cooling_simulation(
            make_year_df(), [Building("t", roof_area_m2=2000)],
            tank_capacity_liters=50_000, population=200,
        )
        # Bergen July normal (17°C) > 14°C threshold → some cooling expected
        july_cooling = sim[sim["date"].dt.month == 7]["cooling_kwh"].sum()
        assert july_cooling > 0
