import pytest

from core.alphabet import AlphabetError, parse_alphabet_text
from validators.alphabet_validator import validate_alphabet


def test_alphabet_valide():
    assert validate_alphabet(["a", "b"]) == ("a", "b")
    assert validate_alphabet(["a", "B", "1"]) == ("a", "B", "1")


@pytest.mark.parametrize("raw, fragment", [
    ([], "vide"),
    (["a", "a"], "double"),
    (["ε"], "epsilon"),
    (["€"], "pas autorisé"),
    (["ab"], "un seul caractère"),
    ([""], "un seul caractère"),
    ([1], "un seul caractère"),
    (["é"], "pas autorisé"),
    ([" "], "pas autorisé"),
    (["|"], "pas autorisé"),
    (["*"], "pas autorisé"),
    (["{"], "pas autorisé"),
    (["a\x00"], "un seul caractère"),
    ("ab", "liste"),
    (None, "liste"),
])
def test_alphabet_invalide(raw, fragment):
    with pytest.raises(AlphabetError) as err:
        validate_alphabet(raw)
    assert fragment in err.value.message


def test_alphabet_trop_grand():
    letters = [chr(ord("a") + i) for i in range(26)] + ["0"]
    with pytest.raises(AlphabetError):
        validate_alphabet(letters)
    assert len(validate_alphabet(letters[:26])) == 26


@pytest.mark.parametrize("text, expected", [
    ("{a,b}", ["a", "b"]),
    ("a,b", ["a", "b"]),
    ("  { a , b }  ", ["a", "b"]),
    ("a", ["a"]),
])
def test_parse_texte_valide(text, expected):
    assert parse_alphabet_text(text) == expected


@pytest.mark.parametrize("text", ["", "{}", "a;b", "a,,b", "{a,b", "a,b}", "ab", "a,b,", "a b"])
def test_parse_texte_invalide(text):
    with pytest.raises(AlphabetError):
        parse_alphabet_text(text)
