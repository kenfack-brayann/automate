"""Enchaîne validation -> AST -> AFN -> AFD (puis AFD minimal, calculé par la route)."""
from config import Config
from core.dfa import nfa_to_dfa
from core.nfa import build_nfa
from validators.regex_validator import validate_regex


def build_automata(alphabet, regex,
                   max_regex_length=Config.MAX_REGEX_LENGTH,
                   max_states=Config.MAX_DFA_STATES,
                   timeout=Config.BUILD_TIMEOUT_SECONDS,
                   max_depth=Config.MAX_PAREN_DEPTH):
    """Retourne le couple (AFN, AFD) de l'expression."""
    ast = validate_regex(regex, alphabet, max_regex_length, max_depth)
    nfa = build_nfa(ast)
    return nfa, nfa_to_dfa(nfa, alphabet, max_states, timeout)


def compile_regex(alphabet, regex, **limits):
    """Retourne uniquement l'AFD (mêmes paramètres que build_automata)."""
    return build_automata(alphabet, regex, **limits)[1]
