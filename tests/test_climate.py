import pandas as pd
import pytest

from backend.climate import (
    SCENARIOS, apply_climate_projection, compare_scenarios,
)


def make_df(precip_values):
    dates = pd.date_range("2025-01-01", periods=len(precip_values), freq="D")
    return pd.DataFrame({
        "station_id": "SN50540",
        "date": dates.strftime("%Y-%m-%d"),
        "precipitation_mm": precip_values,
    })


class TestScenarios:
    def test_three_scenarios(self):
        assert len(SCENARIOS) == 3

    def test_required_keys(self):
        for key, params in SCENARIOS.items():
            assert "label" in params
            assert "intensity_factor" in params
            assert "dry_spell_factor" in params
            assert "description" in params

    def test_historical_is_neutral(self):
        params = SCENARIOS["historical"]
        assert params["intensity_factor"] == 1.0
        assert params["dry_spell_factor"] == 1.0


class TestApplyClimateProjection:
    def test_historical_unchanged(self):
        df = make_df([10, 0, 5, 0, 20])
        result = apply_climate_projection(df, "historical")
        assert list(result["precipitation_mm"]) == [10, 0, 5, 0, 20]

    def test_moderate_increases_rainy_days(self):
        df = make_df([10, 0, 5, 0, 20])
        result = apply_climate_projection(df, "moderate")
        # Rainy days (>=1mm) should increase by 10%
        assert result.iloc[0]["precipitation_mm"] == pytest.approx(11.0)
        assert result.iloc[2]["precipitation_mm"] == pytest.approx(5.5)
        assert result.iloc[4]["precipitation_mm"] == pytest.approx(22.0)

    def test_dry_days_stay_dry(self):
        df = make_df([10, 0, 0, 10])
        result = apply_climate_projection(df, "moderate")
        # Original dry days remain dry or get drier
        assert result.iloc[1]["precipitation_mm"] <= 0.0
        assert result.iloc[2]["precipitation_mm"] <= 0.0

    def test_pessimistic_stronger_than_moderate(self):
        df = make_df([10, 0, 5])
        moderate = apply_climate_projection(df, "moderate")
        pessimistic = apply_climate_projection(df, "pessimistic")
        # Pessimistic should increase rainy day values more
        assert pessimistic.iloc[0]["precipitation_mm"] > moderate.iloc[0]["precipitation_mm"]

    def test_preserves_columns(self):
        df = make_df([10, 0, 5])
        result = apply_climate_projection(df, "moderate")
        assert "station_id" in result.columns
        assert "date" in result.columns
        assert "precipitation_mm" in result.columns
        assert "dry" not in result.columns  # temp columns removed
        assert "spell_id" not in result.columns

    def test_same_length(self):
        df = make_df([10, 0, 5, 0, 20, 3, 0, 0, 15])
        result = apply_climate_projection(df, "pessimistic")
        assert len(result) == len(df)


class TestCompareScenarios:
    def test_returns_all_scenarios(self):
        df = make_df([10, 0, 0, 0, 5, 0, 20])
        results = compare_scenarios(df)
        assert len(results) == 3

    def test_result_structure(self):
        df = make_df([10, 0, 5])
        results = compare_scenarios(df)
        for r in results:
            assert "scenario" in r
            assert "label" in r
            assert "total_precip_mm" in r
            assert "dry_days" in r
            assert "longest_dry_spell" in r

    def test_historical_matches_raw(self):
        df = make_df([10, 0, 0, 0, 5])
        results = compare_scenarios(df)
        hist = next(r for r in results if r["scenario"] == "historical")
        assert hist["total_precip_mm"] == pytest.approx(15.0)
        assert hist["dry_days"] == 3

    def test_custom_scenario_list(self):
        df = make_df([10, 0, 5])
        results = compare_scenarios(df, scenarios=["historical", "moderate"])
        assert len(results) == 2
