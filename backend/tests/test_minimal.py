import itertools

import pytest

from core.minimizer import minimize_dfa
from core.pipeline import compile_regex
from core.serializer import dfa_to_dict
from core.simulation import simulate

AB = ("a", "b")

EXPRESSIONS = [
    "(a|b)*abb", "a*b*", "(ab|ba)*", "ε|a", "(a|ε)(b|ε)", "(a*b)*", "a(a|b)*b|ε",
    "((a|b)(a|b))*", "(a*|b*)*", "(ε)", "(a|b)*ε", "a*(b|ε)a*", "(a|b)*a(a|b)", "ab", "ε",
]


def _words(max_len):
    for n in range(max_len + 1):
        for letters in itertools.product(AB, repeat=n):
            yield "".join(letters)


def _accepts_from(dfa, state, word):
    for symbol in word:
        state = dfa.transitions[state].get(symbol)
        if state is None:
            return False
    return state in dfa.finals


@pytest.mark.parametrize("regex, expected", [
    ("(a|b)*abb", 4),        # l'AFD de Thompson en a 5 : q0 et q2 sont équivalents
    ("(a|b)*ε", 1),
    ("a*", 1),
    ("(a*|b*)*", 1),
    ("((a|b)(a|b))*", 2),
    ("ab", 3),
    ("ε|a", 2),
])
def test_nombre_d_etats_minimal(regex, expected):
    assert len(minimize_dfa(compile_regex(AB, regex)).states) == expected


@pytest.mark.parametrize("regex", EXPRESSIONS)
def test_meme_langage(regex):
    dfa = compile_regex(AB, regex)
    minimal = minimize_dfa(dfa)
    assert len(minimal.states) <= len(dfa.states)
    for word in _words(8):
        assert simulate(minimal, word).accepted == simulate(dfa, word).accepted, (regex, word)


@pytest.mark.parametrize("regex", EXPRESSIONS)
def test_minimalite(regex):
    """Deux états distincts sont toujours distinguables ; aucun état n'est mort ; idempotence."""
    minimal = minimize_dfa(compile_regex(AB, regex))
    probes = [w for w in _words(len(minimal.states))]
    for s, t in itertools.combinations(minimal.states, 2):
        assert any(_accepts_from(minimal, s, w) != _accepts_from(minimal, t, w) for w in probes), (s, t)
    for s in minimal.states:
        assert any(_accepts_from(minimal, s, w) for w in probes), "état mort : " + s
    assert minimize_dfa(minimal) == minimal


def test_structure_et_nommage():
    minimal = minimize_dfa(compile_regex(AB, "(a|b)*abb"))
    assert minimal.initial == "q0"
    assert minimal.states == ("q0", "q1", "q2", "q3")
    assert set(minimal.transitions) == set(minimal.states)
    assert minimal.finals <= set(minimal.states)
    for row in minimal.transitions.values():
        assert set(row) <= set(AB)
        assert set(row.values()) <= set(minimal.states)


def test_pas_d_etat_puits():
    minimal = minimize_dfa(compile_regex(AB, "ab"))
    assert minimal.transitions["q0"] == {"a": "q1"}       # transition absente = rejet


def test_serialisation_afd_minimal():
    dfa = compile_regex(AB, "(a|b)*abb")
    data = dfa_to_dict(dfa, "id", minimal=minimize_dfa(dfa))
    assert len(data["states"]) == 5 and len(data["minimal_dfa"]["states"]) == 4
    assert data["minimal_dfa"]["accepts_empty_word"] is False
    assert "minimal_dfa" not in dfa_to_dict(dfa, "id")
