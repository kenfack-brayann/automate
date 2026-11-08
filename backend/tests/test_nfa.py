import itertools
import json
import re

import pytest

from core.nfa import build_nfa
from core.pipeline import build_automata
from core.serializer import _nfa_fields
from validators.regex_validator import validate_regex

AB = ("a", "b")


def _nfa_dict(regex):
    nfa, dfa = build_automata(AB, regex)
    return _nfa_fields(nfa, dfa.alphabet)


def _closure(data, states):
    closure, stack = set(states), list(states)
    while stack:
        for target in data["transitions"][stack.pop()].get(data["epsilon"], []):
            if target not in closure:
                closure.add(target)
                stack.append(target)
    return closure


def _accepts(data, word):
    """Simule l'AFN sérialisé (ensemble d'états courants + ε-fermeture)."""
    current = _closure(data, {data["initial_state"]})
    for symbol in word:
        step = {t for s in current for t in data["transitions"][s].get(symbol, [])}
        current = _closure(data, step)
    return bool(current & set(data["final_states"]))


def test_structure_de_l_afn():
    data = _nfa_dict("(a|b)*abb")
    assert set(data) == {"alphabet", "epsilon", "initial_state", "states", "final_states", "transitions"}
    assert data["alphabet"] == ["a", "b"] and data["epsilon"] == "ε"
    assert data["initial_state"] == "q0" and data["states"][0] == "q0"
    assert len(data["final_states"]) == 1 and data["final_states"][0] in data["states"]
    assert set(data["transitions"]) == set(data["states"])


def test_afn_d_un_symbole():
    data = _nfa_dict("a")
    assert data["states"] == ["q0", "q1"]
    assert data["transitions"] == {"q0": {"a": ["q1"]}, "q1": {}}
    assert data["final_states"] == ["s1"]


def test_epsilon_dans_l_afn():
    data = _nfa_dict("a|ε")
    labels = {label for row in data["transitions"].values() for label in row}
    assert "ε" in labels and labels <= {"a", "b", "ε"}


def test_numerotation_deterministe():
    assert _nfa_dict("(a|b)*abb") == _nfa_dict("(a|b)*abb")


def test_cibles_valides_et_triees():
    data = _nfa_dict("(a*|b)*a")
    states = set(data["states"])
    for row in data["transitions"].values():
        for targets in row.values():
            assert isinstance(targets, list) and set(targets) <= states
            assert targets == sorted(targets, key=lambda n: int(n[1:]))


@pytest.mark.parametrize("regex", ["(a|b)*abb", "a*b*", "(ab|ba)*", "ε|a", "(a*b)*", "((a|b)(a|b))*", "ε"])
def test_afn_reconnait_le_meme_langage_que_re(regex):
    """L'AFN sérialisé, simulé directement, accepte exactement les mots de l'expression."""
    data = _nfa_dict(regex)
    oracle = re.compile(regex.replace("ε", "(?:)"))
    for n in range(0, 7):
        for letters in itertools.product(AB, repeat=n):
            word = "".join(letters)
            assert _accepts(data, word) == bool(oracle.fullmatch(word)), (regex, word)


def test_api_renvoie_afn_afd_et_afd_minimal(client):
    r = client.post("/api/automate", data=json.dumps({"alphabet": ["a", "b"], "regex": "(a|b)*abb"}),
                    content_type="application/json")
    body = r.get_json()
    assert r.status_code == 200
    assert body["nfa"]["initial_state"] == "q0" and body["nfa"]["epsilon"] == "ε"
    assert len(body["states"]) == 5 and len(body["minimal_dfa"]["states"]) == 4
    assert all(s.startswith("s") for s in body["nfa"]["states"])
    assert all(s.startswith("q") for s in body["states"])
