"""Gestion et normalisation des alphabets."""
from utils.errors import RuleError
from utils.text import short


class AlphabetError(RuleError):
    pass


def parse_alphabet_text(text):
    """Convertit une saisie texte ("{a,b}" ou "a,b") en liste de symboles.

    Les espaces superflus sont supprimés. Les séparateurs incorrects
    (point-virgule, éléments vides...) sont refusés.
    """
    if not isinstance(text, str):
        raise AlphabetError("L'alphabet doit être une chaîne de caractères.")
    text = text.strip()
    if text.startswith("{") or text.endswith("}"):
        if not (text.startswith("{") and text.endswith("}")):
            raise AlphabetError("Les accolades de l'alphabet ne sont pas équilibrées.")
        text = text[1:-1].strip()
    if text == "":
        raise AlphabetError("L'alphabet ne peut pas être vide.")
    symbols = []
    for part in text.split(","):
        part = part.strip()
        if part == "":
            raise AlphabetError("Séparateur incorrect : symbole manquant entre deux virgules.")
        if len(part) != 1:
            raise AlphabetError(
                "Chaque symbole doit être un seul caractère, séparé par des virgules "
                "(élément invalide : « %s »)." % short(part))
        symbols.append(part)
    return symbols
