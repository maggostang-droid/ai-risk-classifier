"""Toy-'System unter Test': automatische Sitzverstellung.

Diese SUT prüft die Eigenschaft, die die Hochrisiko-Einstufung überhaupt
auslöst: die Sitzverstellung greift in die Rückhaltegeometrie ein und
macht das Komfortsystem damit zum Sicherheitsbauteil nach Art. 6(1). Die
zentrale Sicherheitsannahme lautet: je schneller das Fahrzeug fährt, desto
aufrechter muss der Sitz stehen, damit der Gurt korrekt greift.

Kein echtes ML-Modell, ein deterministisches Stellvertreter-Modell.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant

MAX_RECLINE_DEG = 45.0


def decide_seat_recline_angle(
    occupant_height_cm: float,
    occupant_weight_kg: float,
    vehicle_speed_kmh: float,
    occupant_count: int,
) -> float:
    """Berechnet den Ziel-Lehnenwinkel in Grad (0 = aufrecht, 45 = maximal geneigt).

    Das Insassengewicht ist bewusst kein Eingangsfaktor: der Lehnenwinkel
    darf nicht davon abhängen. Die Signatur nimmt es trotzdem entgegen,
    damit eine Relation genau diese Unabhängigkeit prüfen kann.
    """
    base = 30.0
    height_factor = (occupant_height_cm - 170.0) * 0.10
    speed_penalty = vehicle_speed_kmh * 0.15
    occupant_factor = occupant_count * 0.5
    angle = base + height_factor - speed_penalty + occupant_factor
    return max(0.0, min(MAX_RECLINE_DEG, angle))


SEAT_BASELINE = dict(
    occupant_height_cm=175.0,
    occupant_weight_kg=75.0,
    vehicle_speed_kmh=50.0,
    occupant_count=2,
)

SPEED_SAFETY_RELATION = MetamorphicRelation(
    name="Geschwindigkeits-Sicherheitsmonotonie",
    description=(
        "Steigt die Fahrgeschwindigkeit bei sonst gleichen Bedingungen, darf der "
        "Lehnenwinkel nicht größer werden — sonst verschlechtert sich die "
        "Rückhaltegeometrie genau dann, wenn sie am wichtigsten ist."
    ),
    transform=lambda inputs: {
        **inputs,
        "vehicle_speed_kmh": inputs["vehicle_speed_kmh"] + 20.0,
    },
    check=lambda source_output, followup_output: followup_output <= source_output,
    evidence_for="Art. 15",
)

HEIGHT_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Körpergrößen-Monotonie",
    description=(
        "Ein größerer Insasse muss echt mehr Lehnenwinkel bekommen — bleibt der "
        "Winkel gleich, ignoriert das System die Körpergröße."
    ),
    transform=lambda inputs: {
        **inputs,
        "occupant_height_cm": inputs["occupant_height_cm"] + 15.0,
    },
    check=lambda source_output, followup_output: followup_output > source_output,
    evidence_for="Art. 15",
)

WEIGHT_INDEPENDENCE_RELATION = MetamorphicRelation(
    name="Gewichtsunabhängigkeit",
    description=(
        "Das Insassengewicht darf den Lehnenwinkel nicht beeinflussen. Tut es das "
        "doch, ist ein sachfremdes Merkmal in die Entscheidung geraten."
    ),
    transform=lambda inputs: {
        **inputs,
        "occupant_weight_kg": inputs["occupant_weight_kg"] + 25.0,
    },
    check=lambda source_output, followup_output: followup_output == source_output,
    evidence_for="Art. 15",
)

SEAT_SATURATION_RELATION = MetamorphicRelation(
    name="Sättigungsgrenze",
    description=(
        "Auch bei extremen Eingaben muss der Lehnenwinkel im mechanisch "
        "zulässigen Bereich 0 bis 45 Grad bleiben."
    ),
    transform=lambda inputs: {
        **inputs,
        "occupant_height_cm": 400.0,
        "vehicle_speed_kmh": 0.0,
        "occupant_count": 9,
    },
    check=lambda source_output, followup_output: (
        0.0 <= followup_output <= MAX_RECLINE_DEG
    ),
    evidence_for="Art. 15",
)

SEAT_RELATIONS = (
    SPEED_SAFETY_RELATION,
    HEIGHT_MONOTONICITY_RELATION,
    WEIGHT_INDEPENDENCE_RELATION,
    SEAT_SATURATION_RELATION,
)


def _speed_sign_flip(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    base = 30.0
    height_factor = (occupant_height_cm - 170.0) * 0.10
    occupant_factor = occupant_count * 0.5
    # Fehler: höhere Geschwindigkeit neigt den Sitz weiter zurück.
    angle = base + height_factor + vehicle_speed_kmh * 0.15 + occupant_factor
    return max(0.0, min(MAX_RECLINE_DEG, angle))


def _height_ignored(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    base = 30.0
    occupant_factor = occupant_count * 0.5
    # Fehler: die Körpergröße geht gar nicht ein.
    angle = base - vehicle_speed_kmh * 0.15 + occupant_factor
    return max(0.0, min(MAX_RECLINE_DEG, angle))


def _weight_leaks(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    # Fehler: das Gewicht beeinflusst den Winkel, obwohl es das nicht darf.
    angle = (
        decide_seat_recline_angle(
            occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
        )
        + (occupant_weight_kg - 75.0) * 0.05
    )
    return max(0.0, min(MAX_RECLINE_DEG, angle))


def _clip_missing(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    base = 30.0
    height_factor = (occupant_height_cm - 170.0) * 0.10
    occupant_factor = occupant_count * 0.5
    # Fehler: der mechanische Endanschlag wird nicht abgebildet.
    return base + height_factor - vehicle_speed_kmh * 0.15 + occupant_factor


def _rounded(occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count):
    # Fehler: Winkel wird auf ganze Grad gerundet. Verletzt keine der vier
    # Relationen — bekannte Blindstelle der Suite.
    return float(
        round(
            decide_seat_recline_angle(
                occupant_height_cm,
                occupant_weight_kg,
                vehicle_speed_kmh,
                occupant_count,
            )
        )
    )


SEAT_MUTANTS = (
    Mutant(
        key="vorzeichen_geschwindigkeit",
        label="Vorzeichenfehler Geschwindigkeit",
        defect=(
            "Höhere Geschwindigkeit neigt den Sitz weiter zurück statt aufzurichten."
        ),
        fn=_speed_sign_flip,
    ),
    Mutant(
        key="hoehe_ignoriert",
        label="Körpergröße ignoriert",
        defect="Die Körpergröße geht nicht in den Lehnenwinkel ein.",
        fn=_height_ignored,
    ),
    Mutant(
        key="gewicht_leckt",
        label="Gewicht beeinflusst den Winkel",
        defect="Ein sachfremdes Merkmal ist in die Entscheidung geraten.",
        fn=_weight_leaks,
    ),
    Mutant(
        key="clip_fehlt",
        label="Endanschlag fehlt",
        defect="Der Winkel kann über 45 Grad hinauslaufen.",
        fn=_clip_missing,
    ),
    Mutant(
        key="rundung",
        label="Rundung auf ganze Grad",
        defect="Winkel wird gerundet — von keiner Relation erkannt.",
        fn=_rounded,
        expected_survivor=True,
    ),
)
