import pandas as pd
import pytest

from backend.analysis import (
    HEAT_PUMP_CONFIG, annual_cop_improvement, cop_estimate,
    heat_pump_supplement_simulation, tank_temperature_series,
)


def make_year_df(year=2025):
    dates = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "precipitation_mm": [2.0] * 365,
    })


class TestCopEstimate:
    def test_warmer_source_higher_cop(self):
        cop_cold = cop_estimate(0, delivery_temp_c=35)
        cop_warm = cop_estimate(15, delivery_temp_c=35)
        assert cop_warm > cop_cold

    def test_lower_delivery_higher_cop(self):
        # Floor heating (35°C) is more efficient than radiators (60°C)
        cop_floor = cop_estimate(7, delivery_temp_c=35)
        cop_rad = cop_estimate(7, delivery_temp_c=60)
        assert cop_floor > cop_rad

    def test_carnot_efficiency_applied(self):
        cop = cop_estimate(7, delivery_temp_c=35)
        # Carnot at these temps ≈ 11; × 0.45 ≈ 5
        assert 4.5 < cop < 5.5

    def test_source_warmer_than_delivery_returns_one(self):
        # Heat pump can't add heat when source > delivery
        assert cop_estimate(50, delivery_temp_c=35) == 1.0

    def test_source_equal_delivery_returns_one(self):
        assert cop_estimate(35, delivery_temp_c=35) == 1.0


class TestHeatPumpSupplementSimulation:
    def test_columns_present(self):
        sim = heat_pump_supplement_simulation(make_year_df())
        for col in ["date", "air_temp_c", "tank_temp_c", "source",
                    "cop_used", "kwh_demand", "kwh_electricity",
                    "kwh_savings_vs_berg"]:
            assert col in sim.columns

    def test_picks_warmer_source(self):
        # Berg at 7°C; tank is warmer in summer (Sep peak ~10.8°C)
        sim = heat_pump_supplement_simulation(
            make_year_df(), berg_temp_c=7.0,
        )
        sep = sim[sim["date"].dt.month == 9]
        active_sep = sep[sep["kwh_demand"] > 0]
        # In September, when heating demand exists, rainwater is warmer
        if not active_sep.empty:
            assert (active_sep["source"] == "rainwater").all()

    def test_picks_berg_when_warmer(self):
        # Crank berg to 20°C — always warmer than the tank (max ~10.8°C)
        sim = heat_pump_supplement_simulation(
            make_year_df(), berg_temp_c=20.0, delivery_temp_c=35.0,
        )
        active = sim[sim["kwh_demand"] > 0]
        assert (active["source"] == "berg").all()

    def test_total_demand_matches_annual(self):
        annual = 50_000
        sim = heat_pump_supplement_simulation(
            make_year_df(), annual_demand_kwh=annual,
        )
        assert sim["kwh_demand"].sum() == pytest.approx(annual, rel=0.01)

    def test_electricity_less_than_demand(self):
        # COP > 1 means electricity used < heat delivered
        sim = heat_pump_supplement_simulation(make_year_df())
        assert sim["kwh_electricity"].sum() < sim["kwh_demand"].sum()

    def test_savings_nonnegative(self):
        sim = heat_pump_supplement_simulation(make_year_df())
        assert (sim["kwh_savings_vs_berg"] >= 0).all()

    def test_no_demand_in_summer(self):
        # July (15°C average air, above heating threshold of 15°C → near zero demand)
        sim = heat_pump_supplement_simulation(make_year_df())
        july = sim[sim["date"].dt.month == 7]
        # Most July days should have no demand
        assert (july["kwh_demand"] < 20).all()

    def test_uses_real_air_temp_when_present(self):
        df = make_year_df()
        # Provide synthetic mild winter
        df["air_temperature_c"] = [10.0] * 365
        sim = heat_pump_supplement_simulation(df)
        # 10°C air is below 15°C threshold → demand spread evenly
        # All days should have some demand
        assert (sim["kwh_demand"] > 0).all()


class TestAnnualCopImprovement:
    def test_uplift_positive_when_tank_warmer(self):
        df = make_year_df()
        ts = tank_temperature_series(df, "nedgravd")
        imp = annual_cop_improvement(ts, berg_temp_c=7.0)
        # Tank reaches ~10.8°C in September; mostly warmer than 7°C berg
        assert imp["cop_uplift"] > 0
        assert imp["cop_with_rainwater"] > imp["cop_baseline"]

    def test_no_uplift_when_berg_always_warmer(self):
        df = make_year_df()
        ts = tank_temperature_series(df, "nedgravd")
        imp = annual_cop_improvement(ts, berg_temp_c=20.0)
        # Berg always warmer → strategy picks berg → uplift = 0
        assert imp["cop_uplift"] == pytest.approx(0.0, abs=0.01)
        assert imp["rainwater_dominant_days"] == 0

    def test_rainwater_dominant_days_correct(self):
        df = make_year_df()
        ts = tank_temperature_series(df, "nedgravd")
        imp = annual_cop_improvement(ts, berg_temp_c=7.0)
        # Tank ranges 6.78-10.78°C; many days exceed 7°C
        assert 200 < imp["rainwater_dominant_days"] < 365
