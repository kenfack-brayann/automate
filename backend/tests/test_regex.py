import pytest

from core.lexer import RegexSyntaxError, TokenType, tokenize
from core.parser import Concat, Epsilon, Star, Symbol, Union
from validators.regex_validator import validate_regex

AB = ("a", "b")


def test_arbre_syntaxique():
    assert validate_regex("a|b", AB) == Union(Symbol("a"), Symbol("b"))
    assert validate_regex("ab", AB) == Concat(Symbol("a"), Symbol("b"))
    assert validate_regex("a*", AB) == Star(Symbol("a"))
    assert validate_regex("a|b*", AB) == Union(Symbol("a"), Star(Symbol("b")))   # * prioritaire
    assert validate_regex("ab|a", AB) == Union(Concat(Symbol("a"), Symbol("b")), Symbol("a"))


@pytest.mark.parametrize("regex", ["(a|b)*abb", "a", "(a)", "((a|b)*)*", "a|ε", "ε*", "(ε|a)b"])
def test_expressions_valides(regex):
    validate_regex(regex, AB)


@pytest.mark.parametrize("regex", [
    "", "   ", "(a", "a)", "((a)", "()", "*a", "a**", "a||b", "|a", "a|", "(|a)", "(a|)",
    "a|*", "(*a)", "a b", "a\tb", "a\nb", "c", "a|c", "$", "a+", "a?", "a.b", "[ab]", "a{2}", "\\a",
])
def test_expressions_invalides(regex):
    with pytest.raises(RegexSyntaxError):
        validate_regex(regex, AB)


def test_expression_trop_longue():
    with pytest.raises(RegexSyntaxError) as err:
        validate_regex("a" * 201, AB)
    assert "trop longue" in err.value.message
    validate_regex("a" * 200, AB)


def test_imbrication_trop_profonde():
    with pytest.raises(RegexSyntaxError):
        validate_regex("(" * 60 + "a" + ")" * 60, AB)


def test_message_symbole_absent():
    with pytest.raises(RegexSyntaxError) as err:
        validate_regex("a|c", AB)
    assert err.value.message == "Le symbole c ne figure pas dans l'alphabet déclaré."


def test_tokens():
    types = [t.type for t in tokenize("(a|b)*")]
    assert types == [TokenType.LPAREN, TokenType.CHAR, TokenType.UNION, TokenType.CHAR,
                     TokenType.RPAREN, TokenType.STAR, TokenType.END]


def test_epsilon_mal_forme():
    for regex in ["ε**", "|ε", "ε|", "ε(", "(ε"]:
        with pytest.raises(RegexSyntaxError):
            validate_regex(regex, AB)
