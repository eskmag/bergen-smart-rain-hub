import pandas as pd
import pytest

from backend.analysis import (
    Building, EMERGENCY_RESERVE_DAYS, EMERGENCY_RESERVE_PCT,
    available_volume, emergency_reserve_liters, storage_simulation,
)


class TestEmergencyReserveLiters:
    def test_pct_floor_wins_for_typical_household(self):
        # 4 people × 13 L × 7 days = 364 L; 25% × 10 000 = 2500 L → pct wins
        assert emergency_reserve_liters(10_000, 4) == 2500

    def test_days_floor_wins_for_dense_neighbourhood(self):
        # 200 people × 13 × 7 = 18 200 L; 25% × 50 000 = 12 500 L → days wins
        assert emergency_reserve_liters(50_000, 200) == 18_200

    def test_capped_at_tank_capacity(self):
        # 100 people × 13 × 7 = 9100 L; tank only 5000 L → cap at tank
        assert emergency_reserve_liters(5_000, 100) == 5_000

    def test_zero_tank_returns_zero(self):
        assert emergency_reserve_liters(0, 50) == 0

    def test_zero_population_uses_pct_floor(self):
        # 0 people × ... = 0 days floor; pct still applies
        assert emergency_reserve_liters(10_000, 0) == 2_500

    def test_custom_reserve_days(self):
        # 4 people × 13 × 14 = 728 L; 25% × 10 000 = 2500 L → pct still wins
        assert emergency_reserve_liters(10_000, 4, reserve_days=14) == 2500
        # 50 people × 13 × 14 = 9100 L; 25% × 10 000 = 2500 L → days wins
        assert emergency_reserve_liters(10_000, 50, reserve_days=14) == 9100

    def test_custom_reserve_pct(self):
        # 50% of tank capacity
        assert emergency_reserve_liters(10_000, 4, reserve_pct=0.5) == 5000


class TestAvailableVolume:
    def test_above_reserve_returns_difference(self):
        # tank=10000, reserve=2500 → available at 8000 = 5500
        assert available_volume(8_000, 10_000, 4) == 5500

    def test_at_reserve_level_returns_zero(self):
        assert available_volume(2_500, 10_000, 4) == 0

    def test_below_reserve_returns_zero(self):
        assert available_volume(1_000, 10_000, 4) == 0

    def test_full_tank(self):
        # full 10000, reserve 2500 → 7500 available
        assert available_volume(10_000, 10_000, 4) == 7_500

    def test_uses_default_constants(self):
        # Confirm default values match the configured constants
        assert EMERGENCY_RESERVE_DAYS == 7
        assert EMERGENCY_RESERVE_PCT == 0.25


class TestStorageSimulationReserveColumns:
    def _make_df(self, n_days=10, mm=5):
        dates = pd.date_range("2025-06-01", periods=n_days, freq="D")
        return pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"),
            "precipitation_mm": [mm] * n_days,
        })

    def test_available_columns_present(self):
        df = self._make_df()
        sim = storage_simulation(
            df, [Building("test", roof_area_m2=200)],
            tank_capacity_liters=10_000, population=4,
        )
        assert "available_liters" in sim.columns
        assert "available_pct" in sim.columns

    def test_available_never_negative(self):
        df = self._make_df(n_days=30, mm=0)  # no rain → tank drains
        sim = storage_simulation(
            df, [Building("test", roof_area_m2=200)],
            tank_capacity_liters=10_000, population=20,
        )
        assert (sim["available_liters"] >= 0).all()
        assert (sim["available_pct"] >= 0).all()

    def test_available_consistent_with_reserve(self):
        df = self._make_df()
        sim = storage_simulation(
            df, [Building("test", roof_area_m2=500)],
            tank_capacity_liters=10_000, population=4,
        )
        reserve = emergency_reserve_liters(10_000, 4)
        for _, row in sim.iterrows():
            expected = max(0, row["tank_level_liters"] - reserve)
            assert row["available_liters"] == pytest.approx(expected)

    def test_available_pct_matches_liters(self):
        df = self._make_df()
        sim = storage_simulation(
            df, [Building("test", roof_area_m2=300)],
            tank_capacity_liters=20_000, population=20,
        )
        for _, row in sim.iterrows():
            expected_pct = row["available_liters"] / 20_000 * 100
            assert row["available_pct"] == pytest.approx(expected_pct)

    def test_reserve_kwargs_propagate(self):
        df = self._make_df()
        # Crank reserve to 100% — available should always be 0
        sim = storage_simulation(
            df, [Building("test", roof_area_m2=300)],
            tank_capacity_liters=10_000, population=4,
            reserve_pct=1.0,
        )
        assert (sim["available_liters"] == 0).all()
