# ai-act-validation-toolkit

Portfolio-Projekt von Marco Stang für Bewerbungen auf AI/KI-Rollen (ggf.
auch KI-Transformations-Rollen).

🔗 **[Projektseite](https://maggostang-droid.github.io/ai-act-validation-toolkit/)**
— Überblick, Architektur, Motivation (kein Ersatz für die Live-Demo, siehe
unten).

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

👉 **[ai-act-validation-toolkit.streamlit.app](https://ai-act-validation-toolkit.streamlit.app/)**

(Streamlit Community Cloud — Free-Tier-Apps schlafen nach Inaktivität ein,
der erste Aufruf kann ein paar Sekunden zum Aufwachen brauchen.)

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
