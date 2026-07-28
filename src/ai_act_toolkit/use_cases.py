"""Drei fest hinterlegte Beispiel-Use-Cases für die Demo.

Bewusst kein Freitext-Import (siehe Design-Spec, "Bewusst weggelassen") —
jeder Use Case hat vordefinierte, im Fragebogen der App editierbare
Annex-III-Attribute.
"""

from dataclasses import dataclass

from ai_act_toolkit.risk_engine import Annex3Area, UseCaseAttributes


@dataclass
class UseCase:
    key: str
    title: str
    description: str
    attributes: UseCaseAttributes
    has_metamorphic_demo: bool


COMFORT_SYSTEM = UseCase(
    key="comfort_system",
    title="Autonomes Fahrzeug-Komfortsystem",
    description=(
        "KI-System, das Kühlung/Heizung/Sitzeinstellung eines Fahrzeugs "
        "automatisch an Außentemperatur, Innentemperatur und Insassenzahl "
        "anpasst — angelehnt an eine Industriekooperation mit Mercedes-Benz "
        "zu autonomen Fahrzeug-Komfortsystemen (Marcos Promotion, KIT/ITIV)."
    ),
    attributes=UseCaseAttributes(
        is_prohibited_practice=False,
        is_safety_component_regulated_product=True,
        is_annex3_area=False,
        annex3_area=Annex3Area.NONE,
        significant_risk_to_health_safety_fundamental_rights=True,
        has_transparency_obligation=False,
    ),
    has_metamorphic_demo=True,
)

RECRUITING = UseCase(
    key="recruiting",
    title="KI-gestützte Bewerber-Vorauswahl",
    description=(
        "KI-System, das eingehende Bewerbungen automatisch bewertet und "
        "eine Rangliste für die Vorauswahl erstellt."
    ),
    attributes=UseCaseAttributes(
        is_prohibited_practice=False,
        is_safety_component_regulated_product=False,
        is_annex3_area=True,
        annex3_area=Annex3Area.EMPLOYMENT,
        significant_risk_to_health_safety_fundamental_rights=True,
        has_transparency_obligation=False,
    ),
    has_metamorphic_demo=False,
)

CHATBOT = UseCase(
    key="chatbot",
    title="Kundenservice-Chatbot",
    description=(
        "KI-Chatbot, der Standardanfragen im Kundenservice beantwortet und "
        "bei komplexeren Fällen an einen Menschen weiterleitet."
    ),
    attributes=UseCaseAttributes(
        is_prohibited_practice=False,
        is_safety_component_regulated_product=False,
        is_annex3_area=False,
        annex3_area=Annex3Area.NONE,
        significant_risk_to_health_safety_fundamental_rights=False,
        has_transparency_obligation=True,
    ),
    has_metamorphic_demo=False,
)

ALL_USE_CASES = [COMFORT_SYSTEM, RECRUITING, CHATBOT]
