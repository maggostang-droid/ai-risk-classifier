"""Generischer Runner für metamorphe Tests.

Eine metamorphe Relation prüft nicht eine einzelne Ausgabe gegen ein
festes Referenzergebnis (das "Orakel-Problem" bei KI-Systemen: die
"richtige" Ausgabe ist oft unbekannt), sondern eine Beziehung zwischen
der Ausgabe eines Quellfalls und der Ausgabe eines daraus abgeleiteten
Folgefalls, genau das Prinzip aus Marcos Promotion, hier auf konkret
ausführbare Fälle reduziert.
"""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class MetamorphicRelation:
    """Eine prüfbare Beziehung zwischen Quell- und Folgefall.

    `evidence_for` benennt den AI-Act-Artikel, auf den ein bestandener
    Lauf dieser Relation als Nachweis einzahlt (z.B. "Art. 15" für
    Robustheit, "Art. 10" für die Untersuchung auf Verzerrungen). Über
    dieses Feld findet `governance.py` später die passende Pflichtzeile.
    """

    name: str
    description: str
    transform: Callable[[dict], dict]
    check: Callable[[float, float], bool]
    evidence_for: str


@dataclass(frozen=True)
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
    followup_inputs = relation.transform(dict(source_inputs))
    followup_output = sut_fn(**followup_inputs)
    passed = relation.check(source_output, followup_output)
    return MetamorphicResult(
        relation=relation,
        source_inputs=dict(source_inputs),
        source_output=source_output,
        followup_inputs=followup_inputs,
        followup_output=followup_output,
        passed=passed,
    )
