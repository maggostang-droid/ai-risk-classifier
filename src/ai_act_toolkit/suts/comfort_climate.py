"""Toy-'System unter Test': simulierte Klimasteuerung des Komfortsystems.

Kein echtes ML-Modell, ein bewusst einfaches, deterministisches Stellvertreter-
Modell, an dem die metamorphe Testmethodik konkret demonstriert wird.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant


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

CLIMATE_BASELINE = dict(
    outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
)

CABIN_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Kabinen-Monotonie",
    description=(
        "Steigt die Innentemperatur bei sonst gleichen Bedingungen, muss die "
        "Ziel-Kühlintensität echt steigen — bleibt sie gleich, ignoriert das "
        "System die Kabinentemperatur."
    ),
    transform=lambda inputs: {**inputs, "cabin_temp_c": inputs["cabin_temp_c"] + 5.0},
    check=lambda source_output, followup_output: followup_output > source_output,
    evidence_for="Art. 15",
)

CLIMATE_SATURATION_RELATION = MetamorphicRelation(
    name="Sättigungsgrenze",
    description=(
        "Auch bei extremen Eingaben muss die Kühlintensität im gültigen "
        "Wertebereich 0 bis 100 bleiben."
    ),
    transform=lambda inputs: {
        **inputs,
        "outside_temp_c": 90.0,
        "cabin_temp_c": 90.0,
        "occupant_count": 9,
    },
    check=lambda source_output, followup_output: 0.0 <= followup_output <= 100.0,
    evidence_for="Art. 15",
)

CLIMATE_RELATIONS = (
    TEMPERATURE_MONOTONICITY_RELATION,
    CABIN_MONOTONICITY_RELATION,
    CLIMATE_SATURATION_RELATION,
)


def _sign_flip(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    cabin_factor = max(0.0, cabin_temp_c - desired_temp_c) * 3.0
    occupant_factor = occupant_count * 1.5
    # Fehler: die Außentemperatur geht abkühlend statt aufheizend ein.
    intensity = base - outside_factor + cabin_factor + occupant_factor
    return max(0.0, min(100.0, intensity))


def _cabin_ignored(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    occupant_factor = occupant_count * 1.5
    # Fehler: die Kabinentemperatur wird gar nicht berücksichtigt.
    intensity = base + outside_factor + occupant_factor
    return max(0.0, min(100.0, intensity))


def _clip_missing(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    cabin_factor = max(0.0, cabin_temp_c - desired_temp_c) * 3.0
    occupant_factor = occupant_count * 1.5
    # Fehler: der Wertebereich wird nicht begrenzt.
    return base + outside_factor + cabin_factor + occupant_factor


def _rounded(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    # Fehler: Ergebnis wird auf ganze Prozentpunkte gerundet. Verletzt keine
    # der Relationen — bekannte Blindstelle der Suite.
    return float(
        round(
            decide_cooling_intensity(
                outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count
            )
        )
    )


CLIMATE_MUTANTS = (
    Mutant(
        key="vorzeichen_aussen",
        label="Vorzeichenfehler Außentemperatur",
        defect="Höhere Außentemperatur senkt die Kühlintensität statt sie zu erhöhen.",
        fn=_sign_flip,
    ),
    Mutant(
        key="kabine_ignoriert",
        label="Kabinentemperatur ignoriert",
        defect="Die Innentemperatur geht gar nicht in die Berechnung ein.",
        fn=_cabin_ignored,
    ),
    Mutant(
        key="clip_fehlt",
        label="Wertebereich nicht begrenzt",
        defect="Das Ergebnis kann über 100 hinauslaufen.",
        fn=_clip_missing,
    ),
    Mutant(
        key="rundung",
        label="Rundung auf ganze Prozentpunkte",
        defect="Ergebnis wird gerundet — von keiner Relation erkannt.",
        fn=_rounded,
        expected_survivor=True,
    ),
)
