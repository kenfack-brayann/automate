import pytest

from core.pipeline import compile_regex
from core.simulation import simulate
from validators.word_validator import WordError, validate_word

AB = ("a", "b")


@pytest.mark.parametrize("word, expected", [
    ("abb", True), ("aabb", True), ("babb", True),
    ("aba", False), ("ab", False), ("", False),
])
def test_tableau_simulation(word, expected):
    dfa = compile_regex(AB, "(a|b)*abb")
    validate_word(word, dfa.alphabet)
    assert simulate(dfa, word).accepted is expected


def test_symbole_inconnu():
    dfa = compile_regex(AB, "(a|b)*abb")
    with pytest.raises(WordError) as err:
        validate_word("abc", dfa.alphabet)
    assert "non autorisé" in err.value.message


def test_mot_vide_valide():
    assert validate_word("", AB) == ""


def test_mot_trop_long():
    with pytest.raises(WordError):
        validate_word("a" * 1001, AB)


def test_transition_manquante_sans_erreur():
    dfa = compile_regex(AB, "ab")
    result = simulate(dfa, "ba")
    assert result.accepted is False and result.blocked is True
    assert result.path == ("q0",)


def test_parcours():
    dfa = compile_regex(AB, "(a|b)*abb")
    result = simulate(dfa, "abb")
    assert result.path[0] == "q0" and len(result.path) == 4
    assert simulate(dfa, "").path == ("q0",)


def test_tests_multiples_meme_automate():
    dfa = compile_regex(AB, "a*")
    assert [simulate(dfa, w).accepted for w in ["", "a", "aaa", "b"]] == [True, True, True, False]
