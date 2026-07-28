# ai-act-validation-toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein Streamlit-Tool, das einen KI-Use-Case deterministisch nach EU-AI-Act-Risikoklasse (Annex III) klassifiziert, für den Automotive-Use-Case einen echten metamorphen Test ausführt und für Hochrisiko-Fälle ein Governance-Artefakt generiert.

**Architektur:** Python-Package `src/ai_act_toolkit/` (deterministischer Regelbaum, Toy-SUT, metamorphe Test-Runner-Logik, Markdown-Governance-Generator) + Streamlit-App `app.py` als UI-Schicht. Gleiches Grundmuster wie `sql-agent`/`goz-finetune-vs-rag`.

**Tech Stack:** Python ≥3.10, Streamlit, LangChain (`init_chat_model`, provider-agnostisch via `LLM_PROVIDER`/`LLM_MODEL`), pytest, python-dotenv.

## Global Constraints

- Alle Doku/Kommentare/UI-Texte auf Deutsch (Deutsch + Lehrstil, siehe Design-Spec Abschnitt "Lernstil").
- `pytest` läuft komplett ohne LLM/Netzwerk-Zugriff (Design-Spec, Abschnitt "Testing").
- Package-Layout `src/ai_act_toolkit/`, installierbar via `pip install -e ".[dev]"` (Muster aus `sql-agent`).
- Branch heißt `master`, nicht `main` (Konvention aller bestehenden Portfolio-Repos).
- Kein hart kodiertes LLM-Modell im Code — Provider/Modell ausschließlich über `.env` (`LLM_PROVIDER`/`LLM_MODEL`), analog `sql-agent/src/agent/llm.py`.
- Keine rechtsverbindlichen Compliance-Aussagen; jedes Governance-Artefakt trägt den Hinweis, dass es keine juristische Beratung ersetzt (Design-Spec, "Bewusst weggelassen").

---

### Task 1: Projekt-Grundgerüst

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/ai_act_toolkit/__init__.py`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Produces: installierbares Package `ai_act_toolkit` (Import-Pfad für alle folgenden Tasks), Test-Runner-Setup (`pytest tests/`).

- [ ] **Step 1: `pyproject.toml` anlegen**

```toml
[project]
name = "ai-act-validation-toolkit"
version = "0.1.0"
description = "EU-AI-Act-Risikoklassifizierung + metamorphe Validierung (Portfolio-Miniatur von Marco Stangs Promotionsthema)"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3",
    "langchain-anthropic>=0.3",
    "langchain-openai>=0.2",
    "python-dotenv>=1.0",
    "streamlit>=1.38",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["src*"]
```

- [ ] **Step 2: `.gitignore` anlegen**

```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
*.egg-info/
```

- [ ] **Step 3: `.env.example` anlegen**

```
# Welcher LLM-Provider genutzt wird — steuert, welches LangChain-
# Integrationspaket init_chat_model() im Hintergrund verwendet.
LLM_PROVIDER=anthropic
# LLM_PROVIDER=openai

# Modellbezeichner des jeweiligen Anbieters. Bewusst kein Default im Code —
# aktuelle Modell-IDs bitte in der Doku des Anbieters nachschauen.
LLM_MODEL=claude-sonnet-4-5-20250929
# LLM_MODEL=gpt-4o-mini

# Nur den Key des gewählten Providers eintragen.
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

- [ ] **Step 4: Package-Skeleton anlegen**

`src/ai_act_toolkit/__init__.py`:

```python
"""ai_act_toolkit — EU-AI-Act-Risikoklassifizierung + metamorphe Validierung."""
```

- [ ] **Step 5: venv anlegen und Package installieren**

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

- [ ] **Step 6: Smoke-Test schreiben**

`tests/test_smoke.py`:

```python
import ai_act_toolkit


def test_package_importable():
    assert ai_act_toolkit is not None
```

- [ ] **Step 7: Test ausführen, muss grün sein**

Run: `.venv/Scripts/python.exe -m pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/ai_act_toolkit/__init__.py tests/test_smoke.py
git commit -m "chore: Projekt-Grundgerüst (pyproject, package skeleton, smoke test)"
```

---

### Task 2: Risikoklassifizierung (`risk_engine.py`)

**Files:**
- Create: `src/ai_act_toolkit/risk_engine.py`
- Test: `tests/test_risk_engine.py`

**Interfaces:**
- Consumes: nichts (reine Domänenlogik, keine Abhängigkeit zu Task 1 außer dem Package-Pfad).
- Produces: `RiskClass` (Enum: `UNACCEPTABLE`, `HIGH_RISK`, `LIMITED_RISK`, `MINIMAL_RISK`), `Annex3Area` (Enum), `UseCaseAttributes` (dataclass), `ClassificationResult` (dataclass mit `risk_class: RiskClass`, `matched_rule: str`), `classify(attrs: UseCaseAttributes) -> ClassificationResult`. Wird von Task 3 (Use Cases), Task 5 (Governance) und Task 7 (App) importiert.

- [ ] **Step 1: Fehlschlagenden Test schreiben**

`tests/test_risk_engine.py`:

```python
from ai_act_toolkit.risk_engine import (
    Annex3Area,
    RiskClass,
    UseCaseAttributes,
    classify,
)


def _base_attrs(**overrides):
    defaults = dict(
        is_prohibited_practice=False,
        is_safety_component_regulated_product=False,
        is_annex3_area=False,
        annex3_area=Annex3Area.NONE,
        significant_risk_to_health_safety_fundamental_rights=False,
        has_transparency_obligation=False,
    )
    defaults.update(overrides)
    return UseCaseAttributes(**defaults)


def test_prohibited_practice_is_unacceptable():
    result = classify(_base_attrs(is_prohibited_practice=True))
    assert result.risk_class == RiskClass.UNACCEPTABLE


def test_safety_component_is_high_risk():
    result = classify(_base_attrs(is_safety_component_regulated_product=True))
    assert result.risk_class == RiskClass.HIGH_RISK


def test_annex3_area_with_significant_risk_is_high_risk():
    result = classify(
        _base_attrs(
            is_annex3_area=True,
            annex3_area=Annex3Area.EMPLOYMENT,
            significant_risk_to_health_safety_fundamental_rights=True,
        )
    )
    assert result.risk_class == RiskClass.HIGH_RISK
    assert "employment" in result.matched_rule


def test_annex3_area_without_significant_risk_is_not_high_risk():
    result = classify(
        _base_attrs(
            is_annex3_area=True,
            annex3_area=Annex3Area.EMPLOYMENT,
            significant_risk_to_health_safety_fundamental_rights=False,
        )
    )
    assert result.risk_class != RiskClass.HIGH_RISK


def test_transparency_obligation_is_limited_risk():
    result = classify(_base_attrs(has_transparency_obligation=True))
    assert result.risk_class == RiskClass.LIMITED_RISK


def test_no_criteria_is_minimal_risk():
    result = classify(_base_attrs())
    assert result.risk_class == RiskClass.MINIMAL_RISK


def test_prohibited_practice_wins_over_everything_else():
    result = classify(
        _base_attrs(
            is_prohibited_practice=True,
            is_safety_component_regulated_product=True,
        )
    )
    assert result.risk_class == RiskClass.UNACCEPTABLE
```

- [ ] **Step 2: Test ausführen, muss fehlschlagen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_risk_engine.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.risk_engine'`

- [ ] **Step 3: `risk_engine.py` implementieren**

```python
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
```

- [ ] **Step 4: Test ausführen, muss bestehen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_risk_engine.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/risk_engine.py tests/test_risk_engine.py
git commit -m "feat: deterministischer Annex-III-Regelbaum zur Risikoklassifizierung"
```

---

### Task 3: Beispiel-Use-Cases (`use_cases.py`)

**Files:**
- Create: `src/ai_act_toolkit/use_cases.py`
- Test: `tests/test_use_cases.py`

**Interfaces:**
- Consumes: `Annex3Area`, `UseCaseAttributes` aus `ai_act_toolkit.risk_engine` (Task 2).
- Produces: `UseCase` (dataclass: `key: str`, `title: str`, `description: str`, `attributes: UseCaseAttributes`, `has_metamorphic_demo: bool`), Konstanten `COMFORT_SYSTEM`, `RECRUITING`, `CHATBOT`, `ALL_USE_CASES: list[UseCase]`. Wird von Task 5 (Governance) und Task 7 (App) importiert.

- [ ] **Step 1: Fehlschlagenden Test schreiben**

`tests/test_use_cases.py`:

```python
from ai_act_toolkit.risk_engine import RiskClass, classify
from ai_act_toolkit.use_cases import ALL_USE_CASES, CHATBOT, COMFORT_SYSTEM, RECRUITING


def test_all_use_cases_present():
    assert {uc.key for uc in ALL_USE_CASES} == {"comfort_system", "recruiting", "chatbot"}


def test_comfort_system_classifies_as_high_risk_with_metamorphic_demo():
    result = classify(COMFORT_SYSTEM.attributes)
    assert result.risk_class == RiskClass.HIGH_RISK
    assert COMFORT_SYSTEM.has_metamorphic_demo is True


def test_recruiting_classifies_as_high_risk_without_metamorphic_demo():
    result = classify(RECRUITING.attributes)
    assert result.risk_class == RiskClass.HIGH_RISK
    assert RECRUITING.has_metamorphic_demo is False


def test_chatbot_classifies_as_limited_risk():
    result = classify(CHATBOT.attributes)
    assert result.risk_class == RiskClass.LIMITED_RISK
    assert CHATBOT.has_metamorphic_demo is False
```

- [ ] **Step 2: Test ausführen, muss fehlschlagen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_use_cases.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.use_cases'`

- [ ] **Step 3: `use_cases.py` implementieren**

```python
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
```

- [ ] **Step 4: Test ausführen, muss bestehen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_use_cases.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/use_cases.py tests/test_use_cases.py
git commit -m "feat: 3 Beispiel-Use-Cases (Komfortsystem, Recruiting, Chatbot)"
```

---

### Task 4: Toy-SUT + metamorphe Test-Runner-Logik

**Files:**
- Create: `src/ai_act_toolkit/metamorphic.py`
- Create: `src/ai_act_toolkit/comfort_system_sut.py`
- Test: `tests/test_metamorphic.py`

**Interfaces:**
- Consumes: nichts von vorherigen Tasks (eigenständige Domänenlogik).
- Produces: `MetamorphicRelation` (dataclass: `name`, `description`, `transform: Callable[[dict], dict]`, `check: Callable[[float, float], bool]`), `MetamorphicResult` (dataclass: `relation`, `source_inputs`, `source_output`, `followup_inputs`, `followup_output`, `passed: bool`), `run_relation(sut_fn, relation, source_inputs) -> MetamorphicResult` (in `metamorphic.py`); `decide_cooling_intensity(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count) -> float` und `TEMPERATURE_MONOTONICITY_RELATION: MetamorphicRelation` (in `comfort_system_sut.py`). Wird von Task 5 (Governance) und Task 7 (App) importiert.

- [ ] **Step 1: Fehlschlagenden Test schreiben**

`tests/test_metamorphic.py`:

```python
from ai_act_toolkit.comfort_system_sut import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
from ai_act_toolkit.metamorphic import run_relation


def test_monotonic_sut_passes_relation():
    source_inputs = dict(
        outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
    )
    result = run_relation(
        decide_cooling_intensity, TEMPERATURE_MONOTONICITY_RELATION, source_inputs
    )
    assert result.passed is True
    assert result.followup_output >= result.source_output
    assert result.followup_inputs["outside_temp_c"] == 25.0


def test_broken_sut_fails_relation():
    def broken_sut(outside_temp_c, cabin_temp_c, desired_temp_c, occupant_count):
        # bewusst falsch: Kühlintensität sinkt mit steigender Außentemperatur —
        # testet, dass run_relation eine echte Verletzung erkennt.
        return max(0.0, 50.0 - outside_temp_c)

    source_inputs = dict(
        outside_temp_c=20.0, cabin_temp_c=22.0, desired_temp_c=21.0, occupant_count=2
    )
    result = run_relation(broken_sut, TEMPERATURE_MONOTONICITY_RELATION, source_inputs)
    assert result.passed is False


def test_decide_cooling_intensity_is_bounded():
    intensity = decide_cooling_intensity(
        outside_temp_c=50.0, cabin_temp_c=50.0, desired_temp_c=21.0, occupant_count=8
    )
    assert 0.0 <= intensity <= 100.0
```

- [ ] **Step 2: Test ausführen, muss fehlschlagen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_metamorphic.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.metamorphic'`

- [ ] **Step 3: `metamorphic.py` implementieren**

```python
"""Generischer Runner für metamorphe Tests.

Eine metamorphe Relation prüft nicht eine einzelne Ausgabe gegen ein
festes Referenzergebnis (das "Orakel-Problem" bei KI-Systemen: die
"richtige" Ausgabe ist oft unbekannt), sondern eine Beziehung zwischen
der Ausgabe eines Quellfalls und der Ausgabe eines daraus abgeleiteten
Folgefalls — genau das Prinzip aus Marcos Promotion, hier auf einen
konkret ausführbaren Fall reduziert.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class MetamorphicRelation:
    name: str
    description: str
    transform: Callable[[dict], dict]
    check: Callable[[float, float], bool]


@dataclass
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
    followup_inputs = relation.transform(source_inputs)
    followup_output = sut_fn(**followup_inputs)
    passed = relation.check(source_output, followup_output)
    return MetamorphicResult(
        relation=relation,
        source_inputs=source_inputs,
        source_output=source_output,
        followup_inputs=followup_inputs,
        followup_output=followup_output,
        passed=passed,
    )
```

- [ ] **Step 4: `comfort_system_sut.py` implementieren**

```python
"""Toy-'System unter Test': simuliertes KI-Komfortsystem.

Kein echtes ML-Modell — ein bewusst einfaches, deterministisches Stellvertreter-
Modell, an dem die metamorphe Testmethodik konkret demonstriert wird.
"""

from ai_act_toolkit.metamorphic import MetamorphicRelation


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
)
```

- [ ] **Step 5: Test ausführen, muss bestehen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_metamorphic.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/ai_act_toolkit/metamorphic.py src/ai_act_toolkit/comfort_system_sut.py tests/test_metamorphic.py
git commit -m "feat: metamorpher Test-Runner + Toy-Komfortsystem-SUT"
```

---

### Task 5: Governance-Artefakt (`governance.py`)

**Files:**
- Create: `src/ai_act_toolkit/governance.py`
- Test: `tests/test_governance.py`

**Interfaces:**
- Consumes: `ClassificationResult` aus `ai_act_toolkit.risk_engine` (Task 2), `UseCase` aus `ai_act_toolkit.use_cases` (Task 3), `MetamorphicResult` aus `ai_act_toolkit.metamorphic` (Task 4).
- Produces: `generate_governance_artifact(use_case: UseCase, classification: ClassificationResult, rationale: str, metamorphic_result: MetamorphicResult | None) -> str`. Wird von Task 7 (App) importiert.

- [ ] **Step 1: Fehlschlagenden Test schreiben**

`tests/test_governance.py`:

```python
from ai_act_toolkit.comfort_system_sut import (
    TEMPERATURE_MONOTONICITY_RELATION,
    decide_cooling_intensity,
)
from ai_act_toolkit.governance import generate_governance_artifact
from ai_act_toolkit.metamorphic import run_relation
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
```

- [ ] **Step 2: Test ausführen, muss fehlschlagen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_governance.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'ai_act_toolkit.governance'`

- [ ] **Step 3: `governance.py` implementieren**

```python
"""Generiert das Governance-Artefakt (Risk Assessment + Konformitätscheckliste)
als Markdown für Hochrisiko-Use-Cases.
"""

from ai_act_toolkit.metamorphic import MetamorphicResult
from ai_act_toolkit.risk_engine import ClassificationResult
from ai_act_toolkit.use_cases import UseCase

OBLIGATIONS = [
    (
        "Art. 9 — Risikomanagementsystem",
        "Kontinuierlicher Prozess zur Identifikation/Minderung von Risiken über den Lebenszyklus.",
    ),
    (
        "Art. 10 — Daten- und Datenqualitätsmanagement",
        "Trainings-/Validierungs-/Testdaten müssen repräsentativ, fehlerfrei und vollständig sein.",
    ),
    (
        "Art. 11 — Technische Dokumentation",
        "Nachweisbare Dokumentation zu Design, Entwicklung und Leistung.",
    ),
    (
        "Art. 12 — Aufzeichnungspflichten (Logging)",
        "Automatische Protokollierung während des Betriebs.",
    ),
    (
        "Art. 13 — Transparenz und Informationsbereitstellung",
        "Verständliche Betriebsanleitung für Betreiber.",
    ),
    (
        "Art. 14 — Menschliche Aufsicht",
        "Wirksame Aufsichtsmaßnahmen zur Verhinderung/Minimierung von Risiken.",
    ),
    (
        "Art. 15 — Genauigkeit, Robustheit, Cybersicherheit",
        "Angemessenes Leistungsniveau über den gesamten Lebenszyklus.",
    ),
]


def generate_governance_artifact(
    use_case: UseCase,
    classification: ClassificationResult,
    rationale: str,
    metamorphic_result: MetamorphicResult | None,
) -> str:
    lines = [
        f"# Risk Assessment & Konformitätscheckliste — {use_case.title}",
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
            f"**Relation:** {metamorphic_result.relation.name} — {metamorphic_result.relation.description}",
            f"**Ergebnis:** {status}",
            f"- Quellfall: {metamorphic_result.source_inputs} -> {metamorphic_result.source_output:.1f}",
            f"- Folgefall: {metamorphic_result.followup_inputs} -> {metamorphic_result.followup_output:.1f}",
            "",
        ]

    lines.append("## Konformitätscheckliste (EU AI Act, high-risk)")
    for title, desc in OBLIGATIONS:
        lines.append(f"- [ ] **{title}** — {desc}")
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

- [ ] **Step 4: Test ausführen, muss bestehen**

Run: `.venv/Scripts/python.exe -m pytest tests/test_governance.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai_act_toolkit/governance.py tests/test_governance.py
git commit -m "feat: Governance-Artefakt-Generator (Risk Assessment + Konformitätscheckliste)"
```

---

### Task 6: LLM-Anbindung + Begründungstext (`llm.py`, `rationale.py`)

**Files:**
- Create: `src/ai_act_toolkit/llm.py`
- Create: `src/ai_act_toolkit/rationale.py`

**Interfaces:**
- Consumes: `ClassificationResult` aus `ai_act_toolkit.risk_engine` (Task 2), `UseCase` aus `ai_act_toolkit.use_cases` (Task 3).
- Produces: `get_llm() -> BaseChatModel` (in `llm.py`), `generate_rationale(llm: BaseChatModel, use_case: UseCase, classification: ClassificationResult) -> str` (in `rationale.py`). Wird von Task 7 (App) importiert.

Kein automatisierter Test (Design-Spec: Test-Suite läuft ohne LLM/Netzwerk) — Verifikation erfolgt manuell in Task 7, wenn die App mit echtem API-Key läuft (gleiches Vorgehen wie `sql-agent/src/agent/llm.py`).

- [ ] **Step 1: `llm.py` implementieren (1:1 Muster aus `sql-agent`)**

```python
"""Wählt das LLM aus, ohne einen Anbieter fest zu verdrahten.

init_chat_model() ist LangChains einheitliche Fabrik-Funktion: je nach
model_provider lädt sie im Hintergrund das passende Integrationspaket
(hier langchain-anthropic oder langchain-openai) und liefert in beiden
Fällen dasselbe Chat-Model-Interface zurück.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    """Baut das Chat-Model aus LLM_PROVIDER/LLM_MODEL in der .env."""
    provider = os.environ.get("LLM_PROVIDER")
    model = os.environ.get("LLM_MODEL")

    if not provider or not model:
        raise RuntimeError(
            "LLM_PROVIDER und LLM_MODEL müssen in der .env gesetzt sein "
            "(siehe .env.example). Aktuell: "
            f"LLM_PROVIDER={provider!r}, LLM_MODEL={model!r}"
        )

    return init_chat_model(model, model_provider=provider)
```

- [ ] **Step 2: `rationale.py` implementieren**

```python
"""Lässt ein LLM nur die Begründung in Klartext formulieren — die
Risikoklasse selbst kommt deterministisch aus risk_engine.classify().
"""

from langchain_core.language_models.chat_models import BaseChatModel

from ai_act_toolkit.risk_engine import ClassificationResult
from ai_act_toolkit.use_cases import UseCase

RATIONALE_PROMPT = """Du bist Assistent für EU-AI-Act-Risikoklassifizierung.
Ein regelbasierter Klassifizierer hat folgendes Ergebnis ermittelt:

Use Case: {title}
Beschreibung: {description}
Risikoklasse: {risk_class}
Angewendete Regel: {matched_rule}

Formuliere in 3-4 Sätzen auf Deutsch eine für Nicht-Juristen verständliche
Begründung, warum dieser Use Case in diese Risikoklasse fällt. Erfinde
keine zusätzlichen Fakten über den Use Case, die oben nicht genannt sind."""


def generate_rationale(
    llm: BaseChatModel, use_case: UseCase, classification: ClassificationResult
) -> str:
    prompt = RATIONALE_PROMPT.format(
        title=use_case.title,
        description=use_case.description,
        risk_class=classification.risk_class.value,
        matched_rule=classification.matched_rule,
    )
    response = llm.invoke(prompt)
    return response.content
```

- [ ] **Step 3: Manuell verifizieren (kein pytest, siehe Hinweis oben)**

```bash
cp .env.example .env
# LLM_PROVIDER/LLM_MODEL/ANTHROPIC_API_KEY in .env eintragen
.venv/Scripts/python.exe -c "
from ai_act_toolkit.llm import get_llm
from ai_act_toolkit.rationale import generate_rationale
from ai_act_toolkit.risk_engine import classify
from ai_act_toolkit.use_cases import COMFORT_SYSTEM

llm = get_llm()
result = classify(COMFORT_SYSTEM.attributes)
print(generate_rationale(llm, COMFORT_SYSTEM, result))
"
```

Erwartet: druckt einen 3-4-sätzigen deutschen Begründungstext ohne Fehler.

- [ ] **Step 4: Commit**

```bash
git add src/ai_act_toolkit/llm.py src/ai_act_toolkit/rationale.py
git commit -m "feat: LLM-Anbindung + Begründungstext-Generierung"
```

---

### Task 7: Streamlit-App (`app.py`)

**Files:**
- Create: `app.py`

**Interfaces:**
- Consumes: alles aus Task 2–6 (`risk_engine`, `use_cases`, `metamorphic`, `comfort_system_sut`, `governance`, `llm`, `rationale`).
- Produces: lauffähige Streamlit-App, kein weiterer Konsument im Package.

- [ ] **Step 1: `app.py` implementieren**

```python
"""Streamlit-UI für das AI Act Validation Toolkit."""

import streamlit as st

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

st.set_page_config(page_title="AI Act Validation Toolkit", page_icon="⚖️")

st.title("⚖️ AI Act Validation Toolkit")
st.markdown(
    "**In 30 Sekunden:** Dieses Tool sagt dir, ob dein KI-System nach dem "
    "EU AI Act als 'Hochrisiko' gilt — und beweist das an einem live "
    "ausgeführten Test, statt nur zu behaupten. Basiert auf Marco Stangs "
    "Promotion zur Validierung von KI-Systemen durch Szenario-Verknüpfung "
    "und metamorphes Testen (KIT/ITIV, 2019–2025)."
)

use_case_titles = [uc.title for uc in ALL_USE_CASES]
selected_title = st.selectbox("Beispiel-Use-Case wählen", use_case_titles)
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
display_fn(f"**{label}** — Regel: {classification.matched_rule}")

if st.button("Begründung generieren (LLM)"):
    llm = get_llm()
    st.session_state["rationale"] = generate_rationale(llm, use_case, classification)

rationale = st.session_state.get("rationale")
if rationale:
    st.markdown(f"**Begründung:** {rationale}")

metamorphic_result = st.session_state.get("metamorphic_result")
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
        st.session_state["metamorphic_result"] = metamorphic_result

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

if classification.risk_class == RiskClass.HIGH_RISK and rationale:
    st.subheader("Governance-Artefakt")
    artifact = generate_governance_artifact(use_case, classification, rationale, metamorphic_result)
    st.markdown(artifact)
    st.download_button(
        "Als Markdown herunterladen", data=artifact, file_name=f"{use_case.key}_governance.md"
    )
```

- [ ] **Step 2: Manuell verifizieren**

```bash
.venv/Scripts/python.exe -m streamlit run app.py
```

Für jeden der 3 Use Cases im Browser prüfen: (1) Ampel-Farbe + Regel korrekt, (2) Fragebogen-Änderung löst sofortige Neuklassifizierung aus, (3) "Begründung generieren" liefert Text, (4) beim Komfortsystem: "Metamorphen Test ausführen" zeigt BESTANDEN mit Zahlen, (5) bei Komfortsystem + Recruiting: Governance-Artefakt sichtbar + Download-Button funktioniert.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit-UI mit Fragebogen, Ampel, metamorphem Test und Governance-Artefakt"
```

---

### Task 8: README + CLAUDE.md

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`

**Interfaces:**
- Konsumiert nichts, produziert nichts für andere Tasks — reine Dokumentation.

- [ ] **Step 1: `README.md` schreiben**

```markdown
# ai-act-validation-toolkit

Portfolio-Projekt von Marco Stang für Bewerbungen auf AI/KI-Rollen (ggf.
auch KI-Transformations-Rollen).

## In 30 Sekunden

Dieses Tool sagt dir, ob dein KI-System nach dem EU AI Act als "Hochrisiko"
gilt — und beweist das an einem live ausgeführten Test, statt nur zu
behaupten. Ab dem 2. August 2026 gilt die Enforcement-Pflicht für
High-Risk-Systeme nach dem EU AI Act.

Es ist eine anwendbare Miniatur-Version von Marcos Promotionsthema
(Dr.-Ing., "Sehr gut", KIT/ITIV, 2019–2025): "Validierung von KI-Systemen
durch Verknüpfung von Szenarien und metamorphes Testen", erprobt in einer
Industriekooperation mit Mercedes-Benz zu autonomen
Fahrzeug-Komfortsystemen.

## Live-Demo

[Link folgt nach Streamlit-Community-Cloud-Deployment]

## Was das Tool macht

1. Ordnet einen beschriebenen KI-Use-Case per deterministischem Regelbaum
   einer EU-AI-Act-Risikoklasse zu (Annex III) — editierbarer Fragebogen,
   keine Blackbox-Klassifizierung.
2. Lässt ein LLM nur die Begründung in Klartext formulieren, nicht die
   Klassifizierung selbst.
3. Führt für den Automotive-Use-Case einen echten metamorphen Test aus
   (Temperatur-Monotonie-Relation) gegen ein simuliertes Komfortsystem.
4. Generiert für Hochrisiko-Fälle ein Governance-Artefakt (Risk Assessment
   + Konformitätscheckliste) als Markdown, in-App + als Download.

## Architektur

- `src/ai_act_toolkit/risk_engine.py` — deterministischer Annex-III-Regelbaum
- `src/ai_act_toolkit/use_cases.py` — 3 Beispiel-Use-Cases
- `src/ai_act_toolkit/comfort_system_sut.py` — Toy-Komfortsystem + Monotonie-Relation
- `src/ai_act_toolkit/metamorphic.py` — generischer metamorpher Test-Runner
- `src/ai_act_toolkit/governance.py` — Governance-Artefakt-Generator
- `src/ai_act_toolkit/llm.py` / `rationale.py` — LLM-Begründungstext
- `app.py` — Streamlit-UI

## Quickstart

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env  # LLM_PROVIDER/LLM_MODEL/API-Key eintragen

.venv/Scripts/python.exe -m pytest tests/ -v
.venv/Scripts/python.exe -m streamlit run app.py
```

## Limitierungen

- Keine rechtsverbindliche Compliance-Aussage, kein Ersatz für juristische
  Beratung oder ein echtes Konformitätsbewertungsverfahren.
- Nur 3 fest hinterlegte Beispiel-Use-Cases, kein Freitext-Import.
- Ein metamorpher Test (Monotonie-Relation), nicht die volle
  Szenario-Verknüpfungsmethodik der Promotion.
```

- [ ] **Step 2: `CLAUDE.md` schreiben**

```markdown
# ai-act-validation-toolkit — Projektkontext

Design-Spec: `docs/superpowers/specs/2026-07-28-ai-act-validation-toolkit-design.md`
Implementierungsplan: `docs/superpowers/plans/2026-07-28-ai-act-validation-toolkit-implementation.md`

## Was das hier ist

Portfolio-Projekt von Marco Stang für Bewerbungen auf AI/KI-Rollen (ggf.
auch KI-Transformations-Rollen). Miniatur-Version seines Promotionsthemas
(Validierung von KI-Systemen durch Verknüpfung von Szenarien und
metamorphes Testen) als EU-AI-Act-Risikoklassifizierungs- und
Governance-Tool. Zeitbudget 3-4 Tage.

## Commands

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env  # LLM_PROVIDER/LLM_MODEL/API-Key eintragen

.venv/Scripts/python.exe -m pytest tests/ -v          # komplette Test-Suite, kein LLM/Netzwerk nötig
.venv/Scripts/python.exe -m streamlit run app.py       # Demo-App
```

Kein Linter konfiguriert.

## Architektur

- `src/ai_act_toolkit/risk_engine.py` — deterministischer Regelbaum:
  Art. 5 (verboten) → Art. 6(1) (Sicherheitsbauteil) → Art. 6(2)+Annex III
  (Hochrisiko-Bereich mit Art.-6(3)-Ausnahme) → Art. 50 (Transparenzpflicht)
  → minimal
- `src/ai_act_toolkit/use_cases.py` — Komfortsystem (high-risk, mit
  metamorphem Test), Recruiting (high-risk), Chatbot (limited-risk)
- `src/ai_act_toolkit/comfort_system_sut.py` — Toy-SUT + Temperatur-Monotonie-Relation
- `src/ai_act_toolkit/metamorphic.py` — generischer `run_relation()`-Runner
- `src/ai_act_toolkit/governance.py` — Markdown-Governance-Artefakt (Art. 9-15-Checkliste)
- `src/ai_act_toolkit/llm.py` / `rationale.py` — provider-agnostische
  LLM-Anbindung (Muster aus `sql-agent`), generiert nur den Begründungstext
- `app.py` — Streamlit-UI: Use-Case-Auswahl → editierbarer Fragebogen →
  Ampel-Klassifizierung → Begründung (LLM) → metamorpher Test
  (Komfortsystem) → Governance-Artefakt (high-risk)

## Wie hier gearbeitet wird

Deutsch + Lehrstil wie bei `sql-agent`/`goz-finetune-vs-rag` — Marco lernt
aktiv mit, Konzepte erklären statt vorlösen, alle Doku auf Deutsch.

## Aktueller Stand

*Diesen Abschnitt aktuell halten, sobald ein Task aus dem
Implementierungsplan abgeschlossen ist.*

- ✅ Design-Spec + Implementierungsplan erstellt und freigegeben.
```

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: README und CLAUDE.md"
```

---

### Task 9: Neues GitHub-Repo erstellen und pushen

**Files:** keine Code-Dateien — Git-Remote-Operation.

**Interfaces:** keine.

Laut `PORTFOLIO_AGENT_GUIDE.md`, Abschnitt 4: **vor dem Anlegen kurz mit
Marco Repo-Name und Sichtbarkeit bestätigen** (Standardannahme: public,
Name `ai-act-validation-toolkit`, wie bei den 4 bestehenden Repos). `gh`
ist auf diesem Rechner nicht installiert (Stand 2026-07-28) — Fallback
manuell im Browser.

- [ ] **Step 1: Mit Marco bestätigen: Repo-Name `ai-act-validation-toolkit`, public — passt das?**

- [ ] **Step 2: Repo auf github.com als `maggostang-droid` anlegen**

"New repository" → Name `ai-act-validation-toolkit`, **public**, ohne
README/.gitignore-Vorbelegung (kommt aus dem lokalen Repo).

- [ ] **Step 3: Lokal verbinden und pushen**

```bash
git remote add origin https://github.com/maggostang-droid/ai-act-validation-toolkit.git
git push -u origin master
```

- [ ] **Step 4: Verifizieren**

Run: `git remote -v && git log --oneline -1`
Erwartet: `origin` zeigt auf das neue Repo, letzter Commit ist auf GitHub sichtbar.

---

### Task 10: Streamlit Community Cloud Deployment

**Files:** keine — externes Hosting-Setup.

**Interfaces:** keine.

- [ ] **Step 1: Auf share.streamlit.io mit dem GitHub-Account einloggen**

- [ ] **Step 2: Neue App aus `maggostang-droid/ai-act-validation-toolkit`, Branch `master`, Datei `app.py` deployen**

- [ ] **Step 3: Secrets setzen (Streamlit-Cloud-UI, "Secrets")**

```toml
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-sonnet-4-5-20250929"
ANTHROPIC_API_KEY = "..."
```

- [ ] **Step 4: Live-URL im `README.md` unter "Live-Demo" eintragen und committen/pushen**

```bash
git add README.md
git commit -m "docs: Live-Demo-Link ergänzen"
git push
```

---

## Self-Review

- **Spec-Abdeckung:** Alle Abschnitte der Design-Spec (Architektur, 3
  Use-Cases, User-Flow inkl. 30-Sekunden-Erklärung + Ampel, metamorpher
  Test, Governance-Artefakt, Testing, Deployment, Definition of Done) sind
  auf Tasks 1-10 abgebildet.
- **Platzhalter-Scan:** keine TBD/TODO in Code-Blöcken; einzige offene
  Werte (Live-Demo-URL, API-Keys) sind bewusst erst nach Deployment
  bekannt und in Task 10 explizit als Schritt dokumentiert.
- **Typ-Konsistenz geprüft:** `UseCaseAttributes`/`ClassificationResult`/
  `RiskClass`/`Annex3Area` (Task 2) werden in Task 3, 5, 6, 7 identisch
  verwendet; `MetamorphicRelation`/`MetamorphicResult`/`run_relation`
  (Task 4) identisch in Task 5 und 7; `UseCase` (Task 3) identisch in
  Task 5, 6, 7.
