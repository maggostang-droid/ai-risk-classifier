"""Mutationsanalyse: wie gut ist die Relations-Suite eigentlich?

Ein bestandener metamorpher Test sagt für sich genommen wenig — er könnte
auch bestehen, weil die Relation nichts prüft. Deshalb werden absichtlich
fehlerhafte Varianten des Systems unter Test ("Mutanten") gegen dieselbe
Suite gefahren. Ein Mutant gilt als getötet, sobald ihn mindestens eine
Relation fängt. Der Mutation Score zählt Mutanten, nicht Zellen.

Ein überlebender Mutant ist kein Makel, sondern die interessanteste
Information: er zeigt die Blindstelle der Relationsmenge. Genau deshalb
gibt es `expected_survivor` — bekannte Blindstellen werden deklariert und
in den Tests festgenagelt, damit sie nicht stillschweigend verschwinden.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from ai_act_toolkit.metamorphic.core import MetamorphicRelation, run_relation


@dataclass(frozen=True)
class Mutant:
    key: str
    label: str
    defect: str
    fn: Callable[..., float]
    expected_survivor: bool = False


@dataclass(frozen=True)
class KillMatrix:
    relations: tuple[MetamorphicRelation, ...]
    mutants: tuple[Mutant, ...]
    killed: dict[tuple[str, str], bool] = field(default_factory=dict)

    def killed_by(self, mutant: Mutant) -> list[str]:
        """Namen der Relationen, die diesen Mutanten fangen."""
        return [
            relation.name
            for relation in self.relations
            if self.killed[(relation.name, mutant.key)]
        ]

    def is_killed(self, mutant: Mutant) -> bool:
        return bool(self.killed_by(mutant))

    def survivors(self) -> list[Mutant]:
        return [mutant for mutant in self.mutants if not self.is_killed(mutant)]

    @property
    def score(self) -> tuple[int, int]:
        """(getötete Mutanten, Mutanten gesamt)."""
        return len(self.mutants) - len(self.survivors()), len(self.mutants)


def run_kill_matrix(
    relations: Iterable[MetamorphicRelation],
    mutants: Iterable[Mutant],
    baseline_inputs: dict,
) -> KillMatrix:
    relations = tuple(relations)
    mutants = tuple(mutants)
    killed: dict[tuple[str, str], bool] = {}
    for relation in relations:
        for mutant in mutants:
            try:
                result = run_relation(mutant.fn, relation, baseline_inputs)
                caught = not result.passed
            except Exception:
                # Ein Mutant, der abstürzt, ist ebenfalls erkannt — die Relation
                # hat ihn zwar nicht inhaltlich widerlegt, aber sichtbar gemacht.
                caught = True
            killed[(relation.name, mutant.key)] = caught
    return KillMatrix(relations=relations, mutants=mutants, killed=killed)
