import pytest

from backend.bydel import BYDELER, city_potential, suitable_roof_m2


def test_bydeler_cover_bergen_population():
    total = sum(b["population"] for b in BYDELER.values())
    assert 250_000 < total < 320_000


def test_all_eight_bydeler_present():
    assert set(BYDELER) == {
        "arna", "bergenhus", "fana", "fyllingsdalen",
        "laksevag", "ytrebygda", "arstad", "asane",
    }


def test_city_potential_structure():
    res = city_potential(participation_pct=0.20)
    assert set(res) >= {"bydeler", "total_daily_liters", "demand_coverage_pct",
                        "participation_pct", "assumptions"}
    assert len(res["bydeler"]) == len(BYDELER)
    row = res["bydeler"][0]
    assert set(row) >= {"key", "label", "population", "daily_yield_liters",
                        "demand_liters", "coverage_pct"}


def test_more_participation_more_coverage():
    low = city_potential(participation_pct=0.10)["demand_coverage_pct"]
    high = city_potential(participation_pct=0.50)["demand_coverage_pct"]
    assert high > low


def test_invalid_participation_raises():
    with pytest.raises(ValueError):
        city_potential(participation_pct=1.5)
    with pytest.raises(ValueError):
        city_potential(participation_pct=0.0)
    with pytest.raises(ValueError):
        city_potential(participation_pct=-0.2)


def test_dense_bydel_density_factor_applied():
    # Bergenhus (factor 0.6) must have less suitable roof per capita than
    # a bydel without a density factor.
    per_capita_bergenhus = (
        suitable_roof_m2("bergenhus") / BYDELER["bergenhus"]["population"]
    )
    per_capita_fana = suitable_roof_m2("fana") / BYDELER["fana"]["population"]
    assert per_capita_bergenhus < per_capita_fana


def test_persons_covered_derived_from_yield():
    from backend.analysis import WATER_NEEDS
    res = city_potential(participation_pct=0.20)
    expected = round(res["total_daily_liters"] / WATER_NEEDS["survival_total"])
    assert res["persons_covered"] == expected
    assert res["persons_covered"] > 0


def test_persons_covered_monotonic_in_participation():
    low = city_potential(participation_pct=0.10)["persons_covered"]
    high = city_potential(participation_pct=0.50)["persons_covered"]
    assert high > low


def test_roof_assumption_exposed():
    from backend.bydel import SUITABLE_ROOF_M2_PER_CAPITA
    res = city_potential(participation_pct=0.20)
    assert res["roof_m2_per_capita"] == SUITABLE_ROOF_M2_PER_CAPITA


def test_totals_are_sum_of_rows():
    res = city_potential(participation_pct=0.20)
    assert res["total_daily_liters"] == sum(
        r["daily_yield_liters"] for r in res["bydeler"])
    assert res["total_demand_liters"] == sum(
        r["demand_liters"] for r in res["bydeler"])
