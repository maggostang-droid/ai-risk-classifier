"""Erzeugt das Governance-Artefakt: Risk Assessment plus Konformitätscheckliste.

Der Unterschied zur früheren Fassung: die Checkliste ist keine Konstante
mehr. Jede Pflicht wird in einem von drei Zuständen gerendert —

    [x]  belegt: eine metamorphe Relation, die auf diesen Artikel einzahlt,
         wurde ausgeführt und bestanden
    [~]  teilweise: dieses Artefakt selbst ist ein Beitrag zur Pflicht
         (Annex IV Nr. 2(g): dokumentiertes Testverfahren)
    [ ]  offen: kein Nachweis geführt, oder reine Prozesspflicht

Damit ist der metamorphe Test nicht mehr ein Abschnitt neben der Checkliste,
sondern das, was die Checkliste abhakt.
"""

from dataclasses import dataclass

from ai_act_toolkit.metamorphic.mutation import KillMatrix
from ai_act_toolkit.metamorphic.suite import SuiteResult
from ai_act_toolkit.obligations import EvidenceKind, Obligation
from ai_act_toolkit.risk_engine import ClassificationResult
from ai_act_toolkit.use_cases import UseCase


@dataclass(frozen=True)
class EvidenceEntry:
    """Was für eine SUT tatsächlich ausgeführt wurde."""

    sut_label: str
    suite_result: SuiteResult
    kill_matrix: KillMatrix


@dataclass(frozen=True)
class EvidenceBundle:
    entries: tuple[EvidenceEntry, ...]

    def articles_covered(self) -> set[str]:
        """Artikel, für die mindestens eine Relation lief und alle bestanden."""
        covered: set[str] = set()
        for entry in self.entries:
            for article, results in entry.suite_result.by_article().items():
                if all(result.passed for result in results):
                    covered.add(article)
        return covered

    def summary_for(self, article: str) -> str:
        """Kurzbeleg für die Checkliste."""
        parts = []
        for entry in self.entries:
            results = entry.suite_result.by_article().get(article, [])
            if not results:
                continue
            names = ", ".join(result.relation.name for result in results)
            killed, total = entry.kill_matrix.score
            parts.append(
                f"{entry.sut_label}: {names} bestanden, Mutation Score {killed}/{total}"
            )
        return "; ".join(parts)


def render_kill_matrix(kill_matrix: KillMatrix) -> str:
    """Rendert die Kill-Matrix als Markdown-Tabelle mit Mutation Score."""
    header = "| Relation | " + " | ".join(m.label for m in kill_matrix.mutants) + " |"
    divider = "|---" * (len(kill_matrix.mutants) + 1) + "|"
    rows = []
    for relation in kill_matrix.relations:
        cells = [
            "getötet" if kill_matrix.killed[(relation.name, mutant.key)] else "überlebt"
            for mutant in kill_matrix.mutants
        ]
        rows.append(f"| {relation.name} | " + " | ".join(cells) + " |")
    killed, total = kill_matrix.score
    survivors = ", ".join(m.label for m in kill_matrix.survivors()) or "keine"
    return "\n".join(
        [
            header,
            divider,
            *rows,
            "",
            f"**Mutation Score: {killed}/{total}**",
            "Überlebende Mutanten (bekannte Blindstellen der Relationsmenge): "
            f"{survivors}",
        ]
    )


_PARTIAL_NOTE = (
    "teilweise: dieses Artefakt dokumentiert das verwendete Testverfahren "
    "(Annex IV Nr. 2(g))."
)
_PROCESS_NOTE = "Prozesspflicht, durch dieses Werkzeug nicht belegbar."


def _render_obligation(obligation: Obligation, evidence: EvidenceBundle | None) -> str:
    head = f"**{obligation.article}** {obligation.title}"
    if obligation.evidence_kind is EvidenceKind.TECHNICAL_TEST:
        if evidence is not None and obligation.article in evidence.articles_covered():
            return f"- [x] {head} — belegt: {evidence.summary_for(obligation.article)}"
        return f"- [ ] {head} — offen: kein Nachweis ausgeführt."
    if obligation.evidence_kind is EvidenceKind.DOCUMENTATION:
        if evidence is not None:
            return f"- [~] {head} — {_PARTIAL_NOTE}"
        return f"- [ ] {head} — offen: kein Testverfahren dokumentiert."
    return f"- [ ] {head} — {_PROCESS_NOTE}"


def generate_governance_artifact(
    use_case: UseCase,
    classification: ClassificationResult,
    rationale: str,
    obligations: list[Obligation],
    evidence: EvidenceBundle | None,
) -> str:
    """Baut das Markdown-Artefakt aus Einstufung, Pflichten und vorhandener Evidenz."""
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

    if evidence is not None and evidence.entries:
        lines += ["## Nachweise", ""]
        for entry in evidence.entries:
            passed, total = entry.suite_result.counts
            lines += [
                f"### {entry.sut_label}",
                f"Metamorphe Relations-Suite: {passed}/{total} bestanden.",
                "",
            ]
            for result in entry.suite_result.results:
                status = "bestanden" if result.passed else "FEHLGESCHLAGEN"
                lines += [
                    f"- **{result.relation.name}** "
                    f"({result.relation.evidence_for}): {status}",
                    f"  - {result.relation.description}",
                    f"  - Quellfall {result.source_inputs} → {result.source_output:.2f}",
                    f"  - Folgefall {result.followup_inputs} "
                    f"→ {result.followup_output:.2f}",
                ]
            lines += [
                "",
                "Mutationsanalyse (Annex IV Nr. 2(g), Güte des Testverfahrens):",
                "",
                render_kill_matrix(entry.kill_matrix),
                "",
            ]

    lines += ["## Konformitätscheckliste", ""]
    for obligation in obligations:
        lines.append(_render_obligation(obligation, evidence))
    lines += [
        "",
        (
            "*Hinweis: Dieses Dokument ist eine methodische Demonstration und "
            "ersetzt keine juristische Prüfung oder ein echtes "
            "Konformitätsbewertungsverfahren.*"
        ),
    ]

    return "\n".join(lines)
