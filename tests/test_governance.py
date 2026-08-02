from ai_act_toolkit.governance import generate_governance_artifact
from ai_act_toolkit.metamorphic import run_relation
from ai_act_toolkit.suts.comfort_climate import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
from ai_act_toolkit.risk_engine import ClassificationResult, RiskClass
from ai_act_toolkit.use_cases import COMFORT_SYSTEM


def test_artifact_contains_required_sections_for_high_risk_case():
    classification = ClassificationResult(
        RiskClass.HIGH_RISK,
        "Art. 6(1): Sicherheitsbauteil eines regulierten Produkts (Annex I)",
    )
    metamorphic_result = run_relation(
        decide_cooling_intensity,
        TEMPERATURE_MONOTONICITY_RELATION,
        dict(outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2),
    )

    artifact = generate_governance_artifact(
        COMFORT_SYSTEM, classification, "Testbegründung.", metamorphic_result
    )

    assert "# Risk Assessment" in artifact
    assert "## Systembeschreibung" in artifact
    assert "## Klassifizierung" in artifact
    assert "## Begründung" in artifact
    assert "## Metamorpher Test" in artifact
    assert "## Konformitätscheckliste" in artifact
    assert "Art. 9" in artifact
    assert "Art. 15" in artifact
    assert "keine juristische" in artifact.lower() or "keine rechtliche" in artifact.lower()


def test_artifact_omits_metamorphic_section_when_absent():
    classification = ClassificationResult(
        RiskClass.HIGH_RISK,
        "Art. 6(2) + Annex III (employment): signifikantes Risiko",
    )
    artifact = generate_governance_artifact(
        COMFORT_SYSTEM, classification, "Testbegründung.", None
    )
    assert "## Metamorpher Test" not in artifact
