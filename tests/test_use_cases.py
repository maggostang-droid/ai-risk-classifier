from ai_act_toolkit.risk_engine import RiskClass, classify
from ai_act_toolkit.use_cases import ALL_USE_CASES, CHATBOT, COMFORT_SYSTEM, RECRUITING


def test_all_use_cases_present():
    assert {uc.key for uc in ALL_USE_CASES} == {"comfort_system", "recruiting", "chatbot"}


def test_comfort_system_classifies_as_high_risk():
    assert classify(COMFORT_SYSTEM.attributes).risk_class == RiskClass.HIGH_RISK


def test_recruiting_classifies_as_high_risk():
    assert classify(RECRUITING.attributes).risk_class == RiskClass.HIGH_RISK


def test_chatbot_classifies_as_limited_risk():
    assert classify(CHATBOT.attributes).risk_class == RiskClass.LIMITED_RISK
