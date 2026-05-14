import pytest

from backend.lonnsomhet import (
    INSTALLATION_UNIT_COSTS, annual_savings, installation_cost,
    investment_analysis,
)
from backend.economics import lifecycle_cost


class TestInstallationCost:
    def test_itemised_keys(self):
        cost = installation_cost(50_000, 2000)
        for key in ["tank", "heat_exchanger", "pump_and_controls",
                    "piping", "labor", "total"]:
            assert key in cost

    def test_total_equals_sum_of_parts(self):
        cost = installation_cost(50_000, 2000)
        parts = ["tank", "heat_exchanger", "pump_and_controls", "piping", "labor"]
        assert cost["total"] == sum(cost[p] for p in parts)

    def test_tank_scales_with_capacity(self):
        small = installation_cost(10_000, 500)
        big = installation_cost(100_000, 500)
        assert big["tank"] == 10 * small["tank"]

    def test_piping_scales_with_roof(self):
        narrow = installation_cost(10_000, 100)
        wide = installation_cost(10_000, 1000)
        assert wide["piping"] == 10 * narrow["piping"]

    def test_uses_unit_costs(self):
        cost = installation_cost(10_000, 500)
        p = INSTALLATION_UNIT_COSTS
        assert cost["tank"] == 10_000 * p["tank_per_liter"]
        assert cost["heat_exchanger"] == p["heat_exchanger"]
        assert cost["piping"] == 500 * p["piping_per_m2_roof"]

    def test_custom_unit_costs(self):
        custom = dict(INSTALLATION_UNIT_COSTS)
        custom["tank_per_liter"] = 20
        cost = installation_cost(1000, 100, unit_costs=custom)
        assert cost["tank"] == 20_000


class TestAnnualSavings:
    def test_itemised_keys(self):
        s = annual_savings(100_000, 1000, 200)
        for key in ["water", "cooling", "electricity", "total"]:
            assert key in s

    def test_total_equals_sum_of_parts(self):
        s = annual_savings(100_000, 1000, 200)
        assert s["total"] == s["water"] + s["cooling"] + s["electricity"]

    def test_water_uses_default_price(self):
        s = annual_savings(100_000, 0, 0)
        expected = 100_000 * INSTALLATION_UNIT_COSTS["water_price_per_liter"]
        assert s["water"] == pytest.approx(expected)
        assert s["cooling"] == 0
        assert s["electricity"] == 0

    def test_custom_water_price(self):
        s = annual_savings(100_000, 0, 0, water_price_per_liter=0.030)
        assert s["water"] == pytest.approx(100_000 * 0.030)

    def test_custom_electricity_price(self):
        s = annual_savings(0, 0, 1000, electricity_price_kwh=2.00)
        assert s["electricity"] == pytest.approx(2000)

    def test_zero_inputs_zero_savings(self):
        s = annual_savings(0, 0, 0)
        assert s["total"] == 0


class TestInvestmentAnalysis:
    def test_returns_expected_keys(self):
        r = investment_analysis(50_000, 2000, 1_000_000, 4000, 500)
        for key in ["capex", "savings", "annual_savings_gross",
                   "annual_maintenance", "annual_savings_total",
                   "cumulative_savings", "payback_years", "npv",
                   "total_lifecycle_cost", "years"]:
            assert key in r

    def test_default_years_is_20(self):
        r = investment_analysis(50_000, 2000, 1_000_000, 4000, 500)
        assert r["years"] == 20
        assert len(r["cumulative_savings"]) == 21  # year 0..20

    def test_year_zero_is_negative_capex(self):
        r = investment_analysis(50_000, 2000, 1_000_000, 4000, 500)
        assert r["cumulative_savings"][0] == -r["capex"]["total"]

    def test_payback_when_savings_high_enough(self):
        # Crank water price high → fast payback
        r = investment_analysis(
            10_000, 100, 1_000_000, 0, 0,
            water_price_per_liter=1.0,  # absurdly high to force payback
        )
        assert r["payback_years"] is not None
        assert r["payback_years"] > 0

    def test_payback_none_when_savings_below_maintenance(self):
        # Zero savings → payback never
        r = investment_analysis(50_000, 2000, 0, 0, 0)
        assert r["payback_years"] is None

    def test_npv_matches_last_cumulative(self):
        r = investment_analysis(50_000, 2000, 1_000_000, 4000, 500)
        assert r["npv"] == r["cumulative_savings"][-1]

    def test_uses_lifecycle_cost_helper(self):
        # Verify total_lifecycle_cost matches the existing economics.lifecycle_cost
        r = investment_analysis(50_000, 2000, 0, 0, 0, years=15)
        expected = lifecycle_cost(r["capex"]["total"], r["annual_maintenance"], 15)
        assert r["total_lifecycle_cost"] == expected

    def test_maintenance_scales_with_capex(self):
        small = investment_analysis(5_000, 100, 100_000, 0, 0)
        big = investment_analysis(50_000, 1000, 100_000, 0, 0)
        # Both use 2% of capex by default
        assert big["annual_maintenance"] > small["annual_maintenance"]
        assert big["annual_maintenance"] / small["annual_maintenance"] == pytest.approx(
            big["capex"]["total"] / small["capex"]["total"], rel=0.01
        )
