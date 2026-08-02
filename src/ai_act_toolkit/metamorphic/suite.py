"""Führt alle Relationen eines Systems unter Test auf einmal aus.

Eine einzelne Relation belegt wenig. Erst eine Suite mehrerer Relationen
deckt verschiedene Fehlerarten ab, und erst über `by_article()` lässt sich
das Ergebnis den AI-Act-Pflichten zuordnen.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ai_act_toolkit.metamorphic.core import (
    MetamorphicRelation,
    MetamorphicResult,
    run_relation,
)


@dataclass(frozen=True)
class SuiteResult:
    results: tuple[MetamorphicResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def counts(self) -> tuple[int, int]:
        """(bestanden, gesamt)."""
        return sum(1 for result in self.results if result.passed), len(self.results)

    def by_article(self) -> dict[str, list[MetamorphicResult]]:
        """Gruppiert die Ergebnisse nach dem Artikel, auf den sie einzahlen."""
        grouped: dict[str, list[MetamorphicResult]] = {}
        for result in self.results:
            grouped.setdefault(result.relation.evidence_for, []).append(result)
        return grouped


def run_suite(
    sut_fn: Callable[..., float],
    relations: Iterable[MetamorphicRelation],
    baseline_inputs: dict,
) -> SuiteResult:
    return SuiteResult(
        results=tuple(
            run_relation(sut_fn, relation, baseline_inputs) for relation in relations
        )
    )
