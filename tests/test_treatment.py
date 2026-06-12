import pytest

from backend.treatment import (
    ROOF_MATERIALS, RISK_CLASSES, classify_roof, required_treatment,
)


def test_all_materials_have_valid_risk_class():
    for key, mat in ROOF_MATERIALS.items():
        assert mat["risk_class"] in RISK_CLASSES, key
        assert mat["label"]
        assert mat["description"]


def test_classify_roof_known_material():
    result = classify_roof("takstein")
    assert result["risk_class"] == "lav"


def test_classify_roof_lead_is_unsuitable():
    assert classify_roof("blybeslag")["risk_class"] == "uegnet"


def test_classify_roof_unknown_raises():
    with pytest.raises(KeyError):
        classify_roof("does-not-exist")


def test_required_treatment_low_risk_household():
    t = required_treatment("lav", "household")
    assert "Sedimentfilter" in t["barriers"]
    assert t["cost_low_nok"] > 0
    assert t["cost_high_nok"] >= t["cost_low_nok"]


def test_required_treatment_unsuitable_has_no_barriers():
    t = required_treatment("uegnet", "household")
    assert t["potable"] is False
    assert t["barriers"] == []


def test_required_treatment_infrastructure_includes_uv():
    t = required_treatment("middels", "infrastructure")
    assert any("UV" in b for b in t["barriers"])
