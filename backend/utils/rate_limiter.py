"""Limiteur de débit simple (fenêtre glissante par adresse IP, en mémoire)."""
import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, max_requests, window_seconds):
        self._max = max_requests
        self._window = window_seconds
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 10_000:               # nettoyage des clés périmées
                self._hits = {k: q for k, q in self._hits.items()
                              if q and now - q[-1] < self._window}
            queue = self._hits.setdefault(key, deque())
            while queue and now - queue[0] >= self._window:
                queue.popleft()
            if len(queue) >= self._max:
                return False
            queue.append(now)
            return True
