"""Validation d'une expression régulière : longueur, alphabet, syntaxe."""
from config import Config
from core.lexer import RegexSyntaxError, TokenType, tokenize
from core.parser import parse
from utils.text import describe_char


def validate_regex(regex, alphabet, max_length=Config.MAX_REGEX_LENGTH,
                   max_depth=Config.MAX_PAREN_DEPTH):
    """Valide l'expression et retourne son arbre syntaxique."""
    if not isinstance(regex, str):
        raise RegexSyntaxError("L'expression régulière doit être une chaîne de caractères.")
    regex = regex.strip()
    if regex == "":
        raise RegexSyntaxError("L'expression régulière ne peut pas être vide.")
    if len(regex) > max_length:
        raise RegexSyntaxError(
            "L'expression régulière est trop longue (maximum %d caractères)." % max_length)

    tokens = tokenize(regex)       # ε -> EPSILON
    for token in tokens:
        if token.type is TokenType.CHAR and token.value not in alphabet:
            raise RegexSyntaxError(
                "Le symbole %s ne figure pas dans l'alphabet déclaré." % describe_char(token.value))
    return parse(tokens, max_depth)
