# AI Act Evidence Toolkit

**Stuft eine KI-Anwendung nach dem EU AI Act ein, leitet daraus die konkreten
Artikelpflichten ab und führt für die technisch belegbaren davon einen metamorphen Test
live aus. Die Einstufung selbst trifft ein deterministischer Regelbaum, nicht das LLM.**

![Python](https://img.shields.io/badge/Python-3.10+-fbbf24?style=flat-square&labelColor=0a0716)
![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Annex_III-fbbf24?style=flat-square&labelColor=0a0716)
[![CI](https://github.com/marco-stang/ai-risk-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/marco-stang/ai-risk-classifier/actions/workflows/ci.yml)
[![Live-Demo](https://img.shields.io/badge/▶_Live--Demo-Streamlit-0a0716?style=flat-square&labelColor=fbbf24)](https://ai-act-validation-toolkit.streamlit.app/)

> **▶ [Demo ausprobieren](https://ai-act-validation-toolkit.streamlit.app/)**
> Wähle die Bewerber-Vorauswahl und injiziere in Schritt 3 den Fehler „Vom Vornamen
> abgeleitetes Merkmal". Der Test kippt auf Rot, und in der Konformitätscheckliste
> fällt Art. 10 zurück auf „offen".
> *Streamlit Free Tier: der erste Aufruf kann ein paar Sekunden zum Aufwachen brauchen.*

![Im korrekten System bekommen Maximilian und Kevin denselben Score von 85, die Namensinvarianz-Relation ist bestanden und Art. 10 in der Konformitätscheckliste abgehakt. Nach Injektion des Namensmerkmal-Fehlers fällt der Score von 91 auf 79, die Relation schlägt fehl und Art. 10 fällt zurück auf offen.](docs/demo.gif)

<details>
<summary><b>🇬🇧 English summary</b></summary>

Most EU AI Act tools stop at "you are high-risk, good luck." This one continues: the
classification (a deterministic Annex III rule tree — an LLM only phrases the rationale
and cannot influence the outcome) produces a list of concrete article obligations, and
for the technically provable ones it runs a real metamorphic test suite against three
simulated systems under test. Deliberately seeded faults can be injected live, and a
kill matrix reports how many of them the relation suite actually catches. The resulting
governance artefact ticks off only what was genuinely proven. A miniature of the
author's doctoral research (KIT/ITIV). Full write-up in German below.
</details>

---

## In 30 Sekunden

Seit dem 2. August 2026 gilt die Enforcement-Pflicht für Hochrisiko-Systeme nach dem EU AI
Act. Die Einstufung selbst ist der leichte Teil — das kann jede Kanzlei-Checkliste. Die
schwierige Frage kommt danach: **womit belegst du technisch, dass dein System die
Pflichten erfüllt?** Genau da hört jedes andere AI-Act-Werkzeug auf.

Es ist die anwendbare Miniatur-Version von Marcos Promotionsthema (Dr.-Ing., „Sehr gut",
KIT/ITIV, 2019 bis 2025): „Validierung von KI-Systemen durch Verknüpfung von Szenarien und
metamorphes Testen", erprobt in einer Industriekooperation mit Mercedes-Benz zu autonomen
Fahrzeug-Komfortsystemen.

## Der Beweismoment

Wähle in der Demo die Bewerber-Vorauswahl und injiziere in Schritt 3 den Fehler „Vom
Vornamen abgeleitetes Merkmal". Im Bewerbungsprofil ändert sich daraufhin nichts außer
dem Vornamen — der Score fällt trotzdem von 91 auf 79.

Genau das ist metamorphes Testen: geprüft wird nicht eine einzelne Ausgabe gegen ein
bekanntes Sollergebnis (das ist bei KI-Systemen meist unbekannt, das Orakel-Problem),
sondern eine *Beziehung* zwischen zwei Ausgaben. Der Score darf sich nicht ändern, wenn
sich nur der Name ändert. Tut er es doch, ist ein sachfremdes Merkmal in die Entscheidung
geraten — und Art. 10(2)(f)(g) AI Act verlangt genau diese Untersuchung auf Verzerrungen.

Das Entscheidende passiert danach: in der Konformitätscheckliste fällt **Art. 10 von
`[x] belegt` zurück auf `[ ] offen`**. Der Test hängt nicht neben der Checkliste, er ist
das, was sie abhakt.

Der naive Scorer in [`suts/recruiting_scorer.py`](src/ai_act_toolkit/suts/recruiting_scorer.py)
ist ein absichtlich fehlerhaftes Demonstrationsobjekt, dessen Zweck es ist, vom Test
gefangen zu werden — kein Vorschlag, wie man ein Scoring baut.

## Die zentrale Entscheidung: das LLM darf nicht klassifizieren

Bei einem Compliance-Werkzeug ist Nachvollziehbarkeit wichtiger als Sprachgewandtheit. Ein
LLM, das die Risikoklasse selbst bestimmt, wäre bei identischer Eingabe nicht garantiert
reproduzierbar, und genau das ist bei einer Rechtsfrage untragbar. Deshalb steht die Klasse
fest, *bevor* ein LLM überhaupt aufgerufen wird: `risk_engine.py` hat keinerlei
LLM-Abhängigkeit, die Regel-Priorität ist Art. 5 (verboten), dann Art. 6(1)
(Sicherheitsbauteil), dann Art. 6(2) mit Annex III inklusive der Art.-6(3)-Ausnahme, dann
Art. 50 (Transparenz), sonst minimal.

Das LLM bekommt das fertige Ergebnis nur zur Übersetzung in Prosa gereicht. Fällt es aus,
weil das Netzwerk weg ist, der Key ungültig oder das Rate-Limit erreicht, zeigt die App
einen Hinweis statt eines Absturzes und erzeugt das Governance-Artefakt trotzdem, mit
einem Fallback-Text aus der deterministischen Regel.

<details>
<summary><b>▸ Deep Dive: warum es eine Kill-Matrix braucht, nicht nur einen grünen Test</b></summary>

Ein bestandener metamorpher Test sagt für sich genommen wenig. Er könnte auch bestehen,
weil die Relation gar nichts prüft. Deshalb läuft gegen jede Relations-Suite eine Reihe
absichtlich fehlerhafter Varianten des Systems unter Test — „Mutanten". Ein Mutant gilt
als getötet, sobald ihn mindestens eine Relation fängt.

Für das Bewerber-Scoring sieht das so aus:

| Relation | Namensmerkmal | Erfahrung ignoriert | Vorzeichen Skill | Clip fehlt | Rundung |
|---|---|---|---|---|---|
| Namensinvarianz | **getötet** | überlebt | überlebt | überlebt | überlebt |
| Berufsjahre-Monotonie | überlebt | **getötet** | überlebt | überlebt | überlebt |
| Skill-Monotonie | überlebt | überlebt | **getötet** | überlebt | überlebt |
| Sättigungsgrenze | überlebt | überlebt | überlebt | **getötet** | überlebt |

**Mutation Score 4/5.** Über alle drei Systeme unter Test: **11/14.**

Der überlebende Mutant ist der interessanteste Teil. Rundung auf ganze Punkte verletzt
keine der vier Relationen — das ist die Blindstelle dieser Relationsmenge, und sie steht
so im generierten Artefakt. Ein Test in der Suite nagelt sie fest: rüstet jemand später
eine Relation nach, die diesen Mutanten fängt, schlägt der Test fehl und erzwingt, dass
die Dokumentation mitgezogen wird.

Zwei Relationsarten tragen dabei besonders viel. **Unabhängigkeitsrelationen** („der Name
darf den Score nicht beeinflussen", „das Gewicht nicht den Lehnenwinkel") fangen
sachfremde Merkmale. **Strenge Monotonie** („ein größerer Insasse muss echt mehr Winkel
bekommen") fängt ignorierte Eingangsgrößen — nicht-strenge Monotonie ließe eine komplett
ignorierte Variable anstandslos durch. Beides zeigt sich erst an der Kill-Matrix.

Ein Detail aus dem Bau, das dasselbe Prinzip illustriert: das Basisprofil des Scorers
steht auf `education_level=4`, nicht 3. Bei 3 rechnet die Vorzeichenfehler-Variante
`10+15−40+15 = 0` und wird von der unteren Clip-Grenze gehalten — Quell- und Folgefall
wären beide 0, und die Skill-Monotonie sähe den Defekt nicht. Ein Baselinepunkt im
Sättigungsbereich macht eine Relation blind. Aufgefallen ist das nicht beim Nachdenken,
sondern weil der Kill-Matrix-Test rot wurde.

Alle Tests laufen ohne Netzwerk und ohne LLM-Zugriff, kein Mock ersetzt echtes Verhalten.
Die Zuordnung jedes Fragebogen-Kriteriums zur jeweiligen Rechtsgrundlage steht in
[`docs/annex3-mapping.md`](docs/annex3-mapping.md).
</details>

## Architektur

![Use Case und Fragebogen gehen in den deterministischen Regelbaum, daraus folgt die Risikoklasse. Aus der Klasse leitet obligations.py die Artikelpflichten ab; für die technisch belegbaren läuft die Relations-Suite mit Mutanten und Kill-Matrix. Pflichten und Evidenz laufen im Governance-Artefakt zusammen, das nur abhakt was belegt wurde. Das LLM hängt als Seitenzweig an der Klasse und formuliert nur Prosa.](docs/architecture.svg)

Der entscheidende Knoten ist `obligations.py`. Ohne ihn stünden Einstufung und
metamorpher Test nur nebeneinander — er ist es, der aus einer Risikoklasse eine Liste
konkreter Artikelpflichten macht, von denen jede weiß, ob sie überhaupt technisch
belegbar ist. Erst dadurch hat die Relations-Suite ein Ziel und das Artefakt etwas zum
Abhaken.

Bewusst schlank gehalten: kein Frontend-Framework, keine Datenbank, keine Vektor-DB,
kein neues Runtime-Dependency. Die Methodik aus Regelbaum, Relationen und
Mutationsanalyse soll im Vordergrund stehen, nicht die Infrastruktur.

## Was belegt werden kann, und was nicht

Von den sieben Hochrisiko-Pflichten kann dieses Werkzeug nur einen Teil technisch
belegen. Das steht so auch im generierten Artefakt — ein Werkzeug, das seine eigenen
Grenzen benennt, ist brauchbarer als eines mit sieben leeren Kästchen:

| Pflicht | Status | Womit |
|---|---|---|
| Art. 10 Daten und Data Governance | technisch belegt | Namensinvarianz-Relation |
| Art. 15 Genauigkeit und Robustheit | technisch belegt | Monotonie-, Invarianz- und Sättigungsrelationen |
| Art. 9 Risikomanagementsystem | teilweise | Art. 9(7): Testen gegen vorab definierte Kriterien |
| Art. 11 Technische Dokumentation | teilweise | Annex IV Nr. 2(g): dokumentiertes Testverfahren |
| Art. 12 Logging | nicht belegbar | Prozesspflicht |
| Art. 13 Betriebsanleitung | nicht belegbar | Prozesspflicht |
| Art. 14 Menschliche Aufsicht | nicht belegbar | Prozesspflicht |

Drei fest hinterlegte Use Cases decken die Bandbreite der Risikoklassen ab, mit drei
Systemen unter Test:

| Use Case | Risikoklasse | System unter Test | Mutation Score |
|---|---|---|---|
| Autonomes Fahrzeug-Komfortsystem | Hochrisiko (Art. 6(1)) | Sitzverstellung, Klimasteuerung | 4/5, 3/4 |
| KI-gestützte Bewerber-Vorauswahl | Hochrisiko (Annex III) | Vorauswahl-Scoring | 4/5 |
| Kundenservice-Chatbot | Begrenztes Risiko (Art. 50) | keines | — |

**74 Tests**, ohne Netzwerk oder LLM lauffähig, in CI bei jedem Push.

**Was dieses Projekt nicht ist:** Es liefert keine rechtsverbindliche Compliance-Aussage
und ersetzt weder juristische Beratung noch ein echtes Konformitätsbewertungsverfahren. Es
kennt nur die drei hinterlegten Use Cases, keinen Freitext-Import. Die Systeme unter Test
sind deterministische Stellvertreter-Modelle, keine echten ML-Modelle. Und die Relationen
laufen gegen einen festen Quellfall, nicht gegen einen gesuchten Szenarienraum — das wäre
die volle Verknüpfungsmethodik der Promotion und ist bewusst nicht Teil dieser Miniatur.

Klassische ML-Metriken wie F1 gibt es für den Regelbaum nicht und sie wären auch sinnlos:
er ist deterministisch, seine Korrektheit ist eine Frage der Rechtsauslegung, nicht der
Statistik. Für die Relations-Suite gibt es dagegen sehr wohl eine Metrik — den Mutation
Score. Er ist bewusst nicht 100 %: jede SUT hat einen deklarierten überlebenden Mutanten,
der die Blindstelle der Relationsmenge zeigt.

## Selbst ausprobieren

Einmalig: `python -m venv .venv` und `.venv/Scripts/python.exe -m pip install -e ".[dev]"`.

```bash
cp .env.example .env                          # LLM_PROVIDER, LLM_MODEL, API-Key eintragen
.venv/Scripts/python.exe -m pytest tests/ -v  # 74 Tests, ohne Netzwerk
.venv/Scripts/python.exe -m ruff check .      # Linter
.venv/Scripts/python.exe -m streamlit run app.py
```

---

```console
marco@portfolio:~$ open marco-os --project ai-act-validation-toolkit
```

**[▸ Dieses Projekt in MARCO.OS öffnen](https://marco-stang.github.io/#ai-act-validation-toolkit)**,
dem interaktiven Portfolio von Marco Stang.

**Schwesterprojekte:**
[SQL Copilot](https://github.com/marco-stang/sql-copilot) (LangGraph-Agent mit Guardrails) ·
[Review Risk Predictor](https://github.com/marco-stang/review-risk-predictor) (erklärbares ML, React/FastAPI) ·
[Ask-Marco Assistant](https://github.com/marco-stang/ask-marco-assistant) (Chat über alle Projekte)

<sub>Marco Stang · Dr.-Ing. · [LinkedIn](https://www.linkedin.com/in/marco-stang) · stang.marco@t-online.de · MIT-Lizenz</sub>
