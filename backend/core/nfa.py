"""AFN (méthode de Thompson) : étape intermédiaire de la construction, affichée comme première vue."""
from collections import defaultdict

from core.parser import Concat, Epsilon, Star, Symbol, Union

EPS = None  # étiquette des transitions epsilon


class NFA:
    def __init__(self):
        self.transitions = defaultdict(lambda: defaultdict(set))
        self.count = 0
        self.start = None
        self.accept = None

    def new_state(self):
        self.count += 1
        return self.count - 1

    def add(self, src, symbol, dst):
        self.transitions[src][symbol].add(dst)


def build_nfa(ast):
    nfa = NFA()
    nfa.start, nfa.accept = _build(nfa, ast)
    return nfa


def _build(nfa, node):
    """Retourne le couple (état d'entrée, état de sortie) du fragment."""
    if isinstance(node, Symbol):
        s, e = nfa.new_state(), nfa.new_state()
        nfa.add(s, node.char, e)
        return s, e
    if isinstance(node, Epsilon):
        s, e = nfa.new_state(), nfa.new_state()
        nfa.add(s, EPS, e)
        return s, e
    if isinstance(node, Concat):
        ls, le = _build(nfa, node.left)
        rs, re_ = _build(nfa, node.right)
        nfa.add(le, EPS, rs)
        return ls, re_
    if isinstance(node, Union):
        s, e = nfa.new_state(), nfa.new_state()
        ls, le = _build(nfa, node.left)
        rs, re_ = _build(nfa, node.right)
        nfa.add(s, EPS, ls)
        nfa.add(s, EPS, rs)
        nfa.add(le, EPS, e)
        nfa.add(re_, EPS, e)
        return s, e
    if isinstance(node, Star):
        s, e = nfa.new_state(), nfa.new_state()
        cs, ce = _build(nfa, node.child)
        nfa.add(s, EPS, cs)
        nfa.add(s, EPS, e)
        nfa.add(ce, EPS, cs)
        nfa.add(ce, EPS, e)
        return s, e
    raise TypeError("Nœud syntaxique inconnu")
