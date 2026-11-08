"""Analyse lexicale d'une expression régulière.

Seul "ε" est l'élément neutre (token EPSILON). Le caractère "€" n'a aucun rôle
particulier : c'est un caractère ordinaire, refusé s'il ne figure pas dans l'alphabet.
"""
import unicodedata
from dataclasses import dataclass
from enum import Enum, auto

from config import CANONICAL_EPSILON
from utils.errors import RuleError
from utils.text import describe_char


class RegexSyntaxError(RuleError):
    pass


class TokenType(Enum):
    CHAR = auto()
    UNION = auto()
    STAR = auto()
    LPAREN = auto()
    RPAREN = auto()
    EPSILON = auto()
    END = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    pos: int


_OPERATORS = {
    "|": TokenType.UNION,
    "*": TokenType.STAR,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
}


def normalize_epsilon(regex):
    """Normalisation Unicode (NFC) : ε reste le seul symbole du mot vide."""
    return unicodedata.normalize("NFC", regex)


def tokenize(regex):
    """Retourne la liste des tokens, terminée par un token END."""
    regex = normalize_epsilon(regex)
    tokens = []
    for pos, char in enumerate(regex):
        if char == CANONICAL_EPSILON:
            tokens.append(Token(TokenType.EPSILON, char, pos))
        elif char in _OPERATORS:
            tokens.append(Token(_OPERATORS[char], char, pos))
        elif char.isspace() or not char.isprintable():
            raise RegexSyntaxError(
                "L'expression régulière contient un caractère interdit (%s) à la position %d."
                % (describe_char(char), pos + 1))
        else:
            tokens.append(Token(TokenType.CHAR, char, pos))
    tokens.append(Token(TokenType.END, "", len(regex)))
    return tokens
