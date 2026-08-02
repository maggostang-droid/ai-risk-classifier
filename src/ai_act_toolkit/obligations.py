"""Ableitung der konkreten AI-Act-Pflichten aus einer Risikoklasse.

Das ist das Bindeglied zwischen Einstufung und Nachweis: erst hier
entsteht die Liste von Artikelpflichten, für die anschließend Evidenz
gesucht wird. `EvidenceKind` sagt dabei ehrlich, welche Pflicht dieses
Werkzeug überhaupt belegen kann und welche eine reine Prozesspflicht ist.
"""

from dataclasses import dataclass
from enum import Enum

from ai_act_toolkit.risk_engine import ClassificationResult, RiskClass


class EvidenceKind(str, Enum):
    """Wie eine Pflicht belegt werden kann."""

    TECHNICAL_TEST = "technical_test"  # durch eine metamorphe Relation belegbar
    DOCUMENTATION = "documentation"  # teilweise: das Artefakt selbst zahlt darauf ein
    PROCESS = "process"  # organisatorisch, durch dieses Werkzeug nicht belegbar


@dataclass(frozen=True)
class Obligation:
    article: str
    title: str
    description: str
    evidence_kind: EvidenceKind


HIGH_RISK_OBLIGATIONS: tuple[Obligation, ...] = (
    Obligation(
        "Art. 9",
        "Risikomanagementsystem",
        "Kontinuierlicher Prozess zur Identifikation und Minderung von Risiken über "
        "den Lebenszyklus. Art. 9(7) verlangt Testen gegen vorab definierte Metriken "
        "und Schwellen vor dem Inverkehrbringen.",
        EvidenceKind.DOCUMENTATION,
    ),
    Obligation(
        "Art. 10",
        "Daten und Data Governance",
        "Trainings-, Validierungs- und Testdaten müssen repräsentativ und geeignet "
        "sein. Art. 10(2)(f)(g) verlangt ausdrücklich die Untersuchung auf mögliche "
        "Verzerrungen.",
        EvidenceKind.TECHNICAL_TEST,
    ),
    Obligation(
        "Art. 11",
        "Technische Dokumentation",
        "Nachweisbare Dokumentation zu Design, Entwicklung und Leistung. Annex IV "
        "Nr. 2(g) verlangt die verwendeten Validierungs- und Testverfahren samt "
        "Metriken.",
        EvidenceKind.DOCUMENTATION,
    ),
    Obligation(
        "Art. 12",
        "Aufzeichnungspflichten (Logging)",
        "Automatische Protokollierung von Ereignissen während des Betriebs.",
        EvidenceKind.PROCESS,
    ),
    Obligation(
        "Art. 13",
        "Transparenz und Informationsbereitstellung",
        "Verständliche Betriebsanleitung für den Betreiber.",
        EvidenceKind.PROCESS,
    ),
    Obligation(
        "Art. 14",
        "Menschliche Aufsicht",
        "Wirksame Aufsichtsmaßnahmen zur Verhinderung oder Minimierung von Risiken.",
        EvidenceKind.PROCESS,
    ),
    Obligation(
        "Art. 15",
        "Genauigkeit, Robustheit, Cybersicherheit",
        "Angemessenes Leistungs- und Robustheitsniveau über den gesamten "
        "Lebenszyklus.",
        EvidenceKind.TECHNICAL_TEST,
    ),
)

LIMITED_RISK_OBLIGATIONS: tuple[Obligation, ...] = (
    Obligation(
        "Art. 50",
        "Transparenzpflicht",
        "Nutzer müssen erkennen können, dass sie mit einem KI-System interagieren.",
        EvidenceKind.PROCESS,
    ),
)

PROHIBITED_OBLIGATIONS: tuple[Obligation, ...] = (
    Obligation(
        "Art. 5",
        "Verbotene Praktik",
        "Das System darf nicht in Verkehr gebracht oder betrieben werden. Eine "
        "Konformitätsbewertung ist nicht vorgesehen.",
        EvidenceKind.PROCESS,
    ),
)

_BY_RISK_CLASS: dict[RiskClass, tuple[Obligation, ...]] = {
    RiskClass.UNACCEPTABLE: PROHIBITED_OBLIGATIONS,
    RiskClass.HIGH_RISK: HIGH_RISK_OBLIGATIONS,
    RiskClass.LIMITED_RISK: LIMITED_RISK_OBLIGATIONS,
    RiskClass.MINIMAL_RISK: (),
}


def obligations_for(classification: ClassificationResult) -> list[Obligation]:
    """Liefert die Pflichten, die aus der Einstufung folgen."""
    return list(_BY_RISK_CLASS[classification.risk_class])
