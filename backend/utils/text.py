"""Petits utilitaires d'affichage sûr pour les messages d'erreur."""


def describe_char(c):
    """Rend un caractère lisible dans un message (espaces et invisibles explicités)."""
    if c == " ":
        return "espace"
    if not c.isprintable():
        return "\\u%04x" % ord(c)
    return c


def short(text, limit=30):
    """Tronque et échappe une chaîne issue de l'utilisateur."""
    out = "".join(describe_char(c) if not c.isprintable() else c for c in text[:limit])
    return out + ("…" if len(text) > limit else "")
