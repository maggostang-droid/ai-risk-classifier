# AI Act Evidence Toolkit — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Metamorphes Testen wird vom Nebenfeature zum Kern — die Risikoeinstufung erzeugt konkrete Artikelpflichten, eine Relations-Suite mit Fehlerinjektion und Kill-Matrix liefert die Evidenz dafür, und das Governance-Artefakt hakt genau die Pflichten ab, für die ein Nachweis vorliegt.

**Architecture:** Vier Stufen, die aufeinander aufbauen: `risk_engine` (unverändert, deterministisch) → `obligations` (neu: Klasse → Pflichten mit `EvidenceKind`) → `metamorphic.suite` + `metamorphic.mutation` (Relations-Suite und Kill-Matrix gegen drei Systeme unter Test) → `governance` (Pflichten + Evidenz zum Markdown-Artefakt). Die Kopplung zwischen Stufe 2 und 4 läuft über ein neues Feld `evidence_for` an jeder metamorphen Relation.

**Tech Stack:** Python 3.10+, Streamlit, pytest, ruff. LangChain nur für den unveränderten Prosa-Satz. Kein neues Runtime-Dependency.

**Spec:** `docs/superpowers/specs/2026-08-02-evidence-toolkit-design.md`

## Global Constraints

- Arbeitsverzeichnis ist der Worktree `C:\Users\Marco\OneDrive\02_Portfolio\_worktrees\evidence-toolkit`, Branch `feature/evidence-toolkit`.
- Alle Doku, Docstrings, Kommentare und UI-Texte auf **Deutsch** (Projektkonvention, siehe `CLAUDE.md`).
- Alle Tests laufen **ohne Netzwerk und ohne LLM-Zugriff**. Kein Mock ersetzt echtes Verhalten.
- `risk_engine.py` behält seine **Null-LLM-Abhängigkeit**. Das LLM wird in diesem Plan nicht angefasst und nicht ausgebaut.
- **Kein neues Runtime-Dependency.** pandas ist über Streamlit bereits vorhanden und darf verwendet werden.
- Produktname im UI und in der Doku: **AI Act Evidence Toolkit**. Repo-Slug `ai-risk-classifier`, Python-Paket `ai_act_toolkit` und die MARCO.OS-Projekt-`id` `ai-act-validation-toolkit` bleiben **unverändert**.
- Python-Aufruf im Worktree immer über `.venv/Scripts/python.exe`.
- Commit-Messages auf Deutsch, ohne Umlaute im Betreff (Konvention der bestehenden History).

## Vorbereitung (einmalig, vor Task 1)

```bash
cd /c/Users/Marco/OneDrive/02_Portfolio/_worktrees/evidence-toolkit
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest tests/ -v    # Erwartung: 17 passed
```

Die 17 grünen Tests sind der Ausgangszustand. Nach jedem Task muss die Suite wieder vollständig grün sein.

## Dateistruktur nach Abschluss

| Datei | Verantwortung |
|---|---|
| `src/ai_act_toolkit/risk_engine.py` | unverändert — Attribute → Risikoklasse |
| `src/ai_act_toolkit/obligations.py` | **neu** — Risikoklasse → Pflichtenliste mit `EvidenceKind` |
| `src/ai_act_toolkit/use_cases.py` | geändert — `has_metamorphic_demo` entfällt |
| `src/ai_act_toolkit/metamorphic/core.py` | verschoben aus `metamorphic.py`, `evidence_for` ergänzt |
| `src/ai_act_toolkit/metamorphic/suite.py` | **neu** — alle Relationen einer SUT auf einmal |
| `src/ai_act_toolkit/metamorphic/mutation.py` | **neu** — `Mutant`, `KillMatrix`, Mutation Score |
| `src/ai_act_toolkit/suts/comfort_climate.py` | verschoben aus `comfort_system_sut.py`, erweitert |
| `src/ai_act_toolkit/suts/comfort_seat.py` | **neu** — sicherheitsrelevante SUT zu Art. 6(1) |
| `src/ai_act_toolkit/suts/recruiting_scorer.py` | **neu** — naiver/gefixter Scorer, Namensinvarianz |
| `src/ai_act_toolkit/suts/__init__.py` | **neu** — `SUTSpec` + Registry Use-Case → SUTs |
| `src/ai_act_toolkit/governance.py` | umgebaut — Pflichten + Evidenz statt Konstante |
| `app.py` | umgebaut — vier Schritte, Fehlerinjektion, State-Pruning |
| `.github/workflows/ci.yml` | **neu** — ruff + pytest |

---

### Task 1: Modulumzug und `evidence_for`

Rein mechanisch, kein Verhaltenswechsel — aber breit gestreut. Deshalb zuerst, damit die Suite nie lange rot ist.

**Files:**
- Create: `src/ai_act_toolkit/metamorphic/__init__.py`
- Create: `src/ai_act_toolkit/metamorphic/core.py`
- Delete: `src/ai_act_toolkit/metamorphic.py`
- Create: `src/ai_act_toolkit/suts/__init__.py`
- Create: `src/ai_act_toolkit/suts/comfort_climate.py`
- Delete: `src/ai_act_toolkit/comfort_system_sut.py`
- Modify: `app.py:21-24` (Importblock)
- Modify: `tests/test_metamorphic.py:1-5`, `tests/test_governance.py:1-6`

**Interfaces:**
- Produces: `ai_act_toolkit.metamorphic.core.MetamorphicRelation(name, description, transform, check, evidence_for)`, `MetamorphicResult`, `run_relation(sut_fn, relation, source_inputs) -> MetamorphicResult`; `ai_act_toolkit.suts.comfort_climate.decide_cooling_intensity(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count) -> float` und `TEMPERATURE_MONOTONICITY_RELATION`.

- [ ] **Step 1: Test auf das neue Feld schreiben**

Neue Datei `tests/test_metamorphic_core.py`:

```python
from ai_act_toolkit.metamorphic.core import MetamorphicRelation, run_relation


def test_relation_declares_which_article_it_supports():
    relation = MetamorphicRelation(
        name="Dummy",
        description="Verdoppelt die Eingabe.",
        transform=lambda inputs: {**inputs, "x": inputs["x"] * 2},
        check=lambda source, followup: followup >= source,
        evidence_for="Art. 15",
    )
    assert relation.evidence_for == "Art. 15"


def test_run_relation_reports_violation():
    relation = MetamorphicRelation(
        name="Monotonie",
        description="Groesseres x darf das Ergebnis nicht senken.",
        transform=lambda inputs: {**inputs, "x": inputs["x"] + 1.0},
        check=lambda source, followup: followup >= source,
        evidence_for="Art. 15",
    )
    result = run_relation(lambda x: -x, relation, {"x": 1.0})
    assert result.passed is False
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_metamorphic_core.py -v`
Erwartung: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.metamorphic.core'`

- [ ] **Step 3: Paket anlegen und Inhalt verschieben**

`src/ai_act_toolkit/metamorphic/__init__.py`:

```python
"""Metamorphes Testen: Relationen, Suiten und Mutationsanalyse."""

from ai_act_toolkit.metamorphic.core import (
    MetamorphicRelation,
    MetamorphicResult,
    run_relation,
)

__all__ = ["MetamorphicRelation", "MetamorphicResult", "run_relation"]
```

`src/ai_act_toolkit/metamorphic/core.py` — Inhalt der bisherigen `metamorphic.py`, mit einem zusätzlichen Feld:

```python
"""Generischer Runner für metamorphe Tests.

Eine metamorphe Relation prüft nicht eine einzelne Ausgabe gegen ein
festes Referenzergebnis (das "Orakel-Problem" bei KI-Systemen: die
"richtige" Ausgabe ist oft unbekannt), sondern eine Beziehung zwischen
der Ausgabe eines Quellfalls und der Ausgabe eines daraus abgeleiteten
Folgefalls, genau das Prinzip aus Marcos Promotion, hier auf konkret
ausführbare Fälle reduziert.
"""

from dataclasses import dataclass
from typing import Callable


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
```

Der Wechsel auf `dict(source_inputs)` erledigt nebenbei das in `HANDOVER.md` geparkte Minor-Finding „`source_inputs` speichert eine Referenz statt einer Kopie".

Dann `src/ai_act_toolkit/metamorphic.py` löschen.

- [ ] **Step 4: SUT-Paket anlegen**

`src/ai_act_toolkit/suts/__init__.py` (Registry folgt in Task 8, vorerst nur Paketmarker):

```python
"""Systeme unter Test, gegen die die metamorphen Relationen laufen."""
```

`src/ai_act_toolkit/suts/comfort_climate.py` — Inhalt der bisherigen `comfort_system_sut.py`, Import angepasst und `evidence_for` ergänzt:

```python
"""Toy-'System unter Test': simulierte Klimasteuerung des Komfortsystems.

Kein echtes ML-Modell, ein bewusst einfaches, deterministisches Stellvertreter-
Modell, an dem die metamorphe Testmethodik konkret demonstriert wird.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation


def decide_cooling_intensity(
    outside_temp_c: float,
    cabin_temp_c: float,
    desired_temp_c: float,
    occupant_count: int,
) -> float:
    """Berechnet die Ziel-Kühlintensität (0-100) des Komfortsystems."""
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    cabin_factor = max(0.0, cabin_temp_c - desired_temp_c) * 3.0
    occupant_factor = occupant_count * 1.5
    intensity = base + outside_factor + cabin_factor + occupant_factor
    return max(0.0, min(100.0, intensity))


TEMPERATURE_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Temperatur-Monotonie",
    description=(
        "Steigt die Außentemperatur bei sonst gleichen Bedingungen, darf die "
        "Ziel-Kühlintensität nicht sinken (Monotonie-Annahme)."
    ),
    transform=lambda inputs: {**inputs, "outside_temp_c": inputs["outside_temp_c"] + 5.0},
    check=lambda source_output, followup_output: followup_output >= source_output,
    evidence_for="Art. 15",
)
```

Dann `src/ai_act_toolkit/comfort_system_sut.py` löschen.

- [ ] **Step 5: Alle Importstellen nachziehen**

In `app.py` den Block ab Zeile 21:

```python
from ai_act_toolkit.suts.comfort_climate import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
```

und

```python
from ai_act_toolkit.metamorphic import run_relation
```

In `tests/test_metamorphic.py` und `tests/test_governance.py` jeweils:

```python
from ai_act_toolkit.suts.comfort_climate import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
from ai_act_toolkit.metamorphic import run_relation
```

- [ ] **Step 6: Komplette Suite laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Erwartung: 19 passed (17 bestehende + 2 neue)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: metamorphic und SUT in eigene Pakete, evidence_for an der Relation"
```

---

### Task 2: `obligations.py` — von der Klasse zur Pflicht

Das fehlende Bindeglied. Ohne diesen Schritt wirkt der metamorphe Test angeklebt.

**Files:**
- Create: `src/ai_act_toolkit/obligations.py`
- Test: `tests/test_obligations.py`

**Interfaces:**
- Consumes: `ClassificationResult`, `RiskClass` aus `risk_engine.py`
- Produces: `EvidenceKind` (Enum mit `TECHNICAL_TEST`, `DOCUMENTATION`, `PROCESS`), `Obligation(article, title, description, evidence_kind)`, `obligations_for(classification: ClassificationResult) -> list[Obligation]`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_obligations.py`:

```python
from ai_act_toolkit.obligations import EvidenceKind, obligations_for
from ai_act_toolkit.risk_engine import ClassificationResult, RiskClass


def _articles(classification):
    return [o.article for o in obligations_for(classification)]


def test_high_risk_yields_articles_9_to_15():
    result = ClassificationResult(RiskClass.HIGH_RISK, "Art. 6(1): Sicherheitsbauteil")
    assert _articles(result) == [
        "Art. 9", "Art. 10", "Art. 11", "Art. 12", "Art. 13", "Art. 14", "Art. 15",
    ]


def test_limited_risk_yields_only_article_50():
    result = ClassificationResult(RiskClass.LIMITED_RISK, "Art. 50: Transparenzpflicht")
    assert _articles(result) == ["Art. 50"]


def test_minimal_risk_yields_no_obligations():
    result = ClassificationResult(RiskClass.MINIMAL_RISK, "keine Kategorie")
    assert obligations_for(result) == []


def test_prohibited_practice_yields_article_5():
    result = ClassificationResult(RiskClass.UNACCEPTABLE, "Art. 5: verbotene Praktik")
    assert _articles(result) == ["Art. 5"]


def test_only_articles_10_and_15_are_provable_by_technical_test():
    result = ClassificationResult(RiskClass.HIGH_RISK, "Art. 6(1): Sicherheitsbauteil")
    provable = [
        o.article
        for o in obligations_for(result)
        if o.evidence_kind is EvidenceKind.TECHNICAL_TEST
    ]
    assert provable == ["Art. 10", "Art. 15"]


def test_articles_12_to_14_are_process_obligations():
    result = ClassificationResult(RiskClass.HIGH_RISK, "Art. 6(1): Sicherheitsbauteil")
    process = [
        o.article
        for o in obligations_for(result)
        if o.evidence_kind is EvidenceKind.PROCESS
    ]
    assert process == ["Art. 12", "Art. 13", "Art. 14"]
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_obligations.py -v`
Erwartung: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.obligations'`

- [ ] **Step 3: Implementieren**

`src/ai_act_toolkit/obligations.py`:

```python
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
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_obligations.py -v`
Erwartung: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/obligations.py tests/test_obligations.py
git commit -m "feat: Pflichtenableitung aus der Risikoklasse mit Evidenzarten"
```

---

### Task 3: Relations-Suite

**Files:**
- Create: `src/ai_act_toolkit/metamorphic/suite.py`
- Modify: `src/ai_act_toolkit/metamorphic/__init__.py`
- Test: `tests/test_suite.py`

**Interfaces:**
- Consumes: `MetamorphicRelation`, `MetamorphicResult`, `run_relation` aus `metamorphic.core`
- Produces: `SuiteResult` mit `.results: list[MetamorphicResult]`, `.passed: bool`, `.counts -> tuple[int, int]`, `.by_article() -> dict[str, list[MetamorphicResult]]`; `run_suite(sut_fn, relations, baseline_inputs) -> SuiteResult`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_suite.py`:

```python
from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.suite import run_suite

RISING = MetamorphicRelation(
    name="Steigend",
    description="Groesseres x darf das Ergebnis nicht senken.",
    transform=lambda inputs: {**inputs, "x": inputs["x"] + 1.0},
    check=lambda source, followup: followup >= source,
    evidence_for="Art. 15",
)

UNCHANGED = MetamorphicRelation(
    name="Unveraendert",
    description="y beeinflusst das Ergebnis nicht.",
    transform=lambda inputs: {**inputs, "y": inputs["y"] + 1.0},
    check=lambda source, followup: followup == source,
    evidence_for="Art. 10",
)

BASELINE = {"x": 1.0, "y": 1.0}


def _correct(x, y):
    return x * 2.0


def test_suite_passes_on_correct_sut():
    result = run_suite(_correct, [RISING, UNCHANGED], BASELINE)
    assert result.passed is True
    assert result.counts == (2, 2)


def test_suite_reports_which_relation_failed():
    def leaks_y(x, y):
        return x * 2.0 + y

    result = run_suite(leaks_y, [RISING, UNCHANGED], BASELINE)
    assert result.passed is False
    assert result.counts == (1, 2)
    failed = [r.relation.name for r in result.results if not r.passed]
    assert failed == ["Unveraendert"]


def test_suite_groups_results_by_article():
    result = run_suite(_correct, [RISING, UNCHANGED], BASELINE)
    grouped = result.by_article()
    assert set(grouped) == {"Art. 15", "Art. 10"}
    assert grouped["Art. 10"][0].relation.name == "Unveraendert"
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_suite.py -v`
Erwartung: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.metamorphic.suite'`

- [ ] **Step 3: Implementieren**

`src/ai_act_toolkit/metamorphic/suite.py`:

```python
"""Führt alle Relationen eines Systems unter Test auf einmal aus.

Eine einzelne Relation belegt wenig. Erst eine Suite mehrerer Relationen
deckt verschiedene Fehlerarten ab, und erst über `by_article()` lässt sich
das Ergebnis den AI-Act-Pflichten zuordnen.
"""

from dataclasses import dataclass
from typing import Callable, Iterable

from ai_act_toolkit.metamorphic.core import (
    MetamorphicRelation,
    MetamorphicResult,
    run_relation,
)


@dataclass(frozen=True)
class SuiteResult:
    results: tuple[MetamorphicResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def counts(self) -> tuple[int, int]:
        """(bestanden, gesamt)."""
        return sum(1 for result in self.results if result.passed), len(self.results)

    def by_article(self) -> dict[str, list[MetamorphicResult]]:
        """Gruppiert die Ergebnisse nach dem Artikel, auf den sie einzahlen."""
        grouped: dict[str, list[MetamorphicResult]] = {}
        for result in self.results:
            grouped.setdefault(result.relation.evidence_for, []).append(result)
        return grouped


def run_suite(
    sut_fn: Callable[..., float],
    relations: Iterable[MetamorphicRelation],
    baseline_inputs: dict,
) -> SuiteResult:
    return SuiteResult(
        results=tuple(
            run_relation(sut_fn, relation, baseline_inputs) for relation in relations
        )
    )
```

`src/ai_act_toolkit/metamorphic/__init__.py` erweitern:

```python
from ai_act_toolkit.metamorphic.suite import SuiteResult, run_suite

__all__ = [
    "MetamorphicRelation",
    "MetamorphicResult",
    "run_relation",
    "SuiteResult",
    "run_suite",
]
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_suite.py -v`
Erwartung: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/metamorphic/ tests/test_suite.py
git commit -m "feat: Relations-Suite mit Gruppierung nach Artikel"
```

---

### Task 4: Mutanten und Kill-Matrix

Die Metrik, die dem Projekt heute fehlt.

**Files:**
- Create: `src/ai_act_toolkit/metamorphic/mutation.py`
- Modify: `src/ai_act_toolkit/metamorphic/__init__.py`
- Test: `tests/test_mutation.py`

**Interfaces:**
- Consumes: `MetamorphicRelation`, `run_relation` aus `metamorphic.core`
- Produces: `Mutant(key, label, defect, fn, expected_survivor=False)`, `KillMatrix` mit `.is_killed(mutant) -> bool`, `.killed_by(mutant) -> list[str]`, `.score -> tuple[int, int]`, `.survivors() -> list[Mutant]`; `run_kill_matrix(relations, mutants, baseline_inputs) -> KillMatrix`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_mutation.py`:

```python
from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant, run_kill_matrix

RISING = MetamorphicRelation(
    name="Steigend",
    description="Groesseres x darf das Ergebnis nicht senken.",
    transform=lambda inputs: {**inputs, "x": inputs["x"] + 1.0},
    check=lambda source, followup: followup >= source,
    evidence_for="Art. 15",
)

UNCHANGED = MetamorphicRelation(
    name="Unveraendert",
    description="y beeinflusst das Ergebnis nicht.",
    transform=lambda inputs: {**inputs, "y": inputs["y"] + 1.0},
    check=lambda source, followup: followup == source,
    evidence_for="Art. 10",
)

BASELINE = {"x": 1.0, "y": 1.0}

SIGN_FLIP = Mutant(
    key="vorzeichen",
    label="Vorzeichenfehler",
    defect="x geht negativ statt positiv ein.",
    fn=lambda x, y: -x * 2.0,
)

Y_LEAKS = Mutant(
    key="y_leckt",
    label="y leckt ein",
    defect="y beeinflusst das Ergebnis, obwohl es das nicht darf.",
    fn=lambda x, y: x * 2.0 + y,
)

ROUNDING = Mutant(
    key="rundung",
    label="Rundungsfehler",
    defect="Ergebnis wird auf ganze Zahlen gerundet.",
    fn=lambda x, y: float(round(x * 2.0)),
    expected_survivor=True,
)

CRASHES = Mutant(
    key="absturz",
    label="Absturz",
    defect="Wirft bei jedem Aufruf eine Exception.",
    fn=lambda x, y: 1 / 0,
)


def test_each_mutant_is_killed_by_the_matching_relation():
    matrix = run_kill_matrix([RISING, UNCHANGED], [SIGN_FLIP, Y_LEAKS], BASELINE)
    assert matrix.killed_by(SIGN_FLIP) == ["Steigend"]
    assert matrix.killed_by(Y_LEAKS) == ["Unveraendert"]


def test_declared_survivor_is_caught_by_no_relation():
    matrix = run_kill_matrix([RISING, UNCHANGED], [ROUNDING], BASELINE)
    assert matrix.is_killed(ROUNDING) is False
    assert [m.key for m in matrix.survivors()] == ["rundung"]


def test_score_counts_mutants_not_cells():
    matrix = run_kill_matrix([RISING, UNCHANGED], [SIGN_FLIP, Y_LEAKS, ROUNDING], BASELINE)
    assert matrix.score == (2, 3)


def test_crashing_mutant_counts_as_killed():
    matrix = run_kill_matrix([RISING], [CRASHES], BASELINE)
    assert matrix.is_killed(CRASHES) is True
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_mutation.py -v`
Erwartung: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.metamorphic.mutation'`

- [ ] **Step 3: Implementieren**

`src/ai_act_toolkit/metamorphic/mutation.py`:

```python
"""Mutationsanalyse: wie gut ist die Relations-Suite eigentlich?

Ein bestandener metamorpher Test sagt für sich genommen wenig — er könnte
auch bestehen, weil die Relation nichts prüft. Deshalb werden absichtlich
fehlerhafte Varianten des Systems unter Test ("Mutanten") gegen dieselbe
Suite gefahren. Ein Mutant gilt als getötet, sobald ihn mindestens eine
Relation fängt. Der Mutation Score zählt Mutanten, nicht Zellen.

Ein überlebender Mutant ist kein Makel, sondern die interessanteste
Information: er zeigt die Blindstelle der Relationsmenge. Genau deshalb
gibt es `expected_survivor` — bekannte Blindstellen werden deklariert und
in den Tests festgenagelt, damit sie nicht stillschweigend verschwinden.
"""

from dataclasses import dataclass, field
from typing import Callable, Iterable

from ai_act_toolkit.metamorphic.core import MetamorphicRelation, run_relation


@dataclass(frozen=True)
class Mutant:
    key: str
    label: str
    defect: str
    fn: Callable[..., float]
    expected_survivor: bool = False


@dataclass(frozen=True)
class KillMatrix:
    relations: tuple[MetamorphicRelation, ...]
    mutants: tuple[Mutant, ...]
    killed: dict[tuple[str, str], bool] = field(default_factory=dict)

    def killed_by(self, mutant: Mutant) -> list[str]:
        """Namen der Relationen, die diesen Mutanten fangen."""
        return [
            relation.name
            for relation in self.relations
            if self.killed[(relation.name, mutant.key)]
        ]

    def is_killed(self, mutant: Mutant) -> bool:
        return bool(self.killed_by(mutant))

    def survivors(self) -> list[Mutant]:
        return [mutant for mutant in self.mutants if not self.is_killed(mutant)]

    @property
    def score(self) -> tuple[int, int]:
        """(getötete Mutanten, Mutanten gesamt)."""
        return len(self.mutants) - len(self.survivors()), len(self.mutants)


def run_kill_matrix(
    relations: Iterable[MetamorphicRelation],
    mutants: Iterable[Mutant],
    baseline_inputs: dict,
) -> KillMatrix:
    relations = tuple(relations)
    mutants = tuple(mutants)
    killed: dict[tuple[str, str], bool] = {}
    for relation in relations:
        for mutant in mutants:
            try:
                result = run_relation(mutant.fn, relation, baseline_inputs)
                caught = not result.passed
            except Exception:
                # Ein Mutant, der abstürzt, ist ebenfalls erkannt — die Relation
                # hat ihn zwar nicht inhaltlich widerlegt, aber sichtbar gemacht.
                caught = True
            killed[(relation.name, mutant.key)] = caught
    return KillMatrix(relations=relations, mutants=mutants, killed=killed)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_mutation.py -v`
Erwartung: 4 passed

- [ ] **Step 5: `__init__.py` ergänzen und Gesamtsuite prüfen**

```python
from ai_act_toolkit.metamorphic.mutation import KillMatrix, Mutant, run_kill_matrix
```

und in `__all__` aufnehmen.

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Erwartung: 32 passed

- [ ] **Step 6: Commit**

```bash
git add src/ai_act_toolkit/metamorphic/ tests/test_mutation.py
git commit -m "feat: Mutationsanalyse mit Kill-Matrix und Mutation Score"
```

---

### Task 5: Klimasteuerung — Relationen und Mutanten ausbauen

**Files:**
- Modify: `src/ai_act_toolkit/suts/comfort_climate.py`
- Test: `tests/test_sut_comfort_climate.py`

**Interfaces:**
- Produces: `CLIMATE_RELATIONS: tuple[MetamorphicRelation, ...]`, `CLIMATE_MUTANTS: tuple[Mutant, ...]`, `CLIMATE_BASELINE: dict`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_sut_comfort_climate.py`:

```python
import pytest

from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts.comfort_climate import (
    CLIMATE_BASELINE,
    CLIMATE_MUTANTS,
    CLIMATE_RELATIONS,
    decide_cooling_intensity,
)


def test_correct_sut_passes_every_relation():
    result = run_suite(decide_cooling_intensity, CLIMATE_RELATIONS, CLIMATE_BASELINE)
    assert result.passed is True, [r.relation.name for r in result.results if not r.passed]


@pytest.mark.parametrize(
    "mutant", [m for m in CLIMATE_MUTANTS if not m.expected_survivor], ids=lambda m: m.key
)
def test_every_declared_defect_is_killed(mutant):
    matrix = run_kill_matrix(CLIMATE_RELATIONS, [mutant], CLIMATE_BASELINE)
    assert matrix.is_killed(mutant) is True


@pytest.mark.parametrize(
    "mutant", [m for m in CLIMATE_MUTANTS if m.expected_survivor], ids=lambda m: m.key
)
def test_declared_survivors_really_survive(mutant):
    # Sperrt die dokumentierte Blindstelle: wer eine Relation nachruestet, die
    # diesen Mutanten faengt, muss auch README und Blindstellen-Abschnitt aendern.
    matrix = run_kill_matrix(CLIMATE_RELATIONS, [mutant], CLIMATE_BASELINE)
    assert matrix.is_killed(mutant) is False
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_comfort_climate.py -v`
Erwartung: FAIL mit `ImportError: cannot import name 'CLIMATE_BASELINE'`

- [ ] **Step 3: Implementieren**

An `src/ai_act_toolkit/suts/comfort_climate.py` anhängen (Import um `Mutant` erweitern):

```python
from ai_act_toolkit.metamorphic.mutation import Mutant

CLIMATE_BASELINE = dict(
    outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
)

CABIN_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Kabinen-Monotonie",
    description=(
        "Steigt die Innentemperatur bei sonst gleichen Bedingungen, muss die "
        "Ziel-Kühlintensität echt steigen — bleibt sie gleich, ignoriert das "
        "System die Kabinentemperatur."
    ),
    transform=lambda inputs: {**inputs, "cabin_temp_c": inputs["cabin_temp_c"] + 5.0},
    check=lambda source_output, followup_output: followup_output > source_output,
    evidence_for="Art. 15",
)

CLIMATE_SATURATION_RELATION = MetamorphicRelation(
    name="Sättigungsgrenze",
    description=(
        "Auch bei extremen Eingaben muss die Kühlintensität im gültigen "
        "Wertebereich 0 bis 100 bleiben."
    ),
    transform=lambda inputs: {
        **inputs,
        "outside_temp_c": 90.0,
        "cabin_temp_c": 90.0,
        "occupant_count": 9,
    },
    check=lambda source_output, followup_output: 0.0 <= followup_output <= 100.0,
    evidence_for="Art. 15",
)

CLIMATE_RELATIONS = (
    TEMPERATURE_MONOTONICITY_RELATION,
    CABIN_MONOTONICITY_RELATION,
    CLIMATE_SATURATION_RELATION,
)


def _sign_flip(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    cabin_factor = max(0.0, cabin_temp_c - desired_temp_c) * 3.0
    occupant_factor = occupant_count * 1.5
    # Fehler: die Außentemperatur geht abkühlend statt aufheizend ein.
    intensity = base - outside_factor + cabin_factor + occupant_factor
    return max(0.0, min(100.0, intensity))


def _cabin_ignored(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    occupant_factor = occupant_count * 1.5
    # Fehler: die Kabinentemperatur wird gar nicht berücksichtigt.
    intensity = base + outside_factor + occupant_factor
    return max(0.0, min(100.0, intensity))


def _clip_missing(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    base = 20.0
    outside_factor = max(0.0, outside_temp_c - desired_temp_c) * 2.5
    cabin_factor = max(0.0, cabin_temp_c - desired_temp_c) * 3.0
    occupant_factor = occupant_count * 1.5
    # Fehler: der Wertebereich wird nicht begrenzt.
    return base + outside_factor + cabin_factor + occupant_factor


def _rounded(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
    # Fehler: Ergebnis wird auf ganze Prozentpunkte gerundet. Verletzt keine
    # der Relationen — bekannte Blindstelle der Suite.
    return float(
        round(
            decide_cooling_intensity(
                outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count
            )
        )
    )


CLIMATE_MUTANTS = (
    Mutant(
        key="vorzeichen_aussen",
        label="Vorzeichenfehler Außentemperatur",
        defect="Höhere Außentemperatur senkt die Kühlintensität statt sie zu erhöhen.",
        fn=_sign_flip,
    ),
    Mutant(
        key="kabine_ignoriert",
        label="Kabinentemperatur ignoriert",
        defect="Die Innentemperatur geht gar nicht in die Berechnung ein.",
        fn=_cabin_ignored,
    ),
    Mutant(
        key="clip_fehlt",
        label="Wertebereich nicht begrenzt",
        defect="Das Ergebnis kann über 100 hinauslaufen.",
        fn=_clip_missing,
    ),
    Mutant(
        key="rundung",
        label="Rundung auf ganze Prozentpunkte",
        defect="Ergebnis wird gerundet — von keiner Relation erkannt.",
        fn=_rounded,
        expected_survivor=True,
    ),
)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_comfort_climate.py -v`
Erwartung: 5 passed (1 Suite-Test + 3 getötete Mutanten + 1 Überlebender)

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/suts/comfort_climate.py tests/test_sut_comfort_climate.py
git commit -m "feat: Klimasteuerung mit drei Relationen und vier Mutanten"
```

---

### Task 6: Sitzverstellung — die SUT, die zur Einstufung passt

Behebt die inhaltliche Schieflage: das Komfortsystem ist Hochrisiko wegen Art. 6(1) (Sitzgeometrie/Rückhaltesystem), getestet wurde bisher aber die Kühlintensität.

**Files:**
- Create: `src/ai_act_toolkit/suts/comfort_seat.py`
- Test: `tests/test_sut_comfort_seat.py`

**Interfaces:**
- Produces: `decide_seat_recline_angle(occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count) -> float`, `SEAT_RELATIONS`, `SEAT_MUTANTS`, `SEAT_BASELINE`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_sut_comfort_seat.py`:

```python
import pytest

from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts.comfort_seat import (
    SEAT_BASELINE,
    SEAT_MUTANTS,
    SEAT_RELATIONS,
    decide_seat_recline_angle,
)


def test_angle_stays_within_physical_limits():
    angle = decide_seat_recline_angle(
        occupant_height_cm=400.0, occupant_weight_kg=200.0,
        vehicle_speed_kmh=0.0, occupant_count=9,
    )
    assert 0.0 <= angle <= 45.0


def test_higher_speed_never_increases_recline():
    slow = decide_seat_recline_angle(**SEAT_BASELINE)
    fast = decide_seat_recline_angle(**{**SEAT_BASELINE, "vehicle_speed_kmh": 200.0})
    assert fast <= slow


def test_correct_sut_passes_every_relation():
    result = run_suite(decide_seat_recline_angle, SEAT_RELATIONS, SEAT_BASELINE)
    assert result.passed is True, [r.relation.name for r in result.results if not r.passed]


@pytest.mark.parametrize(
    "mutant", [m for m in SEAT_MUTANTS if not m.expected_survivor], ids=lambda m: m.key
)
def test_every_declared_defect_is_killed(mutant):
    matrix = run_kill_matrix(SEAT_RELATIONS, [mutant], SEAT_BASELINE)
    assert matrix.is_killed(mutant) is True


@pytest.mark.parametrize(
    "mutant", [m for m in SEAT_MUTANTS if m.expected_survivor], ids=lambda m: m.key
)
def test_declared_survivors_really_survive(mutant):
    matrix = run_kill_matrix(SEAT_RELATIONS, [mutant], SEAT_BASELINE)
    assert matrix.is_killed(mutant) is False
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_comfort_seat.py -v`
Erwartung: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.suts.comfort_seat'`

- [ ] **Step 3: Implementieren**

`src/ai_act_toolkit/suts/comfort_seat.py`:

```python
"""Toy-'System unter Test': automatische Sitzverstellung.

Diese SUT prüft die Eigenschaft, die die Hochrisiko-Einstufung überhaupt
auslöst: die Sitzverstellung greift in die Rückhaltegeometrie ein und
macht das Komfortsystem damit zum Sicherheitsbauteil nach Art. 6(1). Die
zentrale Sicherheitsannahme lautet: je schneller das Fahrzeug fährt, desto
aufrechter muss der Sitz stehen, damit der Gurt korrekt greift.

Kein echtes ML-Modell, ein deterministisches Stellvertreter-Modell.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant

MAX_RECLINE_DEG = 45.0


def decide_seat_recline_angle(
    occupant_height_cm: float,
    occupant_weight_kg: float,
    vehicle_speed_kmh: float,
    occupant_count: int,
) -> float:
    """Berechnet den Ziel-Lehnenwinkel in Grad (0 = aufrecht, 45 = maximal geneigt).

    Das Insassengewicht ist bewusst kein Eingangsfaktor: der Lehnenwinkel
    darf nicht davon abhängen. Die Signatur nimmt es trotzdem entgegen,
    damit eine Relation genau diese Unabhängigkeit prüfen kann.
    """
    base = 30.0
    height_factor = (occupant_height_cm - 170.0) * 0.10
    speed_penalty = vehicle_speed_kmh * 0.15
    occupant_factor = occupant_count * 0.5
    angle = base + height_factor - speed_penalty + occupant_factor
    return max(0.0, min(MAX_RECLINE_DEG, angle))


SEAT_BASELINE = dict(
    occupant_height_cm=175.0,
    occupant_weight_kg=75.0,
    vehicle_speed_kmh=50.0,
    occupant_count=2,
)

SPEED_SAFETY_RELATION = MetamorphicRelation(
    name="Geschwindigkeits-Sicherheitsmonotonie",
    description=(
        "Steigt die Fahrgeschwindigkeit bei sonst gleichen Bedingungen, darf der "
        "Lehnenwinkel nicht größer werden — sonst verschlechtert sich die "
        "Rückhaltegeometrie genau dann, wenn sie am wichtigsten ist."
    ),
    transform=lambda inputs: {
        **inputs,
        "vehicle_speed_kmh": inputs["vehicle_speed_kmh"] + 20.0,
    },
    check=lambda source_output, followup_output: followup_output <= source_output,
    evidence_for="Art. 15",
)

HEIGHT_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Körpergrößen-Monotonie",
    description=(
        "Ein größerer Insasse muss echt mehr Lehnenwinkel bekommen — bleibt der "
        "Winkel gleich, ignoriert das System die Körpergröße."
    ),
    transform=lambda inputs: {
        **inputs,
        "occupant_height_cm": inputs["occupant_height_cm"] + 15.0,
    },
    check=lambda source_output, followup_output: followup_output > source_output,
    evidence_for="Art. 15",
)

WEIGHT_INDEPENDENCE_RELATION = MetamorphicRelation(
    name="Gewichtsunabhängigkeit",
    description=(
        "Das Insassengewicht darf den Lehnenwinkel nicht beeinflussen. Tut es das "
        "doch, ist ein sachfremdes Merkmal in die Entscheidung geraten."
    ),
    transform=lambda inputs: {
        **inputs,
        "occupant_weight_kg": inputs["occupant_weight_kg"] + 25.0,
    },
    check=lambda source_output, followup_output: followup_output == source_output,
    evidence_for="Art. 15",
)

SEAT_SATURATION_RELATION = MetamorphicRelation(
    name="Sättigungsgrenze",
    description=(
        "Auch bei extremen Eingaben muss der Lehnenwinkel im mechanisch "
        "zulässigen Bereich 0 bis 45 Grad bleiben."
    ),
    transform=lambda inputs: {
        **inputs,
        "occupant_height_cm": 400.0,
        "vehicle_speed_kmh": 0.0,
        "occupant_count": 9,
    },
    check=lambda source_output, followup_output: 0.0 <= followup_output <= MAX_RECLINE_DEG,
    evidence_for="Art. 15",
)

SEAT_RELATIONS = (
    SPEED_SAFETY_RELATION,
    HEIGHT_MONOTONICITY_RELATION,
    WEIGHT_INDEPENDENCE_RELATION,
    SEAT_SATURATION_RELATION,
)


def _speed_sign_flip(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    base = 30.0
    height_factor = (occupant_height_cm - 170.0) * 0.10
    occupant_factor = occupant_count * 0.5
    # Fehler: höhere Geschwindigkeit neigt den Sitz weiter zurück.
    angle = base + height_factor + vehicle_speed_kmh * 0.15 + occupant_factor
    return max(0.0, min(MAX_RECLINE_DEG, angle))


def _height_ignored(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    base = 30.0
    occupant_factor = occupant_count * 0.5
    # Fehler: die Körpergröße geht gar nicht ein.
    angle = base - vehicle_speed_kmh * 0.15 + occupant_factor
    return max(0.0, min(MAX_RECLINE_DEG, angle))


def _weight_leaks(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    # Fehler: das Gewicht beeinflusst den Winkel, obwohl es das nicht darf.
    angle = (
        decide_seat_recline_angle(
            occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
        )
        + (occupant_weight_kg - 75.0) * 0.05
    )
    return max(0.0, min(MAX_RECLINE_DEG, angle))


def _clip_missing(
    occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
):
    base = 30.0
    height_factor = (occupant_height_cm - 170.0) * 0.10
    occupant_factor = occupant_count * 0.5
    # Fehler: der mechanische Endanschlag wird nicht abgebildet.
    return base + height_factor - vehicle_speed_kmh * 0.15 + occupant_factor


def _rounded(occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count):
    # Fehler: Winkel wird auf ganze Grad gerundet. Verletzt keine der vier
    # Relationen — bekannte Blindstelle der Suite.
    return float(
        round(
            decide_seat_recline_angle(
                occupant_height_cm, occupant_weight_kg, vehicle_speed_kmh, occupant_count
            )
        )
    )


SEAT_MUTANTS = (
    Mutant(
        key="vorzeichen_geschwindigkeit",
        label="Vorzeichenfehler Geschwindigkeit",
        defect="Höhere Geschwindigkeit neigt den Sitz weiter zurück statt aufzurichten.",
        fn=_speed_sign_flip,
    ),
    Mutant(
        key="hoehe_ignoriert",
        label="Körpergröße ignoriert",
        defect="Die Körpergröße geht nicht in den Lehnenwinkel ein.",
        fn=_height_ignored,
    ),
    Mutant(
        key="gewicht_leckt",
        label="Gewicht beeinflusst den Winkel",
        defect="Ein sachfremdes Merkmal ist in die Entscheidung geraten.",
        fn=_weight_leaks,
    ),
    Mutant(
        key="clip_fehlt",
        label="Endanschlag fehlt",
        defect="Der Winkel kann über 45 Grad hinauslaufen.",
        fn=_clip_missing,
    ),
    Mutant(
        key="rundung",
        label="Rundung auf ganze Grad",
        defect="Winkel wird gerundet — von keiner Relation erkannt.",
        fn=_rounded,
        expected_survivor=True,
    ),
)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_comfort_seat.py -v`
Erwartung: 8 passed (2 Direkttests + 1 Suite + 4 getötete + 1 Überlebender)

Prüfe bei einem Fehlschlag zuerst die Zahlen am Baseline-Punkt: `30 + 0.5 − 7.5 + 1 = 24.0`, nach `+15 cm` → `25.5`, nach `+20 km/h` → `21.0`.

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/suts/comfort_seat.py tests/test_sut_comfort_seat.py
git commit -m "feat: Sitzverstellung als sicherheitsrelevante SUT zu Art. 6(1)"
```

---

### Task 7: Bewerber-Scoring — das Herzstück

Der Beweismoment: Name getauscht, Score gefallen.

**Files:**
- Create: `src/ai_act_toolkit/suts/recruiting_scorer.py`
- Test: `tests/test_sut_recruiting.py`

**Interfaces:**
- Produces: `score_applicant_fixed(first_name, years_experience, skill_match, education_level) -> float`, `score_applicant_naive(...)` mit identischer Signatur, `RECRUITING_RELATIONS`, `RECRUITING_MUTANTS`, `RECRUITING_BASELINE`, `NAME_INVARIANCE_RELATION`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_sut_recruiting.py`:

```python
import pytest

from ai_act_toolkit.metamorphic.core import run_relation
from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts.recruiting_scorer import (
    NAME_INVARIANCE_RELATION,
    RECRUITING_BASELINE,
    RECRUITING_MUTANTS,
    RECRUITING_RELATIONS,
    score_applicant_fixed,
    score_applicant_naive,
)


def test_naive_scorer_violates_name_invariance():
    result = run_relation(
        score_applicant_naive, NAME_INVARIANCE_RELATION, RECRUITING_BASELINE
    )
    assert result.passed is False
    assert result.followup_output < result.source_output


def test_fixed_scorer_holds_name_invariance():
    result = run_relation(
        score_applicant_fixed, NAME_INVARIANCE_RELATION, RECRUITING_BASELINE
    )
    assert result.passed is True
    assert result.followup_output == result.source_output


def test_name_invariance_supports_article_10():
    assert NAME_INVARIANCE_RELATION.evidence_for == "Art. 10"


def test_correct_sut_passes_every_relation():
    result = run_suite(score_applicant_fixed, RECRUITING_RELATIONS, RECRUITING_BASELINE)
    assert result.passed is True, [r.relation.name for r in result.results if not r.passed]


@pytest.mark.parametrize(
    "mutant",
    [m for m in RECRUITING_MUTANTS if not m.expected_survivor],
    ids=lambda m: m.key,
)
def test_every_declared_defect_is_killed(mutant):
    matrix = run_kill_matrix(RECRUITING_RELATIONS, [mutant], RECRUITING_BASELINE)
    assert matrix.is_killed(mutant) is True


@pytest.mark.parametrize(
    "mutant", [m for m in RECRUITING_MUTANTS if m.expected_survivor], ids=lambda m: m.key
)
def test_declared_survivors_really_survive(mutant):
    matrix = run_kill_matrix(RECRUITING_RELATIONS, [mutant], RECRUITING_BASELINE)
    assert matrix.is_killed(mutant) is False
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_recruiting.py -v`
Erwartung: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.suts.recruiting_scorer'`

- [ ] **Step 3: Implementieren**

`src/ai_act_toolkit/suts/recruiting_scorer.py`:

```python
"""Toy-'System unter Test': Vorauswahl-Scoring für Bewerbungen.

Warum es hier zwei Varianten gibt: `score_applicant_naive` ist ein
absichtlich fehlerhaftes Demonstrationsobjekt. Es enthält ein aus dem
Vornamen abgeleitetes Merkmal — den Fehler, den die metamorphe Relation
fangen soll. In echten Systemen kommt so etwas selten so offen herein,
sondern über korrelierte Proxys (Postleitzahl, Vereinsmitgliedschaft,
Schulname). Hier steht es explizit im Code, damit man den Mechanismus
lesen kann. `score_applicant_fixed` ist die korrigierte Variante.

Die Relation "Namensinvarianz" zahlt auf Art. 10(2)(f)(g) ein: die
Untersuchung des Systems auf mögliche Verzerrungen.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant

# Sachfremdes Merkmal: eine nach Vornamen vergebene "Passung", wie sie in
# fehlerhaften Systemen als Proxy für soziale Herkunft entsteht.
_NAME_BONUS: dict[str, float] = {
    "maximilian": 6.0,
    "charlotte": 6.0,
    "friederike": 6.0,
    "kevin": -6.0,
    "chantal": -6.0,
    "justin": -6.0,
}


def score_applicant_fixed(
    first_name: str,
    years_experience: float,
    skill_match: float,
    education_level: int,
) -> float:
    """Bewertet eine Bewerbung mit 0 bis 100 Punkten, ohne den Namen zu verwenden.

    Der Vorname steht trotzdem in der Signatur, damit die Namensinvarianz-
    Relation ihn variieren kann.
    """
    score = 10.0 + years_experience * 3.0 + skill_match * 50.0 + education_level * 5.0
    return max(0.0, min(100.0, score))


def score_applicant_naive(
    first_name: str,
    years_experience: float,
    skill_match: float,
    education_level: int,
) -> float:
    """Fehlerhafte Variante: rechnet einen vom Vornamen abgeleiteten Bonus mit ein."""
    base = 10.0 + years_experience * 3.0 + skill_match * 50.0 + education_level * 5.0
    base += _NAME_BONUS.get(first_name.lower(), 0.0)
    return max(0.0, min(100.0, base))


RECRUITING_BASELINE = dict(
    first_name="Maximilian",
    years_experience=5.0,
    skill_match=0.8,
    education_level=3,
)

NAME_INVARIANCE_RELATION = MetamorphicRelation(
    name="Namensinvarianz",
    description=(
        "Wird im Bewerbungsprofil ausschließlich der Vorname ausgetauscht und sonst "
        "nichts verändert, muss der Score exakt gleich bleiben. Ändert er sich, "
        "entscheidet das System nach einem sachfremden Merkmal."
    ),
    transform=lambda inputs: {**inputs, "first_name": "Kevin"},
    check=lambda source_output, followup_output: followup_output == source_output,
    evidence_for="Art. 10",
)

EXPERIENCE_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Berufsjahre-Monotonie",
    description=(
        "Mehr einschlägige Berufsjahre bei sonst gleichem Profil müssen den Score "
        "echt erhöhen."
    ),
    transform=lambda inputs: {
        **inputs,
        "years_experience": inputs["years_experience"] + 2.0,
    },
    check=lambda source_output, followup_output: followup_output > source_output,
    evidence_for="Art. 15",
)

SKILL_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Skill-Monotonie",
    description=(
        "Eine bessere Passung der Qualifikationen darf den Score nicht senken."
    ),
    transform=lambda inputs: {**inputs, "skill_match": inputs["skill_match"] + 0.1},
    check=lambda source_output, followup_output: followup_output >= source_output,
    evidence_for="Art. 15",
)

RECRUITING_SATURATION_RELATION = MetamorphicRelation(
    name="Sättigungsgrenze",
    description="Auch bei extremen Profilen muss der Score zwischen 0 und 100 liegen.",
    transform=lambda inputs: {
        **inputs,
        "years_experience": 60.0,
        "skill_match": 1.0,
        "education_level": 9,
    },
    check=lambda source_output, followup_output: 0.0 <= followup_output <= 100.0,
    evidence_for="Art. 15",
)

RECRUITING_RELATIONS = (
    NAME_INVARIANCE_RELATION,
    EXPERIENCE_MONOTONICITY_RELATION,
    SKILL_MONOTONICITY_RELATION,
    RECRUITING_SATURATION_RELATION,
)


def _experience_ignored(first_name, years_experience, skill_match, education_level):
    # Fehler: Berufserfahrung fließt nicht ein.
    score = 10.0 + skill_match * 50.0 + education_level * 5.0
    return max(0.0, min(100.0, score))


def _skill_sign_flip(first_name, years_experience, skill_match, education_level):
    # Fehler: bessere Passung senkt den Score.
    score = 10.0 + years_experience * 3.0 - skill_match * 50.0 + education_level * 5.0
    return max(0.0, min(100.0, score))


def _clip_missing(first_name, years_experience, skill_match, education_level):
    # Fehler: der Wertebereich wird nicht begrenzt.
    return 10.0 + years_experience * 3.0 + skill_match * 50.0 + education_level * 5.0


def _rounded(first_name, years_experience, skill_match, education_level):
    # Fehler: Score wird auf ganze Punkte gerundet. Verletzt keine der vier
    # Relationen — bekannte Blindstelle der Suite.
    return float(
        round(
            score_applicant_fixed(
                first_name, years_experience, skill_match, education_level
            )
        )
    )


RECRUITING_MUTANTS = (
    Mutant(
        key="namensmerkmal",
        label="Vom Vornamen abgeleitetes Merkmal",
        defect="Der Score hängt am Vornamen — ein sachfremdes, diskriminierendes Merkmal.",
        fn=score_applicant_naive,
    ),
    Mutant(
        key="erfahrung_ignoriert",
        label="Berufserfahrung ignoriert",
        defect="Berufsjahre gehen nicht in den Score ein.",
        fn=_experience_ignored,
    ),
    Mutant(
        key="vorzeichen_skill",
        label="Vorzeichenfehler Qualifikationspassung",
        defect="Eine bessere Passung senkt den Score.",
        fn=_skill_sign_flip,
    ),
    Mutant(
        key="clip_fehlt",
        label="Wertebereich nicht begrenzt",
        defect="Der Score kann über 100 hinauslaufen.",
        fn=_clip_missing,
    ),
    Mutant(
        key="rundung",
        label="Rundung auf ganze Punkte",
        defect="Score wird gerundet — von keiner Relation erkannt.",
        fn=_rounded,
        expected_survivor=True,
    ),
)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_recruiting.py -v`
Erwartung: 9 passed

Kontrollrechnung für den Beweismoment: Basis `10 + 15 + 40 + 15 = 80`, mit `+6` für „Maximilian" → `86`, mit `−6` für „Kevin" → `74`. Differenz **12 Punkte**.

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/suts/recruiting_scorer.py tests/test_sut_recruiting.py
git commit -m "feat: Bewerber-Scoring mit Namensinvarianz-Relation als Bias-Nachweis"
```

---

### Task 8: SUT-Registry, `use_cases.py` entkoppeln

**Files:**
- Modify: `src/ai_act_toolkit/suts/__init__.py`
- Modify: `src/ai_act_toolkit/use_cases.py` (Feld `has_metamorphic_demo` entfernen)
- Modify: `tests/test_use_cases.py:9-24`
- Test: `tests/test_sut_registry.py`

**Interfaces:**
- Consumes: `SEAT_*`, `CLIMATE_*`, `RECRUITING_*` aus den drei SUT-Modulen
- Produces: `SUTSpec(key, label, description, fn, baseline_inputs, relations, mutants)`, `SUT_REGISTRY: dict[str, tuple[SUTSpec, ...]]`, `suts_for(use_case_key: str) -> tuple[SUTSpec, ...]`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_sut_registry.py`:

```python
import pytest

from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.suts import SUT_REGISTRY, suts_for
from ai_act_toolkit.use_cases import ALL_USE_CASES

ALL_SUTS = [spec for specs in SUT_REGISTRY.values() for spec in specs]


def test_every_use_case_has_a_registry_entry():
    assert set(SUT_REGISTRY) == {uc.key for uc in ALL_USE_CASES}


def test_comfort_system_has_seat_and_climate():
    assert [s.key for s in suts_for("comfort_system")] == ["seat", "climate"]


def test_recruiting_has_the_scoring_sut():
    assert [s.key for s in suts_for("recruiting")] == ["scoring"]


def test_chatbot_has_no_sut():
    assert suts_for("chatbot") == ()


def test_unknown_use_case_yields_no_sut():
    assert suts_for("gibt-es-nicht") == ()


@pytest.mark.parametrize("spec", ALL_SUTS, ids=lambda s: s.key)
def test_every_registered_sut_passes_its_own_suite(spec):
    # Eine Relation, die auf korrektem Code feuert, ist selbst kaputt.
    result = run_suite(spec.fn, spec.relations, spec.baseline_inputs)
    assert result.passed is True, [r.relation.name for r in result.results if not r.passed]


@pytest.mark.parametrize("spec", ALL_SUTS, ids=lambda s: s.key)
def test_every_registered_sut_declares_at_least_one_mutant(spec):
    assert len(spec.mutants) >= 1
```

Zusätzlich `tests/test_use_cases.py` ab Zeile 9 ersetzen:

```python
def test_comfort_system_classifies_as_high_risk():
    assert classify(COMFORT_SYSTEM.attributes).risk_class == RiskClass.HIGH_RISK


def test_recruiting_classifies_as_high_risk():
    assert classify(RECRUITING.attributes).risk_class == RiskClass.HIGH_RISK


def test_chatbot_classifies_as_limited_risk():
    assert classify(CHATBOT.attributes).risk_class == RiskClass.LIMITED_RISK
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_sut_registry.py -v`
Erwartung: FAIL mit `ImportError: cannot import name 'SUT_REGISTRY'`

- [ ] **Step 3: Registry implementieren**

`src/ai_act_toolkit/suts/__init__.py`:

```python
"""Systeme unter Test, gegen die die metamorphen Relationen laufen.

Die Registry ordnet jedem Use Case seine SUTs zu. Sie ersetzt das frühere
Flag `UseCase.has_metamorphic_demo`: ob ein Nachweis möglich ist, ergibt
sich jetzt daraus, ob überhaupt eine SUT hinterlegt ist. `use_cases.py`
kennt die SUTs dadurch nicht mehr und bleibt reine Falldaten.
"""

from dataclasses import dataclass
from typing import Callable

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant
from ai_act_toolkit.suts.comfort_climate import (
    CLIMATE_BASELINE,
    CLIMATE_MUTANTS,
    CLIMATE_RELATIONS,
    decide_cooling_intensity,
)
from ai_act_toolkit.suts.comfort_seat import (
    SEAT_BASELINE,
    SEAT_MUTANTS,
    SEAT_RELATIONS,
    decide_seat_recline_angle,
)
from ai_act_toolkit.suts.recruiting_scorer import (
    RECRUITING_BASELINE,
    RECRUITING_MUTANTS,
    RECRUITING_RELATIONS,
    score_applicant_fixed,
)


@dataclass(frozen=True)
class SUTSpec:
    key: str
    label: str
    description: str
    fn: Callable[..., float]
    baseline_inputs: dict
    relations: tuple[MetamorphicRelation, ...]
    mutants: tuple[Mutant, ...]


SEAT_SUT = SUTSpec(
    key="seat",
    label="Automatische Sitzverstellung",
    description=(
        "Die Funktion, die die Hochrisiko-Einstufung nach Art. 6(1) überhaupt "
        "auslöst: sie greift in die Rückhaltegeometrie ein."
    ),
    fn=decide_seat_recline_angle,
    baseline_inputs=SEAT_BASELINE,
    relations=SEAT_RELATIONS,
    mutants=SEAT_MUTANTS,
)

CLIMATE_SUT = SUTSpec(
    key="climate",
    label="Klimasteuerung",
    description="Die Komfortfunktion des Systems, ohne Sicherheitsrelevanz.",
    fn=decide_cooling_intensity,
    baseline_inputs=CLIMATE_BASELINE,
    relations=CLIMATE_RELATIONS,
    mutants=CLIMATE_MUTANTS,
)

SCORING_SUT = SUTSpec(
    key="scoring",
    label="Vorauswahl-Scoring",
    description=(
        "Bewertet Bewerbungen mit 0 bis 100 Punkten. Die Namensinvarianz-Relation "
        "prüft, ob ein sachfremdes Merkmal in die Entscheidung eingeht."
    ),
    fn=score_applicant_fixed,
    baseline_inputs=RECRUITING_BASELINE,
    relations=RECRUITING_RELATIONS,
    mutants=RECRUITING_MUTANTS,
)

SUT_REGISTRY: dict[str, tuple[SUTSpec, ...]] = {
    "comfort_system": (SEAT_SUT, CLIMATE_SUT),
    "recruiting": (SCORING_SUT,),
    "chatbot": (),
}


def suts_for(use_case_key: str) -> tuple[SUTSpec, ...]:
    """Liefert die SUTs eines Use Case, oder ein leeres Tupel."""
    return SUT_REGISTRY.get(use_case_key, ())
```

- [ ] **Step 4: `use_cases.py` entkoppeln**

Feld `has_metamorphic_demo: bool` aus der Dataclass `UseCase` entfernen und die drei Argumente `has_metamorphic_demo=...` aus `COMFORT_SYSTEM`, `RECRUITING`, `CHATBOT` streichen. Docstring des Moduls um einen Satz ergänzen:

```python
"""Drei fest hinterlegte Beispiel-Use-Cases für die Demo.

Bewusst kein Freitext-Import (siehe Design-Spec, "Bewusst weggelassen"),
jeder Use Case hat vordefinierte, im Fragebogen der App editierbare
Annex-III-Attribute. Welche Systeme unter Test zu einem Use Case gehören,
steht in `suts/__init__.py` — dieses Modul bleibt reine Falldaten.
"""
```

- [ ] **Step 5: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Erwartung: alle grün, insgesamt 65 passed

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: SUT-Registry statt has_metamorphic_demo am Use Case"
```

---

### Task 9: Governance-Artefakt aus Pflichten und Evidenz

Der geschlossene Kreis. Bis hierher existieren Pflichten und Nachweise nebeneinander.

**Files:**
- Modify: `src/ai_act_toolkit/governance.py` (vollständig ersetzen)
- Modify: `tests/test_governance.py` (vollständig ersetzen)

**Interfaces:**
- Consumes: `Obligation`, `EvidenceKind`, `obligations_for` aus `obligations.py`; `SuiteResult` aus `metamorphic.suite`; `KillMatrix` aus `metamorphic.mutation`; `SUTSpec` aus `suts`
- Produces: `EvidenceBundle(entries: tuple[EvidenceEntry, ...])` mit `.articles_covered() -> set[str]`, `EvidenceEntry(sut_label, suite_result, kill_matrix)`, `render_kill_matrix(kill_matrix) -> str`, `generate_governance_artifact(use_case, classification, rationale, obligations, evidence) -> str`

- [ ] **Step 1: Failing Test schreiben**

`tests/test_governance.py` vollständig ersetzen:

```python
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
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_governance.py -v`
Erwartung: FAIL mit `ImportError: cannot import name 'EvidenceBundle'`

- [ ] **Step 3: Implementieren**

`src/ai_act_toolkit/governance.py` vollständig ersetzen:

```python
"""Erzeugt das Governance-Artefakt: Risk Assessment plus Konformitätscheckliste.

Der Unterschied zur früheren Fassung: die Checkliste ist keine Konstante
mehr. Jede Pflicht wird in einem von drei Zuständen gerendert —

    [x]  belegt: eine metamorphe Relation, die auf diesen Artikel einzahlt,
         wurde ausgeführt und bestanden
    [~]  teilweise: dieses Artefakt selbst ist ein Beitrag zur Pflicht
         (Annex IV 2(g): dokumentiertes Testverfahren)
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
        """Artikel, für die mindestens eine Relation lief und bestand."""
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
            parts.append(f"{entry.sut_label}: {names} bestanden, Mutation Score {killed}/{total}")
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
        [header, divider, *rows, "", f"**Mutation Score: {killed}/{total}**",
         f"Überlebende Mutanten (bekannte Blindstellen der Relationsmenge): {survivors}"]
    )


_STATUS_NOTE = {
    EvidenceKind.PROCESS: "Prozesspflicht, durch dieses Werkzeug nicht belegbar.",
    EvidenceKind.DOCUMENTATION: (
        "teilweise: dieses Artefakt dokumentiert das verwendete Testverfahren "
        "(Annex IV Nr. 2(g))."
    ),
}


def _render_obligation(obligation: Obligation, evidence: EvidenceBundle | None) -> str:
    if obligation.evidence_kind is EvidenceKind.TECHNICAL_TEST:
        if evidence is not None and obligation.article in evidence.articles_covered():
            return (
                f"- [x] **{obligation.article}** {obligation.title} — belegt: "
                f"{evidence.summary_for(obligation.article)}"
            )
        return (
            f"- [ ] **{obligation.article}** {obligation.title} — offen: kein "
            f"Nachweis ausgeführt."
        )
    if obligation.evidence_kind is EvidenceKind.DOCUMENTATION and evidence is not None:
        return (
            f"- [~] **{obligation.article}** {obligation.title} — "
            f"{_STATUS_NOTE[EvidenceKind.DOCUMENTATION]}"
        )
    if obligation.evidence_kind is EvidenceKind.DOCUMENTATION:
        return (
            f"- [ ] **{obligation.article}** {obligation.title} — offen: kein "
            f"Testverfahren dokumentiert."
        )
    return (
        f"- [ ] **{obligation.article}** {obligation.title} — "
        f"{_STATUS_NOTE[EvidenceKind.PROCESS]}"
    )


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
                    f"- **{result.relation.name}** ({result.relation.evidence_for}): {status}",
                    f"  - {result.relation.description}",
                    f"  - Quellfall {result.source_inputs} → {result.source_output:.2f}",
                    f"  - Folgefall {result.followup_inputs} → {result.followup_output:.2f}",
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
```

- [ ] **Step 4: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_governance.py -v`
Erwartung: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/governance.py tests/test_governance.py
git commit -m "feat: Governance-Artefakt hakt Pflichten anhand echter Evidenz ab"
```

---

### Task 10: App auf vier Schritte umbauen

**Files:**
- Modify: `app.py` (Abschnitte ab Zeile 119 ersetzen, Importblock erweitern)
- Test: `tests/test_app_flow.py`

**Interfaces:**
- Consumes: alles aus den Tasks 2 bis 9

- [ ] **Step 1: Failing Test schreiben**

`tests/test_app_flow.py`:

```python
from streamlit.testing.v1 import AppTest


def _run():
    app = AppTest.from_file("app.py", default_timeout=30)
    app.run()
    return app


def test_app_starts_without_exception():
    app = _run()
    assert not app.exception


def test_high_risk_case_shows_all_four_steps():
    app = _run()
    headers = [h.value for h in app.subheader]
    assert any("Einstufung" in h for h in headers)
    assert any("Pflichten" in h for h in headers)
    assert any("Nachweis" in h for h in headers)
    assert any("Artefakt" in h for h in headers)


def test_fault_injection_selectbox_is_present_for_high_risk():
    app = _run()
    labels = [s.label for s in app.selectbox]
    assert any("Fehler injizieren" in label for label in labels)
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_app_flow.py -v`
Erwartung: FAIL — die Subheader „Pflichten"/„Nachweis" und das Selectbox existieren noch nicht

- [ ] **Step 3: Importblock in `app.py` erweitern**

```python
from ai_act_toolkit.governance import (
    EvidenceBundle,
    EvidenceEntry,
    generate_governance_artifact,
    render_kill_matrix,
)
from ai_act_toolkit.metamorphic.mutation import run_kill_matrix
from ai_act_toolkit.metamorphic.suite import run_suite
from ai_act_toolkit.obligations import EvidenceKind, obligations_for
from ai_act_toolkit.suts import suts_for
```

Die bisherigen Importe von `TEMPERATURE_MONOTONICITY_RELATION`, `decide_cooling_intensity` und `run_relation` entfallen.

- [ ] **Step 4: State-Pruning ergänzen**

Direkt nach der Ermittlung von `use_case` einfügen:

```python
def _prune_rationales(active_prefix: str) -> None:
    """Verwirft LLM-Begründungen, die zu einem anderen Use Case gehören.

    Ohne das sammelt der session_state pro (Use Case, Klasse, Regel)-
    Kombination einen Key an und wird ihn nie wieder los — das in
    HANDOVER.md geparkte Minor-Finding.
    """
    stale = [
        key
        for key in st.session_state
        if key.startswith("rationale::") and not key.startswith(active_prefix)
    ]
    for key in stale:
        del st.session_state[key]


_prune_rationales(f"rationale::{use_case.key}::")
```

- [ ] **Step 5: Die vier Schritte implementieren**

Alles ab dem heutigen `classification = classify(attrs)` bis einschließlich des Governance-Blocks ersetzen:

```python
st.subheader("1. Einstufung")
classification = classify(attrs)
label, display_fn = RISK_DISPLAY[classification.risk_class]
display_fn(f"**{label}**, Regel: {classification.matched_rule}")

rationale_key = (
    f"rationale::{use_case.key}::{classification.risk_class.value}::{classification.matched_rule}"
)

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

obligations = obligations_for(classification)

st.subheader("2. Pflichten")
if not obligations:
    st.info("Aus dieser Einstufung folgen keine besonderen Pflichten.")
else:
    st.markdown(
        "Diese Pflichten folgen aus der Einstufung. Belegbar sind nur die, "
        "für die es einen ausführbaren technischen Nachweis gibt:"
    )
    for obligation in obligations:
        marker = {
            EvidenceKind.TECHNICAL_TEST: "🧪 technisch nachweisbar",
            EvidenceKind.DOCUMENTATION: "📄 teilweise über die Dokumentation",
            EvidenceKind.PROCESS: "🏢 Prozesspflicht",
        }[obligation.evidence_kind]
        st.markdown(f"- **{obligation.article}** {obligation.title} — {marker}")

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
                    f"- Quellfall: `{result.source_inputs}` → **{result.source_output:.2f}**"
                )
                st.markdown(
                    f"- Folgefall: `{result.followup_inputs}` → **{result.followup_output:.2f}**"
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
```

- [ ] **Step 6: „Unter der Haube"-Text nachziehen**

Im `with under_the_hood():`-Block den Schlusssatz ersetzen:

```python
    st.markdown(
        "Das LLM formuliert ausschließlich die Begründung in Prosa und kann die "
        "Klasse nicht mehr verändern. Der Nachweis in Schritt 3 läuft vollständig "
        "ohne LLM: Relationen und Mutanten sind Code, keine Sprachausgabe."
    )
```

Und in `portfolio_footer(...)` die Caveats aktualisieren:

```python
    caveats=[
        "keine rechtsverbindliche Compliance-Aussage",
        "drei hinterlegte Use Cases, kein Freitext-Import",
        "belegt 2 von 7 Hochrisiko-Pflichten technisch, der Rest sind Prozesspflichten",
        "Free-Tier-Hosting, der erste Aufruf kann einen Kaltstart haben",
    ],
```

- [ ] **Step 7: Tests laufen lassen**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Erwartung: alle grün, insgesamt 74 passed

- [ ] **Step 8: Manuell im Browser prüfen**

```bash
.venv/Scripts/python.exe -m streamlit run app.py
```

Prüfen: Use Case „KI-gestützte Bewerber-Vorauswahl" wählen, in Schritt 3 den Fehler „Vom Vornamen abgeleitetes Merkmal" injizieren. Erwartung: Namensinvarianz kippt auf ❌, Quellfall 86.00, Folgefall 74.00. In Schritt 4 steht Art. 10 dann wieder auf `- [ ]`.

- [ ] **Step 9: Commit**

```bash
git add app.py tests/test_app_flow.py
git commit -m "feat: App fuehrt von der Einstufung ueber Pflichten und Nachweis zum Artefakt"
```

---

### Task 11: CI und Linter

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `pyproject.toml`

- [ ] **Step 1: ruff als Dev-Dependency und Konfiguration ergänzen**

In `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.6",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 2: ruff installieren und lokal laufen lassen**

Run:
```bash
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m ruff check .
```
Erwartung: Fehler werden gemeldet. Mit `--fix` beheben, was automatisch geht, den Rest von Hand. `app.py` braucht wegen der `sys.path`-Manipulation vor den Importen ein `# noqa: E402` an den betroffenen Importzeilen.

- [ ] **Step 3: Workflow anlegen**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Abhängigkeiten installieren
        run: pip install -e ".[dev]"
      - name: Linter
        run: ruff check .
      - name: Tests
        run: pytest tests/ -v
```

- [ ] **Step 4: Alles laufen lassen**

Run:
```bash
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest tests/ -v
```
Erwartung: ruff meldet nichts, 74 Tests grün.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml pyproject.toml
git commit -m "ci: ruff und pytest bei jedem Push, Linter-Konfiguration ergaenzt"
```

---

### Task 12: Doku und Umbenennung

**Files:**
- Modify: `README.md`
- Modify: `docs/index.html`
- Modify: `CLAUDE.md`
- Modify: `HANDOVER.md`
- Modify: `app.py` (Header-Titel und Claim)
- Modify: `../marco-os/data/projects.js` (nur `title`, `summary`, `description`, `stats`)

- [ ] **Step 1: Produktnamen und Claim in der App ändern**

In `app.py`:

```python
page_setup("AI Act Evidence Toolkit")

page_header(
    title="AI Act Evidence Toolkit",
    claim=(
        "Stuft eine KI-Anwendung nach dem EU AI Act ein, leitet daraus die konkreten "
        "Artikelpflichten ab und führt für die technisch belegbaren davon einen "
        "metamorphen Test live aus — die Einstufung selbst trifft ein deterministischer "
        "Regelbaum, nicht das LLM."
    ),
    project_id="ai-act-validation-toolkit",
    cluster="agentic-ai",
)
```

`project_id` bleibt unverändert, sonst brechen die MARCO.OS-Deep-Links.

- [ ] **Step 2: README umschreiben**

Zu ändern:
- H1 auf `# AI Act Evidence Toolkit`, Claim entlang der Kette Pflicht → Nachweis.
- Badge `Tests-17_passing` durch den CI-Badge ersetzen:
  `![CI](https://github.com/maggostang-droid/ai-risk-classifier/actions/workflows/ci.yml/badge.svg)`
- Neuer Abschnitt „Der Beweismoment" vor dem Architektur-Abschnitt:

```markdown
## Der Beweismoment

Wähle in der Demo die Bewerber-Vorauswahl und injiziere in Schritt 3 den Fehler
„Vom Vornamen abgeleitetes Merkmal". Im Bewerbungsprofil ändert sich daraufhin
nichts außer dem Vornamen — der Score fällt trotzdem von 86 auf 74.

Genau das ist metamorphes Testen: geprüft wird nicht eine einzelne Ausgabe gegen
ein bekanntes Sollergebnis (das ist bei KI-Systemen meist unbekannt, das
Orakel-Problem), sondern eine *Beziehung* zwischen zwei Ausgaben. Der Score darf
sich nicht ändern, wenn sich nur der Name ändert. Tut er es doch, ist ein
sachfremdes Merkmal in die Entscheidung geraten — und Art. 10(2)(f)(g) AI Act
verlangt genau diese Untersuchung auf Verzerrungen.

Der naive Scorer in `suts/recruiting_scorer.py` ist ein absichtlich fehlerhaftes
Demonstrationsobjekt, dessen Zweck es ist, vom Test gefangen zu werden — kein
Vorschlag, wie man ein Scoring baut.
```

- Die Use-Case-Tabelle durch die Pflichten-Tabelle ersetzen:

```markdown
## Was belegt werden kann, und was nicht

| Pflicht | Status | Warum |
|---|---|---|
| Art. 10 Daten und Data Governance | technisch belegt | Namensinvarianz-Relation |
| Art. 15 Genauigkeit und Robustheit | technisch belegt | Monotonie-, Invarianz- und Sättigungsrelationen |
| Art. 9 Risikomanagementsystem | teilweise | Art. 9(7): Testen gegen vorab definierte Kriterien |
| Art. 11 Technische Dokumentation | teilweise | Annex IV Nr. 2(g): dokumentiertes Testverfahren |
| Art. 12 Logging | nicht belegbar | Prozesspflicht |
| Art. 13 Betriebsanleitung | nicht belegbar | Prozesspflicht |
| Art. 14 Menschliche Aufsicht | nicht belegbar | Prozesspflicht |
```

- Im Abschnitt „Was dieses Projekt nicht ist" den Satz über fehlende ML-Metriken ersetzen:

```markdown
Klassische ML-Metriken wie F1 gibt es für den Regelbaum nicht und sie wären auch
sinnlos: er ist deterministisch, seine Korrektheit ist eine Frage der
Rechtsauslegung. Für die Relations-Suite gibt es dagegen sehr wohl eine Metrik —
den Mutation Score. Er ist bewusst nicht 100 %: jede SUT hat einen deklarierten
überlebenden Mutanten (Rundung), der die Blindstelle der Relationsmenge zeigt.
Ein Test in der Suite sorgt dafür, dass diese Blindstelle nicht stillschweigend
verschwindet.
```

- [ ] **Step 3: `docs/index.html`, `CLAUDE.md`, `HANDOVER.md` nachziehen**

- `docs/index.html`: Titel und Claim wie in Schritt 1.
- `CLAUDE.md`: Architektur-Abschnitt auf die neue Modulstruktur, „Kein Linter konfiguriert" durch `ruff check .` ersetzen, „Aktueller Stand" auf diesen Umbau.
- `HANDOVER.md`: den Abschnitt „Nicht umgesetzt, aber als sinnvolle Erweiterung im finalen Review vorgeschlagen" streichen — der Break-the-System-Toggle ist mit Task 10 gebaut.

- [ ] **Step 4: MARCO.OS-Projektkarte aktualisieren**

In `../marco-os/data/projects.js`, Eintrag `id: "ai-act-validation-toolkit"`: `title` auf `"AI Act Evidence Toolkit"`, `summary` und `description` auf die Pflicht→Nachweis-Kette, und ein `stats`-Feld ergänzen:

```javascript
stats: [
  { value: "2/7", label: "Pflichten technisch belegt" },
  { value: "11/14", label: "Mutanten getötet" }
],
```

Die Zahl 11/14 ergibt sich aus den drei Kill-Matrizen: Sitzverstellung 4/5,
Klimasteuerung 3/4, Bewerber-Scoring 4/5 — je ein deklarierter Überlebender pro
SUT. Nach dem Testlauf gegenprüfen. `id`, `demoUrl` und `repoUrl` bleiben
unverändert.

- [ ] **Step 5: Alles prüfen**

```bash
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest tests/ -v
cd ../../marco-os && npm test
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "docs: Umbenennung in AI Act Evidence Toolkit, README auf Pflicht-zu-Nachweis"
```

Der `projects.js`-Commit gehört ins `marco-os`-Repo und wird dort separat committet.

---

## Abschluss

Nach Task 12:

```bash
.venv/Scripts/python.exe -m pytest tests/ -v     # 74 passed
.venv/Scripts/python.exe -m ruff check .          # keine Meldung
```

Danach `superpowers:finishing-a-development-branch` für den Merge von
`feature/evidence-toolkit` nach `master` und das Aufräumen des Worktrees.

**Von Marco selbst zu erledigen, nicht durch eine Agenten-Session möglich:**
- Demo-GIF vom Namenstausch aufnehmen und `docs/demo.png` im README ersetzen.
- Nach dem Merge prüfen, ob die Streamlit-Community-Cloud-App den neuen Stand zieht.
