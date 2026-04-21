import pytest

from backend.economics import (
    COST_ESTIMATES, CAPITAL_CATEGORIES, OPERATING_CATEGORIES,
    find_best_estimate, interpolate_cost, lifecycle_cost,
    cost_per_person, cost_per_liter, cost_breakdown,
)


class TestCostData:
    def test_five_tiers(self):
        assert len(COST_ESTIMATES) == 5

    def test_capital_categories_sum_to_one(self):
        total = sum(share for _, share in CAPITAL_CATEGORIES)
        assert total == pytest.approx(1.0)

    def test_operating_categories_sum_to_one(self):
        total = sum(share for _, share in OPERATING_CATEGORIES)
        assert total == pytest.approx(1.0)

    def test_costs_ascending(self):
        for est in COST_ESTIMATES:
            assert est.capital_low <= est.capital_high
            assert est.annual_operating_low <= est.annual_operating_high


class TestFindBestEstimate:
    def test_household(self):
        est = find_best_estimate(4)
        assert est.label == "Enebolig / husholdning"

    def test_apartment(self):
        est = find_best_estimate(50)
        assert est.label == "Boligblokk (20 enheter)"

    def test_below_minimum_returns_smallest(self):
        est = find_best_estimate(1)
        assert est == COST_ESTIMATES[0]

    def test_above_maximum_returns_largest(self):
        est = find_best_estimate(5000)
        assert est == COST_ESTIMATES[-1]


class TestInterpolateCost:
    def test_at_low_end(self):
        est = COST_ESTIMATES[0]  # household: 4-6 people
        capital, operating = interpolate_cost(est.capacity_low, est)
        assert capital == est.capital_low
        assert operating == est.annual_operating_low

    def test_at_high_end(self):
        est = COST_ESTIMATES[0]
        capital, operating = interpolate_cost(est.capacity_high, est)
        assert capital == est.capital_high
        assert operating == est.annual_operating_high

    def test_midpoint(self):
        est = COST_ESTIMATES[0]  # 15000-45000 for 4-6 people
        mid_pop = (est.capacity_low + est.capacity_high) / 2
        capital, operating = interpolate_cost(mid_pop, est)
        assert est.capital_low < capital < est.capital_high


class TestLifecycleCost:
    def test_year_zero(self):
        assert lifecycle_cost(100_000, 10_000, 0) == 100_000

    def test_year_ten(self):
        assert lifecycle_cost(100_000, 10_000, 10) == 200_000

    def test_year_twenty(self):
        assert lifecycle_cost(100_000, 10_000, 20) == 300_000


class TestCostPerPerson:
    def test_basic(self):
        assert cost_per_person(40_000, 4) == pytest.approx(10_000)

    def test_zero_population(self):
        assert cost_per_person(40_000, 0) == 0


class TestCostPerLiter:
    def test_basic(self):
        # 100k cost, 100k liters/year, 10 years = 100k / 1M = 0.10
        result = cost_per_liter(100_000, 100_000, 10)
        assert result == pytest.approx(0.10)

    def test_zero_liters(self):
        assert cost_per_liter(100_000, 0, 10) == 0


class TestCostBreakdown:
    def test_categories_match(self):
        breakdown = cost_breakdown(100_000, CAPITAL_CATEGORIES)
        assert len(breakdown) == len(CAPITAL_CATEGORIES)

    def test_sums_approximately(self):
        breakdown = cost_breakdown(100_000, CAPITAL_CATEGORIES)
        total = sum(amount for _, amount in breakdown)
        assert abs(total - 100_000) <= len(CAPITAL_CATEGORIES)  # rounding tolerance
