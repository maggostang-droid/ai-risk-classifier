"""Lässt ein LLM nur die Begründung in Klartext formulieren, die
Risikoklasse selbst kommt deterministisch aus risk_engine.classify().
"""

from langchain_core.language_models.chat_models import BaseChatModel

from ai_act_toolkit.risk_engine import ClassificationResult
from ai_act_toolkit.use_cases import UseCase

RATIONALE_PROMPT = """Du bist Assistent für EU-AI-Act-Risikoklassifizierung.
Ein regelbasierter Klassifizierer hat folgendes Ergebnis ermittelt:

Use Case: {title}
Beschreibung: {description}
Risikoklasse: {risk_class}
Angewendete Regel: {matched_rule}

Formuliere in 3-4 Sätzen auf Deutsch eine für Nicht-Juristen verständliche
Begründung, warum dieser Use Case in diese Risikoklasse fällt. Erfinde
keine zusätzlichen Fakten über den Use Case, die oben nicht genannt sind."""


def generate_rationale(
    llm: BaseChatModel, use_case: UseCase, classification: ClassificationResult
) -> str:
    prompt = RATIONALE_PROMPT.format(
        title=use_case.title,
        description=use_case.description,
        risk_class=classification.risk_class.value,
        matched_rule=classification.matched_rule,
    )
    response = llm.invoke(prompt)
    return response.content
