"""Systeme unter Test, gegen die die metamorphen Relationen laufen.

Die Registry ordnet jedem Use Case seine SUTs zu. Sie ersetzt das frühere
Flag `UseCase.has_metamorphic_demo`: ob ein Nachweis möglich ist, ergibt
sich jetzt daraus, ob überhaupt eine SUT hinterlegt ist. `use_cases.py`
kennt die SUTs dadurch nicht mehr und bleibt reine Falldaten.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant
from ai_act_toolkit.suts.comfort_climate import (
    CLIMATE_BASELINE,
    CLIMATE_MUTANTS,
    CLIMATE_RELATIONS,
    decide_cooling_intensity,
)
from ai_act_toolkit.suts.comfort_seat import (
    SEAT_BASELINE,
    SEAT_MUTANTS,
    SEAT_RELATIONS,
    decide_seat_recline_angle,
)
from ai_act_toolkit.suts.recruiting_scorer import (
    RECRUITING_BASELINE,
    RECRUITING_MUTANTS,
    RECRUITING_RELATIONS,
    score_applicant_fixed,
)


@dataclass(frozen=True)
class SUTSpec:
    key: str
    label: str
    description: str
    fn: Callable[..., float]
    baseline_inputs: dict
    relations: tuple[MetamorphicRelation, ...]
    mutants: tuple[Mutant, ...]


SEAT_SUT = SUTSpec(
    key="seat",
    label="Automatische Sitzverstellung",
    description=(
        "Die Funktion, die die Hochrisiko-Einstufung nach Art. 6(1) überhaupt "
        "auslöst: sie greift in die Rückhaltegeometrie ein."
    ),
    fn=decide_seat_recline_angle,
    baseline_inputs=SEAT_BASELINE,
    relations=SEAT_RELATIONS,
    mutants=SEAT_MUTANTS,
)

CLIMATE_SUT = SUTSpec(
    key="climate",
    label="Klimasteuerung",
    description="Die Komfortfunktion des Systems, ohne Sicherheitsrelevanz.",
    fn=decide_cooling_intensity,
    baseline_inputs=CLIMATE_BASELINE,
    relations=CLIMATE_RELATIONS,
    mutants=CLIMATE_MUTANTS,
)

SCORING_SUT = SUTSpec(
    key="scoring",
    label="Vorauswahl-Scoring",
    description=(
        "Bewertet Bewerbungen mit 0 bis 100 Punkten. Die Namensinvarianz-Relation "
        "prüft, ob ein sachfremdes Merkmal in die Entscheidung eingeht."
    ),
    fn=score_applicant_fixed,
    baseline_inputs=RECRUITING_BASELINE,
    relations=RECRUITING_RELATIONS,
    mutants=RECRUITING_MUTANTS,
)

SUT_REGISTRY: dict[str, tuple[SUTSpec, ...]] = {
    "comfort_system": (SEAT_SUT, CLIMATE_SUT),
    "recruiting": (SCORING_SUT,),
    "chatbot": (),
}


def suts_for(use_case_key: str) -> tuple[SUTSpec, ...]:
    """Liefert die SUTs eines Use Case, oder ein leeres Tupel."""
    return SUT_REGISTRY.get(use_case_key, ())
