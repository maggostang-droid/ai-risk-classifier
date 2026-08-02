from ai_act_toolkit.metamorphic.core import MetamorphicRelation, run_relation


def test_relation_declares_which_article_it_supports():
    relation = MetamorphicRelation(
        name="Dummy",
        description="Verdoppelt die Eingabe.",
        transform=lambda inputs: {**inputs, "x": inputs["x"] * 2},
        check=lambda source, followup: followup >= source,
        evidence_for="Art. 15",
    )
    assert relation.evidence_for == "Art. 15"


def test_run_relation_reports_violation():
    relation = MetamorphicRelation(
        name="Monotonie",
        description="Groesseres x darf das Ergebnis nicht senken.",
        transform=lambda inputs: {**inputs, "x": inputs["x"] + 1.0},
        check=lambda source, followup: followup >= source,
        evidence_for="Art. 15",
    )
    result = run_relation(lambda x: -x, relation, {"x": 1.0})
    assert result.passed is False
