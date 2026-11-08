"""Simulation de la lecture d'un mot par l'AFD (mot vide inclus)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationResult:
    accepted: bool
    path: tuple          # états visités, état initial inclus
    blocked: bool        # True si une transition manquait en cours de lecture


def simulate(dfa, word):
    """Le mot vide ne lit aucun symbole : il est accepté ssi l'état initial est final."""
    state = dfa.initial
    path = [state]
    for symbol in word:
        next_state = dfa.transitions.get(state, {}).get(symbol)
        if next_state is None:         # transition manquante : rejet, sans erreur
            return SimulationResult(False, tuple(path), True)
        state = next_state
        path.append(state)
    return SimulationResult(dfa.is_final(state), tuple(path), False)
