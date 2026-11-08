"""Validation stricte d'un alphabet reçu par l'API (liste de symboles)."""
import string

from config import Config, EPSILON_CHARS
from core.alphabet import AlphabetError
from utils.text import describe_char

# Format autorisé : une lettre ASCII ou un chiffre. Cela exclut par construction
# les opérateurs, les accolades, les espaces, les caractères de contrôle et tous
# les caractères Unicode ambigus (epsilon grec, euro, lookalikes...).
# Le symbole ε a son propre message d'erreur ; € est refusé comme tout autre symbole.
ALLOWED_SYMBOLS = frozenset(string.ascii_letters + string.digits)


def validate_alphabet(raw, max_size=Config.MAX_ALPHABET_SIZE):
    if not isinstance(raw, list):
        raise AlphabetError("L'alphabet doit être une liste de symboles.")
    if len(raw) == 0:
        raise AlphabetError("L'alphabet ne peut pas être vide.")
    if len(raw) > max_size:
        raise AlphabetError("L'alphabet est trop grand (maximum %d symboles)." % max_size)

    seen = []
    for symbol in raw:
        if not isinstance(symbol, str) or len(symbol) != 1:
            raise AlphabetError("Chaque symbole de l'alphabet doit être un seul caractère.")
        if symbol in EPSILON_CHARS:
            raise AlphabetError("Le caractère epsilon ne peut pas appartenir à l'alphabet.")
        if symbol not in ALLOWED_SYMBOLS:
            raise AlphabetError(
                "Le symbole « %s » n'est pas autorisé : utilisez uniquement des lettres "
                "(a-z, A-Z) ou des chiffres (0-9)." % describe_char(symbol))
        if symbol in seen:
            raise AlphabetError("Le symbole %s est en double dans l'alphabet." % symbol)
        seen.append(symbol)
    return tuple(seen)
