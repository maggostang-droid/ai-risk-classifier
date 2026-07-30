# LEARNING-PATH.md — ai-act-validation-toolkit

Ziel dieses Dokuments: Marco kann dieses Projekt in einem
Bewerbungsgespräch auswendig, souverän und ehrlich vertreten — inklusive
kritischer Nachfragen. Alle Fakten unten sind gegen den tatsächlichen Code
in `src/ai_act_toolkit/`, `app.py`, `tests/` sowie `README.md`,
`HANDOVER.md`, `CLAUDE.md` und `docs/superpowers/specs/2026-07-28-ai-act-validation-toolkit-design.md`
geprüft. Wo etwas unklar oder ungetestet ist, steht das explizit da.

---

## 1. Elevator-Pitch (auswendig lernen)

> "Das Tool ordnet einen KI-Use-Case per deterministischem Regelbaum einer
> EU-AI-Act-Risikoklasse zu — ein LLM formuliert nur die Begründung in
> Klartext, die Klassifizierung selbst steht vorher schon fest. Für den
> Automotive-Use-Case beweise ich das nicht nur, sondern führe live einen
> echten metamorphen Test gegen ein simuliertes Komfortsystem aus — exakt
> das Prinzip aus meiner Promotion, hier auf einen konkret ausführbaren
> Fall reduziert. Für Hochrisiko-Fälle generiert das Tool zusätzlich ein
> Governance-Artefakt mit Konformitätscheckliste nach Art. 9–15 als
> Markdown-Download."

Zielgruppe: Recruiter/technische Interviewer für AI/KI- bzw.
KI-Transformations-Rollen. Kerninnovation: die Kombination aus (a) einer
rechtlich nachvollziehbaren, nicht-halluzinierenden Klassifizierung und
(b) einem tatsächlich ausgeführten (nicht nur behaupteten) metamorphen
Test — direkt abgeleitet aus Marcos Dissertation.

---

## 2. Architektur-Überblick

```
src/ai_act_toolkit/
  risk_engine.py         # deterministischer Regelbaum: UseCaseAttributes -> ClassificationResult
  use_cases.py            # 3 fest hinterlegte Beispiel-Use-Cases (Attribut-Sets)
  comfort_system_sut.py   # Toy-"System unter Test" + die Metamorphic Relation selbst
  metamorphic.py          # generischer run_relation()-Runner (Relation-agnostisch)
  governance.py           # generate_governance_artifact() — Markdown-Output
  llm.py                  # get_llm() — provider-agnostische LLM-Fabrik (LangChain init_chat_model)
  rationale.py            # generate_rationale() — einziger Ort, an dem das LLM aufgerufen wird
app.py                     # Streamlit-UI, verdrahtet alle Module zu einem User-Flow
tests/                     # 17 Tests, pytest, kein Netzwerk/LLM nötig
docs/annex3-mapping.md     # Fragebogen-Kriterium -> echte AI-Act-Rechtsgrundlage
```

Datenfluss (aus `README.md`, verifiziert gegen `app.py`):
`Fragebogen (UseCaseAttributes)` → `risk_engine.classify()` → `ClassificationResult`
→ optional `rationale.generate_rationale()` (LLM, nur Text) und/oder
`metamorphic.run_relation()` (nur beim Automotive-Use-Case) →
`governance.generate_governance_artifact()` (nur bei `HIGH_RISK`).

---

## 3. Stationen

### Station 1 — Der Regelbaum: `src/ai_act_toolkit/risk_engine.py`, Funktion `classify()`

Der Regelbaum ist eine simple, sequenzielle `if`-Kette mit **fester
Priorität**, keine Gewichtung, kein Scoring, kein ML:

1. `is_prohibited_practice` → `RiskClass.UNACCEPTABLE` (Art. 5) — gewinnt
   über alles andere (siehe `test_prohibited_practice_wins_over_everything_else`
   in `tests/test_risk_engine.py`).
2. `is_safety_component_regulated_product` → `RiskClass.HIGH_RISK` (Art.
   6(1) — Sicherheitsbauteil eines regulierten Produkts, Annex I).
3. `is_annex3_area AND significant_risk_to_health_safety_fundamental_rights`
   → `RiskClass.HIGH_RISK` (Art. 6(2) + Annex III, mit der
   Art.-6(3)-Rückausnahme als zusätzlicher UND-Bedingung).
4. `has_transparency_obligation` → `RiskClass.LIMITED_RISK` (Art. 50).
5. Sonst → `RiskClass.MINIMAL_RISK`.

**Warum deterministisch statt LLM-basiert?** Das ist die wichtigste
Design-Entscheidung im ganzen Projekt (explizit so im Design-Spec unter
"Bewusst weggelassen" begründet): Eine Rechtseinstufung mit realen
Konsequenzen (Compliance-Pflichten, im Zweifel Bußgelder) darf nicht von
einem Modell kommen, das *nicht reproduzierbar* ist. `classify()` ist eine
reine Funktion — gleiche `UseCaseAttributes` liefern *immer* dasselbe
Ergebnis, nachvollziehbar über `matched_rule` als Audit-Trail. Ein LLM
hätte hier zwei Probleme eingeführt, die bewusst vermieden wurden: (a)
Nichtdeterminismus bei einer Entscheidung, die Nachvollziehbarkeit
braucht, und (b) das Risiko, dass ein Freitext-Use-Case durch
LLM-Attribut-Extraktion uneinheitlich interpretiert wird (im Spec
explizit als "unnötige Nichtdeterminismus-Quelle" benannt — deshalb gibt
es auch bewusst keinen Freitext-Import, nur 3 fest hinterlegte Use Cases).

*Selbstkontrollfrage:* Was passiert bei `classify()`, wenn sowohl
`is_prohibited_practice=True` als auch `is_safety_component_regulated_product=True`
gesetzt sind — und warum genau in dieser Reihenfolge (welcher echte
AI-Act-Grundsatz steckt dahinter)?

---

### Station 2 — Die drei Use Cases: `src/ai_act_toolkit/use_cases.py`

Drei fest hinterlegte `UseCase`-Dataclasses (`COMFORT_SYSTEM`,
`RECRUITING`, `CHATBOT`), jede mit eigenem `UseCaseAttributes`-Set:

| Use Case | Klasse | Regel | `has_metamorphic_demo` |
|---|---|---|---|
| `COMFORT_SYSTEM` | Hochrisiko | Art. 6(1) Sicherheitsbauteil | `True` |
| `RECRUITING` | Hochrisiko | Art. 6(2)+Annex III (employment) | `False` |
| `CHATBOT` | Begrenztes Risiko | Art. 50 | `False` |

Wichtig: Nur `COMFORT_SYSTEM` hat `has_metamorphic_demo=True` — der
metamorphe Test ist **nicht** allgemein für jeden Hochrisiko-Use-Case
verfügbar, sondern nur für den einen, für den eine echte SUT
(`comfort_system_sut.py`) existiert.

*Selbstkontrollfrage:* Warum ist `RECRUITING` trotz `is_annex3_area=True`
und `EMPLOYMENT` ebenfalls Hochrisiko, obwohl kein
`is_safety_component_regulated_product` gesetzt ist? Welche zweite
Bedingung muss dafür zusätzlich wahr sein (siehe Regel 3 oben)?

---

### Station 3 — Der metamorphe Test: `comfort_system_sut.py` + `metamorphic.py`

**Das Grundproblem (Orakel-Problem):** Bei einem KI-System ist oft nicht
bekannt, was die "richtige" Ausgabe für einen Input ist. Ein metamorpher
Test umgeht das, indem er nicht eine einzelne Ausgabe prüft, sondern eine
**Beziehung** zwischen der Ausgabe eines Quellfalls und der Ausgabe eines
daraus transformierten Folgefalls (so wörtlich im Docstring von
`metamorphic.py`).

Die konkrete **Metamorphic Relation "Temperatur-Monotonie"**
(`TEMPERATURE_MONOTONICITY_RELATION` in `comfort_system_sut.py`):

```python
transform = lambda inputs: {**inputs, "outside_temp_c": inputs["outside_temp_c"] + 5.0}
check = lambda source_output, followup_output: followup_output >= source_output
```

Aussage: Steigt die Außentemperatur um 5°C bei sonst gleichen Bedingungen,
darf die vom simulierten Komfortsystem berechnete Ziel-Kühlintensität
(`decide_cooling_intensity()`) nicht *sinken*.

Der generische Runner `run_relation()` (`metamorphic.py`) macht drei
Schritte: SUT mit den Quell-Inputs aufrufen → `transform()` anwenden, SUT
erneut aufrufen → `check()` auf beide Ausgaben anwenden. Ergebnis ist ein
`MetamorphicResult` mit `passed: bool` sowie beiden Ein-/Ausgaben-Paaren.

**Was beweist ein Erfolg, was ein Fehlschlag?** Ein `passed=True` beweist
*nicht*, dass die absolute Kühlintensität korrekt ist — nur, dass sich die
SUT bezüglich dieser einen Relation konsistent verhält. Ein `passed=False`
beweist umgekehrt zweifelsfrei, dass die SUT diese Konsistenzannahme
verletzt — unabhängig davon, ob man den "wahren" Referenzwert kennt.
Genau das ist der Witz von Metamorphic Testing.

**Der wichtigste Test im ganzen Projekt** ist laut README
`test_broken_sut_fails_relation` (`tests/test_metamorphic.py`): eine
absichtlich falsch konstruierte SUT (`broken_sut`, Kühlintensität *sinkt*
mit steigender Außentemperatur) wird gegen dieselbe Relation getestet und
muss als `passed=False` erkannt werden. Ohne diesen Test wäre ein
"BESTANDEN" der echten SUT nicht aussagekräftig — er beweist, dass der
Runner echte Verletzungen erkennt und nicht einfach immer grün anzeigt.

**Wichtige ehrliche Einschränkung:** In der App selbst zeigt der Button
"Metamorphen Test ausführen" immer BESTANDEN, weil `decide_cooling_intensity()`
konstruktionsbedingt monoton ist. Ein sichtbares Scheitern im Live-Betrieb
gibt es nicht — nur der pytest-Test mit der separat definierten
`broken_sut`-Funktion beweist, dass der Runner Verletzungen erkennen
*würde*. Das ist laut `HANDOVER.md` ein bekannter, bewusst nicht
umgesetzter Erweiterungsvorschlag (ein Toggle für eine kaputte SUT in der
UI).

*Selbstkontrollfrage:* Was genau transformiert `transform()`, und warum
reicht `followup_output >= source_output` als Prüfung aus, obwohl man den
exakten Zahlenwert der Kühlintensität nie "vorher weiß"?

---

### Station 4 — Trennung "LLM erklärt nur" / "Regelbaum entscheidet": `rationale.py` + `app.py`

Die Trennung ist strukturell im Code erzwungen, nicht nur behauptet:

1. `app.py` ruft zuerst `classify(attrs)` auf → `classification` steht
   fest, *bevor* überhaupt ein LLM-Objekt existiert (Zeile 80 in `app.py`,
   `get_llm()` wird erst später im Button-Handler aufgerufen).
2. `rationale.generate_rationale(llm, use_case, classification)` baut den
   Prompt (`RATIONALE_PROMPT`) ausschließlich aus bereits feststehenden
   Werten: `use_case.title`, `use_case.description`,
   `classification.risk_class.value`, `classification.matched_rule`. Der
   Prompt-Text weist das LLM explizit an: *"Erfinde keine zusätzlichen
   Fakten über den Use Case, die oben nicht genannt sind."*
3. Der Rückgabewert von `generate_rationale()` (`response.content`) fließt
   **nirgendwo** zurück in `classify()` oder in `UseCaseAttributes` — er
   landet nur als Anzeigetext (`st.markdown`) und als Textbaustein im
   Governance-Artefakt.
4. Fällt der LLM-Call fehl (kein Netzwerk, ungültiger Key, Rate-Limit),
   fängt `app.py` das mit `try/except` ab (`st.error(...)`) — die
   Klassifizierung, der metamorphe Test und die Konformitätscheckliste
   sind davon komplett unberührt, weil sie nie vom LLM abhingen.

*Selbstkontrollfrage:* Wenn `generate_rationale()` einen Fehler wirft —
was zeigt `app.py` dann trotzdem im Governance-Artefakt an, und woher
kommt dieser Fallback-Text (Zeile 134–137 in `app.py`)?

---

### Station 5 — Das Governance-Artefakt: `governance.py`, Funktion `generate_governance_artifact()`

Reine String-Zusammensetzung, kein LLM beteiligt. Nimmt `UseCase`,
`ClassificationResult`, einen `rationale`-String und optional ein
`MetamorphicResult` entgegen und baut Markdown mit fixen Abschnitten:
Systembeschreibung, Klassifizierung, Begründung, optional "Metamorpher
Test" (nur falls `metamorphic_result is not None`), und eine
Konformitätscheckliste aus der hartcodierten `OBLIGATIONS`-Liste (Art. 9
Risikomanagement bis Art. 15 Genauigkeit/Robustheit/Cybersicherheit, 7
Punkte). Jeder Punkt ist eine Markdown-Checkbox (`- [ ]`), kein
automatisch abgehakter Nachweis — das Tool behauptet nirgendwo, die
Pflichten seien erfüllt, nur dass sie *anwendbar* sind. Am Ende steht
immer der Disclaimer, dass das Dokument keine juristische Prüfung
ersetzt. Wird in `app.py` nur gerendert, wenn
`classification.risk_class == RiskClass.HIGH_RISK`.

*Selbstkontrollfrage:* Was passiert mit dem "Metamorpher Test"-Abschnitt
im Artefakt für den `RECRUITING`-Use-Case, und warum genau (siehe
`test_artifact_omits_metamorphic_section_when_absent` in
`tests/test_governance.py`)?

---

### Station 6 — Provider-agnostische LLM-Anbindung: `llm.py`

`get_llm()` liest `LLM_PROVIDER`/`LLM_MODEL` aus der `.env` und übergibt
sie an LangChains `init_chat_model()`, die je nach Provider-String
(`anthropic`/`openai`) das passende Integrationspaket
(`langchain-anthropic`/`langchain-openai`) lädt und dasselbe
`BaseChatModel`-Interface zurückgibt. Kein Modell ist hartcodiert. Fehlen
`LLM_PROVIDER`/`LLM_MODEL`, wirft die Funktion sofort einen
`RuntimeError` mit den aktuellen (fehlenden) Werten — kein stiller
Fallback auf ein Default-Modell.

*Selbstkontrollfrage:* Wieso reicht ein einziges `get_llm()` für zwei
verschiedene LLM-Anbieter, ohne dass irgendwo im Code
`if provider == "openai": ...` steht?

---

## 4. Die Brücke zur Promotion

**30-Sekunden-Erklärung fürs Interview:**

> "Meine Promotion am KIT/ITIV war 'Validierung von KI-Systemen durch
> Verknüpfung von Szenarien und metamorphes Testen', unter anderem
> erprobt in einer Industriekooperation mit Mercedes-Benz zu autonomen
> Fahrzeug-Komfortsystemen. Das Kernproblem dort: Bei KI-Systemen kennt
> man oft nicht die 'richtige' Ausgabe für einen Test-Input — das
> Orakel-Problem. Metamorphes Testen löst das, indem man nicht eine
> einzelne Ausgabe prüft, sondern eine Beziehung zwischen zwei
> zusammenhängenden Fällen. Genau dieses Prinzip habe ich hier in
> `metamorphic.py` als generischen `run_relation()`-Runner nachgebaut und
> an einem konkreten Fall — Temperatur-Monotonie bei einem simulierten
> Fahrzeug-Komfortsystem, thematisch an dieselbe Mercedes-Kooperation
> angelehnt — tatsächlich ausgeführt, nicht nur behauptet."

Wichtig für die Ehrlichkeit im Gespräch: Der Bezug zur
Mercedes-Kooperation ist **thematisch** (gleiche Systemklasse:
Fahrzeug-Komfortsystem), nicht identisch — `comfort_system_sut.py` ist
eine für dieses Portfolio-Projekt neu geschriebene Toy-Funktion, kein Code
oder Modell aus der eigentlichen Promotion/Kooperation. Die
Übertragungsleistung liegt in der **Methodik** (Metamorphic Relations
statt Referenzorakel), nicht in wiederverwendetem Forschungscode.

---

## 5. Ehrliche Grenzen & Negativergebnisse

Explizit aus README ("Limitierungen"), `HANDOVER.md` und eigener
Code-Analyse, nichts beschönigt:

- **Nur eine einzige Metamorphic Relation** (Temperatur-Monotonie), nicht
  die volle Szenario-Verknüpfungsmethodik der Promotion. Laut Design-Spec
  bewusst so begrenzt, weil ein generisches Metamorphic-Testing-Framework
  "für beliebige Use-Case-Typen... das 3-4-Tage-Budget sprengen" würde.
- **Nur der Automotive-Use-Case hat überhaupt einen ausgeführten
  metamorphen Test** (`has_metamorphic_demo=True` nur bei
  `COMFORT_SYSTEM`). `RECRUITING` und `CHATBOT` haben keinen — obwohl
  gerade Recruiting (Annex III, Beschäftigung) ein Bereich wäre, in dem
  Bias-Tests methodisch naheliegend wären.
- **Die App zeigt live nie ein FEHLGESCHLAGEN** — `decide_cooling_intensity()`
  ist konstruktionsbedingt monoton, daher liefert der "Test ausführen"-Button
  in der Streamlit-App immer BESTANDEN. Nur der separate pytest-Test
  `test_broken_sut_fails_relation` mit einer eigens kaputt konstruierten
  Funktion beweist, dass der Runner Verletzungen *erkennen würde*. Ein
  Recruiter, der nur die Live-App klickt, sieht nie den Negativfall.
- **Toy-SUT, kein echtes ML-Modell.** `decide_cooling_intensity()` ist
  eine simple, deterministische Formel (gewichtete Summe aus
  Temperaturdifferenzen und Insassenzahl, in `[0, 100]` geklippt) — kein
  trainiertes Modell. Die Methodik-Demonstration ist damit unabhängig von
  ML-Trainingsartefakten, beweist aber auch nichts über reale
  ML-Modell-Robustheit.
- **Nur 3 fest hinterlegte Use Cases, kein Freitext-Import.** Bewusste
  Entscheidung (siehe Station 1), aber dadurch auch kein Beleg, dass die
  Klassifizierungslogik mit beliebigen, unstrukturierten
  Use-Case-Beschreibungen umgehen könnte.
- **Annex III stark vereinfacht:** `docs/annex3-mapping.md` bildet die
  echten Annex-III-Bereiche als 8 disjunkte Enum-Werte ab, ohne die
  reale, teils überlappende Unterpunkt-Struktur (mehrere
  Unterkategorien pro Bereich) nachzubilden.
- **Kein rechtsverbindlicher Compliance-Nachweis.** Explizit im README und
  im Governance-Artefakt selbst als Disclaimer vermerkt — ersetzt keine
  juristische Prüfung oder ein echtes Konformitätsbewertungsverfahren.
- **Laut `HANDOVER.md` nie über einen echten Browser durchgeklickt** —
  nur über `streamlit.testing.v1.AppTest` (browserlos) automatisiert
  verifiziert. Marco hat die Live-App selbst als erreichbar bestätigt,
  ein vollständiger manueller Durchlauf aller 3 Use-Cases inkl.
  Governance-Download in der Live-Version durch eine Agenten-Session
  stand laut Handover-Dokument zuletzt noch aus.
- Kleinere, als "Minor" eingestufte und bewusst offen gelassene Punkte
  laut `HANDOVER.md`: `session_state`-Keys in `app.py` akkumulieren pro
  Use-Case/Klasse/Regel-Kombination ungebremst (bei 3 Use Cases harmlos);
  `requirements.txt` dupliziert die Runtime-Deps aus `pyproject.toml`
  (Drift-Risiko); `generate_rationale()` ist als `-> str` typisiert, manche
  LangChain-Provider liefern aber ggf. `list[dict]` als `response.content`.

---

## 6. Recruiter-Simulation

**1. "Erklär mir das Projekt in einem Satz."**
→ Elevator-Pitch aus Abschnitt 1 nutzen.

**2. "Warum ein deterministischer Regelbaum und nicht einfach ein LLM, das den Use Case liest und klassifiziert?"** *(Warum-X-statt-Y)*
→ Weil eine Rechtseinstufung reproduzierbar und auditierbar sein muss.
`classify()` ist eine reine Funktion mit fester Regel-Priorität — jeder
Input liefert immer dieselbe Klasse plus die genaue Regel
(`matched_rule`) als Nachweis. Ein LLM würde hier Nichtdeterminismus genau
dort einführen, wo Nachvollziehbarkeit am wichtigsten ist. Das LLM kommt
bewusst erst *nach* der Entscheidung ins Spiel, nur für die
Prosa-Begründung.

**3. "Warum ausgerechnet die Temperatur-Monotonie-Relation und keine andere?"** *(Warum-X-statt-Y)*
→ Zeitbudget war 3-4 Tage (siehe `CLAUDE.md`), und ein generisches
Metamorphic-Testing-Framework für beliebige Use-Case-Typen war laut
Design-Spec explizit "Bewusst weggelassen", weil es das Budget gesprengt
hätte. Die Monotonie-Relation ist die einfachste Relation, die (a) für
Laien sofort plausibel ist ("wärmer draußen → nicht weniger kühlen"), (b)
mit wenigen Zeilen Code prüf- und fälschbar ist, und (c) das
Kernprinzip — Beziehung statt Referenzwert — vollständig demonstriert,
ohne die Komplexität einer vollen Szenario-Verknüpfung.

**4. "Wie stellt ihr technisch sicher, dass das LLM die Klassifizierung nicht beeinflusst?"**
→ Strukturell durch Aufrufreihenfolge und Datenfluss: `classify()` läuft
zuerst und braucht kein LLM-Objekt. `generate_rationale()` bekommt nur
das *fertige* `ClassificationResult` als Text in den Prompt und der
Rückgabewert fließt nirgendwo zurück in die Klassifizierungslogik — siehe
Station 4.

**5. "Was passiert, wenn der metamorphe Test fehlschlägt — hast du das mal gesehen?"**
→ Ehrlich: In der Live-App nicht, weil die geshippte SUT konstruktionsbedingt
monoton ist. Bewiesen wird die Fehlererkennung durch
`test_broken_sut_fails_relation`, der eine absichtlich kaputte
SUT-Funktion gegen dieselbe Relation laufen lässt und `passed=False`
erwartet. Ein sichtbarer Live-Fehlschlag in der UI wäre eine sinnvolle,
im finalen Review vorgeschlagene, aber nicht umgesetzte Erweiterung
(Toggle für eine kaputte SUT).

**6. "Was, wenn die LLM-API down ist — stürzt die App ab?"**
→ Nein. `app.py` fängt Exceptions beim LLM-Call ab und zeigt eine
Fehlermeldung, aber Klassifizierung, metamorpher Test und
Governance-Artefakt laufen unabhängig weiter — das Artefakt bekommt dann
einen Fallback-Begründungstext, der nur auf der deterministischen Regel
basiert.

**7. "Wie hängt das mit deiner Promotion zusammen — ist das nicht nur ein Buzzword-Bezug?"**
→ Abschnitt 4 nutzen: konkreter methodischer Kern (Metamorphic Relations
gegen das Orakel-Problem) ist identisch, der Automotive-Kontext ist
thematisch an die Mercedes-Kooperation angelehnt — aber ehrlich als neu
geschriebener Toy-Code kennzeichnen, kein wiederverwendeter
Forschungscode.

**8. "Ist das rechtlich belastbar, könnte ein Unternehmen das produktiv einsetzen?"**
→ Nein, explizit nicht. README und das Governance-Artefakt selbst sagen
das direkt: keine rechtsverbindliche Compliance-Aussage, kein Ersatz für
juristische Beratung oder ein echtes Konformitätsbewertungsverfahren. Der
Wert liegt in der demonstrierten *Methodik* (deterministische
Regelanwendung + echter Test + strukturiertes Artefakt), nicht in
Rechtssicherheit.

**9. "Warum nur 3 Use Cases und kein Freitext-Eingabefeld?"**
→ Bewusste Design-Entscheidung: Ein Freitext-Use-Case bräuchte eine
LLM-gestützte Attribut-Extraktion, um ihn in `UseCaseAttributes` zu
überführen — genau die Art von Nichtdeterminismus, die an dieser Stelle
vermieden werden sollte (siehe Frage 2). Die 3 Use Cases zeigen bewusst
die Bandbreite (Hochrisiko über zwei verschiedene Rechtsgrundlagen,
begrenztes Risiko).

**10. "Wie viele Tests habt ihr, und was decken sie ab?"**
→ 17 Tests über 5 Dateien (`test_smoke.py`: 1, `test_risk_engine.py`: 7,
`test_use_cases.py`: 4, `test_metamorphic.py`: 3, `test_governance.py`:
2), alle ohne Netzwerk-/LLM-Zugriff lauffähig, weil Klassifizierung und
metamorpher Test komplett deterministisch/lokal sind. Der wichtigste ist
`test_broken_sut_fails_relation` — ohne den wäre ein "BESTANDEN" nicht
aussagekräftig.

---

## 7. Checkliste — Bist du bereit?

- [ ] Ich kann den Elevator-Pitch (Abschnitt 1) auswendig, ohne
      abzulesen.
- [ ] Ich kann die 4 Prioritätsstufen des Regelbaums (`risk_engine.classify()`)
      in der richtigen Reihenfolge nennen: Art. 5 → Art. 6(1) → Art.
      6(2)+Annex III (mit Art.-6(3)-Ausnahme) → Art. 50 → minimal.
- [ ] Ich kann erklären, was das "Orakel-Problem" ist und warum
      Metamorphic Testing es umgeht — ohne Fachjargon, in einfachen
      Worten.
- [ ] Ich kann die Temperatur-Monotonie-Relation konkret beschreiben:
      was wird transformiert (`outside_temp_c + 5.0`), was wird geprüft
      (`followup_output >= source_output`).
- [ ] Ich kann erklären, warum `test_broken_sut_fails_relation` der
      wichtigste Test im Projekt ist.
- [ ] Ich kann ehrlich sagen, dass die Live-App nie ein FEHLGESCHLAGEN
      zeigt und warum — ohne dass es wie ein verstecktes Problem wirkt.
- [ ] Ich kann in 30 Sekunden die Brücke zur Promotion erklären
      (Abschnitt 4), inklusive der ehrlichen Einschränkung, dass
      `comfort_system_sut.py` neu geschriebener Toy-Code ist, kein
      Forschungscode aus der Mercedes-Kooperation.
- [ ] Ich kann mindestens 2 "Warum X und nicht Y"-Fragen beantworten,
      ohne zu stocken (deterministisch vs. LLM-Klassifikation; genau
      diese eine Metamorphic Relation).
- [ ] Ich kann die Grenzen (Abschnitt 5) benennen, ohne das Projekt
      dabei kleinzureden — Grenzen kennen wirkt kompetenter als
      Grenzen verschweigen.
- [ ] Ich weiß, wo im Code ich bei einer Live-Demo während des
      Interviews live etwas ändern könnte, um die Wirkung zu zeigen
      (z.B. Checkbox "Sicherheitsbauteil" deaktivieren → Klasse fällt
      auf 🟢 Minimales Risiko, siehe README "Beispiel-Use-Cases").
