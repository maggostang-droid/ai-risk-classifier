# Fragebogen-Kriterien → EU-AI-Act-Rechtsgrundlage

Dieses Dokument ordnet jedes Kriterium aus dem Fragebogen (`app.py`,
implementiert in `src/ai_act_toolkit/risk_engine.py`,
`UseCaseAttributes`) der jeweiligen echten Rechtsgrundlage im EU AI Act
zu. Es dient als Nachvollziehbarkeits-Referenz für die deterministische
Klassifizierungslogik in `classify()`.

*Kurz und sachlich, kein Ersatz für eine juristische Prüfung — siehe auch
README, Abschnitt "Limitierungen".*

## Kriterien im Detail

| Fragebogen-Kriterium (`UseCaseAttributes`-Feld) | Rechtsgrundlage | Bedeutung |
|---|---|---|
| `is_prohibited_practice` | **Art. 5** | Verbotene KI-Praktiken (z.B. Social Scoring, manipulative Techniken, ungezielte Erfassung von Gesichtsbildern). Trifft dieses Kriterium zu, ist das System unzulässig — unabhängig von allen anderen Kriterien. |
| `is_safety_component_regulated_product` | **Art. 6(1) + Annex I** | KI-System ist Sicherheitsbauteil eines Produkts, das bereits einer sektorspezifischen EU-Konformitätsbewertung unterliegt (z.B. Maschinen, Fahrzeuge, Medizinprodukte gemäß den in Annex I gelisteten Harmonisierungsrechtsvorschriften). Führt direkt zu Hochrisiko, ohne Annex-III-Prüfung. |
| `is_annex3_area` + `annex3_area` | **Art. 6(2) + Annex III** | KI-System fällt in einen der 9 in Annex III gelisteten Hochrisiko-Bereiche (siehe Tabelle unten). Notwendige, aber laut Art. 6(3) nicht hinreichende Bedingung für Hochrisiko. |
| `significant_risk_to_health_safety_fundamental_rights` | **Art. 6(3)** (Ausnahme) | Rückausnahme: Selbst wenn ein Annex-III-Bereich zutrifft, ist das System NICHT hochriskant, wenn es kein signifikantes Risiko für Gesundheit, Sicherheit oder Grundrechte darstellt (z.B. rein vorbereitende/unterstützende Aufgaben ohne Einfluss auf die Entscheidung). Im Toolkit als positives Kriterium modelliert: nur wenn `is_annex3_area` UND dieses Feld zutreffen, wird auf Hochrisiko klassifiziert. |
| `has_transparency_obligation` | **Art. 50** | Transparenzpflichten für Systeme, die direkt mit natürlichen Personen interagieren (Chatbots), synthetische Inhalte erzeugen (Deepfakes) oder Emotionserkennung/biometrische Kategorisierung durchführen — unabhängig von der Hochrisiko-Einstufung. Führt zu "begrenztes Risiko", falls keine der obigen Kategorien bereits gegriffen hat. |
| *(keines der obigen trifft zu)* | — | Minimales Risiko: keine spezifischen Pflichten über die allgemeinen Sorgfaltspflichten hinaus. |

## Die 9 Annex-III-Bereiche (`Annex3Area`-Enum)

| Enum-Wert | Annex-III-Bereich (Kurzform) |
|---|---|
| `BIOMETRIC_IDENTIFICATION` | Biometrische Identifizierung und Kategorisierung natürlicher Personen |
| `CRITICAL_INFRASTRUCTURE` | Betrieb kritischer Infrastruktur (z.B. Energie-, Wasser-, Verkehrsnetze) |
| `EDUCATION` | Zugang zu und Bewertung in der allgemeinen und beruflichen Bildung |
| `EMPLOYMENT` | Beschäftigung, Personalmanagement und Zugang zur Selbstständigkeit |
| `ESSENTIAL_SERVICES` | Zugang zu wesentlichen privaten/öffentlichen Diensten (z.B. Kreditwürdigkeit, Sozialleistungen) |
| `LAW_ENFORCEMENT` | Strafverfolgung |
| `MIGRATION_ASYLUM_BORDER` | Migration, Asyl und Grenzkontrolle |
| `JUSTICE_DEMOCRATIC_PROCESSES` | Rechtspflege und demokratische Prozesse |
| `NONE` | Kein Annex-III-Bereich einschlägig |

Hinweis: Die reale Annex-III-Liste umfasst faktisch acht benannte
Kategorien plus die Biometrie-Kategorie, die selbst mehrere
Unterpunkte hat; das Toolkit bildet sie zur Vereinfachung als neun
disjunkte Enum-Werte ab statt die vollständige, teils überlappende
Unterpunkt-Struktur nachzubilden.

## Anwendungsbeispiele im Toolkit

- **Autonomes Fahrzeug-Komfortsystem** (`COMFORT_SYSTEM`):
  `is_safety_component_regulated_product=True` → Art. 6(1), da die
  Sitzverstellung in sicherheitsrelevante Fahrzeuggeometrie eingreift
  (siehe `use_cases.py`).
- **KI-gestützte Bewerber-Vorauswahl** (`RECRUITING`):
  `is_annex3_area=True` mit `annex3_area=EMPLOYMENT` und
  `significant_risk_to_health_safety_fundamental_rights=True` → Art.
  6(2) + Annex III (Beschäftigung).
- **Kundenservice-Chatbot** (`CHATBOT`): keines der Hochrisiko-Kriterien
  trifft zu, aber `has_transparency_obligation=True` → Art. 50
  (Interaktion mit natürlichen Personen).
