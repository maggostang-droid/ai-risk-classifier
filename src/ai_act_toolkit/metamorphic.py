"""Generischer Runner für metamorphe Tests.

Eine metamorphe Relation prüft nicht eine einzelne Ausgabe gegen ein
festes Referenzergebnis (das "Orakel-Problem" bei KI-Systemen: die
"richtige" Ausgabe ist oft unbekannt), sondern eine Beziehung zwischen
der Ausgabe eines Quellfalls und der Ausgabe eines daraus abgeleiteten
Folgefalls — genau das Prinzip aus Marcos Promotion, hier auf einen
konkret ausführbaren Fall reduziert.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class MetamorphicRelation:
    name: str
    description: str
    transform: Callable[[dict], dict]
    check: Callable[[float, float], bool]


@dataclass
class MetamorphicResult:
    relation: MetamorphicRelation
    source_inputs: dict
    source_output: float
    followup_inputs: dict
    followup_output: float
    passed: bool


def run_relation(
    sut_fn: Callable[..., float],
    relation: MetamorphicRelation,
    source_inputs: dict,
) -> MetamorphicResult:
    source_output = sut_fn(**source_inputs)
    followup_inputs = relation.transform(source_inputs)
    followup_output = sut_fn(**followup_inputs)
    passed = relation.check(source_output, followup_output)
    return MetamorphicResult(
        relation=relation,
        source_inputs=source_inputs,
        source_output=source_output,
        followup_inputs=followup_inputs,
        followup_output=followup_output,
        passed=passed,
    )
