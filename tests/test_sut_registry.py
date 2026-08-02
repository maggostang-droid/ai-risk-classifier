import pytest

from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts import SUT_REGISTRY, suts_for
from ai_act_toolkit.use_cases import ALL_USE_CASES

ALL_SUTS = [spec for specs in SUT_REGISTRY.values() for spec in specs]


def test_every_use_case_has_a_registry_entry():
    assert set(SUT_REGISTRY) == {uc.key for uc in ALL_USE_CASES}


def test_comfort_system_has_seat_and_climate():
    assert [s.key for s in suts_for("comfort_system")] == ["seat", "climate"]


def test_recruiting_has_the_scoring_sut():
    assert [s.key for s in suts_for("recruiting")] == ["scoring"]


def test_chatbot_has_no_sut():
    assert suts_for("chatbot") == ()


def test_unknown_use_case_yields_no_sut():
    assert suts_for("gibt-es-nicht") == ()


@pytest.mark.parametrize("spec", ALL_SUTS, ids=lambda s: s.key)
def test_every_registered_sut_passes_its_own_suite(spec):
    # Eine Relation, die auf korrektem Code feuert, ist selbst kaputt.
    result = run_suite(spec.fn, spec.relations, spec.baseline_inputs)
    assert result.passed is True, [
        r.relation.name for r in result.results if not r.passed
    ]


@pytest.mark.parametrize("spec", ALL_SUTS, ids=lambda s: s.key)
def test_every_registered_sut_declares_at_least_one_mutant(spec):
    assert len(spec.mutants) >= 1
