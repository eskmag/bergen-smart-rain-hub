import pytest

from backend.scales import (
    SCALES, SCALE_PRESETS, INFRASTRUCTURE_FACILITIES,
    aggregate_neighbourhood,
)
from backend.analysis import BUILDING_PRESETS


class TestScales:
    def test_three_scales(self):
        assert set(SCALES.keys()) == {"household", "neighbourhood", "infrastructure"}

    def test_scales_have_required_fields(self):
        for key, spec in SCALES.items():
            assert spec.key == key
            assert spec.label
            assert spec.description
            assert len(spec.typical_population) == 2
            assert len(spec.typical_tank_liters) == 2
            assert len(spec.typical_buildings) == 2
            assert spec.treatment_level
            assert spec.governance_note
            assert len(spec.cost_range_nok) == 2

    def test_household_cost_range_matches_docs(self):
        # docs 9.1: NOK 15,000–45,000
        assert SCALES["household"].cost_range_nok == (15_000, 45_000)

    def test_neighbourhood_cost_range_matches_docs(self):
        # docs 9.2: NOK 800,000–2,500,000
        assert SCALES["neighbourhood"].cost_range_nok == (800_000, 2_500_000)

    def test_infrastructure_cost_range_plausible(self):
        low, high = SCALES["infrastructure"].cost_range_nok
        assert low > 0
        assert high > low
        assert high >= 1_000_000  # infrastructure scale is expensive


class TestScalePresets:
    def test_household_presets_exist(self):
        for key in SCALE_PRESETS["household"]:
            assert key in BUILDING_PRESETS, f"{key} missing from BUILDING_PRESETS"

    def test_neighbourhood_presets_exist(self):
        for key in SCALE_PRESETS["neighbourhood"]:
            assert key in BUILDING_PRESETS

    def test_infrastructure_uses_facilities_not_presets(self):
        assert SCALE_PRESETS["infrastructure"] == []
        assert len(INFRASTRUCTURE_FACILITIES) > 0


class TestInfrastructureFacilities:
    def test_required_keys(self):
        required = {"label", "roof_area_m2", "default_people", "height_m", "description"}
        for key, facility in INFRASTRUCTURE_FACILITIES.items():
            assert required.issubset(facility.keys()), f"{key} missing keys"

    def test_haukeland_is_large(self):
        # Haukeland is the flagship example in docs 9.3
        hk = INFRASTRUCTURE_FACILITIES["haukeland"]
        assert hk["roof_area_m2"] >= 10_000
        assert hk["default_people"] >= 1_000

    def test_all_facilities_have_positive_values(self):
        for key, facility in INFRASTRUCTURE_FACILITIES.items():
            assert facility["roof_area_m2"] > 0
            assert facility["default_people"] > 0
            assert facility["height_m"] > 0


class TestAggregateNeighbourhood:
    def test_single_building_equivalent(self):
        preset = BUILDING_PRESETS["leilighet_liten"]
        result = aggregate_neighbourhood(preset, 1)
        assert result["roof_area_m2"] == preset["roof_area_m2"]
        assert result["default_people"] == preset["default_people"]
        assert result["height_m"] == preset["height_m"]

    def test_ten_buildings_multiplies(self):
        preset = BUILDING_PRESETS["leilighet_liten"]
        result = aggregate_neighbourhood(preset, 10)
        assert result["roof_area_m2"] == preset["roof_area_m2"] * 10
        assert result["default_people"] == preset["default_people"] * 10

    def test_height_not_multiplied(self):
        preset = BUILDING_PRESETS["leilighet_stor"]
        result = aggregate_neighbourhood(preset, 5)
        assert result["height_m"] == preset["height_m"]

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            aggregate_neighbourhood(BUILDING_PRESETS["enebolig"], 0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            aggregate_neighbourhood(BUILDING_PRESETS["enebolig"], -1)

    def test_label_reflects_count(self):
        preset = BUILDING_PRESETS["rekkehus"]
        result = aggregate_neighbourhood(preset, 8)
        assert "8" in result["label"]
        assert preset["label"] in result["label"]

    def test_building_count_stored(self):
        result = aggregate_neighbourhood(BUILDING_PRESETS["rekkehus"], 12)
        assert result["building_count"] == 12
