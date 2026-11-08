"""Stockage temporaire en mémoire des AFD, avec durée de vie limitée.

Limite connue : le stockage est propre à chaque processus. Avec plusieurs
workers (gunicorn -w N) il faudrait un stockage partagé (Redis, etc.).
"""
import secrets
import threading
import time

from utils.errors import NotFoundError


class AutomateStore:
    def __init__(self, ttl_seconds, max_items):
        self._ttl = ttl_seconds
        self._max = max_items
        self._items = {}          # id -> (expiration, dfa)
        self._lock = threading.Lock()

    def _purge(self, now):
        for key in [k for k, (exp, _) in self._items.items() if exp <= now]:
            del self._items[key]

    def put(self, dfa):
        now = time.monotonic()
        # Identifiant aléatoire cryptographique : impossible à deviner.
        automate_id = secrets.token_urlsafe(16)
        with self._lock:
            self._purge(now)
            while len(self._items) >= self._max:      # éviction du plus ancien
                oldest = min(self._items, key=lambda k: self._items[k][0])
                del self._items[oldest]
            self._items[automate_id] = (now + self._ttl, dfa)
        return automate_id

    def get(self, automate_id):
        if not isinstance(automate_id, str) or not 0 < len(automate_id) <= 64:
            raise NotFoundError("Impossible de retrouver l'automate demandé.")
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            entry = self._items.get(automate_id)
        if entry is None:
            raise NotFoundError("Impossible de retrouver l'automate demandé.")
        return entry[1]
