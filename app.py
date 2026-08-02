"""Streamlit-UI für den AI Risk Classifier (Portfolio-Demo, MARCO.OS-Stil)."""

import sys
from pathlib import Path

import streamlit as st

# Das Verzeichnis dieser Datei auf den Importpfad legen, damit portfolio_ui
# sowohl beim normalen Start (Streamlit legt es selbst dorthin) als auch im
# Test-Harness (AppTest.from_file laeuft vom Repo-Wurzelverzeichnis) gefunden wird.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_act_toolkit.governance import (
    EvidenceBundle,
    EvidenceEntry,
    generate_governance_artifact,
    render_kill_matrix,
)
from ai_act_toolkit.llm import get_llm
from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.obligations import EvidenceKind, obligations_for
from ai_act_toolkit.rationale import generate_rationale
from ai_act_toolkit.risk_engine import Annex3Area, RiskClass, UseCaseAttributes, classify
from ai_act_toolkit.suts import suts_for
from ai_act_toolkit.use_cases import ALL_USE_CASES
from portfolio_ui import (
    example_picker,
    page_header,
    page_setup,
    portfolio_footer,
    under_the_hood,
)

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
_EXAMPLE_TO_USE_CASE = dict(zip(EXAMPLES, use_case_titles, strict=True))

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

st.subheader("1. Einstufung")
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
    f"rationale::{use_case.key}::{classification.risk_class.value}"
    f"::{classification.matched_rule}"
)


def _prune_rationales(active_prefix: str) -> None:
    """Verwirft LLM-Begründungen, die zu einem anderen Use Case gehören.

    Ohne das sammelt der session_state pro (Use Case, Klasse, Regel)-
    Kombination einen Key an und wird ihn nie wieder los.
    """
    stale = [
        key
        for key in st.session_state
        if key.startswith("rationale::") and not key.startswith(active_prefix)
    ]
    for key in stale:
        del st.session_state[key]


_prune_rationales(f"rationale::{use_case.key}::")

if st.button("Begründung generieren (LLM)"):
    try:
        llm = get_llm()
        with st.spinner("Begründung wird generiert..."):
            st.session_state[rationale_key] = generate_rationale(
                llm, use_case, classification
            )
    except Exception as e:
        st.error(f"Begründung konnte nicht automatisch generiert werden: {e}")

rationale = st.session_state.get(rationale_key)
if rationale:
    st.markdown(f"**Begründung:** {rationale}")

obligations = obligations_for(classification)

st.subheader("2. Pflichten")
if not obligations:
    st.info("Aus dieser Einstufung folgen keine besonderen Pflichten.")
else:
    st.markdown(
        "Diese Pflichten folgen aus der Einstufung. Belegbar sind nur die, "
        "für die es einen ausführbaren technischen Nachweis gibt:"
    )
    _MARKER = {
        EvidenceKind.TECHNICAL_TEST: "🧪 technisch nachweisbar",
        EvidenceKind.DOCUMENTATION: "📄 teilweise über die Dokumentation",
        EvidenceKind.PROCESS: "🏢 Prozesspflicht",
    }
    for obligation in obligations:
        st.markdown(
            f"- **{obligation.article}** {obligation.title} — "
            f"{_MARKER[obligation.evidence_kind]}"
        )

specs = suts_for(use_case.key)
evidence = None

st.subheader("3. Nachweis")
if not specs:
    st.info(
        "Für diesen Use Case ist kein System unter Test hinterlegt — "
        "es lässt sich hier also kein technischer Nachweis führen."
    )
else:
    st.markdown(
        "Der AI Act verlangt den Nachweis, sagt aber nicht wie. Bei einem "
        "KI-System scheitert der naive Weg am Orakel-Problem: die richtige "
        "Ausgabe ist unbekannt. Metamorphes Testen prüft deshalb keine "
        "einzelne Ausgabe, sondern eine **Beziehung** zwischen zwei Ausgaben."
    )
    entries = []
    for spec in specs:
        st.markdown(f"#### {spec.label}")
        st.caption(spec.description)

        fault_options = ["(keiner)"] + [m.label for m in spec.mutants]
        fault_label = st.selectbox(
            "Fehler injizieren",
            fault_options,
            key=f"fault::{use_case.key}::{spec.key}",
        )
        active_fn = spec.fn
        if fault_label != "(keiner)":
            mutant = next(m for m in spec.mutants if m.label == fault_label)
            active_fn = mutant.fn
            st.caption(f"Eingebauter Defekt: {mutant.defect}")

        suite_result = run_suite(active_fn, spec.relations, spec.baseline_inputs)
        for result in suite_result.results:
            status = "✅ bestanden" if result.passed else "❌ FEHLGESCHLAGEN"
            with st.expander(
                f"{status} — {result.relation.name} ({result.relation.evidence_for})",
                expanded=not result.passed,
            ):
                st.markdown(result.relation.description)
                st.markdown(
                    f"- Quellfall: `{result.source_inputs}` → "
                    f"**{result.source_output:.2f}**"
                )
                st.markdown(
                    f"- Folgefall: `{result.followup_inputs}` → "
                    f"**{result.followup_output:.2f}**"
                )

        matrix = run_kill_matrix(spec.relations, spec.mutants, spec.baseline_inputs)
        killed, total = matrix.score
        st.markdown(
            f"**Kill-Matrix** — wie gut fängt diese Relationsmenge eingebaute "
            f"Fehler? Mutation Score **{killed}/{total}**."
        )
        st.markdown(render_kill_matrix(matrix))

        entries.append(EvidenceEntry(spec.label, suite_result, matrix))

    evidence = EvidenceBundle(entries=tuple(entries))

if obligations:
    st.subheader("4. Artefakt")
    artifact_rationale = rationale or (
        f"Automatische Begründung nicht verfügbar. "
        f"Klassifizierungsregel: {classification.matched_rule}"
    )
    artifact = generate_governance_artifact(
        use_case, classification, artifact_rationale, obligations, evidence
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
        "Klasse nicht mehr verändern. Der Nachweis in Schritt 3 läuft vollständig "
        "ohne LLM: Relationen und Mutanten sind Code, keine Sprachausgabe."
    )

portfolio_footer(
    repo="ai-risk-classifier",
    project_id="ai-act-validation-toolkit",
    caveats=[
        "keine rechtsverbindliche Compliance-Aussage",
        "drei hinterlegte Use Cases, kein Freitext-Import",
        "belegt 2 von 7 Hochrisiko-Pflichten technisch, der Rest sind Prozesspflichten",
        "Free-Tier-Hosting, der erste Aufruf kann einen Kaltstart haben",
    ],
)
