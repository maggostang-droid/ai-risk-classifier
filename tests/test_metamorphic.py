from ai_act_toolkit.comfort_system_sut import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
from ai_act_toolkit.metamorphic import run_relation


def test_monotonic_sut_passes_relation():
    source_inputs = dict(
        outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
    )
    result = run_relation(
        decide_cooling_intensity, TEMPERATURE_MONOTONICITY_RELATION, source_inputs
    )
    assert result.passed is True
    assert result.followup_output >= result.source_output
    assert result.followup_inputs["outside_temp_c"] == 25.0


def test_broken_sut_fails_relation():
    def broken_sut(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
        # bewusst falsch: Kühlintensität sinkt mit steigender Außentemperatur —
        # testet, dass run_relation eine echte Verletzung erkennt.
        return max(0.0, 50.0 - outside_temp_c)

    source_inputs = dict(
        outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
    )
    result = run_relation(broken_sut, TEMPERATURE_MONOTONICITY_RELATION, source_inputs)
    assert result.passed is False


def test_decide_cooling_intensity_is_bounded():
    intensity = decide_cooling_intensity(
        outside_temp_c=50.0, cabin_temp_c=50.0, desired_temp_c=21.0, occupant_count=8
    )
    assert 0.0 <= intensity <= 100.0
