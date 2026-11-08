"""Validation d'un mot à tester. La chaîne vide est valide (mot vide)."""
from config import Config, EPSILON_CHARS
from utils.errors import RuleError
from utils.text import describe_char


class WordError(RuleError):
    pass


def validate_word(word, alphabet, max_length=Config.MAX_WORD_LENGTH):
    if not isinstance(word, str):
        raise WordError("Le mot doit être une chaîne de caractères.")
    if len(word) > max_length:
        raise WordError("Le mot est trop long (maximum %d caractères)." % max_length)
    for char in word:
        if char in EPSILON_CHARS:
            raise WordError(
                "Le mot contient un symbole non autorisé : ε est réservé aux "
                "expressions régulières. Laissez le champ vide pour tester le mot vide.")
        if char not in alphabet:
            raise WordError(
                "Le mot contient un symbole non autorisé : « %s » ne figure pas dans l'alphabet."
                % describe_char(char))
    return word
