from ai_act_toolkit.risk_engine import (
    Annex3Area,
    RiskClass,
    UseCaseAttributes,
    classify,
)


def _base_attrs(**overrides):
    defaults = dict(
        is_prohibited_practice=False,
        is_safety_component_regulated_product=False,
        is_annex3_area=False,
        annex3_area=Annex3Area.NONE,
        significant_risk_to_health_safety_fundamental_rights=False,
        has_transparency_obligation=False,
    )
    defaults.update(overrides)
    return UseCaseAttributes(**defaults)


def test_prohibited_practice_is_unacceptable():
    result = classify(_base_attrs(is_prohibited_practice=True))
    assert result.risk_class == RiskClass.UNACCEPTABLE


def test_safety_component_is_high_risk():
    result = classify(_base_attrs(is_safety_component_regulated_product=True))
    assert result.risk_class == RiskClass.HIGH_RISK


def test_annex3_area_with_significant_risk_is_high_risk():
    result = classify(
        _base_attrs(
            is_annex3_area=True,
            annex3_area=Annex3Area.EMPLOYMENT,
            significant_risk_to_health_safety_fundamental_rights=True,
        )
    )
    assert result.risk_class == RiskClass.HIGH_RISK
    assert "employment" in result.matched_rule


def test_annex3_area_without_significant_risk_is_not_high_risk():
    result = classify(
        _base_attrs(
            is_annex3_area=True,
            annex3_area=Annex3Area.EMPLOYMENT,
            significant_risk_to_health_safety_fundamental_rights=False,
        )
    )
    assert result.risk_class != RiskClass.HIGH_RISK


def test_transparency_obligation_is_limited_risk():
    result = classify(_base_attrs(has_transparency_obligation=True))
    assert result.risk_class == RiskClass.LIMITED_RISK


def test_no_criteria_is_minimal_risk():
    result = classify(_base_attrs())
    assert result.risk_class == RiskClass.MINIMAL_RISK


def test_prohibited_practice_wins_over_everything_else():
    result = classify(
        _base_attrs(
            is_prohibited_practice=True,
            is_safety_component_regulated_product=True,
        )
    )
    assert result.risk_class == RiskClass.UNACCEPTABLE
