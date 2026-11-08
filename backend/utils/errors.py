"""Exceptions applicatives et gestion centralisée des erreurs HTTP."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

log = logging.getLogger(__name__)


class AppError(Exception):
    """Erreur contrôlée dont le message peut être montré à l'utilisateur."""

    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class RequestError(AppError):
    """Requête mal formée (JSON, propriétés, types) -> 400."""
    status_code = 400


class RuleError(AppError):
    """Données bien structurées mais contraires aux règles métier -> 422."""
    status_code = 422


class NotFoundError(AppError):
    status_code = 404


class ComputationLimitError(RuleError):
    """Calcul trop coûteux (trop d'états ou délai dépassé)."""


_HTTP_MESSAGES = {
    404: "Ressource introuvable.",
    405: "Méthode non autorisée.",
    413: "Requête trop volumineuse.",
    429: "Trop de requêtes. Veuillez patienter quelques instants.",
}


def _json_error(message, status):
    response = jsonify({"success": False, "error": message})
    response.status_code = status
    return response


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return _json_error(err.message, err.status_code)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_err):
        return _json_error(_HTTP_MESSAGES[413], 413)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        code = err.code or 500
        return _json_error(_HTTP_MESSAGES.get(code, "Requête invalide."), code)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # Détails techniques uniquement dans les journaux, jamais côté client.
        log.exception("Erreur interne non prévue : %s", err)
        return _json_error("Une erreur interne est survenue. Veuillez réessayer.", 500)
