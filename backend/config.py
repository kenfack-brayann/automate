"""Configuration centrale : toutes les limites de sécurité sont définies ici."""


class Config:
    # --- Limites des requêtes ---
    MAX_CONTENT_LENGTH = 4 * 1024      # taille max d'une requête HTTP (octets)

    # --- Limites des données ---
    MAX_ALPHABET_SIZE = 26             # nombre max de symboles
    MAX_REGEX_LENGTH = 200             # longueur max de l'expression régulière
    MAX_WORD_LENGTH = 1000             # longueur max d'un mot à tester
    MAX_PAREN_DEPTH = 50               # imbrication maximale des parenthèses

    # --- Limites de calcul (protection contre l'explosion d'états) ---
    MAX_DFA_STATES = 300
    BUILD_TIMEOUT_SECONDS = 2.0

    # --- Stockage temporaire des automates (en mémoire) ---
    AUTOMATON_TTL_SECONDS = 30 * 60
    MAX_STORED_AUTOMATA = 500

    # --- Anti-abus : requêtes par IP et par fenêtre ---
    RATE_LIMIT_REQUESTS = 60
    RATE_LIMIT_WINDOW_SECONDS = 60


# Seul le caractère epsilon représente le mot vide ("€" n'est PAS un élément neutre).
EPSILON_CHARS = frozenset({"ε"})
# Forme canonique utilisée après normalisation.
CANONICAL_EPSILON = "ε"
