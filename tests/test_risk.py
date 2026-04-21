import pytest

from backend.risk import (
    RISKS, CCPS, CATEGORY_LABELS, OVERALL_SEVERITY_ORDER,
    assess_scenario_risks, Risk, CriticalControlPoint,
)


class TestRiskData:
    def test_twelve_risks(self):
        assert len(RISKS) == 12

    def test_risk_fields(self):
        for risk in RISKS:
            assert risk.name
            assert risk.category in CATEGORY_LABELS
            assert risk.likelihood in ("Lav", "Middels", "Høy")
            assert risk.impact in ("Middels", "Høy", "Kritisk")
            assert risk.overall in ("Middels", "Høy", "Kritisk")
            assert risk.mitigation

    def test_critical_risks_exist(self):
        critical = [r for r in RISKS if r.overall == "Kritisk"]
        assert len(critical) == 3

    def test_six_ccps(self):
        assert len(CCPS) == 6

    def test_ccp_ids_sequential(self):
        ids = [ccp.id for ccp in CCPS]
        assert ids == [f"CCP-{i}" for i in range(1, 7)]

    def test_ccp_fields(self):
        for ccp in CCPS:
            assert ccp.name
            assert ccp.description
            assert ccp.control_measure


class TestAssessScenarioRisks:
    def test_returns_all_risks(self):
        results = assess_scenario_risks(5000, 10, 100)
        assert len(results) == 12

    def test_sorted_descending(self):
        results = assess_scenario_risks(5000, 10, 100)
        scores = [score for _, score, _ in results]
        assert scores == sorted(scores, reverse=True)

    def test_small_tank_elevates_dry_period_risk(self):
        # Small tank for many people
        results = assess_scenario_risks(500, 50, 100)
        dry_risk = next(
            (r, s, reason) for r, s, reason in results
            if "tørkeperiode" in r.name.lower()
        )
        assert dry_risk[1] > OVERALL_SEVERITY_ORDER["Høy"]  # score boosted

    def test_large_infrastructure_elevates_relevant_risks(self):
        results = assess_scenario_risks(50000, 200, 2000)
        # Infrastructure-scale risks should be boosted
        scores = {r.name: s for r, s, _ in results}
        assert scores["Strømbrudd deaktiverer behandlingsutstyr"] > OVERALL_SEVERITY_ORDER["Høy"]

    def test_reason_populated_for_relevant_risks(self):
        results = assess_scenario_risks(500, 50, 100)
        reasons = [reason for _, _, reason in results if reason]
        assert len(reasons) > 0

    def test_days_empty_boosts_dry_risk(self):
        results_no_empty = assess_scenario_risks(5000, 10, 100, days_tank_empty=0)
        results_with_empty = assess_scenario_risks(5000, 10, 100, days_tank_empty=30)
        score_no = next(s for r, s, _ in results_no_empty if "tørkeperiode" in r.name.lower())
        score_with = next(s for r, s, _ in results_with_empty if "tørkeperiode" in r.name.lower())
        assert score_with > score_no
