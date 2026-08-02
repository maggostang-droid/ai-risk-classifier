# AI Act Evidence Toolkit — Projektkontext

Ursprüngliche Spec: `docs/superpowers/specs/2026-07-28-ai-act-validation-toolkit-design.md`
**Aktuelle Spec:** `docs/superpowers/specs/2026-08-02-evidence-toolkit-design.md`
**Aktueller Plan:** `docs/superpowers/plans/2026-08-02-evidence-toolkit-implementation.md`

Repo-Slug bleibt `ai-risk-classifier`, Python-Paket bleibt `ai_act_toolkit`,
MARCO.OS-Projekt-`id` bleibt `ai-act-validation-toolkit` — nur der
Produktname wurde am 2026-08-02 zu „AI Act Evidence Toolkit" geändert. Nicht
umbenennen, sonst brechen Streamlit-Deployment und Deep-Links.

## Was das hier ist

Portfolio-Projekt von Marco Stang für Bewerbungen auf AI/KI-Rollen (ggf.
auch KI-Transformations-Rollen). Miniatur-Version seines Promotionsthemas
(Validierung von KI-Systemen durch Verknüpfung von Szenarien und
metamorphes Testen).

Die Leitfrage ist bewusst nicht „in welche Klasse fällt mein System?", sondern
„ich bin Hochrisiko — womit belege ich das technisch?". Genau dort hört jedes
andere AI-Act-Werkzeug auf, und genau das ist der Gegenstand der Promotion.
Wer hier etwas ändert, sollte diese Kette nicht auftrennen:
Einstufung → Pflichten → Nachweis → Artefakt.

## Commands

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env  # LLM_PROVIDER/LLM_MODEL/API-Key eintragen

.venv/Scripts/python.exe -m pytest tests/ -v          # komplette Test-Suite, kein LLM/Netzwerk nötig
.venv/Scripts/python.exe -m streamlit run app.py       # Demo-App
```

Linter: `.venv/Scripts/python.exe -m ruff check .` — läuft zusammen mit
pytest in `.github/workflows/ci.yml` bei jedem Push.

## Architektur

Die Leitidee: die Einstufung erzeugt Pflichten, die Relations-Suite liefert
die Evidenz dafür, das Artefakt hakt genau das ab, was belegt wurde.

- `src/ai_act_toolkit/risk_engine.py` — deterministischer Regelbaum:
  Art. 5 (verboten) → Art. 6(1) (Sicherheitsbauteil) → Art. 6(2)+Annex III
  (Hochrisiko-Bereich mit Art.-6(3)-Ausnahme) → Art. 50 (Transparenzpflicht)
  → minimal
- `src/ai_act_toolkit/obligations.py` — Risikoklasse → Artikelpflichten, jede
  mit `EvidenceKind` (TECHNICAL_TEST / DOCUMENTATION / PROCESS). Das
  Bindeglied zwischen Einstufung und Nachweis.
- `src/ai_act_toolkit/use_cases.py` — Komfortsystem, Recruiting, Chatbot.
  Reine Falldaten, kennt die SUTs nicht.
- `src/ai_act_toolkit/metamorphic/` — `core.py` (Relation mit `evidence_for`,
  `run_relation`), `suite.py` (alle Relationen einer SUT, `by_article()`),
  `mutation.py` (`Mutant`, `KillMatrix`, Mutation Score)
- `src/ai_act_toolkit/suts/` — `comfort_seat.py` (sicherheitsrelevant, Art. 6(1)),
  `comfort_climate.py`, `recruiting_scorer.py` (naiv/gefixt, Namensinvarianz),
  `__init__.py` mit `SUTSpec` und der Registry Use-Case → SUTs
- `src/ai_act_toolkit/governance.py` — Markdown-Artefakt, Checkliste in drei
  Zuständen: `[x]` belegt, `[~]` teilweise, `[ ]` offen/Prozesspflicht
- `src/ai_act_toolkit/llm.py` / `rationale.py` — provider-agnostische
  LLM-Anbindung (Muster aus `sql-agent`), generiert nur den Begründungstext
- `app.py` — Streamlit-UI in vier Schritten: 1. Einstufung → 2. Pflichten →
  3. Nachweis (mit Fehlerinjektion und Kill-Matrix) → 4. Artefakt

### Zwei Fallen in diesem Code

**Strenge vs. nicht-strenge Monotonie.** Relationen wie die Körpergrößen-
Monotonie prüfen `>` und nicht `>=`. Grund: mit `>=` würde eine komplett
ignorierte Eingangsgröße die Relation anstandslos bestehen. Wer eine solche
Relation lockert, macht sie blind für den entsprechenden Mutanten — und der
zugehörige Kill-Matrix-Test wird rot.

**Baselinepunkte dürfen nicht im Sättigungsbereich liegen.** Das Basisprofil
des Scorers steht auf `education_level=4`, nicht 3: bei 3 wird die
Vorzeichenfehler-Variante von der unteren Clip-Grenze auf 0 gehalten, Quell-
und Folgefall sind beide 0, und die Skill-Monotonie sieht den Defekt nicht.

## Wie hier gearbeitet wird

Deutsch + Lehrstil wie bei `sql-agent`/`goz-finetune-vs-rag` — Marco lernt
aktiv mit, Konzepte erklären statt vorlösen, alle Doku auf Deutsch.

## Aktueller Stand

**Stand 2026-08-02: Umbau zum Evidence Toolkit abgeschlossen** (Branch
`feature/evidence-toolkit`, 12 Tasks nach
`docs/superpowers/plans/2026-08-02-evidence-toolkit-implementation.md`).

- 74 Tests grün, ruff sauber, CI-Workflow angelegt.
- Metamorphes Testen ist der Kern statt eines Nebenfeatures: drei Systeme
  unter Test, elf Relationen, vierzehn Mutanten, Gesamt-Mutation-Score 11/14.
- Das Governance-Artefakt hakt nur ab, was tatsächlich belegt wurde.
- Fehlerinjektion in der UI: der metamorphe Test kann sichtbar fehlschlagen.
  Das war seit dem 2026-07-28 als verpasster Beweismoment vermerkt.

Vorher (2026-07-28): Erstbau nach
`docs/superpowers/plans/2026-07-28-ai-act-validation-toolkit-implementation.md`,
10 Tasks, deployed auf Streamlit Community Cloud unter
https://ai-act-validation-toolkit.streamlit.app/ (Marco hat die Secrets
selbst gesetzt).

## Doku-Artefakte neu erzeugen

- `docs/demo.gif` — Beweismoment als zwei-Frame-Animation:
  ```bash
  .venv/Scripts/python.exe -m streamlit run app.py --server.port 8502 --server.headless true &
  DEMO_CHROME=<pfad-zu-chrome-headless-shell.exe> python scripts/capture_demo.py docs/
  ```
  Playwright liegt global, nicht im venv. Liegt der erwartete Chromium-Build
  nicht vor, zeigt `DEMO_CHROME` auf einen vorhandenen unter
  `%LOCALAPPDATA%\ms-playwright\`.
- `docs/architecture.svg` — aus `docs/architecture.json`:
  ```bash
  node ../marco-os/tools/gen-diagram.mjs docs/architecture.json docs/architecture.svg
  ```
  Positionen sind bewusst von Hand gesetzt. Beim Ändern des Diagramms auch
  den Alt-Text im README nachziehen — er ist die Barrierefreiheits-Fassung
  desselben Inhalts.
