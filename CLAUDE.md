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

Alle 8 Implementierungs-Tasks sind fertig implementiert und einzeln
reviewed:

- ✅ Task 1: Projekt-Grundgerüst (pyproject, package skeleton, smoke test)
- ✅ Task 2: `risk_engine.py` (deterministischer Annex-III-Regelbaum)
- ✅ Task 3: `use_cases.py` (3 Beispiel-Use-Cases)
- ✅ Task 4: `metamorphic.py` + `comfort_system_sut.py` (metamorpher Test-Runner)
- ✅ Task 5: `governance.py` (Governance-Artefakt-Generator)
- ✅ Task 6: `llm.py` + `rationale.py` (LLM-Anbindung)
- ✅ Task 7: `app.py` (Streamlit-UI)
- ✅ Task 8: README + CLAUDE.md

Die finale Whole-Branch-Review wurde durchgeführt, gefundene Findings sind
gefixt (siehe `.superpowers/sdd/2026-07-28-ai-act-validation-toolkit-implementation/final-review-fix-report.md`).

- ✅ GitHub-Repo angelegt und gepusht:
  https://github.com/maggostang-droid/ai-act-validation-toolkit (public,
  Branch `master`).
- ✅ GitHub-Pages-Projektseite live:
  https://maggostang-droid.github.io/ai-act-validation-toolkit/
- ✅ Task 10 abgeschlossen: Streamlit-Community-Cloud-Deployment live unter
  https://ai-act-validation-toolkit.streamlit.app/ (Marco hat Secrets
  selbst gesetzt, App von ihm als erreichbar bestätigt — damit auch der
  erste echte Testlauf mit echtem LLM-API-Key erfolgt).

Alle 10 Plan-Tasks sind damit abgeschlossen. Projekt ist "fertig" im
Sinne des Backlogs (`../PORTFOLIO_BACKLOG.md`, Status entsprechend
aktualisieren, falls noch nicht geschehen).

Noch offen (kein Implementierungs-Task):

- ⬜ Manuelle Browser-Verifikation der App durch eine Agenten-Session war
  nie möglich (kein Browser-Zugriff) — bisher nur automatisiert via
  `streamlit.testing.v1.AppTest` geprüft. Marco hat die Live-App laut
  eigener Aussage erreichbar bestätigt, ein detailliertes Durchklicken
  aller 3 Use-Cases in der Live-Version steht seitens einer Agenten-Session
  weiterhin aus.
