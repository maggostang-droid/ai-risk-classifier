# ai-act-validation-toolkit — Design

Erstellt: 2026-07-28
Status: freigegeben durch Marco (Brainstorming-Session)
Backlog-Referenz: `PORTFOLIO_BACKLOG.md`, Abschnitt 0 (höchste Priorität)

## Was das hier ist

Portfolio-Projekt von Marco Stang für Bewerbungen auf AI/KI-Rollen (ggf. auch
KI-Transformations-Rollen). Ein Tool, das einen beschriebenen KI-Use-Case
nach EU-AI-Act-Risikoklasse (Annex III) einordnet und für high-risk-Fälle
eine metamorphe Test-Suite + ein Governance-Artefakt generiert/ausführt —
eine anwendbare Miniatur-Version von Marcos Promotionsthema ("Validierung
von KI-Systemen durch Verknüpfung von Szenarien und metamorphes Testen",
KIT/ITIV, Mercedes-Benz-Kooperation zu autonomen Fahrzeug-Komfortsystemen).

**Warum:** Einzigartiger Fit (keine andere Bewerbung bringt eine
einschlägige Dr.-Ing.-Forschung mit) und akut zeitrelevant — EU-AI-Act-
Enforcement für High-Risk-Systeme beginnt 2026-08-02.

**Bewusst weggelassen:** Rechtsverbindliche Compliance-Aussagen oder
Vollständigkeitsanspruch ggü. echtem AI-Act-Audit (kein Ersatz für
juristische Beratung); Freitext-Use-Case-Eingabe mit LLM-Attribut-Extraktion
(unnötige Nichtdeterminismus-Quelle bei der Klassifizierung selbst);
generisches Metamorphic-Testing-Framework für beliebige Use-Case-Typen
(würde das 3-4-Tage-Budget sprengen).

## Lernstil

Deutsch + Lehrstil wie bei `sql-agent`/`goz-finetune-vs-rag` — Marco lernt
aktiv mit, Konzepte erklären statt vorlösen, ausführlichere Kommentare bei
neuen/unbekannten Teilen (z.B. Streamlit-Aufbau), alle Doku auf Deutsch.

## Architektur

Python-Package + Streamlit-App, gleiches Grundmuster wie `sql-agent`:

```
src/ai_act_toolkit/
  risk_engine.py        # deterministischer Annex-III-Regelbaum: Attribute -> Risikoklasse
  use_cases.py           # 3 Beispiel-Use-Cases als strukturierte Attribut-Sets
  rationale.py           # LLM generiert Klartext-Begründung aus risk_engine-Output
  comfort_system_sut.py  # Toy-"System unter Test": simuliertes Komfortsystem
  metamorphic.py         # 1 metamorphe Relation, echt ausgeführt gegen die SUT
  governance.py          # generiert Markdown Risk-Assessment + Konformitätscheckliste
  llm.py                 # wiederverwendetes Muster aus sql-agent (LLM_PROVIDER/LLM_MODEL via LangChain init_chat_model)
app.py                   # Streamlit-UI (Root-Level, wie bei goz-finetune-vs-rag)
tests/                   # pytest: risk_engine, metamorphic.py, governance.py — kein LLM/Netzwerk nötig
docs/annex3-mapping.md   # dokumentiert Fragebogen-Kriterien <-> Annex-III-Kategorien
```

## Beispiel-Use-Cases (3, fest hinterlegt in `use_cases.py`)

1. **Autonomes Fahrzeug-Komfortsystem** (Automotive, high-risk) — direkter
   Bezug zur Mercedes-Kooperation aus der Promotion. Einziger Use Case mit
   ausgeführtem metamorphem Test (siehe unten).
2. **KI-gestützte Bewerber-Vorauswahl** (Recruiting, high-risk, Annex III
   Nr. 4 Beschäftigung) — Kontrastbeispiel aus einer anderen Branche.
3. **Kundenservice-Chatbot** (limited-risk, Transparenzpflichten Art. 50) —
   Kontrastbeispiel für eine niedrigere Risikoklasse.

## User-Flow

1. **"Was macht das hier in 30 Sekunden"** — kurzer Erklärblock ganz oben
   in der App (1-2 Sätze Alltagssprache: "Dieses Tool sagt dir, ob dein
   KI-System als 'Hochrisiko' nach dem EU AI Act gilt — und beweist das an
   einem live ausgeführten Test."), damit der Nutzen vor allen
   Fachbegriffen erkennbar ist. Gleicher Einstieg auch als erster
   README-Abschnitt.
2. Nutzer wählt einen der 3 Beispiel-Use-Cases. Ein vorausgefüllter
   Fragebogen (Checkboxen/Dropdowns zu Annex-III-Kriterien) erscheint und
   ist **live editierbar** — Änderung eines Attributs löst sofort eine neue
   Klassifizierung aus (zeigt: echter Klassifizierer, keine
   Lookup-Tabelle).
3. Ergebnis wird als **Ampel** (rot/gelb/grün + Textlabel) angezeigt, nicht
   nur als Text — schneller erfassbar als reine Klassenbezeichnung.
   `risk_engine.py` liefert die Klasse deterministisch, `rationale.py` lässt
   ein LLM nur die Begründung in Klartext formulieren (kein Blackbox-Risiko
   bei der eigentlichen Klassifizierung).
4. **Nur beim Automotive-Use-Case (high-risk):** Abschnitt "Metamorpher
   Test" — eine konkrete Relation (Monotonie: steigt die Außentemperatur bei
   sonst gleichen Bedingungen, darf die Ziel-Kühlintensität nicht sinken)
   wird per Button-Klick gegen `comfort_system_sut.py` mit Quell- und
   Folgefall **tatsächlich ausgeführt**; Ergebnis (bestanden/fehlgeschlagen
   + konkrete Ausgabewerte) wird live angezeigt.
5. **Bei high-risk-Use-Cases:** Governance-Artefakt — Markdown-Dokument mit
   Systembeschreibung, Klassifizierung+Begründung, anwendbaren Pflichten
   (Art. 9-15 AI Act: Risikomanagement, Datengovernance, technische Doku,
   Transparenz, menschliche Aufsicht, Robustheit), Konformitätscheckliste,
   Metamorphic-Test-Ergebnis (falls vorhanden) — in-App lesbar **und** als
   `.md`-Datei herunterladbar.

## Testing

- `tests/test_risk_engine.py` — deterministische Klassifizierung für
  bekannte Attribut-Kombinationen (inkl. Grenzfälle zwischen den Klassen).
- `tests/test_metamorphic.py` — Relation-Runner-Logik gegen die Toy-SUT
  (bestehender Fall + gezielt kaputter Fall, der die Relation verletzt).
- `tests/test_governance.py` — Artefakt enthält alle Pflichtabschnitte für
  einen high-risk-Fall.
- Kein LLM/Netzwerk in der Test-Suite nötig (wie bei `sql-agent`).

## Deployment

Streamlit Community Cloud (kostenlos, direkt an public GitHub-Repo
angebunden) — Live-Link fürs Portfolio, zusätzlich lokal startbar wie die
anderen 4 Projekte.

## Definition of Done

- Live-Demo (Streamlit Community Cloud) für alle 3 Beispiel-Use-Cases mit
  Risikoklassen-Herleitung.
- Mindestens ein metamorpher Test konkret ausgeführt (Automotive-Use-Case).
- Governance-Artefakt in-App + als Download für high-risk-Fälle.
- README erklärt Bezug zur Promotion + AI-Act-Fristen, führt mit dem
  30-Sekunden-Nutzenversprechen.
- `pytest` grün ohne LLM/Netzwerk-Abhängigkeit.
