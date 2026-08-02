import pytest

from ai_act_toolkit.metamorphic.core import run_relation
from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts.recruiting_scorer import (
    NAME_INVARIANCE_RELATION,
    RECRUITING_BASELINE,
    RECRUITING_MUTANTS,
    RECRUITING_RELATIONS,
    score_applicant_fixed,
    score_applicant_naive,
)


def test_naive_scorer_violates_name_invariance():
    result = run_relation(
        score_applicant_naive, NAME_INVARIANCE_RELATION, RECRUITING_BASELINE
    )
    assert result.passed is False
    assert result.followup_output < result.source_output


def test_fixed_scorer_holds_name_invariance():
    result = run_relation(
        score_applicant_fixed, NAME_INVARIANCE_RELATION, RECRUITING_BASELINE
    )
    assert result.passed is True
    assert result.followup_output == result.source_output


def test_name_invariance_supports_article_10():
    assert NAME_INVARIANCE_RELATION.evidence_for == "Art. 10"


def test_correct_sut_passes_every_relation():
    result = run_suite(score_applicant_fixed, RECRUITING_RELATIONS, RECRUITING_BASELINE)
    assert result.passed is True, [
        r.relation.name for r in result.results if not r.passed
    ]


@pytest.mark.parametrize(
    "mutant",
    [m for m in RECRUITING_MUTANTS if not m.expected_survivor],
    ids=lambda m: m.key,
)
def test_every_declared_defect_is_killed(mutant):
    matrix = run_kill_matrix(RECRUITING_RELATIONS, [mutant], RECRUITING_BASELINE)
    assert matrix.is_killed(mutant) is True


@pytest.mark.parametrize(
    "mutant",
    [m for m in RECRUITING_MUTANTS if m.expected_survivor],
    ids=lambda m: m.key,
)
def test_declared_survivors_really_survive(mutant):
    matrix = run_kill_matrix(RECRUITING_RELATIONS, [mutant], RECRUITING_BASELINE)
    assert matrix.is_killed(mutant) is False
