import pytest

from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts.comfort_climate import (
    CLIMATE_BASELINE,
    CLIMATE_MUTANTS,
    CLIMATE_RELATIONS,
    decide_cooling_intensity,
)


def test_correct_sut_passes_every_relation():
    result = run_suite(decide_cooling_intensity, CLIMATE_RELATIONS, CLIMATE_BASELINE)
    assert result.passed is True, [
        r.relation.name for r in result.results if not r.passed
    ]


@pytest.mark.parametrize(
    "mutant",
    [m for m in CLIMATE_MUTANTS if not m.expected_survivor],
    ids=lambda m: m.key,
)
def test_every_declared_defect_is_killed(mutant):
    matrix = run_kill_matrix(CLIMATE_RELATIONS, [mutant], CLIMATE_BASELINE)
    assert matrix.is_killed(mutant) is True


@pytest.mark.parametrize(
    "mutant", [m for m in CLIMATE_MUTANTS if m.expected_survivor], ids=lambda m: m.key
)
def test_declared_survivors_really_survive(mutant):
    # Sperrt die dokumentierte Blindstelle: wer eine Relation nachruestet, die
    # diesen Mutanten faengt, muss auch README und Blindstellen-Abschnitt aendern.
    matrix = run_kill_matrix(CLIMATE_RELATIONS, [mutant], CLIMATE_BASELINE)
    assert matrix.is_killed(mutant) is False
