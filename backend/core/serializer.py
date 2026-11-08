"""Transformation des automates (AFN, AFD, AFD minimal) en données JSON pour le frontend."""
from collections import deque

from config import CANONICAL_EPSILON
from core.nfa import EPS


def _dfa_fields(dfa):
    return {
        "alphabet": list(dfa.alphabet),
        "initial_state": dfa.initial,
        "states": list(dfa.states),
        "final_states": [s for s in dfa.states if s in dfa.finals],
        "transitions": {s: dict(dfa.transitions.get(s, {})) for s in dfa.states},
        "accepts_empty_word": dfa.is_final(dfa.initial),
    }


def _nfa_fields(nfa, alphabet):
    """AFN de Thompson avec états renommés q0, q1... en parcours en largeur (ordre déterministe).

    Les transitions epsilon sont étiquetées « ε » et passent après les symboles de l'alphabet.
    Une transition peut avoir plusieurs cibles : les valeurs sont donc des listes.
    """
    def labels_of(state):
        labels = nfa.transitions.get(state, {})
        return sorted(label for label in labels if label is not EPS) + ([EPS] if EPS in labels else [])

    names = {nfa.start: "q0"}
    order = [nfa.start]
    queue = deque(order)
    while queue:
        state = queue.popleft()
        for label in labels_of(state):
            for target in sorted(nfa.transitions[state][label]):
                if target not in names:
                    names[target] = "q%d" % len(names)
                    order.append(target)
                    queue.append(target)

    transitions = {}
    for state in order:
        row = {}
        for label in labels_of(state):
            targets = sorted((names[t] for t in nfa.transitions[state][label]), key=lambda n: int(n[1:]))
            row[CANONICAL_EPSILON if label is EPS else label] = targets
        transitions[names[state]] = row

    return {
        "alphabet": list(alphabet),
        "epsilon": CANONICAL_EPSILON,
        "initial_state": names[nfa.start],
        "states": [names[s] for s in order],
        "final_states": [names[nfa.accept]],
        "transitions": transitions,
    }


def dfa_to_dict(dfa, automate_id, minimal=None, nfa=None):
    """`minimal` : AFD minimal optionnel (clé « minimal_dfa »). `nfa` : AFN optionnel (clé « nfa »)."""
    data = {"success": True, "automate_id": automate_id, **_dfa_fields(dfa)}
    if minimal is not None:
        data["minimal_dfa"] = _dfa_fields(minimal)
    if nfa is not None:
        data["nfa"] = _nfa_fields(nfa, dfa.alphabet)
    return data


def simulation_to_dict(word, result):
    return {
        "success": True,
        "accepted": result.accepted,
        "message": "Mot accepté" if result.accepted else "Mot rejeté",
        "word": word,
        "path": list(result.path),
        "blocked": result.blocked,
    }
