from ai_act_toolkit.obligations import EvidenceKind, obligations_for
from ai_act_toolkit.risk_engine import ClassificationResult, RiskClass


def _articles(classification):
    return [o.article for o in obligations_for(classification)]


def test_high_risk_yields_articles_9_to_15():
    result = ClassificationResult(RiskClass.HIGH_RISK, "Art. 6(1): Sicherheitsbauteil")
    assert _articles(result) == [
        "Art. 9",
        "Art. 10",
        "Art. 11",
        "Art. 12",
        "Art. 13",
        "Art. 14",
        "Art. 15",
    ]


def test_limited_risk_yields_only_article_50():
    result = ClassificationResult(RiskClass.LIMITED_RISK, "Art. 50: Transparenzpflicht")
    assert _articles(result) == ["Art. 50"]


def test_minimal_risk_yields_no_obligations():
    result = ClassificationResult(RiskClass.MINIMAL_RISK, "keine Kategorie")
    assert obligations_for(result) == []


def test_prohibited_practice_yields_article_5():
    result = ClassificationResult(RiskClass.UNACCEPTABLE, "Art. 5: verbotene Praktik")
    assert _articles(result) == ["Art. 5"]


def test_only_articles_10_and_15_are_provable_by_technical_test():
    result = ClassificationResult(RiskClass.HIGH_RISK, "Art. 6(1): Sicherheitsbauteil")
    provable = [
        o.article
        for o in obligations_for(result)
        if o.evidence_kind is EvidenceKind.TECHNICAL_TEST
    ]
    assert provable == ["Art. 10", "Art. 15"]


def test_articles_12_to_14_are_process_obligations():
    result = ClassificationResult(RiskClass.HIGH_RISK, "Art. 6(1): Sicherheitsbauteil")
    process = [
        o.article
        for o in obligations_for(result)
        if o.evidence_kind is EvidenceKind.PROCESS
    ]
    assert process == ["Art. 12", "Art. 13", "Art. 14"]
