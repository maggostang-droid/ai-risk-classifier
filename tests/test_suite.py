from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.suite import run_suite

RISING = MetamorphicRelation(
    name="Steigend",
    description="Groesseres x darf das Ergebnis nicht senken.",
    transform=lambda inputs: {**inputs, "x": inputs["x"] + 1.0},
    check=lambda source, followup: followup >= source,
    evidence_for="Art. 15",
)

UNCHANGED = MetamorphicRelation(
    name="Unveraendert",
    description="y beeinflusst das Ergebnis nicht.",
    transform=lambda inputs: {**inputs, "y": inputs["y"] + 1.0},
    check=lambda source, followup: followup == source,
    evidence_for="Art. 10",
)

BASELINE = {"x": 1.0, "y": 1.0}


def _correct(x, y):
    return x * 2.0


def test_suite_passes_on_correct_sut():
    result = run_suite(_correct, [RISING, UNCHANGED], BASELINE)
    assert result.passed is True
    assert result.counts == (2, 2)


def test_suite_reports_which_relation_failed():
    def leaks_y(x, y):
        return x * 2.0 + y

    result = run_suite(leaks_y, [RISING, UNCHANGED], BASELINE)
    assert result.passed is False
    assert result.counts == (1, 2)
    failed = [r.relation.name for r in result.results if not r.passed]
    assert failed == ["Unveraendert"]


def test_suite_groups_results_by_article():
    result = run_suite(_correct, [RISING, UNCHANGED], BASELINE)
    grouped = result.by_article()
    assert set(grouped) == {"Art. 15", "Art. 10"}
    assert grouped["Art. 10"][0].relation.name == "Unveraendert"
