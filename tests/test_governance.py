from ai_act_toolkit.governance import (
    EvidenceBundle,
    EvidenceEntry,
    generate_governance_artifact,
    render_kill_matrix,
)
from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.obligations import obligations_for
from ai_act_toolkit.risk_engine import ClassificationResult, RiskClass
from ai_act_toolkit.suts import SCORING_SUT
from ai_act_toolkit.use_cases import RECRUITING

HIGH_RISK = ClassificationResult(
    RiskClass.HIGH_RISK, "Art. 6(2) + Annex III (employment): signifikantes Risiko"
)


def _bundle():
    suite_result = run_suite(
        SCORING_SUT.fn, SCORING_SUT.relations, SCORING_SUT.baseline_inputs
    )
    matrix = run_kill_matrix(
        SCORING_SUT.relations, SCORING_SUT.mutants, SCORING_SUT.baseline_inputs
    )
    return EvidenceBundle(
        entries=(EvidenceEntry(SCORING_SUT.label, suite_result, matrix),)
    )


def _artifact(evidence):
    return generate_governance_artifact(
        RECRUITING, HIGH_RISK, "Testbegründung.", obligations_for(HIGH_RISK), evidence
    )


def test_article_15_is_checked_off_when_the_suite_ran():
    assert "- [x] **Art. 15**" in _artifact(_bundle())


def test_article_15_stays_open_without_evidence():
    artifact = _artifact(None)
    assert "- [x] **Art. 15**" not in artifact
    assert "- [ ] **Art. 15**" in artifact


def test_article_10_is_checked_off_by_the_name_invariance_relation():
    assert "- [x] **Art. 10**" in _artifact(_bundle())


def test_documentation_obligations_are_marked_partial():
    artifact = _artifact(_bundle())
    assert "- [~] **Art. 11**" in artifact
    assert "- [~] **Art. 9**" in artifact


def test_process_obligations_are_never_checked_off():
    artifact = _artifact(_bundle())
    for article in ("Art. 12", "Art. 13", "Art. 14"):
        assert f"- [ ] **{article}**" in artifact
    assert "Prozesspflicht" in artifact


def test_artifact_contains_the_required_sections():
    artifact = _artifact(_bundle())
    for section in (
        "# Risk Assessment",
        "## Systembeschreibung",
        "## Klassifizierung",
        "## Begründung",
        "## Nachweise",
        "## Konformitätscheckliste",
    ):
        assert section in artifact
    assert "keine juristische" in artifact.lower()


def test_artifact_omits_evidence_section_without_evidence():
    assert "## Nachweise" not in _artifact(None)


def test_kill_matrix_renders_as_markdown_table_with_score():
    matrix = run_kill_matrix(
        SCORING_SUT.relations, SCORING_SUT.mutants, SCORING_SUT.baseline_inputs
    )
    table = render_kill_matrix(matrix)
    assert "| Relation |" in table
    assert "Namensinvarianz" in table
    assert "Mutation Score: 4/5" in table
