import itertools
import re

import pytest

from core.lexer import RegexSyntaxError, TokenType, tokenize
from core.parser import Epsilon
from core.pipeline import compile_regex
from core.simulation import simulate
from validators.alphabet_validator import validate_alphabet
from validators.regex_validator import validate_regex
from validators.word_validator import WordError, validate_word
from core.alphabet import AlphabetError

AB = ("a", "b")

# Tableau du cahier des charges (7.3)
CAS_EPSILON = [
    ("ε", "", True),
    ("ε", "a", False),
    ("a|ε", "", True),
    ("a|ε", "a", True),
    ("a*", "", True), ("a*", "aaa", True),
    ("ab", "", False),
    ("(a|b)*ε", "", True),
]


@pytest.mark.parametrize("regex, word, expected", CAS_EPSILON)
def test_tableau_epsilon(regex, word, expected):
    dfa = compile_regex(AB, regex)
    assert simulate(dfa, word).accepted is expected


def test_epsilon_seul_element_neutre():
    types = [t.type for t in tokenize("a|ε")]
    assert TokenType.EPSILON in types
    assert validate_regex("ε", AB) == Epsilon()


def test_euro_n_est_pas_un_element_neutre():
    # € est un caractère ordinaire : le lexer en fait un simple CHAR, pas un EPSILON.
    types = [t.type for t in tokenize("a|€")]
    assert TokenType.EPSILON not in types
    assert types.count(TokenType.CHAR) == 2


@pytest.mark.parametrize("regex", ["€", "a|€", "(a|b)*€", "€*", "(€)", "a€b"])
def test_euro_refuse_dans_expression(regex):
    with pytest.raises(RegexSyntaxError) as err:
        validate_regex(regex, AB)
    assert err.value.message == "Le symbole € ne figure pas dans l'alphabet déclaré."


def test_euro_dans_l_alphabet_refuse():
    with pytest.raises(AlphabetError) as err:
        validate_alphabet(["a", "€"])
    assert "pas autorisé" in err.value.message     # refusé comme tout symbole non alphanumérique


def test_epsilon_interdit_dans_alphabet():
    with pytest.raises(AlphabetError) as err:
        validate_alphabet(["a", "ε"])
    assert "epsilon" in err.value.message


def test_epsilon_interdit_dans_mot():
    with pytest.raises(WordError):
        validate_word("aε", AB)


def test_euro_dans_mot_refuse_comme_symbole_inconnu():
    with pytest.raises(WordError) as err:
        validate_word("a€", AB)
    assert "ne figure pas dans l'alphabet" in err.value.message


def test_aucune_transition_epsilon_dans_afd():
    for regex in ["a|ε", "(a|b)*ε", "ε", "(ε|a)*b"]:
        dfa = compile_regex(AB, regex)
        for row in dfa.transitions.values():
            assert set(row) <= set(AB)          # uniquement des symboles de l'alphabet
            assert all(sym not in ("ε", None, "") for sym in row)


def test_etat_initial_final_ssi_mot_vide_accepte():
    for regex in ["ε", "a*", "a|ε", "(a|b)*ε", "ab", "a", "(a|b)*abb"]:
        dfa = compile_regex(AB, regex)
        assert dfa.is_final(dfa.initial) == simulate(dfa, "").accepted
    assert compile_regex(AB, "a*").is_final("q0")
    assert not compile_regex(AB, "ab").is_final("q0")


def _to_python_re(regex):
    return re.compile(regex.replace("ε", "(?:)"))


@pytest.mark.parametrize("regex", [
    "(a|b)*abb", "a*b*", "(ab|ba)*", "ε|a", "(a|ε)(b|ε)", "(a*b)*", "a(a|b)*b|ε", "((a|b)(a|b))*",
    "(a*|b*)*", "a|ε", "(ε)", "(a|b)*ε", "a*(b|ε)a*",
])
def test_langage_identique_a_python_re(regex):
    """Oracle : on compare l'AFD au moteur `re` de Python sur tous les mots courts (test seulement)."""
    dfa = compile_regex(AB, regex)
    oracle = _to_python_re(regex)
    for n in range(0, 8):
        for letters in itertools.product(AB, repeat=n):
            word = "".join(letters)
            assert simulate(dfa, word).accepted == bool(oracle.fullmatch(word)), (regex, word)
