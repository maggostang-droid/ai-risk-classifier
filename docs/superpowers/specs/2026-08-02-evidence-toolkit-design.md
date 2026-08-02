# Design: vom Risk Classifier zum AI Act Evidence Toolkit

**Datum:** 2026-08-02
**Status:** abgestimmt, bereit für den Implementierungsplan
**Vorgänger-Spec:** `2026-07-28-ai-act-validation-toolkit-design.md` (bleibt gültig für
den deterministischen Regelbaum, wird durch dieses Dokument in den Bereichen
metamorphes Testen und Governance-Artefakt abgelöst)

## Warum überhaupt ein Umbau

Das Projekt in seiner heutigen Form verkauft sich unter Wert, und zwar aus drei
konkreten Gründen:

1. **Der „Classifier" klassifiziert nicht.** `risk_engine.py` ist eine `if`/`elif`-Kette
   mit fünf Zweigen, davor sechs Checkboxen, die aus drei fest verdrahteten Use Cases
   vorbelegt werden. Wer die Demo öffnet, kann seinen eigenen Fall nicht eingeben. Der
   Name verspricht mehr als das Artefakt liefert.

2. **Der metamorphe Test kann nicht fehlschlagen.** Die ausgelieferte SUT ist
   `20 + 2,5·Δaußen + 3·Δkabine + 1,5·n` — konstruktionsbedingt monoton. Der Button
   wird immer grün. Ein Test, der nie rot werden kann, liest sich als Deko.
   `HANDOVER.md` markiert genau das seit dem 2026-07-28 als verpassten Beweismoment.

3. **Die beiden Hälften berühren sich nie.** `governance.py` enthält eine Konstante:
   dieselben sieben leeren Checkboxen (Art. 9–15) für jeden Fall. Das Ergebnis des
   metamorphen Tests steht als Absatz daneben, hakt aber Art. 15 nicht ab — obwohl es
   genau der Nachweis dafür wäre.

Dazu kommt eine schiefe Stelle im Inhalt: das Komfortsystem ist Hochrisiko **wegen
Art. 6(1)** (Sicherheitsbauteil, Sitzgeometrie/Rückhaltesystem), getestet wird aber die
**Kühlintensität** — eine Komfortfunktion. Die Relation prüft nicht die Eigenschaft, die
die Einstufung ausgelöst hat.

### Was erhalten bleibt

Die zentrale Architekturentscheidung — **das LLM darf nicht klassifizieren** — ist
richtig und bleibt unangetastet. `risk_engine.py` behält seine Null-LLM-Abhängigkeit,
das LLM formuliert weiterhin ausschließlich einen Prosa-Satz und wird in diesem Umbau
nicht ausgebaut.

## Die Umdeutung

Das Produkt beantwortet ab jetzt eine andere Frage.

Bisher: *„In welche Klasse fällt mein System?"* — das kann jede Kanzlei-Checkliste.

Neu: *„Ich bin Hochrisiko. Womit belege ich das technisch?"* — genau da hört jedes
andere AI-Act-Tool auf.

Diese Lücke zwischen Compliance-Häkchen und tatsächlichem technischem Nachweis ist der
Gegenstand von Marcos Promotion (Dr.-Ing., KIT/ITIV, 2019–2025: „Validierung von
KI-Systemen durch Verknüpfung von Szenarien und metamorphes Testen"). Sie auszuspielen
ist der eigentliche Zweck dieses Umbaus.

### Warum metamorphes Testen hier zwingend hingehört

Der AI Act verlangt für Hochrisiko-Systeme genau das, was metamorphes Testen liefert:

- **Art. 9(7)** — Testen gegen vorab definierte Metriken und probabilistische Schwellen,
  vor dem Inverkehrbringen.
- **Art. 15** — angemessenes Maß an Genauigkeit und Robustheit über den Lebenszyklus.
- **Art. 10(2)(f)(g)** — Untersuchung auf mögliche Verzerrungen (Bias) in den Daten.
- **Annex IV Nr. 2(g)** (technische Doku nach Art. 11) — „die verwendeten Validierungs-
  und Testverfahren … und die Metriken zur Messung von Genauigkeit und Robustheit".

Das Gesetz sagt also *dass* man Robustheit nachweisen muss, aber nicht *wie*. Bei einem
KI-System scheitert der naive Weg am Orakel-Problem: die richtige Ausgabe ist unbekannt.
Metamorphes Testen ist die anerkannte Antwort darauf. Die Kette
*Einstufung → Art. 15 → Orakel-Problem → metamorphes Testen → ausgeführter Nachweis*
ist keine Konstruktion, sondern die tatsächliche fachliche Logik.

Der Test wirkte bisher nur deshalb angeklebt, weil das Bindeglied fehlte: der Schritt,
der aus der Klasse konkrete Pflichten ableitet.

## Der neue Ablauf

Vier Schritte, jeder sichtbar aus dem vorigen folgend:

```
1. Einstufung   Fragebogen → deterministischer Regelbaum → Risikoklasse
2. Pflichten    Klasse → konkrete Artikelpflichten, jede mit leerem Evidenz-Slot   ← NEU
3. Nachweis     Relations-Suite gegen die SUT, Fehlerinjektion, Kill-Matrix
4. Artefakt     Checkliste, teils mit echter Evidenz gefüllt, teils ehrlich offen
```

Schritt 2 existiert heute nicht. Er ist der Grund, warum Schritt 3 und Schritt 4
aktuell nebeneinanderher laufen.

### Der Ehrlichkeits-Move in Schritt 4

Von den sieben Hochrisiko-Pflichten kann dieses Tool

- **Art. 15** (Robustheit) und **Art. 10(2)(f)(g)** (Bias-Prüfung) mit ausgeführter
  Evidenz belegen,
- **Art. 9(7)** (Testen gegen vorab definierte Kriterien) und **Art. 11 / Annex IV 2(g)**
  (dokumentiertes Testverfahren) teilweise,
- **Art. 12, 13, 14** (Logging, Betriebsanleitung, menschliche Aufsicht) gar nicht —
  das sind Prozesspflichten.

Das steht so im generierten Artefakt. Ein Werkzeug, das seine eigenen Grenzen benennt,
wirkt kompetenter als eines mit sieben leeren Kästchen.

## Die zwei Systeme unter Test

### SUT 1 — Komfortsystem, korrigiert

Neue Funktion `decide_seat_recline_angle(...)`, an der die sicherheitsrelevanten
Relationen hängen — passend zu Art. 6(1), der die Einstufung auslöst. Die bestehende
Klimafunktion `decide_cooling_intensity(...)` bleibt als zweite, harmlosere SUT
erhalten und bekommt zusätzliche Relationen.

### SUT 2 — Bewerber-Scoring, das neue Herzstück

Ein Scorer nimmt Berufsjahre, Skill-Match, Ausbildung und den Namen und gibt 0–100
zurück. Zwei Varianten:

- `score_applicant_naive` enthält den Klassiker-Fehler: ein aus dem Vornamen
  abgeleitetes Feature. In echten Systemen kommt so etwas über korrelierte Proxys
  herein; hier steht es bewusst explizit im Code, damit man es lesen kann.
- `score_applicant_fixed` ohne dieses Feature.

Die Relation: **tausche im Bewerbungsprofil nur den Namen — der Score muss identisch
bleiben.** Die naive Variante fällt sichtbar durch, die gefixte besteht.

Das ist der Beweismoment für einen Betrachter, der 30 Sekunden Zeit hat. „Name
geändert, Score um 12 Punkte gefallen" versteht jeder sofort; Temperatur-Monotonie
versteht er nicht. Und es verbindet Annex III (Beschäftigung) → Art. 10 (Bias-Prüfung)
→ ausgeführten Nachweis in einer geraden Linie. Nebenbei hört der Recruiting-Use-Case
auf, bloße Tabellenzeile zu sein.

**Framing im README:** Der naive Scorer ist ein absichtlich fehlerhaftes
Demonstrationsobjekt, dessen Zweck es ist, vom Test gefangen zu werden. Das muss so
dastehen, damit niemand ihn für einen Vorschlag hält.

### Relations-Suite statt einer Relation

Je SUT etwa vier Relationen:

| SUT | Relationen |
|---|---|
| Sitzverstellung | Monotonie, Permutationsinvarianz (Insassenreihenfolge), Einheiteninvarianz (°C ↔ °F), Sättigungsgrenze |
| Klima | Monotonie, Einheiteninvarianz, Sättigungsgrenze |
| Bewerber-Scoring | Namensinvarianz, Monotonie in den Berufsjahren, Skalierungsinvarianz |

Jede Relation trägt neu ein Feld `evidence_for` (`"Art. 15"`, `"Art. 10"`). Das ist die
technische Kopplung zwischen Schritt 3 und Schritt 4.

### Kill-Matrix

Eine Handvoll absichtlich eingebauter Fehler pro SUT (Vorzeichenfehler, Variable
ignoriert, Sprung an der Schwelle, fehlender Clip) wird gegen jede Relation gefahren:

```
                       Vorzeichen  Var. ignoriert  Schwellensprung  Rundungsfehler
Monotonie                getötet       überlebt        getötet          überlebt
Permutationsinvarianz    überlebt      getötet         überlebt         überlebt
Einheiteninvarianz       überlebt      überlebt        überlebt         überlebt
Sättigungsgrenze         überlebt      überlebt        getötet          überlebt

Mutation Score: 3/4 — „Rundungsfehler" überlebt die gesamte Suite
```

Ein Mutant gilt als getötet, sobald ihn **mindestens eine** Relation fängt; der Score
zählt daher Mutanten, nicht Zellen.

Damit hat das Projekt eine ehrliche Zahl — und zwar genau die, die das README heute
noch wegargumentieren muss („klassische ML-Metriken wie F1 gibt es hier nicht und wären
auch sinnlos"). Für einen deterministischen Regelbaum stimmt das weiterhin; für die
Relations-Suite stimmt es nicht, denn deren Güte *ist* messbar.

Der überlebende Mutant ist kein Makel, sondern der interessanteste Teil des Artefakts:
er zeigt die Blindstelle der Relationsmenge. Dazu gehört die Gegenprobe, dass die
korrekte SUT **alle** Relationen besteht — sonst wäre die Matrix wertlos.

## Modulschnitt

```
src/ai_act_toolkit/
  risk_engine.py         unverändert — Klasse + matched_rule
  obligations.py         NEU   Klasse+Regel → Pflichtenliste mit evidence_kind
  use_cases.py           erweitert — verweist auf die SUT-Registry statt auf ein bool
  metamorphic/
    __init__.py
    core.py              ex metamorphic.py — Relation, Result, run_relation
    suite.py             NEU   run_suite(): alle Relationen einer SUT auf einmal
    mutation.py          NEU   Mutant, run_kill_matrix(), mutation_score()
  suts/
    __init__.py          NEU   Registry: use_case.key → SUTSpec
    comfort_seat.py      NEU   decide_seat_recline_angle + Relationen
    comfort_climate.py   ex comfort_system_sut.py, um weitere Relationen ergänzt
    recruiting_scorer.py NEU   naive/fixed + Namensinvarianz-Relation
  governance.py          umgebaut — Pflichten + Evidenz statt Konstante
  llm.py, rationale.py   unverändert
app.py                   vier klar getrennte Schritte statt einer flachen Liste
```

### Datenstrukturen

Drei Strukturen tragen den ganzen Umbau:

```python
# obligations.py
class EvidenceKind(Enum):
    TECHNICAL_TEST = "technical_test"   # durch Relationen belegbar
    DOCUMENTATION  = "documentation"    # teilweise, Artefakt zahlt darauf ein
    PROCESS        = "process"          # organisatorisch, hier nicht belegbar

@dataclass(frozen=True)
class Obligation:
    article: str            # "Art. 15"
    title: str
    description: str
    evidence_kind: EvidenceKind

def obligations_for(classification: ClassificationResult) -> list[Obligation]: ...
```

```python
# suts/__init__.py
@dataclass(frozen=True)
class SUTSpec:
    key: str
    label: str
    fn: Callable[..., float]
    baseline_inputs: dict
    relations: list[MetamorphicRelation]
    mutants: list[Mutant]

SUT_REGISTRY: dict[str, list[SUTSpec]]   # use_case.key → SUTs
```

```python
# metamorphic/mutation.py
@dataclass(frozen=True)
class Mutant:
    key: str
    label: str
    defect: str                      # was genau kaputt ist
    fn: Callable[..., float]
    expected_survivor: bool = False  # dokumentierte Blindstelle

@dataclass(frozen=True)
class KillMatrix:
    relations: list[MetamorphicRelation]
    mutants: list[Mutant]
    killed: dict[tuple[str, str], bool]   # (relation.name, mutant.key) → getötet?

    @property
    def score(self) -> tuple[int, int]: ...   # (getötet, gesamt)
```

`MetamorphicRelation` in `metamorphic/core.py` bekommt ein zusätzliches Feld
`evidence_for: str`.

### Rendering der Pflichtzeilen

`governance.py` gruppiert die Suite-Ergebnisse nach `evidence_for` und rendert jede
Pflicht in einem von drei Zuständen:

```
- [x] Art. 15  Robustheit             belegt — Suite 4/4 bestanden, Mutation Score 3/4
- [~] Art. 11  Technische Doku        teilweise — Testverfahren nach Annex IV 2(g) dokumentiert
- [ ] Art. 14  Menschliche Aufsicht   Prozesspflicht, durch dieses Tool nicht belegbar
```

Die Kill-Matrix wird als Markdown-Tabelle unter Annex IV 2(g) in das Artefakt
eingebettet.

## UI

Schritt 3 bekommt ein `selectbox` „Fehler injizieren: (keiner) / Vorzeichenfehler /
Variable ignoriert / …". Die Suite läuft live gegen die gewählte Variante, die
betroffenen Relationen kippen sichtbar auf Rot, darunter steht die volle Kill-Matrix
als Tabelle.

Kein neues Runtime-Dependency: pandas kommt bereits über Streamlit.

Die `session_state`-Keys werden um SUT und injizierten Fehler erweitert. Das in
`HANDOVER.md` geparkte „Keys werden nie bereinigt" wächst damit von harmlos zu
unübersichtlich und wird in diesem Zug mit einem kleinen Helfer erledigt, der beim
Wechsel des Use Case die veralteten Keys verwirft.

## Testplan

Von 17 auf etwa 50 Tests. Die bestehenden 17 bleiben inhaltlich unverändert und
brauchen nur neue Importpfade.

| Test | Zweck |
|---|---|
| Jede Relation × jede korrekte SUT → besteht | eine Relation, die auf korrektem Code feuert, ist selbst kaputt |
| Jeder Mutant mit `expected_survivor=False` → von ≥1 Relation getötet | die Suite fängt, was sie fangen soll |
| Jeder deklarierte Überlebende → von **keiner** Relation getötet | sperrt die dokumentierte Blindstelle: wer eine Relation nachrüstet, muss die Doku mitziehen |
| `score_applicant_naive` verletzt Namensinvarianz, `_fixed` nicht | das Kernstück explizit festgenagelt |
| Kill-Matrix: Form und Score | die Metrik selbst |
| `obligations_for()` liefert für Hochrisiko Art. 9–15, für begrenztes Risiko nur Art. 50 | die neue Ableitung |
| Artefakt hakt Art. 15 nur ab, wenn die Suite tatsächlich lief | die Kopplung, nicht nur die Teile |
| Prozesspflichten bleiben im Artefakt offen | verhindert Schönfärberei durch spätere Änderungen |
| AppTest: Fehlerinjektion ändert das angezeigte Ergebnis | der Beweismoment in der UI |

Der dritte Punkt verdient Hervorhebung: ein Test, der Ehrlichkeit in der Dokumentation
erzwingt. Fügt jemand später eine Relation hinzu, die den bisher überlebenden Mutanten
fängt, schlägt der Test fehl und zwingt dazu, README und Blindstellen-Abschnitt
nachzuziehen.

Alle Tests laufen weiterhin ohne Netzwerk und ohne LLM-Zugriff.

## CI

`.github/workflows/ci.yml`: ruff + pytest auf Push und Pull Request. Badge aus dem
Workflow statt der handgepflegten „17 passing"-Grafik. Ruff-Konfiguration nach
`pyproject.toml` (`CLAUDE.md` vermerkt aktuell „Kein Linter konfiguriert").

Bei einem Projekt über Validierung ist fehlendes CI die Pointe, die man sich sonst
erzählen lässt.

## Name

„AI Risk Classifier" bewirbt die schwächere Hälfte. Neuer Produktname:
**AI Act Evidence Toolkit** — passt zum Portfolio-Muster (SQL Copilot, Review Risk
Predictor, Document Auto-Classifier) und zum bereits bestehenden Paketnamen
`ai_act_toolkit`.

Geändert wird nur der *Produktname* in README, App-Header, `docs/index.html` und
`../marco-os/data/projects.js`. Der Repo-Slug `ai-risk-classifier` bleibt: er bringt
wenig und ein Rename streut Bruchstellen über die Streamlit-Deployment-Konfiguration
und die Querverweise in den Schwesterprojekten. Die Projekt-`id`
`ai-act-validation-toolkit` in `projects.js` bleibt ebenfalls unverändert, sonst
brechen die Deep-Links `#ai-act-validation-toolkit`.

## README

- Neuer Claim entlang der Kette Pflicht → Nachweis.
- Kill-Matrix als Heldenbild statt des statischen Screenshots.
- Der 2/2/3-Pflichtensplit ersetzt den Absatz, der heute wegargumentiert, warum es
  keine Metriken gibt.
- Ein Demo-GIF vom Namenstausch wäre stärker als das PNG. Das muss Marco aufnehmen,
  eine Agenten-Session kann es nicht erzeugen.
- Der Abschnitt „Was dieses Projekt nicht ist" bleibt und wird um die bekannte
  Blindstelle der Relationsmenge ergänzt.

## Bewusst weggelassen

- **Kein Freitext-Input, keine LLM-Attributextraktion.** Wäre die naheliegende
  Erweiterung, ist aber ein eigenes Vorhaben mit eigenem Gold-Set und eigener
  Messmethodik.
- **Kein GPAI / Art. 51–55**, keine Annex-III-Unterpunkte, keine Fristen-Timeline.
- **Keine property-based Szenariensuche** (Hypothesis). Sie ist die konsequente
  Fortsetzung Richtung Promotionsthema und lässt sich später an genau einer Stelle
  nachrüsten — dem Quellfall-Generator in `suite.py` — ohne etwas aus diesem Design
  umzubauen.
- **Das LLM wird nicht ausgebaut.** Ein optionaler Prosa-Satz, mehr nicht.
- **Kein neues Runtime-Dependency.**

## Risiken

- Drei Modulumzüge (`metamorphic.py` → `metamorphic/core.py`,
  `comfort_system_sut.py` → `suts/comfort_climate.py`, `use_cases.has_metamorphic_demo`
  → SUT-Registry) brechen bestehende Importe und Tests. Mechanisch, aber breit gestreut
  — sollte als eigener, früher Task laufen, damit die Suite dazwischen nie lange rot ist.
- `governance.generate_governance_artifact()` ändert seine Signatur. Einziger Aufrufer
  ist `app.py`, plus `tests/test_governance.py`.
- Der naive Scorer braucht sorgfältiges Framing im README, damit er nicht als Vorschlag
  missverstanden wird.

## Umfang

Etwa 3–4 Tage — dasselbe Budget wie der ursprüngliche Bau.
