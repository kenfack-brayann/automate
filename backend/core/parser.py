"""Analyse syntaxique (descente récursive) et construction de l'arbre syntaxique.

Grammaire formelle :

    expr    ::= term ( '|' term )*
    term    ::= factor+
    factor  ::= atom '*'?
    atom    ::= CHAR | EPSILON | '(' expr ')'

Un seul '*' par facteur : "a**" est refusé (opérateurs consécutifs). On peut
écrire "(a*)*" si besoin.
"""
from dataclasses import dataclass

from config import Config
from core.lexer import RegexSyntaxError, TokenType


# --- Arbre syntaxique -------------------------------------------------------
@dataclass(frozen=True)
class Epsilon:
    pass


@dataclass(frozen=True)
class Symbol:
    char: str


@dataclass(frozen=True)
class Union:
    left: object
    right: object


@dataclass(frozen=True)
class Concat:
    left: object
    right: object


@dataclass(frozen=True)
class Star:
    child: object


_ATOM_START = (TokenType.CHAR, TokenType.EPSILON, TokenType.LPAREN)


class Parser:
    def __init__(self, tokens, max_depth=Config.MAX_PAREN_DEPTH):
        self.tokens = tokens
        self.i = 0
        self.depth = 0
        self.max_depth = max_depth

    # -- utilitaires
    def _peek(self):
        return self.tokens[self.i]

    def _next(self):
        token = self.tokens[self.i]
        self.i += 1
        return token

    @staticmethod
    def _error(detail, token):
        return RegexSyntaxError(
            "L'expression régulière contient une erreur de syntaxe : %s (position %d)."
            % (detail, token.pos + 1))

    # -- règles de la grammaire
    def parse(self):
        node = self._expr()
        token = self._peek()
        if token.type is TokenType.RPAREN:
            raise self._error("parenthèse fermante sans parenthèse ouvrante", token)
        if token.type is not TokenType.END:      # sécurité, normalement inatteignable
            raise self._error("symbole inattendu", token)
        return node

    def _expr(self):
        node = self._term()
        while self._peek().type is TokenType.UNION:
            union = self._next()
            if self._peek().type in (TokenType.END, TokenType.RPAREN, TokenType.UNION):
                raise self._error("alternative vide après '|'", union)
            node = Union(node, self._term())
        return node

    def _term(self):
        token = self._peek()
        if token.type not in _ATOM_START:
            if token.type is TokenType.STAR:
                raise self._error("'*' mal placé (rien à répéter)", token)
            if token.type is TokenType.UNION:
                raise self._error("'|' mal placé (alternative vide)", token)
            if token.type is TokenType.RPAREN:
                if self.i > 0 and self.tokens[self.i - 1].type is TokenType.LPAREN:
                    raise self._error("parenthèses vides", token)
                raise self._error("')' mal placée", token)
            raise self._error("expression incomplète", token)
        node = self._factor()
        while self._peek().type in _ATOM_START:
            node = Concat(node, self._factor())
        return node

    def _factor(self):
        node = self._atom()
        if self._peek().type is TokenType.STAR:
            self._next()
            node = Star(node)
            if self._peek().type is TokenType.STAR:
                raise self._error("opérateurs '*' consécutifs", self._peek())
        return node

    def _atom(self):
        token = self._next()
        if token.type is TokenType.CHAR:
            return Symbol(token.value)
        if token.type is TokenType.EPSILON:
            return Epsilon()
        # LPAREN (garanti par _ATOM_START)
        self.depth += 1
        if self.depth > self.max_depth:
            raise self._error("parenthèses imbriquées trop profondément", token)
        if self._peek().type is TokenType.END:
            raise self._error("parenthèse ouvrante non fermée", token)
        node = self._expr()
        if self._peek().type is not TokenType.RPAREN:
            raise self._error("parenthèse ouvrante non fermée", token)
        self._next()
        self.depth -= 1
        return node


def parse(tokens, max_depth=Config.MAX_PAREN_DEPTH):
    return Parser(tokens, max_depth).parse()
