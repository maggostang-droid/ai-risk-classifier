"""Toy-'System unter Test': simulierte Klimasteuerung des Komfortsystems.

Kein echtes ML-Modell, ein bewusst einfaches, deterministisches Stellvertreter-
Modell, an dem die metamorphe Testmethodik konkret demonstriert wird.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation


def decide_cooling_intensity(
    outside_temp_c: float,
    cabin_temp_c: float,
    desired_temp_c: float,
    occupant_count: int,
) -> float:
    """Berechnet die Ziel-Kühlintensität (0-100) des Komfortsystems."""
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    cabin_factor = max(0.0, cabin_temp_c - desired_temp_c) * 3.0
    occupant_factor = occupant_count * 1.5
    intensity = base + outside_factor + cabin_factor + occupant_factor
    return max(0.0, min(100.0, intensity))


TEMPERATURE_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Temperatur-Monotonie",
    description=(
        "Steigt die Außentemperatur bei sonst gleichen Bedingungen, darf die "
        "Ziel-Kühlintensität nicht sinken (Monotonie-Annahme)."
    ),
    transform=lambda inputs: {**inputs, "outside_temp_c": inputs["outside_temp_c"] + 5.0},
    check=lambda source_output, followup_output: followup_output >= source_output,
    evidence_for="Art. 15",
)
