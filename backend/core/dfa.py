"""Déterminisation par la méthode des sous-ensembles (avec epsilon-fermetures)."""
import time
from collections import deque
from dataclasses import dataclass

from core.nfa import EPS
from utils.errors import ComputationLimitError


@dataclass(frozen=True)
class DFA:
    alphabet: tuple
    initial: str
    states: tuple
    finals: frozenset
    transitions: dict   # état -> {symbole -> état}. Transition absente = rejet implicite.

    def is_final(self, state):
        return state in self.finals


def epsilon_closure(nfa, states):
    """Ensemble des états atteignables depuis `states` par transitions epsilon seules."""
    closure = set(states)
    stack = list(states)
    while stack:
        state = stack.pop()
        for target in nfa.transitions.get(state, {}).get(EPS, ()):
            if target not in closure:
                closure.add(target)
                stack.append(target)
    return frozenset(closure)


def move(nfa, states, symbol):
    result = set()
    for state in states:
        result |= nfa.transitions.get(state, {}).get(symbol, set())
    return result


def nfa_to_dfa(nfa, alphabet, max_states, timeout):
    deadline = time.monotonic() + timeout
    alphabet = tuple(sorted(alphabet))

    start = epsilon_closure(nfa, {nfa.start})
    names = {start: "q0"}
    order = [start]
    transitions = {}
    queue = deque([start])

    while queue:
        if time.monotonic() > deadline:
            raise ComputationLimitError("Le calcul de l'automate est trop long pour cette expression.")
        current = queue.popleft()
        row = {}
        for symbol in alphabet:
            target = epsilon_closure(nfa, move(nfa, current, symbol))
            if not target:
                continue          # pas d'état "puits" : la transition reste absente
            if target not in names:
                if len(names) >= max_states:
                    raise ComputationLimitError(
                        "L'automate généré dépasse la taille maximale autorisée (%d états)." % max_states)
                names[target] = "q%d" % len(names)
                order.append(target)
                queue.append(target)
            row[symbol] = names[target]
        transitions[names[current]] = row

    # Un état de l'AFD est final s'il contient l'état final de l'AFN.
    finals = frozenset(names[s] for s in order if nfa.accept in s)
    return DFA(alphabet, "q0", tuple(names[s] for s in order), finals, transitions)
