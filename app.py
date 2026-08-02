"""Streamlit-UI für den AI Risk Classifier (Portfolio-Demo, MARCO.OS-Stil)."""

import streamlit as st

from portfolio_ui import (
    example_picker,
    page_header,
    page_setup,
    portfolio_footer,
    under_the_hood,
)

from ai_act_toolkit.comfort_system_sut import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
from ai_act_toolkit.governance import generate_governance_artifact
from ai_act_toolkit.llm import get_llm
from ai_act_toolkit.metamorphic import run_relation
from ai_act_toolkit.rationale import generate_rationale
from ai_act_toolkit.risk_engine import Annex3Area, RiskClass, UseCaseAttributes, classify
from ai_act_toolkit.use_cases import ALL_USE_CASES

RISK_DISPLAY = {
    RiskClass.UNACCEPTABLE: ("🔴 Unzulässig (verbotene Praktik)", st.error),
    RiskClass.HIGH_RISK: ("🟠 Hochrisiko", st.warning),
    RiskClass.LIMITED_RISK: ("🔵 Begrenztes Risiko", st.info),
    RiskClass.MINIMAL_RISK: ("🟢 Minimales Risiko", st.success),
}

page_setup("AI Risk Classifier")

page_header(
    title="AI Risk Classifier",
    claim=(
        "Ordnet eine KI-Anwendung einer EU-AI-Act-Risikoklasse zu und belegt die Methodik "
        "mit einem live ausgeführten metamorphen Test: die Einstufung trifft ein "
        "deterministischer Regelbaum, nicht das LLM."
    ),
    project_id="ai-act-validation-toolkit",
    cluster="agentic-ai",
)

use_case_titles = [uc.title for uc in ALL_USE_CASES]
if "selected_use_case" not in st.session_state:
    st.session_state.selected_use_case = use_case_titles[0]

EXAMPLES = {
    "Fahrzeug-Komfortsystem": "Hochrisiko, mit ausführbarem Test",
    "Bewerber-Vorauswahl": "Hochrisiko über Annex III",
    "Kundenservice-Chatbot": "nur Transparenzpflicht",
}
_EXAMPLE_TO_USE_CASE = dict(zip(EXAMPLES, use_case_titles))

picked = example_picker(
    "Beispiel wählen, ganz ohne Eingabe:", EXAMPLES, key="usecase"
)
if picked:
    st.session_state.selected_use_case = _EXAMPLE_TO_USE_CASE[picked]

selected_title = st.selectbox(
    "Use Case",
    use_case_titles,
    index=use_case_titles.index(st.session_state.selected_use_case),
)
st.session_state.selected_use_case = selected_title
use_case = next(uc for uc in ALL_USE_CASES if uc.title == selected_title)

st.markdown(f"> {use_case.description}")

st.subheader("Fragebogen (editierbar)")
col1, col2 = st.columns(2)
with col1:
    is_prohibited = st.checkbox(
        "Verbotene Praktik nach Art. 5?", value=use_case.attributes.is_prohibited_practice
    )
    is_safety_component = st.checkbox(
        "Sicherheitsbauteil eines regulierten Produkts (Art. 6(1))?",
        value=use_case.attributes.is_safety_component_regulated_product,
    )
    is_annex3 = st.checkbox(
        "Fällt in einen Annex-III-Bereich?", value=use_case.attributes.is_annex3_area
    )
with col2:
    annex3_options = list(Annex3Area)
    annex3_area = st.selectbox(
        "Annex-III-Bereich",
        options=annex3_options,
        format_func=lambda a: a.value,
        index=annex3_options.index(use_case.attributes.annex3_area),
        disabled=not is_annex3,
    )
    significant_risk = st.checkbox(
        "Signifikantes Risiko für Gesundheit/Sicherheit/Grundrechte (Art. 6(3))?",
        value=use_case.attributes.significant_risk_to_health_safety_fundamental_rights,
    )
    has_transparency = st.checkbox(
        "Transparenzpflicht nach Art. 50 (z.B. Chatbot, Deepfake)?",
        value=use_case.attributes.has_transparency_obligation,
    )

attrs = UseCaseAttributes(
    is_prohibited_practice=is_prohibited,
    is_safety_component_regulated_product=is_safety_component,
    is_annex3_area=is_annex3,
    annex3_area=annex3_area,
    significant_risk_to_health_safety_fundamental_rights=significant_risk,
    has_transparency_obligation=has_transparency,
)

classification = classify(attrs)
label, display_fn = RISK_DISPLAY[classification.risk_class]
display_fn(f"**{label}**, Regel: {classification.matched_rule}")

# Session-State-Keys werden auf Use Case UND konkrete Klassifizierung gescoped:
# so hängt die angezeigte Begründung nie an einem anderen Use Case oder einer
# inzwischen durch den Fragebogen überholten Klassifizierung (siehe rationale.py:
# der LLM-Prompt hängt exakt von use_case + risk_class + matched_rule ab, nicht
# von den rohen Fragebogen-Attributen; dieselbe Klassifizierung liefert also
# dieselbe gültige Begründung).
rationale_key = (
    f"rationale::{use_case.key}::{classification.risk_class.value}::{classification.matched_rule}"
)
metamorphic_key = f"metamorphic_result::{use_case.key}"

if st.button("Begründung generieren (LLM)"):
    try:
        llm = get_llm()
        with st.spinner("Begründung wird generiert..."):
            st.session_state[rationale_key] = generate_rationale(llm, use_case, classification)
    except Exception as e:
        st.error(f"Begründung konnte nicht automatisch generiert werden: {e}")

rationale = st.session_state.get(rationale_key)
if rationale:
    st.markdown(f"**Begründung:** {rationale}")

metamorphic_result = st.session_state.get(metamorphic_key)
if use_case.has_metamorphic_demo and classification.risk_class == RiskClass.HIGH_RISK:
    st.subheader("Metamorpher Test")
    st.markdown(TEMPERATURE_MONOTONICITY_RELATION.description)
    if st.button("Metamorphen Test ausführen"):
        source_inputs = dict(
            outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
        )
        metamorphic_result = run_relation(
            decide_cooling_intensity, TEMPERATURE_MONOTONICITY_RELATION, source_inputs
        )
        st.session_state[metamorphic_key] = metamorphic_result

    if metamorphic_result:
        status = "✅ BESTANDEN" if metamorphic_result.passed else "❌ FEHLGESCHLAGEN"
        st.markdown(f"**Ergebnis:** {status}")
        st.markdown(
            f"- Quellfall: {metamorphic_result.source_inputs} → "
            f"Kühlintensität {metamorphic_result.source_output:.1f}"
        )
        st.markdown(
            f"- Folgefall: {metamorphic_result.followup_inputs} → "
            f"Kühlintensität {metamorphic_result.followup_output:.1f}"
        )

if classification.risk_class == RiskClass.HIGH_RISK:
    st.subheader("Governance-Artefakt")
    artifact_rationale = rationale or (
        f"Automatische Begründung nicht verfügbar. "
        f"Klassifizierungsregel: {classification.matched_rule}"
    )
    artifact = generate_governance_artifact(
        use_case, classification, artifact_rationale, metamorphic_result
    )
    st.markdown(artifact)
    st.download_button(
        "Als Markdown herunterladen",
        data=artifact,
        file_name=f"{use_case.key}_governance.md",
        mime="text/markdown",
    )


with under_the_hood():
    st.markdown(
        "Die Klassifizierung ist **deterministisch** und läuft ohne LLM. "
        "Regel-Priorität in `risk_engine.py`:"
    )
    st.code(
        "Art. 5   verbotene Praktik      -> unzulässig\n"
        "Art. 6(1) Sicherheitsbauteil     -> Hochrisiko\n"
        "Art. 6(2) Annex III (+ 6(3))     -> Hochrisiko\n"
        "Art. 50  Transparenzpflicht      -> begrenztes Risiko\n"
        "sonst                            -> minimales Risiko",
        language="text",
    )
    _attr_labels = {
        "is_prohibited_practice": "Art. 5, verbotene Praktik",
        "is_safety_component_regulated_product": "Art. 6(1), Sicherheitsbauteil",
        "is_annex3_area": "Annex-III-Bereich",
        "annex3_area": "Annex-III-Kategorie",
        "significant_risk_to_health_safety_fundamental_rights": "Art. 6(3), signifikantes Risiko",
        "has_transparency_obligation": "Art. 50, Transparenzpflicht",
    }
    _values = attrs.model_dump() if hasattr(attrs, "model_dump") else vars(attrs)
    st.code(
        "\n".join(
            f"{_attr_labels.get(k, k):<38} {getattr(v, 'value', v)}" for k, v in _values.items()
        ),
        language="text",
    )
    st.caption(f"Getroffene Regel: {classification.matched_rule}")
    st.markdown(
        "Das LLM formuliert ausschließlich die Begründung in Prosa und kann die "
        "Klasse nicht mehr verändern. Fällt es aus, bleibt das Governance-Artefakt "
        "trotzdem verfügbar."
    )

portfolio_footer(
    repo="ai-risk-classifier",
    project_id="ai-act-validation-toolkit",
    caveats=[
        "keine rechtsverbindliche Compliance-Aussage",
        "drei hinterlegte Use Cases, kein Freitext-Import",
        "eine metamorphe Relation, nicht die volle Methodik der Promotion",
        "Free-Tier-Hosting, der erste Aufruf kann einen Kaltstart haben",
    ],
)
