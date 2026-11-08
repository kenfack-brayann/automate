"""Validation de la structure des requêtes JSON (schéma strict par endpoint)."""
from utils.errors import RequestError
from utils.text import short


def parse_json_body(request):
    if not request.is_json:
        raise RequestError("Le corps de la requête doit être au format JSON.")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RequestError("Le corps de la requête JSON est invalide : un objet est attendu.")
    return data


def validate_schema(data, schema):
    """`schema` : {nom_de_propriété: type_attendu}. Tout écart est refusé."""
    for key in data:
        if key not in schema:
            raise RequestError("Propriété inattendue dans la requête : « %s »." % short(str(key)))
    for key, expected_type in schema.items():
        if key not in data:
            raise RequestError("Propriété obligatoire manquante : « %s »." % key)
        if not isinstance(data[key], expected_type):
            raise RequestError("Le type de la propriété « %s » est incorrect." % key)
    return data
