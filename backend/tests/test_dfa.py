import pytest

from core.dfa import epsilon_closure, move
from core.nfa import build_nfa
from core.pipeline import compile_regex
from core.serializer import dfa_to_dict
from utils.errors import ComputationLimitError
from validators.regex_validator import validate_regex

AB = ("a", "b")


def test_afd_classique_abb():
    dfa = compile_regex(AB, "(a|b)*abb")
    assert dfa.initial == "q0"
    assert len(dfa.states) == 5                     # AFD classique de Thompson + sous-ensembles
    assert len(dfa.finals) == 1
    assert dfa.initial not in dfa.finals


def test_determinisme_et_coherence():
    dfa = compile_regex(AB, "(a|b)*abb")
    for state in dfa.states:
        for symbol, target in dfa.transitions[state].items():
            assert symbol in dfa.alphabet
            assert isinstance(target, str) and target in dfa.states   # une seule cible
    assert set(dfa.transitions) == set(dfa.states)
    assert dfa.finals <= set(dfa.states)


def test_epsilon_fermeture():
    nfa = build_nfa(validate_regex("a*", AB))
    closure = epsilon_closure(nfa, {nfa.start})
    assert nfa.accept in closure          # a* accepte le mot vide
    assert nfa.start in closure
    nfa2 = build_nfa(validate_regex("a", AB))
    assert nfa2.accept not in epsilon_closure(nfa2, {nfa2.start})


def test_move_puis_fermeture():
    nfa = build_nfa(validate_regex("ab", AB))
    after_a = epsilon_closure(nfa, move(nfa, epsilon_closure(nfa, {nfa.start}), "a"))
    after_ab = epsilon_closure(nfa, move(nfa, after_a, "b"))
    assert nfa.accept in after_ab and nfa.accept not in after_a


def test_transitions_manquantes_pas_d_etat_puits():
    dfa = compile_regex(AB, "ab")
    assert dfa.transitions["q0"] == {"a": "q1"}     # pas de transition 'b' depuis q0


def test_serialisation_afd():
    data = dfa_to_dict(compile_regex(AB, "(a|b)*abb"), "id")
    assert set(data) == {"success", "automate_id", "alphabet", "initial_state", "states",
                         "final_states", "transitions", "accepts_empty_word"}
    assert data["alphabet"] == ["a", "b"]
    assert data["accepts_empty_word"] is False


def test_limite_etats():
    regex = "(a|b)*a" + "(a|b)" * 15          # ~2^16 états après déterminisation
    with pytest.raises(ComputationLimitError):
        compile_regex(AB, regex, max_states=300)


def test_limite_temps():
    with pytest.raises(ComputationLimitError):
        compile_regex(AB, "(a|b)*a" + "(a|b)" * 12, max_states=10**9, timeout=0.0)
