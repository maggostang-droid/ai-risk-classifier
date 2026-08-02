"""Toy-'System unter Test': Vorauswahl-Scoring für Bewerbungen.

Warum es hier zwei Varianten gibt: `score_applicant_naive` ist ein
absichtlich fehlerhaftes Demonstrationsobjekt. Es enthält ein aus dem
Vornamen abgeleitetes Merkmal — den Fehler, den die metamorphe Relation
fangen soll. In echten Systemen kommt so etwas selten so offen herein,
sondern über korrelierte Proxys (Postleitzahl, Vereinsmitgliedschaft,
Schulname). Hier steht es explizit im Code, damit man den Mechanismus
lesen kann. `score_applicant_fixed` ist die korrigierte Variante.

Die Relation "Namensinvarianz" zahlt auf Art. 10(2)(f)(g) ein: die
Untersuchung des Systems auf mögliche Verzerrungen.
"""

from ai_act_toolkit.metamorphic.core import MetamorphicRelation
from ai_act_toolkit.metamorphic.mutation import Mutant

# Sachfremdes Merkmal: eine nach Vornamen vergebene "Passung", wie sie in
# fehlerhaften Systemen als Proxy für soziale Herkunft entsteht.
_NAME_BONUS: dict[str, float] = {
    "maximilian": 6.0,
    "charlotte": 6.0,
    "friederike": 6.0,
    "kevin": -6.0,
    "chantal": -6.0,
    "justin": -6.0,
}


def score_applicant_fixed(
    first_name: str,
    years_experience: float,
    skill_match: float,
    education_level: int,
) -> float:
    """Bewertet eine Bewerbung mit 0 bis 100 Punkten, ohne den Namen zu verwenden.

    Der Vorname steht trotzdem in der Signatur, damit die Namensinvarianz-
    Relation ihn variieren kann.
    """
    score = 10.0 + years_experience * 3.0 + skill_match * 50.0 + education_level * 5.0
    return max(0.0, min(100.0, score))


def score_applicant_naive(
    first_name: str,
    years_experience: float,
    skill_match: float,
    education_level: int,
) -> float:
    """Fehlerhafte Variante: rechnet einen vom Vornamen abgeleiteten Bonus mit ein."""
    base = 10.0 + years_experience * 3.0 + skill_match * 50.0 + education_level * 5.0
    base += _NAME_BONUS.get(first_name.lower(), 0.0)
    return max(0.0, min(100.0, base))


# education_level=4 statt 3 ist kein kosmetischer Wert: bei 3 rechnet die
# Vorzeichenfehler-Variante 10+15-40+15 = 0 und wird von der unteren
# Clip-Grenze auf 0 gehalten — Quell- und Folgefall wären beide 0 und die
# Skill-Monotonie würde den Defekt nicht sehen. Ein Baselinepunkt, an dem
# ein Mutant im Sättigungsbereich liegt, macht die Relation blind.
RECRUITING_BASELINE = dict(
    first_name="Maximilian",
    years_experience=5.0,
    skill_match=0.8,
    education_level=4,
)

NAME_INVARIANCE_RELATION = MetamorphicRelation(
    name="Namensinvarianz",
    description=(
        "Wird im Bewerbungsprofil ausschließlich der Vorname ausgetauscht und sonst "
        "nichts verändert, muss der Score exakt gleich bleiben. Ändert er sich, "
        "entscheidet das System nach einem sachfremden Merkmal."
    ),
    transform=lambda inputs: {**inputs, "first_name": "Kevin"},
    check=lambda source_output, followup_output: followup_output == source_output,
    evidence_for="Art. 10",
)

EXPERIENCE_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Berufsjahre-Monotonie",
    description=(
        "Mehr einschlägige Berufsjahre bei sonst gleichem Profil müssen den Score "
        "echt erhöhen."
    ),
    transform=lambda inputs: {
        **inputs,
        "years_experience": inputs["years_experience"] + 2.0,
    },
    check=lambda source_output, followup_output: followup_output > source_output,
    evidence_for="Art. 15",
)

SKILL_MONOTONICITY_RELATION = MetamorphicRelation(
    name="Skill-Monotonie",
    description=(
        "Eine bessere Passung der Qualifikationen darf den Score nicht senken."
    ),
    transform=lambda inputs: {**inputs, "skill_match": inputs["skill_match"] + 0.1},
    check=lambda source_output, followup_output: followup_output >= source_output,
    evidence_for="Art. 15",
)

RECRUITING_SATURATION_RELATION = MetamorphicRelation(
    name="Sättigungsgrenze",
    description="Auch bei extremen Profilen muss der Score zwischen 0 und 100 liegen.",
    transform=lambda inputs: {
        **inputs,
        "years_experience": 60.0,
        "skill_match": 1.0,
        "education_level": 9,
    },
    check=lambda source_output, followup_output: 0.0 <= followup_output <= 100.0,
    evidence_for="Art. 15",
)

RECRUITING_RELATIONS = (
    NAME_INVARIANCE_RELATION,
    EXPERIENCE_MONOTONICITY_RELATION,
    SKILL_MONOTONICITY_RELATION,
    RECRUITING_SATURATION_RELATION,
)


def _experience_ignored(first_name, years_experience, skill_match, education_level):
    # Fehler: Berufserfahrung fließt nicht ein.
    score = 10.0 + skill_match * 50.0 + education_level * 5.0
    return max(0.0, min(100.0, score))


def _skill_sign_flip(first_name, years_experience, skill_match, education_level):
    # Fehler: bessere Passung senkt den Score.
    score = 10.0 + years_experience * 3.0 - skill_match * 50.0 + education_level * 5.0
    return max(0.0, min(100.0, score))


def _clip_missing(first_name, years_experience, skill_match, education_level):
    # Fehler: der Wertebereich wird nicht begrenzt.
    return 10.0 + years_experience * 3.0 + skill_match * 50.0 + education_level * 5.0


def _rounded(first_name, years_experience, skill_match, education_level):
    # Fehler: Score wird auf ganze Punkte gerundet. Verletzt keine der vier
    # Relationen — bekannte Blindstelle der Suite.
    return float(
        round(
            score_applicant_fixed(
                first_name, years_experience, skill_match, education_level
            )
        )
    )


RECRUITING_MUTANTS = (
    Mutant(
        key="namensmerkmal",
        label="Vom Vornamen abgeleitetes Merkmal",
        defect=(
            "Der Score hängt am Vornamen — ein sachfremdes, diskriminierendes Merkmal."
        ),
        fn=score_applicant_naive,
    ),
    Mutant(
        key="erfahrung_ignoriert",
        label="Berufserfahrung ignoriert",
        defect="Berufsjahre gehen nicht in den Score ein.",
        fn=_experience_ignored,
    ),
    Mutant(
        key="vorzeichen_skill",
        label="Vorzeichenfehler Qualifikationspassung",
        defect="Eine bessere Passung senkt den Score.",
        fn=_skill_sign_flip,
    ),
    Mutant(
        key="clip_fehlt",
        label="Wertebereich nicht begrenzt",
        defect="Der Score kann über 100 hinauslaufen.",
        fn=_clip_missing,
    ),
    Mutant(
        key="rundung",
        label="Rundung auf ganze Punkte",
        defect="Score wird gerundet — von keiner Relation erkannt.",
        fn=_rounded,
        expected_survivor=True,
    ),
)
