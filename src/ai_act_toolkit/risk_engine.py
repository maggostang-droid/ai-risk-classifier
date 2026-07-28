"""Deterministischer Regelbaum zur EU-AI-Act-Risikoklassifizierung.

Bewusst vereinfachte, aber an der echten Artikel-Struktur orientierte
Nachbildung von Art. 5 (verbotene Praktiken), Art. 6(1) (Sicherheitsbauteile
regulierter Produkte), Art. 6(2)+Annex III (Hochrisiko-Bereiche, mit der
Art.-6(3)-Ausnahme bei fehlendem signifikantem Risiko) und Art. 50
(Transparenzpflichten). Kein Ersatz für eine juristische Prüfung — siehe
README, Abschnitt "Limitierungen".
"""

from dataclasses import dataclass
from enum import Enum


class RiskClass(str, Enum):
    UNACCEPTABLE = "unacceptable"
    HIGH_RISK = "high_risk"
    LIMITED_RISK = "limited_risk"
    MINIMAL_RISK = "minimal_risk"


class Annex3Area(str, Enum):
    NONE = "none"
    BIOMETRIC_IDENTIFICATION = "biometric_identification"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION_ASYLUM_BORDER = "migration_asylum_border"
    JUSTICE_DEMOCRATIC_PROCESSES = "justice_democratic_processes"


@dataclass
class UseCaseAttributes:
    is_prohibited_practice: bool
    is_safety_component_regulated_product: bool
    is_annex3_area: bool
    annex3_area: Annex3Area
    significant_risk_to_health_safety_fundamental_rights: bool
    has_transparency_obligation: bool


@dataclass
class ClassificationResult:
    risk_class: RiskClass
    matched_rule: str


def classify(attrs: UseCaseAttributes) -> ClassificationResult:
    if attrs.is_prohibited_practice:
        return ClassificationResult(
            RiskClass.UNACCEPTABLE, "Art. 5: verbotene Praktik"
        )

    if attrs.is_safety_component_regulated_product:
        return ClassificationResult(
            RiskClass.HIGH_RISK,
            "Art. 6(1): Sicherheitsbauteil eines regulierten Produkts (Annex I)",
        )

    if attrs.is_annex3_area and attrs.significant_risk_to_health_safety_fundamental_rights:
        return ClassificationResult(
            RiskClass.HIGH_RISK,
            f"Art. 6(2) + Annex III ({attrs.annex3_area.value}): signifikantes Risiko",
        )

    if attrs.has_transparency_obligation:
        return ClassificationResult(
            RiskClass.LIMITED_RISK, "Art. 50: Transparenzpflicht"
        )

    return ClassificationResult(
        RiskClass.MINIMAL_RISK, "keine der obigen Kategorien trifft zu"
    )
