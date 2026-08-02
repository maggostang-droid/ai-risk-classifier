"""Generiert das Governance-Artefakt (Risk Assessment + Konformitätscheckliste)
als Markdown für Hochrisiko-Use-Cases.
"""

from ai_act_toolkit.metamorphic import MetamorphicResult
from ai_act_toolkit.risk_engine import ClassificationResult
from ai_act_toolkit.use_cases import UseCase

OBLIGATIONS = [
    (
        "Art. 9, Risikomanagementsystem",
        "Kontinuierlicher Prozess zur Identifikation/Minderung von Risiken über den Lebenszyklus.",
    ),
    (
        "Art. 10, Daten- und Datenqualitätsmanagement",
        "Trainings-/Validierungs-/Testdaten müssen repräsentativ, fehlerfrei und vollständig sein.",
    ),
    (
        "Art. 11, Technische Dokumentation",
        "Nachweisbare Dokumentation zu Design, Entwicklung und Leistung.",
    ),
    (
        "Art. 12, Aufzeichnungspflichten (Logging)",
        "Automatische Protokollierung während des Betriebs.",
    ),
    (
        "Art. 13, Transparenz und Informationsbereitstellung",
        "Verständliche Betriebsanleitung für Betreiber.",
    ),
    (
        "Art. 14, Menschliche Aufsicht",
        "Wirksame Aufsichtsmaßnahmen zur Verhinderung/Minimierung von Risiken.",
    ),
    (
        "Art. 15, Genauigkeit, Robustheit, Cybersicherheit",
        "Angemessenes Leistungsniveau über den gesamten Lebenszyklus.",
    ),
]


def generate_governance_artifact(
    use_case: UseCase,
    classification: ClassificationResult,
    rationale: str,
    metamorphic_result: MetamorphicResult | None,
) -> str:
    """Generiert ein Markdown Risk Assessment und Konformitätscheckliste für Hochrisiko-Use-Cases.

    Args:
        use_case: Beschreibung des AI-Systems
        classification: Risikoklassifizierung und Regel
        rationale: Begründung der Klassifizierung
        metamorphic_result: Optional Ergebnis des metamorphen Tests

    Returns:
        Markdown-formatiertes Governance-Artefakt als String
    """
    lines = [
        f"# Risk Assessment & Konformitätscheckliste, {use_case.title}",
        "",
        "## Systembeschreibung",
        use_case.description,
        "",
        "## Klassifizierung",
        f"**Risikoklasse:** {classification.risk_class.value}",
        f"**Regel:** {classification.matched_rule}",
        "",
        "## Begründung",
        rationale,
        "",
    ]

    if metamorphic_result is not None:
        status = "BESTANDEN" if metamorphic_result.passed else "FEHLGESCHLAGEN"
        lines += [
            "## Metamorpher Test",
            f"**Relation:** {metamorphic_result.relation.name}, {metamorphic_result.relation.description}",
            f"**Ergebnis:** {status}",
            f"- Quellfall: {metamorphic_result.source_inputs} -> {metamorphic_result.source_output:.1f}",
            f"- Folgefall: {metamorphic_result.followup_inputs} -> {metamorphic_result.followup_output:.1f}",
            "",
        ]

    lines.append("## Konformitätscheckliste (EU AI Act, high-risk)")
    for title, desc in OBLIGATIONS:
        lines.append(f"- [ ] **{title}**, {desc}")
    lines += [
        "",
        (
            "*Hinweis: Dieses Dokument ist eine methodische Demonstration und "
            "ersetzt keine juristische Prüfung oder ein echtes "
            "Konformitätsbewertungsverfahren.*"
        ),
    ]

    return "\n".join(lines)
