# Handover — ai-act-validation-toolkit

Für jede neue Agenten-Session (Claude Code oder sonst), die an diesem
Projekt weiterarbeitet, ohne den bisherigen Chatverlauf zu kennen. Stand:
2026-07-28.

## TL;DR

Das Projekt ist **funktional fertig implementiert, getestet, reviewed und
auf GitHub veröffentlicht.** Nur der letzte Schritt (Live-Deployment über
Streamlit Community Cloud) fehlt noch, weil er Marcos persönlichen Login
und einen echten LLM-API-Key erfordert — das kann eine Agenten-Session
nicht eigenständig erledigen.

- Repo: https://github.com/maggostang-droid/ai-act-validation-toolkit (public, Branch `master`)
- Projektseite (GitHub Pages): https://maggostang-droid.github.io/ai-act-validation-toolkit/
- Live-Demo (Streamlit): **noch nicht deployed** — siehe "Nächster Schritt" unten
- Tests: `pytest tests/ -v` → 17/17 grün, kein Netzwerk/LLM nötig

## Wie dieses Projekt entstanden ist

1. Ausgewählt aus `../PORTFOLIO_BACKLOG.md` (Item #0, höchste Priorität) —
   Backlog dort noch als `in Arbeit` markiert, nicht `fertig` (erst nach
   Deployment + Rücksprache mit Marco umzustellen, siehe
   `../PORTFOLIO_AGENT_GUIDE.md`).
2. Design per `superpowers:brainstorming` erarbeitet und mit Marco
   abgestimmt → `docs/superpowers/specs/2026-07-28-ai-act-validation-toolkit-design.md`
3. Implementierungsplan (10 Tasks) → `docs/superpowers/plans/2026-07-28-ai-act-validation-toolkit-implementation.md`
4. Umsetzung über `superpowers:subagent-driven-development`: Tasks 1-8
   (Code) je einzeln implementiert und reviewed (Task 7 brauchte eine
   Fix-Runde: Session-State-Leck zwischen Use-Cases), danach eine finale
   Whole-Branch-Review mit einer weiteren Fix-Runde (5 Findings, siehe
   unten).
5. Task 9 (GitHub-Repo) erledigt. Task 10 (Deployment) offen.

## Was funktioniert (verifiziert)

- Deterministische Risikoklassifizierung (`src/ai_act_toolkit/risk_engine.py`)
  über einen Annex-III-Regelbaum, 7 Tests grün.
- 3 Beispiel-Use-Cases (Komfortsystem/high-risk, Recruiting/high-risk,
  Chatbot/limited-risk) in `use_cases.py`.
- Echter, ausgeführter metamorpher Test (Temperatur-Monotonie-Relation)
  gegen ein simuliertes Komfortsystem, inkl. Test, der eine kaputte SUT
  korrekt als Verletzung erkennt (`metamorphic.py`, `comfort_system_sut.py`).
- Governance-Artefakt-Generator (`governance.py`) — funktioniert jetzt
  auch OHNE erfolgreiche LLM-Begründung (Fallback-Text), nachdem das in
  der finalen Review als Important-Finding auffiel und gefixt wurde.
- Streamlit-UI (`app.py`) — per `streamlit.testing.v1.AppTest` (kein
  Browser nötig) mehrfach funktional verifiziert, inkl. sequenziellem
  Multi-Step-Test für den Session-State-Fix. **Ein echter Browser-Durchlauf
  wurde noch nie gemacht.**
- LLM-Anbindung (`llm.py`, `rationale.py`) — nur strukturell verifiziert
  (Imports, Signaturen, Fehlerpfade mit Mocks). **Noch nie mit einem
  echten API-Key aufgerufen.**

## Bekannte, bewusst offen gelassene Punkte (kein Handlungsbedarf, nur zur Info)

Aus den Task-Reviews und der finalen Review, alle als Minor eingestuft und
geparkt (nicht blockierend):

- `comfort_system_sut.py`: unterer Clip nur für unvalidiertes negatives
  `occupant_count` relevant (über die App nicht erreichbar).
- `metamorphic.py`: `MetamorphicResult.source_inputs` speichert eine
  Referenz statt Kopie — aktuell entschärft, weil `transform()` immer ein
  neues Dict baut.
- `session_state` in `app.py` akkumuliert einen Key pro
  (Use-Case, Risikoklasse, Regel)-Kombination, wird nie bereinigt —
  bei 3 Use Cases harmlos.
- Kein `key=`-Parameter an den Fragebogen-Widgets — kein aktiver Bug,
  aber fragiles Muster.
- `requirements.txt` dupliziert die Runtime-Deps aus `pyproject.toml`
  (Drift-Risiko bei künftigen Versions-Updates — an beiden Stellen
  nachziehen).
- `rationale.py`: `generate_rationale()` ist als `-> str` typisiert, manche
  LangChain-Provider liefern aber ggf. `list[dict]` als `response.content`.

**Nicht umgesetzt, aber als sinnvolle Erweiterung im finalen Review
vorgeschlagen:** ein Toggle in der App, der eine absichtlich kaputte SUT
verwendet, damit der metamorphe Test auch mal sichtbar FEHLSCHLÄGT (aktuell
zeigt die App immer BESTANDEN, weil die geshippte SUT konstruktionsbedingt
monoton ist — nur der pytest `test_broken_sut_fails_relation` beweist, dass
der Runner Verletzungen erkennt). Wäre ein guter "Beweis"-Moment für
Recruiter, ist aber reine UI-Erweiterung, kein Bugfix.

## Nächster Schritt: Task 10 (Streamlit Community Cloud Deployment)

**Das kann nur Marco selbst tun** (Login + persönlicher API-Key):

1. Auf https://share.streamlit.io mit seinem GitHub-Account einloggen.
2. Neue App aus `maggostang-droid/ai-act-validation-toolkit`, Branch
   `master`, Datei `app.py` deployen.
3. In den App-Secrets eintragen: `LLM_PROVIDER`, `LLM_MODEL`,
   `ANTHROPIC_API_KEY` (siehe `.env.example` für das Format).
4. Kurz durchklicken: alle 3 Use-Cases, Begründung generieren, metamorphen
   Test ausführen, Governance-Artefakt herunterladen.

**Danach, für eine Agenten-Session:**

1. Live-URL im README.md unter "Live-Demo" eintragen (aktuell Platzhalter).
2. `../PORTFOLIO_BACKLOG.md`: Status von Item #0 auf `fertig` setzen.
3. Falls gewünscht: neue Projekt-Karte in `../stangfolio/data/projects.js`
   ergänzen (Schema dort bereits definiert: `{ id, title, summary,
   description, tags, demoUrl, repoUrl, status, coldStartNote? }`).
4. Kurze Rücksprache mit Marco, ob alles passt, bevor die nächste
   Backlog-Session das nächste Item (`cloud-native-pipeline`, aktuell
   nächsthöchste Priorität) aufgreift.

## Wo was liegt

- `docs/superpowers/specs/` — Design-Spec (Ausgangspunkt für alle
  Design-Entscheidungen)
- `docs/superpowers/plans/` — Implementierungsplan (10 Tasks, Detail-Code
  pro Task)
- `docs/annex3-mapping.md` — Rechtsgrundlagen-Mapping (aus der finalen
  Review nachträglich ergänzt, war in der Spec versprochen, aber im Plan
  vergessen)
- `docs/index.html` — GitHub-Pages-Landingpage (siehe oben)
- `CLAUDE.md` — Projektkontext + laufend aktueller Stand, für den
  Arbeitsstil (Deutsch + Lehrstil)
