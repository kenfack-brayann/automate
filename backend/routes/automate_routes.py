"""Endpoints de l'API REST."""
from flask import Blueprint, current_app, jsonify, request

from core.minimizer import minimize_dfa
from core.pipeline import build_automata
from core.serializer import dfa_to_dict, simulation_to_dict
from core.simulation import simulate
from validators.alphabet_validator import validate_alphabet
from validators.request_validator import parse_json_body, validate_schema
from validators.word_validator import validate_word

bp = Blueprint("automate", __name__, url_prefix="/api")


@bp.post("/automate")
def create_automate():
    cfg = current_app.config
    data = validate_schema(parse_json_body(request), {"alphabet": list, "regex": str})
    alphabet = validate_alphabet(data["alphabet"], cfg["MAX_ALPHABET_SIZE"])
    nfa, dfa = build_automata(
        alphabet, data["regex"],
        max_regex_length=cfg["MAX_REGEX_LENGTH"],
        max_states=cfg["MAX_DFA_STATES"],
        timeout=cfg["BUILD_TIMEOUT_SECONDS"],
        max_depth=cfg["MAX_PAREN_DEPTH"],
    )
    automate_id = current_app.extensions["automate_store"].put(dfa)
    return jsonify(dfa_to_dict(dfa, automate_id, minimal=minimize_dfa(dfa), nfa=nfa))


@bp.post("/automate/check")
def check_word():
    cfg = current_app.config
    data = validate_schema(parse_json_body(request), {"automate_id": str, "word": str})
    dfa = current_app.extensions["automate_store"].get(data["automate_id"])
    word = validate_word(data["word"], dfa.alphabet, cfg["MAX_WORD_LENGTH"])   # "" autorisé
    return jsonify(simulation_to_dict(word, simulate(dfa, word)))
