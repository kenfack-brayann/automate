"""Minimisation d'un AFD par raffinement de partition (algorithme de Moore).

Convention de l'application : pas d'état puits. L'AFD est donc complété
INTERNEMENT par un état puits, minimisé, puis le puits (et tous les états
équivalents à lui, c'est-à-dire ceux d'où aucun état final n'est atteignable)
est retiré du résultat. Une transition absente signifie toujours « rejet ».
"""
from collections import deque

from core.dfa import DFA

_SINK = "<puits>"      # nom interne, ne peut pas entrer en collision avec "q0", "q1"...


def minimize_dfa(dfa):
    """Retourne l'AFD minimal (états renommés q0, q1... en parcours en largeur)."""
    alphabet = dfa.alphabet

    def step(state, symbol):
        if state == _SINK:
            return _SINK
        return dfa.transitions.get(state, {}).get(symbol, _SINK)

    states = list(dfa.states) + [_SINK]

    # Partition initiale : états finaux / non finaux (le puits est non final).
    cls = {s: (1 if s in dfa.finals else 0) for s in states}
    count = len(set(cls.values()))
    while True:
        signatures = {s: (cls[s], tuple(cls[step(s, a)] for a in alphabet)) for s in states}
        ids = {}
        new_cls = {s: ids.setdefault(signatures[s], len(ids)) for s in states}
        if len(ids) == count:          # plus aucun raffinement : partition stable
            break
        cls, count = new_cls, len(ids)

    dead = cls[_SINK]
    if cls[dfa.initial] == dead:       # langage vide (impossible avec ce langage de regex)
        return DFA(alphabet, "q0", ("q0",), frozenset(), {"q0": {}})

    representative = {}
    for s in dfa.states:
        representative.setdefault(cls[s], s)

    # Numérotation déterministe : parcours en largeur, alphabet trié.
    names = {cls[dfa.initial]: "q0"}
    order = [cls[dfa.initial]]
    transitions = {}
    queue = deque(order)
    while queue:
        current = queue.popleft()
        row = {}
        for symbol in alphabet:
            target = cls[step(representative[current], symbol)]
            if target == dead:
                continue
            if target not in names:
                names[target] = "q%d" % len(names)
                order.append(target)
                queue.append(target)
            row[symbol] = names[target]
        transitions[names[current]] = row

    finals = frozenset(names[c] for c in order if representative[c] in dfa.finals)
    return DFA(alphabet, "q0", tuple(names[c] for c in order), finals, transitions)
