import pytest

from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts.comfort_seat import (
    SEAT_BASELINE,
    SEAT_MUTANTS,
    SEAT_RELATIONS,
    decide_seat_recline_angle,
)


def test_angle_stays_within_physical_limits():
    angle = decide_seat_recline_angle(
        occupant_height_cm=400.0,
        occupant_weight_kg=200.0,
        vehicle_speed_kmh=0.0,
        occupant_count=9,
    )
    assert 0.0 <= angle <= 45.0


def test_higher_speed_never_increases_recline():
    slow = decide_seat_recline_angle(**SEAT_BASELINE)
    fast = decide_seat_recline_angle(**{**SEAT_BASELINE, "vehicle_speed_kmh": 200.0})
    assert fast <= slow


def test_correct_sut_passes_every_relation():
    result = run_suite(decide_seat_recline_angle, SEAT_RELATIONS, SEAT_BASELINE)
    assert result.passed is True, [
        r.relation.name for r in result.results if not r.passed
    ]


@pytest.mark.parametrize(
    "mutant", [m for m in SEAT_MUTANTS if not m.expected_survivor], ids=lambda m: m.key
)
def test_every_declared_defect_is_killed(mutant):
    matrix = run_kill_matrix(SEAT_RELATIONS, [mutant], SEAT_BASELINE)
    assert matrix.is_killed(mutant) is True


@pytest.mark.parametrize(
    "mutant", [m for m in SEAT_MUTANTS if m.expected_survivor], ids=lambda m: m.key
)
def test_declared_survivors_really_survive(mutant):
    matrix = run_kill_matrix(SEAT_RELATIONS, [mutant], SEAT_BASELINE)
    assert matrix.is_killed(mutant) is False
