from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant, run_kill_matrix

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

SIGN_FLIP = Mutant(
    key="vorzeichen",
    label="Vorzeichenfehler",
    defect="x geht negativ statt positiv ein.",
    fn=lambda x, y: -x * 2.0,
)

Y_LEAKS = Mutant(
    key="y_leckt",
    label="y leckt ein",
    defect="y beeinflusst das Ergebnis, obwohl es das nicht darf.",
    fn=lambda x, y: x * 2.0 + y,
)

ROUNDING = Mutant(
    key="rundung",
    label="Rundungsfehler",
    defect="Ergebnis wird auf ganze Zahlen gerundet.",
    fn=lambda x, y: float(round(x * 2.0)),
    expected_survivor=True,
)

CRASHES = Mutant(
    key="absturz",
    label="Absturz",
    defect="Wirft bei jedem Aufruf eine Exception.",
    fn=lambda x, y: 1 / 0,
)


def test_each_mutant_is_killed_by_the_matching_relation():
    matrix = run_kill_matrix([RISING, UNCHANGED], [SIGN_FLIP, Y_LEAKS], BASELINE)
    assert matrix.killed_by(SIGN_FLIP) == ["Steigend"]
    assert matrix.killed_by(Y_LEAKS) == ["Unveraendert"]


def test_declared_survivor_is_caught_by_no_relation():
    matrix = run_kill_matrix([RISING, UNCHANGED], [ROUNDING], BASELINE)
    assert matrix.is_killed(ROUNDING) is False
    assert [m.key for m in matrix.survivors()] == ["rundung"]


def test_score_counts_mutants_not_cells():
    matrix = run_kill_matrix(
        [RISING, UNCHANGED], [SIGN_FLIP, Y_LEAKS, ROUNDING], BASELINE
    )
    assert matrix.score == (2, 3)


def test_crashing_mutant_counts_as_killed():
    matrix = run_kill_matrix([RISING], [CRASHES], BASELINE)
    assert matrix.is_killed(CRASHES) is True
