import json

import pytest

from app import create_app


def post(client, url, payload, **kw):
    return client.post(url, data=json.dumps(payload), content_type="application/json", **kw)


def make(client, alphabet=("a", "b"), regex="(a|b)*abb"):
    r = post(client, "/api/automate", {"alphabet": list(alphabet), "regex": regex})
    assert r.status_code == 200, r.get_json()
    return r.get_json()


# ---------- API nominale ----------
def test_generation_et_verification(client):
    data = make(client)
    assert data["success"] and data["initial_state"] == "q0" and len(data["states"]) == 5
    r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": "abb"})
    assert r.status_code == 200
    assert r.get_json()["accepted"] is True and r.get_json()["message"] == "Mot accepté"


def test_mot_vide_via_api(client):
    data = make(client, regex="a*")
    r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": ""})
    assert r.status_code == 200 and r.get_json()["accepted"] is True
    data = make(client, regex="ab")
    r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": ""})
    assert r.status_code == 200 and r.get_json()["accepted"] is False


def test_epsilon_via_api(client):
    data = make(client, regex="a|ε")
    r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": ""})
    assert r.get_json()["accepted"] is True


def test_euro_refuse_via_api(client):
    r = post(client, "/api/automate", {"alphabet": ["a", "b"], "regex": "a|€"})
    assert r.status_code == 422
    assert r.get_json()["error"] == "Le symbole € ne figure pas dans l'alphabet déclaré."


def test_afd_minimal_via_api(client):
    data = make(client)
    minimal = data["minimal_dfa"]
    assert len(data["states"]) == 5 and len(minimal["states"]) == 4
    assert minimal["initial_state"] == "q0" and minimal["alphabet"] == ["a", "b"]
    assert set(minimal) == {"alphabet", "initial_state", "states", "final_states",
                            "transitions", "accepts_empty_word"}


# ---------- Requêtes mal formées ----------
def test_json_mal_forme(client):
    r = client.post("/api/automate", data="{pas du json", content_type="application/json")
    assert r.status_code == 400 and r.get_json()["success"] is False


def test_pas_de_content_type_json(client):
    r = client.post("/api/automate", data="alphabet=a", content_type="text/plain")
    assert r.status_code == 400


def test_json_pas_un_objet(client):
    assert post(client, "/api/automate", ["a"]).status_code == 400


def test_propriete_manquante(client):
    assert post(client, "/api/automate", {"alphabet": ["a"]}).status_code == 400
    assert post(client, "/api/automate/check", {"word": "a"}).status_code == 400


def test_type_incorrect(client):
    assert post(client, "/api/automate", {"alphabet": "ab", "regex": "a"}).status_code == 400
    assert post(client, "/api/automate", {"alphabet": ["a"], "regex": 42}).status_code == 400
    assert post(client, "/api/automate/check", {"automate_id": 1, "word": "a"}).status_code == 400
    assert post(client, "/api/automate/check", {"automate_id": "x", "word": None}).status_code == 400


def test_propriete_inattendue(client):
    r = post(client, "/api/automate", {"alphabet": ["a"], "regex": "a", "admin": True})
    assert r.status_code == 400 and "inattendue" in r.get_json()["error"]


# ---------- Entrées malveillantes ----------
@pytest.mark.parametrize("regex", [
    "__import__('os').system('ls')", "a|b; rm -rf /", "<script>alert(1)</script>",
    "${7*7}", "a' OR '1'='1", "(?:a)", "a{1000000}", "(a+)+$", "../../etc/passwd",
])
def test_code_malveillant_refuse(client, regex):
    r = post(client, "/api/automate", {"alphabet": ["a", "b"], "regex": regex})
    assert r.status_code == 422
    assert "Traceback" not in r.get_data(as_text=True)


def test_alphabet_avec_caracteres_reserves(client):
    for bad in ["|", "*", "(", ")", "{", "}", ",", " ", "ε", "€", "\\", "'", "<"]:
        r = post(client, "/api/automate", {"alphabet": ["a", bad], "regex": "a"})
        assert r.status_code == 422, bad


def test_epsilon_interdit_alphabet_message(client):
    r = post(client, "/api/automate", {"alphabet": ["ε"], "regex": "a"})
    assert r.status_code == 422
    assert r.get_json()["error"] == "Le caractère epsilon ne peut pas appartenir à l'alphabet."


def test_limites(client):
    assert post(client, "/api/automate", {"alphabet": ["a"], "regex": "a" * 201}).status_code == 422
    data = make(client)
    r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": "a" * 1001})
    assert r.status_code == 422


def test_explosion_etats_refusee(client):
    regex = "(a|b)*a" + "(a|b)" * 15
    r = post(client, "/api/automate", {"alphabet": ["a", "b"], "regex": regex})
    assert r.status_code == 422


def test_requete_trop_volumineuse(client):
    r = client.post("/api/automate", data=json.dumps({"alphabet": ["a"], "regex": "a" * 6000}),
                    content_type="application/json")
    assert r.status_code == 413


def test_automate_inexistant(client):
    r = post(client, "/api/automate/check", {"automate_id": "n-existe-pas", "word": "a"})
    assert r.status_code == 404
    r = post(client, "/api/automate/check", {"automate_id": "x" * 500, "word": "a"})
    assert r.status_code == 404


def test_automate_expire():
    app = create_app({"AUTOMATON_TTL_SECONDS": 0, "RATE_LIMIT_REQUESTS": 1000})
    c = app.test_client()
    data = make(c)
    r = post(c, "/api/automate/check", {"automate_id": data["automate_id"], "word": "abb"})
    assert r.status_code == 404


def test_epsilon_dans_mot_refuse(client):
    data = make(client)
    for eps in ("ε", "€"):      # ε est réservé aux expressions ; € n'est pas dans l'alphabet
        r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": eps})
        assert r.status_code == 422


def test_symbole_inconnu_dans_mot(client):
    data = make(client)
    r = post(client, "/api/automate/check", {"automate_id": data["automate_id"], "word": "abc"})
    assert r.status_code == 422 and "non autorisé" in r.get_json()["error"]


def test_identifiants_distincts_et_longs(client):
    ids = {make(client)["automate_id"] for _ in range(5)}
    assert len(ids) == 5 and all(len(i) >= 20 for i in ids)


def test_limitation_de_debit():
    app = create_app({"RATE_LIMIT_REQUESTS": 3, "RATE_LIMIT_WINDOW_SECONDS": 60})
    c = app.test_client()
    codes = [post(c, "/api/automate", {"alphabet": ["a"], "regex": "a"}).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]


def test_erreur_interne_sans_fuite(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("secret /srv/app/interne.py")
    monkeypatch.setattr("routes.automate_routes.build_automata", boom)
    r = post(client, "/api/automate", {"alphabet": ["a"], "regex": "a"})
    assert r.status_code == 500
    body = r.get_data(as_text=True)
    assert "secret" not in body and "interne.py" not in body
    assert r.get_json()["error"] == "Une erreur interne est survenue. Veuillez réessayer."


def test_en_tetes_de_securite_et_route_inconnue(client):
    r = client.get("/api/inconnue")
    assert r.status_code == 404 and r.get_json()["success"] is False
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
