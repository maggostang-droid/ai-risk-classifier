from ai_act_toolkit.risk_engine import RiskClass, classify
from ai_act_toolkit.use_cases import ALL_USE_CASES, CHATBOT, COMFORT_SYSTEM, RECRUITING


def test_all_use_cases_present():
    assert {uc.key for uc in ALL_USE_CASES} == {"comfort_system", "recruiting", "chatbot"}


def test_comfort_system_classifies_as_high_risk_with_metamorphic_demo():
    result = classify(COMFORT_SYSTEM.attributes)
    assert result.risk_class == RiskClass.HIGH_RISK
    assert COMFORT_SYSTEM.has_metamorphic_demo is True


def test_recruiting_classifies_as_high_risk_without_metamorphic_demo():
    result = classify(RECRUITING.attributes)
    assert result.risk_class == RiskClass.HIGH_RISK
    assert RECRUITING.has_metamorphic_demo is False


def test_chatbot_classifies_as_limited_risk():
    result = classify(CHATBOT.attributes)
    assert result.risk_class == RiskClass.LIMITED_RISK
    assert CHATBOT.has_metamorphic_demo is False
